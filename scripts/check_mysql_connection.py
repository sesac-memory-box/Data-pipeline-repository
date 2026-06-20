#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENV_KEYS = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")


@dataclass(frozen=True)
class MySQLConnectionConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check MySQL RDS connectivity using DB_* values from .env."
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="Path to the dotenv file. Default: .env in the repository root.",
    )
    parser.add_argument(
        "--show-tables-limit",
        type=int,
        default=10,
        help="Maximum number of table names to print. Default: 10.",
    )
    return parser.parse_args()


def missing_required_env(env: dict[str, str | None]) -> list[str]:
    return [key for key in REQUIRED_ENV_KEYS if not (env.get(key) or "").strip()]


def load_config(env_file: Path) -> MySQLConnectionConfig:
    load_dotenv(env_file)
    env = {key: os.getenv(key) for key in REQUIRED_ENV_KEYS}
    missing = missing_required_env(env)
    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill DB_* values locally."
        )

    port_value = os.getenv("DB_PORT", "3306")
    try:
        port = int(port_value)
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer.") from exc

    return MySQLConnectionConfig(
        host=os.getenv("DB_HOST", "").strip(),
        port=port,
        database=os.getenv("DB_NAME", "").strip(),
        user=os.getenv("DB_USER", "").strip(),
        password=os.getenv("DB_PASSWORD", ""),
        charset=os.getenv("DB_CHARSET", "utf8mb4").strip() or "utf8mb4",
    )


def connect(config: MySQLConnectionConfig):
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError(
            "pymysql is required. Install dependencies with: python -m pip install -r requirements.txt"
        ) from exc

    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset=config.charset,
        connect_timeout=10,
        read_timeout=10,
        write_timeout=10,
        cursorclass=pymysql.cursors.Cursor,
    )


def explain_failure(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()
    if "access denied" in lowered:
        return "Access denied. Check DB_USER, DB_PASSWORD, and granted privileges."
    if "unknown database" in lowered:
        return "Unknown database. Check DB_NAME and confirm the schema exists."
    if isinstance(exc, TimeoutError) or isinstance(exc, socket.timeout) or "timed out" in lowered:
        return "Connection timed out. Check the RDS security group, public access, and network route."
    if "name or service not known" in lowered or "temporary failure in name resolution" in lowered:
        return "Host resolution failed. Check DB_HOST."
    if "connection refused" in lowered:
        return "Connection refused. Check DB_HOST, DB_PORT, and whether MySQL accepts remote connections."
    return "MySQL connection check failed. Review DB_* values and network access."


def fail(message: str, exit_code: int = 2) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(exit_code)


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.env_file)
    except ValueError as exc:
        fail(str(exc))

    try:
        connection = connect(config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            current_database = cursor.fetchone()[0]
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
    except Exception as exc:
        print(explain_failure(exc), file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return 2
    finally:
        if "connection" in locals():
            connection.close()

    limit = max(args.show_tables_limit, 0)
    preview = tables[:limit]
    print("MySQL connection OK")
    print(f"host={config.host}")
    print(f"port={config.port}")
    print(f"database={current_database}")
    print(f"user={config.user}")
    print(f"table_count={len(tables)}")
    print(f"tables={preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
