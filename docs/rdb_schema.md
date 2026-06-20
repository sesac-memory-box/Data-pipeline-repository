# RDB Schema

MySQL RDS MVP 적재 테이블 기본 이름은 `integrated_content`이다. `scripts/ingest_to_mysql.py --table`로 바꿀 수 있다.

```sql
CREATE TABLE IF NOT EXISTS integrated_content (
  content_id VARCHAR(64) PRIMARY KEY,
  source VARCHAR(100) NOT NULL,
  title VARCHAR(500),
  content_text MEDIUMTEXT,
  event_year INT NULL,
  era VARCHAR(50),
  category VARCHAR(100),
  url TEXT,
  metadata JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

| column | note |
|---|---|
| content_id | 중복 적재를 막는 deterministic primary key. 기본적으로 `NormalizedRecord.record_id`를 사용한다. |
| source | 원본 소스 |
| title | 제목 |
| content_text | 검색/표시/embedding에 사용 가능한 정제 본문 |
| event_year | 날짜/시대에서 추출한 연도 |
| era | 시대 또는 기간 |
| category | 분류 |
| url | 원본 URL |
| metadata | 정제 레코드 전체 JSON |
| created_at, updated_at | 생성/수정 시각 |

`content_id`는 Qdrant payload의 `record_id`/`document_id`와 연결할 수 있는 값이다.

## Legacy Loader

기존 `data_pipeline.ingest --load-mysql` 경로는 `historical_records` 테이블을 사용한다. `.env`의 `MYSQL_TABLE_RECORDS`로 바꿀 수 있다.

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
