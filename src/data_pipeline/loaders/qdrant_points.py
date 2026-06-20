import uuid
from dataclasses import dataclass
from typing import Any

from data_pipeline.schemas.record import NormalizedRecord


DEFAULT_CHUNK_SIZE = 700
DEFAULT_CHUNK_OVERLAP = 100
MIN_CHUNK_LENGTH = 2


@dataclass(frozen=True)
class ChunkedRecord:
    point_id: str
    text: str
    payload: dict[str, Any]


def chunk_text(
    text: str | None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    normalized = " ".join((text or "").split())
    if len(normalized) < MIN_CHUNK_LENGTH:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be greater than or equal to 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = end - chunk_overlap
    return chunks


def generate_point_id(document_id: str, chunk_index: int, content: str) -> str:
    key = f"{document_id}|{chunk_index}|{content[:200]}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def build_chunk_payload(record: NormalizedRecord, content: str, chunk_index: int) -> dict[str, Any]:
    metadata = {
        "record_id": record.record_id,
        "source_name": record.source_name,
        "source_record_id": record.source_record_id,
        "description": record.description,
        "period": record.period,
        "event_date": record.event_date,
        "location": record.location,
        "keywords": record.keywords,
        "data_type": record.data_type,
        "image_url": record.image_url,
        "provider": record.provider,
        "license": record.license,
        "raw_metadata": record.raw_metadata,
    }
    return {
        "content": content,
        "source": record.source_name or record.source_file,
        "title": record.title or record.record_id,
        "chunk_index": chunk_index,
        "document_id": record.record_id,
        "metadata": metadata,
        "record_id": record.record_id,
        "source_name": record.source_name,
        "source_file": record.source_file,
        "category": record.category,
        "url": record.original_url,
        "original_id": record.source_record_id,
        "raw_source": record.source_name,
        "file_path": record.source_file,
    }


def build_chunked_records(
    records: list[NormalizedRecord],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkedRecord]:
    chunked: list[ChunkedRecord] = []
    for record in records:
        text = record.embedding_text or record.description or record.title
        for chunk_index, content in enumerate(chunk_text(text, chunk_size, chunk_overlap)):
            chunked.append(
                ChunkedRecord(
                    point_id=generate_point_id(record.record_id, chunk_index, content),
                    text=content,
                    payload=build_chunk_payload(record, content, chunk_index),
                )
            )
    return chunked
