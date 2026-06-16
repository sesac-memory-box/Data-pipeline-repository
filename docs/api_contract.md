# API Contract with Backend

현재 파이프라인은 백엔드로 데이터를 직접 POST하지 않는다. 데이터는 MySQL과 Qdrant에 적재하고, 백엔드는 두 저장소를 조회한다.

최신 흐름은 [storage_architecture.md](storage_architecture.md)를 기준으로 본다.

## Current Query Flow

```text
backend
  -> Qdrant semantic search
  -> record_id
  -> MySQL detail lookup
```

## Legacy Direct Send

초기 임시 구조에서는 아래처럼 백엔드 직접 전송을 가정했다. 지금은 참고용으로만 남긴다.

```http
POST /api/data
Content-Type: application/json
```

```json
{
  "source": "public-data-api",
  "count": 2,
  "items": [
    {
      "exampleField": "exampleValue"
    }
  ]
}
```

## Open Items

- 백엔드의 MySQL 상세 조회 API 확정
- 백엔드의 Qdrant 검색 API 확정
- 검색 결과 payload와 상세 응답 필드 맞추기
