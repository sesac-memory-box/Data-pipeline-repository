from data_pipeline.clients.public_api_client import fetch_public_api_data
from data_pipeline.config import PROJECT_ROOT, load_settings
from data_pipeline.export.send_to_backend import send_to_backend
from data_pipeline.preprocess.clean_data import clean_records, extract_records
from data_pipeline.utils.file_io import save_json


def main() -> None:
    settings = load_settings()

    if not settings.public_api_base_url or not settings.public_api_service_key:
        print("PUBLIC_API_BASE_URL 또는 PUBLIC_API_SERVICE_KEY가 설정되지 않았습니다.")
        print(".env.example을 참고하여 로컬에 .env 파일을 생성하세요.")
        return

    # TODO: 실제 공공데이터 API 파라미터로 변경
    params = {
        "pageNo": 1,
        "numOfRows": 100,
        "type": "json",
    }

    raw_data = fetch_public_api_data(
        base_url=settings.public_api_base_url,
        service_key=settings.public_api_service_key,
        params=params,
        timeout=settings.request_timeout_seconds,
    )

    raw_output_path = PROJECT_ROOT / "data" / "raw" / "latest_raw_data.json"
    save_json(raw_output_path, raw_data)

    records = extract_records(raw_data)
    cleaned_records = clean_records(records)

    processed_output_path = PROJECT_ROOT / "data" / "processed" / "latest_processed_data.json"
    save_json(processed_output_path, cleaned_records)

    payload = {
        "source": "public-data-api",
        "count": len(cleaned_records),
        "items": cleaned_records,
    }

    if settings.backend_base_url:
        response = send_to_backend(
            base_url=settings.backend_base_url,
            endpoint=settings.backend_data_endpoint,
            payload=payload,
            timeout=settings.request_timeout_seconds,
        )
        print(response)
    else:
        print("BACKEND_BASE_URL이 설정되지 않아 백엔드 전송은 생략합니다.")
        print(f"processed count: {len(cleaned_records)}")


if __name__ == "__main__":
    main()
