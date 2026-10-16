import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app

SAMPLE_CSV = (
    b"nombre,edad,precio,ciudad\n"
    b"Ana,25,10.5,Lima\n"
    b"Luis,30,20.0,Cusco\n"
    b"Marta,,15.5,Lima\n"
    b"Pedro,40,30.0,Lima\n"
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Cliente con BD SQLite en memoria y carpeta de subidas temporal."""
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def uploaded(client):
    """Sube el CSV de ejemplo y devuelve la respuesta JSON."""
    response = client.post(
        "/datasets", files={"file": ("ventas.csv", SAMPLE_CSV, "text/csv")}
    )
    assert response.status_code == 201
    return response.json()
