from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ZaraProduct:
    product_id: str
    source: str
    url: str | None = None
    parent_product_id: str | None = None
    color_variant_product_id: str | None = None
    reference: str | None = None
    display_reference: str | None = None
    color_reference: str | None = None
    color_display_reference: str | None = None
    color_id: str | None = None
    brand: str | None = None
    title: str | None = None
    category: str | None = None
    category_path: list[str] = field(default_factory=list)
    keyword: str | None = None
    price: float | int | None = None
    old_price: float | int | None = None
    discount: float | int | None = None
    discount_label: str | None = None
    is_on_sale: bool | None = None
    color: str | None = None
    hex_code: str | None = None
    sizes: list[str] = field(default_factory=list)
    availability: str | None = None
    state: str | None = None
    first_visible_date: str | None = None
    main_image_url: str | None = None
    gallery_image_urls: list[str] = field(default_factory=list)
    description: str | None = None
    composition: str | None = None
    care: list[str] = field(default_factory=list)
    country: str | None = None
    website: str | None = None
    category_page: str | None = None
    original: dict[str, Any] = field(default_factory=dict)