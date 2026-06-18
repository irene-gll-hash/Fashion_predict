from __future__ import annotations
from collections import Counter

LABEL_RU = {
    "dress": "платье",
    "skirt": "юбка",
    "top": "топ",
    "shirt": "рубашка",
    "jacket": "жакет",
    "jeans": "джинсы",
    "pants": "брюки",
    "jeans pants": "джинсы/брюки",
    "shoes": "обувь",
    "sandals": "сандалии",
    "handbag": "сумка",
    "sunglasses": "солнцезащитные очки",
    "belt": "ремень",
    "classic style": "классический стиль",
    "romantic style": "романтичный стиль",
    "evening style": "вечерний стиль",
    "minimalist style": "минимализм",
    "business style": "деловой стиль",
    "streetwear style": "стритвир",
    "casual style": "casual",
    "boho style": "boho",
    "sporty style": "спортивный стиль",
    "transparent fabric": "прозрачная ткань",
    "silk satin": "сатин / шёлковистая фактура",
    "denim": "деним",
    "lace": "кружево",
    "synthetic fabric": "синтетическая ткань",
    "cotton fabric": "хлопковая ткань",
    "suede": "замша",
    "wool": "шерсть",
    "leather": "кожа",
    "knitwear": "трикотаж",
}

def ru_label(label: str) -> str:
    return LABEL_RU.get(label, label)

def best_label(scores: list[dict]) -> str:
    if not scores:
        return "не определено"
    return ru_label(scores[0]["label"])

def build_fashion_context(results: list[dict]) -> str:
    category_counter = Counter()
    style_counter = Counter()
    material_counter = Counter()
    item_lines = []
    for index, item in enumerate(results, start=1):
        category = ru_label(item.get("dino_label", "не определено"))
        fashion_clip = item.get("fashion_clip", {})
        style = best_label(fashion_clip.get("style_scores", []))
        material = best_label(fashion_clip.get("material_scores", []))
        category_counter[category] += 1
        style_counter[style] += 1
        material_counter[material] += 1
        item_lines.append(f"- Объект {index}: категория — {category}; стиль — {style}; материал/фактура — {material}.")
    lines = []
    lines.append("Категории вещей:")
    for label, count in category_counter.most_common():
        lines.append(f"- {label}: {count}")
    lines.append("")
    lines.append("Стили:")
    for label, count in style_counter.most_common():
        lines.append(f"- {label}: {count}")
    lines.append("")
    lines.append("Материалы и фактуры:")
    for label, count in material_counter.most_common():
        lines.append(f"- {label}: {count}")
    lines.append("")
    lines.append("Объекты:")
    lines.extend(item_lines)
    return "\n".join(lines)