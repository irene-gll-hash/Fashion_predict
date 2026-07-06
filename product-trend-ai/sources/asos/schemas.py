from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
@dataclass
class AsosProduct:
    product_id: str
    source: str
    url: str | None = None
    raw_id: str | None = None
    search_url: str | None = None
    brand: str | None = None
    title: str | None = None
    category: str | None = None
    category_path: list[str] = field(default_factory=list)
    keyword: str | None = None
    price: float | int | None = None
    old_price: float | int | None = None
    discount: float | int | None = None
    discount_label: str | None = None
    currency: str | None = None
    color: str | None = None
    sizes: list[str] = field(default_factory=list)
    availability: str | None = None
    main_image_url: str | None = None
    gallery_image_urls: list[str] = field(default_factory=list)
    scraped_at: str | None = None
    original: dict[str, Any] = field(default_factory=dict)