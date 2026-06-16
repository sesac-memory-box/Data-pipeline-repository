import hashlib
from dataclasses import dataclass, field
from typing import Any


def make_record_id(
    source_name: str,
    source_record_id: str | None = None,
    title: str | None = None,
    original_url: str | None = None,
) -> str:
    parts = [source_name.strip()]
    if source_record_id:
        parts.append(source_record_id.strip())
    else:
        parts.extend([(title or "").strip(), (original_url or "").strip()])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


@dataclass
class NormalizedRecord:
    record_id: str
    source_name: str
    source_file: str
    source_record_id: str | None = None
    title: str = ""
    description: str | None = None
    period: str | None = None
    event_date: str | None = None
    location: str | None = None
    category: str | None = None
    keywords: list[str] = field(default_factory=list)
    data_type: str | None = None
    original_url: str | None = None
    image_url: str | None = None
    provider: str | None = None
    license: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    embedding_text: str = ""
