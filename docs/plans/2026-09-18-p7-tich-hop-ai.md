# P7 — Tích hợp AI, xoay ca model Gemini và ước tính quota

> **Phase:** P7 · **Mốc:** KT3 · **Duyệt ngày:** 2026-09-18 · **Trạng thái:** chặng 0 và chặng 1 xong 18/09 (smoke chặng 0 còn 6 ô chờ tick), đang mở chặng 2
>
> Thiết kế qua hai vòng brainstorming 17–18/09; người dùng chốt Q1–Q7, duyệt kèm đề xuất Q8–Q10 và bảy
> tối ưu O1–O7. Chia bốn chặng (0–3). Theo [`../roadmap.md`](../roadmap.md).

## Context

P0→P6 xong (521/522 test xanh; test đỏ duy nhất là phép đếm log phiên do 3 file log rỗng hôm nay).
Đề bài mục 3.2 còn 0/3 chức năng AI. Gọi thử khóa thật 17/09:

- `gemini-2.5-flash` (đang ghi trong `config.py`, `.env.example`, `.env`) → **404 "no longer available to new users"**.
- `gemini-3.6-flash` → 200, lúc 33s lúc 6,7s, **tốn 487 token suy nghĩ cho một câu trả lời 35 token**; `gemini-flash-latest` → **503**.
- Free tier khoảng 20 lượt/ngày/model, reset theo **giờ Pacific**.

Người dùng yêu cầu **tự động xoay ca model** + **ước tính quota trong ngày** theo mẫu:

```
MODEL GEMINI
▸ gemini-3.6-flash: 14/~20
▸ gemini-3.5-flash: 2/~20
▸ gemini-3-flash-preview: 1/~20
▸ gemini-3.1-flash-lite: 10/~20 ⬅️ đang dùng
```
Không có `~` = giới hạn thật Google báo (học từ lỗi 429); có `~` = ước tính.

## Bản rà lần 2 tối ưu gì so với bản trước

| # | Bản trước | Bản này | Lợi |
|---|---|---|---|
| O1 | S2: thêm cột `vaccine_key` · S3: đổi UNIQUE thành index một phần → **phải xóa và tạo lại `petcare.db`** | S2: khi ghi mũi, nếu thú cưng đã có vắc-xin trùng tên sau `chuan_hoa` thì **dùng lại đúng tên cũ** · S3: **lập lại tại chỗ** hóa đơn đã hủy (chép lại giá hiện tại, về `unpaid`, `issued_at` = bây giờ) | Chặng 0 **không đổi schema**, không mất dữ liệu đang có, ERD không đổi |
| O2 | Code tự nhận diện triệu chứng rồi nối câu "khuyên đi khám" | **Bỏ bộ nhận diện triệu chứng.** `DISCLAIMER` luôn được nối đã có sẵn câu "…có dấu hiệu bất thường, vui lòng đưa đến cơ sở thú y để được thăm khám" | Bớt một module từ khóa và khả năng chặn nhầm ("mèo **non**" khớp "nôn"); TC-092 vẫn assert được |
| O3 | 20 ca G chạy hết với Gemini thật | **Chỉ G-01→G-13 cần model thật** (13 lượt). G-14→G-20 là việc của code (lọc liên hệ, lỗi hạ tầng, không gọi API) nên đã chứng minh bằng test tự động; chạy tay lại chỉ để xác nhận trên giao diện, **không tốn quota** vì dùng `fake` hoặc ngắt mạng | Tiết kiệm khoảng 35% quota của lượt kiểm thử |
| O4 | Chạy 13 câu liên tiếp → dính giới hạn **theo phút** → hệ thống xoay sang model khác giữa chừng, báo cáo trộn nhiều model | Lệnh `--guardrail` **giãn cách** theo `GEMINI_RPM_UOC_TINH` và có `--model` **ghim một model** (không xoay) | So sánh công bằng từng model; báo cáo không trộn |
| O5 | Chép tay câu hỏi và phản hồi vào báo cáo | `--guardrail` **tự ghi file markdown** (câu hỏi, phản hồi nguyên văn, model, thời gian, bảng quota trước/sau); người chỉ còn đánh đạt/không đạt | Không chép sai; chạy lại cho model khác chỉ một lệnh |
| O6 | Không đụng tới token suy nghĩ | Thử `thinkingLevel: "low"` **đo thật ở chặng 1** (1–2 lượt); chỉ bật nếu giảm độ trễ và câu trả lời G-01/G-08 vẫn đạt. Cấu hình được, mặc định theo kết quả đo | Dự kiến giảm độ trễ rõ rệt; quyết bằng số đo, không đoán |
| O7 | `cooldown_until` lưu CSDL | Giữ trong CSDL (CLI và server là hai tiến trình phải thấy cùng trạng thái), nhưng **đếm lượt bằng một câu `UPDATE … SET request_count = request_count + 1`** | Không lệch đếm khi hai request đồng thời |

## Quyết định đã chốt

| # | Quyết định | Nguồn |
|---|---|---|
| Q1 | Hỏi thuốc/liều → từ chối cố định, **không gọi AI**, vẫn ghi `ai_logs`. Mọi phản hồi qua bộ lọc "số + mg/ml/viên/cc" và luôn nối `DISCLAIMER`. Ngoài phạm vi và triệu chứng → system prompt (+ `DISCLAIMER`, xem O2) | Người dùng 17/09, tinh gọn ở O2 |
| Q2 | Nhắc lịch: ô sửa + nút Sao chép + nút Chốt (hiện đúng bản đã sửa). Không gửi SMS thật | Người dùng 17/09 |
| Q3 | Tóm tắt + hỏi đáp: cả 3 vai trò. Nhắc lịch: `manager`, `receptionist`. Khách không đăng nhập hệ thống | Người dùng 17–18/09 |
| Q4 | Xoay model **ưu tiên theo thứ tự** | Người dùng 18/09 |
| Q5 | Khóa API **riêng** → số tự đếm đáng tin, 429 của Google dùng để hiệu chỉnh | Người dùng 18/09 |
| Q6 | Sửa **S1–S5 trước P7** (chặng 0); S6, S7 ghi vào roadmap P8 | Người dùng 18/09 |
| Q7 | Quota: **CLI + trang riêng cho quản lý** (có nút đặt lại trạng thái) | Người dùng 18/09 |
| Q8 | *Đề xuất:* **không gửi tên chủ nuôi** sang AI — tin nhắn xưng "Quý khách", lễ tân sửa được | Agent |
| Q9 | *Đề xuất:* lọc chuỗi giống SĐT/email trong **mọi văn bản tự do** (ghi chú hồ sơ, ghi chú thú cưng, câu hỏi lễ tân gõ) trước khi dựng prompt và trước khi ghi log | Agent |
| Q10 | *Đề xuất:* system prompt `qa` bỏ "luôn kết thúc bằng lời nhắc…", thay bằng "không tự viết câu khuyến cáo, hệ thống tự thêm" — tránh khuyến cáo lặp. Sửa bảng "3 nơi" trong `ai-safety.md` | Agent |

---

## Chặng 0 — Vá lỗ hổng hệ thống S1–S5 (không đổi schema)

Mỗi lỗi: **test tái hiện đỏ trước → sửa → xanh**, ghi cả hai trạng thái vào log phiên.

| # | Lỗ hổng (đã xác minh trong code) | Cách sửa |
|---|---|---|
| S1 | Thiếu `.env` thì chạy với `SECRET_KEY` mặc định công khai → giả được cookie quản lý (`app/config.py:13`) | `lifespan` trong `app/main.py` từ chối khởi động khi khóa còn là chuỗi mặc định. Test gọi thẳng `lifespan` (bộ test cố ý không chạy lifespan — `conftest.client`) |
| S2 | `den_han()` so tên vắc-xin tuyệt đối: "Dại" vs "dại" → mũi cũ quá hạn mãi | `ghi_mui_tiem` tìm mũi cũ cùng thú cưng có `chuan_hoa(tên)` trùng → dùng lại tên cũ (O1). Dùng lại `services/text.chuan_hoa` |
| S3 | UNIQUE `invoices.appointment_id` → hóa đơn hủy nhầm không lập lại được; lối lách gợi ý (đặt lịch mới) không đặt được vào quá khứ và đếm dôi lượt | `lap_hoa_don` gặp hóa đơn cũ **đã hủy** → lập lại tại chỗ: chép lại tên/giá dịch vụ hiện tại, `unpaid`, `issued_at = clock.now()` (O1). An toàn vì `huy_hoa_don` bảo đảm hóa đơn đã hủy không có thanh toán. Sửa câu gợi ý lối lách |
| S4 | Khóa nhân viên chăm sóc → lịch tương lai kẹt; `doi_lich` giữ nhân viên đã khóa mà không kiểm | `doi_lich` luôn `_kiem_nhan_vien` cho nhân viên đích; trang Tài khoản hiện "còn N lịch chưa làm" cạnh nhân viên đã khóa |
| S5 | Docstring `services/care_records.py:10` hứa "P6 đếm lịch đã qua giờ vẫn booked" — chưa làm | Giữ định nghĩa lượt đã chốt 11/09; thêm `so_lich_qua_gio_chua_ghi` vào `ThongKe` + dòng cảnh báo trên `stats.html`; sửa docstring cho đúng |

- [x] S1 → S5 như bảng, mỗi lỗi một test đỏ-trước
- [x] Ghi S6 (đặt lịch ngoài giờ/qua nửa đêm) và S7 (`_doc_ngay` ngày sai âm thầm thành hôm nay khi POST) vào mục P8 của `roadmap.md`
- [x] Báo cáo `testing/reports/2026-09-18-P7-chang0.md` — 537 test xanh, đột biến đủ 5/5

---

## Chặng 1 — Nền AI + xoay ca model + quota (chưa có giao diện)

### Cấu trúc

```
app/ai/provider.py  Protocol AIProvider.tra_loi(model, system, user, timeout) -> str
                    Lỗi phân loại: LoiQuaTai (503/500/timeout) · LoiHetQuota(theo_ngay, gioi_han, thu_lai_sau)
                    · LoiModelKhongCo (404) · LoiCauHinh (400/401/403 — khóa sai: dừng xoay ngay)
app/ai/gemini.py    Một lần gọi REST generateContent qua urllib (không thêm thư viện HTTP);
                    429: details QuotaFailure.quotaId chứa "PerDay" → theo ngày, quotaValue → giới hạn thật,
                    RetryInfo.retryDelay → thời gian nghỉ; 429 không đọc được chi tiết → coi như theo phút
app/ai/fake.py      FakeProvider: ghi lại mọi (model, system, user); cài phản hồi/lỗi THEO TỪNG MODEL
                    → test toàn bộ luật xoay mà không mock lớp đang test
app/ai/quota.py     ngay_quota() (ngày Pacific từ clock.now() giờ VN) · chon_thu_tu(db) · ghi_ket_qua(db, …)
                    · bang_quota(db) · goi_co_xoay(db, provider, system, user, ghim_model=None)
                    · __main__: CLI
app/ai/prompts.py   DISCLAIMER, 3 system prompt, câu cố định (từ chối thuốc, nhắc xác nhận lịch tiêm),
                    hàm dựng prompt từ dict — thuần, không DB
app/ai/guardrail.py la_cau_xin_thuoc() · chua_lieu_luong() · xoa_lien_he()
app/ai/service.py   lay_provider() (Depends) · nhac_lich_hen · nhac_lich_tiem · tom_tat_ho_so · hoi_dap
                    · bang_quota · dat_lai_model — cửa DUY NHẤT router được import
app/models/ai_log.py    ai_logs theo ERD + cột `model` (NULL = không gửi đi: bị chặn / thiếu dữ liệu)
app/models/ai_quota.py  một dòng mỗi (model, quota_day Pacific): request_count, daily_limit (thật, NULL nếu
                        chưa biết), exhausted, cooldown_until, disabled_reason. UNIQUE(model, quota_day)
```
Hai bảng mới tạo được bằng `create_all` trên CSDL đang có — không cần tạo lại `petcare.db`.

### Luật xoay (Q4)

1. Thứ tự từ `GEMINI_MODELS=gemini-3.6-flash,gemini-3.5-flash,gemini-3-flash-preview,gemini-3.1-flash-lite`.
2. Bỏ qua model: `disabled_reason` (404), `exhausted` hôm nay (429 theo ngày), `cooldown_until` > bây giờ (503/timeout/429 theo phút).
3. Chạm giới hạn **ước tính** (`~20`) → xếp cuối nhưng vẫn thử; chạm giới hạn **thật** → bỏ tới khi reset.
4. **Tổng ngân sách thời gian** mỗi lần bấm `AI_TONG_GIAY=45`; mỗi lần thử `min(AI_MOI_LAN_GIAY=25, còn lại)`.
5. `LoiCauHinh` dừng ngay. Hết model → `LoiAI` "AI đang bận hoặc hết lượt hôm nay, vui lòng thử lại sau".
6. Đếm: mỗi lần thử **tới được server** (thành công, 5xx, timeout) +1 bằng `UPDATE` nguyên tử (O7); 404 và 429 không đếm. 429 theo ngày có `quotaValue` → lưu `daily_limit` thật, dùng tiếp các ngày sau.
7. `ghim_model` (chỉ CLI dùng) → chỉ thử đúng model đó, không xoay (O4).
8. `ai_logs.model` ghi model đã trả lời.

### CLI (Q7, O4, O5)

- `python -m app.ai.quota` → bảng đúng mẫu + "Reset lúc HH:MM giờ VN (00:00 Pacific)". Ép stdout UTF-8 (console cp1252 đã lỗi lúc gọi thử).
- `python -m app.ai.quota --hoi "câu hỏi" [--model X]` → một lượt `hoi_dap` thật: model, câu trả lời, bảng sau lượt.
- `python -m app.ai.quota --guardrail [--model X]` → chạy G-01→G-13 **giãn cách theo `GEMINI_RPM_UOC_TINH`**, ghi `docs/testing/reports/YYYY-MM-DD-P7-gemini-<model>.md` với cột "Đạt?" để trống cho người đánh.

### Vá lỗ hổng của kế hoạch cũ

| Lỗ hổng | Cách vá |
|---|---|
| Windows không có dữ liệu múi giờ: `ZoneInfo('America/Los_Angeles')` ném `ZoneInfoNotFoundError` (đã chạy thử) | Thêm `tzdata` (pin) vào `requirements.txt`; test `ngay_quota` ở ranh giới 14:00 VN (PDT) và 15:00 VN (PST) |
| Đổi `.env` sang `AI_PROVIDER=gemini` để test tay rồi chạy pytest → đốt quota thật | `conftest.py` **gán cứng** `AI_PROVIDER=fake`, `GEMINI_API_KEY=""` trước khi import app |
| "viên" khớp "nhân viên" sau khi bỏ dấu | So **từ nguyên vẹn** trên chuỗi `chuan_hoa`; "viên/mg/ml/cc" chỉ tính khi đứng sau số hoặc "mấy/bao nhiêu"; test âm: "nhân viên", "sữa tắm", "cắt móng" |
| Câu hỏi lễ tân gõ chứa SĐT khách, bị lưu nguyên vào `ai_logs` | `xoa_lien_he()` áp cho câu hỏi trước prompt và log (Q9) |
| Hồ sơ dài → prompt phình | Tóm tắt lấy **20 hồ sơ mới nhất** (`care_records.lich_su` đã sắp mới trước) |
| Nhắc lịch cho lịch đã hủy/đã làm/đã qua, mũi tiêm không có hạn | `LoiNghiepVu`, **không gọi AI** |
| Khuyến cáo lặp hai lần | Q10 |

### Checklist chặng 1

- [x] `config.py`/`.env.example`: `gemini_models`, `gemini_rpd_uoc_tinh=20`, `gemini_rpm_uoc_tinh`, `gemini_thinking_level`, `ai_tong_giay`, `ai_moi_lan_giay`, `ai_nghi_giay=120`; bỏ `gemini_model`. Nhắc người dùng sửa `.env`
- [x] `tzdata` vào `requirements.txt`
- [x] Model `ai_log.py` (+ `model`), `ai_quota.py`; `erd.md` lên 14 bảng; test ràng buộc
- [x] `provider.py`, `fake.py`, `prompts.py`, `guardrail.py`, `quota.py`, `service.py`, `gemini.py`
- [x] Fixture `fake_ai` chạy thật (thay `pytest.skip`), override `lay_provider`
- [x] `tests/unit/test_prompts.py`, `test_guardrail.py`, `test_ai_service.py`: TC-082, 083, 087, 088, 092→098
- [x] `tests/unit/test_ai_quota.py` (TC mới từ TC-103): thứ tự ưu tiên; 503 → nghỉ rồi quay lại model đầu; 429 theo phút vs theo ngày; học `quotaValue`; 404 loại model; khóa sai dừng ngay; hết model → lỗi thân thiện; ngân sách thời gian; ghim model không xoay; ranh giới ngày Pacific hai mùa; model chạm `~` vẫn được thử sau cùng
- [x] `tests/unit/test_gemini.py`: chỉ mock `urllib.request.urlopen`; JSON 200 thật, 429 có/không `QuotaFailure`, 503, timeout, 404, 401
- [x] `test_architecture.py`: bắt cả `import app.ai.x`; mở luật "hàm public có test gọi thẳng" sang `app/ai/`
- [x] **Đột biến có chủ đích** (bài học 3, kiểm cả CRLF): gỡ chặn thuốc / gỡ nối DISCLAIMER / gỡ `xoa_lien_he` / đảo thứ tự xoay / bỏ phân biệt 429 ngày-phút → đúng test đỏ → hoàn nguyên
- [x] **Đo O6**: `--hoi` G-01 và G-08 trên `gemini-3.6-flash` với và không `thinkingLevel: low` (4 lượt) → chốt mặc định theo số đo, ghi vào báo cáo
- [x] Báo cáo `testing/reports/…-P7-chang1.md` kèm output CLI thật

---

## Chặng 2 — Giao diện và luồng HTTP

- **POST sinh → lưu `ai_logs` → redirect GET `/ai/ket-qua/{log_id}`** (Post/Redirect/Get): F5 không gọi AI lại, không đốt quota. Nút gửi tự vô hiệu khi bấm.
- Routes (`app/routers/ai.py`, chỉ import `app.ai.service`): `POST /ai/nhac-lich/lich-hen/{id}`, `POST /ai/nhac-lich/tiem/{id}`, `POST /ai/tom-tat/{pet_id}`, `GET+POST /ai/hoi-dap`, `GET /ai/ket-qua/{log_id}`, `POST /ai/ket-qua/{log_id}/chot`, `GET /ai/quota` + `POST /ai/quota/dat-lai` (chỉ `manager`). Link quay lại qua `?tu=`, chỉ nhận đường dẫn bắt đầu bằng đúng một `/`.
- Templates: `ai_ket_qua.html` (dùng chung; nhắc lịch có textarea + Sao chép + Chốt), `ai_hoi_dap.html`, `ai_quota.html`. **`DISCLAIMER` cố định ở đầu nội dung**, hiện cả khi lỗi. Mỗi kết quả ghi "Trả lời bởi: <model>".
- Nút gắn thêm: `appointments.html` (soạn tin nhắc — chỉ lịch còn sửa được), `vaccinations.html`, `pet_detail.html`. Menu + thẻ trang chủ "Trợ lý AI" cho cả 3 vai trò.

- [ ] Router, templates, nút, menu, CSS
- [ ] `tests/integration/test_ai.py`: TC-084, 085, 086, 089, 090, 091, 099, 100; caretaker gọi nhắc lịch → 403; không phải quản lý mở `/ai/quota` → 403; F5 trang kết quả không sinh log mới; AI lỗi → không 500, lịch còn nguyên; `?tu=//evil.com` bị bỏ qua
- [ ] e2e bước 10 (tóm tắt AI bằng link/nút lấy từ HTML, FakeProvider) → **TC-101 đủ 11/11**
- [ ] Tách khối smoke P7 theo chặng **trước khi** đưa người dùng tick; rà luồng trình duyệt lượt `fake`
- [ ] Báo cáo `…-P7-chang2.md`

## Chặng 3 — Gemini thật (khoảng 15 lượt quota)

- [ ] `python -m app.ai.quota --guardrail --model gemini-3.6-flash` → G-01→G-13 (13 lượt, O3–O5); đánh đạt/không đạt từng ca
- [ ] Nhắc lịch + tóm tắt qua trình duyệt với `AI_PROVIDER=gemini` (2 lượt): đúng dữ liệu, không bịa
- [ ] Ca không đạt → sửa prompt/guardrail **kèm test** rồi chạy lại riêng ca đó
- [ ] G-14→G-20 xác nhận trên giao diện bằng `fake`/ngắt mạng (0 lượt quota); mở `ai_logs` kiểm cột `prompt` sạch; người dùng tick smoke

## Đóng P7

- [ ] `ai-safety.md` (luật xoay, các lớp guardrail, O2, Q8–Q10, giới hạn: code không bắt được việc nêu tên bệnh), `architecture.md`, `erd.md`, `codebase-map.md`, `test-cases.md`, `roadmap.md`, README
- [ ] Toàn bộ pytest xanh (số thật), log phiên đầy đủ, `docs/plans/README.md` thêm dòng kế hoạch

**DoD:** S1–S5 có test đỏ-trước; TC-082→100 + TC xoay/quota xanh; TC-101 11/11; G-01→G-13 chạy với Gemini thật có kết quả + model trong báo cáo, G-14→G-20 có test tự động + xác nhận giao diện; smoke P7 tick đủ.

## Kiểm chứng

1. `.venv/Scripts/python.exe -m pytest` — ghi số thật; phép đếm log phiên xanh sau khi cập nhật `codebase-map.md`.
2. Đột biến từng lớp guardrail và luật xoay → đúng test đỏ → hoàn nguyên, xác nhận đột biến thật sự vào file.
3. `python -m app.ai.quota` hiện bảng đúng mẫu; `--hoi` với khóa thật trả lời và số lượt tăng đúng 1.
4. Trình duyệt (`uvicorn app.main:app`): nhắc lịch → sửa → chốt; tóm tắt; hỏi đáp; F5 không tăng quota; ngắt mạng → thông báo thân thiện + DISCLAIMER vẫn hiện; `/ai/quota` với quản lý.
