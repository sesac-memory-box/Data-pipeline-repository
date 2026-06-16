# Ingestion Runbook

처음 실행할 때는 항상 제한 dry-run으로 확인한다.

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --limit 10 --dry-run
```

특정 소스만 확인할 수 있다.

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source historical_photos --limit 10 --dry-run
PYTHONPATH=src python3 -m data_pipeline.ingest --source modern_history_archive --limit 10 --dry-run
PYTHONPATH=src python3 -m data_pipeline.ingest --source korea_by_period --limit 10 --dry-run
```

MySQL 적재:

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --load-mysql
```

Qdrant 적재:

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --load-qdrant
```

MySQL과 Qdrant 동시 적재:

```bash
PYTHONPATH=src python3 -m data_pipeline.ingest --source all --load-mysql --load-qdrant
```

보고서는 기본적으로 `data/reports/latest_ingestion_report.json`에 생성된다. 실행 결과 파일은 커밋하지 않고, `data/reports/.gitkeep`만 커밋한다.

환경변수는 `.env.example`을 기준으로 설정한다. dry-run에서는 MySQL과 Qdrant 연결을 시도하지 않는다.
