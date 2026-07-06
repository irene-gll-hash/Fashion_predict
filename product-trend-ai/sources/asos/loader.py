from __future__ import annotations
from pathlib import Path
from typing import Any
from sources.common.file_loader import load_records
def load_asos_products(input_file: Path) -> list[dict[str, Any]]:
    records = load_records(input_file)
    if isinstance(records, dict):
        for key in ("items", "products", "data", "results"):
            value = records.get(key)
            if isinstance(value, list):
                return value
    if not isinstance(records, list):
        raise ValueError(f"Expected list of ASOS records, got {type(records)}")
    return records
def find_asos_input_file(data_dir: Path, run_date: str) -> Path:
    input_file = data_dir / "asos" / run_date / "asos.json"
    if input_file.exists():
        return input_file
    raise FileNotFoundError(f"ASOS input file not found: {input_file}")