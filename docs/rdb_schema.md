# RDB Schema

MySQL 테이블 기본 이름은 `historical_records`이며 `MYSQL_TABLE_RECORDS`로 변경할 수 있다.

| 컬럼 | 설명 |
|---|---|
| id | 내부 auto increment key |
| record_id | RDB와 Qdrant를 연결하는 UNIQUE key |
| source_name | 원본 소스 이름 |
| source_file | 원본 파일 경로 |
| source_record_id | 원본 레코드 ID |
| title | 제목 |
| description | 설명 |
| period | 시대 표현 |
| event_date | 날짜 표현을 문자열로 보존 |
| location | 장소 |
| category | 분류 |
| keywords | JSON 문자열 |
| data_type | 자료 유형 |
| original_url | 원본 상세 URL |
| image_url | 이미지 URL |
| provider | 제공 기관 |
| license | 라이선스/저작권 |
| embedding_text | embedding에 사용한 텍스트 |
| raw_metadata | 원본 필드 전체 JSON |
| created_at, updated_at | 적재/수정 시각 |

RDB에는 정확한 조회, 필터링, 상세 정보 제공, 원본 필드 추적을 위해 정규화 필드와 `raw_metadata`를 함께 저장한다. `record_id`는 vector 검색 결과를 상세 데이터로 연결하는 안정적인 join key이므로 UNIQUE 인덱스를 둔다.
