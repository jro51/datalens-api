import logging
import os

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Dataset
from app.schemas.dataset import CorrelationOut, DatasetOut, SummaryOut
from app.services import analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


def _get_dataset_or_404(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")
    return dataset


def _load_dataframe(dataset: Dataset) -> pd.DataFrame:
    return analysis.parse_csv(dataset.content)


@router.post("", response_model=DatasetOut, status_code=201)
def upload_dataset(file: UploadFile, db: Session = Depends(get_db)):
    filename = os.path.basename(file.filename or "")
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Solo se aceptan archivos .csv.")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {settings.max_upload_mb} MB.",
        )

    df = analysis.parse_csv(content)  # AnalysisError -> 422 (manejador global)

    dataset = Dataset(
        filename=filename,
        content=content,
        rows=int(len(df)),
        columns=int(df.shape[1]),
        size_bytes=len(content),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    logger.info("Dataset %s subido: %s (%s filas)", dataset.id, filename, dataset.rows)
    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Dataset).order_by(Dataset.id.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()


@router.get("/{dataset_id}/summary", response_model=SummaryOut, response_model_exclude_none=True)
def dataset_summary(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(db, dataset_id)
    return analysis.summarize(_load_dataframe(dataset))


@router.get("/{dataset_id}/correlations", response_model=CorrelationOut)
def dataset_correlations(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(db, dataset_id)
    return analysis.correlations(_load_dataframe(dataset))


@router.get("/{dataset_id}/chart")
def dataset_chart(
    dataset_id: int,
    column: str = Query(..., description="Columna numérica a graficar"),
    bins: int = Query(10, ge=2, le=100),
    db: Session = Depends(get_db),
):
    dataset = _get_dataset_or_404(db, dataset_id)
    png = analysis.histogram_png(_load_dataframe(dataset), column, bins)
    return Response(content=png, media_type="image/png")


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(db, dataset_id)
    db.delete(dataset)
    db.commit()
    logger.info("Dataset %s eliminado", dataset_id)
    return Response(status_code=204)
