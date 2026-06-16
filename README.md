# Data Pipeline

로컬 원본 데이터 3개를 읽어 공통 스키마로 정제하고, MySQL과 Qdrant에 적재하는 파이프라인이다. 백엔드는 Qdrant에서 의미 검색 후보를 찾고, `record_id`로 MySQL 상세 데이터를 조회한다.

KMDB API는 아직 신청/승인 전이라 현재 범위에서는 제외한다.

## Data Sources

| source | file | use |
|---|---|---|
| `korea_by_period` | `data/sources/korea_by_period_04.zip` | 시대별 대한민국 맥락 데이터 |
| `ehistory_historical_photos` | `data/sources/korea_policy_broadcasting_historical_photos_20251031.csv` | 국가기록사진 메타데이터 |
| `modern_history_archive` | `data/sources/modern_history_archive_list_20250902.zip` | 근현대사 아카이브 메타데이터 |

## Flow

```text
data/sources
  -> extract / transform
  -> MySQL historical_records
  -> Qdrant memory_box_records
  -> backend lookup
```

MySQL은 상세 조회, 필터링, 원본 필드 추적을 맡는다. Qdrant는 embedding vector와 최소 payload로 의미 검색 후보를 반환한다. 두 저장소는 같은 `record_id`로 연결한다.

## Local Storage

```bash
cp .env.example .env
docker compose up -d
```

상태 확인:

```bash
./scripts/check_local_storage.sh
```

중지:

```bash
docker compose down
```

볼륨까지 지우려면 `docker compose down -v`를 사용한다. 이 명령은 MySQL/Qdrant 로컬 데이터를 삭제한다.

## Dry Run

DB 연결 없이 파싱, 정제, 보고서 생성을 확인한다.

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 3 --dry-run
```

## Ingest

처음에는 작은 limit으로 확인한다.

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --load-mysql --load-qdrant
```

MySQL만 적재:

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --load-mysql
```

Qdrant만 적재:

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --load-qdrant
```

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Notes

- main 브랜치에 직접 push하지 않는다.
- `.env`, `data/raw`, `data/processed`, `data/reports/*.json`, `logs`는 커밋하지 않는다.
- `data/sources` 원본 파일은 수정하지 않는다.
