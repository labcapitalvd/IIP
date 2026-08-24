"""Puebla forms.fields para los IIP mapeando a través de la jerarquía FieldGroup.

Dependencias previas:
    - seed_questions (Preguntas principales cargadas)
    - seed_loop_questions (Preguntas tipo bucle cargadas)
    - seed_card_templates (Plantillas de tarjetas cargadas)
    - seed_field_groups (Grupos de campos repetibles cargadas)

Utiliza la infraestructura global de utilidades y los modelos ORM del sistema.
El script es idempotente y conserva los UUIDv7 existentes de forma transparente.
"""

import asyncio
import os
from collections import OrderedDict, defaultdict
from pathlib import Path

import pandas as pd
from shared.enums import FieldTypesEnum
from shared.infrastructure import async_engine
from shared.models import (
    CardTemplate,
    Field,
    FieldGroup,
    FieldType,
    Form,
    Question,
    Section,
)
from shared.utils.logger import get_logger
from shared.utils.seeding import (
    assert_all_uuidv7,
    assert_no_duplicates,
    clean_text,
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

FILE_PATH = os.getenv(
    "IIP_STRUCTURE_FILE",
    "/api/populator/pops/jhonatan/Estructura_IIP.xlsx",
)

# -----------------------------------------------------------------------------
# ETL Y EXTRACCIÓN DESDE EL LIBRO EXCEL
# -----------------------------------------------------------------------------


def load_fields_for_years(excel: pd.ExcelFile, years: tuple[int, ...]) -> list[dict]:
    all_fields: list[dict] = []

    for year in years:
        sheet_name = str(year)
        if sheet_name not in excel.sheet_names:
            logger.debug(f"Hoja {sheet_name!r} no encontrada. Omitiendo.")
            continue

        temp_df = pd.read_excel(excel, sheet_name=sheet_name, nrows=1, dtype=object)
        temp_cols = {str(c).strip() for c in temp_df.columns}

        # Resolución dinámica adaptada al formato real de cabeceras híbridas (2019-2025)
        q_col = "Pregunta" if "Pregunta" in temp_cols else "COD_PREGUNTA"
        sub_col = "Subpregunta" if "Subpregunta" in temp_cols else "COD_SUBPREGUNTA"

        # PRIORIDAD 1: Buscar las columnas exactas de preguntas tradicionales (Tu Captura)
        f_code_col = next(
            (
                c
                for c in ["code_field", "Codigo_Campo", "COD_CAMPO", "Campo"]
                if c in temp_cols
            ),
            None,
        )
        f_lbl_col = next(
            (
                c
                for c in [
                    "field",
                    "Nombre de la innovación",
                    "Etiqueta",
                    "DESCRIPCION_CAMPO",
                ]
                if c in temp_cols
            ),
            None,
        )
        f_desc_col = next(
            (c for c in ["desc_field", "DESCRIPCION", "Enunciado"] if c in temp_cols),
            None,
        )
        f_type_col = next(
            (c for c in ["Tipo_dato", "TIPO_DATO", "Tipo de dato"] if c in temp_cols),
            None,
        )

        required_cols = {q_col}
        frame = load_clean_excel_sheet(
            excel, sheet_name=sheet_name, required_columns=required_cols
        )
        sheet_fields: OrderedDict[tuple[str, str], dict] = OrderedDict()

        display_order_counter = defaultdict(int)

        for idx, (_, row) in enumerate(frame.iterrows(), start=2):
            row_idx = idx
            parent_question = clean_text(row.get(q_col))

            if parent_question is None:
                continue

            subquestion = clean_text(row.get(sub_col)) if sub_col in temp_cols else None
            field_label = clean_text(row.get(f_lbl_col)) if f_lbl_col else None
            field_description = clean_text(row.get(f_desc_col)) if f_desc_col else None
            raw_field_type = clean_text(row.get(f_type_col)) if f_type_col else ""

            target_question_label = (
                subquestion if subquestion is not None else parent_question
            )

            display_order_counter[target_question_label] += 1
            display_order = display_order_counter[target_question_label]

            # -----------------------------------------------------------------
            # LOGICA DE GENERACION DE CODIGO SEMANTICO: [AÑO]_FD_[PREGUNTA]
            # -----------------------------------------------------------------
            # 1. Aislar y limpiar el prefijo de la pregunta (ej: "Pregunta 11.1: texto" -> "Q11_1")
            q_clean = str(target_question_label).split(":")[
                0
            ]  # Tomar solo el encabezado numérico antes de los dos puntos
            q_clean = (
                q_clean.replace("Pregunta", "Q").replace(".", "_").replace(" ", "")
            )
            # Asegurar remover caracteres extraños manteniendo la estructura alfanumérica limpia
            q_clean = "".join(c for c in q_clean if c.isalnum() or c == "_").strip("_")

            # 2. Determinar el sufijo del campo basado en el excel o usar MAIN/VAL secuencial como fallback
            excel_suffix = clean_text(row.get(f_code_col)) if f_code_col else None
            if not excel_suffix:
                excel_suffix = "MAIN" if display_order == 1 else f"VAL_{display_order}"
            else:
                # Sanitizar el sufijo para que no repita el año o textos redundantes de otras hojas
                excel_suffix = (
                    str(excel_suffix)
                    .replace(f"{year}_", "")
                    .replace("FIELD_", "")
                    .replace("code_field_", "")
                    .strip("_")
                )

            # 3. Construcción del código final bajo la nomenclatura uniforme solicitada
            field_code_semantic = f"{year}_FD_{q_clean}_{excel_suffix}".strip("_")

            # FALLBACKS INTELIGENTES DE CAPAS VISUALES E INFORMATIVAS
            if field_label is None:
                field_label = field_code_semantic

            if field_description is None:
                field_description = field_label

            # RESOLUCIÓN DE TIPADO VÍA ENUMS EXPLICÍTOS DE TU MODELO DE DOMINIO
            norm_type = fold_for_comparison(raw_field_type) or ""
            if "bool" in norm_type or "dicot" in norm_type:
                field_type_enum = FieldTypesEnum.BOOLEAN
            elif "num" in norm_type or "enter" in norm_type or "monet" in norm_type:
                field_type_enum = FieldTypesEnum.NUMERIC
            elif "archiv" in norm_type or "soport" in norm_type:
                field_type_enum = FieldTypesEnum.FILE
            elif "multi" in norm_type:
                field_type_enum = FieldTypesEnum.MULTI_CHOICE
            elif "sing" in norm_type or "unic" in norm_type or "radio" in norm_type:
                field_type_enum = FieldTypesEnum.SINGLE_CHOICE
            elif "fech" in norm_type or "date" in norm_type:
                field_type_enum = FieldTypesEnum.DATE
            else:
                field_type_enum = FieldTypesEnum.TEXT

            candidate = {
                "year": year,
                "parent_question": parent_question,
                "target_question_label": target_question_label,
                "code": field_code_semantic,
                "label": field_label,
                "description": field_description,
                "display_order": display_order,
                "field_type_code": field_type_enum.code,
            }

            # La clave de unicidad interna del procesador ahora se apoya en el código semántico estructurado
            key = (target_question_label, field_code_semantic)
            if key not in sheet_fields:
                sheet_fields[key] = candidate

        logger.debug(
            f"Año {year}: Extraídos {len(sheet_fields)} campos híbridos mapeados con enums."
        )
        all_fields.extend(sheet_fields.values())

    return all_fields


# -----------------------------------------------------------------------------
# LOOKUPS CENTRALIZADOS VÍA ORM
# -----------------------------------------------------------------------------


async def get_questions_lookup(
    conn: AsyncConnection, years: tuple[int, ...]
) -> dict[tuple[int, str], dict]:
    stmt = (
        select(
            Question.id.label("question_id"),
            Question.label,
            Form.code.label("form_year"),
        )
        .join(Section, Section.id == Question.section_id)
        .join(Form, Form.id == Section.form_id)
    )
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = defaultdict(list)
    for row in rows:
        y = int(row["form_year"])
        if y in years:
            natural_lbl = fold_for_comparison(row["label"]) or ""
            grouped[(y, natural_lbl)].append(dict(row))

    lookup = {}
    for key, items in grouped.items():
        lookup[key] = items[0]
    return lookup


async def get_field_groups_lookup(conn: AsyncConnection) -> dict[str, str]:
    stmt = select(FieldGroup.id.label("field_group_id"), CardTemplate.question_id).join(
        CardTemplate, FieldGroup.card_template_id == CardTemplate.id
    )
    rows = (await conn.execute(stmt)).mappings().all()
    return {str(row["question_id"]): str(row["field_group_id"]) for row in rows}


async def get_existing_fields(conn: AsyncConnection) -> dict[tuple[str, str], dict]:
    stmt = select(
        Field.id.label("field_id"),
        Field.field_group_id,
        Field.field_type_id,
        Field.code,
        Field.label,
        Field.description,
        Field.display_order,
        Field.required,
    )
    rows = (await conn.execute(stmt)).mappings().all()

    grouped = defaultdict(list)
    for row in rows:
        key = (str(row["field_group_id"]), fold_for_comparison(row["code"]) or "")
        grouped[key].append(dict(row))

    lookup = {}
    for key, items in grouped.items():
        lookup[key] = items[0]
    return lookup


# -----------------------------------------------------------------------------
# EJECUCIÓN CENTRAL DE POBLADO (UPGRADE)
# -----------------------------------------------------------------------------


async def upgrade() -> None:
    path = Path(FILE_PATH)
    years = get_seeding_active_years()
    if not path.is_file():
        raise FileNotFoundError(f"Archivo de origen Excel no encontrado: {path}")

    logger.debug(f"Iniciando el poblado de forms.fields desde {path}...")

    excel = pd.ExcelFile(path)
    raw_fields = load_fields_for_years(excel, years)

    async with async_engine.begin() as conn:
        # Validación e introspección dinámica de las columnas físicas reales de la tabla
        db_columns = await get_table_columns(conn, schema="forms", table="fields")
        validate_required_columns(
            db_columns,
            required={
                "id",
                "field_group_id",
                "field_type_id",
                "code",
                "label",
                "description",
                "required",
                "display_order",
            },
            table_name="forms.fields",
        )

        # DYNAMIC ENUM INTEGRATION: Map out all entries configured inside your FieldTypesEnum dictionary catalog
        stmt_all_types = select(FieldType.id, FieldType.code)
        type_rows = (await conn.execute(stmt_all_types)).mappings().all()
        field_type_id_by_code = {str(r["code"]): str(r["id"]) for r in type_rows}

        # Safe fallback extracting the strict string value from the tuple template structure (.code property)
        text_type_code = FieldTypesEnum.TEXT.code
        default_field_type_id = field_type_id_by_code.get(text_type_code)

        if not default_field_type_id:
            raise ValueError(
                f"Catálogo maestro incompleto: El identificador para el tipo de campo por defecto "
                f"'{text_type_code}' no existe registrado en la tabla física de tipos."
            )

        # Inicialización de matrices de búsqueda compartidas relacionales
        questions_map = await get_questions_lookup(conn, years)
        field_groups_map = await get_field_groups_lookup(conn)
        existing_fields = await get_existing_fields(conn)

        # Buscar una plantilla card_template por defecto para dar soporte a las preguntas lineales de 2019/2021
        stmt_default_ct = select(CardTemplate.id).limit(1)
        ct_row = (await conn.execute(stmt_default_ct)).mappings().first()
        global_fallback_card_template_id = str(ct_row["id"]) if ct_row else None

        # Inicializar conjunto de control de duplicados en caliente para evitar violaciones de clave única
        seen_database_keys = set()

        expected_records = []
        for item in raw_fields:
            y = item["year"]
            lbl_key = fold_for_comparison(item["target_question_label"]) or ""

            question = questions_map.get((y, lbl_key))
            if question is None:
                logger.warning(
                    f"Pregunta objetivo '{item['target_question_label']}' ({y}) no encontrada en forms.questions. Omitiendo campo."
                )
                continue

            q_id_str = str(question["question_id"])
            fg_id_str = field_groups_map.get(q_id_str)

            # RESOLUCIÓN DEL ERROR DE INTEGRIDAD (ForeignKeyViolationError):
            if fg_id_str is None:
                expected_fg_code = f"{y}_FG_GENERIC_{q_id_str[:8]}"

                stmt_check_fg = select(FieldGroup.id).where(
                    FieldGroup.code == expected_fg_code
                )
                existing_fg_row = (await conn.execute(stmt_check_fg)).mappings().first()

                if existing_fg_row:
                    fg_id_str = str(existing_fg_row["id"])
                else:
                    stmt_specific_ct = select(CardTemplate.id).where(
                        CardTemplate.question_id == q_id_str
                    )
                    spec_ct_row = (
                        (await conn.execute(stmt_specific_ct)).mappings().first()
                    )
                    active_ct_id = (
                        str(spec_ct_row["id"])
                        if spec_ct_row
                        else global_fallback_card_template_id
                    )

                    if not active_ct_id:
                        active_ct_id = new_uuidv7()
                        stmt_ins_ct = insert(CardTemplate).values(
                            id=active_ct_id,
                            question_id=q_id_str,
                            code=f"{y}_CT_GEN_{q_id_str[:8]}",
                            label="Plantilla Base Proceso Lineal",
                            description="Generada automáticamente para proteger relaciones jerárquicas",
                        )
                        await conn.execute(stmt_ins_ct)
                        global_fallback_card_template_id = active_ct_id

                    fg_id_str = new_uuidv7()
                    stmt_ins_fg = insert(FieldGroup).values(
                        id=fg_id_str,
                        card_template_id=active_ct_id,
                        code=expected_fg_code,
                        label=f"Grupo de campos {item['target_question_label']}"[:255],
                        description="Grupo por defecto autogenerado para campos lineales tradicionales",
                    )
                    await conn.execute(stmt_ins_fg)

                # Sincronizar el lookup local para acelerar campos secuenciales de la misma pregunta
                field_groups_map[q_id_str] = fg_id_str

            # Resolver el ID del tipo de campo exacto usando el string extraído de la propiedad .code del Enum
            ft_code = item["field_type_code"]
            field_type_id = field_type_id_by_code.get(ft_code)
            if field_type_id is None:
                field_type_id = default_field_type_id

            # VALIDACIÓN DEFENSIVA: Calcular la combinación clave natural única final de la base de datos
            db_unique_combination = (fg_id_str, fold_for_comparison(item["code"]) or "")

            if db_unique_combination in seen_database_keys:
                logger.warning(
                    f"⚠️ Saltando combinación duplicada en Excel detectada para evitar colisión: "
                    f"Año {y} | Group ID {fg_id_str[:8]}... | Code '{item['code']}'"
                )
                continue

            seen_database_keys.add(db_unique_combination)

            expected_records.append(
                {
                    "natural_key": db_unique_combination,
                    "field_group_id": fg_id_str,
                    "field_type_id": field_type_id,
                    "code": item["code"],
                    "label": item["label"],
                    "description": item["description"],
                    "display_order": item["display_order"],
                }
            )

        inserted, updated = 0, 0

        for source in expected_records:
            old_field = existing_fields.get(source["natural_key"])
            field_id = old_field["field_id"] if old_field else new_uuidv7()

            db_payload = {
                "id": field_id,
                "field_group_id": source["field_group_id"],
                "field_type_id": source["field_type_id"],
                "code": truncate_text(source["code"], db_columns["code"]["max_length"]),
                "label": truncate_text(
                    source["label"], db_columns["label"]["max_length"]
                ),
                "description": truncate_text(
                    source["description"], db_columns["description"]["max_length"]
                ),
                "required": True,
                "display_order": source["display_order"],
            }

            if old_field:
                stmt_update = (
                    update(Field)
                    .where(Field.id == db_payload["id"])
                    .values(
                        field_group_id=db_payload["field_group_id"],
                        field_type_id=db_payload["field_type_id"],
                        code=db_payload["code"],
                        label=db_payload["label"],
                        description=db_payload["description"],
                        required=db_payload["required"],
                        display_order=db_payload["display_order"],
                    )
                )
                await conn.execute(stmt_update)
                updated += 1
            else:
                stmt_insert = insert(Field).values(db_payload)
                await conn.execute(stmt_insert)
                inserted += 1

        # -----------------------------------------------------------------------------
        # ASERCIONES FINALES DE SANIDAD POST-CARGA CENTRALIZADA
        # -----------------------------------------------------------------------------
        # Selecciona field_group_id junto con code para que refleje la clave compuesta real
        final_stmt = select(Field.id, Field.field_group_id, Field.code)
        final_rows = [
            dict(r) for r in (await conn.execute(final_stmt)).mappings().all()
        ]

        assert_all_uuidv7(rows=final_rows, id_key="id", label_key="code")

        # Validar unicidad usando la combinación relacional del índice único compuesto
        assert_no_duplicates(
            rows=final_rows,
            key_fields=["field_group_id", "code"],
            what="campos de entrada de preguntas (fields) organizados por grupo",
        )

    logger.info(
        f"Poblado de forms.fields finalizado exitosamente. "
        f"Insertados: {inserted}. Actualizados: {updated}. Totales Sincronizados: {len(expected_records)}."
    )


if __name__ == "__main__":
    asyncio.run(upgrade())
