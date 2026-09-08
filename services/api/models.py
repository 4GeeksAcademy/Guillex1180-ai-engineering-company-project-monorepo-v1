import enum
import typing
from datetime import datetime, timedelta

import pydantic
from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Esquemas y enums compartidos desde packages/shared
try:
    from packages.shared.schemas import OriginEnum, StatusEnum
except ImportError:
    # Fallback para cuando se ejecuta desde la raíz del monorepo
    import sys
    from pathlib import Path

    _repo_root = Path(__file__).resolve().parent.parent.parent
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))
    from packages.shared.schemas import OriginEnum, StatusEnum


VALID_CATEGORIES = [
    "carrier_last_mile",
    "carrier_international",
    "warehouse_supplies",
    "packaging_materials",
    "reverse_logistics",
    "fleet_maintenance",
    "it_and_wms_software",
    "cleaning_and_facilities",
]


class SupplierStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


VALID_STATUSES = [
    SupplierStatus.ACTIVE.value,
    SupplierStatus.SUSPENDED.value,
]


class Country(str, enum.Enum):
    USA = "USA"
    SPAIN = "Spain"


class SupplierBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str
    country: Country
    categories: typing.List[str] = pydantic.Field(..., min_length=1)
    rate_per_shipment: float = pydantic.Field(..., gt=0)
    currency: typing.Literal["USD", "EUR"]
    status: SupplierStatus
    service_zone: typing.Optional[str] = None
    contact_email: typing.Optional[pydantic.EmailStr] = None
    notes: typing.Optional[str] = None

    @pydantic.model_validator(mode="after")
    def validate_categories_and_currency(self) -> typing.Self:
        invalid_categories = set(self.categories) - set(VALID_CATEGORIES)
        if invalid_categories:
            invalid_values = ", ".join(sorted(invalid_categories))
            raise ValueError(f"Invalid supplier categories: {invalid_values}")

        expected_currency = "USD" if self.country is Country.USA else "EUR"
        if self.currency != expected_currency:
            raise ValueError(
                f"Currency for {self.country.value} must be {expected_currency}"
            )

        return self


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    rate_per_shipment: typing.Optional[float] = pydantic.Field(default=None, gt=0)
    status: typing.Optional[SupplierStatus] = None
    notes: typing.Optional[str] = None


class SupplierResponse(SupplierBase):
    id: int
    updated_at: str

    @pydantic.field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("updated_at must be a valid ISO 8601 datetime") from error

        if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
            raise ValueError("updated_at must use the UTC timezone")

        return value


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 Base & Modelo Incident
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos SQLAlchemy del proyecto."""


class Incident(Base):
    """Modelo de datos para la tabla ``incidents``.

    Representa un incidente reportado en el sistema de gestión de
    incidencias centralizado.  Los timestamps ``created_at`` y
    ``updated_at`` se gestionan automáticamente a nivel de base de
    datos.
    """

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Identificador único autoincremental.",
    )
    incident_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        doc="Identificador único del CSV legacy (ej: TRF-000001). Opcional, usado para idempotencia.",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Título breve del incidente (obligatorio).",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Descripción detallada del incidente (obligatorio).",
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Categoría del incidente (ej: logistics_damage, it_outage).",
    )
    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum, name="status_enum", create_constraint=True),
        nullable=False,
        default=StatusEnum.OPEN,
        server_default=StatusEnum.OPEN.value,
        doc="Estado del incidente dentro de su ciclo de vida.",
    )
    origin: Mapped[OriginEnum] = mapped_column(
        Enum(OriginEnum, name="origin_enum", create_constraint=True),
        nullable=False,
        doc="Origen del reporte: customer, branch o internal.",
    )
    branch: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Sede donde ocurrió el incidente. Usar 'central' si no aplica una específica.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp UTC de creación del registro (autogenerado).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp UTC de la última modificación (autogenerado con onupdate).",
    )

    def __repr__(self) -> str:
        return f"<Incident id={self.id} title={self.title!r} status={self.status}>"


# ---------------------------------------------------------------------------
# Pydantic models for legacy auth / users / profiles (TinyDB)
# ---------------------------------------------------------------------------


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"


class User(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)
    id: int
    email: str
    hashed_password: str
    is_active: bool = True
    role: UserRole = UserRole.USER
    created_at: str = ""


class UserCreate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    name: str = pydantic.Field(..., min_length=1)
    email: pydantic.EmailStr
    password: str = pydantic.Field(..., min_length=6)
    phone: str | None = None
    address: str | None = None


class UserUpdate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    name: str | None = None
    email: pydantic.EmailStr | None = None
    password: str | None = pydantic.Field(default=None, min_length=6)
    phone: str | None = None
    address: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None


class UserResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)
    id: int
    email: str
    is_active: bool
    role: UserRole
    created_at: str
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class Profile(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)
    id: int
    user_id: int
    name: str
    phone: str | None = None
    address: str | None = None


class ProfileCreate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    user_id: int
    name: str = pydantic.Field(..., min_length=1)
    phone: str | None = None
    address: str | None = None


class ProfileUpdate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    name: str | None = pydantic.Field(default=None, min_length=1)
    phone: str | None = None
    address: str | None = None


class ProfileResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)
    id: int
    user_id: int
    name: str
    phone: str | None = None
    address: str | None = None
    email: str | None = None
    role: str | None = None


# ---------------------------------------------------------------------------
# Auth Pydantic models
# ---------------------------------------------------------------------------


class LoginResponse(pydantic.BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(pydantic.BaseModel):
    email: pydantic.EmailStr


class ForgotPasswordResponse(pydantic.BaseModel):
    message: str


class ResetPasswordRequest(pydantic.BaseModel):
    token: str
    password: str = pydantic.Field(..., min_length=6)


class PasswordActionResponse(pydantic.BaseModel):
    message: str


class ChangePasswordRequest(pydantic.BaseModel):
    current_password: str
    new_password: str = pydantic.Field(..., min_length=6)


class AuthMeResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)
    id: int
    email: str
    is_active: bool
    role: UserRole
    profile: ProfileResponse | None = None


class AuthUserResponse(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)
    id: int
    email: str
    is_active: bool
    role: UserRole
    created_at: str
