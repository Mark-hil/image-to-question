from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    UPLOAD_DIR: str = "uploads"
    
    # External APIs and Tools
    GROQ_API_KEY: Optional[str] = None
    TESSERACT_CMD: Optional[str] = None
    
    # Paystack Billing Configuration
    PAYSTACK_SECRET_KEY: Optional[str] = None
    PAYSTACK_PUBLIC_KEY: Optional[str] = None
    
    # OCR settings (used in some legacy services)
    OCR_ENGINE: str = "paddle"
    PADDLE_USE_GPU: bool = False
    PADDLE_LANG: str = "en"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
