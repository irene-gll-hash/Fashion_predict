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
    "visible_outfit_items": ["string"],
    "styling_context": ["string"],
    "outfit_aesthetic_tags": ["string"],
    "short_trend_summary": "string",
    "confidence": 0.0,
}
def build_lamoda_product_prompt(product_context: dict[str, Any]) -> str:
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
    return f"""
You are analyzing a fashion ecommerce product card.
You will receive one or more images and structured product context.
Your task is to produce fashion-trend analytics, not to repeat marketplace fields.
Return ONLY valid JSON.
Do not use markdown.
Do not add explanations outside JSON.
Product context:
{json.dumps(compact_context, ensure_ascii=False, indent=2)}
Return JSON with exactly this structure:
{json.dumps(LAMODA_PRODUCT_ANALYSIS_SCHEMA, ensure_ascii=False, indent=2)}
CORE RULE:
The structured product context defines the TARGET PRODUCT.
Images define visual details, styling, colors, silhouette, outfit context and trend signals.
If images show a full outfit, do not confuse the target product with other visible items.
The target product must be classified according to title, category, keyword and product context.
Other visible outfit items must go into visible_outfit_items.
PRODUCT FIELDS:
product_type:
- The most specific product name possible.
- This is the main field for trend analytics.
- Never use broad words like "top", "bottom", "outerwear", "clothing", "item" as product_type.
- Use concrete fashion product names.
- Examples: straight high-waist jeans, wide-leg cropped jeans, low-rise striped jeans, barrel trousers, biker jacket, zip-up hoodie, polo sweatshirt, cropped long-sleeve top, ruffled blouse, midi dress, linen hat, heeled sandals.
- If title clearly names the product, follow the title.
- Images may refine product_type, but must not override a clear title/category.
- If title says JEANS, product_type must be a jeans type, not blouse, even if the model also wears a blouse.
- If title says TROUSERS, product_type must be a trousers type.
- If title says SHORTS, product_type must be shorts.
- If title says DRESS or VESTIDO, product_type must be dress.
- If title says BLOUSE or BLUSA, product_type must be blouse.
- If title says JACKET, CHAQUETA or CAZADORA, product_type must be jacket.
base_product_type:
- Broader real product group for aggregation.
- Must still be a product group, not just "top" or "bottom", unless genuinely unclear.
- Examples:
  - straight high-waist jeans -> jeans
  - wide-leg cropped jeans -> jeans
  - low-rise striped jeans -> jeans
  - barrel trousers -> trousers
  - shorts -> shorts
  - biker jacket -> jacket
  - zip-up hoodie -> hoodie
  - polo sweatshirt -> sweatshirt
  - ruffled blouse -> blouse
  - midi dress -> dress
  - linen hat -> accessory
fashion_category:
- Very broad category used only for high-level grouping.
- This field must not replace product_type.
- Use one of: top, outerwear, bottom, dress, shoes, bag, accessory, underwear, swimwear, unknown.
- jeans, trousers, shorts, skirt -> bottom.
- blouse, shirt, t-shirt, sweatshirt, hoodie, sweater, cardigan, top -> top.
- coat, trench coat, blazer, biker jacket, puffer jacket, outerwear jacket -> outerwear.
- dress, jumpsuit, playsuit -> dress.
- sandals, sneakers, boots, shoes -> shoes.
- hat, belt, scarf, jewelry -> accessory.
target_gender:
- women, men, kids, unisex, unknown.
fit:
- oversized, relaxed, regular, slim, fitted, loose, unknown.
silhouette:
- Be specific when visible: straight, boxy, cropped, elongated, fitted, A-line, flared, wide, barrel, tapered, unknown.
length:
- cropped, waist-length, hip-length, long, midi, maxi, mini, unknown.
sleeve_type:
- sleeveless, short sleeve, long sleeve, raglan sleeve, dropped shoulder, unknown.
- For bottoms, shoes, bags and accessories use "unknown".
neckline:
- crew neck, v-neck, scoop neck, turtleneck, stand collar, polo collar, hooded, zip collar, unknown.
- For bottoms, shoes, bags and accessories use "unknown".
- If not clearly visible, use "unknown".
style_tags:
- Practical fashion style labels.
- Examples: casual, sporty, athleisure, streetwear, minimal, classic, premium, romantic, business casual, outdoor, evening, bohemian.
aesthetic_tags:
- Broader aesthetics of the target product.
- Examples: soft basic, neutral minimalism, sporty premium, relaxed casual, logo streetwear, clean everyday, romantic minimalism, summer smart casual.
visible_colors:
- Colors visible in the target product itself, not background colors.
- If full outfit is shown, do not include colors of other items unless they are part of the target product.
- Use normalized color names: black, white, beige, cream, light pink, light blue, dark brown, mid-blue, khaki, red, coral.
pattern:
- Pattern of the target product.
- Use one of: solid, logo, graphic print, stripes, floral, animal print, colorblock, textured, polka dot, lace, unknown.
details:
- Visible or strongly supported target-product design details.
- Examples: zipper, hood, kangaroo pocket, raglan sleeves, ribbed cuffs, logo print, high collar, drawstrings, pleats, belt loops, ruffled sleeves, lace, button placket, high waist, low rise, wide leg, cropped hem.
material_visual_guess:
- Visual/material interpretation of the target product.
- Use composition as context if available.
- Examples: cotton knit, fleece-back jersey, smooth jersey, viscose blend, denim, leather-like, satin-like, linen, lace, lightweight woven.
occasion:
- everyday, casual, sport, office, evening, outdoor, travel, homewear, smart casual.
seasonality:
- summer, demi-season, autumn-winter, winter, all-season, unknown.
trend_keywords:
- Short trend phrases useful for analytics.
- Examples: wide-leg jeans, low-rise trend, pastel stripes, romantic blouse, biker jacket, cropped hoodie, neutral minimalism, relaxed tailoring.
OUTFIT CONTEXT FIELDS:
visible_outfit_items:
- List all clearly visible fashion items in the images, including target product and other styling items.
- Examples: ruffled blouse, white jeans, heeled sandals, leather belt, oversized blazer.
- If only product-only images are visible, include only the target product.
styling_context:
- Describe outfit combinations and styling signals visible in the images.
- Examples: white monochrome outfit, romantic blouse with clean denim, casual denim with heeled sandals, summer smart casual styling.
- Do not put the target product type here only; describe how it is styled.
outfit_aesthetic_tags:
- Overall outfit aesthetics when images show a complete look.
- Examples: clean summer look, romantic minimalism, relaxed casual, soft feminine styling, neutral minimalism.
short_trend_summary:
- One short sentence explaining why the target product or outfit styling matters for trend analysis.
confidence:
- Number from 0 to 1.
- Use high confidence when title/category and image agree.
- Use lower confidence when images are ambiguous, missing or conflict with context.
FINAL CONSISTENCY CHECK:
Before returning JSON, check that product_type, base_product_type and fashion_category do not contradict title/category/keyword.
If title/category says the target product is jeans, trousers, shorts, dress, blouse or jacket, do not return another visible outfit item as product_type.
Return valid JSON object only.
""".strip()