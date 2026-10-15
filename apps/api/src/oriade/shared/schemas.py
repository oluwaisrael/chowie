from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Register(Login):
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=128)


class ResetRequest(Input):
    email: EmailStr


class Reset(Input):
    token: str = Field(min_length=32, max_length=100)
    password: str = Field(min_length=12, max_length=128)


class Line(Input):
    item_id: UUID
    quantity: int = Field(ge=1, le=20)
    modifiers: list[UUID] = Field(default_factory=list, max_length=10)

    @field_validator("modifiers")
    @classmethod
    def unique_modifiers(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Add-ons cannot be repeated.")
        return value


class Checkout(Input):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(pattern=r"^\+?[0-9 ()-]{7,25}$")
    location_id: UUID
    zone_id: UUID | None = None
    fulfillment: Literal["delivery", "pickup"]
    address: str = Field(default="", max_length=500)
    instructions: str = Field(default="", max_length=500)
    items: list[Line] = Field(min_length=1, max_length=30)


class StatusChange(Input):
    status: Literal["CONFIRMED", "PREPARING", "READY", "OUT_FOR_DELIVERY", "COMPLETED", "CANCELLED"]
    version: int = Field(ge=1)


class ModifierInput(Input):
    id: UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    price: int = Field(ge=0, le=100000000)
    available: bool = True


class ItemInput(Input):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=5, max_length=1000)
    price: int = Field(ge=0, le=100000000)
    category_id: UUID
    location_id: UUID
    image: str = Field(default="", max_length=1000)
    available: bool = True
    featured: bool = False
    modifiers: list[ModifierInput] = Field(default_factory=list, max_length=20)

    @field_validator("image")
    @classmethod
    def safe_image(cls, value):
        if value and not (value.startswith("https://") or value.startswith("/images/")):
            raise ValueError("Images must use HTTPS or a local /images/ path.")
        return value


class AddressInput(Input):
    label: str = Field(min_length=1, max_length=60)
    address: str = Field(min_length=5, max_length=500)
    phone: str = Field(pattern=r"^\+?[0-9 ()-]{7,25}$")


class CategoryInput(Input):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)


class LocationInput(Input):
    name: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=5, max_length=500)
    active: bool = True


class ZoneInput(Input):
    name: str = Field(min_length=2, max_length=100)
    location_id: UUID
    fee: int = Field(ge=0, le=100000000)
    active: bool = True


class StaffInput(Input):
    role: Literal["customer", "operator", "kitchen", "admin"]
    active: bool


class StockInput(Input):
    remaining: int | None = Field(default=None, ge=0, le=1000000)
