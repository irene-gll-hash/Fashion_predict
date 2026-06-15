from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    apify_api_token: str | None = os.getenv("APIFY_API_TOKEN")
    google_vision_api_key: str | None = os.getenv("GOOGLE_VISION_API_KEY")
    gigachat_credentials: str | None = os.getenv("GIGACHAT_CREDENTIALS")
    gigachat_scope: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
    gigachat_verify_ssl: bool = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() == "true"

settings = Settings()