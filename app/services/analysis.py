import io

import pandas as pd
from matplotlib.figure import Figure


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


def summarize(df: pd.DataFrame) -> dict:
    numeric_cols = set(df.select_dtypes(include="number").columns)
    stats = {}

    for col in df.columns:
        series = df[col]
        info = {
            "dtype": str(series.dtype),
            "nulls": int(series.isna().sum()),
            "unique": int(series.nunique()),
        }
        if col in numeric_cols:
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
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        raise AnalysisError("Se necesitan al menos 2 columnas numéricas.")

    corr = numeric.corr()
    return {
        "columns": [str(c) for c in corr.columns],
        "matrix": [[_to_python(v) for v in row] for row in corr.to_numpy()],
    }


def histogram_png(df: pd.DataFrame, column: str, bins: int = 10) -> bytes:
    numeric = df.select_dtypes(include="number")
    if column not in numeric.columns:
        raise AnalysisError(f"La columna '{column}' no existe o no es numérica.")

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
