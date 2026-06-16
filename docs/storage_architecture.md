# Storage Architecture

이번 파이프라인은 확보된 3개 로컬 원본만 읽는다. KMDB API는 신청/승인 이후 별도 extractor로 추가한다.

## Flow

```text
data/sources
  -> data-pipeline extractors
  -> NormalizedRecord transformer
  -> MySQL historical_records
  -> Qdrant memory_box_records
```

`data-pipeline`은 MySQL에 정규화된 상세 메타데이터와 `raw_metadata`를 저장한다. 백엔드 서버는 정확한 필터링, 상세 조회, 출처 확인이 필요할 때 MySQL을 조회한다.

`data-pipeline`은 Qdrant에 embedding vector와 검색 결과 표시 및 후속 조회에 필요한 최소 payload만 저장한다. 백엔드 서버는 Qdrant에서 의미 기반 후보를 찾고, 반환된 `record_id`로 MySQL 상세 정보를 조회한다.

`ai-serving-server`는 추후 실제 embedding model과 추론 endpoint를 제공하는 역할로 연결한다. 현재 기본 hash embedding은 적재 파이프라인 검증용이며 의미 검색 품질을 보장하지 않는다.
