from __future__ import annotations
from dataclasses import asdict
from typing import Any
from sources.hm.field_mapping import HM_ALLOWED_MAIN_CATEGORY_PREFIXES
from sources.hm.schemas import HmProduct

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
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        cleaned = (
            value.replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .replace("USD", "")
            .replace("EUR", "")
            .replace(",", ".")
            .strip()
        )
        try:
            number = float(cleaned)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    return None

def _to_int(value: Any) -> int | None:
    number = _to_number(value)
    if number is None:
        return None
    return int(number)

def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "1"):
            return True
        if lowered in ("false", "no", "0"):
            return False
    return None

def _list_of_text(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if ";" in value:
            return [item.strip() for item in value.split(";") if item.strip()]
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]

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

def _is_allowed_hm_record(record: dict[str, Any]) -> bool:
    main_cat_code = _clean_text(record.get("mainCatCode"))
    if not main_cat_code:
        return True
    return any(main_cat_code.startswith(prefix) for prefix in HM_ALLOWED_MAIN_CATEGORY_PREFIXES)

def _build_hm_product_id(record: dict[str, Any]) -> str:
    raw_id = _clean_text(record.get("id") or record.get("productId") or record.get("articleCode"))
    if raw_id:
        return f"hm_{raw_id}"
    url = _clean_text(record.get("productUrl"))
    if url:
        return "hm_" + url.rstrip("/").split("/")[-1].replace(".html", "")
    return "hm_unknown"

def _build_category_path(record: dict[str, Any]) -> list[str]:
    main_cat_code = _clean_text(record.get("mainCatCode"))
    if not main_cat_code:
        return []
    parts = [part.strip() for part in main_cat_code.split("_") if part.strip()]
    return _unique_keep_order(parts)

def _extract_category(record: dict[str, Any]) -> str | None:
    category_path = _build_category_path(record)
    if not category_path:
        return _clean_text(record.get("mainCatCode"))
    if len(category_path) >= 2:
        return category_path[1]
    return category_path[0]

def _extract_image_urls(record: dict[str, Any]) -> list[str]:
    urls: list[str] = []

    product_image = _normalize_image_url(record.get("imageProductSrc"))
    if product_image:
        urls.append(product_image)

    model_image = _normalize_image_url(record.get("imageModelSrc"))
    if model_image:
        urls.append(model_image)

    gallery = record.get("galleryImages")
    if isinstance(gallery, list):
        for image_url in gallery:
            normalized = _normalize_image_url(image_url)
            if normalized:
                urls.append(normalized)

    return _unique_keep_order(urls)

def normalize_hm_record(record: dict[str, Any]) -> dict[str, Any] | None:
    if not _is_allowed_hm_record(record):
        return None

    images = _extract_image_urls(record)

    product = HmProduct(
        product_id=_build_hm_product_id(record),
        source="hm",
        url=_clean_text(record.get("productUrl")),
        raw_id=_clean_text(record.get("id")),
        tracking_id=_clean_text(record.get("trackingId")),
        brand=_clean_text(record.get("brandName")),
        title=_clean_text(record.get("productName")),
        category=_extract_category(record),
        category_path=_build_category_path(record),
        keyword=_clean_text(record.get("searchQuery")),
        price=_to_number(record.get("price")),
        price_min=_to_number(record.get("priceMin")),
        price_max=_to_number(record.get("priceMax")),
        formatted_price=_clean_text(record.get("formattedPrice")),
        old_price=None,
        discount=None,
        currency="USD" if _clean_text(record.get("locale")) == "en_us" else None,
        color=_clean_text(record.get("colorName")),
        color_code=_clean_text(record.get("colorCode")),
        swatch_color_names=_list_of_text(record.get("swatchColorNames")),
        swatch_color_codes=_list_of_text(record.get("swatchColorCodes")),
        sizes=_list_of_text(record.get("allSizes")),
        available_sizes=_list_of_text(record.get("availableSizes")),
        out_of_stock_sizes=_list_of_text(record.get("outOfStockSizes")),
        sizes_count=_to_int(record.get("sizesCount")),
        availability=_clean_text(record.get("stockState")),
        is_coming_soon=_to_bool(record.get("isComingSoon")),
        is_online=_to_bool(record.get("isOnline")),
        is_new_product=_to_bool(record.get("isNewProduct")),
        main_image_url=images[0] if images else None,
        model_image_url=_normalize_image_url(record.get("imageModelSrc")),
        gallery_image_urls=images,
        locale=_clean_text(record.get("locale")),
        page_number=_to_int(record.get("pageNumber")),
        original=record,
    )

    return asdict(product)

def normalize_hm_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_product_ids: set[str] = set()

    for record in records:
        if not isinstance(record, dict):
            continue

        product = normalize_hm_record(record)
        if not product:
            continue

        product_id = product["product_id"]
        if product_id in seen_product_ids:
            continue

        seen_product_ids.add(product_id)
        normalized.append(product)

    return normalized

def get_hm_image_urls(product: dict[str, Any]) -> list[str]:
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

def build_enriched_hm_product(
    product: dict[str, Any],
    gemini_result: dict[str, Any] | None,
) -> dict[str, Any]:
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