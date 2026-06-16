import re
from pathlib import Path
from typing import Iterator
from zipfile import ZipFile

from data_pipeline.schemas.record import NormalizedRecord, make_record_id


SOURCE_NAME = "korea_by_period"

PREDICATES = {
    "rdfs:label",
    "dcterms:title",
    "dcterms:description",
    "dcterms:issued",
    "nlon:keyword",
    "nlon:genre",
    "nlon:titleOfHostItem",
    "dc:publisher",
    "dc:format",
    "nlon:publicationPlace",
    "nlon:holdingInstitution",
}


def _iter_blocks(lines: Iterator[str]) -> Iterator[list[str]]:
    block: list[str] = []
    in_resource = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("@prefix"):
            continue

        if not line.startswith((" ", "\t")) and stripped.endswith(";"):
            in_resource = True
            block = [stripped]
            continue

        if in_resource:
            block.append(stripped)
            if stripped.endswith("."):
                yield block
                block = []
                in_resource = False


def _clean_value(value: str) -> str:
    value = value.rstrip(" ;.")
    value = re.sub(r"\^\^.+$", "", value).strip()
    if value.startswith('"') and '"' in value[1:]:
        return value[1 : value.rfind('"')]
    return value.strip("<>")


def _parse_values(value_text: str) -> list[str]:
    return [_clean_value(part.strip()) for part in re.split(r"\s+,\s+", value_text) if part.strip()]


def _parse_block(block: list[str]) -> tuple[str, dict[str, list[str]]] | None:
    first = block[0]
    subject = first.split(maxsplit=1)[0]
    metadata: dict[str, list[str]] = {}

    for line in block[1:]:
        if not line:
            continue
        match = re.match(r"(?P<predicate>[A-Za-z0-9_:-]+)\s+(?P<value>.+)$", line)
        if not match:
            continue
        predicate = match.group("predicate")
        if predicate not in PREDICATES:
            continue
        metadata.setdefault(predicate, []).extend(_parse_values(match.group("value")))

    if not metadata:
        return None
    return subject, metadata


def _first(metadata: dict[str, list[str]], *keys: str) -> str | None:
    for key in keys:
        values = metadata.get(key) or []
        for value in values:
            if value:
                return value
    return None


def extract_korea_by_period(path: Path, limit: int | None = None) -> Iterator[NormalizedRecord]:
    count = 0
    with ZipFile(path) as archive:
        ttl_names = [name for name in archive.namelist() if name.lower().endswith(".ttl")]
        for name in ttl_names:
            with archive.open(name) as raw_file:
                lines = (line.decode("utf-8", errors="replace") for line in raw_file)
                for block in _iter_blocks(lines):
                    parsed = _parse_block(block)
                    if parsed is None:
                        continue

                    subject, metadata = parsed
                    source_record_id = subject.split(":", 1)[-1]
                    title = _first(metadata, "dcterms:title", "rdfs:label") or ""
                    description = _first(metadata, "dcterms:description")
                    keywords = metadata.get("nlon:keyword", [])
                    category = _first(metadata, "nlon:genre", "dc:format")
                    provider = _first(metadata, "dc:publisher", "nlon:holdingInstitution")

                    yield NormalizedRecord(
                        record_id=make_record_id(SOURCE_NAME, source_record_id, title, None),
                        source_name=SOURCE_NAME,
                        source_file=f"{path}:{name}",
                        source_record_id=source_record_id,
                        title=title,
                        description=description,
                        event_date=_first(metadata, "dcterms:issued"),
                        location=_first(metadata, "nlon:publicationPlace"),
                        category=category,
                        keywords=keywords,
                        data_type=_first(metadata, "dc:format"),
                        provider=provider,
                        raw_metadata={key: values for key, values in metadata.items()},
                    )
                    count += 1
                    if limit is not None and count >= limit:
                        return
