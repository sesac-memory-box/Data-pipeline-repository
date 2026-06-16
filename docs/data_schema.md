# Data Schema

모든 원본은 `src/data_pipeline/schemas/record.py`의 `NormalizedRecord`로 변환한다.

| field | type | note |
|---|---|---|
| record_id | str | MySQL과 Qdrant join key |
| source_name | str | `korea_by_period`, `ehistory_historical_photos`, `modern_history_archive` |
| source_file | str | 원본 파일 또는 zip 내부 파일 |
| source_record_id | str \| None | 원본 식별자 |
| title | str | 필수. 없으면 invalid |
| description | str \| None | 설명 텍스트 |
| period | str \| None | 시대 표현 |
| event_date | str \| None | 원본 날짜 표현을 문자열로 보존 |
| location | str \| None | 장소 |
| category | str \| None | 분류 |
| keywords | list[str] | 중복 제거된 키워드 |
| data_type | str \| None | 자료 유형 |
| original_url | str \| None | 원본 URL |
| image_url | str \| None | 이미지 URL |
| provider | str \| None | 제공 기관 |
| license | str \| None | 저작권/라이선스 |
| raw_metadata | dict | 원본 필드 보존 |
| embedding_text | str | embedding 입력 텍스트 |

`record_id`는 `source_name + source_record_id`를 우선 사용한다. 원본 ID가 없으면 `source_name + title + original_url` 조합으로 만든다. 같은 원본은 같은 ID를 가져야 하므로 sha256으로 고정 생성한다.

`embedding_text`는 `title`, `description`, `period`, `event_date`, `location`, `category`, `keywords`, `provider`를 이어 만든다. Qdrant 벡터 생성에 쓰고, 어떤 텍스트를 embedding했는지 확인할 수 있게 MySQL에도 저장한다.
