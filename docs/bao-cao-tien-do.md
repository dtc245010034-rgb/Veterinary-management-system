# Báo cáo tiến độ dự án — 03/10/2026

Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI (FastAPI + SQLAlchemy + SQLite + Jinja2).
Báo cáo này trả lời ba câu hỏi: **đã làm được gì, còn sót gì, bug còn lại là bug nào.**

Mọi con số bên dưới **đếm lại ngày 03/10 từ hệ thống tập tin và từ lượt chạy test**, không chép từ tài liệu cũ.

## 1. Tóm tắt một đoạn

Mười phase P0 → P9. **P0 → P7 xong** (người dùng đã tick smoke). **P8** (hoàn thiện và nộp) còn 6 ô smoke chờ người dùng.
**P9** (cổng khách hàng, Docker, email) **đã xong về code, test và tài liệu**; còn 23 ô smoke P9 và ô 2.2 (CI Docker) chờ
người dùng. Toàn bộ test xanh: **1381 passed, 1 skipped**. Lượt kiểm thử Chrome 03/10 trên CSDL demo **không phát hiện lỗi
chức năng**, chỉ có **hai lỗi nhỏ** (B-1 giao diện, B-2 thư giả không hiện ở terminal) và **một lỗi tài liệu đã sửa**.

## 2. Tiến độ theo phase

| Phase | Nội dung | Trạng thái |
|---|---|---|
| P0 | Bộ context, đặc tả, chiến lược kiểm thử | Xong |
| P1 | Khung ứng dụng, đăng nhập, phân quyền 3 vai trò | Xong |
| P2 | Chủ nuôi, thú cưng, dịch vụ, gói | Xong |
| P3 | Lịch hẹn, chống trùng lịch | Xong |
| P4 | Hồ sơ chăm sóc, lịch tiêm nhắc lại | Xong |
| P5 | Hóa đơn, thanh toán | Xong |
| P6 | Thống kê | Xong |
| P7 | Ba tính năng AI và guardrail | Xong (đã chạy Gemini thật, người dùng tick smoke 20/09) |
| P8 | README, báo cáo, slide, rà dữ liệu cá nhân | **Đang làm** — còn 6 ô smoke |
| P9 | Cổng khách hàng, Docker, email, tách đặc tả | **Code xong 03/10**; chờ người dùng tick và duyệt |

Chi tiết từng phase: [`roadmap.md`](roadmap.md).

## 3. Con số hiện tại (đếm 03/10)

| Hạng mục | Giá trị |
|---|---|
| Test | **1381 đạt, 1 bỏ qua** trong 59,22 giây (`pytest -p no:cacheprovider -rs`). Ca bỏ qua duy nhất: `tests/unit/test_hooks.py:61`, máy Linux không có PowerShell |
| Số test theo tầng | unit **923** · integration **458** · e2e **1** |
| Phép canh kiến trúc | **84** ca ở `tests/unit/test_architecture.py`, xanh |
| User story | 36 (US-01 → 28 theo đề bài, US-29 → 36 cho cổng khách), 10 nhóm file A–J |
| Test case trong ma trận | 182; chỉ 2 ô còn ⬜: TC-102 (smoke bấm tay) và TC-145 (job CI Docker) |
| Bảng CSDL | 17 |
| Smoke | 149 ô đã tick, **29 ô trống**: 6 ở P8, 23 ở P9 — đều là của người dùng |
| `tools/kiem_tra_song.py` | 150/150, 0 lỗi 500 trong lượt 03/10 trước (chưa chạy lại lượt này); **không** đi qua cổng khách |

## 4. Đợt kiểm thử 03/10 (Chrome, CSDL demo, `AI_PROVIDER=fake`)

Mọi thao tác chạy trên `demo.db` (dựng bằng `tools/tao_du_lieu_demo.py`), `petcare.db` thật **không đổi** (đã so mã băm).

**Cổng khách — đạt:**

- Đăng ký → xác minh email (token dùng một lần) → đặt mật khẩu → đăng nhập; đổi mật khẩu đúng cả ba ca (sai mật khẩu cũ,
  quá ngắn, thành công); quên và đặt lại mật khẩu, dùng lại token bị từ chối.
- Chống dò mật khẩu: 5 lần sai miễn phí, từ lần thứ 6 trả 429 "thử lại sau 30 giây"; nhập đúng khi đang khóa vẫn bị khóa.
- Cách ly dữ liệu: id của người khác = 404 giống id không tồn tại.
- Liên kết hồ sơ: duyệt, từ chối kèm lý do, đúng trạng thái trên từng tài khoản demo.
- Xin lịch: trần 3 lịch chờ mỗi khách; giờ trùng lịch chờ khác bị từ chối; nhân viên duyệt và từ chối đúng.
- Hỏi đáp AI: F5 không tốn lượt, câu xin thuốc bị chặn nhưng vẫn tốn lượt, hết lượt → 429.

**Phía nhân viên — đạt:**

- Phân quyền: chăm sóc bị 403 ở `/invoices`, `/users`, `/stats`, `/ai/quota`, `/lich-cho-duyet`, `/lien-ket-khach`; lễ tân bị 403 ở
  `/users`, `/stats`, `/ai/quota`; quản lý vào được tất cả.
- Ghi hồ sơ chăm sóc (thiếu tình trạng, lịch tương lai, lịch đã xong đều bị từ chối đúng); lập hóa đơn (lần hai bị chặn);
  thu một phần, thu vượt số nợ bị chặn; hủy hóa đơn đã thu bị chặn, hủy hóa đơn chưa thu được; đổi lịch (hợp lệ, ngoài giờ,
  trùng giờ); hủy lịch (không lý do bị chặn); ghi mũi tiêm (hạn nhắc trước ngày tiêm bị chặn); soạn nhắc lịch, tóm tắt, hỏi
  đáp AI; đặt lại trạng thái quota; tạo tài khoản nhân viên (tên trùng bị chặn).

**Không kiểm bằng Chrome trong lượt này** (nói thẳng để không ai tưởng đã phủ): luồng gửi thư thật qua SMTP; hạn 24 giờ của
lịch chờ chạy theo đồng hồ thật (chỉ có test tự động cho phần này); khóa/mở khóa tài khoản nhân viên và sửa bảng giá bằng
Chrome (có test tự động).

## 5. Bug còn lại

Theo luật làm việc của dự án: **chỉ ghi lại và xếp mức độ, chờ người dùng quyết rồi mới sửa.**

| Mã | Mức | Hiện tượng | Gốc | Cách sửa gợi ý |
|---|---|---|---|---|
| **B-2** | **Trung bình** | Chạy thử trên máy mình (`MAIL_PROVIDER=console`, mặc định), khách đăng ký xong **không có thư nào hiện ra**. README, docstring và hướng dẫn lẽ ra bảo "liên kết hiện trong terminal". Hệ quả: không thử được luồng đăng ký khách bằng tay nếu không có SMTP | `ConsoleMailer` chỉ gọi `logging.getLogger("app.mail").info(...)`, nhưng không nơi nào cấu hình logging; mức mặc định là WARNING nên dòng INFO bị bỏ. Đã kiểm lại bằng cấu hình log của uvicorn: mức hiệu lực = 30 (WARNING), không in gì. Không test nào canh dòng log này | Một dòng: đặt mức INFO cho `app.mail` khi khởi động, hoặc cho `ConsoleMailer` in thẳng ra `stderr`; kèm test dùng `caplog`/`capsys` |
| **B-1** | **Thấp** (giao diện) | Trang `/lien-ket-khach`: ô chọn tròn (radio) khi có nhiều ứng viên bị phóng to ~942px | CSS `input` toàn cục áp luôn cho radio (`app/templates/lien_ket_khach.html` dòng 22, `app/static/style.css`) | Thêm quy tắc CSS cho `input[type=radio]`; vẫn bấm chọn được nên không chặn thao tác |

Đã xử lý trong đợt này (không còn là bug):

- **Tài liệu lệch hành vi:** README ghi lịch chờ quá 24 giờ "hết giữ chỗ"; thực tế hệ thống **tự chuyển sang Đã hủy** (hủy lười:
  khi có người mở danh sách hoặc thao tác lịch). Đã sửa README và hướng dẫn.
- **Dữ liệu demo không thực tế:** bản đầu của script demo tạo ~15% lịch "Hoàn thành" không có hồ sơ chăm sóc — điều không thể
  xảy ra ngoài đời vì hoàn thành chỉ xảy ra qua ghi hồ sơ. Đã sửa script (mọi lịch hoàn thành đều có hồ sơ) và kiểm: 0 lịch
  hoàn thành thiếu hồ sơ.

Chấp nhận có chủ ý (**không phải bug**, người dùng quyết 03/10): nhân viên mọi vai trò đọc được câu hỏi/đáp AI của khách qua
`/ai/ket-qua/{id}`. Ghi ở [`ai-safety.md`](ai-safety.md) mục 10.

## 6. Còn sót / chưa hoàn thiện

| Việc | Của ai | Ghi chú |
|---|---|---|
| Tick khối smoke P9 (23 ô) và P8 (6 ô) | Người dùng | Agent không tick thay |
| Tick các ô 8.1 → 8.4 của [kế hoạch tổng P9](plans/2026-09-25-p9-cong-khach-hang.md) | Người dùng | Việc đã làm xong, chờ duyệt |
| Ô 2.2 — job CI `docker` | Người dùng | Có trong `ci.yml` nhưng **chưa chạy trên GitHub** (TC-145 còn ⬜) |
| Đồng bộ tick trong kế hoạch tổng P9 | Chưa quyết | Kế hoạch tổng còn 16 ô `[ ]`, trong đó các ô 4.3 → 7.2 đã có code, test và kế hoạch chặng tương ứng đều đã tick hết. Là chậm cập nhật tài liệu, không phải thiếu việc |
| `tools/kiem_tra_song.py` chưa phủ cổng khách | Có thể làm | Cổng khách đang được phủ bằng 458 test tích hợp và lượt Chrome này |
| Bộ đo chất lượng AI (RAGAS) | Chưa bắt đầu | [Kế hoạch](plans/2026-09-25-ragas-bo-do-ai.md) đã duyệt, **chưa thực hiện** (12 ô chưa tick). Prompt đã đổi hai lần mà chưa có số đo tự động |
| Slide / báo cáo cuối kỳ (P8) | Người dùng | Dựng từ các file trong `docs/` |
| Hạn mức AI của khách không khóa giao dịch | Chấp nhận | Hai yêu cầu đồng thời có thể vượt 1 lượt; ghi ở [kế hoạch chặng 7](plans/2026-10-03-p9-chang7-ai-khach.md) |

## 7. Giới hạn của sản phẩm (không phải bug)

Có trong [`HUONG-DAN-SU-DUNG.md`](../HUONG-DAN-SU-DUNG.md) mục 9: không hoàn tiền, khách không tự hủy/đổi lịch và không
thanh toán trực tuyến, AI chỉ soạn nháp (không tự gửi tin), không chẩn đoán/kê thuốc, một cửa hàng một CSDL, giờ mở cửa cố định
08:00–18:00, một trình duyệt một danh tính, dữ liệu nằm trên máy chạy phần mềm (phải tự sao lưu).

## 8. Cách dựng lại bản demo

```
python tools/tao_du_lieu_demo.py
DATABASE_URL=sqlite:///demo.db AI_PROVIDER=fake python run.py
```

Script từ chối ghi đè `petcare.db`; dữ liệu cố định theo hạt giống nên dựng lại ra đúng bản cũ. Số liệu của bản demo:
15 chủ nuôi, 22 thú cưng, hơn 130 lịch, 80+ hóa đơn, 7 khách ở đủ trạng thái, 6 yêu cầu liên kết, 3 lịch chờ duyệt, 15 lượt AI.
Danh sách tài khoản in ở cuối lượt chạy và nằm trong [`HUONG-DAN-SU-DUNG.md`](../HUONG-DAN-SU-DUNG.md) mục 4.
