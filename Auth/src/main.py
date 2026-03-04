import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from shared_models.relationships import *
from shared_utils import BaseDomainError, configure_logging, get_logger

from routers.auth import router as router_auth
from routers.files import router as router_files

configure_logging()

VERSION = "0.1.0"
PRODUCTION_MODE = os.getenv("PRODUCTION_MODE", "false").lower() in ("1", "true", "yes")
COOKIES_SECURE = False if not PRODUCTION_MODE else True


PUBLIC = os.getenv("PUBLIC_ORIGINS", "*")
PRIVATE = os.environ["PRIVATE_ORIGINS"]

logger = get_logger(__name__)

if not PRODUCTION_MODE:
    PUBLIC_ORIGINS = ["*"]
    PUBLIC_METHODS = ["*"]
    PUBLIC_HEADERS = ["*"]

    PRIVATE_ORIGINS = ["*"]
    PRIVATE_ALLOWED_HOSTS = ["*"]

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
    PRIVATE_ORIGINS = [item.strip() for item in PRIVATE.split(",") if item.strip()]
    PRIVATE_ALLOWED_HOSTS = ["frontend"]

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
    description="API para consumo de la data del HUB.",
    version=VERSION,
    lifespan=lifespan,
)

api_private = FastAPI(
    title="API privada.",
    description="""API PRIVADA para consumo de la data del HUB.
    Aquí encontrará todos los métodos que la Veeduría Distrital pone a su disposición para la consulta de los datos relacionados con el HUB.

Algunos de los métodos disponibles son:

    - Obtener información sobre los resultados en el HUB de una entidad Distrital.
    - Consultar las respuestas dadas por las entidades distritales.
    - Comparar historicos de resultados en el HUB de una entidad Distrital.

Tenga en cuenta que algunos endpoints están protegidos por autenticación y autorización. Por favor escribanos a labcapital@veeduriadistrital.gov.co para obtener más información.
""",
    version=VERSION,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Autenticación", "description": "Endpoints para autenticación"},
    ],
)

api_public = FastAPI(
    title="API publica.",
    description="""API PUBLICA para consumo de la data del HUB.
    Aquí encontrará todos los métodos que la Veeduría Distrital pone a su disposición para la consulta de los datos relacionados con el HUB.

Algunos de los métodos disponibles son:

    - Obtener información sobre los resultados en el HUB de una entidad Distrital.
    - Consultar las respuestas dadas por las entidades distritales.
    - Comparar historicos de resultados en el HUB de una entidad Distrital.

Tenga en cuenta que algunos endpoints están protegidos por autenticación y autorización. Por favor escribanos a labcapital@veeduriadistrital.gov.co para obtener más información.
""",
    version=VERSION,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Autenticación",
            "description": "Endpoints for user authentication.",
        },
    ],
)


##############################################################################################
# MIDDLEWARE
##############################################################################################

# TrustedHostMiddleware must be added before CORSMiddleware so that CORS is the outer-most
# layer and handles OPTIONS requests correctly.
api_private.add_middleware(TrustedHostMiddleware, allowed_hosts=PRIVATE_ALLOWED_HOSTS)

api_private.add_middleware(
    CORSMiddleware,
    allow_origins=PRIVATE_ORIGINS,
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
# LOGS
##############################################################################################

logger.info(f"Client app CORS origins: {PUBLIC_ORIGINS}")
logger.info(f"Client app allow_credentials: {COOKIES_SECURE}")
logger.info(f"Node app CORS origins: {PRIVATE_ORIGINS}")
logger.info(f"Node app allow_credentials: {COOKIES_SECURE}")


##############################################################################################
# Exception Handlers
##############################################################################################
async def domain_exception_handler(request: Request, exc: Any):
    """
    Global handler for all business logic errors.
    Using 'Any' stops the IDE from complaining about the signature match.
    """
    # Since we only register this for BaseDomainError subclasses, 
    # these attributes are guaranteed to exist.
    return JSONResponse(
        status_code=getattr(exc, "status_code", 400),
        content={
            "status": "error",
            "code": type(exc).__name__,
            "message": getattr(exc, "message", "An error occurred"),
        },
    )


async def universal_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "InternalServerError",
            "message": "An unexpected error occurred. Our team has been notified.",
        },
    )


##############################################################################################
# Montaje de frontend en la aplicación principal
##############################################################################################
public_routers = [router_auth, router_files]

private_routers = []

all_routers = public_routers + private_routers

# Register routers to the Public API
for r in public_routers:
    api_public.include_router(r)

# Register routers to the Private API (if any)
for r in private_routers:
    api_private.include_router(r)

for app_instance in [api, api_private, api_public]:
    app_instance.add_exception_handler(BaseDomainError, domain_exception_handler)
    app_instance.add_exception_handler(Exception, universal_exception_handler)


##############################################################################################
# Montaje de frontend en la aplicación principal
##############################################################################################

api.mount("/private", api_private)
api.mount("/public", api_public)

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
