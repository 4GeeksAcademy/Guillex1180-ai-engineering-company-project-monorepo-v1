"""
Esquemas Pydantic v2 y enumerados compartidos para la entidad Incident.

Este módulo es consumido tanto por la API (services/api/) como por los
scripts de carga (scripts/seed_incidents.py) y cualquier otro componente
del monorepo que necesite trabajar con incidentes.

Ejemplo de uso:
    from packages.shared.schemas import IncidentCreate, StatusEnum

    incident = IncidentCreate(
        title="Paquete dañado",
        description="El paquete llegó con la caja abierta",
        category="logistics_damage",
        origin=OriginEnum.CUSTOMER,
        branch="Madrid-Centro",
    )
"""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerados
# ---------------------------------------------------------------------------


class StatusEnum(str, enum.Enum):
    """Estados posibles de un incidente dentro del ciclo de vida."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISCARDED = "discarded"


class OriginEnum(str, enum.Enum):
    """Orígenes desde los que se puede reportar un incidente."""

    CUSTOMER = "customer"
    BRANCH = "branch"
    INTERNAL = "internal"


# ---------------------------------------------------------------------------
# Esquemas Pydantic v2
# ---------------------------------------------------------------------------


class IncidentBase(BaseModel):
    """Campos comunes del modelo Incident con validaciones básicas.

    Todas las cadenas de texto se limpian de espacios extremos
    (strip_whitespace) y se exige longitud mínima 1 para evitar
    valores vacíos.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    incident_id: str | None = Field(
        default=None,
        min_length=1,
        strip_whitespace=True,
        description="Identificador único del CSV legacy (ej: TRF-000001). Opcional, se usa para idempotencia.",
        examples=["TRF-000001"],
    )
    title: str = Field(
        ...,
        min_length=1,
        strip_whitespace=True,
        description="Título del incidente (obligatorio, no vacío).",
        examples=["Paquete perdido en tránsito"],
    )
    description: str = Field(
        ...,
        min_length=1,
        strip_whitespace=True,
        description="Descripción detallada del incidente (obligatorio, no vacío).",
        examples=["El tracking número XXXX muestra entregado pero el cliente no recibió nada."],
    )
    category: str = Field(
        ...,
        min_length=1,
        strip_whitespace=True,
        description="Categoría del incidente (ej: logistics_damage, it_outage, etc.).",
        examples=["logistics_damage"],
    )
    status: StatusEnum = Field(
        default=StatusEnum.OPEN,
        description="Estado actual del incidente. Por defecto 'open'.",
    )
    origin: OriginEnum = Field(
        ...,
        description="Origen del reporte: cliente, sede o interno.",
        examples=[OriginEnum.CUSTOMER],
    )
    branch: str = Field(
        ...,
        min_length=1,
        strip_whitespace=True,
        description=(
            "Nombre de la sede donde ocurrió el incidente. "
            "Usar 'central' cuando no aplique una sede específica."
        ),
        examples=["Madrid-Centro", "central"],
    )


class IncidentCreate(IncidentBase):
    """Esquema para crear un nuevo incidente (entrada).

    Hereda todas las validaciones de :class:`IncidentBase`.
    Se espera que todos los campos requeridos estén presentes;
    la ausencia de cualquiera dispara un error de validación 422.
    """


class IncidentResponse(IncidentBase):
    """Esquema de respuesta para un incidente (salida).

    Incluye el identificador único y las marcas temporales
    generadas automáticamente por la base de datos.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador único del incidente (autoincremental).")
    created_at: datetime = Field(
        ...,
        description="Timestamp UTC de creación del registro.",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp UTC de la última modificación del registro.",
    )


# ---------------------------------------------------------------------------
# Mapeo CSV → Modelo (compartido entre seed y API)
# ---------------------------------------------------------------------------

CSV_STATUS_MAP: dict[str, StatusEnum] = {
    "OPEN": StatusEnum.OPEN,
    "CLOSED": StatusEnum.RESOLVED,
    "DISCARDED": StatusEnum.DISCARDED,
}

CSV_CATEGORY_MAP: dict[str, str] = {
    "LOST_PARCEL": "carrier_last_mile",
    "DELAYED_DELIVERY": "carrier_last_mile",
    "WRONG_ADDRESS": "carrier_last_mile",
    "RETURN_REQUEST": "reverse_logistics",
    "DAMAGE": "packaging_materials",
}

CSV_COUNTRY_BRANCH_MAP: dict[str, str] = {
    "US": "Los-Angeles",
    "ES": "Zaragoza",
}


def normalize_csv_status(raw: str | None) -> StatusEnum | None:
    """Normaliza un valor de estado desde el CSV al StatusEnum del modelo.

    Returns ``None`` si el valor es desconocido o está vacío.
    """
    if not raw or not raw.strip():
        return None
    return CSV_STATUS_MAP.get(raw.strip().upper())


def normalize_csv_category(raw: str | None) -> str | None:
    """Normaliza una categoría del CSV al formato estandarizado del modelo.

    Returns ``None`` si el valor no está en el mapa de categorías conocidas
    (por ejemplo, ``UNKNOWN``).
    """
    if not raw or not raw.strip():
        return None
    return CSV_CATEGORY_MAP.get(raw.strip().upper())


def normalize_csv_branch(country: str | None) -> str:
    """Calcula el nombre de sede a partir del país del CSV.

    Usa el nombre de la ciudad principal de operaciones en cada país.
    Por defecto retorna ``'central'`` cuando el país no está reconocido.
    """
    if not country or not country.strip():
        return "central"
    return CSV_COUNTRY_BRANCH_MAP.get(country.strip().upper(), "central")


def generate_title_from_description(description: str, max_chars: int = 60) -> str:
    """Genera un título breve a partir del contenido de la descripción.

    Si la descripción es más corta que ``max_chars`` se usa completa;
    en caso contrario se trunca en la última palabra completa antes
    del límite.
    """
    text = description.strip()
    if not text:
        return "Incidente sin descripción"
    if len(text) <= max_chars:
        return text
    # Truncar en la última palabra completa antes de max_chars
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        return truncated[:last_space] + "…"
    return truncated + "…"