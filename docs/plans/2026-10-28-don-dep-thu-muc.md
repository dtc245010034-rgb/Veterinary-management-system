# Kế hoạch — Dọn thư mục gốc repo

**Trạng thái: ĐÃ DUYỆT 28/10/2026** (người dùng chọn "Dọn vừa: đưa tài liệu vào docs/", đồng ý sửa đúng một dòng
`CLAUDE.md`, đồng ý xóa hai nhánh remote đã merge, và chọn commit B-1 riêng trước khi dọn).

Vấn đề: gốc repo có 15 file theo dõi, trong đó ba file không đúng chỗ — `đề-bài.md` (tên file **có dấu**, trái quy ước
`CLAUDE.md` mục 5; git hiển thị `"\304\221\341\273\201-b\303\240i.md"`), `HUONG-DAN-SU-DUNG.md` và `bao-cao-ra-soat-2026-10-02.md`
(báo cáo duy nhất nằm ngoài `docs/testing/reports/`) — và `.gitignore` có khối lặp ở cuối.

**Cố ý KHÔNG làm** (đã cân nhắc, người dùng không chọn): xóa `test.py` (nằm trong kế hoạch đã duyệt 02/10, 391 byte), dời `petcare.db`
vào `data/` (đụng `config.py`, Docker, `.env.example`, `run.py`, test mà không thu được gì), sắp lại `docs/plans`/`docs/sessions`
(vỡ hàng trăm link trong log lịch sử).

## Các bước

- [x] 0. Commit B-1 riêng trước (`da370e3`), loại `docs/testing/smoke-checklist.md` — phần người dùng tự tick.
- [x] 1. `git mv` để giữ lịch sử: `đề-bài.md` → `docs/de-bai.md`; `HUONG-DAN-SU-DUNG.md` → `docs/huong-dan-su-dung.md` (chữ thường cho
      khớp các file khác trong `docs/`); `bao-cao-ra-soat-2026-10-02.md` → `docs/testing/reports/2026-10-02-ra-soat-doc-lap.md`.
      → verify: `git status` hiện `renamed`, không phải xóa + thêm.
- [x] 2. Sửa link tới ba file (CLAUDE.md dòng 75, README dòng 12, `bao-cao-tien-do`, `ai-safety`, `roadmap`, `user-stories/README`,
      hai kế hoạch/ma trận trỏ báo cáo rà soát) và link đi ra từ chính ba file (`README.md` → `../README.md`; `docs/...` → `../../...`).
      Nhắc tên dạng văn bản trong log phiên/kế hoạch cũ **giữ nguyên** (là lịch sử; `git log --follow` truy được).
      → verify: `test_moi_link_tuong_doi_trong_tai_lieu_deu_ton_tai` xanh.
- [x] 3. `.gitignore`: bỏ khối lặp (`.venv/`, `__pycache__/` ghi hai lần), `.venv312/` và `test-results.txt` lạc chỗ thì gộp vào khối Python.
      → verify: `git status --ignored` không đổi so với trước (không file nào bị lộ ra hay bị che thêm).
- [x] 4. `docs/codebase-map.md`: gỡ hai dòng khỏi mục "Gốc dự án", thêm vào mục `docs/`; báo cáo 26 → 27; kế hoạch 31 → 32.
      → verify: `test_so_luong_ghi_trong_codebase_map_khop_so_file_that` và phép canh file trong bản đồ xanh.
- [x] 5. Xóa nhánh remote đã merge hết vào `main`: `origin/demo-cac-chuc-nang`, `origin/hung`.
      → verify: `git branch -r --merged origin/main` trước khi xóa liệt kê đủ hai nhánh; sau khi xóa `git ls-remote --heads origin` chỉ còn `main`.
- [x] 6. `pytest` toàn bộ xanh; `AI_PROVIDER=fake python tools/kiem_tra_song.py` 150/150. Không chạy lại `docker build`: không đụng `Dockerfile`,
      `app/`, `requirements.txt` hay `.dockerignore`; `test_docker_files.py` xanh trong lượt `pytest` toàn bộ.
- [x] 7. Log phiên (Phần 3), một commit `chore:` riêng. **Chưa push** — chờ người dùng bảo.
