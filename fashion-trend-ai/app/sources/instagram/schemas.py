from pydantic import BaseModel, Field

class NormalizedPost(BaseModel):
    post_url: str
    source_username: str
    published_at: str | None = None
    raw_id: str | None = None
    raw_type: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    video_urls: list[str] = Field(default_factory=list)
    likes_count: int | None = None
    comments_count: int | None = None
    caption: str | None = None
    local_image_paths: list[str] = Field(default_factory=list)
    local_video_paths: list[str] = Field(default_factory=list)
    local_frame_paths: list[str] = Field(default_factory=list)