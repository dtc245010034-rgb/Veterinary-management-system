"""Cấu hình đọc từ biến môi trường hoặc file .env.

File .env không vào repo; .env.example là mẫu để sao chép.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./petcare.db"
    secret_key: str = "doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that"

    # Số vòng băm bcrypt. 12 là mặc định của bcrypt và là giá trị dùng khi chạy thật.
    # Test hạ xuống 4 qua biến môi trường: bcrypt cố ý chậm (~1,5s mỗi lần băm), mà mỗi
    # test integration phải đăng nhập một lần. Đây là tham số cấu hình hợp lệ, không phải
    # làm yếu thuật toán — salt, cách băm và cách kiểm tra không đổi.
    bcrypt_rounds: int = 12

    # Nhà cung cấp AI: "gemini" gọi API thật, "fake" trả lời cố định (dùng từ P7)
    ai_provider: str = "fake"
    gemini_api_key: str = ""
    # Kiểm ngày 13/09 tại https://ai.google.dev/gemini-api/docs/models: `gemini-2.0-flash`
    # đặt từ P0 nay nằm trong mục "Previous models — Shut down". Tên model chết là lỗi 404
    # lúc chạy thật chứ không phải lỗi code, nên kiểm lại tên này trước khi viết gemini.py.
    gemini_model: str = "gemini-2.5-flash"


settings = Settings()
