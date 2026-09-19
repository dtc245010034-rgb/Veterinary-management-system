# Chế độ AI giả lập: nhãn đúng, không đếm quota, báo rõ trên giao diện

> **Duyệt ngày:** 2026-09-19 — người dùng chọn "Sửa cả hai + báo rõ chế độ giả".
>
> **Người dùng gặp:** chạy server với `.env` `AI_PROVIDER=fake`, hỏi "Hôm nay thời tiết Hà Nội thế
> nào" → nhận câu mẫu "Bạn nên tắm cho chó…" kèm nhãn **"Trả lời bởi: gemini-3.5-flash"**, nên tưởng
> Gemini trả lời sai. `ai_logs` #40 → #44: năm câu hỏi khác nhau, cùng một câu trả lời.

## Nguyên nhân gốc

`quota.goi_co_xoay` luôn xoay qua danh sách model **Gemini** trong cấu hình, bất kể provider là gì.
`FakeProvider` nhận tên model nào cũng trả câu mẫu, nên:

1. `ai_logs.model` ghi tên model Gemini cho câu trả lời giả → nhãn sai trên giao diện.
2. `ghi_lan_goi` cộng lượt cho model Gemini → quota bị đếm khống (`3.5-flash` 6 → 11).

Test không bắt được vì test cố ý dùng `FakeProvider` **đóng vai Gemini** — ở đó xoay và đếm là đúng.

## Cách sửa

- `AIProvider` có thêm thuộc tính `tinh_quota`. `GeminiProvider`: luôn `True`. `FakeProvider`: mặc
  định `True` (giữ nguyên mọi test đang dùng nó đóng vai Gemini).
- `service.lay_provider()` ở chế độ `AI_PROVIDER=fake` trả `FakeProvider(tinh_quota=False)`.
- `goi_co_xoay` gặp provider `tinh_quota=False` → gọi thẳng một lần với model `fake`, không xoay,
  không đếm, không đổi trạng thái model.
- `ai_ket_qua.html`: model `fake` → "AI giả lập — không gọi Gemini".
- Ba trang AI hiện dòng cảnh báo khi cấu hình đang ở chế độ giả lập (Jinja global đọc `settings`).
- Trả số đếm `gemini-3.5-flash` hôm nay về 6 (5 lượt khống của #40 → #44).

## Checklist

- [x] Test đỏ: quota (không đếm, model `fake`), service (`lay_provider` chế độ fake), HTTP (nhãn + cảnh báo)
- [x] Sửa → xanh → đột biến
- [x] Kiểm trên Chrome với server `AI_PROVIDER=fake`; trả quota về đúng
- [x] pytest toàn bộ, `test-cases.md`, `ai-safety.md` mục 8, `codebase-map.md`, báo cáo, log phiên
