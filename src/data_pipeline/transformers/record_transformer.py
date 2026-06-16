import re
from dataclasses import dataclass

from data_pipeline.schemas.record import NormalizedRecord, make_record_id
from data_pipeline.transformers.embedding_text_builder import build_embedding_text


_WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class TransformResult:
    records: list[NormalizedRecord]
    invalid_count: int = 0
    duplicate_count: int = 0


def clean_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _WHITESPACE_RE.sub(" ", str(value)).strip()
    return cleaned or None


def split_keywords(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []

    candidates = value if isinstance(value, list) else re.split(r"[,;|]", value)
    keywords: list[str] = []
    seen: set[str] = set()

    for item in candidates:
        cleaned = clean_string(str(item))
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            keywords.append(cleaned)

    return keywords


def normalize_record(record: NormalizedRecord) -> NormalizedRecord | None:
    title = clean_string(record.title)
    if not title:
        return None

    source_record_id = clean_string(record.source_record_id)
    original_url = clean_string(record.original_url)
    record.record_id = make_record_id(
        source_name=clean_string(record.source_name) or record.source_name,
        source_record_id=source_record_id,
        title=title,
        original_url=original_url,
    )
    record.source_name = clean_string(record.source_name) or record.source_name
    record.source_file = clean_string(record.source_file) or record.source_file
    record.source_record_id = source_record_id
    record.title = title
    record.description = clean_string(record.description)
    record.period = clean_string(record.period)
    record.event_date = clean_string(record.event_date)
    record.location = clean_string(record.location)
    record.category = clean_string(record.category)
    record.keywords = split_keywords(record.keywords)
    record.data_type = clean_string(record.data_type)
    record.original_url = original_url
    record.image_url = clean_string(record.image_url)
    record.provider = clean_string(record.provider)
    record.license = clean_string(record.license)
    record.embedding_text = build_embedding_text(record)
    return record


def normalize_records(records: list[NormalizedRecord]) -> TransformResult:
    normalized: list[NormalizedRecord] = []
    seen: set[str] = set()
    invalid_count = 0
    duplicate_count = 0

    for record in records:
        normalized_record = normalize_record(record)
        if normalized_record is None:
            invalid_count += 1
            continue

        if normalized_record.record_id in seen:
            duplicate_count += 1
            continue

        seen.add(normalized_record.record_id)
        normalized.append(normalized_record)

    return TransformResult(
        records=normalized,
        invalid_count=invalid_count,
        duplicate_count=duplicate_count,
    )
