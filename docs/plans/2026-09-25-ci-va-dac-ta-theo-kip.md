# Kế hoạch 2026-09-25 — CI GitHub Actions và đặc tả theo kịp code

**Trạng thái: đã duyệt 25/09.** Người dùng chọn hai việc trong năm việc được đề xuất đầu phiên:
dựng CI, và trả lời câu hỏi treo *"11 lỗi sửa hôm 24/09 thêm hành vi mới nhưng `user-stories.md`
không thêm tiêu chí nào — đặc tả có nên đuổi theo không?"*.

## Hai quyết định của người dùng

1. **CI chạy matrix cả `windows-latest` lẫn `ubuntu-latest`**, không chọn một nền.
   Đổi lại phải chấp nhận job Linux có thể đỏ lần đầu vì lý do nền tảng: dự án **chưa từng chạy
   trên Linux lần nào**, và máy làm việc không có WSL để thử trước.
2. **Đặc tả chỉ đuổi theo luật nghiệp vụ**, không đuổi theo hành vi giao diện.
   `user-stories.md` là tài liệu nghiệm thu; trộn `Cache-Control` và "giữ lại tên đăng nhập đã gõ"
   vào đó làm loãng đúng thứ nó dùng để nghiệm thu. Bốn lỗi giao diện **L-01, L-02, L-05, L-07**
   ở lại `test-cases.md`.

## Vì sao CI đáng làm trước

Phiên này mở ra đã bắt được hai thứ mà **không ai đang canh**:

- `README.md` ghi `pytest` "902 ca, ~101s" và "ma trận 122 test case" — thực tế **904 ca, ~115s,
  133 ca trong ma trận**. Số cũ chép tay từ phiên trước.
- Bộ test chạy **115s**, vượt ngân sách của `test-strategy.md`, treo từ 11/09.
  > ⚠️ **Đính chính (cùng ngày, phần 2).** Câu trên viết "ngưỡng 90s" là **sai**: ngân sách thật
  > là **100s**, nới lần hai ngày 18/09. Con số 90s là của lần nới 13/09 còn sót trong
  > `roadmap.md`, và agent đã chép nó thay vì đọc `test-strategy.md`. Nay có phép canh
  > `test_nguong_thoi_gian_test_khong_bi_chep_lech_khoi_test_strategy` giữ chỗ này.

Cả hai đều là dạng lỗi "không ai chạy lại nên không ai biết". CI đóng đúng lớp đó: mỗi lần push là
một phép đo thật, có mốc thời gian, không phụ thuộc trí nhớ của ai.

## Ranh giới phải giữ

- **CI không được tạo `.env`.** Suite phải chạy bằng giá trị mặc định của `config.py`; đó cũng là
  phép chứng minh rằng người chấm clone repo về là chạy test được ngay. Bước 1.2 kiểm điều này
  **tại chỗ trước** khi đẩy lên, không đoán.
- **Không sửa test để job Linux xanh.** Test nào đỏ trên Linux thì hoặc là lỗi thật (sửa code),
  hoặc là giới hạn nền tảng (ghi rõ lý do skip). Sửa assert cho hợp màu xanh là đúng thứ
  `CLAUDE.md` mục 7 gọi là test giả.
- **Luật nào không có test đang canh thì KHÔNG viết vào đặc tả** — `CLAUDE.md` mục 9 dòng 2, bốn lần
  tài liệu từng mô tả chức năng chưa tồn tại.
- Giữ nguyên giọng và dạng câu `- Given … When … Then …` của 104 tiêu chí đang có.

## Mười hai lỗi, phân loại đã chốt

| Mã | Luật | Vào đặc tả? | US |
|---|---|---|---|
| M-06 | Cả buổi nằm trọn trong 08:00–18:00, cùng một ngày | ✅ | US-10, US-12 |
| M-05 | SĐT là số Việt Nam 10 chữ số, chuẩn hóa `+84`/`84`; email đúng định dạng | ✅ | US-04 |
| L-03 | Trần độ dài chuỗi · cân nặng 200 kg · tuổi 40 năm · giới tính theo danh sách · giá 1 tỷ · tiền chỉ nhận số nguyên đồng | ✅ | US-04, US-05, US-07 |
| L-06 | Lịch đã hủy báo đúng lý do khi lập hóa đơn; đổi lịch không đổi gì thì không thành `rescheduled` | ✅ | US-19, US-12 |
| D-02 | Số lượt mỗi dòng trong gói phải > 0, không âm thầm bỏ qua dòng sai | ✅ | US-08 |
| M-03 | Câu hỏi AI quá 1.000 ký tự bị chặn **trước khi gọi API** | ✅ | US-26 |
| M-07 | Hỏi trước khi tạo chủ nuôi trùng số điện thoại | ❌ **đã có sẵn** | US-04 |
| L-01 | Thẻ trang chủ khớp thanh điều hướng theo vai trò | ❌ giao diện | — |
| L-02 | `Cache-Control: no-store` cho mọi trang trừ `/static` | ❌ giao diện | — |
| L-05 | Trang kết quả AI hiện lại câu hỏi | ❌ giao diện | — |
| L-07 | Đăng nhập sai giữ lại tên đăng nhập | ❌ giao diện | — |

**M-07 là ca đáng chú ý nhất bảng này:** US-04 **đã đặc tả đúng từ đầu** — *"cảnh báo trùng và
**hỏi** có phải khách cũ không"* — code mới là thứ đi lệch (tạo bản ghi rồi mới cảnh báo). Đặc tả
không thiếu gì; nó bị bỏ qua. Ghi lại để không ai tưởng mọi lỗi đều là lỗ hổng đặc tả.

## Các bước

### Chặng 1 — CI GitHub Actions

- [x] 1.1 `.github/workflows/ci.yml`: matrix `windows-latest` + `ubuntu-latest`, Python 3.14,
      `fail-fast: false` để job Windows vẫn chạy hết khi Linux đỏ, cài `requirements.txt`,
      chạy `pytest -rs` cho **hiện rõ test bị bỏ qua** thay vì giấu trong màu xanh.
      → verify: YAML đọc được bằng trình phân tích, không có bước nào tạo `.env`.
- [x] 1.2 Chứng minh tại chỗ suite không cần `.env`: đổi tên `.env` rồi chạy lại toàn bộ.
      → verify: vẫn xanh đủ số ca, rồi trả `.env` về đúng tên cũ.
- [x] 1.3 Ghi lại danh sách test sẽ bỏ qua trên Linux và lý do nền tảng.
      → verify: `pytest -rs` trên Windows in ra số skip để đối chiếu với job Linux sau này.
- [x] 1.4 Cập nhật `docs/codebase-map.md` (thêm mục `.github/`) và `README.md` (huy hiệu CI).
      **Không** sửa số ca trong khối "Cách chạy test": đó là vấn đề ② người dùng chưa chọn xử lý,
      và tự ý sửa là agent tự mở rộng phạm vi.
      → verify: `pytest tests/unit/test_architecture.py` xanh.

### Chặng 2 — Đặc tả theo kịp

- [x] 2.1 Đối chiếu **từng** luật ở bảng trên với tên test đang canh nó. Luật nào không tìm được
      test thì gạch khỏi danh sách, không viết vào đặc tả.
      → verify: bảng luật → tên test dán vào log phiên, không phải câu "đã kiểm".
- [x] 2.2 Thêm tiêu chí vào US-04, US-05, US-07, US-08, US-10, US-12, US-19, US-26.
      → verify: đếm lại số tiêu chí bằng lệnh, cập nhật con số ở `README.md` và `codebase-map.md`.
- [x] 2.3 Soát `test-cases.md` xem tiêu chí mới có cần dòng truy vết nào chưa có.
      → verify: ma trận vẫn **131 ✅ · 1 ⬜ · 1 ➖** trên 133 dòng, hoặc giải thích vì sao đổi.

### Chặng 4 — việc tồn, làm cùng ngày theo yêu cầu *"xử lý những việc còn sót lại"*

Ba vấn đề ①②③ báo cáo đầu phiên nay xử lý hết. ③ hóa ra **không cần người dùng quyết** như agent
tưởng: `test-strategy.md` đã ghi sẵn *"Vượt thì đo và tìm nguyên nhân, không cắt test"* — tức phần
đo và truy nguyên là việc của agent, chỉ **kết luận cuối** mới cần người dùng.

- [x] 4.1 **①** Sửa phép canh tự báo động giả: bỏ qua khung log phiên rỗng hook vừa tạo, dùng đúng
      ngưỡng 5 ô `_(chua ghi)_` của `session-stop.ps1`. Tách hàm `dem_log_phien_da_ghi()` ra để
      test được bằng thư mục tạm.
      → verify: tái hiện đỏ trước bằng khung rỗng thật · 1 lượt đột biến (`<` thành `<=`), xác nhận
      đột biến đã vào file, **bị bắt bởi cả test cô lập lẫn phép canh gốc** · hoàn nguyên · xóa khung.
- [x] 4.2 **②** Sửa số ca trong README bằng **số đo thật**, không chép.
      → verify: đo từng tầng hai lượt, ghi cả khoảng dao động.
- [x] 4.3 **③** Đo và truy nguyên nhân thời gian test đúng luật `test-strategy.md`.
      → verify: `--durations=20` cho thấy 20 ca chậm nhất chỉ ~24s/115s; đo riêng `create_all`
      **25,6 ms × 905 ≈ 23s**. Kết luận: **không test nào đáng cắt**.
- [x] 4.4 Đính chính **ngưỡng 90s → 100s** ở `roadmap.md`, `codebase-map.md`, kế hoạch này; thêm
      phép canh `test_nguong_thoi_gian_test_khong_bi_chep_lech_khoi_test_strategy`.
      → verify: phép canh **đỏ thật** trên bản chưa sửa (bắt đúng ba chỗ), thu hẹp mẫu cho khỏi vồ
      bản ghi lịch sử, rồi xanh. **54 → 55 phép canh.**
- [x] 4.5 `roadmap.md`: CI không còn nằm trong danh sách "chưa bắt đầu"; thêm bản ghi tiến độ 25/09;
      **giữ nguyên dòng lịch sử 13/09** và gắn cảnh báo thay vì viết lại.
      → verify: `pytest tests/unit/test_architecture.py` xanh.
- [x] 4.6 Chạy lại toàn bộ suite trên máy rảnh, cập nhật `codebase-map.md` và log phiên.

### Chặng 3 — Đóng phiên

- [x] 3.1 Chạy toàn bộ suite, ghi kết quả thật kèm thời gian.
- [x] 3.2 Điền `docs/sessions/2026-09-25-01.md` và cập nhật `docs/codebase-map.md`.

**Tổng: 15 ô** (9 ô hai việc người dùng chọn + 6 ô việc tồn ở chặng 4). *(Viết "10" lúc lập kế hoạch rồi đếm lại ra 9 — đúng lớp lỗi "chép số thay
vì đếm" mà `CLAUDE.md` mục 10 cảnh, lần thứ hai sau kế hoạch RAGAS hôm 24/09. Lần này còn do
backtick trong chuỗi bash bị shell diễn giải — cùng họ với mục 9 dòng 5.)*

## Rủi ro đã biết

| Rủi ro | Cách xử lý |
|---|---|
| Job Linux đỏ lần đầu vì lý do nền tảng | Đã báo trước và người dùng chấp nhận. `fail-fast: false` giữ job Windows chạy hết để vẫn có tín hiệu thật |
| `tests/unit/test_hooks.py` im lặng bỏ qua trên Linux | `pytest -rs` in rõ lý do skip; bước 1.3 ghi trước con số mong đợi |
| Sửa test cho hợp màu xanh của Linux | Ghi thành ranh giới ở trên; mọi thay đổi test phải nói rõ là lỗi thật hay giới hạn nền tảng |
| Viết tiêu chí cho hành vi chưa có test | Bước 2.1 chặn trước bằng bảng luật → tên test |
| Đếm sai số tiêu chí như đã đếm sai số lỗi ba lần | Bước 2.2 đếm bằng lệnh, không chép tay |
