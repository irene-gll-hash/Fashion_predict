from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
@dataclass
class LamodaProduct:
    product_id: str
    source: str
    url: str | None
    brand: str | None = None
    title: str | None = None
    category: str | None = None
    category_path: list[str] = field(default_factory=list)
    price: float | int | None = None
    old_price: float | int | None = None
    discount: float | int | None = None
    color: str | None = None
    sizes: list[str] = field(default_factory=list)
    size_names: list[str] = field(default_factory=list)
    seller: str | None = None
    rating: float | int | None = None
    reviews: int | None = None
    questions: int | None = None
    season: str | None = None
    collection: str | None = None
    quantity: int | None = None
    main_image_url: str | None = None
    gallery_image_urls: list[str] = field(default_factory=list)
    description: str | None = None
    composition: str | None = None
    country: str | None = None
    original: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
