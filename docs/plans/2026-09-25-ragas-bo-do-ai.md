# Kế hoạch 2026-09-25 — Bộ đo chất lượng AI, có RAGAS cho phần tóm tắt

**Trạng thái: đã duyệt, CHƯA thực hiện.** Viết ra trước khi đóng phiên 24/09 để phiên sau mở ra là
làm được ngay.

## Vấn đề

`G-01 → G-13` mới chạy **một lần bằng tay** ngày 19/09 rồi chép kết quả vào báo cáo. Sau đó prompt
đã đổi hai lần — M-08 (20/09, bỏ dòng sai khiến mô hình tự viết khuyến cáo) và M-03 (24/09, trần độ
dài câu hỏi) — mà **không ai biết chất lượng có tụt không**.

Công cụ `python -m app.ai.quota --guardrail` đã sinh câu trả lời và dựng báo cáo Markdown, nhưng
**cố ý để trống cột "Đạt?"** kèm lý do ghi ngay trong báo cáo:

> *"test tự động chỉ kiểm được phần guardrail nằm trong code, còn mô hình có tuân thủ hay không thì
> phải người đọc."*

Vậy khoảng trống thật là **chấm điểm đang làm bằng tay**, không phải "chưa có bộ đo".

## Vì sao KHÔNG dùng RAGAS đầy đủ

Hệ thống này gần như không có chữ "R" trong RAG — không retriever, không vector store, không chunking.

| Tính năng | "Context" đến từ đâu | Metric RAGAS áp được? |
|---|---|---|
| Soạn tin nhắc lịch | Đưa thẳng từ `appointments` | Không |
| Tóm tắt hồ sơ | Đưa thẳng từ `care_records` | **`Faithfulness` có nghĩa thật** |
| Hỏi đáp chăm sóc | **Không có context nào** | Không |

`context_precision` và `context_recall` **luôn bằng 1 theo cấu tạo**, không phải theo chất lượng:
hệ thống truyền đúng những bản ghi nó chọn, không retriever nào có thể chọn sai. Dán bảng điểm
1.00/1.00 vào báo cáo là đúng cái `CLAUDE.md` mục 7 gọi là *"test luôn xanh nhưng không chứng minh
điều gì"*.

**Nhưng `Faithfulness` thì có nghĩa với tóm tắt** — nó tách câu trả lời thành từng mệnh đề rồi đối
chiếu từng mệnh đề với hồ sơ gốc. Và lượt rà 19/09 **đã ghi nhận đúng một ca hỏng kiểu đó**: AI hiểu
nhãn dữ liệu "Rà 19/09" thành ngày 19/09, và gán lời dặn của nhân viên thành "khách dặn". Lúc đó ghi
là "nhiễu do dữ liệu test"; nhìn bằng lăng kính faithfulness thì nó là **hallucination có thật,
chưa ai đo**.

## Bốn quyết định của người dùng (25/09)

1. **Dùng RAGAS, nhưng chỉ cho tóm tắt** (`Faithfulness`). Ba nhóm còn lại chấm bằng **luật code**,
   không tốn lượt gọi nào và không cần thư viện.
2. **RAGAS gọi Gemini qua wrapper gọi ngược vào `goi_co_xoay`** — lượt chấm cũng được xoay ca và
   được đếm vào bảng quota. Không đi thẳng SDK riêng của RAGAS.
3. **Giám khảo phải là model KHÁC model bị chấm.** `G-01 → G-13` chạy trên `gemini-3.6-flash`; để
   model tự chấm bài của chính nó là thiên vị đã biết (self-preference).
4. **Bộ ca tóm tắt và nhắc lịch viết riêng, có cài bẫy** — dựng lại đúng hai lỗi đã gặp thật 19/09.
   Dùng hồ sơ mẫu sạch thì điểm luôn 1.00 và bộ đo vô dụng.

## Ngân sách quota — đã tính lại cho đúng

Ban đầu agent đọc `GEMINI_RPD_UOC_TINH=20` thành trần toàn cục. **Sai**: docstring `app/ai/quota.py`
nói rõ *"gói miễn phí cho **mỗi model** khoảng 20 lượt/ngày"*, và `GEMINI_MODELS` đang có 4 model →
ngân sách thật **~80 lượt/ngày**. Chính docstring đó còn nói cơ chế xoay ca sinh ra **vì** *"một
model là không đủ để chạy 20 ca guardrail"*.

| Nhóm | Ca | Lượt sinh | Cách chấm | Lượt chấm | Tổng |
|---|---|---|---|---|---|
| An toàn | `G-01 → G-13` (đã có trong `CAU_HOI_GUARDRAIL`) | 13 | luật | 0 | **13** |
| Bám phạm vi | `G-11`, `G-13` nằm sẵn trong 13 ca trên | 0 | luật | 0 | **0** |
| Nhắc lịch | 3 ca cài bẫy | 3 | luật | 0 | **3** |
| Tóm tắt | 3 ca cài bẫy | 3 | **RAGAS `Faithfulness`** | ~12 | **15** |

**Tổng ≈ 31 lượt / ~80 lượt mỗi ngày.** Chạy gọn một lệnh, một ngày.

`G-14 → G-20` **không** đưa ra model thật: `ai-safety.md` chốt *"Chỉ G-01 → G-13 cần model thật.
G-14 → G-20 là việc của code"* — lọc dữ liệu liên hệ, xử lý lỗi, `ai_logs` — đã có test tự động xanh.

## Ranh giới phải giữ

- **Cộng thêm, không thay thế.** Giữ nguyên cột "Đạt?" cho người đọc; máy chấm thêm cột bên cạnh.
  **Chỗ hai bên lệch nhau là thứ đáng đọc nhất trong báo cáo.**
- **`ragas` KHÔNG vào `requirements.txt`**, tách sang file phụ thuộc riêng, `import` đặt **bên trong
  hàm**. Lý do cụ thể: `pytest.ini` để `filterwarnings = error`; một `DeprecationWarning` từ
  `datasets` là đỏ cả bộ test ở những file chẳng liên quan — ngày 24/09 đã dính đúng vậy với `httpx`.
- **Trong CI chỉ chạy được phần chấm bằng luật.** `FakeProvider` trả câu cố định nên faithfulness
  không có gì để đo. Ghi thẳng câu này vào báo cáo, đừng để người đọc tưởng CI xanh là mô hình đạt.
- `quota.py` giữ nguyên vai trò, chỉ gọi sang module mới.

## Các bước

### Chặng 1 — tầng chấm bằng luật (0 phụ thuộc, 0 lượt gọi)

- [ ] 1.1 `app/ai/danh_gia.py`: các hàm chấm **thuần**, nhận `(cau_hoi, phan_hoi)` trả về điểm và lý
      do — có câu khuyến cáo? · lọt mẫu liều lượng (dùng lại `guardrail.chua_lieu_luong`)? · lọt
      SĐT/email (dùng lại `guardrail.xoa_lien_he`)? · có từ chối đúng với ca cần từ chối?
      → verify: test đỏ-trước cho từng hàm, gọi thẳng, không cần mạng.
- [ ] 1.2 Chấm tin nhắc lịch bằng luật: ngày/giờ/tên dịch vụ có xuất hiện trong tin không, khuyến
      cáo có bị lặp không (chính là M-08).
      → verify: ca đối chứng cho tin đúng, ca bẫy cho tin thiếu thông tin.
- [ ] 1.3 Nối vào `_ghi_bao_cao` của `quota.py`: thêm cột máy chấm, **giữ nguyên cột "Đạt?"**.
      → verify: chạy với `FakeProvider`, báo cáo sinh ra có đủ cả hai loại cột.

### Chặng 2 — bộ ca cài bẫy

- [ ] 2.1 Ba ca tóm tắt: hồ sơ chứa nhãn trông như ngày tháng · lời dặn của nhân viên dễ bị gán
      thành lời khách · một hồ sơ sạch làm ca đối chứng.
- [ ] 2.2 Ba ca nhắc lịch: lịch bình thường · lịch tiêm (ca M-08, dễ lặp khuyến cáo) · lịch có ghi
      chú dài.
      → verify: mỗi ca ghi rõ **bẫy là gì** và **điểm mong đợi**, ngay trong bộ ca.

### Chặng 3 — RAGAS cho faithfulness của tóm tắt

- [ ] 3.1 Lớp LLM tùy biến cho RAGAS, gọi ngược vào `goi_co_xoay`, ghim giám khảo sang model **khác**
      model bị chấm.
      → verify: test bằng `FakeProvider` rằng wrapper gọi đúng `goi_co_xoay` và đếm đúng lượt.
- [ ] 3.2 Chạy `Faithfulness` cho 3 ca tóm tắt, ghi điểm và danh sách mệnh đề không đối chiếu được
      vào báo cáo.
      → verify: ca bẫy phải ra điểm **thấp hơn** ca sạch — bằng nhau nghĩa là phép đo không đo gì.
- [ ] 3.3 File phụ thuộc riêng cho `ragas`, `import` bên trong hàm, `app` vẫn khởi động được khi
      chưa cài.
      → verify: gỡ `ragas` ra rồi chạy `pytest` toàn bộ — phải xanh hết.

### Chặng 4 — nghiệm thu và đóng

- [ ] 4.1 Đột biến có chủ đích cho từng hàm chấm, xác nhận đã vào file trước khi chạy.
- [ ] 4.2 Chạy lượt thật với Gemini (≈31 lượt), dán báo cáo vào `docs/testing/reports/`.
- [ ] 4.3 So cột máy chấm với cột người chấm của lượt 19/09; chỗ lệch ghi rõ lý do.
- [ ] 4.4 Cập nhật `ai-safety.md`, `test-cases.md`, `codebase-map.md`, log phiên.

## Rủi ro đã biết

| Rủi ro | Cách xử lý |
|---|---|
| `ragas` kéo `datasets` → warning làm đỏ cả bộ test | Tách phụ thuộc, import trong hàm, có bước 3.3 kiểm khi gỡ ra |
| Giám khảo cũng sai | Ghi cả mệnh đề mà giám khảo phản đối vào báo cáo để người đọc tự xét |
| Điểm faithfulness cao giả vì ca quá dễ | Bước 3.2 đòi ca bẫy phải thấp hơn ca sạch |
| Người đọc tưởng CI xanh là mô hình đạt | Ghi giới hạn ngay trong báo cáo và trong README |
