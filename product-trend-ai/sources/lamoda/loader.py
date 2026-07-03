from __future__ import annotations
from pathlib import Path
from typing import Any
from sources.common.file_loader import load_records
def load_lamoda_products(input_file: Path) -> list[dict[str, Any]]:
    records = load_records(input_file)
    if not records:
        raise ValueError(f"No Lamoda products found in file: {input_file}")
    return records
def find_lamoda_input_file(data_dir: Path, run_date: str) -> Path:
    compact_date = run_date.replace("-", "")
    date_dir = data_dir / "lamoda" / run_date
    preferred = date_dir / f"lamoda_products_{compact_date}.json"
    if preferred.exists():
        return preferred
    candidates = sorted(date_dir.glob("lamoda_products*.json"))
    if candidates:
        return candidates[0]
    raise FileNotFoundError(
        f"Lamoda input file not found. Expected: {preferred}"
    )
