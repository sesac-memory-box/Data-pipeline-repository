import json
from urllib.request import Request, urlopen


def send_to_backend(
    base_url: str,
    endpoint: str,
    payload: dict,
    timeout: int = 10,
) -> dict:
    """
    전처리된 데이터를 백엔드 서버로 전송한다.

    백엔드 API 명세가 확정되면 endpoint, method, payload schema를 맞춘다.
    """
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    request = Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")

    if not response_body:
        return {"status": "success"}

    return json.loads(response_body)
