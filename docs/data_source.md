# Data Sources

현재 파이프라인은 확보된 로컬 원본 3개만 처리한다. KMDB API는 신청/승인 이후 별도 작업으로 추가한다.

| source_name | file | format | use |
|---|---|---|---|
| `korea_by_period` | `data/sources/korea_by_period_04.zip` | TTL/RDF text | 시대별 대한민국 맥락 데이터 |
| `ehistory_historical_photos` | `data/sources/korea_policy_broadcasting_historical_photos_20251031.csv` | CSV, cp949 우선 | 국가기록사진 메타데이터 |
| `modern_history_archive` | `data/sources/modern_history_archive_list_20250902.zip` | XML files | 근현대사 아카이브 메타데이터 |

원본 파일은 `data/sources` 아래에서 읽기만 한다. 압축 파일은 `data/raw`나 `data/processed`에 풀지 않고 zip 내부에서 streaming 처리한다.
