"""Canh các file Docker: lỗi ở đây không làm test nào đỏ nhưng làm lộ bí mật hoặc mất dữ liệu.

Không chạy Docker thật (máy chấm có thể không có); việc dựng image và gọi `/login` do job `docker`
trong CI và `python run.py docker up --check` làm. Test ở đây chỉ khóa những dòng mà đổi nhầm thì
hậu quả không hiện ra ngay: bí mật bị nướng vào image, chạy bằng root, cổng mở ra cả mạng LAN,
CSDL nằm trong lớp image (mất khi dựng lại).
"""

import re
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]


def _doc(ten: str) -> str:
    return (GOC / ten).read_text(encoding="utf-8")


def _dong_lenh(noi_dung: str) -> list[str]:
    """Các dòng không phải chú thích và không trống."""
    return [d.strip() for d in noi_dung.splitlines() if d.strip() and not d.strip().startswith("#")]


# --- .dockerignore ---------------------------------------------------------------------


def test_dockerignore_loai_bi_mat_csdl_va_moi_truong_ao():
    muc = set(_dong_lenh(_doc(".dockerignore")))

    for can in (".env", "*.db", ".venv", ".git"):
        assert can in muc, f".dockerignore thiếu {can!r}: nội dung đó sẽ lọt vào bối cảnh dựng image"


# --- Dockerfile ------------------------------------------------------------------------


def test_dockerfile_khong_sao_chep_env_hay_ca_thu_muc_goc():
    for d in _dong_lenh(_doc("Dockerfile")):
        if d.upper().startswith(("COPY", "ADD")):
            assert ".env" not in d, f"Dockerfile nướng .env vào image: {d}"
            # `COPY . .` kéo cả docs/, tests/, petcare.db (nếu .dockerignore lỡ thiếu) vào image.
            assert not re.match(r"(COPY|ADD)\s+(--\S+\s+)*\.\s", d, re.I), f"COPY cả thư mục gốc: {d}"


def test_dockerfile_chay_bang_user_thuong_truoc_lenh_khoi_dong():
    dong = _dong_lenh(_doc("Dockerfile"))
    chi_so_user = [i for i, d in enumerate(dong) if d.upper().startswith("USER ")]
    chi_so_cmd = [i for i, d in enumerate(dong) if d.upper().startswith("CMD ")]

    assert chi_so_user and chi_so_cmd, "Dockerfile phải có USER và CMD"
    assert chi_so_user[-1] < chi_so_cmd[-1], "USER phải đứng trước CMD"
    assert dong[chi_so_user[-1]].split()[1] not in ("root", "0")


def test_dockerfile_dat_csdl_o_volume_data_va_chi_seed_khi_chua_co_file():
    noi_dung = _doc("Dockerfile")

    assert "DATABASE_URL=sqlite:////data/petcare.db" in noi_dung  # 4 dấu "/" = đường dẫn tuyệt đối
    assert "VOLUME" in noi_dung and "/data" in noi_dung
    # Seed vô điều kiện thì mỗi lần khởi động lại container lại thêm dữ liệu mẫu vào CSDL thật.
    assert re.search(r"\[\s+-f\s+/data/petcare\.db\s+\]\s*\|\|\s*python -m app\.seed", noi_dung)


def test_dockerfile_cai_thu_vien_truoc_khi_chep_ma_nguon_de_tan_dung_cache():
    dong = _dong_lenh(_doc("Dockerfile"))
    pip = next(i for i, d in enumerate(dong) if "pip install" in d)
    chep_app = next(i for i, d in enumerate(dong) if re.match(r"COPY\s+app\b", d, re.I))

    assert pip < chep_app


# --- docker-compose.yml ----------------------------------------------------------------


def test_compose_chi_mo_cong_cho_may_local_khong_mo_ra_mang_lan():
    cong = [d for d in _dong_lenh(_doc("docker-compose.yml")) if '"' in d and ":8000" in d]

    assert cong, "không tìm thấy dòng ánh xạ cổng"
    assert all("127.0.0.1:" in d for d in cong), f"cổng mở ra mọi giao diện mạng: {cong}"


def test_compose_dung_volume_co_ten_va_ghi_de_database_url_ve_data():
    noi_dung = _doc("docker-compose.yml")

    assert re.search(r"petcare-data:/data", noi_dung)
    assert "DATABASE_URL: sqlite:////data/petcare.db" in noi_dung  # .env dùng ./petcare.db, trong container sẽ mất khi dựng lại


def test_compose_khong_ghi_cung_bi_mat_ma_lay_tu_env():
    noi_dung = _doc("docker-compose.yml")

    assert "env_file" in noi_dung
    # SECRET_KEY phải đến từ .env, không được có giá trị viết thẳng trong file này (file vào git).
    assert not re.search(r"SECRET_KEY\s*:\s*\S", noi_dung)
    assert "matkhau123" not in noi_dung


def test_compose_chuyen_ba_bien_cong_khai_tu_moi_truong_va_mac_dinh_la_tat():
    noi_dung = _doc("docker-compose.yml")

    assert "SESSION_HTTPS_ONLY: ${SESSION_HTTPS_ONLY:-false}" in noi_dung
    assert "APP_ORIGIN: ${APP_ORIGIN:-}" in noi_dung
    assert "SEED_MAT_KHAU: ${SEED_MAT_KHAU:-}" in noi_dung
