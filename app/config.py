from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DataLens API"
    app_version: str = "0.2.0"
    environment: str = "development"
    max_upload_mb: int = 10
    database_url: str = "sqlite:///./datalens.db"
    upload_dir: str = "uploads"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
