"""
Script that tests LWA token retrieval and a static sandbox getOrders call.
Loads environment variables from a .env file and prints results or errors.
"""

import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _get_env(name: str) -> str:
    # 필요한 환경변수 값을 읽고, 비어 있으면 즉시 에러를 발생시킵니다.
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"환경변수가 필요합니다: {name}")
    return value


def _get_sandbox_endpoint() -> str:
    # Sandbox 엔드포인트는 리전마다 다를 수 있으므로 환경변수로 오버라이드 가능하게 처리합니다.
    # 값을 주지 않으면 NA(북미) 기본 엔드포인트를 사용합니다.
    return os.getenv(
        "SPAPI_SANDBOX_ENDPOINT",
        "https://sandbox.sellingpartnerapi-na.amazon.com",
    )


def get_lwa_access_token() -> str:
    # LWA 토큰 발급에 필요한 3가지 값을 환경변수에서 읽습니다.
    # refresh_token은 Seller 인증 후 발급받은 장기 토큰입니다.
    client_id = _get_env("SPAPI_CLIENT_ID")
    client_secret = _get_env("SPAPI_CLIENT_SECRET")
    refresh_token = _get_env("SPAPI_REFRESH_TOKEN")

    # Amazon LWA OAuth 토큰 엔드포인트
    url = "https://api.amazon.com/auth/o2/token"
    # OAuth2 refresh_token grant 규격에 맞는 폼 데이터
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    # Content-Type을 폼 형식으로 지정해 POST 요청 전송
    # timeout으로 네트워크 무한 대기 방지
    body = urlencode(data).encode("utf-8")
    request = Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            import json

            return json.loads(payload)["access_token"]
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LWA HTTP 오류: {exc.code} {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"LWA 네트워크 오류: {exc}") from exc


def call_get_orders_static_sandbox(access_token: str) -> dict:
    # Step 5 문서 예제와 동일한 static sandbox 파라미터를 사용합니다.
    # CreatedAfter=TEST_CASE_200 은 샌드박스 고정 테스트 케이스 트리거용 값입니다.
    url = (
        f"{_get_sandbox_endpoint()}/orders/v0/orders"
        "?MarketplaceIds=ATVPDKIKX0DER&CreatedAfter=TEST_CASE_200"
    )
    # x-amz-access-token: 방금 발급받은 LWA access token
    # User-Agent: SP-API 권장/예제에 맞춘 클라이언트 식별자
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json",
        "User-Agent": "My-Testing-App/1.0",
    }
    # getOrders 호출 (주의: 실서비스에서는 추가로 SigV4 서명이 필요할 수 있습니다)
    request = Request(url=url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            import json

            return json.loads(payload)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"getOrders HTTP 오류: {exc.code} {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"getOrders 네트워크 오류: {exc}") from exc


if __name__ == "__main__":
    # 실행 위치와 무관하게 스크립트와 같은 폴더의 .env를 로드
    _load_dotenv(str(Path(__file__).resolve().parent / ".env"))
    try:
        # 1) LWA access token 발급
        token = get_lwa_access_token()
        print("[OK] LWA access token 발급 성공")
        # 보안상 전체 토큰을 로그에 남기지 않기 위해 앞부분만 출력
        print("ACCESS_TOKEN:", token[:20] + "...")
        # 2) Step 5 static sandbox getOrders 호출
        data = call_get_orders_static_sandbox(token)
        print("[OK] getOrders(static sandbox) 호출 성공")
        print(data)
    except Exception as exc:  # noqa: BLE001
        # 어떤 단계에서든 실패하면 한 곳에서 공통 에러 메시지 출력
        print("[ERROR] LWA/getOrders 테스트 실패")
        print(f"[DETAIL] {exc}")
