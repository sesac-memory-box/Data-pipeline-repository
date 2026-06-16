import unittest

from data_pipeline.schemas.record import NormalizedRecord
from data_pipeline.transformers.embedding_text_builder import build_embedding_text


class EmbeddingTextBuilderTest(unittest.TestCase):
    def test_build_embedding_text_omits_none_values(self):
        record = NormalizedRecord(
            record_id="1",
            source_name="source",
            source_file="source.csv",
            title="Title",
            description=None,
            period="1980년대",
            keywords=["정책", "사진"],
            provider="Provider",
        )

        text = build_embedding_text(record)

        self.assertIn("Title", text)
        self.assertIn("1980년대", text)
        self.assertIn("정책, 사진", text)
        self.assertIn("Provider", text)

    def test_build_embedding_text_truncates(self):
        record = NormalizedRecord(
            record_id="1",
            source_name="source",
            source_file="source.csv",
            title="a" * 20,
        )

        self.assertEqual(len(build_embedding_text(record, max_length=5)), 5)


if __name__ == "__main__":
    unittest.main()
