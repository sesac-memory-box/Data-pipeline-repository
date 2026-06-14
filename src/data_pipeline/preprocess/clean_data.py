import json
from typing import Any


def extract_records(raw_data: Any) -> list[dict]:
    """
    공공데이터 API 원본 응답에서 실제 item 목록을 추출한다.

    실제 API 응답 구조가 확정되면 이 함수를 해당 구조에 맞게 수정한다.
    """
    if not isinstance(raw_data, dict):
        return []

    if isinstance(raw_data.get("items"), list):
        return raw_data["items"]

    response = raw_data.get("response")
    if isinstance(response, dict):
        body = response.get("body")
        if isinstance(body, dict):
            items = body.get("items")
            if isinstance(items, dict) and isinstance(items.get("item"), list):
                return items["item"]
            if isinstance(items, list):
                return items

    return []


def clean_records(records: list[dict]) -> list[dict]:
    """
    원본 레코드를 서비스에 필요한 형태로 정제한다.

    기본 처리:
    - 문자열 앞뒤 공백 제거
    - 완전히 동일한 레코드 중복 제거
    """
    cleaned = []
    seen = set()

    for record in records:
        if not isinstance(record, dict):
            continue

        normalized = {}

        for key, value in record.items():
            if isinstance(value, str):
                normalized[key] = value.strip()
            else:
                normalized[key] = value

        record_key = json.dumps(normalized, ensure_ascii=False, sort_keys=True)

        if record_key in seen:
            continue

        seen.add(record_key)
        cleaned.append(normalized)

    return cleaned
