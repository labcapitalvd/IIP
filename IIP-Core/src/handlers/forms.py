from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from db.forms import FormDb

from schemas.forms import (
    ResponseForm,
    ResponseForms,
)

from shared_utils import TextUtils


class FormHandler:
    def __init__(self, db: AsyncSession, current_user: UUID):
        self.db = db

        self.textutils = TextUtils()
        self.form_editionondb = FormDb(self.db)

    async def FormRead(self, id: UUID, detailed: bool = False) -> ResponseForm:
        form_edition = await self.form_editionondb.get_form_edition_entry(id=id)
        if detailed:
            return ResponseForm(
                id=form_edition.id,
                anno=form_edition.anno,
                name=form_edition.name,
                description=form_edition.description,
            )
        else:
            return ResponseForm(
                id=form_edition.id,
                anno=form_edition.anno,
            )

    async def FormReadAll(self, detailed: bool = False) -> ResponseForms:
        form_editionqueries = (
            await self.form_editionondb.get_all_form_edition_entries()
        )
        if detailed:
            return ResponseForms(
                form_editions=[
                    ResponseForm(
                        id=i.id,
                        anno=i.anno,
                        name=i.name,
                        description=i.description,
                    )
                    for i in form_editionqueries
                ]
            )
        else:
            return ResponseForms(
                form_editions=[
                    ResponseForm(
                        id=i.id,
                        anno=i.anno,
                    )
                    for i in form_editionqueries
                ]
            )
