import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from data_pipeline.config import load_dotenv


DEFAULT_MYSQL_TABLE = "historical_records"
JOIN_KEY = "record_id"


@dataclass(frozen=True)
class StorageVerificationConfig:
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_table_records: str
    qdrant_url: str
    qdrant_api_key: str | None
    qdrant_collection_name: str


def load_config() -> StorageVerificationConfig:
    load_dotenv()
    return StorageVerificationConfig(
        mysql_host=os.getenv("MYSQL_HOST", "localhost"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", ""),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        mysql_database=os.getenv("MYSQL_DATABASE", "memory_box"),
        mysql_table_records=os.getenv("MYSQL_TABLE_RECORDS", DEFAULT_MYSQL_TABLE),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY") or None,
        qdrant_collection_name=(
            os.getenv("QDRANT_COLLECTION")
            or os.getenv("QDRANT_COLLECTION_NAME")
            or "memory_box_contents"
        ),
    )


def validate_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier


def format_source_counts(source_counts: dict[str, int]) -> list[str]:
    if not source_counts:
        return ["  - none: 0"]
    return [f"  - {source_name}: {count}" for source_name, count in sorted(source_counts.items())]


def find_missing_record_ids(
    qdrant_record_ids: list[str],
    mysql_records_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    mysql_record_ids = set(mysql_records_by_id)
    return [record_id for record_id in qdrant_record_ids if record_id not in mysql_record_ids]


def build_report(
    *,
    mysql_total_count: int,
    mysql_source_counts: dict[str, int],
    qdrant_collection_name: str,
    qdrant_exists: bool,
    qdrant_points_count: int | None,
    qdrant_vectors_count: int | None,
    sample_size: int,
    qdrant_record_ids: list[str],
    matched_mysql_records: dict[str, dict[str, Any]],
    missing_record_ids: list[str],
) -> dict[str, Any]:
    return {
        "mysql": {
            "total_count": mysql_total_count,
            "source_counts": mysql_source_counts,
        },
        "qdrant": {
            "collection_name": qdrant_collection_name,
            "exists": qdrant_exists,
            "points_count": qdrant_points_count,
            "vectors_count": qdrant_vectors_count,
        },
        "join_check": {
            "join_key": JOIN_KEY,
            "sample_size": sample_size,
            "qdrant_sample_count": len(qdrant_record_ids),
            "matched_mysql_count": len(matched_mysql_records),
            "missing_record_ids": missing_record_ids,
        },
    }


def extract_record_id(payload: Any) -> str | None:
    if not payload:
        return None
    if isinstance(payload, dict):
        value = payload.get(JOIN_KEY)
    else:
        value = getattr(payload, JOIN_KEY, None)
    if value is None:
        return None
    return str(value)


def get_collection_count(collection_info: Any, field_name: str) -> int | None:
    value = getattr(collection_info, field_name, None)
    if value is None and isinstance(collection_info, dict):
        value = collection_info.get(field_name)
    return int(value) if value is not None else None


def connect_mysql(config: StorageVerificationConfig):
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError("mysql-connector-python is required for storage verification.") from exc

    try:
        return mysql.connector.connect(
            host=config.mysql_host,
            port=config.mysql_port,
            user=config.mysql_user,
            password=config.mysql_password,
            database=config.mysql_database,
            charset="utf8mb4",
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to connect to MySQL "
            f"(host={config.mysql_host}, port={config.mysql_port}, database={config.mysql_database})."
        ) from exc


def query_mysql_counts(
    connection: Any,
    table_name: str,
    source_name: str | None,
) -> tuple[int, dict[str, int]]:
    table_name = validate_identifier(table_name)
    cursor = connection.cursor()
    try:
        if source_name:
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE source_name = %s",
                (source_name,),
            )
            total_count = int(cursor.fetchone()[0])
            cursor.execute(
                f"""
                SELECT source_name, COUNT(*) AS count
                FROM {table_name}
                WHERE source_name = %s
                GROUP BY source_name
                """,
                (source_name,),
            )
        else:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = int(cursor.fetchone()[0])
            cursor.execute(
                f"""
                SELECT source_name, COUNT(*) AS count
                FROM {table_name}
                GROUP BY source_name
                """
            )
        source_counts = {str(row[0]): int(row[1]) for row in cursor.fetchall()}
        return total_count, source_counts
    finally:
        cursor.close()


def fetch_mysql_records_by_ids(
    connection: Any,
    table_name: str,
    record_ids: list[str],
) -> dict[str, dict[str, Any]]:
    if not record_ids:
        return {}

    table_name = validate_identifier(table_name)
    placeholders = ", ".join(["%s"] * len(record_ids))
    sql = (
        f"SELECT record_id, source_name, title "
        f"FROM {table_name} "
        f"WHERE record_id IN ({placeholders})"
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(record_ids))
        rows = cursor.fetchall()
        return {
            str(record_id): {
                "record_id": str(record_id),
                "source_name": source_name,
                "title": title,
            }
            for record_id, source_name, title in rows
        }
    finally:
        cursor.close()


def create_qdrant_client(config: StorageVerificationConfig):
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise RuntimeError("qdrant-client is required for storage verification.") from exc

    return QdrantClient(url=config.qdrant_url, api_key=config.qdrant_api_key)


def get_qdrant_collection_summary(client: Any, config: StorageVerificationConfig) -> dict[str, Any]:
    try:
        collections = client.get_collections().collections
        exists = any(
            collection.name == config.qdrant_collection_name for collection in collections
        )
        if not exists:
            return {
                "collection_name": config.qdrant_collection_name,
                "exists": False,
                "points_count": None,
                "vectors_count": None,
            }
        collection_info = client.get_collection(collection_name=config.qdrant_collection_name)
    except Exception as exc:
        raise RuntimeError(
            "Failed to read Qdrant collection "
            f"(url={config.qdrant_url}, collection={config.qdrant_collection_name})."
        ) from exc

    return {
        "collection_name": config.qdrant_collection_name,
        "exists": True,
        "points_count": get_collection_count(collection_info, "points_count"),
        "vectors_count": get_collection_count(collection_info, "vectors_count"),
    }


def build_qdrant_filter(source_name: str | None):
    if not source_name:
        return None

    from qdrant_client.models import FieldCondition, Filter, MatchValue

    return Filter(
        must=[
            FieldCondition(
                key="source_name",
                match=MatchValue(value=source_name),
            )
        ]
    )


def sample_qdrant_record_ids(
    client: Any,
    config: StorageVerificationConfig,
    sample_size: int,
    source_name: str | None,
) -> list[str]:
    try:
        scroll_result = client.scroll(
            collection_name=config.qdrant_collection_name,
            limit=sample_size,
            with_payload=True,
            with_vectors=False,
            scroll_filter=build_qdrant_filter(source_name),
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to sample Qdrant points "
            f"(url={config.qdrant_url}, collection={config.qdrant_collection_name})."
        ) from exc

    points = scroll_result[0] if isinstance(scroll_result, tuple) else scroll_result
    record_ids: list[str] = []
    for point in points:
        record_id = extract_record_id(getattr(point, "payload", None))
        if record_id:
            record_ids.append(record_id)
    return record_ids


def print_summary(report: dict[str, Any]) -> None:
    print(f"MySQL total records: {report['mysql']['total_count']}")
    print("MySQL source counts:")
    for line in format_source_counts(report["mysql"]["source_counts"]):
        print(line)
    print(f"Qdrant collection: {report['qdrant']['collection_name']}")
    print(f"Qdrant points count: {report['qdrant']['points_count']}")
    print(f"Sample checked: {report['join_check']['qdrant_sample_count']}")
    print(f"Matched in MySQL: {report['join_check']['matched_mysql_count']}")
    print(f"Missing record_ids: {len(report['join_check']['missing_record_ids'])}")
    print(f"Join key: {report['join_check']['join_key']}")


def write_report(report: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def verify_storage(
    config: StorageVerificationConfig,
    sample_size: int,
    source_name: str | None,
) -> dict[str, Any]:
    mysql_connection = connect_mysql(config)
    try:
        mysql_total_count, mysql_source_counts = query_mysql_counts(
            mysql_connection,
            config.mysql_table_records,
            source_name,
        )

        qdrant_client = create_qdrant_client(config)
        qdrant_summary = get_qdrant_collection_summary(qdrant_client, config)
        if qdrant_summary["exists"]:
            qdrant_record_ids = sample_qdrant_record_ids(
                qdrant_client,
                config,
                sample_size,
                source_name,
            )
        else:
            qdrant_record_ids = []
        matched_mysql_records = fetch_mysql_records_by_ids(
            mysql_connection,
            config.mysql_table_records,
            qdrant_record_ids,
        )
        missing_record_ids = find_missing_record_ids(qdrant_record_ids, matched_mysql_records)

        return build_report(
            mysql_total_count=mysql_total_count,
            mysql_source_counts=mysql_source_counts,
            qdrant_collection_name=qdrant_summary["collection_name"],
            qdrant_exists=qdrant_summary["exists"],
            qdrant_points_count=qdrant_summary["points_count"],
            qdrant_vectors_count=qdrant_summary["vectors_count"],
            sample_size=sample_size,
            qdrant_record_ids=qdrant_record_ids,
            matched_mysql_records=matched_mysql_records,
            missing_record_ids=missing_record_ids,
        )
    finally:
        mysql_connection.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify read-only MySQL and Qdrant storage linkage by record_id."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of Qdrant sample points to check. Default: 5.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Optional JSON report path. No report file is written when omitted.",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with code 1 when sampled Qdrant record_ids are missing in MySQL.",
    )
    parser.add_argument(
        "--source",
        default="all",
        help="Specific source_name to verify. Default: all.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.sample_size < 1:
        print("--sample-size must be greater than 0", file=sys.stderr)
        return 2

    source_name = None if args.source == "all" else args.source
    config = load_config()
    try:
        report = verify_storage(config, args.sample_size, source_name)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print_summary(report)
    if args.report_path:
        write_report(report, args.report_path)
        print(f"JSON report written: {args.report_path}")

    if args.fail_on_missing and report["join_check"]["missing_record_ids"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
