from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from shared.db import Base
from shared.models import (
    ActorSegment,
    CommentType,
    FieldType,
    FileType,
    LogActionType,
    NotificationType,
    Permission,
    RelationalOperator,
    ResourceRole,
    RuleType,
    SectionType,
    SubmissionStatusType,
    SystemRole,
    UserSystemRoleLink,
    UserTier,
)
from shared.utils import BaseDomainError
from sqlalchemy import Boolean, Integer, Numeric, String, Text, func, select
from sqlalchemy.exc import IntegrityError

from infrastructure.uow import ParametersUoW

##############################################################################################
# Errors
##############################################################################################


class ParameterError(BaseDomainError):
    status_code = 400
    message = "Parameter error."


class ParameterNotFoundError(ParameterError):
    status_code = 404
    message = "The parameter table or record does not exist."


class ParameterForbiddenError(ParameterError):
    status_code = 403
    message = "Only administrators can manage parameters."


class ParameterValidationError(ParameterError):
    status_code = 422
    message = "Invalid parameter data."


class ParameterConflictError(ParameterError):
    status_code = 409
    message = "A record with the same unique value already exists."


class ParameterInUseError(ParameterError):
    status_code = 409
    message = "The record is in use and cannot be deleted."


class ParameterReadOnlyError(ParameterError):
    status_code = 405
    message = "This operation is not allowed for this parameter table."


##############################################################################################
# Registry
##############################################################################################


@dataclass(frozen=True)
class ParamDef:
    """
    Configuración de una tabla parametrizable.
    - `can_create` / `can_delete`: operaciones permitidas.
    - `locked_on_edit`: columnas que no se pueden cambiar tras crear el registro
      (su valor lo usa el código para decidir comportamiento, p. ej. `code`).
    """

    key: str
    model: type[Base]
    label: str
    group: str
    description: str
    can_create: bool = True
    can_delete: bool = True
    locked_on_edit: frozenset[str] = frozenset()
    column_units: dict[str, str] = field(default_factory=dict)


_CODE_LOCKED = frozenset({"code"})

REGISTRY: dict[str, ParamDef] = {
    d.key: d
    for d in [
        ParamDef("sectores", ActorSegment, "Sectores", "Entidades",
                 "Sectores a los que pertenecen las entidades distritales."),
        ParamDef("tipos-seccion", SectionType, "Tipos de sección", "Formularios",
                 "Niveles del formulario: Componente, Variable e Indicador. El diseñador usa V e I.",
                 can_create=False, can_delete=False, locked_on_edit=_CODE_LOCKED),
        ParamDef("tipos-campo", FieldType, "Tipos de campo", "Formularios",
                 "Tipos de pregunta/campo que soporta el sistema (cada código tiene lógica asociada).",
                 can_create=False, can_delete=False, locked_on_edit=_CODE_LOCKED),
        ParamDef("tipos-archivo", FileType, "Tipos de archivo", "Formularios",
                 "Formatos que pueden cargar las preguntas de tipo archivo, con su tamaño máximo.",
                 column_units={"max_size": "bytes"}),
        ParamDef("operadores", RelationalOperator, "Operadores relacionales", "Formularios",
                 "Operadores usados en las condiciones entre preguntas (cada código tiene lógica asociada).",
                 can_create=False, can_delete=False, locked_on_edit=_CODE_LOCKED),
        ParamDef("tipos-regla", RuleType, "Tipos de regla de validación", "Formularios",
                 "Reglas de validación de campos (mínimo, máximo, tipos de archivo…).",
                 can_create=False, can_delete=False, locked_on_edit=_CODE_LOCKED),
        ParamDef("estados-radicado", SubmissionStatusType, "Estados de radicado", "Radicados",
                 "Ciclo de vida de un envío: borrador, radicado, en revisión…",
                 locked_on_edit=_CODE_LOCKED),
        ParamDef("tipos-comentario", CommentType, "Tipos de comentario", "Interacciones",
                 "Clasificación de los comentarios.", locked_on_edit=_CODE_LOCKED),
        ParamDef("tipos-notificacion", NotificationType, "Tipos de notificación", "Interacciones",
                 "Clasificación de las notificaciones.", locked_on_edit=_CODE_LOCKED),
        ParamDef("tipos-accion-log", LogActionType, "Tipos de acción de auditoría", "Seguridad",
                 "Acciones que registra la bitácora de auditoría.", locked_on_edit=_CODE_LOCKED),
        ParamDef("roles-sistema", SystemRole, "Roles de sistema", "Seguridad",
                 "Roles globales de la plataforma (admin, calificador, auditor…).",
                 locked_on_edit=_CODE_LOCKED),
        ParamDef("roles-recurso", ResourceRole, "Roles sobre recursos", "Seguridad",
                 "Roles dentro de una entidad o recurso (propietario, editor, evaluador…).",
                 locked_on_edit=_CODE_LOCKED),
        ParamDef("permisos", Permission, "Permisos", "Seguridad",
                 "Permisos atómicos que verifica el código (la clave no se puede cambiar).",
                 can_create=False, can_delete=False, locked_on_edit=frozenset({"key", "code"})),
        ParamDef("niveles-usuario", UserTier, "Niveles de usuario (cuotas)", "Seguridad",
                 "Límites por nivel: tamaño de archivo, almacenamiento, solicitudes por minuto.",
                 locked_on_edit=_CODE_LOCKED),
    ]
}

LABELS = {
    "code": "Código",
    "label": "Nombre",
    "description": "Descripción",
    "key": "Clave",
    "mime_type": "Tipo MIME",
    "extension": "Extensión",
    "category": "Categoría",
    "max_size": "Tamaño máximo",
    "max_file_size": "Tamaño máximo de archivo",
    "storage_quota": "Cuota de almacenamiento",
    "max_requests_per_minute": "Solicitudes por minuto",
    "priority_level": "Nivel de prioridad",
}

HIDDEN_COLUMNS = {"id", "created_at", "updated_at", "deleted_at"}
BYTE_COLUMNS = {"max_size", "max_file_size", "storage_quota"}


def _col_type(column) -> str:
    t = column.type
    if isinstance(t, Boolean):
        return "boolean"
    if isinstance(t, Integer):
        return "integer"
    if isinstance(t, Numeric):
        return "number"
    if isinstance(t, Text):
        return "textarea"
    return "text"


def _columns(pdef: ParamDef) -> list[dict[str, Any]]:
    cols = []
    for c in pdef.model.__table__.columns:
        if c.name in HIDDEN_COLUMNS:
            continue
        cols.append(
            {
                "name": c.name,
                "label": LABELS.get(c.name, c.name),
                "type": _col_type(c),
                "required": not c.nullable,
                "max_length": getattr(c.type, "length", None) if isinstance(c.type, String) else None,
                "unit": "bytes" if c.name in BYTE_COLUMNS else None,
                "locked_on_edit": c.name in pdef.locked_on_edit,
            }
        )
    return cols


def _referencing_columns(model: type[Base]):
    """Todas las FK de la base que apuntan a la tabla del modelo."""
    table = model.__table__
    refs = []
    for other in Base.metadata.tables.values():
        for fk in other.foreign_keys:
            if fk.column.table is table:
                refs.append(fk.parent)
    return refs


def _serialize(obj: Base, pdef: ParamDef) -> dict[str, Any]:
    row: dict[str, Any] = {"id": str(obj.id)}
    for c in pdef.model.__table__.columns:
        if c.name in HIDDEN_COLUMNS:
            continue
        v = getattr(obj, c.name)
        row[c.name] = float(v) if isinstance(v, Decimal) and isinstance(c.type, Numeric) and c.type.scale else (
            int(v) if isinstance(v, Decimal) else v
        )
    return row


class ParameterService:
    async def require_admin(self, uow: ParametersUoW, user_id: str) -> None:
        stmt = (
            select(func.count())
            .select_from(UserSystemRoleLink)
            .join(SystemRole, SystemRole.id == UserSystemRoleLink.system_role_id)
            .where(UserSystemRoleLink.user_id == UUID(user_id), SystemRole.code == "admin")
        )
        if not await uow.session.scalar(stmt):
            raise ParameterForbiddenError()

    def _def(self, key: str) -> ParamDef:
        pdef = REGISTRY.get(key)
        if not pdef:
            raise ParameterNotFoundError(f"Unknown parameter table '{key}'.")
        return pdef

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "key": d.key,
                "label": d.label,
                "group": d.group,
                "description": d.description,
                "can_create": d.can_create,
                "can_delete": d.can_delete,
                "columns": _columns(d),
            }
            for d in REGISTRY.values()
        ]

    async def _usage(self, uow: ParametersUoW, pdef: ParamDef) -> dict[str, int]:
        """id -> cantidad de registros que lo referencian (para bloquear borrados peligrosos)."""
        usage: dict[str, int] = {}
        for col in _referencing_columns(pdef.model):
            rows = await uow.session.execute(
                select(col, func.count()).where(col.isnot(None)).group_by(col)
            )
            for ref_id, n in rows.all():
                usage[str(ref_id)] = usage.get(str(ref_id), 0) + n
        return usage

    async def list_rows(self, uow: ParametersUoW, key: str) -> list[dict[str, Any]]:
        pdef = self._def(key)
        order = pdef.model.__table__.columns.get("label")
        objs = (await uow.session.execute(select(pdef.model).order_by(order))).scalars().all()
        usage = await self._usage(uow, pdef)
        out = []
        for o in objs:
            row = _serialize(o, pdef)
            row["usage_count"] = usage.get(row["id"], 0)
            out.append(row)
        return out

    def _clean(self, pdef: ParamDef, data: dict[str, Any], *, editing: bool) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        for c in pdef.model.__table__.columns:
            if c.name in HIDDEN_COLUMNS:
                continue
            if editing and c.name in pdef.locked_on_edit:
                continue
            present = c.name in data
            value = data.get(c.name)
            if isinstance(value, str):
                value = value.strip()
            if value in (None, ""):
                if editing and not present:
                    continue
                if not c.nullable and c.default is None and c.server_default is None:
                    raise ParameterValidationError(f"'{LABELS.get(c.name, c.name)}' es obligatorio.")
                clean[c.name] = None if c.nullable else value
                continue
            t = c.type
            try:
                if isinstance(t, Boolean):
                    value = bool(value)
                elif isinstance(t, Integer):
                    value = int(value)
                elif isinstance(t, Numeric):
                    value = Decimal(str(value))
                    if value < 0:
                        raise ValueError
                else:
                    value = str(value)
                    length = getattr(t, "length", None)
                    if length and len(value) > length:
                        raise ParameterValidationError(
                            f"'{LABELS.get(c.name, c.name)}' supera {length} caracteres."
                        )
            except (ValueError, InvalidOperation):
                raise ParameterValidationError(f"'{LABELS.get(c.name, c.name)}' no es un valor válido.")
            clean[c.name] = value
        return clean

    async def create(self, uow: ParametersUoW, key: str, data: dict[str, Any]) -> dict[str, Any]:
        pdef = self._def(key)
        if not pdef.can_create:
            raise ParameterReadOnlyError("No se pueden crear registros en esta tabla.")
        obj = pdef.model(**self._clean(pdef, data, editing=False))
        uow.session.add(obj)
        try:
            await uow.session.flush()
        except IntegrityError as e:
            raise ParameterConflictError("Ya existe un registro con el mismo código/clave.") from e
        row = _serialize(obj, pdef)
        row["usage_count"] = 0
        return row

    async def update(self, uow: ParametersUoW, key: str, row_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        pdef = self._def(key)
        obj = await uow.session.get(pdef.model, row_id)
        if not obj:
            raise ParameterNotFoundError("El registro no existe.")
        for name, value in self._clean(pdef, data, editing=True).items():
            setattr(obj, name, value)
        try:
            await uow.session.flush()
        except IntegrityError as e:
            raise ParameterConflictError("Ya existe un registro con el mismo código/clave.") from e
        row = _serialize(obj, pdef)
        row["usage_count"] = (await self._usage(uow, pdef)).get(row["id"], 0)
        return row

    async def delete(self, uow: ParametersUoW, key: str, row_id: UUID) -> None:
        pdef = self._def(key)
        if not pdef.can_delete:
            raise ParameterReadOnlyError("No se pueden eliminar registros de esta tabla.")
        obj = await uow.session.get(pdef.model, row_id)
        if not obj:
            raise ParameterNotFoundError("El registro no existe.")
        # Muchas FK de la base son ON DELETE CASCADE: borrar un valor en uso arrastraría datos.
        used = (await self._usage(uow, pdef)).get(str(row_id), 0)
        if used:
            raise ParameterInUseError(
                f"No se puede eliminar: está en uso por {used} registro(s). Quite primero esas referencias."
            )
        await uow.session.delete(obj)
        await uow.session.flush()
