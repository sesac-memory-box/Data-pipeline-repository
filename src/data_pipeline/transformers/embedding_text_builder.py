from data_pipeline.schemas.record import NormalizedRecord


def build_embedding_text(record: NormalizedRecord, max_length: int = 2000) -> str:
    parts: list[str] = []

    for value in (
        record.title,
        record.description,
        record.period,
        record.event_date,
        record.location,
        record.category,
        ", ".join(record.keywords) if record.keywords else None,
        record.provider,
    ):
        if value:
            parts.append(value)

    return " ".join(parts)[:max_length]
