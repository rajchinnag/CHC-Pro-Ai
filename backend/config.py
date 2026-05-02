"""
CHC Pro AI — Application Configuration
Validates all environment variables at startup.
Any missing required variable raises a clear error immediately,
not a cryptic AttributeError three layers deep at runtime.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # AWS Core
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    # Cognito
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    COGNITO_CLIENT_SECRET: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # NPPES / OIG / PECOS
    NPPES_API_BASE: str = "https://npiregistry.cms.hhs.gov/api"
    NPPES_API_VERSION: str = "2.1"
    OIG_LEIE_API_BASE: str = "https://oig.hhs.gov/exclusions/api/1.0/get-full-record"
    PECOS_API_BASE: str = "https://data.cms.gov/provider-data/api/1/datastore/query/4j6d-yzce/0"

    # SES / OTP
    SES_FROM_EMAIL: str = "noreply@carolincodepro.ai"
    SES_CONFIGURATION_SET: str = "chc-transactional"
    OTP_EXPIRE_SECONDS: int = 300
    OTP_LENGTH: int = 6
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RATE_WINDOW_SECONDS: int = 600

    # TOTP
    TOTP_ISSUER: str = "CarolinCodeProAI"
    TOTP_INTERVAL: int = 30

    # S3
    S3_BUCKET_RAW: str = "chc-raw-uploads"
    S3_BUCKET_DEIDENTIFIED: str = "chc-deidentified"

    # Rate limits (slowapi format)
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_OTP: str = "3/minute"
    RATE_LIMIT_REGISTER: str = "10/minute"

    # Sentry
    SENTRY_DSN: str = ""

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
