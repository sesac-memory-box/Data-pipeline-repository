import json
from urllib.parse import urlencode
from urllib.request import urlopen


def fetch_public_api_data(
    base_url: str,
    service_key: str,
    params: dict,
    timeout: int = 10,
) -> dict:
    """
    공공데이터 API에서 데이터를 가져온다.

    현재는 Python standard library만 사용한다.
    실제 API 응답 형식이 XML이면 추후 XML 파싱 로직으로 변경한다.
    """
    query_params = {
        **params,
        "serviceKey": service_key,
    }

    url = f"{base_url}?{urlencode(query_params)}"

    with urlopen(url, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")

    return json.loads(response_body)
