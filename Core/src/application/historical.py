"""
Carga de datos históricos (2019-2025) a partir de plantillas Excel generadas desde un
formulario con la edición cerrada:

- Plantilla de respuestas: lo que cada entidad contestó en su época (una fila por entidad en la
  hoja «Respuestas» y una hoja por pregunta bucle con una fila por tarjeta).
- Plantilla de resultados: el puntaje de cada entidad por componente, variable, indicador y pregunta y el
  total. NO se valida contra los pesos del formulario: son valores ya presentados en su época.

La entidad se identifica por su `actor_id` (el de la base de datos). Antes de guardar se puede
validar el archivo (`dry_run`): devuelve el reporte de errores sin escribir nada.
"""

import hashlib
import io
import re
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from sqlalchemy import delete, func, or_, select

from shared.db import UnitOfWork
from shared.enums import SubmissionStatusesEnum
from shared.models import (
    Actor,
    Form,
    FormResult,
    Grade,
    QuestionResult,
    SectionResult,
    Submission,
    SubmissionStatusType,
)

from domain.services.errors import (
    FormEditionHasDataError,
    FormEditionOpenError,
    FormNotFoundError,
    HistoricalFileError,
    HistoricalForbiddenError,
)
from application.submissions import SubmissionAppService
from domain.services.submissions import SubmissionService
from infrastructure.repositories.forms import FormRepository
from schemas.historical import (
    ResponseEntityResults,
    ResponseHistoricalForm,
    ResponseHistoricalIssue,
    ResponseHistoricalReport,
    ResponseQuestionScore,
    ResponseRecord,
    ResponseSectionScore,
)
from schemas.submissions import (
    BooleanAnswerIn,
    CardEntryAnswerIn,
    DateAnswerIn,
    MultiChoiceAnswerIn,
    NumericAnswerIn,
    SingleChoiceAnswerIn,
    TextAnswerIn,
)

from ._access import is_admin

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_RESPONSES_SHEET = "Respuestas"
_RESULTS_SHEET = "Resultados"
_META_SHEET = "_meta"
_LISTS_SHEET = "_listas"
_MAX_ANSWER_NUMERIC = Decimal("99999999999999.9999")  # numeric(18,4): 14 enteros
_MAX_RESULT_NUMERIC = Decimal("9999999999.9999")  # numeric(14,4): 10 enteros
_YES = {"si", "sí", "s", "yes", "y", "true", "verdadero", "1"}
_NO = {"no", "n", "false", "falso", "0"}
_LEVEL = {"C": "Componente", "V": "Variable", "I": "Indicador", "Q": "Pregunta"}

_HEAD_FILL = PatternFill("solid", fgColor="E0E7FF")
_BOLD = Font(bold=True)


# ---------------------------------------------------------------------------- estructura


@dataclass
class QField:
    id: UUID
    label: str
    type: str
    choices: list = dc_field(default_factory=list)  # [(id, code, label, text_input)]


@dataclass
class QInfo:
    n: int  # posición de la pregunta en el formulario (1..N)
    id: UUID
    label: str
    code: str
    is_loop: bool
    source_id: UUID | None
    template_id: UUID | None
    indicator_label: str
    fields: list[QField]  # sin los campos de archivo

    @property
    def sheet(self) -> str:
        return f"P{self.n}"


@dataclass
class Node:
    id: UUID
    code: str
    label: str
    level: str  # C / V / I


@dataclass
class Structure:
    form: Form
    nodes: list[Node]
    questions: list[QInfo]
    skipped_files: int
    # Orden de las columnas de la plantilla de resultados: componente → variable → indicador →
    # sus preguntas. (clave = id, nivel «C»/«V»/«I» o «Q», código, etiqueta)
    result_columns: list[tuple[UUID, str, str, str]] = dc_field(default_factory=list)


def _build_structure(form: Form, sections: list) -> Structure:
    by_parent: dict[Any, list] = {}
    for s in sections:
        by_parent.setdefault(s.parent_id, []).append(s)
    for lst in by_parent.values():
        lst.sort(key=lambda s: (s.display_order, s.code))

    nodes: list[Node] = []
    questions: list[QInfo] = []
    columns: list[tuple[UUID, str, str, str]] = []
    skipped = 0

    def walk(parent_id) -> None:
        nonlocal skipped
        for s in by_parent.get(parent_id, []):
            nodes.append(Node(s.id, s.code, s.label, s.type.code if s.type else "?"))
            columns.append((s.id, s.type.code if s.type else "?", s.code, s.label))
            for q in sorted(s.questions, key=lambda q: (q.display_order, q.code)):
                ct = q.card_template
                fields: list[QField] = []
                if ct:
                    for g in sorted(ct.field_groups, key=lambda g: g.display_order):
                        for f in sorted(g.fields, key=lambda f: f.display_order):
                            if f.field_type.code == "file":
                                skipped += 1
                                continue
                            fields.append(
                                QField(
                                    f.id,
                                    f.label,
                                    f.field_type.code,
                                    [
                                        (c.id, c.code, c.label, c.text_input)
                                        for c in sorted(f.field_choices, key=lambda c: c.display_order)
                                    ],
                                )
                            )
                columns.append((q.id, "Q", q.code, q.label))
                questions.append(
                    QInfo(
                        len(questions) + 1,
                        q.id,
                        q.label,
                        q.code,
                        q.is_loop,
                        q.source_question_id,
                        ct.id if ct else None,
                        s.label,
                        fields,
                    )
                )
            walk(s.id)

    walk(None)
    return Structure(form, nodes, questions, skipped, columns)


# ---------------------------------------------------------------------------- utilidades Excel


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _append_entities_sheet(wb: Workbook, actors) -> None:
    ent = wb.create_sheet("Entidades")
    ent.append(["actor_id", "código", "nombre"])
    for a in actors:
        ent.append([str(a.id), a.code, a.label])
    for c in ent[1]:
        c.font = _BOLD
    ent.column_dimensions["A"].width = 40
    ent.column_dimensions["C"].width = 60


def _choice_text_key(field_id: UUID, choice_id: UUID) -> str:
    return f"choice_text:{field_id}:{choice_id}"


def _parse_choice_text_key(key: str) -> tuple[str, UUID] | None:
    if not key.startswith("choice_text:"):
        return None
    parts = key.split(":")
    if len(parts) != 3:
        return None
    try:
        return parts[1], UUID(parts[2])
    except ValueError:
        return None


def _multi_choice_comment(f: QField) -> Comment | None:
    if f.type != "multi_choice" or not f.choices:
        return None
    lines = ["Opciones válidas (separe varias con «;»):"]
    for _, _, lab, ti in f.choices:
        lines.append(f"• {lab}" + (" [texto adicional al lado]" if ti else ""))
    comment = Comment("\n".join(lines), "IIP")
    comment.width = 320
    comment.height = max(80, 22 * len(lines))
    return comment


def _header(ws, labels: list[str], keys: list[str]) -> None:
    ws.append(labels)
    ws.append(keys)
    ws.row_dimensions[2].hidden = True
    for cell in ws[1]:
        cell.font = _BOLD
        cell.fill = _HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[1].height = 60
    ws.freeze_panes = "B3"
    for i in range(1, len(labels) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 38 if i > 1 else 40


def _read_table(ws) -> tuple[list[str], list[str], list[tuple[int, list[Any]]]]:
    """(rótulos, claves, filas con datos) — rótulos en la fila 1, claves en la 2, datos desde la 3."""
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise HistoricalFileError("La hoja no tiene las filas de encabezado de la plantilla.")
    labels = ["" if v is None else str(v) for v in rows[0]]
    keys = ["" if v is None else str(v).strip() for v in rows[1]]
    data = [
        (i, list(r))
        for i, r in enumerate(rows[2:], start=3)
        if not all(_blank(v) for v in r)
    ]
    return labels, keys, data


def _open(data: bytes):
    try:
        return load_workbook(io.BytesIO(data), data_only=True)
    except Exception as exc:  # noqa: BLE001 - archivo ajeno / corrupto
        raise HistoricalFileError("No se pudo leer el archivo: debe ser un Excel (.xlsx).") from exc


def _meta(wb, form_id: UUID) -> dict[str, str]:
    """Hoja oculta `_meta`: garantiza que la plantilla pertenece a este formulario."""
    if _META_SHEET not in wb.sheetnames:
        raise HistoricalFileError("El archivo no es una plantilla generada por el sistema.")
    rows = [r for r in wb[_META_SHEET].iter_rows(values_only=True) if r and r[0]]
    meta = {str(r[0]): str(r[1]) for r in rows if len(r) > 1 and r[1] is not None}
    if meta.get("form_id") != str(form_id):
        raise HistoricalFileError(
            "La plantilla fue generada para otro formulario. Descargue la plantilla de este formulario."
        )
    return meta


class _Issues:
    def __init__(self) -> None:
        self.errors: list[ResponseHistoricalIssue] = []
        self.warnings: list[ResponseHistoricalIssue] = []

    def error(self, sheet: str, row: int | None, column: str | None, message: str) -> None:
        self.errors.append(ResponseHistoricalIssue(sheet=sheet, row=row, column=column, message=message))

    def warn(self, sheet: str, row: int | None, column: str | None, message: str) -> None:
        self.warnings.append(ResponseHistoricalIssue(sheet=sheet, row=row, column=column, message=message))


def _structure_hash(st: Structure, kind: str) -> str:
    h = hashlib.sha256()
    h.update(kind.encode())
    if kind == "responses":
        for q in st.questions:
            if not q.fields or (q.is_loop and not q.template_id):
                continue
            h.update(f"|Q:{q.id}:{int(q.is_loop)}:{q.source_id or ''}".encode())
            for f in q.fields:
                h.update(f"|F:{f.id}:{f.type}".encode())
                for cid, _, _, ti in f.choices:
                    if ti is not None:
                        h.update(f"|CT:{cid}".encode())
    else:
        for cid, level, _, _ in st.result_columns:
            h.update(f"|R:{cid}:{level}".encode())
    return h.hexdigest()[:16]


def _validate_sheet_columns(
    issues: _Issues,
    sheet: str,
    labels: list[str],
    keys: list[str],
    expected: dict[str, str],
    fixed: set[str],
) -> None:
    present = set(keys)
    for ci, key in enumerate(keys):
        if not key or key in fixed or key in expected:
            continue
        col_label = (labels[ci] if ci < len(labels) else "").splitlines()[0].strip() or key
        issues.error(
            sheet,
            1,
            get_column_letter(ci + 1),
            f"La columna «{col_label}» ya no existe en el formulario actual.",
        )
    for exp_key, exp_label in expected.items():
        if exp_key not in present:
            issues.error(
                sheet,
                1,
                None,
                f"Falta la columna «{exp_label}» del formulario actual.",
            )


def _actor_id(raw: Any) -> UUID | None:
    try:
        return UUID(str(raw).strip())
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------- conversión de valores


def _to_decimal(raw: Any, max_abs: Decimal = _MAX_ANSWER_NUMERIC) -> Decimal:
    if isinstance(raw, bool):
        raise InvalidOperation
    if isinstance(raw, (int, float)):
        value = Decimal(str(raw))
    else:
        text = str(raw).strip().replace(" ", "")
        if "," in text and "." in text:
            # el último separador es el decimal: 1.234,5 -> 1234.5 ; 1,234.5 -> 1234.5
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        else:
            text = text.replace(",", ".")
        value = Decimal(text)
    if not value.is_finite() or abs(value) > max_abs:
        raise InvalidOperation
    return value


def _to_date(raw: Any) -> date:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(text)


def _convert(f: QField, raw: Any):
    """(item parcial sin field_id, error) para el valor de una celda no vacía."""
    t = f.type
    if t == "boolean":
        if isinstance(raw, bool):
            return raw, None
        v = _norm(raw)
        if v in _YES:
            return True, None
        if v in _NO:
            return False, None
        return None, "Use Sí o No."
    if t == "text":
        return str(raw).strip(), None
    if t == "numeric":
        try:
            return _to_decimal(raw), None
        except (InvalidOperation, ValueError):
            return None, "Número no válido."
    if t == "date":
        try:
            return _to_date(raw), None
        except ValueError:
            return None, "Fecha no válida (use AAAA-MM-DD o DD/MM/AAAA)."
    if t in ("single_choice", "multi_choice"):
        lookup = {}
        for cid, code, label, _ in f.choices:
            lookup[_norm(label)] = cid
            lookup.setdefault(_norm(code), cid)
        parts = [str(raw).strip()] if t == "single_choice" else [
            p for p in re.split(r"[;\n|]", str(raw)) if p.strip()
        ]
        ids, unknown = [], []
        for p in parts:
            cid = lookup.get(_norm(p))
            (ids if cid else unknown).append(cid or p.strip())
        if unknown:
            return None, f"Opción no válida: {', '.join(unknown)}."
        return (ids[0] if t == "single_choice" else list(dict.fromkeys(ids))), None
    return None, f"Tipo de campo no soportado: {t}."


def _answer_item(f: QField, value: Any, choice_texts: dict[UUID, str] | None = None):
    base = {"field_id": f.id}
    if f.type == "boolean":
        return BooleanAnswerIn(type="boolean", value=value, **base)
    if f.type == "numeric":
        return NumericAnswerIn(type="numeric", value=value, **base)
    if f.type == "date":
        return DateAnswerIn(type="date", value=value, **base)
    if f.type == "single_choice":
        other_text = (choice_texts or {}).get(value)
        return SingleChoiceAnswerIn(type="single_choice", value=value, other_text=other_text, **base)
    if f.type == "multi_choice":
        other_texts = {cid: txt for cid, txt in (choice_texts or {}).items() if cid in value} or None
        return MultiChoiceAnswerIn(type="multi_choice", value=value, other_texts=other_texts, **base)
    return TextAnswerIn(type="text", value=value, **base)


# ---------------------------------------------------------------------------- servicio


class HistoricalAppService:
    """Cierre de edición, plantillas Excel y carga masiva de respuestas y resultados históricos."""

    # -------------------------------------------------------------- acceso / carga

    @staticmethod
    async def _admin(session, requester_id: UUID) -> None:
        if not await is_admin(session, requester_id):
            raise HistoricalForbiddenError()

    @staticmethod
    async def _form(session, form_id: UUID) -> Form:
        form = await session.get(Form, form_id)
        if form is None:
            raise FormNotFoundError(f"Form '{form_id}' not found.")
        return form

    async def _structure(self, session, form: Form, *, need_closed: bool = True) -> Structure:
        if need_closed and form.edition_closed_at is None:
            raise FormEditionOpenError()
        sections = await FormRepository(session).list_sections_tree(form.id)
        return _build_structure(form, sections)

    # -------------------------------------------------------------- monitor

    async def list_records(self, requester_id: UUID) -> list[ResponseRecord]:
        """Entidad × formulario con respuestas (radicado) y/o resultados cargados."""
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            sub_rows = (
                await s.execute(SubmissionAppService._summary_query().order_by(Submission.updated_at.desc()))
            ).all()
            res_rows = (
                await s.execute(
                    select(FormResult, Form, Actor)
                    .join(Form, Form.id == FormResult.form_id)
                    .join(Actor, Actor.id == FormResult.actor_id)
                )
            ).all()
            segments = await SubmissionAppService._segment_labels(
                s, {r[2].id for r in sub_rows} | {r[2].id for r in res_rows}
            )

            records: dict[tuple, dict] = {}
            for row in sub_rows:
                base = SubmissionAppService._to_summary(row, segments.get(row[2].id))
                key = (base["form_id"], base["actor_id"])
                if key in records:  # un entidad puede tener varios radicados: se muestra el más reciente
                    continue
                records[key] = dict(
                    form_id=base["form_id"],
                    form_code=base["form_code"],
                    form_label=base["form_label"],
                    form_year=row[1].year,
                    actor_id=base["actor_id"],
                    actor_label=base["actor_label"],
                    actor_segment_label=base["actor_segment_label"],
                    submission_id=base["id"],
                    status=base["status"],
                    updated_at=base["updated_at"],
                    answer_count=base["answer_count"],
                    card_count=base["card_count"],
                )
            for fr, form, actor in res_rows:
                key = (form.id, actor.id)
                rec = records.setdefault(
                    key,
                    dict(
                        form_id=form.id,
                        form_code=form.code,
                        form_label=form.label,
                        form_year=form.year,
                        actor_id=actor.id,
                        actor_label=actor.label,
                        actor_segment_label=segments.get(actor.id),
                        updated_at=fr.updated_at,
                    ),
                )
                rec["has_results"] = True
                rec["total"] = float(fr.total) if fr.total is not None else None
            return [ResponseRecord(**r) for r in records.values()]

    async def entity_results(
        self, requester_id: UUID, form_id: UUID, actor_id: UUID
    ) -> ResponseEntityResults:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            fr = await s.scalar(
                select(FormResult).where(FormResult.form_id == form_id, FormResult.actor_id == actor_id)
            )
            if fr is None:
                return ResponseEntityResults(has_results=False)
            rows = (
                await s.execute(
                    select(SectionResult.section_id, SectionResult.score).where(
                        SectionResult.form_result_id == fr.id
                    )
                )
            ).all()
            q_rows = (
                await s.execute(
                    select(QuestionResult.question_id, QuestionResult.score).where(
                        QuestionResult.form_result_id == fr.id
                    )
                )
            ).all()
            return ResponseEntityResults(
                has_results=True,
                total=float(fr.total) if fr.total is not None else None,
                sections=[
                    ResponseSectionScore(section_id=sid, score=float(sc) if sc is not None else None)
                    for sid, sc in rows
                ],
                questions=[
                    ResponseQuestionScore(question_id=qid, score=float(sc) if sc is not None else None)
                    for qid, sc in q_rows
                ],
                updated_at=fr.updated_at,
            )

    # -------------------------------------------------------------- lista y estado

    async def list_forms(self, requester_id: UUID) -> list[ResponseHistoricalForm]:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            subs = (
                select(Submission.form_id, func.count().label("n"))
                .group_by(Submission.form_id)
                .subquery()
            )
            res = (
                select(FormResult.form_id, func.count().label("n"))
                .group_by(FormResult.form_id)
                .subquery()
            )
            rows = (
                await s.execute(
                    select(Form, func.coalesce(subs.c.n, 0), func.coalesce(res.c.n, 0))
                    .outerjoin(subs, subs.c.form_id == Form.id)
                    .outerjoin(res, res.c.form_id == Form.id)
                    .order_by(Form.year.desc().nulls_last(), Form.code)
                )
            ).all()
            return [
                ResponseHistoricalForm(
                    id=f.id,
                    code=f.code,
                    label=f.label,
                    year=f.year,
                    is_active=f.is_active,
                    edition_closed_at=f.edition_closed_at,
                    submission_count=int(ns),
                    result_count=int(nr),
                )
                for f, ns, nr in rows
            ]

    async def close_edition(self, requester_id: UUID, form_id: UUID) -> ResponseHistoricalForm:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            form = await self._form(s, form_id)
            if form.edition_closed_at is None:
                form.edition_closed_at = datetime.now(timezone.utc)
                form.updated_at = form.edition_closed_at
        return next(f for f in await self.list_forms(requester_id) if str(f.id) == str(form_id))

    async def reopen_edition(self, requester_id: UUID, form_id: UUID) -> ResponseHistoricalForm:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            form = await self._form(s, form_id)
            has_data = await s.scalar(
                select(
                    or_(
                        select(Submission.id).where(Submission.form_id == form_id).exists(),
                        select(FormResult.id).where(FormResult.form_id == form_id).exists(),
                    )
                )
            )
            if has_data:
                raise FormEditionHasDataError()
            form.edition_closed_at = None
            form.updated_at = datetime.now(timezone.utc)
        return next(f for f in await self.list_forms(requester_id) if str(f.id) == str(form_id))

    # -------------------------------------------------------------- plantilla de respuestas

    async def responses_template(self, requester_id: UUID, form_id: UUID) -> tuple[str, bytes]:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            form = await self._form(s, form_id)
            st = await self._structure(s, form)
            actors = (await s.execute(select(Actor.id, Actor.code, Actor.label).order_by(Actor.label))).all()

        wb = Workbook()
        info = wb.active
        info.title = "Instrucciones"
        lists = wb.create_sheet(_LISTS_SHEET)
        meta = wb.create_sheet(_META_SHEET)
        meta.append(["form_id", str(form.id)])
        meta.append(["kind", "responses"])
        meta.append(["structure_hash", _structure_hash(st, "responses")])
        if form.edition_closed_at:
            meta.append(["edition_closed_at", form.edition_closed_at.isoformat()])

        simple = [q for q in st.questions if not q.is_loop and q.fields]
        loops = [q for q in st.questions if q.is_loop and q.fields and q.template_id]
        by_id = {q.id: q for q in st.questions}

        # --- hoja de preguntas simples
        ws = wb.create_sheet(_RESPONSES_SHEET)
        labels, keys = ["actor_id (ID de la entidad)"], ["actor_id"]
        list_col = 0

        def validation(sheet, f: QField, col_idx: int) -> None:
            nonlocal list_col
            if f.type == "boolean":
                dv = DataValidation(type="list", formula1='"Sí,No"', allow_blank=True)
            elif f.type == "single_choice" and f.choices:
                list_col += 1
                letter = get_column_letter(list_col)
                lists.cell(row=1, column=list_col, value=f.label)
                for i, (_, _, lab, _) in enumerate(f.choices, start=2):
                    lists.cell(row=i, column=list_col, value=lab)
                dv = DataValidation(
                    type="list",
                    formula1=f"={_LISTS_SHEET}!${letter}$2:${letter}${len(f.choices) + 1}",
                    allow_blank=True,
                )
            elif f.type == "multi_choice":
                comment = _multi_choice_comment(f)
                if comment:
                    sheet.cell(row=1, column=col_idx).comment = comment
                return
            else:
                return
            dv.error = "Valor fuera de la lista"
            sheet.add_data_validation(dv)
            col = get_column_letter(col_idx)
            dv.add(f"{col}3:{col}5000")

        for q in simple:
            for f in q.fields:
                extra = f" — {f.label}" if len(q.fields) > 1 else ""
                hint = {"multi_choice": " (varias opciones separadas por «;»)", "date": " (AAAA-MM-DD)"}.get(f.type, "")
                base_hdr = f"P{q.n} · {q.label}{extra}"
                labels.append(f"{base_hdr}{hint}\n[{q.indicator_label}]")
                keys.append(str(f.id))
                for cid, _, clab, ti in f.choices:
                    if ti is not None:
                        labels.append(f"{base_hdr} — Texto «{clab}»\n[{q.indicator_label}]")
                        keys.append(_choice_text_key(f.id, cid))
        _header(ws, labels, keys)
        col = 2
        for q in simple:
            for f in q.fields:
                validation(ws, f, col)
                col += 1 + sum(1 for _, _, _, ti in f.choices if ti is not None)

        # --- una hoja por pregunta bucle
        mapping: list[tuple[str, str]] = []
        for q in loops:
            lws = wb.create_sheet(q.sheet)
            src = by_id.get(q.source_id) if q.source_id else None
            llabels = ["actor_id (ID de la entidad)", "ref (identificador de la tarjeta, único por entidad)"]
            lkeys = ["actor_id", "ref"]
            if src:
                llabels.append(f"ref_padre (ref de la tarjeta de la hoja {src.sheet} a la que se refiere)")
                lkeys.append("parent_ref")
            llabels.append("Nombre de la tarjeta *")
            lkeys.append("title")
            field_cols: list[tuple[QField, int]] = []
            for f in q.fields:
                hint = {"multi_choice": " (varias separadas por «;»)", "date": " (AAAA-MM-DD)"}.get(f.type, "")
                field_cols.append((f, len(llabels) + 1))
                llabels.append(f"{f.label}{hint}")
                lkeys.append(str(f.id))
                for cid, _, clab, ti in f.choices:
                    if ti is not None:
                        llabels.append(f"{f.label} — Texto «{clab}»")
                        lkeys.append(_choice_text_key(f.id, cid))
            _header(lws, llabels, lkeys)
            for f, c_idx in field_cols:
                validation(lws, f, c_idx)
            mapping.append((q.sheet, f"P{q.n} · {q.label}" + (f"  (cuelga de {src.sheet})" if src else "")))
            meta.append(["sheet", q.sheet, str(q.id)])

        for sh in (lists, meta):
            sh.sheet_state = "hidden"

        # --- catálogo de opciones (referencia para multi_choice y single_choice)
        opts = wb.create_sheet("Opciones")
        opts.append(["hoja", "pregunta", "campo", "tipo", "opción válida", "texto adicional"])
        for c in opts[1]:
            c.font = _BOLD
            c.fill = _HEAD_FILL
        for q in st.questions:
            sheet_name = q.sheet if q.is_loop else _RESPONSES_SHEET
            for f in q.fields:
                if f.type not in ("single_choice", "multi_choice") or not f.choices:
                    continue
                tlabel = "Selección única" if f.type == "single_choice" else "Selección múltiple (separar con «;»)"
                for _, _, clab, ti in f.choices:
                    extra_txt = "Obligatorio (al lado)" if (ti and ti.is_required) else ("Opcional (al lado)" if ti else "")
                    opts.append([sheet_name, f"P{q.n} · {q.label}", f.label, tlabel, clab, extra_txt])
        for ci, w in enumerate((14, 42, 32, 32, 38, 22), start=1):
            opts.column_dimensions[get_column_letter(ci)].width = w

        # --- entidades de referencia
        _append_entities_sheet(wb, actors)

        # --- instrucciones
        lines = [
            f"Plantilla de RESPUESTAS históricas — formulario {form.code} · {form.label}",
            "",
            "1. En la hoja «Respuestas» escriba una fila por entidad: en la columna A el actor_id (ID de la entidad en la base de datos; la hoja «Entidades» lo lista de referencia) y, en las demás columnas, lo que la entidad respondió en su época.",
            "2. Cada pregunta bucle tiene su propia hoja (P#): una fila por tarjeta, con el actor_id, un «ref» (texto cualquiera, único por entidad dentro de la hoja) y el nombre de la tarjeta.",
            "3. Las hojas de preguntas vinculadas llevan «ref_padre»: el ref de la tarjeta, de la hoja de la pregunta origen y de la misma entidad, a la que se refiere.",
            "4. Deje en blanco lo que la entidad no respondió. No se exigen campos obligatorios ni se validan pesos.",
            "5. Sí/No: escriba «Sí» o «No». Opciones: use el texto de la lista. Opción múltiple: sepárelas con «;». Fechas: AAAA-MM-DD o DD/MM/AAAA.",
            "6. No cambie ni borre las filas 1 y 2 (la 2 está oculta) ni las hojas ocultas.",
            "7. Antes de guardar, el sistema valida el archivo y muestra un reporte; si hay errores no se guarda nada.",
        ]
        if st.skipped_files:
            lines.append(
                f"8. {st.skipped_files} campo(s) de tipo archivo no se incluyen: los archivos no se cargan por Excel."
            )
        lines += ["", "Hojas de preguntas bucle:"] + [f"   {sh} → {desc}" for sh, desc in mapping]
        for ln in lines:
            info.append([ln])
        info["A1"].font = Font(bold=True, size=13)
        info.column_dimensions["A"].width = 140

        return f"plantilla_respuestas_{form.code}.xlsx", self._bytes(wb)

    # -------------------------------------------------------------- plantilla de resultados

    async def results_template(self, requester_id: UUID, form_id: UUID) -> tuple[str, bytes]:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            form = await self._form(s, form_id)
            st = await self._structure(s, form)
            actors = (await s.execute(select(Actor.id, Actor.code, Actor.label).order_by(Actor.label))).all()

        wb = Workbook()
        info = wb.active
        info.title = "Instrucciones"
        ws = wb.create_sheet(_RESULTS_SHEET)
        meta = wb.create_sheet(_META_SHEET)
        meta.append(["form_id", str(form.id)])
        meta.append(["kind", "results"])
        meta.append(["structure_hash", _structure_hash(st, "results")])
        if form.edition_closed_at:
            meta.append(["edition_closed_at", form.edition_closed_at.isoformat()])
        meta.sheet_state = "hidden"

        labels, keys = ["actor_id (ID de la entidad)"], ["actor_id"]
        for cid, level, code, label in st.result_columns:
            labels.append(f"{_LEVEL.get(level, level)} {code}\n{label}")
            keys.append(str(cid))
        labels.append("TOTAL")
        keys.append("TOTAL")
        _header(ws, labels, keys)
        _append_entities_sheet(wb, actors)

        for ln in [
            f"Plantilla de RESULTADOS históricos — formulario {form.code} · {form.label}",
            "",
            "1. Una fila por entidad: en la columna A el actor_id (ID de la entidad en la base de datos).",
            "2. Escriba el puntaje de la entidad en cada componente, variable, indicador y pregunta, y el TOTAL, tal como se presentó en su época.",
            "   Las columnas siguen el orden del formulario: componente, variable, indicador y, a continuación, las preguntas de ese indicador.",
            "3. No se valida contra los pesos del formulario ni se exige que los niveles sumen: se guarda tal cual.",
            "4. Deje en blanco lo que no tenga resultado. Admite decimales con punto o coma.",
            "5. Si la entidad ya tiene resultados para este formulario, la carga los reemplaza por completo.",
            "6. No cambie ni borre las filas 1 y 2 (la 2 está oculta) ni la hoja oculta.",
        ]:
            info.append([ln])
        info["A1"].font = Font(bold=True, size=13)
        info.column_dimensions["A"].width = 140

        return f"plantilla_resultados_{form.code}.xlsx", self._bytes(wb)

    @staticmethod
    def _bytes(wb) -> bytes:
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    # -------------------------------------------------------------- carga de respuestas

    async def load_responses(
        self, requester_id: UUID, form_id: UUID, data: bytes, *, dry_run: bool, replace: bool
    ) -> ResponseHistoricalReport:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            form = await self._form(s, form_id)
            st = await self._structure(s, form)
            wb = _open(data)
            meta = _meta(wb, form.id)
            if meta.get("kind") == "results":
                raise HistoricalFileError("Este archivo es la plantilla de resultados, no la de respuestas.")

            issues = _Issues()
            expected_hash = _structure_hash(st, "responses")
            if meta.get("structure_hash") and meta.get("structure_hash") != expected_hash:
                issues.error(
                    _META_SHEET,
                    None,
                    None,
                    "El formulario cambió desde la última generación de esta plantilla; descárguela nuevamente.",
                )
            by_sheet = {q.sheet: q for q in st.questions if q.is_loop and q.fields and q.template_id}
            by_id = {q.id: q for q in st.questions}
            simple = [q for q in st.questions if not q.is_loop and q.fields]
            field_of = {str(f.id): (q, f) for q in st.questions for f in q.fields}

            known = {
                row[0]
                for row in (await s.execute(select(Actor.id))).all()
            }
            first_seen: dict[UUID, tuple[str, int]] = {}
            items_by_actor: dict[UUID, list] = {}
            counters = {"answers": 0, "cards": 0}

            def actor_of(sheet: str, row: int, raw: Any) -> UUID | None:
                aid = _actor_id(raw)
                if aid is None:
                    issues.error(sheet, row, "actor_id", "actor_id vacío o no es un UUID válido.")
                    return None
                if aid not in known:
                    issues.error(sheet, row, "actor_id", f"La entidad {aid} no existe en la base de datos.")
                    return None
                first_seen.setdefault(aid, (sheet, row))
                return aid

            def extract_row_answers(sheet_name: str, rownum: int, row_keys: list[str], cells: list[Any], scope_q_id: UUID | None = None) -> list:
                row_choice_texts: dict[str, list[tuple[UUID, int, str]]] = {}
                for ci, key in enumerate(row_keys):
                    parsed_ct = _parse_choice_text_key(key)
                    if not parsed_ct:
                        continue
                    fid_str, cid = parsed_ct
                    raw_txt = cells[ci] if ci < len(cells) else None
                    if not _blank(raw_txt):
                        row_choice_texts.setdefault(fid_str, []).append((cid, ci, str(raw_txt).strip()))

                row_items = []
                seen_fields: set[str] = set()
                for ci, key in enumerate(row_keys):
                    raw = cells[ci] if ci < len(cells) else None
                    hit = field_of.get(key)
                    if hit is None:
                        continue
                    if scope_q_id is not None and hit[0].id != scope_q_id:
                        continue
                    seen_fields.add(key)
                    if _blank(raw):
                        for cid, tcol, _ in row_choice_texts.get(key, []):
                            issues.error(
                                sheet_name,
                                rownum,
                                get_column_letter(tcol + 1),
                                "Escribió texto adicional pero no seleccionó la opción correspondiente.",
                            )
                        continue
                    value, err = _convert(hit[1], raw)
                    if err:
                        issues.error(sheet_name, rownum, get_column_letter(ci + 1), err)
                        continue
                    chosen_ids = {value} if hit[1].type == "single_choice" else (set(value) if hit[1].type == "multi_choice" else set())
                    ti_by_cid = {c_id: ti for c_id, _, _, ti in hit[1].choices if ti is not None}
                    valid_texts: dict[UUID, str] = {}
                    for cid, tcol, txt in row_choice_texts.get(key, []):
                        if cid not in chosen_ids:
                            issues.error(
                                sheet_name,
                                rownum,
                                get_column_letter(tcol + 1),
                                "Escribió texto adicional para una opción que no fue seleccionada.",
                            )
                            continue
                        ti = ti_by_cid.get(cid)
                        if ti is None:
                            issues.error(
                                sheet_name,
                                rownum,
                                get_column_letter(tcol + 1),
                                "Esta opción no admite texto adicional.",
                            )
                            continue
                        if ti.max_length is not None and len(txt) > ti.max_length:
                            issues.error(
                                sheet_name,
                                rownum,
                                get_column_letter(tcol + 1),
                                f"El texto adicional supera el máximo de {ti.max_length} caracteres.",
                            )
                            continue
                        valid_texts[cid] = txt
                    row_items.append(_answer_item(hit[1], value, valid_texts or None))
                return row_items

            # --- hoja Respuestas
            if _RESPONSES_SHEET not in wb.sheetnames:
                raise HistoricalFileError(f"Falta la hoja «{_RESPONSES_SHEET}».")
            labels, keys, rows = _read_table(wb[_RESPONSES_SHEET])
            expected_simple: dict[str, str] = {}
            for q in simple:
                for f in q.fields:
                    expected_simple[str(f.id)] = f"P{q.n} · {q.label}"
                    for cid, _, clab, ti in f.choices:
                        if ti is not None:
                            expected_simple[_choice_text_key(f.id, cid)] = f"P{q.n} · {q.label} — Texto «{clab}»"
            _validate_sheet_columns(issues, _RESPONSES_SHEET, labels, keys, expected_simple, {"actor_id"})
            seen_rows: dict[UUID, int] = {}
            for rownum, cells in rows:
                aid = actor_of(_RESPONSES_SHEET, rownum, cells[0] if cells else None)
                if aid is None:
                    continue
                if aid in seen_rows:
                    issues.error(
                        _RESPONSES_SHEET, rownum, "actor_id",
                        f"La entidad ya aparece en la fila {seen_rows[aid]}: una sola fila por entidad.",
                    )
                    continue
                seen_rows[aid] = rownum
                items = items_by_actor.setdefault(aid, [])
                built = extract_row_answers(_RESPONSES_SHEET, rownum, keys, cells)
                items.extend(built)
                counters["answers"] += len(built)

            # --- hojas de bucles
            refs: dict[tuple[UUID, str], str] = {}  # (actor, "P8:ref") -> ref único
            pending_links: list[tuple[UUID, str, int, QInfo, str]] = []
            cards: dict[UUID, list] = {}
            for sheet, q in by_sheet.items():
                if sheet not in wb.sheetnames:
                    issues.warn(sheet, None, None, "La hoja de esta pregunta bucle no está en el archivo; se omite.")
                    continue
                labels, keys, rows = _read_table(wb[sheet])
                src = by_id.get(q.source_id) if q.source_id else None
                expected_loop: dict[str, str] = {}
                for f in q.fields:
                    expected_loop[str(f.id)] = f.label
                    for cid, _, clab, ti in f.choices:
                        if ti is not None:
                            expected_loop[_choice_text_key(f.id, cid)] = f"{f.label} — Texto «{clab}»"
                fixed_loop = {"actor_id", "ref", "title"} | ({"parent_ref"} if src else set())
                _validate_sheet_columns(issues, sheet, labels, keys, expected_loop, fixed_loop)
                col = {k: i for i, k in enumerate(keys) if k}
                if "actor_id" not in col or "title" not in col:
                    raise HistoricalFileError(f"La hoja {sheet} no tiene las columnas esperadas de la plantilla.")
                local_refs: set[tuple[UUID, str]] = set()
                for rownum, cells in rows:
                    get = lambda k: cells[col[k]] if k in col and col[k] < len(cells) else None  # noqa: E731
                    aid = actor_of(sheet, rownum, get("actor_id"))
                    if aid is None:
                        continue
                    title = get("title")
                    if _blank(title):
                        issues.error(sheet, rownum, get_column_letter(col["title"] + 1), "El nombre de la tarjeta es obligatorio.")
                        continue
                    ref_raw = get("ref")
                    ref = str(ref_raw).strip() if not _blank(ref_raw) else f"#fila{rownum}"
                    if len(ref) > 40:
                        issues.error(sheet, rownum, "ref", "El ref es demasiado largo (máx. 40 caracteres).")
                        continue
                    if (aid, ref) in local_refs:
                        issues.error(sheet, rownum, "ref", f"El ref «{ref}» está repetido para esta entidad.")
                        continue
                    local_refs.add((aid, ref))
                    parent = None
                    if src:
                        p_raw = get("parent_ref")
                        if _blank(p_raw):
                            issues.error(sheet, rownum, "ref_padre", f"Indique el ref de la tarjeta de la hoja {src.sheet} a la que se refiere.")
                            continue
                        parent = f"{src.sheet}:{str(p_raw).strip()}"
                        pending_links.append((aid, parent, rownum, q, sheet))
                    answers = extract_row_answers(sheet, rownum, keys, cells, scope_q_id=q.id)
                    own = f"{sheet}:{ref}"
                    refs[(aid, own)] = own
                    cards.setdefault(aid, []).append(
                        CardEntryAnswerIn(
                            type="card_entry",
                            field_id=q.fields[0].id,
                            question_id=q.id,
                            card_template_id=q.template_id,
                            title=str(title).strip()[:255],
                            card_index=len(cards.get(aid, [])),
                            ref=own,
                            parent_ref=parent,
                            answers=answers,
                        )
                    )
                    counters["cards"] += 1
                    items_by_actor.setdefault(aid, [])

            for aid, parent, rownum, q, sheet in pending_links:
                if (aid, parent) not in refs:
                    issues.error(
                        sheet, rownum, "ref_padre",
                        f"No existe la tarjeta «{parent.split(':', 1)[1]}» de esta entidad en la hoja {parent.split(':', 1)[0]}.",
                    )

            for aid, lst in cards.items():
                items_by_actor[aid].extend(lst)

            # --- radicados existentes
            existing = {}
            if items_by_actor:
                existing = {
                    r.actor_id: r.id
                    for r in (
                        await s.execute(
                            select(Submission.actor_id, Submission.id)
                            .where(Submission.form_id == form.id, Submission.actor_id.in_(items_by_actor.keys()))
                        )
                    ).all()
                }
            for aid in existing:
                sheet, row = first_seen.get(aid, (_RESPONSES_SHEET, None))
                if replace:
                    issues.warn(sheet, row, "actor_id", "La entidad ya tenía respuestas para este formulario: se reemplazarán.")
                else:
                    issues.error(sheet, row, "actor_id", "La entidad ya tiene respuestas para este formulario. Marque «Reemplazar» para sustituirlas.")

            summary = {
                "entidades": len(items_by_actor),
                "respuestas": counters["answers"],
                "tarjetas": counters["cards"],
                "reemplazos": len(existing) if replace else 0,
            }
            if dry_run or issues.errors:
                return ResponseHistoricalReport(
                    dry_run=dry_run, committed=False, errors=issues.errors, warnings=issues.warnings, summary=summary
                )

            # --- escritura (una sola transacción)
            status_id = await s.scalar(
                select(SubmissionStatusType.id).where(SubmissionStatusType.code == SubmissionStatusesEnum.SUBMITTED.code)
            )
            if existing:
                sub_ids = list(existing.values())
                await s.execute(delete(Grade).where(Grade.submission_id.in_(sub_ids)))
                await s.execute(delete(Submission).where(Submission.id.in_(sub_ids)))
                await s.flush()
            builder = SubmissionService()
            for aid, items in items_by_actor.items():
                s.add(builder.build_submission(aid, form.id, status_id, items))
            await s.flush()
            return ResponseHistoricalReport(
                dry_run=False, committed=True, errors=[], warnings=issues.warnings, summary=summary
            )

    # -------------------------------------------------------------- carga de resultados

    async def load_results(
        self, requester_id: UUID, form_id: UUID, data: bytes, *, dry_run: bool
    ) -> ResponseHistoricalReport:
        async with UnitOfWork() as uow:
            s = uow.session
            await self._admin(s, requester_id)
            form = await self._form(s, form_id)
            st = await self._structure(s, form)
            wb = _open(data)
            meta = _meta(wb, form.id)
            if meta.get("kind") == "responses":
                raise HistoricalFileError("Este archivo es la plantilla de respuestas, no la de resultados.")
            if _RESULTS_SHEET not in wb.sheetnames:
                raise HistoricalFileError(f"Falta la hoja «{_RESULTS_SHEET}».")

            issues = _Issues()
            expected_hash = _structure_hash(st, "results")
            if meta.get("structure_hash") and meta.get("structure_hash") != expected_hash:
                issues.error(
                    _META_SHEET,
                    None,
                    None,
                    "El formulario cambió desde la última generación de esta plantilla; descárguela nuevamente.",
                )
            node_ids = {str(n.id) for n in st.nodes}
            question_ids = {str(q.id) for q in st.questions}
            known = {row[0] for row in (await s.execute(select(Actor.id))).all()}
            labels, keys, rows = _read_table(wb[_RESULTS_SHEET])
            if "actor_id" not in keys:
                raise HistoricalFileError("La hoja de resultados no tiene la columna actor_id.")
            expected_results = {
                str(cid): f"{_LEVEL.get(level, level)} {code} · {lab}"
                for cid, level, code, lab in st.result_columns
            }
            expected_results["TOTAL"] = "TOTAL"
            _validate_sheet_columns(issues, _RESULTS_SHEET, labels, keys, expected_results, {"actor_id"})
            a_col = keys.index("actor_id")

            parsed: dict[UUID, dict[str, Decimal | None]] = {}
            seen_rows: dict[UUID, int] = {}
            for rownum, cells in rows:
                aid = _actor_id(cells[a_col] if a_col < len(cells) else None)
                if aid is None:
                    issues.error(_RESULTS_SHEET, rownum, "actor_id", "actor_id vacío o no es un UUID válido.")
                    continue
                if aid not in known:
                    issues.error(_RESULTS_SHEET, rownum, "actor_id", f"La entidad {aid} no existe en la base de datos.")
                    continue
                if aid in seen_rows:
                    issues.error(_RESULTS_SHEET, rownum, "actor_id", f"La entidad ya aparece en la fila {seen_rows[aid]}: una sola fila por entidad.")
                    continue
                seen_rows[aid] = rownum
                values: dict[str, Decimal | None] = {}
                for ci, key in enumerate(keys):
                    if key == "actor_id" or not key or (key != "TOTAL" and key not in node_ids and key not in question_ids):
                        continue
                    raw = cells[ci] if ci < len(cells) else None
                    if _blank(raw):
                        continue
                    try:
                        values[key] = _to_decimal(raw, max_abs=_MAX_RESULT_NUMERIC)
                    except (InvalidOperation, ValueError):
                        issues.error(_RESULTS_SHEET, rownum, get_column_letter(ci + 1), "Número no válido o fuera de rango.")
                parsed[aid] = values

            existing = {}
            if parsed:
                existing = {
                    r.actor_id: r.id
                    for r in (
                        await s.execute(
                            select(FormResult.actor_id, FormResult.id)
                            .where(FormResult.form_id == form.id, FormResult.actor_id.in_(parsed.keys()))
                        )
                    ).all()
                }
            for aid in existing:
                issues.warn(_RESULTS_SHEET, seen_rows.get(aid), "actor_id", "La entidad ya tenía resultados para este formulario: se reemplazarán.")

            summary = {
                "entidades": len(parsed),
                "valores": sum(len(v) for v in parsed.values()),
                "reemplazos": len(existing),
            }
            if dry_run or issues.errors:
                return ResponseHistoricalReport(
                    dry_run=dry_run, committed=False, errors=issues.errors, warnings=issues.warnings, summary=summary
                )

            if existing:
                await s.execute(delete(FormResult).where(FormResult.id.in_(list(existing.values()))))
                await s.flush()
            for aid, values in parsed.items():
                fr = FormResult(form_id=form.id, actor_id=aid, total=values.get("TOTAL"))
                fr.sections = [
                    SectionResult(section_id=UUID(k), score=v)
                    for k, v in values.items()
                    if k in node_ids
                ]
                fr.questions = [
                    QuestionResult(question_id=UUID(k), score=v)
                    for k, v in values.items()
                    if k in question_ids
                ]
                s.add(fr)
            await s.flush()
            return ResponseHistoricalReport(
                dry_run=False, committed=True, errors=[], warnings=issues.warnings, summary=summary
            )
