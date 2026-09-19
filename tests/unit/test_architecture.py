"""Test canh gác các ranh giới của dự án — không kiểm hành vi, kiểm kỷ luật.

Mỗi test ở đây sinh ra từ một lỗi đã thật sự xảy ra. Chúng không kiểm chức năng nào cho
người dùng; chúng ngăn một loại lỗi lặp lại.

Vì sao là test chứ không phải một dòng luật trong CLAUDE.md: luật phải được đọc và nhớ
mới có tác dụng — luật "chỉ tick ô kiểm được thật" viết ra từ P1 mà vẫn bị phạm lại ở P2
và P3. Test thì đỏ, không cần ai nhớ.

Xem thêm: CLAUDE.md mục 9.
"""

import re
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]

FILE_ROUTER = sorted((GOC / "app" / "routers").glob("*.py"))
FILE_SERVICE = [
    p for p in sorted((GOC / "app" / "services").glob("*.py")) if p.name != "__init__.py"
]
# Luật bao phủ của CLAUDE.md mục 7 nói tới `app/services/`, nhưng `app/ai/` cũng là tầng
# nghiệp vụ gọi thẳng được và là nơi guardrail sống — mở phép canh sang đó từ P7.
FILE_AI = [
    p for p in sorted((GOC / "app" / "ai").glob("*.py")) if p.name != "__init__.py"
]


def _doc(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# --- Ranh giới router / services -------------------------------------------------


@pytest.mark.parametrize("tep", FILE_ROUTER, ids=lambda p: p.name)
def test_router_khong_ghi_thang_xuong_csdl(tep):
    """Router chỉ làm HTTP — CLAUDE.md mục 8.

    Lỗi thật: P1 viết toàn bộ nghiệp vụ tài khoản thẳng trong `app/routers/users.py`.
    Hậu quả: quy tắc "quản lý không tự khóa chính mình" là nghiệp vụ thuần nhưng chỉ
    kiểm được bằng cách dựng TestClient và gửi form.

    NẾU TEST NÀY ĐỎ: chuyển thao tác sang `app/services/`, đừng xóa test.
    """
    ghi = re.findall(r"\bdb\.(add|add_all|commit|delete|flush)\(", _doc(tep))

    assert not ghi, (
        f"{tep.name} gọi db.{'/'.join(sorted(set(ghi)))} trực tiếp. "
        f"Chuyển thao tác này sang app/services/ rồi gọi từ router."
    )


@pytest.mark.parametrize("tep", FILE_SERVICE, ids=lambda p: p.name)
def test_services_khong_phu_thuoc_fastapi(tep):
    """Tầng nghiệp vụ phải test được mà không khởi động app — CLAUDE.md mục 8.

    Đây là điều kiện để tầng unit test tồn tại. Một lần import fastapi vào `services/`
    là cả tầng đó sụp về mức integration.
    """
    assert not re.search(r"^\s*(from fastapi|import fastapi)", _doc(tep), re.M), (
        f"{tep.name} import fastapi. Tầng services/ phải gọi được trực tiếp trong test."
    )


@pytest.mark.parametrize("tep", FILE_ROUTER, ids=lambda p: p.name)
def test_router_khong_import_thang_vao_app_ai(tep):
    """Mọi lời gọi AI đi qua `app/ai/service.py` — CLAUDE.md mục 8.

    Chưa có hiệu lực vì `app/ai/` chưa tồn tại; đặt sẵn cho P7, phase có ranh giới dễ vỡ
    nhất: gọi thẳng `gemini.py` từ router sẽ bỏ qua bước lọc dữ liệu cá nhân và bước
    chèn khuyến cáo bác sĩ thú y.
    """
    # Bắt cả hai lối viết: `from app.ai.x import ...` và `import app.ai.x`. Kẽ hở này lộ ra
    # khi mở P7 — bản cũ chỉ bắt lối thứ nhất, nên lối thứ hai vẫn lách qua được.
    noi_dung = _doc(tep)
    sai = [
        m
        for m in re.findall(r"^\s*from app\.ai\.(\w+)", noi_dung, re.M)
        + re.findall(r"^\s*import app\.ai\.(\w+)", noi_dung, re.M)
        if m != "service"
    ]

    assert not sai, (
        f"{tep.name} import thẳng app/ai/{sai}. Chỉ được gọi qua app/ai/service.py."
    )


# --- Tài liệu đi song song với code ----------------------------------------------


def test_moi_link_tuong_doi_trong_tai_lieu_deu_ton_tai():
    """Tài liệu chết dần khi đổi tên file mà không ai biết."""
    tai_lieu = sorted(GOC.glob("*.md")) + sorted((GOC / "docs").rglob("*.md"))

    hong = []
    for md in tai_lieu:
        for lien_ket in re.findall(r"\]\(([^)#]+?)(?:#[^)]*)?\)", _doc(md)):
            if lien_ket.startswith(("http", "mailto")):
                continue
            if not (md.parent / lien_ket).resolve().exists():
                hong.append(f"{md.relative_to(GOC).as_posix()} -> {lien_ket}")

    assert not hong, "Link hỏng trong tài liệu:\n  " + "\n  ".join(hong)


def test_moi_file_app_va_tests_deu_co_trong_codebase_map():
    """Lỗi lặp số một của dự án: tài liệu nói thứ code không làm, và ngược lại.

    CLAUDE.md mục 6 bắt cập nhật `codebase-map.md` khi thêm/xóa/đổi vai trò một file.
    Trước khi có test này, luật đó chỉ được thực hiện khi agent nhớ ra.

    NẾU TEST NÀY ĐỎ: thêm dòng mô tả file vào `docs/codebase-map.md`, đừng xóa test.

    Kẽ hở đã sửa 13/09: luật cũ nhận một file khi bản đồ có dòng nào **trùng tên file**,
    kể cả ở thư mục khác — `app/routers/stats.py` từng lọt qua nhờ dòng `services/stats.py`,
    và chỉ bị bắt bằng mắt. Nay so theo đuôi đường dẫn, cắt trên dấu `/`.
    """
    nhac = set(re.findall(r"`([^`]+)`", _doc(GOC / "docs" / "codebase-map.md")))

    tep = []
    for thu_muc in ("app", "tests"):
        for p in sorted((GOC / thu_muc).rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            if p.suffix not in (".py", ".html", ".css"):
                continue
            # `__init__.py` rỗng chỉ đánh dấu package, không có vai trò gì để mô tả.
            # `models/__init__.py` có nội dung (gom model cho `create_all`) nên vẫn bị đòi.
            if p.name == "__init__.py" and not _doc(p).strip():
                continue
            tep.append(p)

    trung_ten = {p.name for p in tep if sum(q.name == p.name for q in tep) > 1}

    thieu = [
        p.relative_to(GOC).as_posix()
        for p in tep
        if not any(
            _bao_phu(p.relative_to(GOC).as_posix(), m, p.name in trung_ten) for m in nhac
        )
    ]

    assert not thieu, "File chưa có trong docs/codebase-map.md:\n  " + "\n  ".join(thieu)


def _bao_phu(duong_dan: str, nhac: str, ten_bi_trung: bool) -> bool:
    """Dòng bản đồ `nhac` có mô tả đúng file `duong_dan` không."""
    if nhac == duong_dan:
        return True
    if not duong_dan.endswith("/" + nhac):
        return False
    # Dòng ghi mỗi tên file (`main.py`) thì chấp nhận — bản đồ chia mục theo thư mục nên
    # viết đủ `app/main.py` ở mọi dòng là thừa. Nhưng khi hai thư mục có file trùng tên,
    # một dòng như thế nhận thay cho cả hai: lúc đó bắt buộc ghi kèm thư mục.
    return "/" in nhac or not ten_bi_trung


def test_moi_loai_o_nhap_deu_dung_chung_quy_tac_khung_voi_input():
    """Lỗi thật: form hồ sơ chăm sóc ở P4 là form đầu tiên dùng `<textarea>`.

    `style.css` chỉ tạo kiểu cho `input, select`, nên ba ô nhập lệch hẳn khỏi nhãn, chữ
    monospace, không giãn hết chiều rộng — khác hẳn mọi form khác. Không test nào bắt
    được vì HTML vẫn đúng; chỉ nhìn bằng mắt mới thấy.

    Đây là phép kiểm HÌNH DẠNG, không phải phép kiểm giao diện: nó chỉ khẳng định mọi
    thẻ nhập liệu dùng trong template đều nằm chung bộ chọn với `input` ở quy tắc khung
    (`width: 100%`). Trông có đẹp hay không thì vẫn phải nhìn bằng mắt.

    NẾU TEST NÀY ĐỎ: thêm thẻ đó vào bộ chọn của quy tắc khung, đừng xóa test.
    """
    css = _doc(GOC / "app" / "static" / "style.css")
    html = "".join(_doc(p) for p in (GOC / "app" / "templates").glob("*.html"))

    quy_tac_khung = [
        khoi.split("{")[0].rsplit("}", 1)[-1]
        for khoi in re.findall(r"[^{}]*\{[^{}]*\}", css)
        if "width: 100%" in khoi and re.search(r"(^|[\s,])input([\s,:]|$)", khoi.split("{")[0])
    ]
    assert quy_tac_khung, "Không tìm thấy quy tắc khung dùng chung cho ô nhập liệu."
    bo_chon = quy_tac_khung[0]

    thieu = [
        the
        for the in ("input", "select", "textarea")
        if f"<{the}" in html and not re.search(rf"(^|[\s,]){the}([\s,:]|$)", bo_chon)
    ]

    assert not thieu, (
        "Template dùng thẻ này nhưng nó không nằm trong quy tắc khung dùng chung "
        f"({bo_chon.strip()}): " + ", ".join(thieu)
    )


# --- Bao phủ tầng nghiệp vụ ------------------------------------------------------


def test_moi_ham_public_trong_services_deu_duoc_goi_thang_trong_test():
    """Luật bao phủ — CLAUDE.md mục 7.

    Lỗi thật: đến sau P3 còn 10 hàm public chỉ được kiểm gián tiếp qua router. Kiểm gián
    tiếp thì khi đỏ không biết lỗi nằm ở hàm nền hay ở lớp gọi nó.

    Đây là ngưỡng sàn, không phải trần: nó chỉ bảo đảm hàm CÓ được gọi thẳng, không bảo
    đảm đủ 1 happy path + 1 ca biên. Phần đó vẫn thuộc trách nhiệm người viết test.
    """
    van_ban_test = "".join(_doc(p) for p in (GOC / "tests").rglob("test_*.py"))

    thieu = []
    for tep in FILE_SERVICE + FILE_AI:
        if tep.name in ("errors.py", "provider.py"):
            continue
        for ham in re.findall(r"^def ([a-z][a-z0-9_]*)\(", _doc(tep), re.M):
            if f"{ham}(" not in van_ban_test:
                thieu.append(f"{tep.name}::{ham}")

    assert not thieu, "Hàm public chưa có test gọi thẳng:\n  " + "\n  ".join(thieu)


def test_moi_class_dung_trong_template_deu_co_trong_css():
    """Lỗi thật, ba lần trong cùng phase P4: `chinh-nhe`, `bat-buoc`, `dong-canh-bao`.

    Cả ba được viết vào template với ý đồ tạo kiểu — link "Ghi hồ sơ" nổi hơn link thường,
    dấu sao đỏ ở ô bắt buộc, dòng quá hạn có nền cảnh báo — nhưng không có quy tắc CSS nào
    tương ứng. Trang vẫn dựng đúng, mọi test vẫn xanh, chỉ là ý đồ không xảy ra. Không nhìn
    bằng mắt thì không ai biết.

    Kiểm hai dạng: class viết cứng, và class có dấu gạch nối nằm trong chuỗi của biểu thức
    Jinja (`class="{{ 'dong-canh-bao' if v.qua_han }}"`) — chính dạng thứ hai sinh ra lỗi
    `dong-canh-bao`, nên phép kiểm bỏ nó thì bỏ đúng ca đã xảy ra. Dấu gạch nối là cách
    phân biệt tên class với chuỗi so sánh thường (`'cancelled'`, `'manager'`).

    Class ghép từ biến (`nhan-{{ a.status }}`) vẫn nằm ngoài tầm và phải nhìn bằng mắt.

    NẾU TEST NÀY ĐỎ: thêm quy tắc CSS, hoặc bỏ class thừa khỏi template. Đừng xóa test.
    """
    css = _doc(GOC / "app" / "static" / "style.css")
    co_trong_css = set(re.findall(r"\.([a-z][a-z0-9-]*)", css))

    thieu = []
    for tep in sorted((GOC / "app" / "templates").glob("*.html")):
        noi_dung = _doc(tep)
        ten_class = []

        for khoi in re.findall(r'class="([^"]*)"', noi_dung):
            ten_class += re.findall(r"'([a-z][a-z0-9]*(?:-[a-z0-9]+)+)'", khoi)
            # Bỏ biểu thức Jinja rồi mới tách, nếu không sẽ nhặt cả `if`, `else`, `not`.
            ten_class += re.sub(r"\{\{.*?\}\}|\{%.*?%\}", " ", khoi, flags=re.S).split()

        for ten in ten_class:
            # Bỏ mảnh còn lại của class ghép từ biến, ví dụ `nhan-` của `nhan-{{ x }}`.
            if ten.startswith("-") or ten.endswith("-"):
                continue
            if ten not in co_trong_css:
                thieu.append(f"{tep.name}: .{ten}")

    assert not thieu, "Class dùng trong template nhưng không có trong style.css:\n  " + "\n  ".join(
        sorted(set(thieu))
    )


# --- Trạng thái hóa đơn chỉ được quyết ở một chỗ ----------------------------------


def test_chuoi_trang_thai_tien_chi_xuat_hien_o_model_va_service_hoa_don():
    """Ba chuỗi `unpaid`, `partial`, `paid` chỉ được viết ở hai file — kế hoạch P5.

    Cột `invoices.status` là bản cache của thứ suy được từ `payments`. Nó chỉ đúng chừng
    nào mọi phép ghi đi qua `billing.ghi_nhan_thanh_toan()`. Một dòng `if hd.status ==
    'paid'` trong router hay template là chỗ để logic tiền bạc âm thầm rẽ nhánh theo cột
    cache thay vì theo số tiền thật; tệ hơn, một dòng gán `status = 'paid'` ở ngoài sẽ
    làm sổ sách lệch mà không test nào đỏ.

    `cancelled` KHÔNG nằm trong phép canh này vì nó cũng là trạng thái của lịch hẹn — cấm
    nó ở mọi nơi thì phải mở ngoại lệ cho `appointments`, và một phép canh đầy ngoại lệ
    thì không ai tin nữa.

    NẾU TEST NÀY ĐỎ: dùng `hd.ten_trang_thai`, `hd.con_no`, `billing.trang_thai_tinh_lai()`
    thay vì so chuỗi. Đừng xóa test.
    """
    duoc_phep = {"invoice.py", "billing.py"}
    tep_can_quet = [
        p
        for p in list((GOC / "app").rglob("*.py")) + list((GOC / "app").rglob("*.html"))
        if "__pycache__" not in p.parts and p.name not in duoc_phep
    ]

    vi_pham = []
    for tep in sorted(tep_can_quet):
        for chuoi in re.findall(r"""['"](unpaid|partial|paid)['"]""", _doc(tep)):
            vi_pham.append(f"{tep.relative_to(GOC)}: '{chuoi}'")

    assert not vi_pham, (
        "Chuỗi trạng thái tiền chỉ được viết trong app/models/invoice.py và "
        "app/services/billing.py:\n  " + "\n  ".join(sorted(set(vi_pham)))
    )


def _doi_so_cua(ma_nguon: str, mo_dau: str) -> list[str]:
    """Cắt phần trong ngoặc của từng lời gọi `mo_dau`, có đếm ngoặc lồng nhau.

    Không dùng regex kiểu `\\(.*?\\)`: thông báo lỗi thường có f-string gọi hàm bên trong
    (`{_so(hd.con_no)}`), và regex sẽ dừng ở dấu đóng ngoặc ĐẦU TIÊN — tức bỏ sót đúng
    phần chữ nằm sau nó, đúng ca đã sinh ra phép canh này.
    """
    ket_qua = []
    i = ma_nguon.find(mo_dau)
    while i != -1:
        j, sau = i + len(mo_dau), 1
        while j < len(ma_nguon) and sau:
            sau += (ma_nguon[j] == "(") - (ma_nguon[j] == ")")
            j += 1
        ket_qua.append(ma_nguon[i + len(mo_dau) : j - 1])
        i = ma_nguon.find(mo_dau, j)
    return ket_qua


def test_thong_bao_loi_nghiep_vu_khong_lot_ma_phase_ra_ngoai():
    """Thông điệp `LoiNghiepVu` hiện thẳng cho người dùng — CLAUDE.md mục 5.

    Lỗi thật: P5 viết "Số tiền vượt quá số còn nợ (90.000đ). P5 chưa làm nghiệp vụ hoàn
    tiền." Lễ tân đọc câu đó không biết "P5" là gì; đó là từ vựng của người làm dự án,
    không phải của người dùng cửa hàng.

    Chỉ quét chuỗi bên trong `LoiNghiepVu(...)`, không quét docstring hay comment — nói
    về phase trong tài liệu nội bộ là đúng chỗ.

    NẾU TEST NÀY ĐỎ: viết lại thông báo theo lời người dùng ("hệ thống chưa làm..."),
    đừng xóa test.
    """
    vi_pham = []
    for tep in FILE_SERVICE + FILE_ROUTER:
        for loi in _doi_so_cua(_doc(tep), "LoiNghiepVu("):
            ma_phase = re.findall(r"\bP[0-9]\b", loi)
            if ma_phase:
                vi_pham.append(f"{tep.name}: {'/'.join(ma_phase)}")

    assert not vi_pham, (
        "Thông báo lỗi cho người dùng có mã phase của dự án:\n  " + "\n  ".join(vi_pham)
    )


def test_moi_link_tren_thanh_dieu_huong_deu_co_the_tren_trang_chu():
    """Trang chủ là màn hình đầu tiên sau đăng nhập — nó phải liệt kê đủ chức năng.

    Lỗi thật, lặp lần thứ ba của cùng một lớp: P5 thêm link "Hóa đơn" vào thanh điều
    hướng nhưng quên thẻ trên trang chủ, y như P2b thêm trang dịch vụ mà quên link menu
    cho hai vai trò, và P4 quên link "Chủ nuôi" cho nhân viên chăm sóc. CLAUDE.md mục 9
    dòng 4 nói "sửa một lỗi thì soát cả lớp lỗi"; phép canh này biến câu đó thành máy.

    Chỉ so danh sách đường dẫn, KHÔNG so điều kiện vai trò — vai trò phải kiểm bằng test
    integration vì nó phụ thuộc dữ liệu đăng nhập.

    NẾU TEST NÀY ĐỎ: thêm thẻ vào home.html, hoặc bỏ link khỏi thanh điều hướng.
    """
    thanh = _doc(GOC / "app" / "templates" / "base.html")
    trang_chu = _doc(GOC / "app" / "templates" / "home.html")

    khoi_nav = thanh[thanh.index("<nav>") : thanh.index("</nav>")]
    thieu = [
        href
        for href in re.findall(r'href="(/[^"]*)"', khoi_nav)
        if f'href="{href}"' not in trang_chu
    ]

    assert not thieu, (
        "Có trong thanh điều hướng nhưng thiếu thẻ trên trang chủ: " + ", ".join(thieu)
    )


def test_dong_trang_thai_trong_readme_khop_phase_moi_nhat():
    """README nói dự án đang ở phase nào — và nó lệch suốt bốn phase liền.

    Lỗi thật: dòng "Trạng thái: **P1 xong**" viết ngày làm P1 và không ai sửa cho tới khi
    P5 xong. README là thứ người chấm và phiên agent mới đọc trước tiên, nên nó lệch là
    lệch ở chỗ đắt nhất. Lần thứ tư của lớp lỗi "tài liệu mô tả thứ không đúng với code"
    — US-18, TC-066, sơ đồ trong architecture.md, giờ tới README.

    Neo vào tên file báo cáo mới nhất trong docs/testing/reports/ vì đó là thứ luật DoD
    bắt phải sinh ra ở mỗi phase, nên nó không tự trôi. So bằng mã phase, không so ngày:
    một phase có thể có nhiều báo cáo.

    NẾU TEST NÀY ĐỎ: sửa dòng Trạng thái trong README cho khớp phase vừa xong.
    """
    bao_cao = sorted((GOC / "docs" / "testing" / "reports").glob("20*.md"))
    assert bao_cao, "Không có báo cáo nào trong docs/testing/reports/"

    phase = re.findall(r"P[0-9]", bao_cao[-1].name)
    assert phase, f"Tên báo cáo mới nhất không nêu phase: {bao_cao[-1].name}"

    dong = [d for d in _doc(GOC / "README.md").splitlines() if "Trạng thái:" in d]
    assert len(dong) == 1, f"README phải có đúng một dòng Trạng thái, đang có {len(dong)}"

    assert phase[-1] in dong[0], (
        f"README nói {dong[0].strip()!r} nhưng báo cáo mới nhất là của {phase[-1]} "
        f"({bao_cao[-1].name})"
    )


def test_so_luong_ghi_trong_codebase_map_khop_so_file_that():
    """`codebase-map.md` đếm số kế hoạch, số log phiên, số báo cáo — và đếm sai.

    Lỗi thật: bản đồ nói "Hiện có 5" kế hoạch trong khi có 9, "5" báo cáo trong khi có
    15, và dòng "Cập nhật lần cuối" dừng ở P3 suốt tới hết P5. Đây là file CLAUDE.md mục
    6 bắt agent đọc **đầu tiên** mỗi phiên, nên nó lệch là phiên sau làm việc trên thông
    tin sai — đúng thứ cả dự án dựng ra để chống.

    Phép canh sẵn có chỉ soát file trong `app/` và `tests/`; ba con số này nằm ở phần mô
    tả `docs/` nên không ai canh.

    NẾU TEST NÀY ĐỎ: sửa con số trong bản đồ, và nhân tiện đọc lại dòng "Cập nhật lần
    cuối" xem còn đúng không.
    """
    thu_muc = {
        "`plans/": GOC / "docs" / "plans",
        "`sessions/": GOC / "docs" / "sessions",
        "`testing/reports/": GOC / "docs" / "testing" / "reports",
    }
    lech = []
    da_soat = []

    for dong in _doc(GOC / "docs" / "codebase-map.md").splitlines():
        for dau, duong_dan in thu_muc.items():
            if not dong.startswith("| " + dau):
                continue
            ghi = re.search(r"Hiện có (\d+)", dong)
            if ghi is None:
                continue
            da_soat.append(dau)
            that = len(list(duong_dan.glob("20*.md")))
            if int(ghi.group(1)) != that:
                lech.append(f"{dau.strip('`')} bản đồ ghi {ghi.group(1)}, thực tế {that}")

    # Không tìm thấy dòng nào cũng là hỏng: hai lần trước, một phép canh mới xanh vì
    # regex của nó không khớp gì cả chứ không phải vì code đúng.
    assert len(da_soat) == 3, f"Chỉ soát được {da_soat}, bản đồ đã đổi cách viết ba dòng đó?"
    assert len(lech) == 0, "codebase-map.md dem sai:" + "".join('\n  ' + d for d in lech)


def _cot_trong_erd() -> dict[str, dict[str, str]]:
    """Đọc bảng mô tả cột của từng mục "### `bang`" trong docs/erd.md.

    Trả về {bảng: {cột: ô ràng buộc}}. Mỗi mục dừng ở tiêu đề `##`/`###` kế tiếp, nên bảng
    "Đối chiếu bảng với user story" ở cuối file không bị đọc nhầm thành cột của `ai_logs`.
    """
    erd = _doc(GOC / "docs" / "erd.md")
    return {
        bang: dict(re.findall(r"^\| `(\w+)` \| [^|]+ \| ([^|]*) \|", than, re.M))
        for bang, than in re.findall(r"^### `(\w+)`(.*?)(?=^##|\Z)", erd, re.M | re.S)
    }


def test_erd_khop_model_tung_cot():
    """ERD là tài liệu thiết kế đã nộp ở KT1 — nó phải nói đúng thứ CSDL thật có.

    Lỗi thật: đợt rà 08/09 ghi "ERD vs code: 0 lệch" nhưng chỉ so TÊN BẢNG. Rà 11/09 so tới
    từng cột thì ra bốn chỗ: thiếu `vaccinations.created_at`, một INDEX không tồn tại, một
    câu trái với US-21 đã sửa, một CHECK không ghi. Lần thứ năm của lớp lỗi "tài liệu nói
    thứ code không làm" — và lớp này tự động hóa được.

    Chỉ so bốn thứ đọc được không nhập nhằng: tập cột, NOT NULL, UNIQUE, khóa ngoại. Bảng
    có trong ERD mà code chưa có (`ai_logs` trước P7) được phép — thiết kế đi trước code.
    Chiều ngược lại thì không: bảng trong code phải có trong ERD.

    NẾU TEST NÀY ĐỎ: sửa docs/erd.md cho khớp model (hoặc sửa model nếu ERD mới đúng).
    """
    import app.models  # noqa: F401 — đăng ký mọi bảng vào metadata
    from sqlalchemy import UniqueConstraint

    from app.db import Base

    erd = _cot_trong_erd()
    # Đọc được quá ít bảng nghĩa là ERD đổi cách viết và regex hụt — phép canh xanh vì
    # không soát gì, đúng lỗi đã gặp hai lần với các phép canh trước.
    assert len(erd) >= len(Base.metadata.tables), f"Chỉ đọc được {sorted(erd)} từ erd.md"

    lech = []
    for ten, bang in sorted(Base.metadata.tables.items()):
        if ten not in erd:
            lech.append(f"{ten}: có trong code, không có trong ERD")
            continue
        cot_erd = erd[ten]
        cot_code = set(bang.columns.keys())

        for cot in sorted(set(cot_erd) ^ cot_code):
            lech.append(f"{ten}.{cot}: chỉ có ở {'ERD' if cot in cot_erd else 'code'}")

        for cot in sorted(set(cot_erd) & cot_code):
            c, rang_buoc = bang.columns[cot], cot_erd[cot]
            viet_hoa = rang_buoc.upper()

            if ("NOT NULL" in viet_hoa or "PK" in viet_hoa) != (not c.nullable):
                lech.append(f"{ten}.{cot}: ERD '{rang_buoc}', code nullable={c.nullable}")

            unique_code = bool(c.unique) or any(
                isinstance(k, UniqueConstraint) and [x.name for x in k.columns] == [cot]
                for k in bang.constraints
            )
            if ("UNIQUE" in viet_hoa) != unique_code:
                lech.append(f"{ten}.{cot}: ERD '{rang_buoc}', code unique={unique_code}")

            fk_erd = re.search(r"FK → `(\w+\.\w+)`", rang_buoc)
            fk_code = [f"{f.column.table.name}.{f.column.name}" for f in c.foreign_keys]
            if (fk_erd.group(1) if fk_erd else None) != (fk_code[0] if fk_code else None):
                lech.append(f"{ten}.{cot}: FK trong ERD {fk_erd and fk_erd.group(1)}, code {fk_code}")

    assert not lech, "docs/erd.md lệch model:\n  " + "\n  ".join(lech)


@pytest.mark.parametrize(
    "muc, ten_hang",
    [("3.1", "SYSTEM_NHAC_LICH"), ("3.2", "SYSTEM_TOM_TAT"), ("3.3", "SYSTEM_HOI_DAP")],
)
def test_system_prompt_in_trong_ai_safety_khop_tung_chu_voi_code(muc, ten_hang):
    """`ai-safety.md` là tài liệu nộp ở KT3 — prompt in trong đó phải là prompt đang chạy.

    Lỗi thật 19/09: mục 3.3 vẫn in dòng "Luôn kết thúc câu trả lời bằng lời nhắc…" đã bỏ khỏi
    code từ 18/09 (quyết định Q10), và mục 3.1 thiếu dòng xưng hô "Anh/chị". Thêm một lần của
    lớp lỗi "tài liệu nói thứ code không làm" (CLAUDE.md mục 9, bài học 2).

    NẾU TEST NÀY ĐỎ: chép lại nguyên văn hằng số trong app/ai/prompts.py vào khối ``` của mục đó.
    """
    from app.ai import prompts

    tai_lieu = _doc(GOC / "docs" / "ai-safety.md").replace("\r\n", "\n")
    khoi = re.search(rf"^### {re.escape(muc)} .*?\n```\n(.*?)\n```", tai_lieu, re.S | re.M)
    assert khoi, f"Không tìm thấy khối prompt của mục {muc} — tài liệu đã đổi cách viết?"
    assert khoi.group(1) == getattr(prompts, ten_hang)
