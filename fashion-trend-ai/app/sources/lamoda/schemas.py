# app/sources/lamoda/schemas.py

from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class Product:
    source: str
    product_url: str | None

    title: str | None = None
    description: str | None = None
    brand: str | None = None

    price: float | None = None
    old_price: float | None = None
    currency: str | None = "RUB"

    image_urls: list[str] = field(default_factory=list)

    source_category: str | None = None
    source_category_url: str | None = None

    brand_url: str | None = None
    brand_category: str | None = None
    brand_category_url: str | None = None

    category_path: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)

    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LinkItem:
    title: str
    url: str