from __future__ import annotations
from pydantic import BaseModel, HttpUrl

class InstagramPost(BaseModel):
    source: str = "instagram"
    post_url: HttpUrl
    source_username: str | None = None
    caption: str | None = None
    published_at: str | None = None
    image_urls: list[HttpUrl] = []
    video_urls: list[HttpUrl] = []
    likes_count: int | None = None
    comments_count: int | None = None
    raw_id: str | None = None
    raw_type: str | None = None