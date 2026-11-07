"""
Carga de datos históricos (2019-2025) a partir de plantillas Excel generadas desde un
formulario con la edición cerrada:

- Plantilla de respuestas: lo que cada entidad contestó en su época (una fila por entidad en la
  hoja «Respuestas» y una hoja por pregunta bucle con una fila por tarjeta).
- Plantilla de resultados: el puntaje de cada entidad por componente, variable e indicador y el
  total. NO se valida contra los pesos del formulario: son valores ya presentados en su época.

La entidad se identifica por su `actor_id` (el de la base de datos). Antes de guardar se puede
validar el archivo (`dry_run`): devuelve el reporte de errores sin escribir nada.
"""

import io
import re
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from openpyxl import Workbook, load_workbook
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
from domain.services.submissions import SubmissionService
from infrastructure.repositories.forms import FormRepository
from schemas.historical import (
    ResponseHistoricalForm,
    ResponseHistoricalIssue,
    ResponseHistoricalReport,
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
_MAX_NUMERIC = Decimal("99999999999")  # numeric(14,4): 10 enteros
_YES = {"si", "sí", "s", "yes", "y", "true", "verdadero", "1"}
_NO = {"no", "n", "false", "falso", "0"}
_LEVEL = {"C": "Componente", "V": "Variable", "I": "Indicador"}

_HEAD_FILL = PatternFill("solid", fgColor="E0E7FF")
_BOLD = Font(bold=True)


# ---------------------------------------------------------------------------- estructura


@dataclass
class QField:
    id: UUID
    label: str
    type: str
    choices: list = dc_field(default_factory=list)  # [(id, code, label)]


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


def _build_structure(form: Form, sections: list) -> Structure:
    by_parent: dict[Any, list] = {}
    for s in sections:
        by_parent.setdefault(s.parent_id, []).append(s)
    for lst in by_parent.values():
        lst.sort(key=lambda s: (s.display_order, s.code))

    nodes: list[Node] = []
    questions: list[QInfo] = []
    skipped = 0

    def walk(parent_id) -> None:
        nonlocal skipped
        for s in by_parent.get(parent_id, []):
            nodes.append(Node(s.id, s.code, s.label, s.type.code if s.type else "?"))
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
                                        (c.id, c.code, c.label)
                                        for c in sorted(f.field_choices, key=lambda c: c.display_order)
                                    ],
                                )
                            )
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
    return Structure(form, nodes, questions, skipped)


# ---------------------------------------------------------------------------- utilidades Excel


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


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


def _actor_id(raw: Any) -> UUID | None:
    try:
        return UUID(str(raw).strip())
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------- conversión de valores


def _to_decimal(raw: Any) -> Decimal:
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
    if not value.is_finite() or abs(value) > _MAX_NUMERIC:
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
        for cid, code, label in f.choices:
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


def _answer_item(f: QField, value: Any):
    base = {"field_id": f.id}
    if f.type == "boolean":
        return BooleanAnswerIn(type="boolean", value=value, **base)
    if f.type == "numeric":
        return NumericAnswerIn(type="numeric", value=value, **base)
    if f.type == "date":
        return DateAnswerIn(type="date", value=value, **base)
    if f.type == "single_choice":
        return SingleChoiceAnswerIn(type="single_choice", value=value, **base)
    if f.type == "multi_choice":
        return MultiChoiceAnswerIn(type="multi_choice", value=value, **base)
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
                for i, (_, _, lab) in enumerate(f.choices, start=2):
                    lists.cell(row=i, column=list_col, value=lab)
                dv = DataValidation(
                    type="list",
                    formula1=f"={_LISTS_SHEET}!${letter}$2:${letter}${len(f.choices) + 1}",
                    allow_blank=True,
                )
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
                labels.append(f"P{q.n} · {q.label}{extra}{hint}\n[{q.indicator_label}]")
                keys.append(str(f.id))
        _header(ws, labels, keys)
        col = 2
        for q in simple:
            for f in q.fields:
                validation(ws, f, col)
                col += 1

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
            for f in q.fields:
                hint = {"multi_choice": " (varias separadas por «;»)", "date": " (AAAA-MM-DD)"}.get(f.type, "")
                llabels.append(f"{f.label}{hint}")
                lkeys.append(str(f.id))
            _header(lws, llabels, lkeys)
            base = 2 + (1 if src else 0) + 1
            for i, f in enumerate(q.fields):
                validation(lws, f, base + i + 1)
            mapping.append((q.sheet, f"P{q.n} · {q.label}" + (f"  (cuelga de {src.sheet})" if src else "")))
            meta.append(["sheet", q.sheet, str(q.id)])

        for sh in (lists, meta):
            sh.sheet_state = "hidden"

        # --- entidades de referencia
        ent = wb.create_sheet("Entidades")
        ent.append(["actor_id", "código", "nombre"])
        for a in actors:
            ent.append([str(a.id), a.code, a.label])
        for c in ent[1]:
            c.font = _BOLD
        ent.column_dimensions["A"].width = 40
        ent.column_dimensions["C"].width = 60

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

        wb = Workbook()
        info = wb.active
        info.title = "Instrucciones"
        ws = wb.create_sheet(_RESULTS_SHEET)
        meta = wb.create_sheet(_META_SHEET)
        meta.append(["form_id", str(form.id)])
        meta.append(["kind", "results"])
        meta.sheet_state = "hidden"

        labels, keys = ["actor_id (ID de la entidad)"], ["actor_id"]
        for n in st.nodes:
            labels.append(f"{_LEVEL.get(n.level, n.level)} {n.code}\n{n.label}")
            keys.append(str(n.id))
        labels.append("TOTAL")
        keys.append("TOTAL")
        _header(ws, labels, keys)

        for ln in [
            f"Plantilla de RESULTADOS históricos — formulario {form.code} · {form.label}",
            "",
            "1. Una fila por entidad: en la columna A el actor_id (ID de la entidad en la base de datos).",
            "2. Escriba el puntaje de la entidad en cada componente, variable e indicador y el TOTAL, tal como se presentó en su época.",
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

            # --- hoja Respuestas
            if _RESPONSES_SHEET not in wb.sheetnames:
                raise HistoricalFileError(f"Falta la hoja «{_RESPONSES_SHEET}».")
            labels, keys, rows = _read_table(wb[_RESPONSES_SHEET])
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
                for ci in range(1, len(keys)):
                    raw = cells[ci] if ci < len(cells) else None
                    hit = field_of.get(keys[ci])
                    if hit is None:
                        continue
                    if _blank(raw):
                        continue
                    value, err = _convert(hit[1], raw)
                    if err:
                        issues.error(_RESPONSES_SHEET, rownum, get_column_letter(ci + 1), err)
                        continue
                    items.append(_answer_item(hit[1], value))
                    counters["answers"] += 1

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
                    answers = []
                    for ci, key in enumerate(keys):
                        hit = field_of.get(key)
                        raw = cells[ci] if ci < len(cells) else None
                        if hit is None or hit[0].id != q.id or _blank(raw):
                            continue
                        value, err = _convert(hit[1], raw)
                        if err:
                            issues.error(sheet, rownum, get_column_letter(ci + 1), err)
                            continue
                        answers.append(_answer_item(hit[1], value))
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
            node_ids = {str(n.id) for n in st.nodes}
            known = {row[0] for row in (await s.execute(select(Actor.id))).all()}
            labels, keys, rows = _read_table(wb[_RESULTS_SHEET])
            if "actor_id" not in keys:
                raise HistoricalFileError("La hoja de resultados no tiene la columna actor_id.")
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
                    if key == "actor_id" or not key or (key != "TOTAL" and key not in node_ids):
                        continue
                    raw = cells[ci] if ci < len(cells) else None
                    if _blank(raw):
                        continue
                    try:
                        values[key] = _to_decimal(raw)
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
                    SectionResult(section_id=UUID(k), score=v) for k, v in values.items() if k != "TOTAL"
                ]
                s.add(fr)
            await s.flush()
            return ResponseHistoricalReport(
                dry_run=False, committed=True, errors=[], warnings=issues.warnings, summary=summary
            )
