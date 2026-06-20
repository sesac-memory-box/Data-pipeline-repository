# Data Pipeline

로컬 원본 데이터 3개를 읽어 공통 스키마로 정제하고, MySQL과 Qdrant에 적재하는 파이프라인이다. Qdrant에는 FastEmbed로 만든 실제 텍스트 embedding과 검색용 chunk payload를 저장한다.

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
  -> chunk text
  -> FastEmbed
  -> Qdrant memory_box_contents
  -> backend lookup
```

MySQL은 상세 조회, 필터링, 원본 필드 추적을 맡는다. Qdrant는 embedding vector와 `content` 본문을 포함한 chunk payload로 의미 검색 후보를 반환한다. 두 저장소는 같은 `record_id`/`document_id`로 연결한다.

## Local Storage

```bash
cp .env.example .env
docker compose up -d
```

Qdrant만 빠르게 띄울 수도 있다.

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

의존성 설치:

```bash
pip install -r requirements.txt
```

MVP에서 ai-serving-server와 반드시 맞춰야 하는 값:

```bash
QDRANT_COLLECTION=memory_box_contents
FASTEMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
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

스크립트 wrapper로도 실행할 수 있다.

```bash
python scripts/ingest_to_qdrant.py --input ./data --source all --collection memory_box_contents --load-qdrant
```

collection을 삭제 후 재생성하려면 reset 옵션을 명시한다.

```bash
python scripts/ingest_to_qdrant.py --input ./data --source all --collection memory_box_contents --load-qdrant --reset-collection
```

## Search

적재 후 같은 FastEmbed 모델로 query embedding을 만들고 Qdrant에서 top-k를 확인한다.

```bash
python scripts/search_qdrant.py --query "1970년대 서울역" --top-k 5
```

## Verify

MySQL과 Qdrant 적재 결과가 `record_id`로 연결되는지 읽기 전용으로 확인한다.

```bash
PYTHONPATH=src python3 -m data_pipeline.verify_storage --sample-size 5
PYTHONPATH=src python3 -m data_pipeline.verify_storage --sample-size 10 --report-path /tmp/memory-box-storage-verify-report.json
```

## MySQL RDS Check

RDS 접속 정보는 로컬 `.env`에만 입력한다.

```bash
cp .env.example .env
```

`.env`에서 아래 값을 실제 RDS 접속 정보로 채운다.

```bash
DB_HOST=
DB_PORT=3306
DB_NAME=memorybox
DB_USER=
DB_PASSWORD=
DB_CHARSET=utf8mb4
```

MySQL client로 먼저 3306 포트 접속을 확인할 수 있다.

```bash
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p
```

Python에서 같은 `.env` 값으로 database 선택과 `SHOW TABLES` 권한을 확인한다.

```bash
python scripts/check_mysql_connection.py
```

RDS MySQL 적재는 기존 ingest 명령의 `--load-mysql` 옵션을 사용한다.

```bash
python scripts/ingest_to_qdrant.py --input ./data --source all --limit 10 --load-mysql
```

주의:

- `.env`는 커밋하지 않는다.
- `DB_PASSWORD`를 README, PR, 채팅에 노출하지 않는다.
- RDS host는 브라우저가 아니라 MySQL client 또는 Python으로 3306 포트에 접속한다.

## Test

```bash
pip install -r requirements.txt
pip install -e .
pytest
```

## Notes

- main 브랜치에 직접 push하지 않는다.
- `.env`, `data/raw`, `data/processed`, `data/reports/*.json`, `logs`는 커밋하지 않는다.
- `data/sources` 원본 파일은 수정하지 않는다.
