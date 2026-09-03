import enum
import typing
from datetime import datetime, timedelta

import pydantic


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


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class User(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    id: int
    email: pydantic.EmailStr
    hashed_password: str
    is_active: bool = True
    role: UserRole = UserRole.USER
    created_at: str


class UserCreate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    email: pydantic.EmailStr
    password: str = pydantic.Field(..., min_length=8)
    name: str | None = pydantic.Field(default=None, min_length=1)
    phone: str | None = None
    address: str | None = None


class UserUpdate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    email: pydantic.EmailStr | None = None
    password: str | None = pydantic.Field(default=None, min_length=8)
    is_active: bool | None = None
    role: UserRole | None = None


class UserResponse(pydantic.BaseModel):
    id: int
    email: pydantic.EmailStr
    is_active: bool
    role: UserRole
    created_at: str


class LoginResponse(pydantic.BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthUserResponse(pydantic.BaseModel):
    id: int
    email: pydantic.EmailStr
    role: str
    is_active: bool


class AuthMeResponse(pydantic.BaseModel):
    user: AuthUserResponse
    profile: "Profile"


class Profile(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    id: int
    user_id: int
    name: str | None = pydantic.Field(default=None, min_length=1)
    phone: str | None = None
    address: str | None = None


class ProfileCreate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    user_id: int
    name: str | None = pydantic.Field(default=None, min_length=1)
    phone: str | None = None
    address: str | None = None


class ProfileUpdate(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = pydantic.Field(default=None, min_length=1)
    phone: str | None = None
    address: str | None = None


class ProfileResponse(Profile):
    pass
