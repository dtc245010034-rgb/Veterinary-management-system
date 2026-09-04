# Log phiên làm việc

Mỗi phiên chat với AI agent để lại một file ở đây. Đây là nhật ký thi công của dự án.

## Vì sao cần

Dự án được làm bằng vibe code qua nhiều phiên chat. Mỗi phiên agent bắt đầu lại từ con số không —
không nhớ phiên trước đã quyết định gì, sửa file nào, còn dở việc gì. Thư mục này là bộ nhớ ngoài
bù cho chỗ đó.

Nó cũng giải quyết vấn đề thứ hai: cuối kỳ, báo cáo được dựng từ chính các file này, nên quá trình
làm và nội dung báo cáo khớp nhau theo đúng nghĩa đen thay vì phải nhớ lại.

## Cơ chế

File được **tạo tự động** bởi hook `SessionStart` (xem [`../../.claude/hooks/session-start.ps1`](../../.claude/hooks/session-start.ps1))
với khung sẵn 5 mục. Agent điền nội dung trong lúc làm việc.

Hook `Stop` **xóa file nếu cả 5 mục còn nguyên placeholder** — phiên chỉ hỏi đáp, không thay đổi gì
thì không cần để lại log. Nếu còn mục chưa điền, hook in nhắc thay vì xóa.

## Quy ước

- Tên file: `YYYY-MM-DD-NN.md`, `NN` là số thứ tự phiên trong ngày (`01`, `02`, …)
- Điền **trong lúc làm**, không để dồn tới cuối phiên — phiên bị ngắt giữa chừng thì phần đã ghi vẫn còn
- Mục **Kết quả test** ghi số thật (`42 passed, 0 failed`), không ghi "test chạy ok"
- Mục **File đã thay đổi** ghi đường dẫn cụ thể, không ghi "sửa một số file"
- Mục **Quyết định** chỉ ghi thứ **không đọc ra được từ diff**: vì sao chọn cách này thay vì cách kia,
  đã cân nhắc gì rồi loại. Việc gì làm rồi thì diff đã kể, không cần chép lại
- Test đỏ chưa sửa được: ghi tên test cụ thể vào mục **Còn dở**, không im lặng bỏ qua

## Cấu trúc file

```markdown
# Phiên YYYY-MM-DD-NN

- **Ngày:** YYYY-MM-DD
- **Mục tiêu phiên:** một dòng

## Quyết định
Những lựa chọn đã chốt và lý do. Bỏ trống nếu phiên không quyết định gì mới.

## File đã thay đổi
Danh sách đường dẫn kèm một dòng mô tả.

## Kết quả test
Output thật của pytest, hoặc "không chạy test — phiên chỉ sửa tài liệu".

## Còn dở / phiên sau làm gì
Việc chưa xong, test đang đỏ, quyết định còn treo.
```

## Liên hệ với các tài liệu khác

| Tài liệu | Quan hệ |
|---|---|
| [`../plans/`](../plans/) | Kế hoạch ghi việc **sẽ làm**; log phiên ghi việc **đã làm** |
| [`../codebase-map.md`](../codebase-map.md) | Phiên thêm/xóa file thì phải cập nhật bản đồ, và ghi việc đó vào log |
| [`../testing/reports/`](../testing/reports/) | Log phiên ghi kết quả test từng phiên; report ghi kết quả từng phase |
