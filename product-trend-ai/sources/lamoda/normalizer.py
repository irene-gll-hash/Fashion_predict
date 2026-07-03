from __future__ import annotations
from typing import Any
from sources.lamoda.schemas import LamodaProduct
def normalize_lamoda_record(record: dict[str, Any]) -> LamodaProduct:
    product_id = _to_str(record.get("Артикул") or record.get("article") or record.get("URL"))
    category = _to_optional_str(record.get("Категория"))
    category_path = _split_multi_value(category, separator="/")
    main_image_url = _to_optional_str(record.get("Картинка"))
    gallery_image_urls = _split_multi_value(record.get("Галерея"), separator=";")
    if main_image_url and main_image_url not in gallery_image_urls:
        gallery_image_urls.insert(0, main_image_url)
    return LamodaProduct(
        product_id=product_id,
        source="lamoda",
        url=_to_optional_str(record.get("URL")),
        brand=_to_optional_str(record.get("Бренд")),
        title=_to_optional_str(record.get("Название")),
        category=category,
        category_path=category_path,
        price=_to_number(record.get("Цена")),
        old_price=_to_number(record.get("Старая цена")),
        discount=_to_number(record.get("Скидка")),
        color=_to_optional_str(record.get("Цвет")),
        sizes=_split_multi_value(record.get("Размер"), separator=";"),
        size_names=_split_multi_value(record.get("Название размера"), separator=";"),
        seller=_to_optional_str(record.get("Продавец")),
        rating=_to_number(record.get("Рейтинг")),
        reviews=_to_int(record.get("Отзывы")),
        questions=_to_int(record.get("Вопросы")),
        season=_to_optional_str(record.get("Сезон")),
        collection=_to_optional_str(record.get("Коллекция")),
        quantity=_to_int(record.get("Количество")),
        main_image_url=main_image_url,
        gallery_image_urls=gallery_image_urls,
        description=_to_optional_str(record.get("Описание")),
        composition=_to_optional_str(record.get("Состав")),
        country=_to_optional_str(record.get("Страна производства")),
        original=record,
    )
def normalize_lamoda_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_lamoda_record(record).to_dict() for record in records]
def get_lamoda_image_urls(product: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    main_image_url = product.get("main_image_url")
    if isinstance(main_image_url, str) and main_image_url:
        urls.append(main_image_url)
    gallery = product.get("gallery_image_urls")
    if isinstance(gallery, list):
        for url in gallery:
            if isinstance(url, str) and url and url not in urls:
                urls.append(url)
    return urls
def build_enriched_lamoda_product(
    product: dict[str, Any],
    gemini_result: dict[str, Any] | None,
) -> dict[str, Any]:
    status = None
    gemini_analysis = None
    analysis_meta = None
    if gemini_result:
        status = gemini_result.get("status")
        gemini_analysis = gemini_result.get("gemini_analysis")
        analysis_meta = gemini_result.get("analysis_meta")
    return {
        "product_id": product.get("product_id"),
        "source": "lamoda",
        "url": product.get("url"),
        "original": product.get("original", {}),
        "normalized": {
            key: value
            for key, value in product.items()
            if key != "original"
        },
        "gemini_analysis": gemini_analysis,
        "analysis_status": status,
        "analysis_meta": analysis_meta,
    }
def _split_multi_value(value: Any, *, separator: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(separator) if part.strip()]
def _to_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
def _to_str(value: Any) -> str:
    text = _to_optional_str(value)
    if not text:
        raise ValueError("Required string value is missing.")
    return text
def _to_number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().replace(" ", "").replace(",", ".")
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number
def _to_int(value: Any) -> int | None:
    number = _to_number(value)
    if number is None:
        return None
    return int(number)
