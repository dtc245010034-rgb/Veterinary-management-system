"""Test cho `run.py` — script chạy dự án bằng một lệnh.

`run.py` nằm ở gốc repo chứ không trong `app/`, nên luật "hàm public của services phải có test"
không bắt nó; nhưng nó là thứ đầu tiên người chấm gõ, và lỗi nặng nhất của nó là âm thầm làm
mất `.env` của người dùng. Vì vậy test tập trung vào các hàm thuần và vào cam kết
"không bao giờ ghi đè thứ người dùng đã đặt".

Không mock chính `run.py`. Ổ cắm mạng và hệ tập tin dùng thật (tmp_path).
"""

import socket
import time
from pathlib import Path

import pytest

import run

MAU = (
    "# Sao chép file này\r\n"
    "AI_PROVIDER=fake\r\n"
    "SECRET_KEY=doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that\r\n"
    "BCRYPT_ROUNDS=12\r\n"
)


@pytest.fixture
def thu_muc(tmp_path: Path):
    (tmp_path / ".env.example").write_bytes(MAU.encode("utf-8"))
    return tmp_path


def _doc_env(thu_muc: Path) -> dict:
    return run.parse_env((thu_muc / ".env").read_text(encoding="utf-8"))


# --- parse_env ------------------------------------------------------------------------


def test_parse_env_bo_comment_dong_trong_va_dau_nhay():
    text = '# ghi chu\n\nA=1\nB = "hai"\nC=\n  D=ba  \nkhong-co-dau-bang\n'

    assert run.parse_env(text) == {"A": "1", "B": "hai", "C": "", "D": "ba"}


def test_parse_env_giu_dau_bang_trong_gia_tri():
    # Chuỗi khóa/URL có thể chứa dấu "=": chỉ tách ở dấu bằng đầu tiên.
    assert run.parse_env("URL=sqlite:///a.db?x=1") == {"URL": "sqlite:///a.db?x=1"}


# --- ensure_env: cam kết quan trọng nhất ----------------------------------------------


def test_ensure_env_tao_env_moi_voi_khoa_ngau_nhien(thu_muc: Path):
    hanh_dong = run.ensure_env(thu_muc)

    env = _doc_env(thu_muc)
    assert hanh_dong == "tao"
    assert len(env["SECRET_KEY"]) >= 32
    assert env["SECRET_KEY"] != "doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that"
    # Các biến khác chép nguyên từ file mẫu.
    assert env["AI_PROVIDER"] == "fake"
    assert env["BCRYPT_ROUNDS"] == "12"


def test_ensure_env_khong_bao_gio_ghi_de_env_da_co_khoa_that(thu_muc: Path):
    goc = "AI_PROVIDER=gemini\nSECRET_KEY=khoa-that-cua-toi-rat-dai-va-bi-mat-123456\nGEMINI_API_KEY=abc\n"
    (thu_muc / ".env").write_bytes(goc.encode("utf-8"))

    hanh_dong = run.ensure_env(thu_muc)

    assert hanh_dong == "giu"
    # So từng byte: không đổi cả khoảng trắng hay kiểu xuống dòng.
    assert (thu_muc / ".env").read_bytes() == goc.encode("utf-8")


def test_ensure_env_chi_thay_dung_dong_khoa_khi_con_gia_tri_mac_dinh(thu_muc: Path):
    # Người dùng tự `copy .env.example .env` nhưng quên đổi khóa: app sẽ từ chối chạy.
    (thu_muc / ".env").write_bytes(
        b"AI_PROVIDER=gemini\nGEMINI_API_KEY=abc\nSECRET_KEY=doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that\n"
    )

    hanh_dong = run.ensure_env(thu_muc)

    env = _doc_env(thu_muc)
    assert hanh_dong == "dat_khoa"
    assert env["SECRET_KEY"] != "doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that"
    assert len(env["SECRET_KEY"]) >= 32
    # Những gì người dùng đã đặt phải còn nguyên.
    assert env["AI_PROVIDER"] == "gemini"
    assert env["GEMINI_API_KEY"] == "abc"


def test_ensure_env_bo_sung_khoa_khi_env_thieu_hang_secret_key(thu_muc: Path):
    (thu_muc / ".env").write_bytes(b"AI_PROVIDER=gemini\n")

    hanh_dong = run.ensure_env(thu_muc)

    env = _doc_env(thu_muc)
    assert hanh_dong == "dat_khoa"
    assert len(env["SECRET_KEY"]) >= 32
    assert env["AI_PROVIDER"] == "gemini"


def test_ensure_env_chay_hai_lan_khong_doi_khoa_lan_hai(thu_muc: Path):
    run.ensure_env(thu_muc)
    khoa = _doc_env(thu_muc)["SECRET_KEY"]

    hanh_dong = run.ensure_env(thu_muc)

    assert hanh_dong == "giu"
    assert _doc_env(thu_muc)["SECRET_KEY"] == khoa


def test_khoa_sinh_ra_khac_nhau_moi_lan():
    assert run.new_secret_key() != run.new_secret_key()
    assert len(run.new_secret_key()) >= 32


# --- cổng -----------------------------------------------------------------------------


def test_port_busy_nhan_ra_cong_dang_co_nguoi_nghe():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ben:
        ben.bind(("127.0.0.1", 0))
        ben.listen(1)
        cong = ben.getsockname()[1]

        assert run.port_busy(cong) is True


def test_pick_port_lay_cong_dau_tien_con_trong():
    assert run.pick_port(8000, is_busy=lambda p: p in (8000, 8001)) == 8002


def test_pick_port_bao_loi_ro_khi_het_cong():
    with pytest.raises(run.Fail, match="cổng trống"):
        run.pick_port(8000, limit=3, is_busy=lambda p: True)


# --- đường dẫn và CSDL ----------------------------------------------------------------


def test_venv_python_khac_nhau_giua_windows_va_linux(tmp_path: Path):
    assert run.venv_python(tmp_path, "nt") == tmp_path / ".venv" / "Scripts" / "python.exe"
    assert run.venv_python(tmp_path, "posix") == tmp_path / ".venv" / "bin" / "python"


def test_db_file_doc_duong_dan_sqlite_tuong_doi_va_tuyet_doi(tmp_path: Path):
    assert run.db_file("sqlite:///./petcare.db", tmp_path) == tmp_path / "petcare.db"
    assert run.db_file("sqlite:///" + str(tmp_path / "x.db"), tmp_path) == tmp_path / "x.db"


def test_db_file_tu_choi_csdl_khong_phai_sqlite(tmp_path: Path):
    # `reset` xóa file. Một URL Postgres không phải file để xóa — không được đoán mò.
    assert run.db_file("postgresql://u:p@host/db", tmp_path) is None


# --- dòng lệnh ------------------------------------------------------------------------


def test_khong_ghi_lenh_con_la_up():
    args = run.parse_args([])

    assert args.command == "up"
    assert args.port is None and args.no_open is False


def test_chi_ghi_co_thi_van_la_up():
    args = run.parse_args(["--port", "9000", "--no-open"])

    assert args.command == "up"
    assert args.port == 9000 and args.no_open is True


def test_lenh_test_chuyen_tiep_nguyen_tham_so_cho_pytest():
    args = run.parse_args(["test", "-k", "dang_nhap", "-x"])

    assert args.command == "test"
    assert args.pytest_args == ["-k", "dang_nhap", "-x"]


def test_lenh_la_bi_tu_choi():
    with pytest.raises(SystemExit):
        run.parse_args(["xoa-het"])


# --- đợi server -----------------------------------------------------------------------


def test_wait_healthy_tra_false_khi_khong_co_server():
    # Cổng vừa được hệ điều hành cấp rồi trả lại: gần như chắc chắn không ai nghe.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        cong = s.getsockname()[1]

    bat_dau = time.time()
    assert run.wait_healthy(cong, timeout=1, interval=0.2) is False
    assert time.time() - bat_dau < 5
