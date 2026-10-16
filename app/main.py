from fastapi import FastAPI

from app.config import settings
from app.routers import health

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para analizar archivos CSV: estadísticas, correlaciones y gráficos.",
)

app.include_router(health.router)
