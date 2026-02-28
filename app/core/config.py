import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Amazon Ops Dashboard")
    environment: str = os.getenv("ENVIRONMENT", "local")
    cors_allowed_origins_env: str = os.getenv("CORS_ALLOWED_ORIGINS", "")
    database_url_env: str = os.getenv("DATABASE_URL", "")
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
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    demo_mode: bool = _as_bool(os.getenv("DEMO_MODE"), default=False)

    @property
    def database_url(self) -> str:
        if self.database_url_env:
            if self.database_url_env.startswith("postgresql://"):
                return self.database_url_env.replace(
                    "postgresql://", "postgresql+psycopg://", 1
                )
            return self.database_url_env
        return (
            "postgresql+psycopg://"
            f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_allowed_origins(self) -> list[str]:
        return _as_csv_list(self.cors_allowed_origins_env)


settings = Settings()
