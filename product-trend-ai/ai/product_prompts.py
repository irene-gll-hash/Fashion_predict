from __future__ import annotations

import json
from typing import Any


LAMODA_PRODUCT_ANALYSIS_SCHEMA: dict[str, Any] = {
    "product_type": "string",
    "base_product_type": "string",
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
Your task is NOT to repeat marketplace fields.
Your task is to add fashion-trend analytics.

Use the product image as the main source for visual attributes.
Use title, category, description, composition and color as supporting context.
Do not invent facts that are not visible or not supported by the product context.

Return ONLY valid JSON.
Do not use markdown.
Do not add explanations outside JSON.

Product context:
{json.dumps(compact_context, ensure_ascii=False, indent=2)}

Return JSON with this structure:
{json.dumps(LAMODA_PRODUCT_ANALYSIS_SCHEMA, ensure_ascii=False, indent=2)}

STRICT CATEGORY RULES:

fashion_category must be one of:
- top
- outerwear
- bottom
- dress
- shoes
- bag
- accessory
- underwear
- swimwear
- unknown

Use "top" for:
- sweatshirt
- hoodie
- zip-up hoodie
- track jacket / олимпийка
- pullover
- sweater
- cardigan
- shirt
- blouse
- t-shirt
- top

Use "outerwear" ONLY for:
- coat
- jacket intended as outerwear
- blazer
- trench coat
- parka
- puffer jacket
- vest/gilet intended as outerwear

Important:
- A hoodie is usually "top", not "outerwear".
- A sweatshirt is "top", not "outerwear".
- A track jacket / олимпийка in the hoodie/sweatshirt category is "top", not "outerwear".
- If marketplace category says "Худи и свитшоты", prefer fashion_category = "top".

Field instructions:

product_type:
- specific product type.
- Examples: sweatshirt, polo sweatshirt, graphic sweatshirt, hoodie, zip-up hoodie, cropped hoodie, track jacket, sweater, cardigan, t-shirt, blouse, shirt, dress, skirt, trousers, jeans, sneakers, boots, bag.
- Do not over-generalize product_type.
- If the item is a sweatshirt with a polo collar and button placket, product_type should be "polo sweatshirt", not just "sweatshirt".
- If the item is a hoodie with a zipper, product_type should be "zip-up hoodie", not just "hoodie".

base_product_type:
- broader normalized product group for aggregation.
- Use one of: sweatshirt, hoodie, track jacket, sweater, cardigan, t-shirt, blouse, shirt, top, jacket, coat, trousers, jeans, skirt, dress, shoes, bag, accessory, unknown.
- Examples:
  - polo sweatshirt -> base_product_type: sweatshirt
  - graphic sweatshirt -> base_product_type: sweatshirt
  - zip-up hoodie -> base_product_type: hoodie
  - cropped hoodie -> base_product_type: hoodie
  - track jacket / олимпийка -> base_product_type: track jacket
  - hoodie -> base_product_type: hoodie
  - sweatshirt -> base_product_type: sweatshirt

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
- crew neck, v-neck, turtleneck, stand collar, polo collar, hooded, zip collar, unknown.
- If the neckline/collar is not clearly visible, use "unknown".
- Do not over-specify the neckline if the image does not clearly show it.

style_tags:
- practical fashion style labels: casual, sporty, athleisure, streetwear, minimal, classic, premium, romantic, business casual, outdoor.

aesthetic_tags:
- broader visual aesthetics: soft basic, neutral minimalism, sporty premium, relaxed casual, logo streetwear, clean everyday.

visible_colors:
- colors visible in the product itself, not background colors.
- Prefer normalized color names, for example: black, white, beige, light pink, light blue, dark brown.

pattern:
- solid, logo, graphic print, stripes, floral, animal print, colorblock, textured, unknown.

details:
- visible or strongly supported construction/design details: zipper, hood, kangaroo pocket, raglan sleeves, ribbed cuffs, logo print, high collar, drawstrings.

material_visual_guess:
- visual material impression, for example: cotton knit, fleece-back jersey, smooth jersey, viscose blend, denim, leather-like, satin-like.
- If composition is available, use it as context, but still write this as visual/material interpretation.

occasion:
- everyday, casual, sport, office, evening, outdoor, travel, homewear.

seasonality:
- summer, demi-season, autumn-winter, winter, all-season, unknown.

trend_keywords:
- short phrases useful for trend analytics, for example: pastel sweatshirt, relaxed casual, sporty basic, cropped hoodie, neutral minimalism.

short_trend_summary:
- one short sentence summarizing why this item may matter for trend analysis.

confidence:
- number from 0 to 1.
""".strip()
