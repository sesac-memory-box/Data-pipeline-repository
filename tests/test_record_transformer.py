import unittest

from data_pipeline.schemas.record import NormalizedRecord, make_record_id
from data_pipeline.transformers.record_transformer import normalize_records, split_keywords


class RecordTransformerTest(unittest.TestCase):
    def test_normalize_record_and_deduplicate_keywords(self):
        record = NormalizedRecord(
            record_id="",
            source_name=" test_source ",
            source_file=" source.csv ",
            source_record_id=" 1 ",
            title="  Test   Title ",
            keywords=[" 정책 ", "정책", " 사진 "],
        )

        result = normalize_records([record])

        self.assertEqual(result.invalid_count, 0)
        self.assertEqual(result.duplicate_count, 0)
        self.assertEqual(result.records[0].title, "Test Title")
        self.assertEqual(result.records[0].keywords, ["정책", "사진"])
        self.assertTrue(result.records[0].embedding_text.startswith("Test Title"))

    def test_missing_title_is_invalid(self):
        record = NormalizedRecord(
            record_id="",
            source_name="source",
            source_file="source.csv",
            title=" ",
        )

        result = normalize_records([record])

        self.assertEqual(result.records, [])
        self.assertEqual(result.invalid_count, 1)

    def test_record_id_is_deterministic(self):
        first = make_record_id("source", "abc", "Title", "https://example.com")
        second = make_record_id("source", "abc", "Other", "https://other.example.com")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_split_keywords(self):
        self.assertEqual(split_keywords("a, b; a|c"), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
