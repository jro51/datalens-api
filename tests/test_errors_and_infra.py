import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.database import get_db
from app.main import app
from tests.conftest import SAMPLE_CSV


def test_unexpected_error_returns_generic_500_and_saves_nothing(client, monkeypatch):
    def boom(self):
        raise RuntimeError("base de datos caída")

    monkeypatch.setattr(Session, "commit", boom)
    safe_client = TestClient(app, raise_server_exceptions=False)

    response = safe_client.post("/datasets", files={"file": ("ventas.csv", SAMPLE_CSV)})

    assert response.status_code == 500
    assert response.json() == {"detail": "Error interno del servidor."}
    assert client.get("/datasets").json() == []


def test_requests_are_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.main"):
        client.get("/health")

    assert any("GET /health -> 200" in record.message for record in caplog.records)


def test_lifespan_creates_tables(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    monkeypatch.setattr("app.main.engine", engine)

    with TestClient(app):
        assert "datasets" in inspect(engine).get_table_names()


def test_get_db_yields_and_closes_session():
    generator = get_db()
    db = next(generator)
    assert db is not None
    generator.close()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql://u:p@h/db?sslmode=require", "postgresql+psycopg://u:p@h/db?sslmode=require"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("sqlite:///./x.db", "sqlite:///./x.db"),
    ],
)
def test_database_url_is_normalized_for_psycopg(raw, expected):
    assert Settings(database_url=raw).database_url == expected
