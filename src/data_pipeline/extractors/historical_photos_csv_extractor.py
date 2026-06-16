import csv
from pathlib import Path
from typing import Iterator

from data_pipeline.schemas.record import NormalizedRecord, make_record_id
from data_pipeline.transformers.record_transformer import split_keywords


SOURCE_NAME = "ehistory_historical_photos"


def _open_with_fallback(path: Path):
    try:
        handle = path.open("r", encoding="cp949", newline="")
        handle.read(1024)
        handle.seek(0)
        return handle
    except UnicodeDecodeError:
        handle.close()
        return path.open("r", encoding="utf-8-sig", newline="")


def extract_historical_photos(path: Path, limit: int | None = None) -> Iterator[NormalizedRecord]:
    with _open_with_fallback(path) as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader):
            if limit is not None and index >= limit:
                break

            source_record_id = row.get("고유키") or None
            title = row.get("제목") or ""
            category = " / ".join(
                item for item in [row.get("대분류"), row.get("중분류")] if item
            )

            yield NormalizedRecord(
                record_id=make_record_id(SOURCE_NAME, source_record_id, title, row.get("링크주소")),
                source_name=SOURCE_NAME,
                source_file=str(path),
                source_record_id=source_record_id,
                title=title,
                description=row.get("키워드") or None,
                event_date=row.get("제작일") or None,
                location=row.get("출처") or None,
                category=category or None,
                keywords=split_keywords(row.get("키워드")),
                data_type=row.get("메뉴코드") or None,
                original_url=row.get("링크주소") or None,
                image_url=row.get("이미지주소") or None,
                provider=row.get("출처") or "한국정책방송원",
                license=row.get("저작권") or None,
                raw_metadata=dict(row),
            )
