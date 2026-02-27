"""
Configuration settings for the application.
Reads environment variables and provides a Settings dataclass instance.
"""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Amazon Ops Dashboard")
    environment: str = os.getenv("ENVIRONMENT", "local")


settings = Settings()
