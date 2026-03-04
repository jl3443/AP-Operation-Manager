"""Application configuration loaded from environment variables."""

from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings sourced from env / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://ap_user:ap_password_dev@localhost:5432/ap_operations"

    # ── Redis ───────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security / JWT ──────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── S3 / MinIO ──────────────────────────────────────────────────────
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_BUCKET: str = "ap-invoices"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"

    # ── LLM / AI ────────────────────────────────────────────────────────
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "claude-haiku-4-5-20251001"

    # ── OCR ──────────────────────────────────────────────────────────────
    OCR_ENDPOINT: str = "http://localhost:8080/ocr"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]

    # ── App metadata ─────────────────────────────────────────────────────
    APP_NAME: str = "AP Digital Ops Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False


settings = Settings()
