from __future__ import annotations
from collections import Counter
from typing import Any
FASHION_KEEP_WORDS = {
    "dress","jacket","blazer","coat","trench coat","outerwear","top","shirt","blouse","t-shirt","pants","trousers","jeans","skirt","shorts","suit","vest","sweater","cardigan","shoe","footwear","sandal","heels","boots","loafers","sneakers","bag","handbag","shoulder bag","sunglasses","belt","scarf","jewelry","earrings","necklace","denim","leather","lace","silk","satin","linen","knit","sheer","metallic","formal wear","cocktail dress","day dress","haute couture","fashion","fashion design"
}
NOISE_WORDS = {
    "person","model","fashion model","photo shoot","foot","leg","waist","neck","shoulder","knee","ankle","hair","beauty","floor","flooring","wall","room","furniture","food","cake","travel","vacation","happiness"
}
def normalize_text(value: str) -> str:
    return value.strip().lower()
def is_useful_term(term: str) -> bool:
    normalized = normalize_text(term)
    if normalized in NOISE_WORDS:
        return False
    if normalized in FASHION_KEEP_WORDS:
        return True
    return False
def build_vision_context(vision_results: list[dict[str, Any]]) -> dict[str, Any]:
    object_counter = Counter()
    label_counter = Counter()
    color_counter = Counter()
    ocr_counter = Counter()
    logo_counter = Counter()
    post_summaries = []
    for post in vision_results:
        post_terms = Counter()
        media_examples = []
        for media in post.get("media", []):
            vision = media.get("vision", {})
            for obj in vision.get("objects", []):
                name = obj.get("name")
                if name and is_useful_term(name):
                    object_counter[name] += 1
                    post_terms[name] += 1
            for label in vision.get("labels", []):
                description = label.get("description")
                if description and is_useful_term(description):
                    label_counter[description] += 1
                    post_terms[description] += 1
            for color in vision.get("colors", [])[:3]:
                hex_color = color.get("hex")
                if hex_color:
                    color_counter[hex_color] += 1
            for item in vision.get("ocr_text", [])[:3]:
                text = item.get("text")
                if text:
                    ocr_counter[text] += 1
            for logo in vision.get("logos", []):
                description = logo.get("description")
                if description:
                    logo_counter[description] += 1
            if len(media_examples) < 3:
                media_examples.append({
                    "image_id": media.get("image_id"),
                    "image_path": media.get("image_path"),
                    "media_type": media.get("media_type")
                })
        post_summaries.append({
            "post_url": post.get("post_url"),
            "source_username": post.get("source_username"),
            "published_at": post.get("published_at"),
            "top_terms": [term for term, _ in post_terms.most_common(10)],
            "media_examples": media_examples
        })
    return {
        "top_objects": object_counter.most_common(30),
        "top_labels": label_counter.most_common(30),
        "top_colors": color_counter.most_common(20),
        "top_ocr_text": ocr_counter.most_common(20),
        "top_logos": logo_counter.most_common(20),
        "posts": post_summaries[:30]
    }