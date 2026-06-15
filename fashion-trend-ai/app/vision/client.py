from __future__ import annotations
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import requests

@dataclass
class GoogleVisionClient:
    api_key: str
    def analyze_image_file(self, image_path: str) -> dict[str, Any]:
        url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
        image_bytes = Path(image_path).read_bytes()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "requests": [
                {
                    "image": {"content": image_base64},
                    "features": [
                        {"type": "LABEL_DETECTION", "maxResults": 30},
                        {"type": "OBJECT_LOCALIZATION", "maxResults": 20},
                        {"type": "IMAGE_PROPERTIES", "maxResults": 10},
                        {"type": "TEXT_DETECTION", "maxResults": 20},
                        {"type": "LOGO_DETECTION", "maxResults": 10},
                    ],
                }
            ]
        }
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        result = data["responses"][0]
        if "error" in result:
            raise RuntimeError(result["error"])
        image_id = Path(image_path).stem
        return {
            "image_id": image_id,
            "image_path": image_path,
            "vision": {
                "objects": self._extract_objects(result),
                "labels": self._extract_labels(result),
                "colors": self._extract_colors(result),
                "ocr_text": self._extract_ocr_text(result),
                "logos": self._extract_logos(result),
            },
        }
    def _extract_objects(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "name": obj.get("name"),
                "score": obj.get("score"),
            }
            for obj in result.get("localizedObjectAnnotations", [])
        ]
    def _extract_labels(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "description": label.get("description"),
                "score": label.get("score"),
                "topicality": label.get("topicality"),
            }
            for label in result.get("labelAnnotations", [])
        ]
    def _extract_colors(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        colors = result.get("imagePropertiesAnnotation", {}).get("dominantColors", {}).get("colors", [])
        return [
            {
                "hex": self._rgb_to_hex(
                    item.get("color", {}).get("red", 0),
                    item.get("color", {}).get("green", 0),
                    item.get("color", {}).get("blue", 0),
                ),
                "rgb": {
                    "red": item.get("color", {}).get("red", 0),
                    "green": item.get("color", {}).get("green", 0),
                    "blue": item.get("color", {}).get("blue", 0),
                },
                "score": item.get("score"),
                "pixel_fraction": item.get("pixelFraction"),
            }
            for item in colors
        ]
    def _extract_ocr_text(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        annotations = result.get("textAnnotations", [])
        if not annotations:
            return []
        return [
            {
                "text": item.get("description"),
                "score": item.get("score"),
            }
            for item in annotations[:10]
            if item.get("description")
        ]
    def _extract_logos(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "description": logo.get("description"),
                "score": logo.get("score"),
            }
            for logo in result.get("logoAnnotations", [])
        ]
    def _rgb_to_hex(self, red: int, green: int, blue: int) -> str:
        return f"#{red:02x}{green:02x}{blue:02x}"