from __future__ import annotations
from dataclasses import asdict
from typing import Any
from sources.zara.schemas import ZaraProduct

def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text

def _to_number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(" ", "").replace("\u00a0", "").replace(",", ".").replace("%", "")
    try:
        number = float(text)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number

def _split_comma_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            clean = _clean_text(item)
            if clean:
                result.append(clean)
        return result
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]

def _normalize_image_url(url: Any, width: int = 1024) -> str | None:
    clean = _clean_text(url)
    if not clean:
        return None
    return clean.replace("{width}", str(width))

def _unique_keep_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

def _extract_composition(record: dict[str, Any]) -> str | None:
    detailed = record.get("detailedComposition")
    if not isinstance(detailed, dict):
        return None
    parts = detailed.get("parts")
    if not isinstance(parts, list):
        return None
    composition_parts: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        part_description = _clean_text(part.get("description"))
        components = part.get("components")
        if not isinstance(components, list):
            continue
        material_parts = []
        for component in components:
            if not isinstance(component, dict):
                continue
            material = _clean_text(component.get("material"))
            percentage = _clean_text(component.get("percentage"))
            if material and percentage:
                material_parts.append(f"{material} {percentage}")
            elif material:
                material_parts.append(material)
        if material_parts:
            if part_description:
                composition_parts.append(f"{part_description}: {', '.join(material_parts)}")
            else:
                composition_parts.append(", ".join(material_parts))
    if not composition_parts:
        return None
    return "; ".join(composition_parts)

def _extract_care(record: dict[str, Any]) -> list[str]:
    product_care = record.get("productCare")
    if not isinstance(product_care, dict):
        return []
    icons = product_care.get("icons")
    if not isinstance(icons, list):
        return []
    result = []
    for icon in icons:
        if not isinstance(icon, dict):
            continue
        description = _clean_text(icon.get("description"))
        if description:
            result.append(description)
    return result

def _extract_country(record: dict[str, Any]) -> str | None:
    origin = record.get("origin")
    if isinstance(origin, list) and origin:
        return _clean_text(origin[0])
    return _clean_text(origin)

def _extract_variant_sizes(variant: dict[str, Any], record: dict[str, Any]) -> list[str]:
    variant_sizes = variant.get("sizes")
    if isinstance(variant_sizes, list) and variant_sizes:
        result = []
        for size in variant_sizes:
            if not isinstance(size, dict):
                continue
            size_name = _clean_text(size.get("name"))
            if size_name:
                result.append(size_name)
        if result:
            return _unique_keep_order(result)
    return _split_comma_list(record.get("sizes"))

def _extract_variant_images(variant: dict[str, Any], record: dict[str, Any]) -> list[str]:
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
    main_image = _normalize_image_url(record.get("mainImage"))
    if main_image:
        urls.insert(0, main_image)
    return _unique_keep_order(urls)

def _build_category_path(category: str | None) -> list[str]:
    if not category:
        return []
    return [part.strip() for part in category.replace("_", "-").split("-") if part.strip()]

def _build_zara_product_id(record: dict[str, Any], variant: dict[str, Any]) -> str:
    variant_product_id = _clean_text(variant.get("productId"))
    if variant_product_id:
        return f"zara_{variant_product_id}"
    reference = _clean_text(record.get("reference"))
    color_id = _clean_text(variant.get("id"))
    if reference and color_id:
        return f"zara_{reference}_{color_id}"
    raw_id = _clean_text(record.get("id"))
    if raw_id:
        return f"zara_{raw_id}"
    raise ValueError("Cannot build Zara product_id: missing productId/reference/id")

def normalize_zara_record(record: dict[str, Any]) -> list[ZaraProduct]:
    """
    Normalize one raw Zara record.
    Important:
    Zara raw product can contain several color variants inside colorsSizesImagesJSON.
    We return one normalized product per color variant.
    """
    variants = record.get("colorsSizesImagesJSON")
    if not isinstance(variants, list) or not variants:
        variants = [{}]
    normalized_products: list[ZaraProduct] = []
    parent_product_id = _clean_text(record.get("id"))
    reference = _clean_text(record.get("reference"))
    display_reference = _clean_text(record.get("displayReference"))
    brand = _clean_text(record.get("brand")) or "Zara"
    title = _clean_text(record.get("name"))
    category = _clean_text(record.get("category"))
    category_path = _build_category_path(category)
    keyword = _clean_text(record.get("keyword"))
    composition = _extract_composition(record)
    care = _extract_care(record)
    country = _extract_country(record)
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        product_id = _build_zara_product_id(record, variant)
        gallery_image_urls = _extract_variant_images(variant, record)
        main_image_url = gallery_image_urls[0] if gallery_image_urls else None
        description = _clean_text(variant.get("description")) or _clean_text(record.get("description"))
        price = _to_number(variant.get("price"))
        if price is None:
            price = _to_number(record.get("price"))
        old_price = _to_number(variant.get("oldPrice"))
        if old_price is None:
            old_price = _to_number(record.get("oldPrice"))
        discount = _to_number(variant.get("displayDiscountPercentage"))
        if discount is None:
            discount = _to_number(record.get("displayDiscountPercentage"))
        discount_label = (
            _clean_text(variant.get("discountLabel"))
            or _clean_text(variant.get("discountPercentage"))
            or _clean_text(record.get("discountLabel"))
            or _clean_text(record.get("discountPercentage"))
        )
        is_on_sale = variant.get("isOnSale")
        if is_on_sale is None:
            is_on_sale = record.get("isOnSale")
        product = ZaraProduct(
            product_id=product_id,
            source="zara",
            url=_clean_text(variant.get("productPageSelectedColor")) or _clean_text(record.get("productPage")),
            parent_product_id=parent_product_id,
            color_variant_product_id=_clean_text(variant.get("productId")),
            reference=reference,
            display_reference=display_reference,
            color_reference=_clean_text(variant.get("reference")),
            color_display_reference=_clean_text(variant.get("displayReference")),
            color_id=_clean_text(variant.get("id")),
            brand=brand,
            title=title,
            category=category,
            category_path=category_path,
            keyword=keyword,
            price=price,
            old_price=old_price,
            discount=discount,
            discount_label=discount_label,
            is_on_sale=is_on_sale if isinstance(is_on_sale, bool) else None,
            color=_clean_text(variant.get("name")) or _clean_text(record.get("colors")),
            hex_code=_clean_text(variant.get("hexCode")),
            sizes=_extract_variant_sizes(variant, record),
            availability=_clean_text(variant.get("availability")) or _clean_text(record.get("availability")),
            state=_clean_text(record.get("state")),
            first_visible_date=_clean_text(record.get("firstVisibleDate")),
            main_image_url=main_image_url,
            gallery_image_urls=gallery_image_urls,
            description=description,
            composition=composition,
            care=care,
            country=country,
            website=_clean_text(record.get("website")),
            category_page=_clean_text(record.get("categoryPage")),
            original=record,
        )
        normalized_products.append(product)
    return normalized_products

def normalize_zara_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for record in records:
        products = normalize_zara_record(record)
        for product in products:
            normalized.append(asdict(product))
    return normalized

def get_zara_image_urls(product: dict[str, Any]) -> list[str]:
    urls = []
    main_image_url = product.get("main_image_url")
    if isinstance(main_image_url, str) and main_image_url.strip():
        urls.append(main_image_url.strip())
    gallery_image_urls = product.get("gallery_image_urls")
    if isinstance(gallery_image_urls, list):
        for url in gallery_image_urls:
            if isinstance(url, str) and url.strip():
                urls.append(url.strip())
    return _unique_keep_order(urls)

def build_enriched_zara_product(
    product: dict[str, Any],
    gemini_result: dict[str, Any] | None,
) -> dict[str, Any]:
    gemini_result = gemini_result or {}
    status = gemini_result.get("status", "not_analyzed")
    gemini_analysis = gemini_result.get("gemini_analysis")
    analysis_meta = gemini_result.get("analysis_meta", {})
    return {
        "product_id": product.get("product_id"),
        "source": "zara",
        "url": product.get("url"),
        "original": product.get("original", {}),
        "normalized": {key: value for key, value in product.items() if key != "original"},
        "gemini_analysis": gemini_analysis,
        "analysis_status": status,
        "analysis_meta": analysis_meta,
    }