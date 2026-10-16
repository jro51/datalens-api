import io
import re

import pandas as pd
from matplotlib.figure import Figure

IDENTIFIER_HINTS = {"id", "index", "ean", "sku", "uuid", "code", "isbn", "upc"}


class AnalysisError(ValueError):
    """Error de negocio al leer o analizar un CSV."""


def parse_csv(content: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(content))
    except pd.errors.EmptyDataError as exc:
        raise AnalysisError("El archivo CSV está vacío.") from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise AnalysisError("El archivo no es un CSV válido.") from exc

    if df.empty:
        raise AnalysisError("El CSV no contiene filas de datos.")
    return df


def _to_python(value):
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return round(value, 4) if isinstance(value, float) else value


def _is_identifier(name: str) -> bool:
    """Detecta columnas tipo id/index/ean por su nombre (también camelCase)."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(name))
    tokens = re.split(r"[^a-zA-Z0-9]+", spaced.lower())
    return any(token in IDENTIFIER_HINTS for token in tokens)


def _identifier_columns(df: pd.DataFrame) -> set:
    return {col for col in df.columns if _is_identifier(col)}


def _numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Columnas numéricas con sentido estadístico (sin identificadores)."""
    numeric = df.select_dtypes(include="number")
    return numeric.drop(columns=list(_identifier_columns(numeric)))


def summarize(df: pd.DataFrame) -> dict:
    identifiers = _identifier_columns(df)
    numeric_cols = set(_numeric_columns(df).columns)
    stats = {}

    for col in df.columns:
        series = df[col]
        info = {
            "dtype": str(series.dtype),
            "nulls": int(series.isna().sum()),
            "unique": int(series.nunique()),
        }
        if col in identifiers:
            info["identifier"] = True
        elif col in numeric_cols:
            info.update(
                mean=_to_python(series.mean()),
                median=_to_python(series.median()),
                min=_to_python(series.min()),
                max=_to_python(series.max()),
                std=_to_python(series.std()),
            )
        else:
            mode = series.mode(dropna=True)
            info["top"] = str(mode.iloc[0]) if not mode.empty else None
        stats[str(col)] = info

    return {"rows": int(len(df)), "columns": int(df.shape[1]), "stats": stats}


def correlations(df: pd.DataFrame) -> dict:
    numeric = _numeric_columns(df)
    if numeric.shape[1] < 2:
        raise AnalysisError("Se necesitan al menos 2 columnas numéricas.")

    corr = numeric.corr()
    return {
        "columns": [str(c) for c in corr.columns],
        "matrix": [[_to_python(v) for v in row] for row in corr.to_numpy()],
    }


def histogram_png(df: pd.DataFrame, column: str, bins: int = 10) -> bytes:
    numeric = _numeric_columns(df)
    if column not in numeric.columns:
        raise AnalysisError(
            f"La columna '{column}' no existe, no es numérica o es un identificador."
        )

    data = df[column].dropna()
    if data.empty:
        raise AnalysisError(f"La columna '{column}' no tiene valores para graficar.")

    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()
    ax.hist(data, bins=bins, edgecolor="black")
    ax.set_title(f"Distribución de {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("Frecuencia")

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
    return buffer.getvalue()
