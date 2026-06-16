# Ingestion Runbook

## 1. Start Local Storage

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

`docker compose down -v`는 MySQL/Qdrant named volume까지 삭제한다.

## 2. Dry Run

DB 연결 없이 추출, 정제, 보고서 생성을 확인한다.

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --dry-run
```

소스별 확인:

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source historical_photos --limit 10 --dry-run
PYTHONPATH=src python3 -m data_pipeline.ingest --source modern_history_archive --limit 10 --dry-run
PYTHONPATH=src python3 -m data_pipeline.ingest --source korea_by_period --limit 10 --dry-run
```

## 3. Load Data

처음에는 `--limit 10`으로 확인한다.

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --load-mysql
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --load-qdrant
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --load-mysql --load-qdrant
```

전체 적재는 limit 없이 실행한다.

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --load-mysql --load-qdrant
```

## 4. Report

기본 보고서 경로:

```text
data/reports/latest_ingestion_report.json
```

보고서 JSON은 실행 결과물이므로 커밋하지 않는다. 필요한 경우 `--report-path /tmp/report.json`처럼 레포 밖으로 지정한다.
