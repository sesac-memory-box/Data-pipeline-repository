import importlib.util
from pathlib import Path
import sys
import unittest

from data_pipeline.schemas.record import NormalizedRecord


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ingest_to_mysql.py"
SPEC = importlib.util.spec_from_file_location("ingest_to_mysql", SCRIPT_PATH)
ingest_to_mysql = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = ingest_to_mysql
SPEC.loader.exec_module(ingest_to_mysql)


class IngestToMySQLTest(unittest.TestCase):
    def test_stable_content_id_uses_record_id(self):
        record = NormalizedRecord(
            record_id="record-1",
            source_name="source",
            source_file="source.csv",
            title="Title",
        )

        self.assertEqual(ingest_to_mysql.stable_content_id(record), "record-1")

    def test_stable_content_id_is_deterministic_without_record_id(self):
        record = NormalizedRecord(
            record_id="",
            source_name="source",
            source_file="source.csv",
            title="Title",
            embedding_text="Body",
        )

        first = ingest_to_mysql.stable_content_id(record)
        second = ingest_to_mysql.stable_content_id(record)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_record_to_row_maps_integrated_content_fields(self):
        record = NormalizedRecord(
            record_id="record-1",
            source_name="source",
            source_file="source.csv",
            title="Title",
            description="Description",
            period="1980년대",
            event_date="1980-04-17",
            category="photo",
            original_url="https://example.com",
            embedding_text="Title Description",
        )

        row = ingest_to_mysql.record_to_row(record)

        self.assertEqual(row["content_id"], "record-1")
        self.assertEqual(row["source"], "source")
        self.assertEqual(row["content_text"], "Title Description")
        self.assertEqual(row["event_year"], 1980)
        self.assertEqual(row["era"], "1980년대")
        self.assertEqual(row["category"], "photo")
        self.assertIn('"record_id": "record-1"', row["metadata"])

    def test_validate_table_name_rejects_unsafe_name(self):
        with self.assertRaises(ValueError):
            ingest_to_mysql.validate_table_name("bad;DROP")

    def test_missing_required_env_reports_key_names(self):
        missing = ingest_to_mysql.missing_required_env(
            {
                "DB_HOST": "",
                "DB_NAME": "memorybox",
                "DB_USER": "user",
                "DB_PASSWORD": None,
            }
        )

        self.assertEqual(missing, ["DB_HOST", "DB_PASSWORD"])


if __name__ == "__main__":
    unittest.main()
