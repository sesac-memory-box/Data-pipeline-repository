import os
import uuid

from data_pipeline.schemas.record import NormalizedRecord


class QdrantLoader:
    def __init__(self, vector_size: int | None = None) -> None:
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY") or None
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "memory_box_records")
        self.vector_size = vector_size or int(os.getenv("QDRANT_VECTOR_SIZE", "384"))

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

        collections = client.get_collections().collections
        exists = any(collection.name == self.collection_name for collection in collections)
        if not exists:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def upsert_records(
        self,
        records: list[NormalizedRecord],
        vectors: list[list[float]],
    ) -> int:
        if not records:
            return 0
        if len(records) != len(vectors):
            raise ValueError("records and vectors must have the same length")

        from qdrant_client.models import PointStruct

        client = self._client()
        self.ensure_collection(client)
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, record.record_id)),
                vector=vector,
                payload=self._payload(record),
            )
            for record, vector in zip(records, vectors)
        ]
        client.upsert(collection_name=self.collection_name, points=points)
        return len(records)

    def _payload(self, record: NormalizedRecord) -> dict:
        description = record.description or ""
        return {
            "record_id": record.record_id,
            "source_name": record.source_name,
            "source_file": record.source_file,
            "title": record.title,
            "description_preview": description[:300],
            "period": record.period,
            "event_date": record.event_date,
            "category": record.category,
            "keywords": record.keywords,
            "data_type": record.data_type,
            "original_url": record.original_url,
            "image_url": record.image_url,
            "provider": record.provider,
        }
