"""Poblado de forms.sections desde Estructura_IIP.xlsx.

Carga la jerarquía:
    COMPONENTE -> VARIABLE -> INDICADOR

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva los UUID existentes basándose en estrategias
de coincidencia por código técnico, labels y jerarquías parentales.
"""

import asyncio
import os
from collections import OrderedDict
from pathlib import Path

import pandas as pd

# Infraestructura y Registro global
from shared.infrastructure import async_engine

# Importación de Modelos ORM Centralizados desde tu Módulo init
from shared.models import Form, Section, SectionType
from shared.utils.logger import get_logger

# Utilidades Core de Seeding Compartidas (Elimina duplicación)
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    clean_text,
    compute_hierarchical_order,
    extract_numeric_suffix,
    fold_for_comparison,
    get_seeding_active_years,
    get_table_columns,
    load_clean_excel_sheet,
    new_uuidv7,
    truncate_text,
    validate_required_columns,
)
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN ESPECÍFICA DE ÁMBITO
# -----------------------------------------------------------------------------

LOCAL_IIP_STRUCTURE_FILE = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

SECTION_LEVELS = ("COMPONENTE", "VARIABLE", "INDICADOR")

LEVEL_ORDER = {
    "COMPONENTE": 1,
    "VARIABLE": 2,
    "INDICADOR": 3,
}

PARENT_LEVEL = {
    "COMPONENTE": None,
    "VARIABLE": "COMPONENTE",
    "INDICADOR": "VARIABLE",
}

DISPLAY_PREFIX = {
    "COMPONENTE": "Componente",
    "VARIABLE": "Variable",
    "INDICADOR": "Indicador",
}

# -----------------------------------------------------------------------------
# IDENTIFICADORES TÉCNICOS Y TRATAMIENTO LOCAL
# -----------------------------------------------------------------------------


def make_code(prefix: str, raw_code) -> str:
    """Construye un código técnico interno estable: C1, V2, I3, etc."""
    suffix = extract_numeric_suffix(raw_code)
    if suffix:
        return f"{prefix}{suffix}"

    folded = fold_for_comparison(raw_code) or "sin_codigo"
    import re

    cleaned = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    return f"{prefix}{cleaned}"


def make_section_label(level: str, raw_code) -> str:
    """Construye el label visible: Componente 1, Variable 1, Indicador 1."""
    suffix = extract_numeric_suffix(raw_code)
    if suffix:
        readable_suffix = suffix.replace("_", ".")
        return f"{DISPLAY_PREFIX[level]} {readable_suffix}"

    cleaned_raw = clean_text(raw_code)
    if cleaned_raw is None:
        raise ValueError(f"No se pudo construir label para {level}: {raw_code!r}")
    return cleaned_raw


# -----------------------------------------------------------------------------
# EXCEL EXTRACT-TRANSFORM-LOAD (ETL)
# -----------------------------------------------------------------------------


def required_columns_for_year(year: int) -> dict[str, str]:
    return {
        "component_code": "Componente",
        "component_description": f"Componente {year}",
        "variable_code": "Variable",
        "variable_description": f"Variable {year}",
        "indicator_code": "Indicador",
        "indicator_description": f"Indicador {year}",
    }


def normalize_annual_structure(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Valida mapeos anuales y normaliza datos planos con forward-fill jerárquico."""
    expected = required_columns_for_year(year)

    # Crear dataframe base con tipado limpio usando asignaciones directas
    normalized = pd.DataFrame(
        {
            "year": year,
            "source_row": df.index + 2,
            "component_raw_code": df[expected["component_code"]],
            "component_description": df[expected["component_description"]],
            "variable_raw_code": df[expected["variable_code"]],
            "variable_description": df[expected["variable_description"]],
            "indicator_raw_code": df[expected["indicator_code"]],
            "indicator_description": df[expected["indicator_description"]],
        }
    )

    hierarchy_columns = [
        "component_raw_code",
        "component_description",
        "variable_raw_code",
        "variable_description",
        "indicator_raw_code",
        "indicator_description",
    ]

    for col in hierarchy_columns:
        normalized[col] = normalized[col].apply(clean_text)

    # Soporte para celdas combinadas nativo mediante forward-fill
    normalized[hierarchy_columns] = normalized[hierarchy_columns].ffill()

    # Filtrar únicamente filas completamente pobladas en su jerarquía
    normalized = normalized[normalized[hierarchy_columns].notna().all(axis=1)].copy()

    if normalized.empty:
        raise ValueError(f"La hoja {year} no produjo una jerarquía de datos válida.")

    # Generar códigos de negocio técnicos estables
    normalized["component_code"] = normalized["component_raw_code"].apply(
        lambda v: make_code(f"{year}_C", v)
    )
    normalized["variable_code"] = normalized["variable_raw_code"].apply(
        lambda v: make_code(f"{year}_V", v)
    )
    normalized["indicator_code"] = normalized["indicator_raw_code"].apply(
        lambda v: make_code(f"{year}_I", v)
    )

    return normalized


def add_section_record(registry: OrderedDict, candidate: dict) -> None:
    key = (int(candidate["year"]), candidate["level"], candidate["code"])
    existing = registry.get(key)

    if existing is not None:
        conflicts = []
        if fold_for_comparison(existing["label"]) != fold_for_comparison(
            candidate["label"]
        ):
            conflicts.append(f"label {existing['label']!r} != {candidate['label']!r}")
        if fold_for_comparison(existing["description"]) != fold_for_comparison(
            candidate["description"]
        ):
            conflicts.append("description diferente")
        if existing["parent_code"] != candidate["parent_code"]:
            conflicts.append(
                f"parent_code {existing['parent_code']!r} != {candidate['parent_code']!r}"
            )

        if conflicts:
            raise ValueError(
                f"Datos contradictorios en sección {key}. Fila inicial: {existing['source_row']}; "
                f"Fila conflicto: {candidate['source_row']}. Detalle: {'; '.join(conflicts)}"
            )
        return
    registry[key] = candidate


def build_section_records(normalized: pd.DataFrame) -> list[dict]:
    registry = OrderedDict()

    for _, row in normalized.iterrows():
        year = int(row["year"])
        src_row = int(row["source_row"])

        add_section_record(
            registry,
            {
                "year": year,
                "source_row": src_row,
                "level": "COMPONENTE",
                "code": row["component_code"],
                "parent_code": None,
                "label": make_section_label("COMPONENTE", row["component_raw_code"]),
                "description": row["component_description"],
                "display_order": compute_hierarchical_order(row["component_raw_code"]),
            },
        )

        add_section_record(
            registry,
            {
                "year": year,
                "source_row": src_row,
                "level": "VARIABLE",
                "code": row["variable_code"],
                "parent_code": row["component_code"],
                "label": make_section_label("VARIABLE", row["variable_raw_code"]),
                "description": row["variable_description"],
                "display_order": compute_hierarchical_order(row["variable_raw_code"]),
            },
        )

        add_section_record(
            registry,
            {
                "year": year,
                "source_row": src_row,
                "level": "INDICADOR",
                "code": row["indicator_code"],
                "parent_code": row["variable_code"],
                "label": make_section_label("INDICADOR", row["indicator_raw_code"]),
                "description": row["indicator_description"],
                "display_order": compute_hierarchical_order(row["indicator_raw_code"]),
            },
        )

    records = list(registry.values())
    records.sort(
        key=lambda x: (
            int(x["year"]),
            LEVEL_ORDER[x["level"]],
            int(x["display_order"]),
            x["code"],
        )
    )
    return records


# -----------------------------------------------------------------------------
# MASTRUZ DE LOOKUPS USANDO MODELOS ORM
# -----------------------------------------------------------------------------


async def get_forms_lookup(
    conn: AsyncConnection, active_years: tuple[int, ...]
) -> dict[int, str]:
    stmt = select(Form.code, Form.id).order_by(Form.code)
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = {}
    for row in rows:
        y = int(row["code"])
        if y in active_years:
            grouped.setdefault(y, []).append(str(row["id"]))

    lookup = {}
    for year in active_years:
        ids = grouped.get(year, [])
        if len(ids) != 1:
            raise ValueError(
                f"Debe existir exactamente un formulario en forms.forms para el año {year}. Encontrados: {len(ids)}"
            )
        lookup[year] = ids[0]
    return lookup


async def get_section_types_lookup(conn: AsyncConnection) -> dict[str, str]:
    stmt = select(SectionType.label, SectionType.id)
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = {}
    for row in rows:
        cleaned_label = str(row["label"]).strip().upper()
        if cleaned_label in SECTION_LEVELS:
            grouped.setdefault(cleaned_label, []).append(str(row["id"]))

    lookup = {}
    for level in SECTION_LEVELS:
        ids = grouped.get(level, [])
        if len(ids) != 1:
            raise ValueError(
                f"Debe existir exactamente un section_type en forms.section_types con label {level}."
            )
        lookup[level] = ids[0]
    return lookup


async def get_existing_sections(
    conn: AsyncConnection, active_years: tuple[int, ...]
) -> list[dict]:
    # Consulta robusta resolviendo relaciones con Form y SectionType vía ORM
    stmt = (
        select(
            Section.id,
            Section.code,
            Section.form_id,
            Section.parent_id,
            Section.section_type_id,
            Section.label,
            Section.description,
            Section.helper,
            Section.display_order,
            Form.code.label("form_year"),
        )
        .join(Form, Form.id == Section.form_id)
        .order_by(Form.code, Section.id)
    )
    rows = (await conn.execute(stmt)).mappings().all()
    return [dict(row) for row in rows if int(row["form_year"]) in active_years]


# -----------------------------------------------------------------------------
# MOTOR DE CONCILIACIÓN DE IDENTIDAD IDEMPOTENTE
# -----------------------------------------------------------------------------


def find_existing_section(
    source_record: dict,
    form_id: str,
    section_type_id: str,
    parent_id: str | None,
    existing_rows: list[dict],
    used_ids: set[str],
) -> dict | None:
    available = [
        row
        for row in existing_rows
        if str(row["id"]) not in used_ids
        and str(row["form_id"]) == form_id
        and str(row["section_type_id"]) == section_type_id
    ]

    def unique_or_none(candidates: list[dict], strategy: str):
        if not candidates:
            return None
        if len(candidates) > 1:
            raise ValueError(
                f"Ambiguación crítica en {source_record['year']} {source_record['level']} {source_record['code']} vía {strategy}."
            )
        return candidates[0]

    # 1. Coincidencia directa por código de negocio técnico
    match = unique_or_none(
        [r for r in available if r.get("code") == source_record["code"]], "code"
    )
    if match:
        return match

    # 2. Respaldo por combinación estructural estricta de labels y jerarquía de padres
    norm_lbl = fold_for_comparison(source_record["label"])
    match = unique_or_none(
        [
            r
            for r in available
            if str(r["parent_id"]) == str(parent_id)
            and fold_for_comparison(r["label"]) == norm_lbl
        ],
        "label + parent",
    )
    if match:
        return match

    # 3. Respaldo por descripción semántica y jerarquía de padres (Soporte de migración estructural v1)
    norm_desc = fold_for_comparison(source_record["description"])
    match = unique_or_none(
        [
            r
            for r in available
            if str(r["parent_id"]) == str(parent_id)
            and (
                fold_for_comparison(r["label"]) == norm_desc
                or fold_for_comparison(r["description"]) == norm_desc
            )
        ],
        "description + parent",
    )
    if match:
        return match

    # 4. Reparación estructural: Label técnico único sin importar alteración de padres históricos
    match = unique_or_none(
        [r for r in available if fold_for_comparison(r["label"]) == norm_lbl],
        "label técnico global",
    )
    if match:
        return match

    # 5. Reparación semántica global
    match = unique_or_none(
        [
            r
            for r in available
            if (
                fold_for_comparison(r["label"]) == norm_desc
                or fold_for_comparison(r["description"]) == norm_desc
            )
        ],
        "descripción global",
    )

    return match


def prepare_db_record(
    source_record: dict,
    db_columns: dict,
    form_id: str,
    section_type_id: str,
    parent_id: str | None,
    existing_id: str | None,
) -> dict:
    section_id = existing_id or new_uuidv7()
    helper_value = None if db_columns["helper"]["nullable"] else ""

    return {
        "id": section_id,
        "code": truncate_text(
            source_record["code"], db_columns.get("code", {}).get("max_length")
        ),
        "form_id": form_id,
        "file_id": None,
        "parent_id": parent_id,
        "section_type_id": section_type_id,
        "label": truncate_text(
            source_record["label"], db_columns["label"]["max_length"]
        ),
        "description": truncate_text(
            source_record["description"], db_columns["description"]["max_length"]
        ),
        "helper": helper_value,
        "display_order": int(source_record["display_order"] or 0),
    }


# -----------------------------------------------------------------------------
# EJECUCIÓN CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(LOCAL_IIP_STRUCTURE_FILE)
    active_years = get_seeding_active_years()

    logger.debug("Iniciando ejecución de poblado para forms.sections...")
    if not path.exists():
        raise FileNotFoundError(f"Archivo de origen Excel no encontrado: {path}")

    try:
        excel_file = pd.ExcelFile(path)
        all_records: list[dict] = []

        # ETL del libro Excel unificado por año operacional activo
        for year in active_years:
            df_year = load_clean_excel_sheet(
                excel_file,
                sheet_name=str(year),
                required_columns=set(required_columns_for_year(year).values()),
            )
            normalized = normalize_annual_structure(df_year, year)
            year_records = build_section_records(normalized)
            all_records.extend(year_records)

        async with async_engine.begin() as conn:
            # Validación e introspección del esquema físico real
            db_columns = await get_table_columns(conn, schema="forms", table="sections")
            validate_required_columns(
                db_columns,
                required={
                    "id",
                    "code",
                    "form_id",
                    "file_id",
                    "parent_id",
                    "section_type_id",
                    "label",
                    "description",
                    "helper",
                    "display_order",
                },
                table_name="forms.sections",
            )

            # Obtención de mapeos relacionales estables
            forms_lookup = await get_forms_lookup(conn, active_years)
            section_types_lookup = await get_section_types_lookup(conn)
            existing_rows = await get_existing_sections(conn, active_years)

            inserted, updated = 0, 0
            used_existing_ids: set[str] = set()
            section_id_by_key: dict[tuple[int, str, str], str] = {}

            # Carga por niveles estrictos secuenciales para resolver dependencias parentales
            for level in SECTION_LEVELS:
                level_records = [r for r in all_records if r["level"] == level]

                for src_record in level_records:
                    year = int(src_record["year"])
                    key = (year, level, src_record["code"])

                    # Resolución de claves parentales foráneas internas
                    parent_id = None
                    if src_record["parent_code"] is not None:
                        parent_key = (
                            year,
                            PARENT_LEVEL[level],
                            src_record["parent_code"],
                        )
                        parent_id = section_id_by_key.get(parent_key)
                        if parent_id is None:
                            raise ValueError(
                                f"Inconsistencia estructural en la jerarquía: No se localizó el ID del padre para {key}."
                            )

                    # Conciliación de registros previos
                    existing_row = find_existing_section(
                        source_record=src_record,
                        form_id=forms_lookup[year],
                        section_type_id=section_types_lookup[level],
                        parent_id=parent_id,
                        existing_rows=existing_rows,
                        used_ids=used_existing_ids,
                    )
                    existing_id = str(existing_row["id"]) if existing_row else None

                    # Mapeo y preparación del payload para la base de datos
                    db_payload = prepare_db_record(
                        source_record=src_record,
                        db_columns=db_columns,
                        form_id=forms_lookup[year],
                        section_type_id=section_types_lookup[level],
                        parent_id=parent_id,
                        existing_id=existing_id,
                    )

                    if existing_id:
                        stmt_update = (
                            update(Section)
                            .where(Section.id == db_payload["id"])
                            .values(
                                code=db_payload["code"],
                                form_id=db_payload["form_id"],
                                file_id=db_payload["file_id"],
                                parent_id=db_payload["parent_id"],
                                section_type_id=db_payload["section_type_id"],
                                label=db_payload["label"],
                                description=db_payload["description"],
                                helper=db_payload["helper"],
                                display_order=db_payload["display_order"],
                            )
                        )
                        await conn.execute(stmt_update)
                        used_existing_ids.add(existing_id)
                        updated += 1
                    else:
                        stmt_insert = insert(Section).values(db_payload)
                        await conn.execute(stmt_insert)
                        inserted += 1

                    section_id_by_key[key] = str(db_payload["id"])

            # Aserciones finales de sanidad post-carga centralizada
            final_sections_stmt = select(Section.id, Section.code).where(
                Section.form_id.in_(list(forms_lookup.values()))
            )
            final_sections = (await conn.execute(final_sections_stmt)).mappings().all()
            final_rows_dict = [dict(r) for r in final_sections]

            assert_all_uuidv7(rows=final_rows_dict, id_key="id", label_key="code")
            assert_no_duplicates(
                rows=final_rows_dict,
                key_fields=["code"],
                what="secciones de formulario",
            )

        logger.info(
            f"Poblado de forms.sections finalizado exitosamente. Insertados: {inserted}. Actualizados: {updated}."
        )

    except Exception as exc:
        logger.error(f"Error crítico en el proceso de poblado de sections: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(upgrade())
