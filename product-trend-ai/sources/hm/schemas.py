from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class HmProduct:
    product_id: str
    source: str
    url: str | None = None
    raw_id: str | None = None
    tracking_id: str | None = None
    brand: str | None = None
    title: str | None = None
    category: str | None = None
    category_path: list[str] = field(default_factory=list)
    keyword: str | None = None
    price: float | int | None = None
    price_min: float | int | None = None
    price_max: float | int | None = None
    formatted_price: str | None = None
    old_price: float | int | None = None
    discount: float | int | None = None
    currency: str | None = None
    color: str | None = None
    color_code: str | None = None
    swatch_color_names: list[str] = field(default_factory=list)
    swatch_color_codes: list[str] = field(default_factory=list)
    sizes: list[str] = field(default_factory=list)
    available_sizes: list[str] = field(default_factory=list)
    out_of_stock_sizes: list[str] = field(default_factory=list)
    sizes_count: int | None = None
    availability: str | None = None
    is_coming_soon: bool | None = None
    is_online: bool | None = None
    is_new_product: bool | None = None
    main_image_url: str | None = None
    model_image_url: str | None = None
    gallery_image_urls: list[str] = field(default_factory=list)
    locale: str | None = None
    page_number: int | None = None
    original: dict[str, Any] = field(default_factory=dict)