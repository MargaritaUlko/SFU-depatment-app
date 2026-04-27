from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://dept_user:dept_pass@localhost:5432/department_db"
    SECRET_KEY: str = "change-me-to-a-64-character-random-string-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 20

    # Поля из .env
    POSTGRES_USER: str = "dept_user"
    POSTGRES_PASSWORD: str = "dept_pass"
    POSTGRES_DB: str = "department_db"
    MAX_BOT_TOKEN: str = ""
    MAX_BOT_API_URL: str = "https://api.max.ru/bot/v1"
    REDIS_URL: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()