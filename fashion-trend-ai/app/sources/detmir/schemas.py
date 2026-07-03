from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
@dataclass
class DetmirProduct:
    product_id: str
    url: str
    title: str | None = None
    description: str | None = None
    brand: str | None = None
    category_path: list[str] = field(default_factory=list)
    price: float | None = None
    old_price: float | None = None
    currency: str | None = "RUB"
    image_urls: list[str] = field(default_factory=list)
    age_group: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
