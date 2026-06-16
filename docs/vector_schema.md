# Vector Schema

Qdrant collection 기본 이름은 `memory_box_records`이다. vector size 기본값은 384이며 `QDRANT_VECTOR_SIZE`와 `EMBEDDING_DIM`을 같은 값으로 맞춘다.

## Payload

Qdrant payload에는 최소 조회 정보만 저장한다.

| 필드 | 설명 |
|---|---|
| record_id | RDB 상세 조회 key |
| source_name | 소스 필터 |
| source_file | 가벼운 lineage |
| title | 검색 결과 표시 |
| description_preview | 짧은 설명 |
| period | 필터/표시 |
| event_date | 필터/표시 |
| category | 필터 |
| keywords | 필터와 검색 힌트 |
| data_type | 자료 유형 필터 |
| original_url | 원본 링크 |
| image_url | 미리보기 |
| provider | 출처 표시 |

Vector DB에는 `raw_metadata` 전체를 넣지 않는다. 의미 검색과 후보 검색에 집중하고, 상세 조회와 원본 필드 추적은 `record_id`로 MySQL에서 수행하기 때문이다.

기본 embedding provider는 deterministic hash vector이다. 이 값은 Qdrant 적재, payload, join key를 검증하기 위한 임시 벡터이며 실제 의미 검색 품질에는 적합하지 않다. 운영 품질의 의미 검색에는 추후 `ai-serving-server` 또는 별도 embedding model을 `EMBEDDING_PROVIDER=http`로 연결해야 한다.
