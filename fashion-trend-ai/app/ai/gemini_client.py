from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any
from google import genai
from google.genai import types


FASHION_ATTRIBUTE_PROMPT = """
You are a fashion product attribute extraction system.
Analyze the cropped fashion object image. The object was detected by another model as:
DINO_LABEL: {dino_label}
Return ONLY valid JSON. Do not add markdown. Do not add explanation.
Use this JSON structure exactly:
{{
  "category": "string",
  "subcategory": "string",
  "fit": "string",
  "silhouette": "string",
  "length": "string",
  "sleeve_type": "string",
  "waist_type": "string",
  "materials": ["string"],
  "textures": ["string"],
  "patterns": ["string"],
  "colors": ["string"],
  "style": ["string"],
  "details": ["string"],
  "occasion": ["string"],
  "confidence": "low | medium | high",
  "notes": "short string"
}}
Rules:
- Use null if an attribute is not visible or not applicable.
- Do not invent details that are not visible.
- Prefer concrete fashion vocabulary.
- category should be a broad item type: dress, top, shirt, blouse, t-shirt, skirt, jeans, pants, jacket, coat, shoes, sandals, handbag, belt, sunglasses, jewelry, unknown.
- subcategory should be more specific if visible.
- fit examples: oversized, slim, regular, relaxed, skinny, loose, fitted, unknown.
- silhouette examples: straight, A-line, flared, bodycon, flowy, structured, draped, unknown.
- materials examples: denim, leather, suede, satin, silk, cotton, wool, knitwear, lace, mesh, transparent fabric, synthetic fabric, unknown.
- style examples: classic, casual, streetwear, romantic, business, evening, minimalist, sporty, boho, unknown.
"""


class GeminiFashionClient:
    def __init__(
        self,
        project: str,
        location: str,
        model: str,
    ) -> None:
        self.model = model
        self.client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    def analyze_crop(self, crop_path: Path, dino_label: str) -> dict[str, Any]:
        image_bytes = crop_path.read_bytes()
        mime_type = self._get_mime_type(crop_path)
        prompt = FASHION_ATTRIBUTE_PROMPT.format(dino_label=dino_label)
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        text = response.text or ""
        return self._parse_json_response(text)

    @staticmethod
    def _get_mime_type(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if suffix == ".png":
            return "image/png"
        if suffix == ".webp":
            return "image/webp"
        raise ValueError(f"Unsupported image format: {path}")

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise ValueError(f"Gemini returned invalid JSON: {text}") from error
        if not isinstance(parsed, dict):
            raise ValueError(f"Gemini response is not a JSON object: {text}")
        return parsed