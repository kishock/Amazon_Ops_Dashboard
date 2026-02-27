import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Amazon Ops Dashboard")
    environment: str = os.getenv("ENVIRONMENT", "local")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")
    db_name: str = os.getenv("DB_NAME", "amazon_ops")
    spapi_client_id: str = os.getenv("SPAPI_CLIENT_ID", "")
    spapi_client_secret: str = os.getenv("SPAPI_CLIENT_SECRET", "")
    spapi_refresh_token: str = os.getenv("SPAPI_REFRESH_TOKEN", "")
    spapi_sandbox_endpoint: str = os.getenv(
        "SPAPI_SANDBOX_ENDPOINT",
        "https://sandbox.sellingpartnerapi-na.amazon.com",
    )
    spapi_marketplace_id: str = os.getenv("SPAPI_MARKETPLACE_ID", "ATVPDKIKX0DER")

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
