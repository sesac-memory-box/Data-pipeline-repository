import unittest

from data_pipeline.verify_storage import (
    build_report,
    extract_record_id,
    find_missing_record_ids,
    format_source_counts,
)


class StorageVerificationTest(unittest.TestCase):
    def test_find_missing_record_ids_preserves_sample_order(self):
        missing = find_missing_record_ids(
            ["record-1", "record-2", "record-3"],
            {
                "record-1": {"record_id": "record-1"},
                "record-3": {"record_id": "record-3"},
            },
        )

        self.assertEqual(missing, ["record-2"])

    def test_format_source_counts_sorts_by_source_name(self):
        lines = format_source_counts(
            {
                "modern_history_archive": 2,
                "historical_photos": 3,
            }
        )

        self.assertEqual(
            lines,
            [
                "  - historical_photos: 3",
                "  - modern_history_archive: 2",
            ],
        )

    def test_build_report_contains_join_summary(self):
        report = build_report(
            mysql_total_count=2,
            mysql_source_counts={"historical_photos": 2},
            qdrant_collection_name="memory_box_records",
            qdrant_exists=True,
            qdrant_points_count=2,
            qdrant_vectors_count=None,
            sample_size=5,
            qdrant_record_ids=["record-1", "record-2"],
            matched_mysql_records={"record-1": {"record_id": "record-1"}},
            missing_record_ids=["record-2"],
        )

        self.assertEqual(report["mysql"]["total_count"], 2)
        self.assertEqual(report["qdrant"]["collection_name"], "memory_box_records")
        self.assertEqual(report["join_check"]["join_key"], "record_id")
        self.assertEqual(report["join_check"]["qdrant_sample_count"], 2)
        self.assertEqual(report["join_check"]["matched_mysql_count"], 1)
        self.assertEqual(report["join_check"]["missing_record_ids"], ["record-2"])

    def test_extract_record_id_returns_string_from_payload(self):
        self.assertEqual(extract_record_id({"record_id": 123}), "123")
        self.assertIsNone(extract_record_id({"title": "missing"}))


if __name__ == "__main__":
    unittest.main()
