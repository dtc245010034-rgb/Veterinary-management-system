"""`tools/tao_du_lieu_demo.py`: CSDL demo phải đủ ca để trình diễn trang tiêm phòng (đề bài 3.1.6).

Dữ liệu demo tính từ ngày chạy (`clock.now()`), nên "sắp đến hạn" không cố định được trong file — phải kiểm
bằng cách dựng một CSDL mới rồi hỏi chính `den_han()`, đúng thứ trang `/vaccinations` hiển thị. Chạy script thật
trong tiến trình con vì nó tự đặt `DATABASE_URL` trước khi nạp app (xem đầu file script).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]

DEM_LICH_TIEM = """
import json
from datetime import timedelta
from app.db import SessionLocal
from app.services import clock, vaccinations

hom_nay = clock.now().date()
with SessionLocal() as db:
    print(json.dumps([[(m.next_due_at - hom_nay).days, m.pet_id] for m in vaccinations.den_han(db)]))
"""


def _dung_demo_va_lay_lich_tiem(tmp_path):
    env = {**os.environ, "BCRYPT_ROUNDS": "4", "PYTHONIOENCODING": "utf-8"}
    dich = tmp_path / "demo.db"
    dung = subprocess.run(
        [sys.executable, str(GOC / "tools" / "tao_du_lieu_demo.py"), "--out", str(dich)],
        cwd=GOC, env=env, capture_output=True, timeout=180,
    )
    assert dung.returncode == 0, dung.stderr.decode("utf-8", "replace")

    env_doc = {**env, "DATABASE_URL": f"sqlite:///{dich.as_posix()}", "AI_PROVIDER": "fake"}
    doc = subprocess.run(
        [sys.executable, "-c", DEM_LICH_TIEM], cwd=GOC, env=env_doc, capture_output=True, timeout=120,
    )
    assert doc.returncode == 0, doc.stderr.decode("utf-8", "replace")
    return json.loads(doc.stdout.decode("utf-8"))


def test_demo_co_nhieu_ca_tiem_sap_den_han_tren_nhieu_thu_cung_khac_nhau(tmp_path):
    """Lỗi thật (28/10): `/vaccinations` của demo chỉ có 4 dòng, **không ca nào** trong 7 ngày tới — màn hình
    nhắc tiêm (đề bài 3.1.6) trình diễn ra gần như trống."""
    lich = _dung_demo_va_lay_lich_tiem(tmp_path)

    sap_den = [(so_ngay, thu_cung) for so_ngay, thu_cung in lich if 0 <= so_ngay <= 7]
    assert len(sap_den) >= 5, f"chỉ {len(sap_den)} ca đến hạn trong 7 ngày: {lich}"
    assert len({thu_cung for _, thu_cung in sap_den}) == len(sap_den), "mỗi ca nên là một thú cưng khác nhau"


def test_demo_van_con_ca_qua_han_de_trinh_dien_loi_nhac_gap(tmp_path):
    """Thêm ca sắp đến hạn không được làm mất các ca quá hạn sẵn có — đó là nhóm cần gọi nhắc nhất."""
    lich = _dung_demo_va_lay_lich_tiem(tmp_path)

    assert any(so_ngay < 0 for so_ngay, _ in lich), f"không còn ca quá hạn nào: {lich}"


DUNG_VA_DEM_LICH_HOM_NAY = """
import contextlib, json, os, runpy, sys
from datetime import datetime
from app.services import clock

dich = sys.argv[1]
with clock.freeze(datetime(2026, 10, 31, 8, 0)):  # sáng thứ Bảy 31/10, đúng lúc người dùng sẽ dựng demo
    sys.argv = ["tao_du_lieu_demo.py", "--out", dich]
    with open(os.devnull, "w", encoding="utf-8") as bo_di, contextlib.redirect_stdout(bo_di):  # script gọi reconfigure()
        runpy.run_path("tools/tao_du_lieu_demo.py", run_name="__main__")
    from sqlalchemy import select
    from app.db import SessionLocal
    from app.models.appointment import Appointment
    with SessionLocal() as db:
        ds = db.scalars(select(Appointment).where(Appointment.status == "booked")).all()
        hom_nay = [[a.start_at.strftime("%H:%M"), a.staff_id] for a in ds if a.start_at.date() == clock.now().date()]
print(json.dumps(hom_nay))
"""


def test_demo_dung_sang_ngay_demo_co_lich_hom_nay_de_trang_lich_hen_khong_trong(tmp_path):
    """Lỗi thật (28/10): `/appointments` mở mặc định ở **hôm nay**, mà demo chỉ sinh lịch từ ngày mai — trang đầu
    tiên thầy cô thấy là "Chưa có lịch hẹn nào trong ngày này"."""
    dich = tmp_path / "demo.db"
    env = {**os.environ, "BCRYPT_ROUNDS": "4", "PYTHONIOENCODING": "utf-8",
           "DATABASE_URL": f"sqlite:///{dich.as_posix()}", "AI_PROVIDER": "fake"}

    kq = subprocess.run(
        [sys.executable, "-c", DUNG_VA_DEM_LICH_HOM_NAY, str(dich)],
        cwd=GOC, env=env, capture_output=True, timeout=240,
    )

    assert kq.returncode == 0, kq.stderr.decode("utf-8", "replace")
    lich = json.loads(kq.stdout.decode("utf-8").strip().splitlines()[-1])
    assert len(lich) >= 6, f"chỉ {len(lich)} lịch hôm nay: {lich}"
    assert len({nhan_vien for _, nhan_vien in lich}) >= 2, "lịch hôm nay chỉ của một nhân viên"
