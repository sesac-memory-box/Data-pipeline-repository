# Storage Architecture

현재 범위는 로컬 원본 3개를 MySQL과 Qdrant에 적재하는 것이다. KMDB API는 추후 추가한다.

## Flow

```text
data/sources
  -> extractor
  -> NormalizedRecord
  -> MySQL historical_records
  -> Qdrant memory_box_records
  -> backend 조회
```

MySQL은 정규화된 상세 메타데이터와 `raw_metadata`를 저장한다. 백엔드는 정확한 필터링, 상세 화면, 출처 확인이 필요할 때 MySQL을 조회한다.

Qdrant는 embedding vector와 최소 payload만 저장한다. 백엔드는 Qdrant에서 의미 검색 후보를 받고, `record_id`로 MySQL 상세 데이터를 가져온다.

`ai-serving-server`는 추후 embedding API나 추론 API를 제공하는 쪽으로 연결한다. 현재 hash embedding은 파이프라인 검증용이라 의미 검색 품질을 기대하지 않는다.

## Local Services

```bash
cp .env.example .env
docker compose up -d
```

서비스:

| service | default port | volume |
|---|---:|---|
| MySQL | 3306 | `mysql_data` |
| Qdrant HTTP | 6333 | `qdrant_data` |
| Qdrant gRPC | 6334 | `qdrant_data` |

중지는 `docker compose down`을 사용한다. `docker compose down -v`는 named volume까지 삭제하므로 로컬 적재 데이터가 사라진다.
