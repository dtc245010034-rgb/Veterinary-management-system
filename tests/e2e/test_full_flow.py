"""Kịch bản xuyên suốt — TC-101, bước 1 → 9 của docs/testing/test-strategy.md mục 6.

Khác mọi tầng test khác ở một điểm quyết định: **test này không được tự dựng URL.**
Nó bắt đầu ở "/" rồi chỉ đi tiếp bằng link và nút có thật trong HTML vừa nhận, và gửi
form đúng như trình duyệt gửi.

Vì sao ràng buộc đó là lý do tồn tại của file này: năm trong chín lỗi tìm được ngày
05/09 lọt qua toàn bộ test tầng HTTP vì test gọi thẳng URL còn người dùng đi theo đường
bấm. Nặng nhất là lỗi ô `<select>` không có option nào `selected` — trình duyệt gửi
option đầu tiên, nên bấm "Đổi" mà không sửa gì lại chuyển lịch sang tên người khác. Test
tự dựng `data={...}` không bao giờ chạm tới lỗi đó, vì nó không gửi thứ trình duyệt gửi.

Bước 10 → 11 (AI tóm tắt, thống kê) nối tiếp ở P6 và P7. Vì vậy TC-101 vẫn là 🟡 chứ
chưa phải ✅.
"""

import re
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from html.parser import HTMLParser
from urllib.parse import urljoin

import pytest

# Lấy từ conftest thay vì viết cứng: bài học số 1 trong CLAUDE.md mục 9 — ba lần test đỏ
# vì giả định về dữ liệu được viết cứng thay vì đọc từ nơi sinh ra dữ liệu.
from tests.conftest import MAT_KHAU_MAU, MOC_THOI_GIAN

DAI_HAN = 45  # phút — thời lượng dịch vụ dùng trong kịch bản


def _gon(chuoi: str) -> str:
    return re.sub(r"\s+", " ", chuoi).strip()


# --- Trình duyệt tí hon ----------------------------------------------------------


@dataclass
class _Form:
    action: str
    method: str
    truong: dict[str, str] = field(default_factory=dict)
    lua_chon: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    nhan_nut: list[str] = field(default_factory=list)


class _BocTrang(HTMLParser):
    """Bóc link, form và chữ hiển thị ra khỏi HTML.

    Chỉ hiểu đúng phần HTML mà dự án này dùng. Ô `checkbox`/`radio` cố ý ném lỗi thay vì
    đoán: gửi sai một ô như vậy sẽ làm test xanh vì lý do sai — đúng loại lỗi mà file này
    sinh ra để chặn.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lien_ket: list[tuple[str, str]] = []
        self.form: list[_Form] = []
        self.chu: list[str] = []
        self._form: _Form | None = None
        self._select: str | None = None
        self._thu: list | None = None  # [loại thẻ, giá trị, [chữ], có 'selected']
        self._bo_qua = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)

        if tag in ("script", "style"):
            self._bo_qua = True
        elif tag == "a" and "href" in a:
            self._thu = ["a", a["href"], [], False]
        elif tag == "form":
            self._form = _Form(a.get("action", ""), a.get("method", "get").lower())
        elif self._form is None:
            return
        elif tag == "input":
            loai = a.get("type", "text").lower()
            if loai in ("checkbox", "radio"):
                raise NotImplementedError(
                    f"Trình duyệt tí hon chưa biết gửi ô {loai} (name={a.get('name')}). "
                    "Bổ sung vào _BocTrang trước khi dùng form này trong e2e."
                )
            if "name" in a and loai != "submit":
                self._form.truong[a["name"]] = a.get("value", "")
        elif tag == "select":
            self._select = a.get("name")
            self._form.lua_chon.setdefault(self._select, [])
        elif tag == "option" and self._select is not None:
            self._thu = ["option", a.get("value"), [], "selected" in a]
        elif tag == "textarea" and "name" in a:
            self._thu = ["textarea", a["name"], [], False]
        elif tag == "button":
            self._thu = ["button", None, [], False]

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._bo_qua = False

        if self._thu is not None and tag == self._thu[0]:
            self._dong_the(*self._thu)
            self._thu = None

        if tag == "select":
            self._select = None
        elif tag == "form" and self._form is not None:
            self.form.append(self._form)
            self._form = None

    def handle_data(self, du_lieu):
        if self._bo_qua:
            return
        self.chu.append(du_lieu)
        if self._thu is not None:
            self._thu[2].append(du_lieu)

    def _dong_the(self, loai, gia_tri, cac_chu, co_chon):
        chu = _gon("".join(cac_chu))

        if loai == "a":
            self.lien_ket.append((chu, gia_tri))
        elif self._form is None:
            return
        elif loai == "option" and self._select is not None:
            gia = gia_tri if gia_tri is not None else chu
            self._form.lua_chon[self._select].append((chu, gia))
            # Đúng như trình duyệt: option đầu tiên là mặc định khi không có 'selected'.
            if co_chon or self._select not in self._form.truong:
                self._form.truong[self._select] = gia
        elif loai == "textarea":
            self._form.truong[gia_tri] = chu
        elif loai == "button":
            self._form.nhan_nut.append(chu)


class TrinhDuyet:
    """Đi qua ứng dụng như người dùng: chỉ bấm link và nút có thật trên trang."""

    def __init__(self, client):
        self._client = client
        self.duong_dan = ""
        self.ma = 0
        self._trang = _BocTrang()

    # --- thao tác ---

    def mo(self, duong_dan: str) -> None:
        """Địa chỉ gõ tay. Trong kịch bản chỉ dùng đúng một lần, cho trang chủ."""
        self._di("GET", duong_dan)

    def bam(self, chu: str) -> None:
        dich = {href for nhan, href in self._trang.lien_ket if chu.casefold() in nhan.casefold()}

        if not dich:
            raise AssertionError(
                f"Không có link nào chứa “{chu}” trên {self.duong_dan}. "
                f"Đang có: {[n for n, _ in self._trang.lien_ket]}"
            )
        if len(dich) > 1:
            raise AssertionError(f"“{chu}” khớp nhiều link khác nhau: {sorted(dich)}")

        self._di("GET", urljoin(self.duong_dan, dich.pop()))

    def gui(self, nut: str, **truong: str) -> None:
        """Điền và bấm nút `nut`. Trường không khai vẫn được gửi theo giá trị mặc định."""
        form = self._tim_form(nut)
        du_lieu = dict(form.truong)

        for ten, gia in truong.items():
            if ten not in du_lieu:
                raise AssertionError(
                    f"Form “{nut}” không có ô “{ten}”. Đang có: {sorted(du_lieu)}"
                )
            du_lieu[ten] = self._gia_tri(form, ten, gia)

        self._di(form.method.upper(), urljoin(self.duong_dan, form.action), du_lieu)

    # --- đọc trang ---

    @property
    def van_ban(self) -> str:
        return _gon("".join(self._trang.chu))

    @property
    def nut(self) -> list[str]:
        return [nhan for f in self._trang.form for nhan in f.nhan_nut]

    # --- nội bộ ---

    def _di(self, phuong_thuc: str, dia_chi: str, du_lieu: dict | None = None) -> None:
        phan_hoi = self._client.request(
            phuong_thuc, dia_chi, data=du_lieu, follow_redirects=True
        )
        self.ma = phan_hoi.status_code
        self.duong_dan = str(phan_hoi.url)
        self._trang = _BocTrang()
        self._trang.feed(phan_hoi.text)

    def _tim_form(self, nut: str) -> _Form:
        khop = [f for f in self._trang.form if any(nut in n for n in f.nhan_nut)]

        if not khop:
            raise AssertionError(
                f"Không có nút nào chứa “{nut}” trên {self.duong_dan}. Đang có: {self.nut}"
            )
        if len(khop) > 1:
            raise AssertionError(f"“{nut}” khớp {len(khop)} form khác nhau, không rõ bấm cái nào.")

        return khop[0]

    def _gia_tri(self, form: _Form, ten: str, gia: str) -> str:
        """Trong ô chọn, người dùng chọn theo NHÃN nhìn thấy chứ không theo id."""
        if ten not in form.lua_chon:
            return gia

        cac_nhan = form.lua_chon[ten]
        khop = [v for nhan, v in cac_nhan if nhan == gia] or [
            v for nhan, v in cac_nhan if gia.casefold() in nhan.casefold()
        ]

        if len(khop) != 1:
            raise AssertionError(
                f"“{gia}” khớp {len(khop)} lựa chọn trong ô “{ten}”. "
                f"Đang có: {[n for n, _ in cac_nhan]}"
            )

        return khop[0]


# --- Hạ tầng: CSDL file thật, mỗi request một session ----------------------------


@pytest.fixture
def tao_phien(tmp_path):
    """Sessionmaker trên CSDL **file thật**, không phải in-memory.

    Fixture `db` dùng chung một session cho cả test lẫn ứng dụng, nên lỗi "quên commit"
    không lộ ra. Ở đây mỗi request lấy một session riêng đúng như production, và dữ liệu
    chỉ sang được request sau nếu đã thật sự ghi xuống file.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa: F401 — đăng ký mọi bảng trước create_all
    from app.db import Base

    engine = create_engine(
        f"sqlite:///{tmp_path / 'e2e.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine, autoflush=False)
    finally:
        engine.dispose()


@pytest.fixture
def nen_e2e(tao_phien, bam_mat_khau_mau):
    """Tài khoản và bảng giá — thứ đã có sẵn trước khi cửa hàng mở cửa.

    Chủ nuôi, thú cưng và lịch hẹn KHÔNG dựng ở đây: chúng là việc người dùng làm qua
    giao diện, và kịch bản phải đi qua đúng con đường đó.
    """
    from app.models.service import Service
    from app.models.user import User

    phien = tao_phien()
    try:
        # Hai nhân viên chăm sóc, và người ĐƯỢC phân lịch cố ý không phải người đứng đầu
        # danh sách (danh sách xếp theo tên). Nhờ vậy, nếu ô chọn nhân viên trong form đổi
        # lịch mất dấu 'selected', trình duyệt sẽ gửi người đứng đầu và lịch âm thầm sang
        # tên người khác — đúng lỗi nặng nhất tìm được ngày 05/09. Chỉ một nhân viên thì
        # bước 5 xanh một cách tình cờ và không chứng minh gì.
        tai_khoan = [
            User(username="letan", full_name="Tran Thi Le", role="receptionist"),
            User(username="chamsoc1", full_name="Le Van Cham", role="caretaker"),
            User(username="chamsoc2", full_name="Bui Thi An", role="caretaker"),
        ]
        for u in tai_khoan:
            u.password_hash = bam_mat_khau_mau
        dich_vu = Service(
            code="TAM", name="Tắm và sấy", duration_min=DAI_HAN, price=Decimal("150000")
        )
        phien.add_all([*tai_khoan, dich_vu])
        phien.commit()

        return {
            "le_tan": tai_khoan[0].username,
            "nhan_vien": tai_khoan[1].username,
            "ten_nhan_vien": tai_khoan[1].full_name,
            "ten_nhan_vien_khac": tai_khoan[2].full_name,
            "ten_dich_vu": dich_vu.name,
        }
    finally:
        phien.close()


@pytest.fixture
def trinh_duyet(tao_phien):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def get_db_file():
        phien = tao_phien()
        try:
            yield phien
        finally:
            phien.close()

    app.dependency_overrides[get_db] = get_db_file
    try:
        yield TrinhDuyet(TestClient(app))
    finally:
        app.dependency_overrides.clear()


# --- Kịch bản --------------------------------------------------------------------

GIO_DAT = MOC_THOI_GIAN.replace(hour=9)  # 09:00–09:45
GIO_TRUNG = MOC_THOI_GIAN.replace(hour=9, minute=15)  # chèn vào giữa lịch trên
GIO_DOI = MOC_THOI_GIAN.replace(hour=10)  # khung còn trống
SAU_BUOI_CHAM = GIO_DOI + timedelta(hours=1)  # lúc nhân viên ngồi ghi hồ sơ


def test_tu_dat_lich_den_ho_so_cham_soc(trinh_duyet, nen_e2e):
    """Lễ tân tạo khách, đặt lịch, bị chặn trùng, đổi lịch; nhân viên ghi hồ sơ."""
    from app.services import clock

    tb = trinh_duyet

    with clock.freeze(MOC_THOI_GIAN):
        # 1. Chưa đăng nhập thì mọi đường đều dẫn về trang đăng nhập.
        tb.mo("/")
        assert tb.duong_dan.endswith("/login")

        tb.gui("Đăng nhập", username=nen_e2e["le_tan"], password=MAT_KHAU_MAU)
        assert "Xin chào" in tb.van_ban

        # 2. Tạo chủ nuôi rồi tạo thú cưng — mở hồ sơ khách bằng chính link vừa hiện ra.
        tb.bam("Chủ nuôi")
        tb.gui("Thêm chủ nuôi", ho_ten="Vũ Thị Hoa", so_dien_thoai="0906111222")
        assert "Vũ Thị Hoa" in tb.van_ban

        tb.bam("Vũ Thị Hoa")
        tb.gui("Thêm thú cưng", ten="Miu", loai="Mèo", giong="Anh lông ngắn")
        tb.gui("Thêm thú cưng", ten="Đốm", loai="Chó")
        assert "Thú cưng (2)" in tb.van_ban

        # 3. Đặt lịch. Ô chọn điền theo NHÃN nhìn thấy, không theo id.
        tb.bam("Lịch hẹn")
        tb.gui(
            "Đặt lịch",
            thu_cung_id="Miu",
            dich_vu_id=nen_e2e["ten_dich_vu"],
            nhan_vien_id=nen_e2e["ten_nhan_vien"],
            gio=f"{GIO_DAT:%H:%M}",
        )
        assert tb.ma == 200
        assert f"{GIO_DAT:%H:%M}–{GIO_DAT + timedelta(minutes=DAI_HAN):%H:%M}" in tb.van_ban

        # 4. Con thứ hai, cùng nhân viên, chèn vào giữa buổi đang bận → phải bị từ chối.
        tb.gui(
            "Đặt lịch",
            thu_cung_id="Đốm",
            dich_vu_id=nen_e2e["ten_dich_vu"],
            nhan_vien_id=nen_e2e["ten_nhan_vien"],
            gio=f"{GIO_TRUNG:%H:%M}",
        )
        assert tb.ma == 400
        assert f"Nhân viên {nen_e2e['ten_nhan_vien']} đã có lịch" in tb.van_ban
        assert "Khung giờ còn trống" in tb.van_ban

        # 5. Đổi lịch sang khung trống. Chỉ sửa giờ; nhân viên phải giữ nguyên theo
        #    option đang được chọn sẵn — không khai lại thì trình duyệt gửi cái đó.
        tb.gui("Đổi", gio=f"{GIO_DOI:%H:%M}")
        assert tb.ma == 200
        assert f"{GIO_DOI:%H:%M}–{GIO_DOI + timedelta(minutes=DAI_HAN):%H:%M}" in tb.van_ban
        assert "Đã đổi lịch" in tb.van_ban
        # Lịch có còn thuộc về đúng nhân viên không thì không đọc được ở trang này — tên
        # người kia cũng nằm trong ô chọn nên chữ nào cũng có mặt. Bằng chứng thật nằm ở
        # bước 6: người được phân lịch phải thấy nó trong "Lịch của tôi".

        tb.gui("Đăng xuất")

    # 6. Sau buổi chăm sóc, nhân viên ghi hồ sơ từ lịch của chính mình.
    with clock.freeze(SAU_BUOI_CHAM):
        tb.gui("Đăng nhập", username=nen_e2e["nhan_vien"], password=MAT_KHAU_MAU)
        tb.bam("Lịch của tôi")
        # Đây là chỗ chứng minh bước 5 không âm thầm đổi nhân viên: lịch phải nằm trong
        # danh sách của chính người được phân, không phải của người đứng đầu ô chọn.
        assert "Miu" in tb.van_ban
        assert nen_e2e["ten_nhan_vien_khac"] not in tb.van_ban

        tb.bam("Ghi hồ sơ")
        tb.gui(
            "Lưu hồ sơ",
            tinh_trang="Da sạch, không phát hiện ve",
            viec_da_lam="Tắm, sấy, cắt móng",
            dan_do="Tắm lại sau 3 tuần",
        )
        assert tb.ma == 200
        assert "Hoàn thành" in tb.van_ban

        # Hồ sơ phải hiện trong lịch sử của đúng con vật đó, ghi theo giờ buổi chăm sóc
        # chứ không phải giờ ngồi gõ.
        tb.bam("Miu")
        assert "Da sạch, không phát hiện ve" in tb.van_ban
        assert f"{GIO_DOI:%d/%m/%Y %H:%M}" in tb.van_ban

        # Lịch đã hoàn thành thì lễ tân không còn đổi hay hủy được nữa.
        tb.gui("Đăng xuất")
        tb.gui("Đăng nhập", username=nen_e2e["le_tan"], password=MAT_KHAU_MAU)
        tb.bam("Lịch hẹn")
        assert "Hoàn thành" in tb.van_ban
        assert "Đổi" not in tb.nut and "Hủy" not in tb.nut

        # 7. Lập hóa đơn từ chính dòng lịch vừa hoàn thành.
        tb.gui("Lập hóa đơn")
        assert tb.ma == 200
        assert "/invoices/" in tb.duong_dan
        assert nen_e2e["ten_dich_vu"] in tb.van_ban
        assert "150.000đ" in tb.van_ban
        assert "Chưa thu" in tb.van_ban

        # 8. Khách trả trước một phần. Hình thức chọn theo nhãn nhìn thấy.
        tb.gui("Ghi nhận", so_tien="50000", hinh_thuc="Chuyển khoản")
        assert tb.ma == 200
        assert "Thu một phần" in tb.van_ban
        assert "Còn nợ 100.000đ" in tb.van_ban

        # 9. Trả nốt phần còn lại thì hóa đơn đóng, form thu tiền biến mất.
        tb.gui("Ghi nhận", so_tien="100000", hinh_thuc="Tiền mặt")
        assert tb.ma == 200
        assert "Đã thu đủ" in tb.van_ban
        assert "Ghi nhận" not in tb.nut

        # Và nó phải hiện đúng trạng thái đó ở danh sách hóa đơn.
        tb.bam("Hóa đơn")
        assert "Đã thu đủ" in tb.van_ban
