from __future__ import annotations
from pathlib import Path
from typing import Any
from sources.common.file_loader import load_records

def load_zara_products(input_file: Path) -> list[dict[str, Any]]:
    records = load_records(input_file)
    if not isinstance(records, list):
        raise ValueError(f"Expected list of Zara records, got {type(records)}")
    return records

def find_zara_input_file(data_dir: Path, run_date: str) -> Path:
    input_file = data_dir / "Zara" / run_date / "zara.json"
    if input_file.exists():
        return input_file
    raise FileNotFoundError(f"Zara input file not found: {input_file}")