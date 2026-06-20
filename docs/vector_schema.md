# Vector Schema

Qdrant collection 기본 이름은 `memory_box_contents`이다. vector size는 `FASTEMBED_MODEL`이 생성한 embedding dimension을 기준으로 자동 결정한다.

## Payload

| field | note |
|---|---|
| content | 검색/답변에 사용할 chunk 본문 |
| source | 데이터 출처 또는 파일명 |
| title | 검색 결과 표시 |
| chunk_index | 원문 내 chunk 순서 |
| document_id | 원문 문서 ID |
| metadata | 원문 record 기반 추가 메타데이터 |
| record_id | MySQL 상세 조회 key |
| source_name | 소스 필터 |
| source_file | 가벼운 출처 확인 |
| category | 필터 |
| url | 원본 링크 |
| original_id | 원본 ID |
| raw_source | 원천 이름 |
| file_path | 원천 파일 경로 |

기본 embedding provider는 `fastembed.TextEmbedding`이다. 기본 모델은 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`이며, 적재와 검색 테스트 스크립트가 같은 `FASTEMBED_MODEL` 환경변수를 사용한다.

point id는 `document_id + chunk_index + content 일부`로 만든 uuid5라서 같은 chunk를 다시 적재하면 같은 point를 갱신한다.
