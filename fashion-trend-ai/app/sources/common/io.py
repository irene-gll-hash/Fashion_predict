from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_urls(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"URL file not found: {path}")

    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            urls.append(value)

    if not urls:
        raise ValueError(f"No URLs found in {path}")

    return urls


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    return json.loads(path.read_text(encoding="utf-8"))