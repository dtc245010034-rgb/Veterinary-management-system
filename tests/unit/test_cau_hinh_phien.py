"""Cấu hình cookie phiên đọc từ môi trường: `SESSION_HTTPS_ONLY` bật cờ `Secure` cho cookie.

Middleware được dựng lúc import `app.main`, nên mỗi giá trị phải thử trong một tiến trình riêng.
Test kiểm cấu hình đã đi tới `SessionMiddleware` chứ không chỉ tới `Settings`.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]

MA = (
    "import json\n"
    "from starlette.middleware.sessions import SessionMiddleware\n"
    "from app.main import app\n"
    "print(json.dumps([m.kwargs.get('https_only') for m in app.user_middleware if m.cls is SessionMiddleware]))\n"
)


def _https_only(gia_tri_moi_truong: str):
    moi_truong = {**os.environ, "SECRET_KEY": "khoa-test-" + "x" * 40, "DATABASE_URL": "sqlite://"}
    moi_truong.pop("SESSION_HTTPS_ONLY", None)
    if gia_tri_moi_truong is not None:
        moi_truong["SESSION_HTTPS_ONLY"] = gia_tri_moi_truong
    ra = subprocess.run(
        [sys.executable, "-c", MA], cwd=GOC, env=moi_truong, check=True, capture_output=True, text=True, timeout=60
    )
    return json.loads(ra.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("gia_tri, mong_doi", [("false", False), ("true", True)])
def test_session_https_only_di_tu_bien_moi_truong_toi_session_middleware(gia_tri, mong_doi):
    assert _https_only(gia_tri) == [mong_doi]


def test_mac_dinh_la_tat_vi_http_cuc_bo_khong_gui_lai_cookie_secure():
    from app.config import Settings

    assert Settings(_env_file=None).session_https_only is False
    assert Settings(_env_file=None).app_origin == ""
