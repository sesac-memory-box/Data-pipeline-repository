import unittest

from data_pipeline.embeddings.embedding_provider import HashEmbeddingProvider


class HashEmbeddingProviderTest(unittest.TestCase):
    def test_hash_embedding_dimension_and_determinism(self):
        provider = HashEmbeddingProvider(dimension=384)

        first = provider.embed_texts(["대한민국 역사"])[0]
        second = provider.embed_texts(["대한민국 역사"])[0]

        self.assertEqual(len(first), 384)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
