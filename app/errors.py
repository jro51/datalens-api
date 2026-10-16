import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.analysis import AnalysisError

logger = logging.getLogger(__name__)


async def analysis_error_handler(_: Request, exc: AnalysisError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor."})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AnalysisError, analysis_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
