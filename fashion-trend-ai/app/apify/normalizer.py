from __future__ import annotations
from typing import Any
from pydantic import HttpUrl
from app.apify.schemas import InstagramPost

def normalize_apify_post(raw: dict[str, Any]) -> InstagramPost:
    """
    Преобразует один сырой Instagram-пост из Apify в нашу внутреннюю модель.
    """
    return InstagramPost(
        source="instagram",
        post_url=raw["url"],
        source_username=raw.get("ownerUsername"),
        caption=raw.get("caption"),
        published_at=raw.get("timestamp"),
        image_urls=extract_image_urls(raw),
        video_urls=extract_video_urls(raw),
        likes_count=raw.get("likesCount"),
        comments_count=raw.get("commentsCount"),
        raw_id=raw.get("shortCode") or raw.get("id"),
        raw_type=raw.get("type"),
    )

def normalize_apify_posts(raw_posts: list[dict[str, Any]]) -> list[InstagramPost]:
    """
    Преобразует список сырых Apify-постов в список InstagramPost.
    """
    return [normalize_apify_post(raw_post) for raw_post in raw_posts]

def extract_image_urls(raw: dict[str, Any]) -> list[HttpUrl]:
    """
    Достаёт все изображения из поста: childPosts, images, displayUrl.
    """
    urls: list[str] = []
    for child in _get_child_posts(raw):
        urls.extend(_extract_image_urls_from_item(child))
    urls.extend(_extract_image_urls_from_item(raw))
    return _deduplicate_urls(urls)

def extract_video_urls(raw: dict[str, Any]) -> list[HttpUrl]:
    """
    Достаёт все видео из поста: childPosts и основной объект.
    """
    urls: list[str] = []
    for child in _get_child_posts(raw):
        urls.extend(_extract_video_urls_from_item(child))
    urls.extend(_extract_video_urls_from_item(raw))
    return _deduplicate_urls(urls)

def _get_child_posts(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Возвращает childPosts только если это список объектов.
    """
    child_posts = raw.get("childPosts") or []
    if not isinstance(child_posts, list):
        return []
    return [child for child in child_posts if isinstance(child, dict)]

def _extract_image_urls_from_item(item: dict[str, Any]) -> list[str]:
    """
    Достаёт изображения из одного объекта поста или childPost.
    """
    urls: list[str] = []
    images = item.get("images") or []
    if isinstance(images, list):
        for image in images:
            if isinstance(image, str):
                urls.append(image)
            elif isinstance(image, dict):
                value = _get_first_existing_value(image, ("url", "displayUrl", "src"))
                if value:
                    urls.append(value)
    display_url = item.get("displayUrl")
    if isinstance(display_url, str) and display_url:
        urls.append(display_url)
    return urls

def _extract_video_urls_from_item(item: dict[str, Any]) -> list[str]:
    """
    Достаёт видео из одного объекта поста или childPost.
    """
    urls: list[str] = []
    value = _get_first_existing_value(item, ("videoUrl", "video_url", "videoPlayUrl"))
    if value:
        urls.append(value)
    videos = item.get("videos") or []
    if isinstance(videos, list):
        for video in videos:
            if isinstance(video, str):
                urls.append(video)
            elif isinstance(video, dict):
                value = _get_first_existing_value(video, ("url", "videoUrl", "src"))
                if value:
                    urls.append(value)
    return urls

def _get_first_existing_value(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    """
    Возвращает первое непустое строковое значение по списку ключей.
    """
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None

def _deduplicate_urls(urls: list[str]) -> list[str]:
    """
    Убирает дубли ссылок, сохраняя порядок.
    """
    seen: set[str] = set()
    unique_urls: list[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)
    return unique_urls