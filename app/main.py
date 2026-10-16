from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401  (registra los modelos en Base.metadata)
from app.config import settings
from app.database import Base, engine
from app.routers import datasets, health


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para analizar archivos CSV: estadísticas, correlaciones y gráficos.",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(datasets.router)
