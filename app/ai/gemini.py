"""Gọi Gemini API bằng REST, qua `urllib` của thư viện chuẩn.

Không thêm SDK: việc cần làm ở đây là một POST JSON và đọc một chuỗi trong phản hồi. Một
thư viện nữa chỉ thêm phụ thuộc phải pin phiên bản và theo dõi.

File này CHỈ gọi một model một lần. Việc chọn model, đếm lượt và xử lý hết quota nằm ở
app/ai/quota.py — xem docs/architecture.md.

Kết quả gọi thử bằng khóa thật ngày 17/09, dùng làm căn cứ cho cách đọc lỗi ở đây:
- `gemini-2.5-flash` → 404 "no longer available to new users"
- `gemini-3.6-flash` → 200 (6,7s; lần đầu 33s)
- `gemini-flash-latest` → 503 "experiencing high demand"
"""

import json
import re
import socket
import urllib.error
import urllib.request

from app.ai.provider import (
    LoiCauHinh,
    LoiHetQuota,
    LoiKetNoi,
    LoiModelKhongCo,
    LoiQuaTai,
)
from app.config import settings

GOC = "https://generativelanguage.googleapis.com/v1beta/models"

# "37s" hoặc "1.5s" trong RetryInfo.retryDelay.
GIAY_CHO = re.compile(r"(\d+(?:\.\d+)?)s")


class GeminiProvider:
    """Cài đặt `AIProvider` cho Gemini. Một lần gọi, không tự thử lại."""

    tinh_quota = True

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.gemini_api_key

    def tra_loi(self, model: str, system: str, user: str, timeout: float) -> str:
        if not self.api_key:
            raise LoiCauHinh(
                "Chưa có GEMINI_API_KEY. Đặt khóa trong .env rồi khởi động lại."
            )

        than = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
        }
        if settings.gemini_thinking_budget >= 0:
            than["generationConfig"] = {
                "thinkingConfig": {"thinkingBudget": settings.gemini_thinking_budget}
            }
        du_lieu = json.dumps(than).encode("utf-8")

        yeu_cau = urllib.request.Request(
            f"{GOC}/{model}:generateContent",
            data=du_lieu,
            method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
        )

        try:
            with urllib.request.urlopen(yeu_cau, timeout=timeout) as phan_hoi:
                return _doc_noi_dung(json.load(phan_hoi))
        except urllib.error.HTTPError as loi:
            raise _doi_loi_http(loi) from loi
        except urllib.error.URLError as loi:
            if isinstance(loi.reason, (socket.timeout, TimeoutError)):
                raise LoiQuaTai(f"Không gọi được AI: {loi}") from loi
            # Chưa tới được server: không tính lượt. Chuỗi gốc của urllib là tiếng Anh nên
            # chỉ giữ trong chuỗi ngoại lệ (`from loi`), không đưa lên màn hình.
            raise LoiKetNoi(
                "Không kết nối được tới máy chủ AI, vui lòng kiểm tra kết nối mạng."
            ) from loi
        except (socket.timeout, TimeoutError) as loi:
            # Quá hạn chờ: model khác có thể vẫn kịp trả lời trong ngân sách.
            raise LoiQuaTai(f"Không gọi được AI: {loi}") from loi


def _doc_noi_dung(du_lieu: dict) -> str:
    """Lấy chuỗi trả lời khỏi JSON của Gemini.

    Phản hồi 200 vẫn có thể không có chữ nào — ví dụ bộ lọc an toàn của Google chặn. Ca đó
    phải thành lỗi có tên, không phải chuỗi rỗng lặng lẽ hiển thị cho người dùng.
    """
    ung_vien = du_lieu.get("candidates") or []
    for c in ung_vien:
        phan = (c.get("content") or {}).get("parts") or []
        chu = "".join(p.get("text", "") for p in phan).strip()
        if chu:
            return chu

    ly_do = ung_vien[0].get("finishReason") if ung_vien else du_lieu.get("promptFeedback")
    raise LoiQuaTai(f"AI trả về phản hồi rỗng (lý do: {ly_do}).")


def _doi_loi_http(loi: urllib.error.HTTPError):
    """Đổi mã HTTP thành lỗi đã phân loại để quota.py biết phải làm gì tiếp."""
    # Đọc xong phải đóng: HTTPError giữ một luồng mở, không đóng thì Python dọn muộn và ném
    # ResourceWarning ở một chỗ hoàn toàn khác — bộ test bắt được đúng ca này.
    try:
        than = loi.read().decode("utf-8", "replace")
    finally:
        loi.close()
    try:
        chi_tiet = json.loads(than).get("error", {})
    except json.JSONDecodeError:
        chi_tiet = {}
    thong_diep = chi_tiet.get("message", than[:300])

    if loi.code == 404:
        return LoiModelKhongCo(thong_diep)
    if loi.code == 429:
        theo_ngay, gioi_han, thu_lai_sau = _doc_chi_tiet_429(chi_tiet)
        return LoiHetQuota(thong_diep, theo_ngay=theo_ngay, gioi_han=gioi_han, thu_lai_sau=thu_lai_sau)
    if loi.code in (400, 401, 403):
        return LoiCauHinh(thong_diep)
    return LoiQuaTai(thong_diep)


def _doc_chi_tiet_429(chi_tiet: dict) -> tuple[bool, int | None, int | None]:
    """Đọc `details` của lỗi 429: hết lượt theo ngày hay theo phút, hạn mức thật, chờ bao lâu.

    Phân biệt hai loại là điều quan trọng nhất ở đây. Hết lượt/phút chỉ cần nghỉ vài chục
    giây; coi nhầm nó là hết lượt/ngày thì model bị bỏ oan tới tận nửa đêm giờ Pacific.

    Không đọc được `details` thì coi là theo phút — đoán nhẹ hơn, và lần 429 sau vẫn sửa được.
    """
    theo_ngay = False
    gioi_han: int | None = None
    thu_lai_sau: int | None = None

    for muc in chi_tiet.get("details", []):
        loai = muc.get("@type", "")
        if loai.endswith("QuotaFailure"):
            for vi_pham in muc.get("violations", []):
                ten = f"{vi_pham.get('quotaId', '')} {vi_pham.get('quotaMetric', '')}"
                if "PerDay" in ten:
                    theo_ngay = True
                    gia_tri = vi_pham.get("quotaValue")
                    if gia_tri is not None:
                        try:
                            gioi_han = int(gia_tri)
                        except (TypeError, ValueError):
                            gioi_han = None
        elif loai.endswith("RetryInfo"):
            khop = GIAY_CHO.search(str(muc.get("retryDelay", "")))
            if khop:
                thu_lai_sau = int(float(khop.group(1))) + 1

    return theo_ngay, gioi_han, thu_lai_sau
