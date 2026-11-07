from uuid import UUID

from fastapi import APIRouter, Depends, File, Path, Query, Response, UploadFile
from shared.utils import AccessContext, get_claims

from application.historical import XLSX_MEDIA_TYPE, HistoricalAppService
from domain.services.errors import HistoricalFileError
from schemas.historical import ResponseHistoricalForm, ResponseHistoricalReport

router = APIRouter(tags=["Cargas históricas"], prefix="/forms")

_MAX_UPLOAD = 25 * 1024 * 1024


def get_historical_service() -> HistoricalAppService:
    return HistoricalAppService()


def _user(ctx: AccessContext) -> UUID:
    return UUID(get_claims(token=ctx.access_token)["sub"])


async def _read(file: UploadFile) -> bytes:
    data = await file.read(_MAX_UPLOAD + 1)
    if len(data) > _MAX_UPLOAD:
        raise HistoricalFileError("El archivo supera los 25 MB.")
    return data


def _xlsx(name_and_bytes: tuple[str, bytes]) -> Response:
    name, content = name_and_bytes
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.get(
    "/historical",
    response_model=list[ResponseHistoricalForm],
    response_model_exclude_none=True,
    operation_id="list_historical_forms",
    summary="Formularios con su estado de edición y datos históricos cargados (solo admin)",
)
async def list_historical_forms(
    ctx: AccessContext = Depends(),
    service: HistoricalAppService = Depends(get_historical_service),
):
    return await service.list_forms(requester_id=_user(ctx))


@router.post(
    "/{form_id}/edition/close",
    response_model=ResponseHistoricalForm,
    response_model_exclude_none=True,
    operation_id="close_form_edition",
    summary="Dar por terminada la edición del formulario (habilita las cargas históricas)",
)
async def close_edition(
    form_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: HistoricalAppService = Depends(get_historical_service),
):
    return await service.close_edition(requester_id=_user(ctx), form_id=form_id)


@router.post(
    "/{form_id}/edition/reopen",
    response_model=ResponseHistoricalForm,
    response_model_exclude_none=True,
    operation_id="reopen_form_edition",
    summary="Reabrir la edición (solo si no hay respuestas ni resultados cargados)",
)
async def reopen_edition(
    form_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: HistoricalAppService = Depends(get_historical_service),
):
    return await service.reopen_edition(requester_id=_user(ctx), form_id=form_id)


@router.get(
    "/{form_id}/historical/templates/responses",
    operation_id="download_responses_template",
    summary="Descargar la plantilla Excel de respuestas históricas",
    response_class=Response,
)
async def download_responses_template(
    form_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: HistoricalAppService = Depends(get_historical_service),
):
    return _xlsx(await service.responses_template(requester_id=_user(ctx), form_id=form_id))


@router.get(
    "/{form_id}/historical/templates/results",
    operation_id="download_results_template",
    summary="Descargar la plantilla Excel de resultados históricos",
    response_class=Response,
)
async def download_results_template(
    form_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: HistoricalAppService = Depends(get_historical_service),
):
    return _xlsx(await service.results_template(requester_id=_user(ctx), form_id=form_id))


@router.post(
    "/{form_id}/historical/responses",
    response_model=ResponseHistoricalReport,
    response_model_exclude_none=True,
    operation_id="upload_historical_responses",
    summary="Validar o cargar las respuestas históricas de un Excel",
)
async def upload_historical_responses(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="Solo validar: no guarda nada."),
    replace: bool = Query(False, description="Reemplazar las respuestas que una entidad ya tenga."),
    form_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: HistoricalAppService = Depends(get_historical_service),
):
    return await service.load_responses(
        requester_id=_user(ctx), form_id=form_id, data=await _read(file), dry_run=dry_run, replace=replace
    )


@router.post(
    "/{form_id}/historical/results",
    response_model=ResponseHistoricalReport,
    response_model_exclude_none=True,
    operation_id="upload_historical_results",
    summary="Validar o cargar los resultados históricos de un Excel",
)
async def upload_historical_results(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="Solo validar: no guarda nada."),
    form_id: UUID = Path(),
    ctx: AccessContext = Depends(),
    service: HistoricalAppService = Depends(get_historical_service),
):
    return await service.load_results(
        requester_id=_user(ctx), form_id=form_id, data=await _read(file), dry_run=dry_run
    )
