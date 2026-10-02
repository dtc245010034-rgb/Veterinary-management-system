"""Kiểm tra sống: dựng CSDL MỚI, chạy ứng dụng thật, đi qua mọi chức năng theo từng vai trò.

Chạy:  python tools/kiem_tra_song.py            (cần đã cài requirements.txt, ví dụ qua `python run.py`)
       python tools/kiem_tra_song.py --giu-lai  (không xóa CSDL tạm sau khi chạy, để mở xem tay)

Khác với pytest: pytest dùng CSDL in-memory và TestClient; công cụ này dùng một file SQLite
thật trong thư mục tạm, một tiến trình uvicorn thật và các yêu cầu HTTP thật. Nó KHÔNG đụng
`petcare.db` của bạn và KHÔNG gọi Gemini (ép AI_PROVIDER=fake). Mỗi lần chạy dựng lại từ đầu
nên kết quả không phụ thuộc lần trước. Thoát 0 nếu mọi kiểm tra đạt, 1 nếu còn lỗi.

Kiểm tra bằng HTTP không thay được smoke bấm tay trên trình duyệt (layout, nút bấm, thông báo
hiện đúng chỗ) — xem docs/testing/smoke-checklist.md.
"""

import os
import re
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import datetime as dt
from pathlib import Path

import httpx2 as httpx

GOC = Path(__file__).resolve().parent.parent


def _cong_trong() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _dung_va_chay() -> int:
    """Chế độ điều phối: dựng CSDL tạm + server, chạy lại chính file này ở chế độ kịch bản."""
    giu_lai = "--giu-lai" in sys.argv
    thu_muc = Path(tempfile.mkdtemp(prefix="petcare-song-"))
    db_file = thu_muc / "moi.db"
    cong = _cong_trong()
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_file.as_posix()}",
        "AI_PROVIDER": "fake",
        "GEMINI_API_KEY": "",
        "SECRET_KEY": secrets.token_urlsafe(32),
        "SESSION_HTTPS_ONLY": "false",
        "APP_ORIGIN": "",
        "SEED_MAT_KHAU": "",
    }
    print(f"CSDL tạm: {db_file}\nCổng: {cong}")
    server = None
    try:
        subprocess.run([sys.executable, "-m", "app.seed"], cwd=GOC, env=env, check=True, capture_output=True)
        log = open(thu_muc / "server.log", "w", encoding="utf-8")
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(cong)],
            cwd=GOC, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        for _ in range(60):
            try:
                if httpx.get(f"http://127.0.0.1:{cong}/login", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        else:
            print("Server không lên được, xem", thu_muc / "server.log")
            return 2
        ma = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--kich-ban", f"http://127.0.0.1:{cong}", str(db_file)],
            cwd=GOC, env=env,
        ).returncode
        loi_500 = len(re.findall(r'" 500 ', (thu_muc / "server.log").read_text(encoding="utf-8", errors="replace")))
        print(f"Số phản hồi 500 trong log server: {loi_500}")
        return 1 if loi_500 else ma
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=10)
        if giu_lai:
            print("Giữ lại:", thu_muc)
        else:
            shutil.rmtree(thu_muc, ignore_errors=True)


if "--kich-ban" not in sys.argv:
    sys.exit(_dung_va_chay())

BASE = sys.argv[sys.argv.index("--kich-ban") + 1]
DB = sys.argv[sys.argv.index("--kich-ban") + 2]
KQ = []

def db(sql, *a):
    c = sqlite3.connect(DB); r = c.execute(sql, a).fetchall(); c.close(); return r

def phien(user, pw="matkhau123"):
    c = httpx.Client(base_url=BASE, follow_redirects=False, timeout=20)
    r = c.post("/login", data={"username": user, "password": pw})
    assert r.status_code == 303, (user, r.status_code, r.text[:200])
    return c

def ck(ten, ok, chi_tiet=""):
    KQ.append((ten, bool(ok), chi_tiet))
    print(("PASS " if ok else "FAIL ") + ten + ("" if ok else f"  <-- {chi_tiet}"))

def st(r): return r.status_code
def txt(r): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))

# ---------- A. Đăng nhập / phân quyền ----------
anon = httpx.Client(base_url=BASE, follow_redirects=False)
for p in ["/", "/owners", "/appointments", "/invoices", "/users", "/services", "/stats", "/ai/hoi-dap"]:
    r = anon.get(p)
    ck(f"A1 chưa đăng nhập GET {p} -> chuyển về /login", st(r) in (302, 303, 307) and "/login" in r.headers.get("location", ""), f"{st(r)} {r.headers.get('location')}")
r = anon.post("/login", data={"username": "quanly", "password": "sai"})
ck("A2 sai mật khẩu -> 401, không lộ tài khoản có tồn tại", st(r) == 401 and "không tồn tại" not in r.text.lower(), st(r))
r2 = anon.post("/login", data={"username": "khongco", "password": "sai"})
ck("A3 sai tài khoản và sai mật khẩu cho cùng thông báo", txt(r2).count("không đúng") == txt(r).count("không đúng") and st(r2) == 401, (st(r2),))

ql, lt, c1, c2 = phien("quanly"), phien("letan"), phien("chamsoc1"), phien("chamsoc2")

MA_TRAN = {  # đường dẫn: (quanly, letan, chamsoc)
    "/": (200, 200, 200), "/owners": (200, 200, 200), "/appointments": (200, 200, 303),
    "/appointments/cua-toi": (200, 200, 200),
    "/services": (200, 200, 200), "/invoices": (200, 200, 403), "/vaccinations": (200, 200, 200),
    "/users": (200, 403, 403), "/stats": (200, 403, 403), "/ai/hoi-dap": (200, 200, 200),
    "/ai/quota": (200, 403, 403), "/doi-mat-khau": (200, 200, 200),
}
for p, (a, b, c) in MA_TRAN.items():
    for ten, cl, mong in (("quanly", ql, a), ("letan", lt, b), ("chamsoc1", c1, c)):
        r = cl.get(p)
        ck(f"A4 {ten} GET {p} -> {mong}", st(r) == mong, st(r))

r = ql.get("/")
ck("A5 trang chủ hiện tên người dùng", "Nguyễn Văn Quản" in r.text or "quanly" in r.text)
hd = ql.get("/login").headers
ck("A6 header bảo mật có mặt", hd.get("x-frame-options") and hd.get("x-content-type-options") and hd.get("referrer-policy"), dict(hd))
r = ql.post("/owners", data={"ho_ten": "X", "so_dien_thoai": "0900000001"}, headers={"Origin": "https://evil.example"})
ck("A7 POST từ Origin lạ bị chặn 403", st(r) == 403, st(r))

# ---------- B. Chủ nuôi ----------
r = lt.get("/owners", params={"q": "dau do"})
ck("B1 tìm không dấu 'dau do' ra Đậu Đỏ", "Đậu Đỏ" in r.text or "Trần Quốc Đạt" in r.text, st(r))
r = lt.get("/owners", params={"q": "0912345678"})
ck("B2 tìm theo số điện thoại", "Đỗ Thị Hằng" in r.text)
r = lt.post("/owners", data={"ho_ten": "Hoàng Thị Mai", "so_dien_thoai": "0933111222", "email": "mai@example.com", "dia_chi": "12 Lê Lợi", "ghi_chu": "khách mới"})
ck("B3 lễ tân thêm chủ nuôi -> chuyển hướng", st(r) in (302, 303), (st(r), txt(r)[:200]))
mai = db("select id from owners where phone=?", "0933111222")
ck("B4 chủ nuôi mới có trong CSDL", len(mai) == 1)
mai = mai[0][0] if mai else None
r = lt.post("/owners", data={"ho_ten": "Người Trùng", "so_dien_thoai": "0933111222"})
ck("B5 trùng số điện thoại bị từ chối (không tạo thêm)", st(r) != 303 and len(db("select id from owners where phone=?", "0933111222")) == 1, (st(r), txt(r)[:200]))
r = lt.post("/owners", data={"ho_ten": "", "so_dien_thoai": "0933"})
ck("B6 họ tên trống bị từ chối 4xx", 400 <= st(r) < 500, st(r))
r = lt.post("/owners", data={"ho_ten": "Số Sai", "so_dien_thoai": "abc"})
ck("B7 số điện thoại sai định dạng bị từ chối", 400 <= st(r) < 500 and not db("select 1 from owners where full_name='Số Sai'"), st(r))
r = lt.post(f"/owners/{mai}/sua", data={"ho_ten": "Hoàng Thị Mai B", "so_dien_thoai": "0933111222", "email": "", "dia_chi": "34 Hai Bà Trưng", "ghi_chu": ""})
ck("B8 sửa chủ nuôi", st(r) in (302, 303) and db("select full_name from owners where id=?", mai)[0][0] == "Hoàng Thị Mai B", st(r))
r = c1.get(f"/owners/{mai}")
ck("B9 caretaker xem được chi tiết chủ nuôi", st(r) == 200)
r = c1.post("/owners", data={"ho_ten": "Cấm", "so_dien_thoai": "0911000000"})
ck("B10 caretaker không được thêm chủ nuôi (403)", st(r) == 403, st(r))

# ---------- C. Thú cưng ----------
r = lt.post(f"/owners/{mai}/pets", data={"ten": "Kem", "loai": "Chó", "giong": "Phú Quốc", "gioi_tinh": "Đực", "ngay_sinh": "2022-03-04", "can_nang": "9.5", "ghi_chu": ""})
ck("C1 thêm thú cưng", st(r) in (302, 303), (st(r), txt(r)[:250]))
kem = db("select id from pets where owner_id=? and name='Kem'", mai)
ck("C2 thú cưng có trong CSDL", len(kem) == 1)
kem = kem[0][0] if kem else None
r = lt.post(f"/owners/{mai}/pets", data={"ten": "Tương Lai", "loai": "Chó", "ngay_sinh": "2999-01-01"})
ck("C3 ngày sinh ở tương lai bị từ chối", 400 <= st(r) < 500 and not db("select 1 from pets where name='Tương Lai'"), st(r))
r = lt.post(f"/owners/{mai}/pets", data={"ten": "Nặng", "loai": "Chó", "can_nang": "-3"})
ck("C4 cân nặng âm bị từ chối", 400 <= st(r) < 500 and not db("select 1 from pets where name='Nặng'"), st(r))
r = lt.post(f"/pets/{kem}/sua", data={"ten": "Kem Sữa", "loai": "Chó", "giong": "Phú Quốc", "gioi_tinh": "Đực", "ngay_sinh": "2022-03-04", "can_nang": "10", "ghi_chu": "hiền"})
ck("C5 sửa thú cưng", st(r) in (302, 303) and db("select name from pets where id=?", kem)[0][0] == "Kem Sữa", st(r))
r = c1.get(f"/pets/{kem}")
ck("C6 thú cưng chưa có hồ sơ: có mục Lịch sử, chưa có nút Tóm tắt AI", st(r) == 200 and "Lịch sử chăm sóc" in r.text and "Tóm tắt bằng AI" not in r.text)

# ---------- D. Dịch vụ & gói (quản lý) ----------
r = ql.post("/services", data={"ma": "NHUOM", "ten": "Nhuộm lông", "gia": "300000", "thoi_luong_phut": "60", "mo_ta": "thử"})
ck("D1 quản lý thêm dịch vụ", st(r) in (302, 303), (st(r), txt(r)[:200]))
dv = db("select id from services where code='NHUOM'")
dv = dv[0][0] if dv else None
r = ql.post("/services", data={"ma": "NHUOM", "ten": "Trùng mã", "gia": "1000", "thoi_luong_phut": "10", "mo_ta": ""})
ck("D2 trùng mã dịch vụ bị từ chối", st(r) != 303 and len(db("select 1 from services where code='NHUOM'")) == 1, st(r))
r = ql.post("/services", data={"ma": "AM", "ten": "Giá âm", "gia": "-5", "thoi_luong_phut": "10", "mo_ta": ""})
ck("D3 giá âm bị từ chối", st(r) != 303 and not db("select 1 from services where code='AM'"), st(r))
r = ql.post(f"/services/{dv}/sua", data={"ten": "Nhuộm lông màu", "gia": "350000", "thoi_luong_phut": "75", "mo_ta": "x"})
ck("D4 sửa dịch vụ", st(r) in (302, 303) and db("select price from services where id=?", dv)[0][0] in (350000, "350000", 350000.0), db("select price from services where id=?", dv))
r = lt.post("/services", data={"ma": "CAM", "ten": "Cấm", "gia": "1", "thoi_luong_phut": "10", "mo_ta": ""})
ck("D5 lễ tân không được thêm dịch vụ (403)", st(r) == 403, st(r))
r = ql.post(f"/services/{dv}/ngung-ban")
ck("D6 ngừng bán dịch vụ", st(r) in (302, 303) and db("select is_active from services where id=?", dv)[0][0] == 0, st(r))
r = ql.post(f"/services/{dv}/ban-lai")
ck("D7 bán lại dịch vụ", db("select is_active from services where id=?", dv)[0][0] == 1)
tam, mong_ = db("select id from services where code='TAM'")[0][0], db("select id from services where code='CATMONG'")[0][0]
r = ql.post("/services/goi", data={"ten": "Gói thử", "gia": "180000", "dich_vu_id": [str(tam), str(mong_)], "so_luong": ["1", "2"]})
ck("D8 tạo gói dịch vụ", st(r) in (302, 303) and db("select 1 from service_packages where name='Gói thử'"), (st(r), txt(r)[:300]))
goi = db("select id from service_packages where name='Gói thử'")
if goi:
    ck("D9 ngừng bán gói", st(ql.post(f"/services/goi/{goi[0][0]}/ngung-ban")) in (302, 303) and db("select is_active from service_packages where id=?", goi[0][0])[0][0] == 0)
    ck("D10 bán lại gói", st(ql.post(f"/services/goi/{goi[0][0]}/ban-lai")) in (302, 303) and db("select is_active from service_packages where id=?", goi[0][0])[0][0] == 1)

# ---------- E. Lịch hẹn ----------
ngay = (dt.date.today() + dt.timedelta(days=3)).isoformat()
nv = db("select id from users where username='chamsoc1'")[0][0]
nv2 = db("select id from users where username='chamsoc2'")[0][0]
def dat(cl, gio, ngay=ngay, dv=tam, nv=nv, pet=kem):
    return cl.post("/appointments", data={"thu_cung_id": pet, "dich_vu_id": dv, "nhan_vien_id": nv, "ngay": ngay, "gio": gio, "ghi_chu": ""})
r = dat(lt, "09:00")
ck("E1 lễ tân đặt lịch trong giờ mở cửa", st(r) in (302, 303), (st(r), txt(r)[:300]))
lich = db("select id from appointments where pet_id=? order by id desc limit 1", kem)
lich = lich[0][0] if lich else None
r = dat(lt, "09:30")
ck("E2 đặt chồng giờ cùng nhân viên bị từ chối", st(r) != 303 and len(db("select 1 from appointments where pet_id=?", kem)) == 1, (st(r), txt(r)[:200]))
muc = db("select id from pets where name='Mực'")[0][0]
r = dat(lt, "09:30", nv=nv2, pet=kem)
ck("E3a cùng thú cưng đã có lịch giờ đó (nhân viên khác) bị từ chối", st(r) != 303, st(r))
r = dat(lt, "09:30", nv=nv2, pet=muc)
ck("E3 cùng giờ, khác nhân viên, khác thú cưng thì được", st(r) in (302, 303), (st(r), txt(r)[:200]))
r = dat(lt, "07:00", nv=nv2)
ck("E4 đặt trước giờ mở cửa (07:00) bị từ chối", st(r) != 303, st(r))
r = dat(lt, "17:45", nv=nv2)
ck("E5 đặt vượt giờ đóng cửa (17:45 + 45 phút) bị từ chối", st(r) != 303, st(r))
r = dat(lt, "10:00", ngay=(dt.date.today() - dt.timedelta(days=2)).isoformat(), nv=nv2)
ck("E6 đặt vào ngày quá khứ bị từ chối", st(r) != 303, st(r))
r = dat(lt, "ab:cd", nv=nv2)
ck("E7 giờ sai định dạng bị từ chối 4xx", 400 <= st(r) < 500, st(r))
r = lt.get("/appointments", params={"ngay": ngay})
ck("E8 lưới lịch hiện lịch vừa đặt", st(r) == 200 and "Kem" in r.text)
r = lt.post(f"/appointments/{lich}/doi", data={"ngay": ngay, "gio": "11:00", "nhan_vien_id": nv})
ck("E9 đổi giờ lịch", st(r) in (302, 303) and "11:00" in db("select start_at from appointments where id=?", lich)[0][0], (st(r), db("select start_at,status from appointments where id=?", lich)))
r = c1.get("/appointments/cua-toi", params={"ngay": ngay})
ck("E10 caretaker thấy lịch của mình", st(r) == 200 and "Kem" in r.text)
qk = db("select id from appointments where status='booked' and start_at < ? order by id", dt.datetime.now().isoformat(sep=" "))[0][0]
dd_pet = db("select pet_id from appointments where id=?", qk)[0][0]
r = c2.post(f"/appointments/{qk}/ho-so", data={"tinh_trang": "x", "viec_da_lam": "y", "dan_do": ""})
ck("E11 caretaker khác không ghi hồ sơ lịch của người khác (bị chặn, không tạo hồ sơ)", st(r) in (400, 403, 404) and not db("select 1 from care_records where appointment_id=?", qk), st(r))
r = c1.post(f"/appointments/{qk}/ho-so", data={"tinh_trang": "Lông rối, da bình thường", "viec_da_lam": "Tắm, sấy, chải", "dan_do": "Tắm lại sau 2 tuần"})
ck("E12 caretaker ghi hồ sơ -> lịch chuyển 'done'", st(r) in (302, 303) and db("select status from appointments where id=?", qk)[0][0] == "done", (st(r), txt(r)[:250], db("select status from appointments where id=?", qk)))
r = lt.post(f"/appointments/{qk}/huy", data={"ngay": ngay, "ly_do": "thử"})
ck("E12b sau khi có hồ sơ, trang thú cưng hiện hồ sơ và nút Tóm tắt AI", "Tóm tắt bằng AI" in c1.get(f"/pets/{dd_pet}").text and "Tắm, sấy, chải" in c1.get(f"/pets/{dd_pet}").text)
ck("E13 không hủy được lịch đã hoàn thành", db("select status from appointments where id=?", qk)[0][0] == "done", st(r))
# lịch để hủy
r = dat(lt, "14:00", dv=mong_, nv=nv2)
l2 = db("select id from appointments where pet_id=? order by id desc limit 1", kem)[0][0]
r = lt.post(f"/appointments/{l2}/huy", data={"ngay": ngay, "ly_do": "khách bận"})
ck("E14 hủy lịch có lý do", st(r) in (302, 303) and db("select status from appointments where id=?", l2)[0][0] == "cancelled", st(r))
r = lt.post(f"/appointments/{l2}/doi", data={"ngay": ngay, "gio": "15:00", "nhan_vien_id": nv2})
ck("E15 không đổi được lịch đã hủy", db("select status from appointments where id=?", l2)[0][0] == "cancelled", st(r))
r = dat(lt, "14:00", dv=mong_, nv=nv2)
ck("E16 giờ của lịch đã hủy được giải phóng", st(r) in (302, 303), st(r))

# ---------- F. Hóa đơn ----------
r = lt.post(f"/appointments/{qk}/hoa-don", data={"ngay": ngay})
hd_ = db("select id,total_amount from invoices order by id desc limit 1")
ck("F1 lập hóa đơn từ lịch đã hoàn thành", st(r) in (302, 303) and len(db("select 1 from invoices")) == 3, (st(r), txt(r)[:250]))
hd_id, tong = hd_[0]
r = lt.post(f"/appointments/{qk}/hoa-don", data={"ngay": ngay})
ck("F2 không lập hóa đơn lần hai cho cùng lịch", len(db("select 1 from invoices")) == 3, st(r))
r = lt.get(f"/invoices/{hd_id}")
ck("F3 xem chi tiết hóa đơn", st(r) == 200 and "Tắm" in r.text)
r = lt.post(f"/invoices/{hd_id}/thanh-toan", data={"so_tien": "50000", "hinh_thuc": "cash"})
ck("F4 thu một phần -> còn nợ", st(r) in (302, 303) and db("select status from invoices where id=?", hd_id)[0][0] in ("partial", "partially_paid", "unpaid"), db("select status from invoices where id=?", hd_id))
r = lt.post(f"/invoices/{hd_id}/thanh-toan", data={"so_tien": "99999999", "hinh_thuc": "cash"})
ck("F5 thu vượt số còn nợ bị từ chối", 400 <= st(r) < 500, st(r))
r = lt.post(f"/invoices/{hd_id}/thanh-toan", data={"so_tien": "abc", "hinh_thuc": "cash"})
ck("F6 số tiền không phải số bị từ chối", 400 <= st(r) < 500, st(r))
r = lt.post(f"/invoices/{hd_id}/thanh-toan", data={"so_tien": str(int(tong) - 50000), "hinh_thuc": "transfer"})
ck("F7 thu nốt -> đã thanh toán", db("select status from invoices where id=?", hd_id)[0][0] == "paid", db("select status from invoices where id=?", hd_id))
r = lt.post(f"/invoices/{hd_id}/thanh-toan", data={"so_tien": "1000", "hinh_thuc": "cash"})
ck("F8 hóa đơn đã trả đủ không thu thêm được", 400 <= st(r) < 500, st(r))
ck("F9 trang hủy hóa đơn mở được", st(lt.get(f"/invoices/{hd_id}/huy")) == 200)
r = c1.get("/invoices")
ck("F10 caretaker không xem được danh sách hóa đơn", st(r) == 403)
r = ql.get("/invoices")
ck("F11 danh sách hóa đơn mở được", st(r) == 200)

# ---------- G. Tiêm phòng ----------
today = dt.date.today()
r = c1.post(f"/pets/{kem}/vaccinations", data={"ten_vac_xin": "Dại", "so_mui": "1", "ngay_tiem": (today - dt.timedelta(days=350)).isoformat(), "han_nhac": (today + dt.timedelta(days=5)).isoformat(), "ghi_chu": ""})
ck("G1 ghi mũi tiêm có hạn nhắc sắp tới", st(r) in (302, 303), (st(r), txt(r)[:250]))
r = lt.get("/vaccinations")
ck("G2 mũi sắp đến hạn hiện ở trang nhắc tiêm", st(r) == 200 and "Kem" in r.text)
r = c1.post(f"/pets/{kem}/vaccinations", data={"ten_vac_xin": "Dại", "so_mui": "1", "ngay_tiem": today.isoformat(), "han_nhac": (today - dt.timedelta(days=1)).isoformat()})
ck("G3 hạn nhắc trước ngày tiêm bị từ chối", 400 <= st(r) < 500, st(r))
r = c1.post(f"/pets/{kem}/vaccinations", data={"ten_vac_xin": "", "so_mui": "1", "ngay_tiem": today.isoformat()})
ck("G4 thiếu tên vắc-xin bị từ chối", 400 <= st(r) < 500, st(r))

# ---------- H. Tài khoản (quản lý) ----------
r = ql.post("/users", data={"username": "nhanvien9", "full_name": "Nhân Viên Chín", "role": "caretaker", "password": "matkhau999"})
ck("H1 quản lý tạo tài khoản", st(r) in (302, 303) and db("select 1 from users where username='nhanvien9'"), (st(r), txt(r)[:250]))
uid = db("select id from users where username='nhanvien9'")
uid = uid[0][0] if uid else None
r = ql.post("/users", data={"username": "nhanvien9", "full_name": "Trùng", "role": "caretaker", "password": "matkhau999"})
ck("H2 trùng tên đăng nhập bị từ chối", st(r) != 303 and len(db("select 1 from users where username='nhanvien9'")) == 1, st(r))
r = ql.post("/users", data={"username": "yeu", "full_name": "Yếu", "role": "caretaker", "password": "123"})
ck("H3 mật khẩu yếu bị từ chối", st(r) != 303 and not db("select 1 from users where username='yeu'"), st(r))
r = ql.post("/users", data={"username": "saivt", "full_name": "Sai VT", "role": "admin", "password": "matkhau999"})
ck("H4 vai trò không hợp lệ bị từ chối", st(r) != 303 and not db("select 1 from users where username='saivt'"), st(r))
r = ql.post(f"/users/{uid}/sua", data={"full_name": "Nhân Viên Chín B", "role": "receptionist"})
ck("H5 sửa họ tên và vai trò", db("select role from users where id=?", uid)[0][0] == "receptionist", st(r))
r = ql.post(f"/users/{uid}/dat-lai-mat-khau", data={"mat_khau_moi": "matkhau777"})
ck("H6 đặt lại mật khẩu", st(r) in (302, 303), st(r))
n9 = httpx.Client(base_url=BASE, follow_redirects=False)
ck("H7 đăng nhập bằng mật khẩu cũ thất bại", st(n9.post("/login", data={"username": "nhanvien9", "password": "matkhau999"})) == 401)
ck("H8 đăng nhập bằng mật khẩu mới được", st(n9.post("/login", data={"username": "nhanvien9", "password": "matkhau777"})) == 303)
r = ql.post(f"/users/{uid}/khoa")
ck("H9 khóa tài khoản", st(r) in (302, 303) and db("select is_active from users where id=?", uid)[0][0] == 0, st(r))
ck("H10 phiên đang mở của tài khoản bị khóa mất hiệu lực", st(n9.get("/owners")) in (302, 303, 401, 403), st(n9.get("/owners")))
r = httpx.Client(base_url=BASE).post("/login", data={"username": "nhanvien9", "password": "matkhau777"})
ck("H11 tài khoản bị khóa không đăng nhập được", st(r) in (401, 403) and "ngưng" in txt(r).lower(), (st(r), txt(r)[-200:]))
r = ql.post(f"/users/{uid}/mo-khoa")
ck("H12 mở khóa", db("select is_active from users where id=?", uid)[0][0] == 1)
qid = db("select id from users where username='quanly'")[0][0]
r = ql.post(f"/users/{qid}/khoa")
ck("H13 quản lý không tự khóa chính mình", db("select is_active from users where id=?", qid)[0][0] == 1, st(r))

# ---------- I. Đổi mật khẩu / đăng xuất ----------
p = phien("nhanvien9", "matkhau777")
r = p.post("/doi-mat-khau", data={"mat_khau_cu": "sai", "mat_khau_moi": "matkhau555", "nhap_lai": "matkhau555"})
ck("I1 đổi mật khẩu với mật khẩu cũ sai bị từ chối", 400 <= st(r) < 500, st(r))
r = p.post("/doi-mat-khau", data={"mat_khau_cu": "matkhau777", "mat_khau_moi": "matkhau555", "nhap_lai": "khac"})
ck("I2 nhập lại không khớp bị từ chối", 400 <= st(r) < 500, st(r))
r = p.post("/doi-mat-khau", data={"mat_khau_cu": "matkhau777", "mat_khau_moi": "matkhau555", "nhap_lai": "matkhau555"})
ck("I3 đổi mật khẩu thành công", st(r) in (200, 302, 303), st(r))
ck("I4 đăng nhập bằng mật khẩu mới", st(httpx.Client(base_url=BASE).post("/login", data={"username": "nhanvien9", "password": "matkhau555"})) == 303)
q2 = phien("nhanvien9", "matkhau555")
q3 = phien("nhanvien9", "matkhau555")
q2.post("/logout")
ck("I5 đăng xuất xong không còn vào được", st(q2.get("/owners")) in (302, 303))
ck("I6 đăng xuất thu hồi cả phiên ở thiết bị khác", st(q3.get("/owners")) in (302, 303, 401), st(q3.get("/owners")))

# ---------- J. Xóa chủ nuôi / thú cưng ----------
r = lt.post(f"/owners/{mai}/xoa", data={})
ck("J1 chủ nuôi còn thú cưng/lịch -> không xóa được (không lỗi 500)", st(r) != 500 and db("select 1 from owners where id=?", mai), st(r))
r = lt.post(f"/pets/{kem}/xoa", data={})
ck("J2 thú cưng còn lịch/tiêm -> không xóa được (không lỗi 500)", st(r) != 500 and db("select 1 from pets where id=?", kem), st(r))
lt.post("/owners", data={"ho_ten": "Để Xóa", "so_dien_thoai": "0944555666"})
xo = db("select id from owners where phone='0944555666'")[0][0]
ck("J3 trang xác nhận xóa mở được", st(lt.get(f"/owners/{xo}/xoa")) == 200)
r = lt.post(f"/owners/{xo}/xoa", data={})
ck("J4 xóa chủ nuôi không ràng buộc", st(r) in (302, 303) and not db("select 1 from owners where id=?", xo), st(r))
ck("J5 xem chủ nuôi đã xóa -> 404", st(lt.get(f"/owners/{xo}")) == 404)
ck("J6 id không tồn tại / không phải số không gây 500", st(lt.get("/owners/99999")) == 404 and st(lt.get("/owners/abc")) in (404, 422))

# ---------- K. Thống kê ----------
r = ql.get("/stats")
ck("K1 thống kê hiện số liệu", st(r) == 200 and "Doanh thu" in r.text, st(r))
for kh in ("?tu=2026-01-01&den=2026-12-31", "?tu=2026-12-31&den=2026-01-01", "?tu=abc"):
    r = ql.get("/stats" + kh)
    ck(f"K2 /stats{kh} không lỗi 500", st(r) != 500, st(r))

# ---------- L. AI (fake provider) ----------
r = lt.post(f"/ai/nhac-lich/lich-hen/{lich}", data={"tu": "/appointments"})
ck("L1 soạn tin nhắc lịch hẹn", st(r) in (302, 303) and "/ai/ket-qua/" in r.headers.get("location", ""), (st(r), txt(r)[:250]))
loc = r.headers.get("location", "")
r = lt.get(loc)
ck("L2 trang kết quả AI có dòng khuyến cáo", st(r) == 200 and ("bác sĩ thú y" in r.text or "tham khảo" in r.text), st(r))
log_id = re.search(r"/ai/ket-qua/(\d+)", loc)
if log_id:
    r = lt.post(f"/ai/ket-qua/{log_id.group(1)}/chot", data={"noi_dung": "Chào chị, mai bé Kem có lịch tắm lúc 11:00 ạ.", "tu": "/appointments"})
    ck("L3 chốt tin nhắn sau khi sửa", st(r) in (200, 302, 303), st(r))
vm = db("select id from vaccinations order by id desc limit 1")[0][0]
r = lt.post(f"/ai/nhac-lich/tiem/{vm}", data={"tu": "/vaccinations"})
ck("L4 soạn tin nhắc tiêm", st(r) in (302, 303), (st(r), txt(r)[:200]))
r = c1.post(f"/ai/tom-tat/{dd_pet}", data={"tu": f"/pets/{dd_pet}"})
ck("L5 tóm tắt hồ sơ chăm sóc", st(r) in (302, 303), (st(r), txt(r)[:200]))
r = lt.post("/ai/hoi-dap", data={"cau_hoi": "Bao lâu nên tắm cho chó một lần?"})
ck("L6 hỏi đáp chăm sóc thường ngày", st(r) in (200, 302, 303), st(r))
r = lt.post("/ai/hoi-dap", data={"cau_hoi": "Cho chó uống thuốc gì và liều bao nhiêu mg khi bị nôn?"})
body = r.text if st(r) == 200 else lt.get(r.headers.get("location", "/")).text
ck("L7 câu xin thuốc/liều bị chặn, khuyên gặp bác sĩ thú y", "bác sĩ thú y" in body.lower(), (st(r), txt(r)[:300]))
r = lt.post("/ai/hoi-dap", data={"cau_hoi": ""})
ck("L8 câu hỏi trống bị từ chối", 400 <= st(r) < 500, st(r))
r = lt.post("/ai/hoi-dap", data={"cau_hoi": "x" * 5000})
ck("L9 câu hỏi quá dài không gây 500", st(r) != 500, st(r))
r = ql.get("/ai/quota")
ck("L10 quản lý xem bảng lượt AI", st(r) == 200)
ck("L11 mọi prompt đã lưu không chứa SĐT/email chủ nuôi", not any(re.search(r"0912345678|0933111222|mai@example\.com", str(row)) for row in db("select * from ai_logs")), "")

# ---------- M. Chống dò mật khẩu (R-1) ----------
dd = httpx.Client(base_url=BASE)
res = [st(dd.post("/login", data={"username": "chamsoc2", "password": "sai"})) for _ in range(8)]
r = dd.post("/login", data={"username": "chamsoc2", "password": "matkhau123"})
ck("M1 nhiều lần sai liên tiếp -> bị làm chậm (429), kể cả khi lần sau đúng", 429 in res or st(r) == 429, (res, st(r)))
ck("M2 người khác (tài khoản khác) không bị vạ lây", st(httpx.Client(base_url=BASE).post("/login", data={"username": "letan", "password": "matkhau123"})) == 303)

tong = len(KQ); dat_ = sum(1 for k in KQ if k[1])
print(f"\nTỔNG: {dat_}/{tong} đạt, {tong - dat_} lỗi")
sys.exit(0 if dat_ == tong else 1)
