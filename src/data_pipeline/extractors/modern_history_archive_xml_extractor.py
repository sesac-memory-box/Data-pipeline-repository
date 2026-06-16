from pathlib import Path
from typing import Iterator
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from data_pipeline.schemas.record import NormalizedRecord, make_record_id
from data_pipeline.transformers.record_transformer import split_keywords


SOURCE_NAME = "modern_history_archive"


def _tag_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _record_to_dict(element: ET.Element) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for child in list(element):
        text = "".join(child.itertext()).strip()
        metadata[_tag_name(child.tag)] = text
    return metadata


def extract_modern_history_archive(path: Path, limit: int | None = None) -> Iterator[NormalizedRecord]:
    count = 0
    with ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".xml"):
                continue
            with archive.open(name) as xml_file:
                context = ET.iterparse(xml_file, events=("end",))
                for _, element in context:
                    if _tag_name(element.tag) != "DATA_RECORD":
                        continue

                    metadata = _record_to_dict(element)
                    source_record_id = metadata.get("FILE_NM") or metadata.get("IMG_URL")
                    title = metadata.get("NAME") or metadata.get("INFO_NAME") or ""
                    provider = metadata.get("PROD_ORG") or metadata.get("MNFCT")
                    period = metadata.get("AGE_INFO") or metadata.get("DATE_AGE")

                    yield NormalizedRecord(
                        record_id=make_record_id(
                            SOURCE_NAME,
                            source_record_id,
                            title,
                            metadata.get("IMG_URL"),
                        ),
                        source_name=SOURCE_NAME,
                        source_file=f"{path}:{name}",
                        source_record_id=source_record_id,
                        title=title,
                        description=metadata.get("LINE_DESC") or None,
                        period=period or None,
                        category=metadata.get("BIG_CLS") or None,
                        keywords=split_keywords(metadata.get("KEYWORD")),
                        data_type=metadata.get("DATA_TY_CD") or None,
                        original_url=metadata.get("IMG_URL") or None,
                        provider=provider or None,
                        license=metadata.get("KOGLCD") or None,
                        raw_metadata=metadata,
                    )
                    count += 1
                    element.clear()
                    if limit is not None and count >= limit:
                        return
