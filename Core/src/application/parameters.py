from typing import Any
from uuid import UUID

from domain.services.parameters import ParameterService
from infrastructure.uow import ParametersUoW


class ParameterAppService:
    """Mantenimiento (CRUD) de tablas de parámetros. Solo para administradores."""

    def __init__(self, service: ParameterService | None = None):
        self.service = service or ParameterService()

    async def catalog(self, user_id: str) -> list[dict[str, Any]]:
        async with ParametersUoW() as uow:
            await self.service.require_admin(uow, user_id)
            return self.service.catalog()

    async def list_rows(self, user_id: str, key: str) -> list[dict[str, Any]]:
        async with ParametersUoW() as uow:
            await self.service.require_admin(uow, user_id)
            return await self.service.list_rows(uow, key)

    async def create(self, user_id: str, key: str, data: dict[str, Any]) -> dict[str, Any]:
        async with ParametersUoW() as uow:
            await self.service.require_admin(uow, user_id)
            return await self.service.create(uow, key, data)

    async def update(self, user_id: str, key: str, row_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        async with ParametersUoW() as uow:
            await self.service.require_admin(uow, user_id)
            return await self.service.update(uow, key, row_id, data)

    async def delete(self, user_id: str, key: str, row_id: UUID) -> None:
        async with ParametersUoW() as uow:
            await self.service.require_admin(uow, user_id)
            await self.service.delete(uow, key, row_id)
