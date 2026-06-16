import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from data_pipeline.schemas.record import NormalizedRecord


@dataclass
class SourceSummary:
    source_name: str
    source_file: str
    extracted_count: int = 0
    normalized_count: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    duplicate_count: int = 0
    mysql_upserted_count: int = 0
    qdrant_upserted_count: int = 0
    skipped_count: int = 0
    errors: list[str] = field(default_factory=list)


RDB_FIELD_REASONS = {
    "record_id": "RDB and Vector DB join key.",
    "source_name": "Source filtering and lineage.",
    "source_file": "Source file traceability.",
    "source_record_id": "Original source identifier.",
    "title": "Exact display and filtering.",
    "description": "Detailed metadata display.",
    "period": "Period filtering.",
    "event_date": "Date filtering while preserving source expressions.",
    "location": "Location filtering and display.",
    "category": "Category filtering.",
    "keywords": "Keyword filtering.",
    "data_type": "Media or source type filtering.",
    "original_url": "Link back to source.",
    "image_url": "Image preview.",
    "provider": "Provider attribution.",
    "license": "License and rights checks.",
    "embedding_text": "Audit what was embedded.",
    "raw_metadata": "Preserve original fields for traceability.",
}

VECTOR_FIELD_REASONS = {
    "record_id": "Join search candidates back to RDB details.",
    "source_name": "Filter search candidates by source.",
    "source_file": "Lightweight lineage for debugging.",
    "title": "Search result display.",
    "description_preview": "Short search result context.",
    "period": "Search result filtering and display.",
    "event_date": "Search result filtering and display.",
    "category": "Search result filtering.",
    "keywords": "Search result filtering and ranking hints.",
    "data_type": "Search result filtering.",
    "original_url": "Direct source link when useful.",
    "image_url": "Preview display.",
    "provider": "Attribution in search results.",
}


def sample_records(records: list[NormalizedRecord]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": record.record_id,
            "title": record.title,
            "source_name": record.source_name,
            "embedding_text_preview": record.embedding_text[:300],
        }
        for record in records[:3]
    ]


def write_ingestion_report(
    path: Path,
    run_id: str,
    started_at: str,
    finished_at: str,
    dry_run: bool,
    source_summaries: list[SourceSummary],
    samples_by_source: dict[str, list[NormalizedRecord]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "dry_run": dry_run,
        "source_summary": [asdict(summary) for summary in source_summaries],
        "storage_policy": {
            "rdb_storage_reason": (
                "RDB stores normalized detailed metadata and raw_metadata so the backend can "
                "perform exact filtering, detail lookup, source verification, and original field tracing."
            ),
            "vector_storage_reason": (
                "Vector DB stores embedding vectors and the minimum payload needed for semantic "
                "candidate search; detailed records are fetched from RDB by record_id."
            ),
            "join_key": "record_id",
        },
        "rdb_fields": RDB_FIELD_REASONS,
        "vector_fields": VECTOR_FIELD_REASONS,
        "sample_records": {
            source_name: sample_records(records)
            for source_name, records in samples_by_source.items()
        },
        "errors": {
            summary.source_name: summary.errors
            for summary in source_summaries
            if summary.errors
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
