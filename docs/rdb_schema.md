# RDB Schema

MySQL 테이블 기본 이름은 `historical_records`이다. `.env`의 `MYSQL_TABLE_RECORDS`로 바꿀 수 있다.

| column | note |
|---|---|
| id | 내부 auto increment key |
| record_id | Qdrant와 연결하는 UNIQUE key |
| source_name | 원본 소스 |
| source_file | 원본 파일 경로 |
| source_record_id | 원본 레코드 ID |
| title | 제목 |
| description | 설명 |
| period | 시대 |
| event_date | 원본 날짜 표현 |
| location | 장소 |
| category | 분류 |
| keywords | JSON |
| data_type | 자료 유형 |
| original_url | 원본 URL |
| image_url | 이미지 URL |
| provider | 제공 기관 |
| license | 저작권/라이선스 |
| embedding_text | embedding에 사용한 텍스트 |
| raw_metadata | 원본 필드 JSON |
| created_at, updated_at | 생성/수정 시각 |

MySQL에는 상세 조회와 필터링에 필요한 값을 저장한다. `raw_metadata`를 함께 두는 이유는 원본 필드 확인과 디버깅이 필요하기 때문이다.

`record_id`는 Qdrant 검색 결과를 MySQL 상세 레코드로 연결하는 값이라 UNIQUE로 둔다.
