from __future__ import annotations
import json
from typing import Any
from fashion.taxonomy import format_taxonomy_for_prompt
from fashion.attributes import format_attributes_for_prompt

PRODUCT_ANALYSIS_SCHEMA: dict[str, Any] = {
    "main_product": {
        "category": "string | null",
        "subcategory": "string | null",
        "specific_type": "string | null",
        "commercial_name_ru": "string | null",
        "commercial_name_en": "string | null",
        "confidence": 0.0,
    },
    "visible_items": [
        {
            "category": "string | null",
            "specific_type": "string | null",
            "role": "main_product | styling_item",
            "confidence": 0.0,
        }
    ],
    "attributes": {
        "fit": "string | null",
        "silhouette": "string | null",
        "length": "string | null",
        "sleeve_type": "string | null",
        "neckline": "string | null",
        "rise": "string | null",
        "leg_shape": "string | null",
        "details": ["string"],
    },
    "visual_features": {
        "colors": ["string"],
        "pattern": "string | null",
        "material_guess": ["string"],
        "texture": "string | null",
    },
    "style_tags": ["string"],
    "trend_tags": ["string"],
    "seasonality": ["string"],
    "visible_outfit_items": ["string"],
    "styling_context": "string",
    "outfit_aesthetic_tags": ["string"],
    "short_trend_summary": "string",
    "confidence": 0.0,
    "uncertainty": ["string"],
}

def build_product_prompt(product_context: dict[str, Any]) -> str:
    compact_context = {
        "product_id": product_context.get("product_id") or product_context.get("Артикул"),
        "source": product_context.get("source"),
        "brand": product_context.get("brand") or product_context.get("Бренд"),
        "title": product_context.get("title") or product_context.get("Название"),
        "category": product_context.get("category") or product_context.get("Категория"),
        "category_path": product_context.get("category_path"),
        "keyword": product_context.get("keyword"),
        "price": product_context.get("price") or product_context.get("Цена"),
        "old_price": product_context.get("old_price") or product_context.get("Старая цена"),
        "discount": product_context.get("discount") or product_context.get("Скидка"),
        "color": product_context.get("color") or product_context.get("Цвет"),
        "sizes": product_context.get("sizes") or product_context.get("Размер"),
        "availability": product_context.get("availability"),
        "season": product_context.get("season") or product_context.get("Сезон"),
        "collection": product_context.get("collection") or product_context.get("Коллекция"),
        "description": product_context.get("description") or product_context.get("Описание"),
        "composition": product_context.get("composition") or product_context.get("Состав"),
        "country": product_context.get("country") or product_context.get("Страна производства"),
        "url": product_context.get("url") or product_context.get("URL"),
    }

    taxonomy_text = format_taxonomy_for_prompt()
    attributes_text = format_attributes_for_prompt()

    return f"""
You are analyzing a fashion ecommerce product card.

You will receive one or more images and structured product context.
Your task is to extract structured fashion-trend analytics, not to repeat marketplace fields.
Do not make purchase recommendations.
Do not decide whether the item should be bought.
Return ONLY valid JSON.
Do not use markdown.
Do not add explanations outside JSON.

Product context:
{json.dumps(compact_context, ensure_ascii=False, indent=2)}

Allowed product taxonomy:
{taxonomy_text}

Allowed attributes:
{attributes_text}

Return JSON with exactly this structure:
{json.dumps(PRODUCT_ANALYSIS_SCHEMA, ensure_ascii=False, indent=2)}

CORE RULES:
1. Determine the MAIN PRODUCT being sold using product title, category, description and images together.
2. Do not analyze the image alone if product text metadata is available.
3. Also list other visible fashion items in the image if they are clearly visible.
4. Do not confuse styling items with the main product.
5. Use allowed product taxonomy values when possible.
6. If exact type is uncertain, use the closest allowed type and explain the uncertainty.
7. Use English snake_case values for categories, product types, attributes and tags.
8. commercial_name_ru must be a normal Russian commercial product name, for example: "широкие брюки", "худи", "кардиган", "рубашка", "платье миди".
9. trend_tags should describe useful fashion signals, for example: "wide_leg", "office_core", "minimal_basic", "cargo_pockets", "denim_total_look".
10. visible_items must include the main product and clearly visible styling items.
11. visible_outfit_items can be a simple text list of all visible outfit items.
12. material_guess is only a visual/text-based guess. If uncertain, mention it in uncertainty.
13. confidence must be a number from 0 to 1.

FIELD MEANINGS:
- main_product: the product being sold in this card.
- visible_items: all clearly visible fashion items in the image.
- attributes: concrete product attributes such as fit, length, sleeve type, neckline, rise, leg shape and details.
- visual_features: color, pattern, approximate material and texture.
- style_tags: broad style categories.
- trend_tags: more specific trend markers useful for later aggregation.
- styling_context: how the item is styled in the image.
- outfit_aesthetic_tags: aesthetic of the full outfit, not only the main product.
- short_trend_summary: one short Russian sentence describing the product as a fashion/trend item.
- uncertainty: list of unclear points or possible mistakes.

IMPORTANT:
If a field is unknown, use null, [] or an empty string according to the schema.
Do not invent exact fabric composition if it is not present in product context.
Do not include buying_relevance, buying_score, recommended_for, commercial_strengths or commercial_risks.
"""