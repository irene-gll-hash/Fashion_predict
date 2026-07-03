from __future__ import annotations
import json
from typing import Any
LAMODA_PRODUCT_ANALYSIS_SCHEMA: dict[str, Any] = {
    "product_type": "string",
    "fashion_category": "string",
    "target_gender": "string",
    "fit": "string",
    "silhouette": "string",
    "length": "string",
    "sleeve_type": "string",
    "neckline": "string",
    "style_tags": ["string"],
    "aesthetic_tags": ["string"],
    "visible_colors": ["string"],
    "pattern": "string",
    "details": ["string"],
    "material_visual_guess": ["string"],
    "occasion": ["string"],
    "seasonality": ["string"],
    "trend_keywords": ["string"],
    "short_trend_summary": "string",
    "confidence": 0.0,
}
def build_lamoda_product_prompt(product_context: dict[str, Any]) -> str:
    """
    Builds a prompt for Gemini product-card analysis.
    The model should enrich the original marketplace data, not replace it.
    Original fields such as price, sizes, brand, title, description, composition,
    rating, reviews and URLs are preserved elsewhere in the final enriched file.
    """
    compact_context = {
        "article": product_context.get("Артикул"),
        "brand": product_context.get("Бренд"),
        "title": product_context.get("Название"),
        "category": product_context.get("Категория"),
        "price": product_context.get("Цена"),
        "old_price": product_context.get("Старая цена"),
        "discount": product_context.get("Скидка"),
        "color": product_context.get("Цвет"),
        "sizes": product_context.get("Размер"),
        "seller": product_context.get("Продавец"),
        "rating": product_context.get("Рейтинг"),
        "reviews": product_context.get("Отзывы"),
        "season": product_context.get("Сезон"),
        "collection": product_context.get("Коллекция"),
        "quantity": product_context.get("Количество"),
        "description": product_context.get("Описание"),
        "composition": product_context.get("Состав"),
        "country": product_context.get("Страна производства"),
        "url": product_context.get("URL"),
    }
    return f"""
You are analyzing a product card from a fashion marketplace.
You will receive one or more product images and structured product context.
Your task is NOT to repeat the marketplace fields. Your task is to add fashion-trend analytics.
Use the product image as the main source for visual attributes.
Use the title, category, description, composition and color as supporting context.
Do not invent facts that are not visible or not supported by the product context.
Return ONLY valid JSON.
Do not use markdown.
Do not add explanations outside JSON.
Product context:
{json.dumps(compact_context, ensure_ascii=False, indent=2)}
Return JSON with this structure:
{json.dumps(LAMODA_PRODUCT_ANALYSIS_SCHEMA, ensure_ascii=False, indent=2)}
Field instructions:
product_type:
- specific product type, for example: sweatshirt, hoodie, jacket, dress, skirt, trousers, jeans, sneakers, boots, bag.
fashion_category:
- broad category, for example: top, outerwear, bottom, dress, shoes, bag, accessory.
target_gender:
- women, men, kids, unisex, unknown.
fit:
- oversized, relaxed, regular, slim, fitted, loose, unknown.
silhouette:
- straight, boxy, cropped, elongated, fitted, A-line, flared, wide, unknown.
length:
- cropped, waist-length, hip-length, long, midi, maxi, mini, unknown.
sleeve_type:
- sleeveless, short sleeve, long sleeve, raglan sleeve, dropped shoulder, unknown.
neckline:
- crew neck, v-neck, turtleneck, stand collar, hooded, zip collar, unknown.
style_tags:
- practical fashion style labels: casual, sporty, athleisure, streetwear, minimal, classic, premium, romantic, business casual, outdoor, etc.
aesthetic_tags:
- broader visual aesthetics: soft basic, neutral minimalism, sporty premium, relaxed casual, logo streetwear, clean everyday, etc.
visible_colors:
- colors visible in the product itself, not background colors.
pattern:
- solid, logo, graphic print, stripes, floral, animal print, colorblock, textured, unknown.
details:
- visible or strongly supported construction/design details: zipper, hood, kangaroo pocket, raglan sleeves, ribbed cuffs, logo print, high collar, drawstrings, etc.
material_visual_guess:
- visual material impression, for example: cotton knit, fleece, smooth jersey, viscose blend, denim, leather-like, satin-like.
- If composition is available, use it as context, but still write this as a visual/material interpretation.
occasion:
- everyday, casual, sport, office, evening, outdoor, travel, homewear, etc.
seasonality:
- summer, demi-season, autumn-winter, winter, all-season, unknown.
trend_keywords:
- short phrases useful for trend analytics, for example: pastel sweatshirt, relaxed casual, sporty basic, cropped hoodie, neutral minimalism.
short_trend_summary:
- one short sentence summarizing why this item may matter for trend analysis.
confidence:
- number from 0 to 1.
""".strip()
