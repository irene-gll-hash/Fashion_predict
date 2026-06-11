from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel

def save_models_json(data: list[BaseModel], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    items = [item.model_dump(mode="json") for item in data]
    output_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def save_raw_json(data: Any, path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")