import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from shared_schemas import (
    CustomError,
    ItemError,
    add_routers_with_custom_errors,
    custom_error_handler,
)
from shared_utils.logger import get_logger


VERSION = "0.1.0"
PRODUCTION_MODE = os.environ["PRODUCTION_MODE"].lower() in ("1", "true", "yes")
COOKIES_SECURE = False if not PRODUCTION_MODE else True


PUBLIC = os.getenv("PUBLIC_ORIGINS", "*")
NODE = os.environ["NODE_ORIGINS"]

logger = get_logger("api/main")


if not PRODUCTION_MODE:
    PUBLIC_ORIGINS = ["*"]
    PUBLIC_METHODS = ["*"]
    PUBLIC_HEADERS = ["*"]

    NODE_ORIGINS = ["*"]
    NODE_ALLOWED_HOSTS = ["*"]


else:
    PUBLIC_ORIGINS = [item.strip() for item in PUBLIC.split(",") if item.strip()]
    PUBLIC_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    PUBLIC_HEADERS = [
        "Authorization",
        "Content-Type",
        "Cookie",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "X-Platform",
    ]
    NODE_ORIGINS = [item.strip() for item in NODE.split(",") if item.strip()]
    NODE_ALLOWED_HOSTS = ["frontend"]


COOKIES_SAMESITE: Literal["lax", "strict", "none"] = (
    "strict" if PRODUCTION_MODE and COOKIES_SECURE else "lax"
)

##############################################################################################
# Context Manager
##############################################################################################


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


##############################################################################################
# APIS
##############################################################################################

api = FastAPI(
    title="Main API",
    description="API para consumo de la data del IIP.",
    version=VERSION,
    lifespan=lifespan,
)

api_node = FastAPI(
    title="Servicios privados para stats",
    description="API para stats",
    version=VERSION,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Ejemplo",
            "description": "Endpoints para ejemplo.",
        },
    ],
)

api_public = FastAPI(
    title="Endpoints publicos para data del IIP",
    description="""API para consumo de la data del IIP.
    Aquí encontrará todos los métodos que la Veeduría Distrital pone a su disposición para la consulta de los datos relacionados con el IIP.

Algunos de los métodos disponibles son:

    - Obtener información sobre los resultados en el IIP de una entidad Distrital.
    - Consultar las respuestas dadas por las entidades distritales.
    - Comparar historicos de resultados en el IIP de una entidad Distrital.

Tenga en cuenta que algunos endpoints están protegidos por autenticación y autorización. Por favor escribanos a labcapital@veeduriadistrital.gov.co para obtener más información.
""",
    version=VERSION,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Ejemplo",
            "description": "Endpoints para ejemplo.",
        },
    ],
)

##############################################################################################
# MIDDLEWARE
##############################################################################################

api_node.add_middleware(
    CORSMiddleware,
    allow_origins=NODE_ORIGINS,
    allow_credentials=COOKIES_SECURE,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)

api_public.add_middleware(
    CORSMiddleware,
    allow_origins=PUBLIC_ORIGINS,
    allow_credentials=COOKIES_SECURE,
    allow_methods=PUBLIC_METHODS,
    allow_headers=PUBLIC_HEADERS,
    max_age=86400,
)

##############################################################################################
# TrustedHostMiddleware
##############################################################################################

api_node.add_middleware(TrustedHostMiddleware, allowed_hosts=NODE_ALLOWED_HOSTS)

##############################################################################################
# ExceptionHandlerMiddleware
##############################################################################################

api_node.add_exception_handler(CustomError, custom_error_handler)
api_public.add_exception_handler(CustomError, custom_error_handler)

##############################################################################################
# ExceptionHandlerMiddleware
##############################################################################################


@api_node.exception_handler(RequestValidationError)
async def validation_exception_handler_frontend(
    request: Request, exc: RequestValidationError
):
    errors = [
        ItemError(
            code="INVALID_REQUEST",
            message=e["msg"],
            more_info=".".join(map(str, e["loc"])),
        )
        for e in exc.errors()
    ]
    return await custom_error_handler(request, CustomError(errors=errors))


@api_public.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        ItemError(
            code="INVALID_REQUEST",
            message=e["msg"],
            more_info=".".join(map(str, e["loc"])),
        )
        for e in exc.errors()
    ]
    return await custom_error_handler(request, CustomError(errors=errors))


##############################################################################################
# LOGS
##############################################################################################

logger.info(f"Client app CORS origins: {PUBLIC_ORIGINS}")
logger.info(f"Client app allow_credentials: {COOKIES_SECURE}")
logger.info(f"Node app CORS origins: {NODE_ORIGINS}")
logger.info(f"Node app allow_credentials: {COOKIES_SECURE}")

##############################################################################################
# Montaje de frontend en la aplicación principal
##############################################################################################

api.mount("/node", api_node)
api.mount("/public", api_public)

##############################################################################################
# Montaje de frontend en la aplicación principal
##############################################################################################
public_routers = []

node_routers = []

all_routers = public_routers + node_routers

add_routers_with_custom_errors(api_node, all_routers)
for route in api_node.routes:
    logger.info(f"Public route mounted: {route}")

add_routers_with_custom_errors(api_public, public_routers)
for route in api_public.routes:
    logger.info(f"Node route mounted: {route}")


##############################################################################################
# Tests
##############################################################################################


@api.get("/")
async def main():
    """Base path"""
    return {
        "message": "Main app is working",
        "cors": f"conditional_credentials: {COOKIES_SECURE}",
    }
