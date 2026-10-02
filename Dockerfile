# Image chạy ứng dụng. Dựng và chạy bằng `python run.py docker` (xem docs/trien-khai.md).
# Cùng phiên bản Python với CI để "chạy được trong Docker" nghĩa là "chạy được trên bản đã kiểm".
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Thư viện trước, mã nguồn sau: sửa code không làm cài lại thư viện.
# requirements.txt có cả pytest và httpx nên image cài thừa vài MB; chưa đáng tách file riêng.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# CSDL SQLite nằm ở /data (volume) để dựng lại image không mất dữ liệu.
RUN useradd --create-home --uid 10001 petcare && mkdir /data && chown petcare /data
USER petcare
ENV DATABASE_URL=sqlite:////data/petcare.db
VOLUME /data

EXPOSE 8000

# Volume trống thì nạp dữ liệu mẫu một lần; đã có CSDL thì giữ nguyên. Một dòng sh -c thay vì
# file .sh riêng: file .sh bị git trên Windows đổi sang CRLF sẽ không chạy được trong container Linux.
CMD ["sh", "-c", "[ -f /data/petcare.db ] || python -m app.seed; exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
