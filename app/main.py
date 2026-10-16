import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

import app.models  # noqa: F401  (registra los modelos en Base.metadata)
from app.config import settings
from app.database import Base, engine
from app.errors import register_exception_handlers
from app.logging_config import setup_logging
from app.routers import datasets, health

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info(
        "%s v%s iniciada (%s)", settings.app_name, settings.app_version, settings.environment
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para analizar archivos CSV: estadísticas, correlaciones y gráficos.",
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, elapsed_ms
    )
    return response


app.include_router(health.router)
app.include_router(datasets.router)
