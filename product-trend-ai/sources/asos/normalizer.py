from __future__ import annotations
import re
from dataclasses import asdict
from typing import Any
from urllib.parse import parse_qs, urlparse
from sources.asos.field_mapping import ASOS_COLOR_KEYWORDS, ASOS_PRODUCT_TYPE_KEYWORDS
from sources.asos.schemas import AsosProduct
def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value).strip() or None
def _to_number(value: Any) -> float | int | None:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        cleaned = (
            value.replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .replace("USD", "")
            .replace("EUR", "")
            .replace("GBP", "")
            .replace(",", ".")
            .strip()
        )
        try:
            number = float(cleaned)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    return None
def _normalize_image_url(value: Any) -> str | None:
    url = _clean_text(value)
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
def _first_not_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None
def _extract_currency(*values: Any) -> str | None:
    joined = " ".join(str(value) for value in values if value not in (None, ""))
    if "£" in joined or "GBP" in joined:
        return "GBP"
    if "€" in joined or "EUR" in joined:
        return "EUR"
    if "$" in joined or "USD" in joined:
        return "USD"
    return None
def _calculate_discount(old_price: float | int | None, current_price: float | int | None) -> float | int | None:
    if old_price in (None, 0) or current_price is None:
        return None
    if current_price >= old_price:
        return None
    discount = round((old_price - current_price) / old_price * 100, 2)
    return int(discount) if float(discount).is_integer() else discount
def _extract_keyword(search_url: Any) -> str | None:
    url = _clean_text(search_url)
    if not url:
        return None
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    keyword_values = query.get("q")
    if keyword_values:
        return _clean_text(keyword_values[0])
    return None
def _title_from_slug(value: str) -> str:
    return " ".join(part for part in value.replace("-", " ").split() if part).title()
def _extract_brand(record: dict[str, Any]) -> str | None:
    product_url = _clean_text(record.get("productUrl"))
    if product_url:
        path_parts = [part for part in urlparse(product_url).path.split("/") if part]
        if path_parts:
            return _title_from_slug(path_parts[0])
    title = _clean_text(record.get("productName"))
    if not title:
        return None
    words = title.split()
    if len(words) >= 2 and words[1].lower() in ("training", "running", "sportswear"):
        return f"{words[0]} {words[1]}"
    return words[0]
def _extract_category(title: str | None) -> str | None:
    if not title:
        return None
    lowered = title.lower()
    for category, keywords in ASOS_PRODUCT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                return category
    return None
def _extract_color(title: str | None) -> str | None:
    if not title:
        return None
    lowered = title.lower().strip()
    in_match = re.search(r"\bin\s+([a-z][a-z\s\-]+)$", lowered)
    if in_match:
        raw_color = in_match.group(1).strip()
        for color in sorted(ASOS_COLOR_KEYWORDS, key=len, reverse=True):
            if color == raw_color or raw_color.endswith(color):
                return color
        return raw_color
    for color in sorted(ASOS_COLOR_KEYWORDS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(color)}\b", lowered):
            return color
    return None
def _build_asos_product_id(record: dict[str, Any]) -> str:
    raw_id = _clean_text(record.get("uniqueId") or record.get("id") or record.get("productId"))
    if raw_id:
        return f"asos_{raw_id}"
    product_url = _clean_text(record.get("productUrl"))
    if product_url:
        match = re.search(r"/prd/(\d+)", product_url)
        if match:
            return f"asos_{match.group(1)}"
        return "asos_" + product_url.rstrip("/").split("/")[-1].split("#")[0]
    return "asos_unknown"
def _extract_image_urls(record: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    image_url = _normalize_image_url(record.get("imageUrl"))
    if image_url:
        urls.append(image_url)
    images = record.get("images")
    if isinstance(images, list):
        for item in images:
            normalized = _normalize_image_url(item)
            if normalized:
                urls.append(normalized)
    return _unique_keep_order(urls)
def normalize_asos_record(record: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None
    title = _clean_text(record.get("productName") or record.get("title") or record.get("name"))
    if not title:
        return None
    old_price = _to_number(record.get("originalPrice") or record.get("oldPrice"))
    current_price = _to_number(record.get("currentPrice") or record.get("price"))
    price = _first_not_empty(current_price, old_price)
    images = _extract_image_urls(record)
    category = _extract_category(title)
    keyword = _extract_keyword(record.get("searchUrl"))
    product = AsosProduct(
        product_id=_build_asos_product_id(record),
        source="asos",
        url=_clean_text(record.get("productUrl") or record.get("url")),
        raw_id=_clean_text(record.get("uniqueId") or record.get("id") or record.get("productId")),
        search_url=_clean_text(record.get("searchUrl")),
        brand=_extract_brand(record),
        title=title,
        category=category,
        category_path=[value for value in ("asos", keyword, category) if value],
        keyword=keyword,
        price=price,
        old_price=old_price,
        discount=_calculate_discount(old_price, current_price),
        discount_label=None,
        currency=_extract_currency(record.get("originalPrice"), record.get("currentPrice")),
        color=_extract_color(title),
        sizes=[],
        availability=None,
        main_image_url=images[0] if images else None,
        gallery_image_urls=images,
        scraped_at=_clean_text(record.get("scrapedAt")),
        original=record,
    )
    return asdict(product)
def normalize_asos_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_product_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        product = normalize_asos_record(record)
        if not product:
            continue
        product_id = product["product_id"]
        if product_id in seen_product_ids:
            continue
        seen_product_ids.add(product_id)
        normalized.append(product)
    return normalized
def get_asos_image_urls(product: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    main_image_url = _normalize_image_url(product.get("main_image_url"))
    if main_image_url:
        urls.append(main_image_url)
    gallery_image_urls = product.get("gallery_image_urls")
    if isinstance(gallery_image_urls, list):
        for image_url in gallery_image_urls:
            normalized = _normalize_image_url(image_url)
            if normalized:
                urls.append(normalized)
    return _unique_keep_order(urls)
def build_enriched_asos_product(product: dict[str, Any], gemini_result: dict[str, Any] | None) -> dict[str, Any]:
    normalized = {key: value for key, value in product.items() if key != "original"}
    enriched = {
        "product_id": product.get("product_id"),
        "source": product.get("source"),
        "url": product.get("url"),
        "original": product.get("original"),
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