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
