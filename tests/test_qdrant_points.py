import unittest

from data_pipeline.loaders.qdrant_points import (
    build_chunk_payload,
    build_chunked_records,
    chunk_text,
    generate_point_id,
)
from data_pipeline.schemas.record import NormalizedRecord


class QdrantPointsTest(unittest.TestCase):
    def test_chunk_text_splits_with_overlap(self):
        text = "abcdefghijklmnopqrstuvwxyz"

        chunks = chunk_text(text, chunk_size=10, chunk_overlap=3)

        self.assertEqual(chunks[0], "abcdefghij")
        self.assertEqual(chunks[1], "hijklmnopq")
        self.assertGreater(len(chunks), 2)

    def test_chunk_text_skips_empty_text(self):
        self.assertEqual(chunk_text("   "), [])
        self.assertEqual(chunk_text(""), [])

    def test_payload_contains_required_fields(self):
        record = self._record()

        payload = build_chunk_payload(record, "본문 chunk", 0)

        for field in ("content", "source", "title", "chunk_index", "document_id", "metadata"):
            self.assertIn(field, payload)
        self.assertEqual(payload["content"], "본문 chunk")
        self.assertEqual(payload["document_id"], "record-1")
        self.assertEqual(payload["metadata"]["record_id"], "record-1")

    def test_point_id_is_deterministic(self):
        first = generate_point_id("document-1", 2, "same content")
        second = generate_point_id("document-1", 2, "same content")

        self.assertEqual(first, second)

    def test_build_chunked_records_uses_deterministic_ids(self):
        record = self._record(embedding_text="a" * 900)

        first = build_chunked_records([record], chunk_size=700, chunk_overlap=100)
        second = build_chunked_records([record], chunk_size=700, chunk_overlap=100)

        self.assertEqual(len(first), 2)
        self.assertEqual(first[0].point_id, second[0].point_id)
        self.assertEqual(first[0].payload["chunk_index"], 0)

    def _record(self, embedding_text: str = "검색에 사용할 본문") -> NormalizedRecord:
        return NormalizedRecord(
            record_id="record-1",
            source_name="source",
            source_file="source.csv",
            source_record_id="original-1",
            title="제목",
            description="설명",
            category="category",
            original_url="https://example.com",
            raw_metadata={"year": "1970"},
            embedding_text=embedding_text,
        )


if __name__ == "__main__":
    unittest.main()
