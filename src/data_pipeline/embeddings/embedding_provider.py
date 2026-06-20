import os
from typing import Protocol


DEFAULT_FASTEMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingProvider(Protocol):
    model_name: str
    dimension: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class FastEmbedProvider:
    def __init__(self, model_name: str | None = None) -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError(
                "fastembed is required for Qdrant ingestion. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from exc

        self.model_name = model_name or os.getenv("FASTEMBED_MODEL", DEFAULT_FASTEMBED_MODEL)
        self._model = TextEmbedding(model_name=self.model_name)
        self.dimension = self._detect_dimension()

    def _detect_dimension(self) -> int:
        embedding = next(iter(self._model.embed(["dimension probe"])))
        return len(embedding)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        clean_texts = [text for text in texts if text and text.strip()]
        if len(clean_texts) != len(texts):
            raise ValueError("FastEmbed received an empty text. Filter empty chunks before embedding.")
        return [embedding.tolist() for embedding in self._model.embed(clean_texts)]


def create_embedding_provider() -> EmbeddingProvider:
    return FastEmbedProvider()
