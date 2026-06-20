import json
import os
from dataclasses import asdict

from data_pipeline.schemas.record import NormalizedRecord


RDB_FIELDS = [
    "record_id",
    "source_name",
    "source_file",
    "source_record_id",
    "title",
    "description",
    "period",
    "event_date",
    "location",
    "category",
    "keywords",
    "data_type",
    "original_url",
    "image_url",
    "provider",
    "license",
    "embedding_text",
    "raw_metadata",
]


class MySQLLoader:
    def __init__(self) -> None:
        self.host = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT") or os.getenv("MYSQL_PORT", "3306"))
        self.user = os.getenv("DB_USER") or os.getenv("MYSQL_USER", "")
        self.password = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD", "")
        self.database = os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE", "memorybox")
        self.charset = os.getenv("DB_CHARSET", "utf8mb4")
        self.table = os.getenv("MYSQL_TABLE_RECORDS", "historical_records")

    def _connect(self):
        try:
            import mysql.connector
        except ImportError as exc:
            raise RuntimeError(
                "mysql-connector-python is required for --load-mysql. "
                "Dry-run does not require this package."
            ) from exc

        return mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset,
        )

    def ensure_table(self, connection) -> None:
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {self.table} (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            record_id VARCHAR(64) NOT NULL UNIQUE,
            source_name VARCHAR(100) NOT NULL,
            source_file VARCHAR(255) NOT NULL,
            source_record_id VARCHAR(255),
            title TEXT NOT NULL,
            description MEDIUMTEXT,
            period VARCHAR(100),
            event_date VARCHAR(100),
            location VARCHAR(255),
            category VARCHAR(255),
            keywords JSON,
            data_type VARCHAR(100),
            original_url TEXT,
            image_url TEXT,
            provider VARCHAR(255),
            license VARCHAR(255),
            embedding_text MEDIUMTEXT,
            raw_metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_source_name (source_name),
            INDEX idx_event_date (event_date),
            INDEX idx_category (category)
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
        cursor = connection.cursor()
        cursor.execute(ddl)
        cursor.close()

    def upsert_records(self, records: list[NormalizedRecord]) -> int:
        if not records:
            return 0

        connection = self._connect()
        try:
            self.ensure_table(connection)
            columns = ", ".join(RDB_FIELDS)
            placeholders = ", ".join(["%s"] * len(RDB_FIELDS))
            updates = ", ".join(
                f"{field}=VALUES({field})" for field in RDB_FIELDS if field != "record_id"
            )
            sql = (
                f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {updates}"
            )
            values = [self._record_values(record) for record in records]
            cursor = connection.cursor()
            cursor.executemany(sql, values)
            connection.commit()
            cursor.close()
            return len(records)
        finally:
            connection.close()

    def _record_values(self, record: NormalizedRecord) -> tuple:
        data = asdict(record)
        data["keywords"] = json.dumps(data["keywords"], ensure_ascii=False)
        data["raw_metadata"] = json.dumps(data["raw_metadata"], ensure_ascii=False)
        return tuple(data[field] for field in RDB_FIELDS)
