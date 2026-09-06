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
    sai = [m for m in re.findall(r"^\s*from app\.ai\.(\w+)", _doc(tep), re.M) if m != "service"]

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
    """
    nhac = set(re.findall(r"`([^`]+)`", _doc(GOC / "docs" / "codebase-map.md")))

    thieu = []
    for thu_muc in ("app", "tests"):
        for p in sorted((GOC / thu_muc).rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            if p.suffix not in (".py", ".html", ".css"):
                continue
            duong_dan = p.relative_to(GOC).as_posix()
            if not any(m == duong_dan or m.endswith("/" + p.name) or m == p.name for m in nhac):
                thieu.append(duong_dan)

    assert not thieu, "File chưa có trong docs/codebase-map.md:\n  " + "\n  ".join(thieu)


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
    for tep in FILE_SERVICE:
        if tep.name == "errors.py":
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
