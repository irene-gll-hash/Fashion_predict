from __future__ import annotations
from typing import Any
from sources.lamoda.field_mapping import LAMODA_DEFAULT_CURRENCY, LAMODA_DEFAULT_SOURCE, LAMODA_FIELD_ALIASES
from sources.lamoda.schemas import LamodaProduct

def normalize_lamoda_record(record: dict[str, Any]) -> dict[str, Any]:
    raw_id = _first_text(record, "raw_id")
    url = _first_text(record, "url")
    product_id = _build_product_id(raw_id, url)
    category = _first_text(record, "category")
    category_path = _split_multi_value(category, separator="/")
    main_image_url = _normalize_image_url(_first_value(record, "main_image_url"))
    gallery_image_urls = _extract_gallery_image_urls(record)
    if main_image_url and main_image_url not in gallery_image_urls:
        gallery_image_urls.insert(0, main_image_url)
    sizes = _split_multi_value(_first_value(record, "sizes"), separator=";")
    size_names = _split_multi_value(_first_value(record, "size_names"), separator=";")
    price = _to_number(_first_value(record, "price"))
    old_price = _to_number(_first_value(record, "old_price"))
    discount = _to_number(_first_value(record, "discount"))
    currency = _first_text(record, "currency") or LAMODA_DEFAULT_CURRENCY
    product = LamodaProduct(
        product_id=product_id,
        source=LAMODA_DEFAULT_SOURCE,
        url=url,
        raw_id=raw_id,
        seller_article=_first_text(record, "seller_article"),
        brand=_first_text(record, "brand"),
        title=_first_text(record, "title"),
        category=category,
        category_path=category_path,
        price=price,
        old_price=old_price,
        discount=discount,
        formatted_price=_format_price(price, currency),
        currency=currency,
        color=_first_text(record, "color"),
        sizes=sizes,
        size_names=size_names,
        available_sizes=sizes,
        out_of_stock_sizes=[],
        sizes_count=len(sizes) if sizes else None,
        seller=_first_text(record, "seller"),
        rating=_to_number(_first_value(record, "rating")),
        reviews=_to_int(_first_value(record, "reviews")),
        questions=_to_int(_first_value(record, "questions")),
        season=_first_text(record, "season"),
        collection=_first_text(record, "collection"),
        quantity=_to_int(_first_value(record, "quantity")),
        availability=_first_text(record, "availability"),
        main_image_url=main_image_url,
        model_image_url=None,
        gallery_image_urls=gallery_image_urls,
        description=_first_text(record, "description"),
        composition=_first_text(record, "composition"),
        country=_first_text(record, "country"),
        original=record,
    )
    return product.to_dict()
def normalize_lamoda_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_product_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        product = normalize_lamoda_record(record)
        product_id = product["product_id"]
        if product_id in seen_product_ids:
            continue
        seen_product_ids.add(product_id)
        normalized.append(product)
    return normalized
def get_lamoda_image_urls(product: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    main_image_url = _normalize_image_url(product.get("main_image_url"))
    if main_image_url:
        urls.append(main_image_url)
    model_image_url = _normalize_image_url(product.get("model_image_url"))
    if model_image_url:
        urls.append(model_image_url)
    gallery_image_urls = product.get("gallery_image_urls")
    if isinstance(gallery_image_urls, list):
        for image_url in gallery_image_urls:
            normalized = _normalize_image_url(image_url)
            if normalized:
                urls.append(normalized)
    return _unique_keep_order(urls)
def build_enriched_lamoda_product(product: dict[str, Any], gemini_result: dict[str, Any] | None) -> dict[str, Any]:
    normalized = {key: value for key, value in product.items() if key != "original"}
    enriched = {
        "product_id": product.get("product_id"),
        "source": product.get("source"),
        "url": product.get("url"),
        "original": product.get("original", {}),
        "normalized": normalized,
        "gemini_analysis": None,
        "analysis_status": "missing",
        "analysis_meta": None,
    }
    if not gemini_result:
        return enriched
    enriched["analysis_status"] = gemini_result.get("status")
    enriched["gemini_analysis"] = gemini_result.get("gemini_analysis") or gemini_result.get("analysis")
    enriched["analysis_meta"] = gemini_result.get("analysis_meta")
    if gemini_result.get("error"):
        enriched["analysis_error"] = gemini_result.get("error")
    return enriched
def _first_value(record: dict[str, Any], field_key: str) -> Any:
    aliases = LAMODA_FIELD_ALIASES.get(field_key, [field_key])
    for alias in aliases:
        value = record.get(alias)
        if value not in (None, "", [], {}):
            return value
    return None
def _first_text(record: dict[str, Any], field_key: str) -> str | None:
    return _to_optional_str(_first_value(record, field_key))
def _build_product_id(raw_id: str | None, url: str | None) -> str:
    if raw_id:
        return f"lamoda_{_safe_id(raw_id)}"
    if url:
        tail = url.rstrip("/").split("/")[-1]
        if tail:
            return f"lamoda_{_safe_id(tail)}"
    raise ValueError("Lamoda product id is missing.")
def _safe_id(value: str) -> str:
    return str(value).strip().replace(" ", "_").replace("/", "_").replace("\\", "_").replace(".", "_").replace(":", "_")
def _extract_gallery_image_urls(record: dict[str, Any]) -> list[str]:
    value = _first_value(record, "gallery_image_urls")
    urls: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                normalized = _normalize_image_url(item.get("url") or item.get("src") or item.get("image"))
            else:
                normalized = _normalize_image_url(item)
            if normalized:
                urls.append(normalized)
    elif isinstance(value, str):
        separator = ";" if ";" in value else ","
        for part in value.split(separator):
            normalized = _normalize_image_url(part)
            if normalized:
                urls.append(normalized)
    return _unique_keep_order(urls)
def _split_multi_value(value: Any, *, separator: str) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, dict):
                text = _to_optional_str(item.get("name") or item.get("value") or item.get("size") or item.get("title"))
            else:
                text = _to_optional_str(item)
            if text:
                result.append(text)
        return _unique_keep_order(result)
    text = str(value).strip()
    if not text:
        return []
    if separator in text:
        return _unique_keep_order([part.strip() for part in text.split(separator) if part.strip()])
    if "," in text:
        return _unique_keep_order([part.strip() for part in text.split(",") if part.strip()])
    return [text]
def _normalize_image_url(value: Any) -> str | None:
    url = _to_optional_str(value)
    if not url:
        return None
    if url.startswith("//"):
        return f"https:{url}"
    return url
def _unique_keep_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
def _to_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
def _to_number(value: Any) -> int | float | None:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().replace(" ", "").replace("\u00a0", "").replace("₽", "").replace("руб.", "").replace("руб", "").replace("$", "").replace("€", "").replace("£", "").replace("%", "").replace(",", ".")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number
def _to_int(value: Any) -> int | None:
    number = _to_number(value)
    if number is None:
        return None
    return int(number)
def _format_price(price: int | float | None, currency: str | None) -> str | None:
    if price is None:
        return None
    if currency == "RUB":
        return f"{price} RUB"
    if currency == "USD":
        return f"${price}"
    if currency == "EUR":
        return f"{price} EUR"
    return str(price)