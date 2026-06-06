"""Pydantic schemas for the Item resource.

Separated into create/update/read shapes so the API surface is explicit:
clients never set ``id``, and updates are partial.
"""

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(ge=0)


class ItemCreate(ItemBase):
    """Payload for creating an item."""


class ItemUpdate(BaseModel):
    """Partial update — every field is optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, ge=0)


class Item(ItemBase):
    """Item as returned by the API."""

    id: int
