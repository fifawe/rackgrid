"""Structured application configuration, loaded from environment
variables / .env. Single source of truth for config across the app."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    # IANA timezone name (e.g. "Africa/Cairo", "Asia/Riyadh"). Containers
    # default to UTC unless this is set - it drives the scheduler's cron
    # interpretation (see scheduler_main.py) so "run at 2am" means 2am
    # here, not 2am UTC.
    tz: str = "UTC"

    db_host: str = "mariadb"
    db_port: int = 3306
    db_user: str = "asset_inventory"
    db_password: str = "change_me"
    db_name: str = "asset_inventory"

    secret_key: str = "change_me_to_a_long_random_string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Shared secret the Ansible collector presents on POST /api/v1/discovery
    # (machine-to-machine, not a user JWT).
    collector_api_key: str = "change_me_collector_api_key"

    cors_origins: str = "http://localhost:3000,http://localhost"

    scheduler_enabled: bool = True
    default_collector_cron: str = "0 2 * * *"

    active_threshold_days: int = 7
    offline_threshold_days: int = 30

    # Dashboard "support expiring soon" alert: an asset is flagged when its
    # HW or OS support expiry date is this many days away or sooner
    # (including already past-due, which is trivially "sooner").
    support_expiry_alert_days: int = 60

    # Where uploaded files (asset design-document attachments, the
    # platform logo) are written on local disk. Relative paths resolve
    # against the process's working directory (the backend container's
    # WORKDIR is /app); mount a volume here in docker-compose for the
    # uploads to survive a container recreate.
    upload_dir: str = "uploads"

    # Rejects an attachment upload above this size outright, before it's
    # ever written to disk.
    max_attachment_size_bytes: int = 25 * 1024 * 1024

    # Single source of truth for the version shown in the UI (Dashboard
    # footer, GET /api/v1/settings/public) - keep in lockstep with
    # main.py's FastAPI(version=...) and the repo's top-level VERSION
    # file on every release.
    app_version: str = "1.9.0"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
