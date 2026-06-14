import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    public_api_base_url: str
    public_api_service_key: str
    backend_base_url: str
    backend_data_endpoint: str
    request_timeout_seconds: int


def load_dotenv(dotenv_path: Path = PROJECT_ROOT / ".env") -> None:
    """
    python-dotenv 없이 간단한 .env 파일을 읽는다.
    이미 환경변수에 값이 있으면 덮어쓰지 않는다.
    """
    if not dotenv_path.exists():
        return

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        os.environ.setdefault(key, value)


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        public_api_base_url=os.getenv("PUBLIC_API_BASE_URL", ""),
        public_api_service_key=os.getenv("PUBLIC_API_SERVICE_KEY", ""),
        backend_base_url=os.getenv("BACKEND_BASE_URL", ""),
        backend_data_endpoint=os.getenv("BACKEND_DATA_ENDPOINT", "/api/data"),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
    )
