from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    PINECONE_ENVIRONMENT: str

    # Job APIs
    ADZUNA_APP_ID: str
    ADZUNA_API_KEY: str
    REMOTEOK_API_URL: str

    # LLM
    LLM_ENDPOINT: str
    EMBEDDING_MODEL: str

    # Auth
    AUTH_STUB_USER_ID: str

    # Scheduler
    JOB_REFRESH_CRON: str

    # Storage
    STORAGE_BUCKET: str
    STORAGE_PROVIDER: str

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
