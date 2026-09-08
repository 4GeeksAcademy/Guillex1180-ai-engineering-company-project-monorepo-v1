"""
Tests del CRUD de incidencias (``/api/incidents``).

Usa una base de datos SQLite en archivo temporal para cada sesión de tests,
evitando efectos laterales entre pruebas y con la base de datos real.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.routers.incidents_crud import get_db
from models import Base, Incident
from packages.shared.schemas import OriginEnum, StatusEnum


@pytest.fixture(autouse=True)
def _db_session() -> Generator[Session]:
    """Crea engine + tablas + override de dependencia por test.

    Cada test obtiene su propia base SQLite en archivo temporal,
    con ``get_db`` apuntando a ella mediante ``dependency_overrides``.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def _get_test_db() -> Generator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db

    yield TestingSessionLocal()

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(db_path)
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_incident(_db_session: Session) -> Incident:
    """Crea un incidente de ejemplo directamente en la DB."""
    record = Incident(
        title="Paquete dañado",
        description="Llegó con la caja rota",
        category="logistics_damage",
        status=StatusEnum.OPEN,
        origin=OriginEnum.CUSTOMER,
        branch="Madrid-Centro",
    )
    _db_session.add(record)
    _db_session.commit()
    _db_session.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "title": "Incidente de prueba",
    "description": "Descripción de prueba para endpoint create",
    "category": "logistics_damage",
    "origin": "customer",
    "branch": "Barcelona-Sede",
}


# ============================================================================
# POST /api/incidents
# ============================================================================


class TestCreateIncident:
    def test_create_minimal(self, client: TestClient) -> None:
        response = client.post("/api/incidents", json=_VALID_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Incidente de prueba"
        assert data["category"] == "logistics_damage"
        assert data["status"] == "open"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_with_optional_fields(self, client: TestClient) -> None:
        payload = {**_VALID_PAYLOAD, "incident_id": "TRF-999999"}
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 201
        assert response.json()["incident_id"] == "TRF-999999"

    def test_create_missing_title_returns_422(self, client: TestClient) -> None:
        payload = {**{k: v for k, v in _VALID_PAYLOAD.items() if k != "title"}}
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_create_invalid_origin_returns_422(self, client: TestClient) -> None:
        payload = {**_VALID_PAYLOAD, "origin": "extraterrestre"}
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 422


# ============================================================================
# GET /api/incidents
# ============================================================================


class TestListIncidents:
    def test_list_empty(self, client: TestClient) -> None:
        response = client.get("/api/incidents")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_data(
        self, client: TestClient, sample_incident: Incident
    ) -> None:
        response = client.get("/api/incidents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == sample_incident.title

    def test_list_filter_by_status(
        self, client: TestClient, _db_session: Session
    ) -> None:
        _db_session.add_all([
            Incident(
                title="A",
                description="d1",
                category="c",
                status=StatusEnum.OPEN,
                origin=OriginEnum.CUSTOMER,
                branch="b",
            ),
            Incident(
                title="B",
                description="d2",
                category="c",
                status=StatusEnum.RESOLVED,
                origin=OriginEnum.BRANCH,
                branch="b",
            ),
        ])
        _db_session.commit()

        response = client.get("/api/incidents?status=open")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "A"

    def test_list_filter_by_origin_and_branch(
        self, client: TestClient, _db_session: Session
    ) -> None:
        _db_session.add_all([
            Incident(
                title="X",
                description="d",
                category="c",
                status=StatusEnum.OPEN,
                origin=OriginEnum.INTERNAL,
                branch="HQ",
            ),
            Incident(
                title="Y",
                description="d",
                category="c",
                status=StatusEnum.OPEN,
                origin=OriginEnum.BRANCH,
                branch="HQ",
            ),
        ])
        _db_session.commit()

        response = client.get("/api/incidents?origin=internal&branch=HQ")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "X"


# ============================================================================
# GET /api/incidents/{incident_id}
# ============================================================================


class TestGetIncident:
    def test_get_existing(
        self, client: TestClient, sample_incident: Incident
    ) -> None:
        response = client.get(f"/api/incidents/{sample_incident.id}")
        assert response.status_code == 200
        assert response.json()["title"] == sample_incident.title

    def test_get_non_existent(self, client: TestClient) -> None:
        response = client.get("/api/incidents/99999")
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"].lower()


# ============================================================================
# PATCH /api/incidents/{incident_id}/status
# ============================================================================


class TestUpdateStatus:
    def test_open_to_in_progress(
        self, client: TestClient, sample_incident: Incident
    ) -> None:
        response = client.patch(
            f"/api/incidents/{sample_incident.id}/status",
            json={"status": "in_progress"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

    def test_open_to_discarded(
        self, client: TestClient, sample_incident: Incident
    ) -> None:
        response = client.patch(
            f"/api/incidents/{sample_incident.id}/status",
            json={"status": "discarded"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "discarded"

    def test_in_progress_to_resolved(
        self, client: TestClient, _db_session: Session
    ) -> None:
        inc = Incident(
            title="Progresando",
            description="d",
            category="c",
            status=StatusEnum.IN_PROGRESS,
            origin=OriginEnum.BRANCH,
            branch="b",
        )
        _db_session.add(inc)
        _db_session.commit()

        response = client.patch(
            f"/api/incidents/{inc.id}/status",
            json={"status": "resolved"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    def test_terminal_cannot_change(
        self, client: TestClient, _db_session: Session
    ) -> None:
        inc = Incident(
            title="Resuelto",
            description="d",
            category="c",
            status=StatusEnum.RESOLVED,
            origin=OriginEnum.BRANCH,
            branch="b",
        )
        _db_session.add(inc)
        _db_session.commit()

        response = client.patch(
            f"/api/incidents/{inc.id}/status",
            json={"status": "open"},
        )
        assert response.status_code == 400
        assert "final" in response.json()["detail"].lower()

    def test_invalid_transition_returns_400(
        self, client: TestClient, sample_incident: Incident
    ) -> None:
        # open → resolved no está permitida (falta in_progress)
        response = client.patch(
            f"/api/incidents/{sample_incident.id}/status",
            json={"status": "resolved"},
        )
        assert response.status_code == 400

    def test_non_existent_returns_404(self, client: TestClient) -> None:
        response = client.patch(
            "/api/incidents/99999/status",
            json={"status": "discarded"},
        )
        assert response.status_code == 404


# ============================================================================
# GET /api/incidents/summary
# ============================================================================


class TestSummary:
    def test_summary_empty(self, client: TestClient) -> None:
        response = client.get("/api/incidents/summary")
        assert response.status_code == 200
        data = response.json()
        assert all(v == 0 for v in data["by_status"].values())
        assert data["by_category"] == {}
        assert data["by_branch"] == {}

    def test_summary_with_data(
        self, client: TestClient, _db_session: Session
    ) -> None:
        _db_session.add_all([
            Incident(
                title="A",
                description="d",
                category="logistics_damage",
                status=StatusEnum.OPEN,
                origin=OriginEnum.CUSTOMER,
                branch="Madrid",
            ),
            Incident(
                title="B",
                description="d",
                category="it_outage",
                status=StatusEnum.RESOLVED,
                origin=OriginEnum.INTERNAL,
                branch="Barcelona",
            ),
            Incident(
                title="C",
                description="d",
                category="logistics_damage",
                status=StatusEnum.OPEN,
                origin=OriginEnum.CUSTOMER,
                branch="Madrid",
            ),
        ])
        _db_session.commit()

        response = client.get("/api/incidents/summary")
        assert response.status_code == 200
        data = response.json()

        assert data["by_status"]["open"] == 2
        assert data["by_status"]["resolved"] == 1
        assert data["by_category"]["logistics_damage"] == 2
        assert data["by_category"]["it_outage"] == 1
        assert data["by_origin"]["customer"] == 2
        assert data["by_origin"]["internal"] == 1
        assert data["by_branch"]["Madrid"] == 2
        assert data["by_branch"]["Barcelona"] == 1


# ============================================================================
# Error handling global
# ============================================================================


class TestErrorHandling:
    def test_validation_error_returns_422_format(
        self, client: TestClient
    ) -> None:
        """Campos inválidos deben devolver 422 con estructura de error."""
        response = client.post("/api/incidents", json={})
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("title" in str(err.get("field", "")) for err in detail)

    def test_unknown_route_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/nonexistent")
        assert response.status_code == 404