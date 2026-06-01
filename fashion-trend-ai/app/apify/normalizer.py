from __future__ import annotations
from typing import Any
from pydantic import HttpUrl
from app.apify.schemas import InstagramPost

def normalize_apify_post(raw: dict[str, Any]) -> InstagramPost:
    """
    Преобразует один сырой JSON-объект из Apify Instagram Scraper
    в наш внутренний формат InstagramPost.
    """
    image_urls = extract_image_urls(raw)
    return InstagramPost(
        post_url=raw["url"],
        source_username=raw.get("ownerUsername"),
        caption=raw.get("caption"),
        published_at=raw.get("timestamp"),
        image_urls=image_urls,
        likes_count=raw.get("likesCount"),
        comments_count=raw.get("commentsCount"),
        raw_id=raw.get("shortCode"),
        raw_type=raw.get("type"),
    )

def normalize_apify_posts(raw_posts: list[dict[str, Any]]) -> list[InstagramPost]:
    """
    Преобразует список сырых Apify-постов в список InstagramPost.
    """
    return [normalize_apify_post(raw_post) for raw_post in raw_posts]

def extract_image_urls(raw: dict[str, Any]) -> list[HttpUrl]:
    """
    Достаёт все изображения из Instagram-поста.
    Правило:
    1. Берём displayUrl из childPosts.
    2. Берём значения из images.
    3. Берём displayUrl основного поста.
    4. Убираем дубли, сохраняя порядок.
    """
    urls: list[str] = []
    child_posts = raw.get("childPosts") or []
    for child in child_posts:
        if not isinstance(child, dict):
            continue
        child_display_url = child.get("displayUrl")
        if child_display_url:
            urls.append(child_display_url)
        child_images = child.get("images") or []
        urls.extend(_extract_urls_from_images_field(child_images))
    images = raw.get("images") or []
    urls.extend(_extract_urls_from_images_field(images))
    display_url = raw.get("displayUrl")
    if display_url:
        urls.append(display_url)
    return _deduplicate_urls(urls)

def _extract_urls_from_images_field(images: Any) -> list[str]:
    """
    Обрабатывает поле images.
    """
    urls: list[str] = []
    if not isinstance(images, list):
        return urls
    for image in images:
        if isinstance(image, str):
            urls.append(image)
            continue
        if isinstance(image, dict):
            for key in ("url", "displayUrl", "src"):
                value = image.get(key)
                if value:
                    urls.append(value)
                    break
    return urls

def _deduplicate_urls(urls: list[str]) -> list[HttpUrl]:
    """
    Убирает дубли ссылок.
    """
    seen: set[str] = set()
    unique_urls: list[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)
    return unique_urls