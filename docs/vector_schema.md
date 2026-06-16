# Vector Schema

Qdrant collection 기본 이름은 `memory_box_records`이다. 기본 vector size는 384이고, `QDRANT_VECTOR_SIZE`와 `EMBEDDING_DIM`을 같은 값으로 맞춘다.

## Payload

| field | note |
|---|---|
| record_id | MySQL 상세 조회 key |
| source_name | 소스 필터 |
| source_file | 가벼운 출처 확인 |
| title | 검색 결과 표시 |
| description_preview | 짧은 설명 |
| period | 필터/표시 |
| event_date | 필터/표시 |
| category | 필터 |
| keywords | 필터와 검색 힌트 |
| data_type | 자료 유형 |
| original_url | 원본 링크 |
| image_url | 미리보기 |
| provider | 출처 표시 |

Qdrant에는 `raw_metadata` 전체를 넣지 않는다. Vector DB는 의미 검색 후보를 빠르게 찾는 역할이고, 상세 정보와 원본 필드 추적은 MySQL이 맡는다.

기본 embedding provider는 deterministic hash vector이다. 로컬 적재와 join key 검증용이며 실제 의미 검색 품질용은 아니다. 실제 검색 품질은 추후 `ai-serving-server` 또는 별도 embedding model을 `EMBEDDING_PROVIDER=http`로 연결해 확인한다.
