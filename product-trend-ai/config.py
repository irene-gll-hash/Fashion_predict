from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent
load_dotenv(REPO_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")
DATA_DIR = PROJECT_ROOT / "data"
class Settings:
    apify_api_token: str | None = os.getenv("APIFY_API_TOKEN")
    google_vision_api_key: str | None = os.getenv("GOOGLE_VISION_API_KEY")
    gigachat_credentials: str | None = os.getenv("GIGACHAT_CREDENTIALS")
    gigachat_scope: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
    gigachat_verify_ssl: bool = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() == "true"
    google_cloud_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
settings = Settings()