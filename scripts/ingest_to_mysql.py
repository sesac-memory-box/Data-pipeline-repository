#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_pipeline.ingest import build_source_config, selected_sources
from data_pipeline.schemas.record import NormalizedRecord
from data_pipeline.transformers.record_transformer import normalize_record


DEFAULT_TABLE = "integrated_content"
REQUIRED_ENV_KEYS = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
TABLE_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
YEAR_RE = re.compile(r"(18|19|20)\d{2}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest normalized public data into MySQL RDS integrated_content."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data",
        help="Input directory. If ./data is provided, ./data/sources is used.",
    )
    parser.add_argument(
        "--source",
        choices=["all", "historical_photos", "modern_history_archive", "korea_by_period"],
        default="all",
        help="Source to ingest. Default: all.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum records per source.")
    parser.add_argument("--table", default=DEFAULT_TABLE, help=f"MySQL table. Default: {DEFAULT_TABLE}.")
    parser.add_argument("--batch-size", type=int, default=None, help="Upsert batch size. Default: MYSQL_INGEST_BATCH_SIZE or 10.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="Path to dotenv file. Default: repository .env.",
    )
    return parser.parse_args()


def missing_required_env(env: dict[str, str | None]) -> list[str]:
    return [key for key in REQUIRED_ENV_KEYS if not (env.get(key) or "").strip()]


def validate_table_name(table_name: str) -> str:
    if not TABLE_NAME_RE.fullmatch(table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name


def load_db_config(env_file: Path) -> dict[str, Any]:
    load_dotenv(env_file)
    env = {key: os.getenv(key) for key in REQUIRED_ENV_KEYS}
    missing = missing_required_env(env)
    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill DB_* values locally."
        )

    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer.") from exc

    return {
        "host": os.getenv("DB_HOST", "").strip(),
        "port": port,
        "database": os.getenv("DB_NAME", "").strip(),
        "user": os.getenv("DB_USER", "").strip(),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": os.getenv("DB_CHARSET", "utf8mb4").strip() or "utf8mb4",
    }


def connect(config: dict[str, Any]):
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError(
            "pymysql is required. Install dependencies with: python -m pip install -r requirements.txt"
        ) from exc

    return pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset=config["charset"],
        autocommit=False,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )


def ensure_table(connection: Any, table_name: str) -> None:
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
      content_id VARCHAR(64) PRIMARY KEY,
      source VARCHAR(100) NOT NULL,
      title VARCHAR(500),
      content_text MEDIUMTEXT,
      event_year INT NULL,
      era VARCHAR(50),
      category VARCHAR(100),
      url TEXT,
      metadata JSON,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """
    with connection.cursor() as cursor:
        cursor.execute(ddl)


def stable_content_id(record: NormalizedRecord) -> str:
    if record.record_id:
        return record.record_id
    key = "|".join(
        [
            record.source_name or "",
            record.title or "",
            record.embedding_text or record.description or "",
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def extract_event_year(record: NormalizedRecord) -> int | None:
    for value in (record.event_date, record.period):
        if not value:
            continue
        match = YEAR_RE.search(str(value))
        if match:
            return int(match.group(0))
    return None


def record_to_row(record: NormalizedRecord) -> dict[str, Any]:
    metadata = asdict(record)
    content_text = record.embedding_text or record.description or record.title
    return {
        "content_id": stable_content_id(record),
        "source": record.source_name,
        "title": record.title[:500] if record.title else None,
        "content_text": content_text,
        "event_year": extract_event_year(record),
        "era": record.period[:50] if record.period else None,
        "category": record.category[:100] if record.category else None,
        "url": record.original_url,
        "metadata": json.dumps(metadata, ensure_ascii=False),
    }


def upsert_rows(connection: Any, table_name: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    columns = [
        "content_id",
        "source",
        "title",
        "content_text",
        "event_year",
        "era",
        "category",
        "url",
        "metadata",
    ]
    placeholders = ", ".join(["%s"] * len(columns))
    updates = ", ".join(f"{column}=VALUES({column})" for column in columns if column != "content_id")
    sql = (
        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {updates}"
    )
    values = [tuple(row[column] for column in columns) for row in rows]
    with connection.cursor() as cursor:
        cursor.executemany(sql, values)
    return len(rows)


def table_count(connection: Any, table_name: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return int(cursor.fetchone()[0])


def iter_normalized_records(input_path: Path, source: str, limit: int | None):
    source_config = build_source_config(input_path)
    for source_key in selected_sources(source):
        config = source_config[source_key]
        path = config["path"]
        if not path.exists():
            raise FileNotFoundError(f"Source file not found for {source_key}: {path}")
        seen: set[str] = set()
        for extracted_record in config["extractor"](path, limit=limit):
            normalized = normalize_record(extracted_record)
            if normalized is None:
                yield source_key, None, "missing title"
                continue
            if normalized.record_id in seen:
                yield source_key, None, f"duplicate record_id={normalized.record_id}"
                continue
            seen.add(normalized.record_id)
            yield source_key, normalized, None


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        print(f"Input path does not exist: {args.input}", file=sys.stderr)
        return 2

    try:
        table_name = validate_table_name(args.table)
        config = load_db_config(args.env_file)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    batch_size = args.batch_size or int(os.getenv("MYSQL_INGEST_BATCH_SIZE", "10"))
    if batch_size < 1:
        print("--batch-size must be greater than 0", file=sys.stderr)
        return 2

    extracted_count = 0
    success_count = 0
    skip_count = 0
    fail_count = 0
    pending: list[dict[str, Any]] = []

    try:
        connection = connect(config)
        ensure_table(connection, table_name)
        for source_key, record, skip_reason in iter_normalized_records(args.input, args.source, args.limit):
            extracted_count += 1
            if skip_reason:
                skip_count += 1
                print(f"skip source={source_key} reason={skip_reason}")
                continue
            try:
                assert record is not None
                pending.append(record_to_row(record))
                if len(pending) >= batch_size:
                    success_count += upsert_rows(connection, table_name, pending)
                    connection.commit()
                    pending = []
                    print(
                        "progress "
                        f"extracted_count={extracted_count} "
                        f"upserted_count={success_count} "
                        f"skip_count={skip_count} "
                        f"fail_count={fail_count}"
                    )
            except Exception as exc:
                fail_count += 1
                title = (record.title if record else "")[:120]
                record_id = record.record_id if record else ""
                print(
                    f"fail record_id={record_id} source={source_key} title={title} error={exc}",
                    file=sys.stderr,
                )

        if pending:
            success_count += upsert_rows(connection, table_name, pending)
            connection.commit()
        total_count = table_count(connection, table_name)
    except Exception as exc:
        if "connection" in locals():
            connection.rollback()
        print(f"MySQL ingest failed: {exc}", file=sys.stderr)
        return 2
    finally:
        if "connection" in locals():
            connection.close()

    print("MySQL ingest complete")
    print(f"table={table_name}")
    print(f"database={config['database']}")
    print(f"extracted_count={extracted_count}")
    print(f"upserted_count={success_count}")
    print(f"skip_count={skip_count}")
    print(f"fail_count={fail_count}")
    print(f"total_row_count={total_count}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
