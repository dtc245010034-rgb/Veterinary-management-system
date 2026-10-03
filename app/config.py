"""Cấu hình đọc từ biến môi trường hoặc file .env.

File .env không vào repo; .env.example là mẫu để sao chép.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

# Chuỗi này nằm công khai trong repo. app/main.py từ chối khởi động khi khóa còn là nó —
# ai đọc được mã nguồn cũng tự ký được cookie phiên của tài khoản quản lý.
SECRET_KEY_MAC_DINH = "doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that"

# Mật khẩu chung của tài khoản mẫu do `python -m app.seed` tạo. Ai đọc repo cũng biết chuỗi này,
# nên khi cổng công khai bật (SESSION_HTTPS_ONLY) app từ chối chạy nếu còn tài khoản dùng nó.
MAT_KHAU_MAC_DINH = "matkhau123"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./petcare.db"
    secret_key: str = SECRET_KEY_MAC_DINH

    # Cookie phiên chỉ được gửi qua HTTPS (cờ `Secure`). Bật khi công khai ra Internet qua tunnel
    # HTTPS; để tắt khi chạy http://127.0.0.1 vì trình duyệt sẽ không gửi lại cookie Secure qua HTTP.
    session_https_only: bool = False

    # Địa chỉ công khai của ứng dụng, ví dụ https://abc.ngrok.app. Tunnel/proxy có thể đổi `Host` nên
    # `Origin` của trình duyệt không còn khớp `Host` nhận được; địa chỉ này được tin thêm ở bước chặn
    # POST từ trang khác (app/security.py). Để trống khi chạy cục bộ.
    app_origin: str = ""

    # Mật khẩu seed đặt cho mọi tài khoản mẫu. Để trống thì dùng MAT_KHAU_MAC_DINH (chạy cục bộ).
    # `python run.py up --public-url ...` sinh chuỗi ngẫu nhiên và đưa vào đây.
    seed_mat_khau: str = ""

    # Số vòng băm bcrypt. 12 là mặc định của bcrypt và là giá trị dùng khi chạy thật.
    # Test hạ xuống 4 qua biến môi trường: bcrypt cố ý chậm (~1,5s mỗi lần băm), mà mỗi
    # test integration phải đăng nhập một lần. Đây là tham số cấu hình hợp lệ, không phải
    # làm yếu thuật toán — salt, cách băm và cách kiểm tra không đổi.
    bcrypt_rounds: int = 12

    # Gửi thư (xác minh email, đặt lại mật khẩu — P9). "console" in thư ra log, đủ cho máy phát triển
    # không có SMTP; "smtp" gửi thật qua máy chủ bên dưới. KHÔNG dùng "console" cho bản công khai:
    # liên kết xác minh sẽ nằm trong log. Tên lạ bị từ chối chứ không rơi về "console" (app/mail/service.py).
    mail_provider: str = "console"
    mail_from: str = "Petcare <noreply@localhost>"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    # Bí mật: chỉ ở .env, không vào repo. Gmail cần "mật khẩu ứng dụng" (bật xác minh hai bước).
    smtp_password: str = ""
    smtp_starttls: bool = True
    mail_timeout_giay: float = 10

    # Số lượt hỏi đáp AI tối đa của MỘT tài khoản khách trong một ngày (P9 chặng 7). Gói Gemini miễn phí chỉ có vài chục
    # lượt mỗi model mỗi ngày; không chặn theo tài khoản thì một khách đốt hết phần của cả cửa hàng. Câu bị guardrail
    # chặn (xin thuốc) cũng tính, câu gặp lỗi AI thì không. Nhân viên không bị giới hạn này.
    ai_khach_toi_da_moi_ngay: int = 10

    # Nhà cung cấp AI: "gemini" gọi API thật, "fake" trả lời cố định (dùng từ P7)
    ai_provider: str = "fake"
    gemini_api_key: str = ""

    # DANH SÁCH model theo thứ tự ưu tiên, không phải một tên. Gói miễn phí giới hạn lượt
    # mỗi ngày cho từng model, nên hết lượt model đầu thì hệ thống xoay sang model kế
    # (app/ai/quota.py). Tên model chết là lỗi 404 lúc chạy thật chứ không phải lỗi code:
    # kiểm 17/09 bằng khóa thật, `gemini-2.0-flash` (P0) và `gemini-2.5-flash` (13/09) đều
    # đã đóng với người dùng mới; `gemini-3.6-flash` chạy được.
    gemini_models: str = "gemini-3.6-flash,gemini-3.5-flash,gemini-3-flash-preview,gemini-3.1-flash-lite"

    # Ước tính lượt/ngày và lượt/phút cho mỗi model. Chỉ là ước tính: con số thật chỉ biết
    # khi Google trả 429 kèm quotaValue, và lúc đó hệ thống ghi lại số thật.
    gemini_rpd_uoc_tinh: int = 20
    gemini_rpm_uoc_tinh: int = 5

    # Ngân sách thời gian cho MỘT lần người dùng bấm: tổng cả chuỗi model đã thử, và tối đa
    # cho từng lần thử. Không có tổng thì bốn model quá tải nối nhau treo trang vài phút.
    ai_tong_giay: float = 45
    ai_moi_lan_giay: float = 25

    # Model vừa quá tải (503) hoặc chạm giới hạn phút thì nghỉ bấy nhiêu giây rồi mới thử lại.
    ai_nghi_giay: int = 120

    # Số token "suy nghĩ" cho mỗi lời gọi. Đo bằng khóa thật ngày 18/09 trên gemini-3.6-flash,
    # cùng một câu hỏi: mặc định 5,9–10,2 giây (438–752 token suy nghĩ), đặt 0 còn 2,2–3,0
    # giây và câu trả lời ca G-04 vẫn đúng mực (không gọi tên bệnh, khuyên đi khám ngay).
    # Ba tính năng ở đây đều là việc viết lại dữ liệu có sẵn, không phải suy luận nhiều bước.
    # Đặt -1 để dùng mặc định của model.
    gemini_thinking_budget: int = 0

    @property
    def danh_sach_model(self) -> list[str]:
        return [m.strip() for m in self.gemini_models.split(",") if m.strip()]


settings = Settings()
