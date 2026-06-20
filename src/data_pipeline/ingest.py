import argparse
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from data_pipeline.config import PROJECT_ROOT, load_dotenv
from data_pipeline.embeddings import create_embedding_provider
from data_pipeline.extractors import (
    extract_historical_photos,
    extract_korea_by_period,
    extract_modern_history_archive,
)
from data_pipeline.loaders import MySQLLoader, QdrantLoader
from data_pipeline.loaders.qdrant_points import build_chunked_records
from data_pipeline.reports.ingestion_report import SourceSummary, write_ingestion_report
from data_pipeline.schemas.record import NormalizedRecord
from data_pipeline.transformers.record_transformer import normalize_record


SOURCE_FILES = {
    "historical_photos": {
        "source_name": "ehistory_historical_photos",
        "filename": "korea_policy_broadcasting_historical_photos_20251031.csv",
        "extractor": extract_historical_photos,
    },
    "modern_history_archive": {
        "source_name": "modern_history_archive",
        "filename": "modern_history_archive_list_20250902.zip",
        "extractor": extract_modern_history_archive,
    },
    "korea_by_period": {
        "source_name": "korea_by_period",
        "filename": "korea_by_period_04.zip",
        "extractor": extract_korea_by_period,
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest local historical data sources.")
    parser.add_argument(
        "--source",
        choices=["all", "historical_photos", "modern_history_archive", "korea_by_period"],
        default="all",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data" / "sources",
        help="Directory containing source files. If ./data is provided, ./data/sources is used.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum records per source.")
    parser.add_argument("--dry-run", action="store_true", help="Parse, normalize, and report only.")
    parser.add_argument("--load-mysql", action="store_true", help="Upsert records into MySQL.")
    parser.add_argument("--load-qdrant", action="store_true", help="Upsert vectors into Qdrant.")
    parser.add_argument("--collection", default=None, help="Qdrant collection name.")
    parser.add_argument("--reset-collection", action="store_true", help="Delete and recreate Qdrant collection.")
    parser.add_argument(
        "--report-path",
        type=Path,
        default=PROJECT_ROOT / "data" / "reports" / "latest_ingestion_report.json",
    )
    return parser.parse_args()


def selected_sources(source: str) -> list[str]:
    if source == "all":
        return list(SOURCE_FILES)
    return [source]


def resolve_input_dir(input_path: Path) -> Path:
    if input_path.name == "data" and (input_path / "sources").exists():
        return input_path / "sources"
    return input_path


def build_source_config(input_path: Path) -> dict[str, dict]:
    source_dir = resolve_input_dir(input_path)
    config: dict[str, dict] = {}
    for key, value in SOURCE_FILES.items():
        config[key] = {
            "source_name": value["source_name"],
            "path": source_dir / value["filename"],
            "extractor": value["extractor"],
        }
    return config


def process_source(
    key: str,
    source_config: dict[str, dict],
    limit: int | None,
    batch_size: int,
    mysql_loader: MySQLLoader | None,
    qdrant_loader: QdrantLoader | None,
    embedding_provider,
) -> tuple[SourceSummary, list[NormalizedRecord]]:
    config = source_config[key]
    path = config["path"]
    summary = SourceSummary(
        source_name=config["source_name"],
        source_file=str(path),
    )

    try:
        samples: list[NormalizedRecord] = []
        pending: list[NormalizedRecord] = []
        seen: set[str] = set()
        for extracted_record in config["extractor"](path, limit=limit):
            summary.extracted_count += 1
            normalized_record = normalize_record(extracted_record)
            if normalized_record is None:
                summary.invalid_count += 1
                continue
            if normalized_record.record_id in seen:
                summary.duplicate_count += 1
                continue
            seen.add(normalized_record.record_id)
            summary.normalized_count += 1
            summary.valid_count += 1
            if len(samples) < 3:
                samples.append(normalized_record)
            pending.append(normalized_record)
            if len(pending) >= batch_size:
                flush_batch(pending, summary, mysql_loader, qdrant_loader, embedding_provider)
                pending = []

        flush_batch(pending, summary, mysql_loader, qdrant_loader, embedding_provider)
        return summary, samples
    except Exception as exc:
        summary.errors.append(str(exc))
        summary.skipped_count = 1
        return summary, []


def flush_batch(
    records: list[NormalizedRecord],
    summary: SourceSummary,
    mysql_loader: MySQLLoader | None,
    qdrant_loader: QdrantLoader | None,
    embedding_provider,
) -> None:
    if not records:
        return
    if mysql_loader is not None:
        summary.mysql_upserted_count += mysql_loader.upsert_records(records)
    if qdrant_loader is not None and embedding_provider is not None:
        chunked_records = build_chunked_records(
            records,
            qdrant_loader.chunk_size,
            qdrant_loader.chunk_overlap,
        )
        skipped = len(records) - len({chunk.payload["document_id"] for chunk in chunked_records})
        summary.skipped_count += max(skipped, 0)
        if chunked_records:
            vectors = embedding_provider.embed_texts([chunk.text for chunk in chunked_records])
            summary.qdrant_upserted_count += qdrant_loader.upsert_chunked_records(chunked_records, vectors)


def main() -> None:
    load_dotenv()
    args = parse_args()
    dry_run = args.dry_run or not (args.load_mysql or args.load_qdrant)
    run_id = str(uuid.uuid4())
    started_at = utc_now()
    batch_size = int(os.getenv("BATCH_SIZE", os.getenv("INGESTION_BATCH_SIZE", "64")))

    summaries: list[SourceSummary] = []
    samples_by_source: dict[str, list[NormalizedRecord]] = {}
    source_config = build_source_config(args.input)

    mysql_loader = None if dry_run or not args.load_mysql else MySQLLoader()
    embedding_provider = None if dry_run or not args.load_qdrant else create_embedding_provider()
    qdrant_loader = (
        None
        if dry_run or not args.load_qdrant
        else QdrantLoader(
            vector_size=embedding_provider.dimension,
            collection_name=args.collection,
            reset_collection=args.reset_collection,
        )
    )

    for source_key in selected_sources(args.source):
        summary, samples = process_source(
            source_key,
            source_config,
            args.limit,
            batch_size,
            mysql_loader,
            qdrant_loader,
            embedding_provider,
        )
        samples_by_source[summary.source_name] = samples
        summaries.append(summary)

    finished_at = utc_now()
    write_ingestion_report(
        path=args.report_path,
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        dry_run=dry_run,
        source_summaries=summaries,
        samples_by_source=samples_by_source,
    )

    total_valid = sum(summary.valid_count for summary in summaries)
    total_errors = sum(len(summary.errors) for summary in summaries)
    print(f"run_id={run_id}")
    print(f"dry_run={dry_run}")
    print(f"valid_count={total_valid}")
    print(f"errors={total_errors}")
    if embedding_provider is not None and qdrant_loader is not None:
        total_qdrant = sum(summary.qdrant_upserted_count for summary in summaries)
        total_skipped = sum(summary.skipped_count for summary in summaries)
        print(f"qdrant_collection={qdrant_loader.collection_name}")
        print(f"fastembed_model={embedding_provider.model_name}")
        print(f"qdrant_upserted_chunks={total_qdrant}")
        print(f"skipped_records={total_skipped}")
    print(f"report_path={args.report_path}")


if __name__ == "__main__":
    main()
