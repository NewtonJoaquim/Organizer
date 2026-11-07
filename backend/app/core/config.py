from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Organizer App API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    # Ingestão e Restrições de Arquivos (RF-01, RNF-01)
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    ALLOWED_EXTENSIONS: set[str] = {".xlsx", ".xls"}
    ALLOWED_MIME_TYPES: set[str] = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
        "application/x-excel",
        "application/excel",
    }

    # Armazenamento Temporário e TTL (RN-04, RNF-03)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    TEMP_STORAGE_DIR: Path = BASE_DIR / "storage" / "temp"
    TEMP_FILE_TTL_MINUTES: int = 15

    # Configuração do Orquestrador Semântico / LLM (RF-03, RF-04, RNF-04)
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "gemini"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str | None = None
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    MAX_TOKENS_PER_CALL: int = 800  # RNF-04: teto de tokens

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
