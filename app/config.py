from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DataLens API"
    app_version: str = "1.0.0"
    environment: str = "development"
    max_upload_mb: int = 10
    database_url: str = "sqlite:///./datalens.db"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Los proveedores (Neon, Render...) entregan postgres:// o postgresql://;
        SQLAlchemy necesita indicar el driver (psycopg 3)."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value


settings = Settings()
