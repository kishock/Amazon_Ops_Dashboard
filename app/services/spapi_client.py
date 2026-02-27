from urllib.parse import urlencode

import requests

from app.core.config import settings


class SPAPIClient:
    def __init__(self) -> None:
        self.client_id = settings.spapi_client_id
        self.client_secret = settings.spapi_client_secret
        self.refresh_token = settings.spapi_refresh_token
        self.sandbox_endpoint = settings.spapi_sandbox_endpoint.rstrip("/")
        self.marketplace_id = settings.spapi_marketplace_id

    def _validate_credentials(self) -> None:
        missing = []
        if not self.client_id:
            missing.append("SPAPI_CLIENT_ID")
        if not self.client_secret:
            missing.append("SPAPI_CLIENT_SECRET")
        if not self.refresh_token:
            missing.append("SPAPI_REFRESH_TOKEN")
        if missing:
            raise RuntimeError(f"Missing SP-API credentials: {', '.join(missing)}")

    def get_lwa_access_token(self) -> str:
        self._validate_credentials()
        response = requests.post(
            "https://api.amazon.com/auth/o2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get_sandbox_orders(self, created_after: str = "TEST_CASE_200") -> list[dict]:
        token = self.get_lwa_access_token()
        query = urlencode(
            {"MarketplaceIds": self.marketplace_id, "CreatedAfter": created_after},
            doseq=True,
        )
        url = f"{self.sandbox_endpoint}/orders/v0/orders?{query}"
        response = requests.get(
            url,
            headers={
                "x-amz-access-token": token,
                "Content-Type": "application/json",
                "User-Agent": "AmazonOpsDashboard/1.0",
            },
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        payload = body.get("payload", {})
        return payload.get("Orders", [])
