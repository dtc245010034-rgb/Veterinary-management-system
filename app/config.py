"""Cấu hình đọc từ biến môi trường hoặc file .env.

File .env không vào repo; .env.example là mẫu để sao chép.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./petcare.db"
    secret_key: str = "doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that"

    # Nhà cung cấp AI: "gemini" gọi API thật, "fake" trả lời cố định (dùng từ P7)
    ai_provider: str = "fake"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


settings = Settings()
