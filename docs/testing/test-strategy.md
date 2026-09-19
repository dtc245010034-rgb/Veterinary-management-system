# Chiến lược kiểm thử

Yêu cầu: [`../user-stories.md`](../user-stories.md) · Kiến trúc: [`../architecture.md`](../architecture.md) · Ma trận: [`test-cases.md`](test-cases.md)

Đề bài yêu cầu *"có test cho lịch hẹn, hóa đơn, hồ sơ và AI"*. File này định nghĩa cách tổ chức để
yêu cầu đó được đáp ứng thật, không phải chỉ có file test tồn tại.

---

## 1. Bốn tầng, bốn tần suất

Chi phí mỗi tầng rất khác nhau. Bắt chạy đủ bốn tầng ở mọi thời điểm sẽ làm vòng lặp chậm tới mức
bị bỏ qua — và một hệ thống test bị bỏ qua thì bằng không có.

| Tầng | Phạm vi | Chạy khi nào | Ngân sách | Lệnh |
|---|---|---|---|---|
| **Unit** | Hàm trong `app/services/` và `app/ai/`. Không HTTP, DB in-memory hoặc không DB | Mỗi lần sửa code | < 40s | `pytest tests/unit` |
| **Integration** | Router + DB in-memory qua `TestClient`. Có phân quyền, có validation | Cuối mỗi phiên làm việc | < 60s | `pytest tests/integration` |
| **Regression** | Chạy lại **toàn bộ** suite | Trước mỗi commit | < 100s | `pytest` |
| **Hệ thống hoàn chỉnh** | `tests/e2e/test_full_flow.py` + [`smoke-checklist.md`](smoke-checklist.md) bấm tay | Cuối mỗi phase P1–P8 | vài phút | `pytest tests/e2e` |

> **Ngân sách nới ngày 13/09 cho khớp thực đo** — người dùng chốt. Ba con số cũ (15s / 30s / 60s)
> đặt từ P0 khi suite mới có vài chục test; tới P6 là 516 test thì cả ba đều vượt, và một ngân sách
> luôn vượt thì không ai còn nhìn nó nữa.
>
> **Nới lần hai ngày 18/09**, cùng lý do: P7 thêm 134 test (tầng AI), suite đi từ 522 lên 671 ca nên
> hai ngân sách cũ vượt ngay cả khi máy rảnh. Thực đo 18/09: unit 457 ca **32,3s**, integration 213 ca
> **48,3s**, e2e **6,4s**, toàn bộ **73,7s**. Vẫn không có test nào đáng cắt.
>
> **Thực đo 19/09** (chưa nới lần ba — chờ người dùng quyết): unit 463–467 ca **30,6s – 40,2s**,
> integration 213–258 ca **52,2s – 61,1s**, e2e **6,0s – 17,5s**, toàn bộ 726 ca **81s – 95s**. Dao
> động lớn theo tải máy trong cùng một ngày.
>
> **Bài học của lượt rà soát 19/09:** 677 test xanh vẫn lọt ba lỗi cao — hai request **đồng thời**,
> **id không tồn tại** ở một số router, **ngày sai định dạng** khi đổi lịch. Ba dạng này nay có test
> riêng (TC-113 → TC-115); bộ test xanh không thay được lượt rà bằng trình duyệt.
>
> Thực đo 11–13/09: unit 336 ca **21,5s – 26,9s** tùy tải máy; integration 179 ca **34,7s – 42,7s**;
> toàn bộ **57s – 72s**. Không có test nào đáng cắt: chậm nhất 1,03s (test hook), còn lại dưới 0,3s.
> Gần **một nửa** thời gian tầng unit (10,8s / 23s) là fixture `db` dựng CSDL mới bằng `create_all`
> cho **từng** test — đó là cái giá của việc mỗi test hoàn toàn cô lập, và là thứ đã bắt được nhiều
> lỗi rò trạng thái giữa các test. Hướng còn lại (dựng schema một lần mỗi phiên + rollback từng
> test, ước giảm 8–9s) **cố ý không làm**: nó sửa đúng chỗ cả 516 test đi qua, ngay trước P7 là
> phase khó nhất. Chi tiết đo: [`reports/2026-09-11-P6.md`](reports/2026-09-11-P6.md) mục 8.
>
> **Ngân sách này là mốc xem lại, không phải mốc chặn.** Vượt thì đo và tìm nguyên nhân, không cắt
> test để lấy màu xanh.

**"Test hồi quy" không phải một loại test cần viết riêng.** Nó là việc chạy lại toàn bộ suite cũ sau
khi thêm code mới. Hiểu như vậy thì không phải nuôi hai bộ test song song — mọi test đã viết đều tự
động trở thành test hồi quy từ ngày hôm sau.

---

## 2. Cấu trúc thư mục test

Cây dưới đây chỉ nêu các file chính; danh sách đầy đủ, luôn khớp file thật, nằm ở
[`../codebase-map.md`](../codebase-map.md).

```
tests/
├── conftest.py                fixture dùng chung: db in-memory, client,
│                              tài khoản mẫu, FakeProvider, clock cố định
├── unit/
│   ├── test_architecture.py   canh ranh giới dự án — xem mục 3b
│   ├── test_models_*.py       ràng buộc CSDL từng bảng
│   ├── test_*_service.py      nghiệp vụ từng mảng: users, owners, catalog,
│   │                          care_records, vaccinations, billing
│   ├── test_scheduling.py     quy tắc trùng lịch, tính end_at, đổi/hủy lịch
│   ├── test_stats_service.py  doanh thu, khách quay lại
│   ├── test_prompts.py        dựng prompt, ba system prompt, chèn DISCLAIMER
│   ├── test_guardrail.py      chặn câu xin thuốc, soát liều lượng, xóa SĐT/email
│   ├── test_ai_service.py     ba tính năng AI ở tầng nghiệp vụ, ghi ai_logs
│   ├── test_ai_quota.py       xoay ca model, ngày quota theo giờ Pacific
│   └── test_gemini.py         đọc phản hồi và phân loại lỗi HTTP (chỉ thay urlopen)
├── integration/
│   ├── test_auth.py           đăng nhập
│   ├── test_users.py          phân quyền, quản lý tài khoản
│   ├── test_owners.py         chủ nuôi, thú cưng, tra cứu
│   ├── test_services.py       dịch vụ, gói dịch vụ
│   ├── test_appointments.py   đặt/đổi/hủy lịch qua HTTP
│   ├── test_care_records.py   ghi hồ sơ chăm sóc
│   ├── test_vaccinations.py   mũi tiêm và danh sách đến hạn
│   ├── test_invoices.py       lập hóa đơn, ghi nhận thanh toán
│   ├── test_stats.py          trang thống kê
│   ├── test_ai.py             ba tính năng AI qua HTTP, phân quyền, Post/Redirect/Get
│   └── test_khong_tim_thay.py mọi đường dẫn theo id gặp bản ghi không tồn tại → 404/400, không 500
└── e2e/
    └── test_full_flow.py      một kịch bản xuyên suốt trên DB file thật
```

### Quy ước đặt tên test

`test_<đối tượng>_<tình huống>_<kỳ vọng>`

```python
def test_dat_lich_trung_nhan_vien_bi_tu_choi(): ...
def test_dat_lich_lien_ke_duoc_chap_nhan(): ...
def test_thanh_toan_vuot_so_phai_tra_bi_tu_choi(): ...
def test_tom_tat_ho_so_prompt_khong_chua_so_dien_thoai(): ...
```

Tên tiếng Việt không dấu ở đây là ngoại lệ có chủ đích so với quy ước "định danh tiếng Anh": khi test
đỏ, dòng tên test chính là thông tin đầu tiên đọc được, và nó cần khớp thẳng với tiêu chí chấp nhận
trong [`../user-stories.md`](../user-stories.md).

---

## 3. Ba luật chống test giả

Rủi ro lớn nhất khi sinh test bằng AI không phải là thiếu test — mà là **thừa test luôn xanh nhưng
không chứng minh điều gì**. Ba luật này nhằm chặn đúng chuyện đó, và cũng có mặt trong
[`../../CLAUDE.md`](../../CLAUDE.md) mục 7 để agent nạp được ở mọi phiên.

### Luật 1 — Không mock chính lớp đang test

Mock chỉ dành cho hai ranh giới ngoài: **API Gemini** (thay bằng `FakeProvider`) và **thời gian hệ
thống** (thay bằng clock cố định). Mọi thứ khác dùng thật, kể cả CSDL — SQLite in-memory nhanh tới
mức không có lý do gì để mock nó.

```python
# Sai: mock đúng thứ đang cần kiểm chứng, test luôn xanh dù logic sai
def test_dat_lich_trung_bi_tu_choi(monkeypatch):
    monkeypatch.setattr(scheduling, "has_conflict", lambda *a: True)
    ...

# Đúng: dựng dữ liệu thật rồi để logic tự chạy
def test_dat_lich_trung_nhan_vien_bi_tu_choi(db, staff, pet, service):
    scheduling.create_appointment(db, pet.id, service.id, staff.id, at("09:00"))
    with pytest.raises(ConflictError):
        scheduling.create_appointment(db, pet.id, service.id, staff.id, at("09:30"))
```

### Luật 2 — Mỗi bug fix phải có test tái hiện được bug

Trình tự bắt buộc: **viết test → chạy, thấy đỏ → sửa code → chạy, thấy xanh.**

Bỏ bước "thấy đỏ" thì không có gì chứng minh test thật sự bắt được bug — rất nhiều test viết sau khi
sửa xong vẫn xanh kể cả khi hoàn nguyên bản sửa. Log phiên phải ghi lại cả hai trạng thái.

### Luật 3 — Test AI phải assert nội dung thật

```python
# Sai: xanh kể cả khi guardrail bị gỡ hoàn toàn
def test_ai_qa():
    resp = client.post("/ai/qa", json={"question": "cho mèo uống paracetamol mấy viên"})
    assert resp.status_code == 200

# Đúng: assert đúng điều guardrail phải bảo đảm
def test_qa_xin_lieu_thuoc_khong_tra_ve_lieu_luong():
    resp = client.post("/ai/qa", json={"question": "cho mèo uống paracetamol mấy viên"})
    body = resp.json()["answer"]
    assert DISCLAIMER in body
    assert not re.search(r"\d+\s*(mg|ml|viên)", body, re.IGNORECASE)
```

---

## 3b. Test canh ranh giới — `tests/unit/test_architecture.py`

Một nhóm test đặc biệt: chúng **không kiểm chức năng nào cho người dùng**, chúng kiểm chính kỷ luật
của dự án. Router không ghi thẳng xuống CSDL; `services/` không import fastapi; router không gọi
thẳng `app/ai`; link tài liệu không hỏng; `codebase-map.md` không thiếu file; hàm public trong
`services/` không thiếu test gọi thẳng.

Mỗi test sinh ra từ một lỗi **đã thật sự xảy ra**, không phải từ lo xa.

Lý do dùng test thay vì một dòng luật: luật phải được đọc và nhớ mới có tác dụng. Luật "chỉ tick ô
kiểm được thật" được viết ra từ P1 và vẫn bị phạm lại ở P2 rồi P3. Test thì đỏ — một agent hoàn toàn
không biết file này tồn tại, chạy `pytest`, vẫn nhận dòng đỏ.

Đây cũng là chỗ duy nhất trong suite mà **test đỏ có thể vì tài liệu lệch chứ không vì code sai**.
Đó là chủ ý: tiền đề của dự án là tài liệu, test và code đi song song, nên nó xứng đáng có ràng buộc
cứng chứ không chỉ là lời hứa trong CLAUDE.md.

Quy tắc giữ nhóm này còn giá trị: **phép kiểm phải hẹp và chính xác** để đỏ luôn có nghĩa là có gì đó
sai thật. Một lần đỏ giả là cả nhóm mất uy tín và người ta bắt đầu tìm cách tắt nó. Cách phân loại
bài học mới — cái nào thành test, cái nào thành luật — nằm ở [`../../CLAUDE.md`](../../CLAUDE.md)
mục 9.

---

## 4. Hai luật bao phủ — và vì sao không dùng coverage %

- Mỗi hàm public trong `app/services/` có tối thiểu **1 test happy path + 1 test biên**.
- Mọi thay đổi trong `app/ai/` phải kèm test guardrail.

**Không đặt mục tiêu coverage phần trăm.** Chỉ tiêu coverage đo số dòng code được *chạy qua*, không
đo số hành vi được *kiểm chứng*. Đặt mục tiêu 80% thì cách rẻ nhất để đạt là viết test gọi hàm rồi
`assert result is not None` — coverage tăng, chất lượng không đổi. Hai luật đếm được ở trên khó lách
hơn vì chúng nói về *tình huống* chứ không về *dòng code*.

---

## 5. Fixture dùng chung (`tests/conftest.py`)

| Fixture | Nội dung | Vì sao cần |
|---|---|---|
| `db` | `Session` trên SQLite in-memory, tạo bảng mới mỗi test | Test độc lập, chạy thứ tự nào cũng như nhau |
| `client` | `TestClient` với `get_db` override sang `db` | Integration test dùng đúng DB đó |
| `fake_ai` | `FakeProvider` ghi lại mọi `(system, user)` đã nhận | Cho phép assert prompt đã gửi — nền tảng của test US-28 |
| `frozen_clock` | Cố định "bây giờ" ở một mốc | Ca "đặt lịch trong quá khứ", "đến hạn trong 30 ngày" không phụ thuộc ngày chạy |
| `seed_basic` | 1 manager, 1 receptionist, 2 caretaker — **chỉ tài khoản**; chủ nuôi, thú cưng, dịch vụ do từng file test tự dựng | Không phải dựng lại tài khoản ở từng test |

`fake_ai` ghi lại tham số nhận được là chi tiết quan trọng nhất trong bảng này: không có nó thì không
kiểm chứng được prompt sạch dữ liệu cá nhân, và US-28 sẽ chỉ là một dòng chữ trong tài liệu.

---

## 6. Kịch bản e2e xuyên suốt

`tests/e2e/test_full_flow.py` — một test duy nhất, chạy trên **DB file thật** (không in-memory) để
bắt được cả lỗi ở tầng lưu trữ:

1. ✅ Đăng nhập vai trò lễ tân
2. ✅ Tạo chủ nuôi → tạo thú cưng
3. ✅ Đặt lịch chăm sóc
4. ✅ Thử đặt lịch trùng → phải bị từ chối
5. ✅ Đổi lịch sang khung trống → thành công
6. ✅ Đăng nhập vai trò nhân viên chăm sóc → ghi hồ sơ chăm sóc → lịch chuyển `done`
7. ✅ Đăng nhập lễ tân → lập hóa đơn *(P5)*
8. ✅ Ghi nhận thanh toán một phần → trạng thái `partial` *(P5)*
9. ✅ Ghi nhận nốt phần còn lại → trạng thái `paid` *(P5)*
10. ✅ Gọi AI tóm tắt hồ sơ → có nội dung và có `DISCLAIMER`, tải lại trang không gọi AI lần nữa *(P7)*
11. ✅ Đăng nhập quản lý → xem thống kê → doanh thu khớp số đã thu *(P6)*

Một test đi qua gần hết hệ thống, nên nó bắt được lỗi tích hợp mà unit test không thấy: sai thứ tự
trạng thái, session đăng nhập rơi giữa chừng, dữ liệu không commit, phân quyền chặn nhầm.

Đổi lại, khi nó đỏ thì thông tin chẩn đoán kém — nên nó **không thay thế** ba tầng trên, chỉ chạy
cuối mỗi phase.

**Luật riêng của tầng này, thêm ngày 05/09:** kịch bản **chỉ được đi theo link và nút lấy từ HTML
trả về**; địa chỉ gõ tay duy nhất là `/`. Form phải gửi đúng như trình duyệt gửi — đủ mọi trường
`hidden`, và `<select>` không có option nào `selected` thì lấy **option đầu tiên**. Lý do: năm trong
chín lỗi tìm được ngày 05/09 lọt qua toàn bộ test tầng HTTP vì test tự dựng URL và tự dựng `data={}`.
Viết e2e theo kiểu cũ thì nó xanh mà vẫn để lọt đúng những lỗi ấy — đã chứng minh bằng đột biến:
bỏ dấu `selected` ở ô chọn nhân viên làm **e2e đỏ trong khi cả 344 test unit + integration vẫn xanh**.

---

## 7. Ghi nhận kết quả

- **Mỗi phiên làm việc**: kết quả unit + integration ghi vào mục "Kết quả test" của
  `docs/sessions/YYYY-MM-DD-NN.md`. Ghi số thật (`42 passed, 0 failed`), không ghi "test đã chạy ok".
- **Mỗi phase**: dán output đầy đủ của `pytest` và kết quả [`smoke-checklist.md`](smoke-checklist.md)
  vào `reports/YYYY-MM-DD-Pn.md`.
- **Test đỏ chưa sửa được**: ghi rõ trong log phiên ở mục "Còn dở", kèm tên test. Không được xóa hoặc
  `@pytest.mark.skip` để lấy màn hình xanh.

Điều cuối cùng quan trọng hơn vẻ ngoài của nó: một test bị skip lặng lẽ là cách nhanh nhất để hệ
thống test mất giá trị mà không ai nhận ra.

## 8. CI

Chưa dựng. Chạy `pytest` cục bộ là đủ ở giai đoạn này. Cân nhắc lại ở P8 nếu dự án được đẩy lên
GitHub và có nhu cầu gắn badge vào báo cáo.
