# API Contract with Backend

> 현재 구조는 백엔드 직접 전송이 아니라 MySQL/Qdrant 저장소 적재 방식으로 변경되었다. 최신 구조는 `docs/storage_architecture.md`를 기준으로 확인한다.

데이터 파이프라인에서 백엔드 서버로 데이터를 전달하기 위한 임시 API 계약입니다.

## Endpoint

POST /api/data

Content-Type: application/json

## Request Body

예시:

    {
      "source": "public-data-api",
      "count": 2,
      "items": [
        {
          "exampleField": "exampleValue"
        }
      ]
    }

## Response Body

예시:

    {
      "status": "success",
      "savedCount": 2
    }

## TODO

- 백엔드 실제 endpoint 확정
- items 내부 필드 확정
- 실패 응답 형식 확정
- 한 번에 전송할 데이터 개수 확정
