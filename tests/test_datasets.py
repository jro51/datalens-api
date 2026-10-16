from app.config import settings
from tests.conftest import ID_CSV, SAMPLE_CSV


def test_upload_returns_metadata(uploaded):
    assert uploaded["filename"] == "ventas.csv"
    assert uploaded["rows"] == 4
    assert uploaded["columns"] == 4
    assert "content" not in uploaded


def test_upload_rejects_non_csv_extension(client):
    response = client.post("/datasets", files={"file": ("datos.txt", b"a,b\n1,2\n")})
    assert response.status_code == 415


def test_upload_rejects_empty_file(client):
    response = client.post("/datasets", files={"file": ("vacio.csv", b"")})
    assert response.status_code == 422


def test_upload_rejects_file_over_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 0)
    response = client.post("/datasets", files={"file": ("ventas.csv", SAMPLE_CSV)})
    assert response.status_code == 413


def test_list_datasets(client, uploaded):
    response = client.get("/datasets")

    assert response.status_code == 200
    assert [d["id"] for d in response.json()] == [uploaded["id"]]


def test_list_datasets_supports_pagination(client):
    for name in ("a.csv", "b.csv", "c.csv"):
        client.post("/datasets", files={"file": (name, SAMPLE_CSV)})

    page = client.get("/datasets", params={"skip": 1, "limit": 1}).json()

    assert len(page) == 1
    assert page[0]["filename"] == "b.csv"


def test_summary(client, uploaded):
    response = client.get(f"/datasets/{uploaded['id']}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["stats"]["edad"]["nulls"] == 1
    assert "top" not in body["stats"]["precio"]


def test_summary_not_found(client):
    assert client.get("/datasets/999/summary").status_code == 404


def test_correlations(client, uploaded):
    response = client.get(f"/datasets/{uploaded['id']}/correlations")

    assert response.status_code == 200
    assert response.json()["columns"] == ["edad", "precio"]


def test_correlations_with_one_numeric_column_fails(client):
    upload = client.post("/datasets", files={"file": ("x.csv", b"a,b\n1,x\n2,y\n")})
    response = client.get(f"/datasets/{upload.json()['id']}/correlations")
    assert response.status_code == 422


def test_chart_returns_png(client, uploaded):
    response = client.get(f"/datasets/{uploaded['id']}/chart", params={"column": "precio"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_chart_invalid_column(client, uploaded):
    for column in ("ciudad", "no_existe"):
        response = client.get(f"/datasets/{uploaded['id']}/chart", params={"column": column})
        assert response.status_code == 422


def test_delete_removes_dataset(client, uploaded):
    assert client.delete(f"/datasets/{uploaded['id']}").status_code == 204
    assert client.get(f"/datasets/{uploaded['id']}/summary").status_code == 404
    assert client.get("/datasets").json() == []


def test_delete_not_found(client):
    assert client.delete("/datasets/999").status_code == 404


def test_identifier_columns_are_flagged_in_summary_and_excluded_from_correlations(client):
    upload = client.post("/datasets", files={"file": ("ids.csv", ID_CSV)}).json()

    summary = client.get(f"/datasets/{upload['id']}/summary").json()
    assert summary["stats"]["Index"]["identifier"] is True
    assert "mean" not in summary["stats"]["Index"]

    correlations = client.get(f"/datasets/{upload['id']}/correlations").json()
    assert correlations["columns"] == ["Price", "Stock"]
