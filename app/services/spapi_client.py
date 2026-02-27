"""
Stub client for interacting with the Amazon SP-API.
In real use this would handle authentication, signing, and HTTP requests.
"""

class SPAPIClient:
    def __init__(self) -> None:
        self.ready = True

    def ping(self) -> dict[str, bool]:
        return {"spapi_client_ready": self.ready}
