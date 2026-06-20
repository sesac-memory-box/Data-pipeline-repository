import os

from data_pipeline.loaders.qdrant_points import ChunkedRecord, build_chunked_records
from data_pipeline.schemas.record import NormalizedRecord


class QdrantLoader:
    def __init__(
        self,
        vector_size: int,
        collection_name: str | None = None,
        reset_collection: bool = False,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY") or None
        self.collection_name = (
            collection_name
            or os.getenv("QDRANT_COLLECTION")
            or os.getenv("QDRANT_COLLECTION_NAME")
            or "memory_box_contents"
        )
        self.vector_size = vector_size
        self.distance = os.getenv("QDRANT_DISTANCE", "Cosine")
        self.reset_collection = reset_collection or os.getenv("RESET_COLLECTION", "").lower() == "true"
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "700"))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "100"))
        self._collection_ready = False

    def _client(self):
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError(
                "qdrant-client is required for --load-qdrant. "
                "Dry-run does not require this package."
            ) from exc
        return QdrantClient(url=self.url, api_key=self.api_key)

    def ensure_collection(self, client) -> None:
        from qdrant_client.models import Distance, VectorParams

        if self._collection_ready:
            return
        try:
            collections = client.get_collections().collections
        except Exception as exc:
            raise RuntimeError(
                "Failed to connect to Qdrant "
                f"(url={self.url}, collection={self.collection_name}). "
                "Start local Qdrant with: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant"
            ) from exc

        exists = any(collection.name == self.collection_name for collection in collections)
        if exists and self.reset_collection:
            client.delete_collection(collection_name=self.collection_name)
            exists = False
        if not exists:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=self._distance(Distance)),
            )
        self._collection_ready = True

    def _distance(self, distance_enum):
        normalized = self.distance.strip().upper()
        if normalized == "COSINE":
            return distance_enum.COSINE
        if normalized == "DOT":
            return distance_enum.DOT
        if normalized == "EUCLID":
            return distance_enum.EUCLID
        raise ValueError(f"Unsupported QDRANT_DISTANCE: {self.distance}")

    def upsert_records(
        self,
        records: list[NormalizedRecord],
        vectors: list[list[float]],
    ) -> int:
        if not records:
            return 0
        chunked_records = build_chunked_records(records, self.chunk_size, self.chunk_overlap)
        return self.upsert_chunked_records(chunked_records, vectors)

    def upsert_chunked_records(
        self,
        chunked_records: list[ChunkedRecord],
        vectors: list[list[float]],
    ) -> int:
        if len(chunked_records) != len(vectors):
            raise ValueError("chunked records and vectors must have the same length")
        points = self.build_points(chunked_records, vectors)
        if not points:
            return 0

        client = self._client()
        self.ensure_collection(client)
        client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def build_points(self, chunked_records: list[ChunkedRecord], vectors: list[list[float]]):
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=chunked.point_id,
                vector=vector,
                payload=chunked.payload,
            )
            for chunked, vector in zip(chunked_records, vectors)
        ]
        return points
