from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
@dataclass
class MediaAsset:
    asset_id: str
    parent_id: str
    source: str
    source_type: str
    profile: str
    media_type: str
    url: str
    local_path: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
