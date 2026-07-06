from __future__ import annotations
from dataclasses import asdict
from typing import Any
from sources.zara.schemas import ZaraProduct


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


def _split_comma_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
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


def _first_not_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _extract_composition(record: dict[str, Any]) -> str | None:
    detailed = record.get("detailedComposition")
    if isinstance(detailed, dict):
        parts = []
        for value in detailed.values():
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
            elif isinstance(value, list):
                parts.extend(str(item).strip() for item in value if str(item).strip())
        if parts:
            return "; ".join(parts)
    return _clean_text(record.get("composition"))


def _extract_care(record: dict[str, Any]) -> list[str]:
    care = record.get("productCare") or record.get("care")
    if isinstance(care, list):
        return [str(item).strip() for item in care if str(item).strip()]
    if isinstance(care, str):
        return [care.strip()] if care.strip() else []
    return []


def _extract_country(record: dict[str, Any]) -> str | None:
    origin = record.get("origin")
    if isinstance(origin, dict):
        return _clean_text(origin.get("name") or origin.get("country"))
    return _clean_text(origin or record.get("country"))


def _extract_variant_sizes(variant: dict[str, Any], record: dict[str, Any]) -> list[str]:
    sizes = variant.get("sizes") or record.get("sizes")
    if isinstance(sizes, list):
        result = []
        for item in sizes:
            if isinstance(item, dict):
                size_name = item.get("name") or item.get("size") or item.get("value")
                if size_name:
                    result.append(str(size_name).strip())
            elif str(item).strip():
                result.append(str(item).strip())
        return result
    return _split_comma_list(sizes)


def _extract_old_format_variant_images(variant: dict[str, Any], record: dict[str, Any]) -> list[str]:
    urls: list[str] = []

    xmedia = variant.get("xmedia")
    if isinstance(xmedia, list):
        for image_url in xmedia:
            normalized = _normalize_image_url(image_url)
            if normalized:
                urls.append(normalized)

    pdp_media = variant.get("pdpMedia")
    if isinstance(pdp_media, dict):
        pdp_url = _normalize_image_url(pdp_media.get("url"))
        if pdp_url:
            urls.append(pdp_url)

        extra_info = pdp_media.get("extraInfo")
        if isinstance(extra_info, dict):
            delivery_url = _normalize_image_url(extra_info.get("deliveryUrl"))
            if delivery_url:
                urls.append(delivery_url)

    if not urls:
        main_image = _normalize_image_url(record.get("mainImage"))
        if main_image:
            urls.append(main_image)

    return _unique_keep_order(urls)


def _extract_new_format_images(record: dict[str, Any], color: dict[str, Any] | None = None) -> list[str]:
    urls: list[str] = []

    if color:
        color_images = color.get("images")
        if isinstance(color_images, list):
            for image_url in color_images:
                normalized = _normalize_image_url(image_url)
                if normalized:
                    urls.append(normalized)

    record_images = record.get("images")
    if isinstance(record_images, list):
        for image_url in record_images:
            normalized = _normalize_image_url(image_url)
            if normalized:
                urls.append(normalized)

    main_image = _normalize_image_url(
        record.get("mainImage")
        or record.get("image")
        or record.get("imageUrl")
    )
    if main_image:
        urls.append(main_image)

    return _unique_keep_order(urls)


def _build_category_path(record: dict[str, Any]) -> list[str]:
    category_path = []

    for key in ("section", "familyName", "subfamilyName", "category", "keyword"):
        value = _clean_text(record.get(key))
        if value:
            category_path.append(value)

    raw_category_path = record.get("category_path")
    if isinstance(raw_category_path, list):
        category_path.extend(str(item).strip() for item in raw_category_path if str(item).strip())

    return _unique_keep_order(category_path)


def _build_zara_product_id(record: dict[str, Any], color: dict[str, Any] | None = None) -> str:
    raw_id = _first_not_empty(
        color.get("productId") if color else None,
        record.get("id"),
        record.get("productId"),
        color.get("id") if color else None,
        record.get("reference"),
    )
    color_id = color.get("id") if color else None

    if raw_id and color_id:
        return f"zara_{raw_id}_{color_id}"

    if raw_id:
        return f"zara_{raw_id}"

    reference = _clean_text(record.get("reference")) or "unknown"
    return f"zara_{reference}"


def _normalize_old_format_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    variants = record.get("colorsSizesImagesJSON")

    if not isinstance(variants, list) or not variants:
        variants = [{}]

    normalized_products: list[dict[str, Any]] = []

    for variant in variants:
        if not isinstance(variant, dict):
            variant = {}

        images = _extract_old_format_variant_images(variant, record)

        product = ZaraProduct(
            product_id=_build_zara_product_id(record, variant),
            source="zara",
            url=_clean_text(
                variant.get("productPageSelectedColor")
                or record.get("productPage")
                or record.get("url")
            ),
            parent_product_id=_clean_text(record.get("id")),
            color_variant_product_id=_clean_text(variant.get("productId")),
            reference=_clean_text(record.get("reference")),
            display_reference=_clean_text(record.get("displayReference")),
            color_reference=_clean_text(variant.get("reference")),
            color_display_reference=_clean_text(variant.get("displayReference")),
            color_id=_clean_text(variant.get("id")),
            brand=_clean_text(record.get("brand")),
            title=_clean_text(record.get("name") or record.get("title")),
            category=_clean_text(record.get("category")),
            category_path=_build_category_path(record),
            keyword=_clean_text(record.get("keyword")),
            price=_to_number(_first_not_empty(variant.get("price"), record.get("price"))),
            old_price=_to_number(_first_not_empty(variant.get("oldPrice"), record.get("oldPrice"))),
            discount=_to_number(
                _first_not_empty(
                    variant.get("discountPercentage"),
                    record.get("discountPercentage"),
                    record.get("displayDiscountPercentage"),
                )
            ),
            discount_label=_clean_text(_first_not_empty(variant.get("discountLabel"), record.get("discountLabel"))),
            is_on_sale=_first_not_empty(variant.get("isOnSale"), record.get("isOnSale")),
            color=_clean_text(variant.get("name") or record.get("color")),
            hex_code=_clean_text(variant.get("hexCode")),
            sizes=_extract_variant_sizes(variant, record),
            availability=_clean_text(_first_not_empty(variant.get("availability"), record.get("availability"))),
            state=_clean_text(record.get("state")),
            first_visible_date=_clean_text(record.get("firstVisibleDate")),
            main_image_url=images[0] if images else None,
            gallery_image_urls=images,
            description=_clean_text(_first_not_empty(variant.get("description"), record.get("description"))),
            composition=_extract_composition(record),
            care=_extract_care(record),
            country=_extract_country(record),
            website=_clean_text(record.get("website")),
            category_page=_clean_text(record.get("categoryPage")),
            original=record,
        )

        normalized_products.append(asdict(product))

    return normalized_products


def _normalize_new_format_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    colors = record.get("colors")
    color = colors[0] if isinstance(colors, list) and colors and isinstance(colors[0], dict) else None

    images = _extract_new_format_images(record, color)

    product = ZaraProduct(
        product_id=_build_zara_product_id(record, color),
        source="zara",
        url=_clean_text(record.get("url") or record.get("productUrl") or record.get("productPage")),
        parent_product_id=_clean_text(record.get("id")),
        color_variant_product_id=_clean_text(record.get("id")),
        reference=_clean_text(record.get("reference")),
        display_reference=_clean_text(record.get("displayReference")),
        color_reference=_clean_text(color.get("reference") if color else None),
        color_display_reference=None,
        color_id=_clean_text(color.get("id") if color else None),
        brand=_clean_text(record.get("brand")),
        title=_clean_text(record.get("name") or record.get("title") or record.get("productName")),
        category=_clean_text(record.get("familyName") or record.get("category")),
        category_path=_build_category_path(record),
        keyword=_clean_text(record.get("subfamilyName")),
        price=_to_number(_first_not_empty(color.get("price") if color else None, record.get("price"))),
        old_price=_to_number(record.get("originalPrice") or record.get("oldPrice")),
        discount=_to_number(record.get("discountPercent") or record.get("discountPercentage")),
        discount_label=None,
        is_on_sale=bool(record.get("discountPercent")) if record.get("discountPercent") is not None else None,
        color=_clean_text(color.get("name") if color else record.get("color")),
        hex_code=None,
        sizes=[],
        availability=_clean_text(_first_not_empty(color.get("availability") if color else None, record.get("availability"))),
        state=None,
        first_visible_date=None,
        main_image_url=images[0] if images else None,
        gallery_image_urls=images,
        description=_clean_text(record.get("description")),
        composition=_extract_composition(record),
        care=_extract_care(record),
        country=_extract_country(record),
        website="zara",
        category_page=None,
        original=record,
    )

    return [asdict(product)]


def normalize_zara_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    if "colorsSizesImagesJSON" in record:
        return _normalize_old_format_record(record)

    if "colors" in record and ("images" in record or "url" in record or "name" in record):
        return _normalize_new_format_record(record)

    raise ValueError(f"Unknown Zara record format. Available keys: {list(record.keys())}")


def normalize_zara_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for record in records:
        if not isinstance(record, dict):
            continue
        normalized.extend(normalize_zara_record(record))

    return normalized


def get_zara_image_urls(product: dict[str, Any]) -> list[str]:
    urls = []

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


def build_enriched_zara_product(
    product: dict[str, Any],
    gemini_result: dict[str, Any] | None,
) -> dict[str, Any]:
    enriched = dict(product)

    if not gemini_result:
        enriched["gemini_analysis"] = None
        enriched["gemini_status"] = "missing"
        return enriched

    enriched["gemini_status"] = gemini_result.get("status")
    enriched["gemini_analysis"] = gemini_result.get("gemini_analysis") or gemini_result.get("analysis")

    if gemini_result.get("error"):
        enriched["gemini_error"] = gemini_result.get("error")

    return enriched