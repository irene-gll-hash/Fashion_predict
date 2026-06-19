from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TAXONOMY_PATH = PROJECT_ROOT / "data" / "raw" / "fashion_taxonomy.json"

class FashionTaxonomy:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @classmethod
    def load(cls, path: Path = DEFAULT_TAXONOMY_PATH) -> "FashionTaxonomy":
        if not path.exists():
            raise FileNotFoundError(f"Fashion taxonomy not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            return cls(json.load(f))

    def get_categories(self) -> list[str]:
        categories = self.data.get("categories", [])
        if not categories:
            raise ValueError("categories is empty in fashion_taxonomy.json")
        return categories

    def get_dino_prompt(self) -> str:
        return ". ".join(self.get_categories()) + "."

    def get_gemini_categories_text(self) -> str:
        return ", ".join(self.get_categories())