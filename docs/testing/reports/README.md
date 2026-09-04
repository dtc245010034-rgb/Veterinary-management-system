# Báo cáo kiểm thử theo phase

Mỗi phase P1–P8 kết thúc bằng một file `YYYY-MM-DD-Pn.md` trong thư mục này.

**Nguyên tắc: dán output thật, không viết lại bằng lời.** Câu "test đã chạy ổn" không có giá trị
làm bằng chứng; khối output `pytest` có số passed/failed thì có. Cuối kỳ, các file ở đây là phần
kết quả kiểm thử của báo cáo.

## Mẫu file

```markdown
# Báo cáo kiểm thử — P3 Lịch hẹn

- **Ngày:** 2026-__-__
- **Phase:** P3 — Đặt/đổi/hủy lịch, chống trùng lịch
- **Commit:** <hash ngắn>

## 1. Kết quả tự động

### Toàn bộ suite

    $ pytest
    <dán nguyên output>

### Thời gian từng tầng

| Tầng | Số test | Kết quả | Thời gian |
|---|---|---|---|
| unit | | | |
| integration | | | |
| e2e | | | |

## 2. Test case đã hoàn thành trong phase

Cập nhật tương ứng trong `../test-cases.md`.

| TC | Tình huống | File test | Kết quả |
|---|---|---|---|
| TC-0xx | | | ✅ |

## 3. Checklist thủ công

Chép khối checklist của phase này **và mọi phase trước** từ `../smoke-checklist.md`, tick trong lúc bấm.

- [x] ...

## 4. Lỗi phát hiện và cách xử lý

| # | Hiện tượng | Nguyên nhân | Test tái hiện | Đã sửa |
|---|---|---|---|---|
| 1 | | | TC-0xx / tên test | ✅ |

Theo luật 2 trong `../test-strategy.md`, mỗi lỗi phải có test chạy **đỏ trước khi sửa**. Ghi lại cả
hai trạng thái ở đây.

## 5. Còn tồn đọng

- Test đỏ chưa sửa được (nêu tên test và lý do), hoặc "không có".
- Hạng mục hoãn sang phase sau.
```

## Quy ước

- Một file cho mỗi lần kết thúc phase. Chạy lại phase thì thêm file mới, **không sửa đè** file cũ —
  lịch sử kiểm thử là một phần của báo cáo.
- Phase P7 (AI) có thêm phần bắt buộc: chép nguyên **câu hỏi và phản hồi thật** của bộ ca guardrail
  `G-01` → `G-20` khi chạy với `AI_PROVIDER=gemini`. Đây là bằng chứng duy nhất cho thấy guardrail
  hoạt động với mô hình thật, vì test tự động chỉ chạy với `FakeProvider`.
- Test bị `skip` phải được nêu rõ ở mục 5 kèm lý do. Skip lặng lẽ là cách nhanh nhất làm hệ thống
  test mất giá trị mà không ai nhận ra.
