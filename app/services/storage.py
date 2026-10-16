from pathlib import Path
from uuid import uuid4

from app.config import settings


def _upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_file(content: bytes) -> str:
    """Guarda el contenido con un nombre aleatorio (nunca el nombre que envía el usuario)."""
    stored_name = f"{uuid4().hex}.csv"
    (_upload_dir() / stored_name).write_bytes(content)
    return stored_name


def get_path(stored_name: str) -> Path:
    return _upload_dir() / stored_name


def delete_file(stored_name: str) -> None:
    get_path(stored_name).unlink(missing_ok=True)
