from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ai.gemini_client import GeminiProductClient
from ai.product_prompts import build_lamoda_product_prompt


class ProductGeminiAnalyzer:
    def __init__(
        self,
        client: GeminiProductClient | None = None,
        sleep_seconds: float = 1.0,
        max_retries: int = 3,
    ) -> None:
        self.client = client or GeminiProductClient()
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries

    def analyze_lamoda_product(
        self,
        product: dict[str, Any],
        image_paths: list[Path],
    ) -> dict[str, Any]:
        prompt = build_lamoda_product_prompt(product)

        last_error: str | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                analysis = self.client.analyze_product_images(
                    image_paths=image_paths,
                    prompt=prompt,
                )

                return {
                    "product_id": _get_lamoda_product_id(product),
                    "source": "lamoda",
                    "status": "ok",
                    "gemini_analysis": analysis,
                    "analysis_meta": {
                        "attempt": attempt,
                        "images_used": _make_relative_paths(image_paths),
                        "error": None,
                    },
                }

            except Exception as exc:
                last_error = str(exc)

                if attempt < self.max_retries:
                    time.sleep(self.sleep_seconds * attempt)

        return {
            "product_id": _get_lamoda_product_id(product),
            "source": "lamoda",
            "status": "error",
            "gemini_analysis": None,
            "analysis_meta": {
                "attempt": self.max_retries,
                "images_used": _make_relative_paths(image_paths),
                "error": last_error,
            },
        }


def _get_lamoda_product_id(product: dict[str, Any]) -> str:
    value = product.get("Артикул") or product.get("product_id") or product.get("URL")

    if not value:
        raise ValueError("Cannot determine Lamoda product_id. Missing Артикул and URL.")

    return str(value)


def _make_relative_paths(paths: list[Path]) -> list[str]:
    base_dir = Path.cwd().resolve()
    result: list[str] = []

    for path in paths:
        resolved = path.resolve()

        try:
            relative = resolved.relative_to(base_dir)
            result.append(relative.as_posix())
        except ValueError:
            result.append(path.as_posix())

    return result
