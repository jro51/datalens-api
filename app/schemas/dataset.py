from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    rows: int
    columns: int
    size_bytes: int
    created_at: datetime


class ColumnStats(BaseModel):
    dtype: str
    nulls: int
    unique: int
    mean: float | None = None
    median: float | None = None
    min: float | None = None
    max: float | None = None
    std: float | None = None
    top: str | None = None


class SummaryOut(BaseModel):
    rows: int
    columns: int
    stats: dict[str, ColumnStats]


class CorrelationOut(BaseModel):
    columns: list[str]
    matrix: list[list[float | None]]
