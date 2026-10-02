"""Khởi động ứng dụng: từ chối chạy với SECRET_KEY mặc định (lỗ hổng S1, kế hoạch P7 chặng 0).

Khóa ký cookie phiên nằm công khai trong `app/config.py`. Chạy với nó thì ai đọc được mã
nguồn cũng tự ký được cookie `user_id` của tài khoản quản lý.

Gọi thẳng `lifespan` thay vì `with TestClient(app)`: bộ test cố ý không chạy lifespan (xem
`conftest.client`). `engine` được thay bằng SQLite in-memory để ca khởi động thành công không
tạo file `petcare.db` trong thư mục dự án.
"""

import asyncio

import pytest
from sqlalchemy import create_engine


@pytest.fixture
def engine_tam(monkeypatch):
    """Engine in-memory thay cho engine thật, đóng lại sau test.

    Không dispose thì kết nối SQLite bị thu gom rác muộn, ném ResourceWarning — và
    `filterwarnings = error` biến nó thành lỗi ở một test khác chạy sau.
    """
    import app.main as main

    engine = create_engine("sqlite://")
    monkeypatch.setattr(main, "engine", engine)
    yield engine
    engine.dispose()


def _chay_lifespan():
    from app.main import app, lifespan

    async def _chay():
        async with lifespan(app):
            pass

    asyncio.run(_chay())


@pytest.mark.usefixtures("engine_tam")
def test_tu_choi_khoi_dong_khi_secret_key_con_la_chuoi_mac_dinh(monkeypatch):
    import app.main as main
    from app.config import SECRET_KEY_MAC_DINH

    monkeypatch.setattr(main.settings, "secret_key", SECRET_KEY_MAC_DINH)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _chay_lifespan()


@pytest.mark.usefixtures("engine_tam")
def test_khoi_dong_binh_thuong_khi_da_doi_secret_key(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main.settings, "secret_key", "mot-chuoi-rieng-cua-cua-hang")

    _chay_lifespan()


def test_khoi_dong_them_cot_con_thieu_vao_csdl_cu(engine_tam, monkeypatch):
    """Lỗi tái hiện: `petcare.db` dựng từ bản cũ thiếu cột mới thì chỉ `create_all` là không đủ."""
    import app.main as main
    from app.db import Base
    from sqlalchemy import inspect, text

    monkeypatch.setattr(main.settings, "secret_key", "mot-chuoi-rieng-cua-cua-hang")
    Base.metadata.create_all(engine_tam)
    with engine_tam.begin() as c:
        c.execute(text("ALTER TABLE owners DROP COLUMN email"))

    _chay_lifespan()

    assert "email" in {c["name"] for c in inspect(engine_tam).get_columns("owners")}


# --- Chế độ công khai từ chối mật khẩu mặc định (P9 chặng 2) -----------------------


def _them_tai_khoan_mat_khau_mac_dinh(engine):
    """Dựng bảng và một tài khoản dùng đúng mật khẩu mặc định của seed."""
    from sqlalchemy.orm import Session

    from app.config import MAT_KHAU_MAC_DINH
    from app.db import Base
    from app.models.user import User
    from app.security import hash_password

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(
            User(
                username="quanly",
                full_name="Quan Ly",
                role="manager",
                password_hash=hash_password(MAT_KHAU_MAC_DINH),
            )
        )
        db.commit()


def _cau_hinh_cong_khai_day_du(monkeypatch):
    """Chế độ công khai hợp lệ: cookie Secure, có địa chỉ công khai và bộ gửi thư thật."""
    import app.main as main

    monkeypatch.setattr(main.settings, "secret_key", "mot-chuoi-rieng-cua-cua-hang")
    monkeypatch.setattr(main.settings, "session_https_only", True)
    monkeypatch.setattr(main.settings, "app_origin", "https://shop.example.com")
    monkeypatch.setattr(main.settings, "mail_provider", "smtp")


def test_che_do_cong_khai_tu_choi_khoi_dong_khi_con_mat_khau_mac_dinh(engine_tam, monkeypatch):
    _cau_hinh_cong_khai_day_du(monkeypatch)
    _them_tai_khoan_mat_khau_mac_dinh(engine_tam)

    with pytest.raises(RuntimeError, match="quanly"):
        _chay_lifespan()


def test_che_do_thuong_khong_kiem_mat_khau_mac_dinh(engine_tam, monkeypatch):
    """Chạy cục bộ với dữ liệu demo `matkhau123` là việc bình thường, không được cản."""
    import app.main as main

    monkeypatch.setattr(main.settings, "secret_key", "mot-chuoi-rieng-cua-cua-hang")
    monkeypatch.setattr(main.settings, "session_https_only", False)
    _them_tai_khoan_mat_khau_mac_dinh(engine_tam)

    _chay_lifespan()


def test_che_do_cong_khai_khoi_dong_duoc_sau_khi_doi_mat_khau(engine_tam, monkeypatch):
    from sqlalchemy.orm import Session

    import app.main as main
    from app.models.user import User
    from app.security import hash_password

    monkeypatch.setattr(main.settings, "secret_key", "mot-chuoi-rieng-cua-cua-hang")
    _cau_hinh_cong_khai_day_du(monkeypatch)
    _them_tai_khoan_mat_khau_mac_dinh(engine_tam)
    with Session(engine_tam) as db:
        db.query(User).update({"password_hash": hash_password("mat-khau-rieng-cua-quan-ly")})
        db.commit()

    _chay_lifespan()


# --- Chế độ công khai cần thư thật và địa chỉ công khai (P9 chặng 4a) ---------------


def test_che_do_cong_khai_voi_mail_console_tu_choi_khoi_dong(engine_tam, monkeypatch):
    """`console` in thư ra log: liên kết xác minh nằm trong log máy chủ, khách không nhận được gì."""
    _cau_hinh_cong_khai_day_du(monkeypatch)
    monkeypatch.setattr("app.main.settings.mail_provider", "console")

    with pytest.raises(RuntimeError, match="MAIL_PROVIDER"):
        _chay_lifespan()


def test_che_do_cong_khai_thieu_app_origin_tu_choi_khoi_dong(engine_tam, monkeypatch):
    """Thiếu `APP_ORIGIN` thì liên kết trong thư dựng từ header `Host` — kẻ gửi `Host` giả chiếm được token."""
    _cau_hinh_cong_khai_day_du(monkeypatch)
    monkeypatch.setattr("app.main.settings.app_origin", "")

    with pytest.raises(RuntimeError, match="APP_ORIGIN"):
        _chay_lifespan()


def test_che_do_cong_khai_day_du_cau_hinh_thi_khoi_dong_duoc(engine_tam, monkeypatch):
    _cau_hinh_cong_khai_day_du(monkeypatch)

    _chay_lifespan()


def test_chay_cuc_bo_voi_mail_console_va_khong_app_origin_van_khoi_dong(engine_tam, monkeypatch):
    import app.main as main

    monkeypatch.setattr(main.settings, "secret_key", "mot-chuoi-rieng-cua-cua-hang")
    monkeypatch.setattr(main.settings, "session_https_only", False)
    monkeypatch.setattr(main.settings, "app_origin", "")
    monkeypatch.setattr(main.settings, "mail_provider", "console")

    _chay_lifespan()
