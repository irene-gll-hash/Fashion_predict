from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any
def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json_records(path)
    if suffix == ".csv":
        return _load_csv_records(path)
    if suffix in {".xlsx", ".xls"}:
        return _load_excel_records(path)
    raise ValueError(f"Unsupported input file format: {suffix}")
def _load_json_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return _ensure_dict_records(data)
    if isinstance(data, dict):
        for key in ("items", "products", "data", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return _ensure_dict_records(value)
    raise ValueError("JSON file must contain a list of product records.")
def _load_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]
def _load_excel_records(path: Path) -> list[dict[str, Any]]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "Excel loading requires pandas and openpyxl. "
            "Install them or use JSON/CSV input."
        ) from exc
    dataframe = pd.read_excel(path)
    dataframe = dataframe.where(pd.notnull(dataframe), None)
    return dataframe.to_dict(orient="records")
def _ensure_dict_records(records: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record #{index} is not a JSON object.")
        result.append(record)
    return result
