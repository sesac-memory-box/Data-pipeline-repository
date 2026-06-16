# Data Schema

## NormalizedRecord

모든 원본 소스는 `src/data_pipeline/schemas/record.py`의 `NormalizedRecord`로 변환된다.

| 필드 | 타입 | 설명 |
|---|---|---|
| record_id | str | RDB와 Qdrant를 연결하는 sha256 기반 deterministic key |
| source_name | str | `korea_by_period`, `ehistory_historical_photos`, `modern_history_archive` |
| source_file | str | 읽은 원본 파일 경로 또는 zip 내부 파일 경로 |
| source_record_id | str \| None | 원본 데이터가 제공한 식별자 |
| title | str | 필수 제목, 없으면 invalid 처리 |
| description | str \| None | 설명 또는 대표 텍스트 |
| period | str \| None | 시대 표현, 예: `1980년대` |
| event_date | str \| None | 날짜 표현, 예: `1954-05-20`, `19491126` |
| location | str \| None | 장소 |
| category | str \| None | 분류 |
| keywords | list[str] | 중복 제거된 키워드 |
| data_type | str \| None | 자료 유형 |
| original_url | str \| None | 원본 상세 URL |
| image_url | str \| None | 이미지 URL |
| provider | str \| None | 제공 기관 |
| license | str \| None | 저작권 또는 라이선스 |
| raw_metadata | dict | 원본 필드 보존용 메타데이터 |
| embedding_text | str | vector embedding 입력 텍스트, RDB에도 저장 |

`record_id`는 `source_name + source_record_id`를 우선 사용하고, 원본 식별자가 없으면 `source_name + title + original_url` 조합으로 만든다. 같은 원본 레코드는 항상 같은 `record_id`가 나오며, RDB와 Qdrant payload 모두 동일한 값을 사용한다.

`embedding_text`는 `title`, `description`, `period`, `event_date`, `location`, `category`, `keywords`, `provider`를 조합한다. 의미 검색 후보를 만들기 위한 텍스트이며, 너무 긴 값은 기본 2000자로 제한한다.
