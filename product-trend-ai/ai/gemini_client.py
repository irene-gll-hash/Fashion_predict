from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_ROOT.parent

load_dotenv(REPO_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
class GeminiProductClient:
    def __init__(
        self,
        model_name: str | None = None,
        project: str | None = None,
        location: str | None = None,
    ) -> None:
        self.model_name = model_name or DEFAULT_GEMINI_MODEL
        self.client = genai.Client(
            vertexai=True,
            project=project or os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    def analyze_product_images(
        self,
        image_paths: list[Path],
        prompt: str,
    ) -> dict[str, Any]:
        if not image_paths:
            raise ValueError("No image paths provided for Gemini analysis.")
        parts: list[Any] = [prompt]
        for image_path in image_paths:
            if not image_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image_bytes = image_path.read_bytes()
            mime_type = _guess_mime_type(image_path)
            parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
            )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=parts,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        text = response.text
        if not text:
            raise ValueError("Gemini returned empty response.")
        return _parse_json_response(text)
def _guess_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    raise ValueError(f"Unsupported image format: {path}")
def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini response must be a JSON object.")
    return parsed
