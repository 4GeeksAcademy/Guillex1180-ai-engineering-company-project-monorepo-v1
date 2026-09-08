"""
Router CRUD para la entidad Incident.

Provee endpoints de creación, listado, detalle, actualización de
estado (con máquina de estados) y resumen agregado.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrapping: asegurar que el monorepo root está en sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from packages.shared.schemas import (
    IncidentCreate,
    IncidentResponse,
    OriginEnum,
    StatusEnum,
)

try:
    from ...database import get_db
    from ...models import Incident
except ImportError:
    from services.api.database import get_db  # type: ignore[no-redef]
    from services.api.models import Incident  # type: ignore[no-redef]

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


# ---------------------------------------------------------------------------
# Esquemas internos del router
# ---------------------------------------------------------------------------


class StatusUpdate(BaseModel):
    """Esquema para el cambio de estado vía PATCH."""

    model_config = ConfigDict(extra="forbid")

    status: StatusEnum = Field(
        ...,
        description="Nuevo estado al que se desea transicionar.",
    )


# ---------------------------------------------------------------------------
# Máquina de estados
# ---------------------------------------------------------------------------

STATUS_TRANSITIONS: dict[StatusEnum, set[StatusEnum]] = {
    StatusEnum.OPEN: {StatusEnum.IN_PROGRESS, StatusEnum.DISCARDED},
    StatusEnum.IN_PROGRESS: {StatusEnum.RESOLVED, StatusEnum.DISCARDED},
    StatusEnum.RESOLVED: set(),       # final
    StatusEnum.DISCARDED: set(),      # final
}

TERMINAL_STATUSES: set[StatusEnum] = {StatusEnum.RESOLVED, StatusEnum.DISCARDED}


def validate_transition(current: StatusEnum, target: StatusEnum) -> None:
    """Valida que la transición ``current → target`` esté permitida.

    Raises:
        HTTPException 400 si la transición no es válida.
    """
    allowed = STATUS_TRANSITIONS.get(current, set())
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El estado '{current.value}' es final y no permite cambios. "
                f"No se puede transicionar a '{target.value}'."
            ),
        )
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Transición no válida: de '{current.value}' "
                f"solo se permite a {_format_allowed(allowed)}. "
                f"Se recibió '{target.value}'."
            ),
        )


def _format_allowed(states: set[StatusEnum]) -> str:
    return ", ".join(f"'{s.value}'" for s in sorted(states, key=lambda s: s.value))


# ---------------------------------------------------------------------------
# Dependencia helper
# ---------------------------------------------------------------------------


def _get_incident_or_404(incident_id: int, db: Session) -> Incident:
    """Obtiene un incidente por ID o lanza 404."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidente con id {incident_id} no encontrado.",
        )
    return incident


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
) -> Incident:
    """Crea una nueva incidencia.

    Valida todos los campos obligatorios a través del esquema
    ``IncidentCreate`` (Pydantic).  Devuelve el objeto persistido
    con su ``id`` generado y timestamps.
    """
    record = Incident(**{k: v for k, v in payload.model_dump().items() if v is not None})
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    status_filter: StatusEnum | None = Query(
        default=None, alias="status", description="Filtrar por estado."
    ),
    origin_filter: OriginEnum | None = Query(
        default=None, alias="origin", description="Filtrar por origen."
    ),
    branch_filter: str | None = Query(
        default=None, alias="branch", description="Filtrar por sede."
    ),
    category_filter: str | None = Query(
        default=None, alias="category", description="Filtrar por categoría."
    ),
    db: Session = Depends(get_db),
) -> list[Incident]:
    """Lista incidencias con filtros opcionales.

    Siempre devuelve ``200 OK``.  Si no hay registros o los filtros
    no coinciden, retorna una lista vacía ``[]``.
    """
    query = db.query(Incident)

    if status_filter is not None:
        query = query.filter(Incident.status == status_filter)
    if origin_filter is not None:
        query = query.filter(Incident.origin == origin_filter)
    if branch_filter is not None:
        query = query.filter(Incident.branch == branch_filter)
    if category_filter is not None:
        query = query.filter(Incident.category == category_filter)

    return query.order_by(Incident.created_at.desc()).all()


@router.get("/summary")
def incidents_summary(db: Session = Depends(get_db)) -> dict:
    """Devuelve métricas agregadas de todas las incidencias.

    Retorna cuatro contadores: por estado, por categoría, por origen
    y por sede.  Si no hay datos, todos los valores son ``0``.
    """
    total = db.query(func.count(Incident.id)).scalar() or 0

    if total == 0:
        return {
            "by_status": {s.value: 0 for s in StatusEnum},
            "by_category": {},
            "by_origin": {o.value: 0 for o in OriginEnum},
            "by_branch": {},
        }

    # Consultas agregadas
    by_status = dict(
        db.query(Incident.status, func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    )
    by_category = dict(
        db.query(Incident.category, func.count(Incident.id))
        .group_by(Incident.category)
        .all()
    )
    by_origin = dict(
        db.query(Incident.origin, func.count(Incident.id))
        .group_by(Incident.origin)
        .all()
    )
    by_branch = dict(
        db.query(Incident.branch, func.count(Incident.id))
        .group_by(Incident.branch)
        .all()
    )

    return {
        "by_status": {k.value if hasattr(k, "value") else k: v for k, v in by_status.items()},
        "by_category": dict(by_category),
        "by_origin": {k.value if hasattr(k, "value") else k: v for k, v in by_origin.items()},
        "by_branch": dict(by_branch),
    }


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
) -> Incident:
    """Obtiene el detalle de una incidencia por su ID numérico."""
    return _get_incident_or_404(incident_id, db)


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
) -> Incident:
    """Actualiza el estado de una incidencia respetando la máquina de estados.

    Transiciones permitidas:
        open       → in_progress, discarded
        in_progress → resolved, discarded
        resolved   → ❌ (final)
        discarded  → ❌ (final)
    """
    incident = _get_incident_or_404(incident_id, db)
    validate_transition(incident.status, payload.status)

    incident.status = payload.status
    db.commit()
    db.refresh(incident)
    return incident