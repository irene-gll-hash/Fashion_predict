from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    apify_api_token: str | None = os.getenv("APIFY_API_TOKEN")
    google_vision_api_key: str | None = os.getenv("GOOGLE_VISION_API_KEY")

settings = Settings()