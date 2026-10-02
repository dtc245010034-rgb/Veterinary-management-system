"""Test dữ liệu mẫu `app/seed.py` — thứ mọi đợt smoke test bấm tay đều dựa vào.

Chạy đúng lệnh người dùng chạy (`python -m app.seed`) trong một tiến trình riêng, trỏ vào
CSDL tạm qua biến môi trường `DATABASE_URL`, nên không đụng `petcare.db` thật. Không gọi
thẳng `seed.main()` vì nó tự mở `SessionLocal` của CSDL thật.
"""

from datetime import datetime
import os
import sqlite3
from contextlib import closing
import subprocess
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]


def _chay_seed(tmp_path: Path) -> Path:
    return _chay_seed_lay_dau_ra(tmp_path)[0]


def _chay_seed_lay_dau_ra(tmp_path: Path, them: dict | None = None) -> tuple[Path, str]:
    csdl = tmp_path / "seed.db"
    moi_truong = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{csdl.as_posix()}",
        "BCRYPT_ROUNDS": "4",
        **(them or {}),
    }
    ket_qua = subprocess.run(
        [sys.executable, "-m", "app.seed"],
        cwd=GOC,
        env=moi_truong,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    return csdl, ket_qua.stdout


def test_hoa_don_va_thanh_toan_mau_mang_ngay_cua_buoi_cham_soc(tmp_path):
    """Lỗi thật, tìm ra khi rà 11/09: mọi hóa đơn và lần trả mẫu mang ngày chạy seed.

    Kể cả hóa đơn của buổi chăm sóc cách đây 28 ngày. Hậu quả rơi vào P6: mọi đồng
    tiền mẫu nằm chung một ngày, nên "doanh thu theo khoảng thời gian" không kiểm tay
    được — chọn kỳ nào có hôm nay cũng ra đủ, kỳ nào không có thì ra 0.
    """
    csdl = _chay_seed(tmp_path)

    # closing() chứ không phải `with sqlite3.connect(...)`: context manager của sqlite3
    # chỉ commit, KHÔNG đóng kết nối. Kết nối rò rỉ bị GC dọn giữa một test khác, và
    # filterwarnings = error biến ResourceWarning đó thành lỗi ở test chẳng liên quan —
    # đã xảy ra thật, đỏ ở test_services.py.
    with closing(sqlite3.connect(csdl)) as c:
        hoa_don = c.execute(
            "SELECT i.id, date(i.issued_at), date(a.end_at) "
            "FROM invoices i JOIN appointments a ON a.id = i.appointment_id"
        ).fetchall()
        thanh_toan = c.execute(
            "SELECT p.invoice_id, date(p.paid_at), date(i.issued_at) "
            "FROM payments p JOIN invoices i ON i.id = p.invoice_id"
        ).fetchall()

    # Không có dòng nào thì mọi phép so bên dưới đều xanh mà không chứng minh gì.
    assert hoa_don and thanh_toan

    assert all(ngay_lap == ngay_buoi for _, ngay_lap, ngay_buoi in hoa_don), hoa_don
    assert all(ngay_thu == ngay_lap for _, ngay_thu, ngay_lap in thanh_toan), thanh_toan

    # Dữ liệu mẫu cố ý có buổi hôm qua và buổi 28 ngày trước — hai ngày lập khác nhau
    # là điều kiện để smoke test chọn kỳ mà thấy doanh thu thay đổi.
    assert len({ngay_lap for _, ngay_lap, _ in hoa_don}) >= 2


def test_moi_lich_mau_deu_nam_trong_gio_mo_cua(tmp_path):
    """M-06, bài học 4: `seed.py` ghi thẳng `Appointment`, không đi qua `dat_lich`.

    Nó buộc phải làm vậy — dữ liệu mẫu có cả buổi đã qua, mà `dat_lich` từ chối mọi mốc
    trong quá khứ. Hệ quả là luật giờ mở cửa **không** che được đường này. Hiện seed sinh
    09:00 → 12:45 nên hợp lệ, nhưng không có gì giữ cho nó hợp lệ: chỉ cần ai đó nới vòng
    lặp thêm vài giờ là dữ liệu mẫu lại chứa đúng thứ mà bản vá vừa cấm, và mọi đợt smoke
    bấm tay sẽ dựa trên dữ liệu vi phạm chính luật của hệ thống.
    """
    from app.services.scheduling import GIO_DONG_CUA, GIO_MO_CUA

    csdl = _chay_seed(tmp_path)

    with closing(sqlite3.connect(csdl)) as c:
        lich = c.execute("SELECT id, start_at, end_at FROM appointments").fetchall()

    assert lich, "Không có lịch mẫu nào — phép canh sẽ xanh mà không chứng minh gì"

    vi_pham = []
    for ma, bat_dau, ket_thuc in lich:
        b = datetime.fromisoformat(bat_dau)
        k = datetime.fromisoformat(ket_thuc)
        if b.date() != k.date() or b.hour < GIO_MO_CUA:
            vi_pham.append((ma, bat_dau, ket_thuc))
        elif (k.hour, k.minute) > (GIO_DONG_CUA, 0):
            vi_pham.append((ma, bat_dau, ket_thuc))

    assert not vi_pham, f"Lịch mẫu nằm ngoài giờ {GIO_MO_CUA}h–{GIO_DONG_CUA}h: {vi_pham}"


def test_dong_tong_ket_cua_seed_dem_dung_so_lich_hen_thuc_te(tmp_path):
    """R-5 (rà soát 02/10): dòng in báo "5 lịch hẹn" trong khi CSDL có 8 — ba buổi đã xong kèm hồ sơ
    được thêm vào bảng nhưng không được đếm. Người đọc dòng này để biết seed có chạy đúng không."""
    import re

    csdl, dau_ra = _chay_seed_lay_dau_ra(tmp_path)

    with closing(sqlite3.connect(csdl)) as c:
        thuc_te = c.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    khop = re.search(r"(\d+) lịch hẹn", dau_ra)
    assert khop, f"không thấy mục đếm lịch hẹn trong: {dau_ra!r}"
    assert thuc_te > 0
    assert int(khop.group(1)) == thuc_te


def _mat_khau_dang_dung(csdl: Path, username: str, thu: str) -> bool:
    from app.security import verify_password

    with closing(sqlite3.connect(csdl)) as c:
        (bam,) = c.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
    return verify_password(thu, bam)


def test_seed_dung_mat_khau_tu_seed_mat_khau_khi_duoc_dat(tmp_path):
    """Chế độ công khai (P9 chặng 2): run.py sinh mật khẩu ngẫu nhiên và đưa qua biến môi trường."""
    csdl, dau_ra = _chay_seed_lay_dau_ra(tmp_path, {"SEED_MAT_KHAU": "mat-khau-ngau-nhien-12345"})

    assert _mat_khau_dang_dung(csdl, "quanly", "mat-khau-ngau-nhien-12345")
    assert not _mat_khau_dang_dung(csdl, "quanly", "matkhau123")
    # Người vận hành chỉ thấy mật khẩu qua dòng in của seed, nên dòng đó phải in mật khẩu thật.
    assert "mat-khau-ngau-nhien-12345" in dau_ra


def test_seed_giu_matkhau123_khi_khong_dat_seed_mat_khau(tmp_path):
    csdl, _ = _chay_seed_lay_dau_ra(tmp_path, {"SEED_MAT_KHAU": ""})

    assert _mat_khau_dang_dung(csdl, "quanly", "matkhau123")
