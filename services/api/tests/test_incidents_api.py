from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_analyze_success(trackflow_expected_csv_bytes: bytes) -> None:
    response = client.post(
        "/api/incidents/analyze",
        files={"file": ("incidents-trackflow.csv", trackflow_expected_csv_bytes, "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 100
    assert data["valid_records"] == 95
    assert data["invalid_records"] == 5


def test_get_export_after_analyze(trackflow_expected_csv_bytes: bytes) -> None:
    analyze_response = client.post(
        "/api/incidents/analyze",
        files={"file": ("incidents-trackflow.csv", trackflow_expected_csv_bytes, "text/csv")},
    )
    assert analyze_response.status_code == 200

    export_response = client.get("/api/incidents/results/export")
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"results.csv\"" in export_response.headers["content-disposition"]
    assert "metric,value" in export_response.text
    assert "total_processed,100" in export_response.text


def test_get_export_without_previous_analysis() -> None:
    response = client.get("/api/incidents/results/export")
    assert response.status_code == 404
    assert response.json()["detail"] == "No existe un análisis previo para exportar."


def test_post_analyze_without_file() -> None:
    response = client.post("/api/incidents/analyze")
    assert response.status_code == 400
    assert response.json()["detail"] == "No se proporcionó ningún archivo CSV."


def test_post_analyze_empty_file() -> None:
    response = client.post(
        "/api/incidents/analyze",
        files={"file": ("incidents-trackflow.csv", b"", "text/csv")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El archivo CSV está vacío."


def test_post_analyze_wrong_extension(single_valid_csv_bytes: bytes) -> None:
    response = client.post(
        "/api/incidents/analyze",
        files={"file": ("incidents-trackflow.txt", single_valid_csv_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El archivo no tiene un formato CSV válido."


def test_post_analyze_incompatible_structure() -> None:
    response = client.post(
        "/api/incidents/analyze",
        files={"file": ("incidents-trackflow.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert response.status_code == 400
    assert "Faltan columnas obligatorias" in response.json()["detail"]
