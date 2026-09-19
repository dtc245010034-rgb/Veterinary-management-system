"""Test cho app/ai/gemini.py — đọc phản hồi và phân loại lỗi HTTP.

Chỉ thay `urllib.request.urlopen` — đúng ranh giới ngoài được phép thay (CLAUDE.md mục 7).
Mọi thứ khác là code thật: dựng request, đọc JSON, đổi mã lỗi thành lỗi có tên.

JSON trong file này chép từ phản hồi THẬT ngày 17/09 (khóa thật, `gemini-3.6-flash`), nên
nếu Google đổi cấu trúc thì test còn xanh mà thực tế đã hỏng — chỗ đó chỉ lượt chạy tay ở
chặng 3 mới phát hiện được. Đây là giới hạn đã biết của tầng unit.
"""

import io
import json
import urllib.error

import pytest

from app.ai.gemini import GeminiProvider
from app.ai.provider import LoiCauHinh, LoiHetQuota, LoiKetNoi, LoiModelKhongCo, LoiQuaTai

PHAN_HOI_THAT = {
    "candidates": [
        {
            "content": {
                "parts": [{"text": "Thông thường, bạn nên tắm cho chó khoảng 2 đến 4 tuần một lần."}],
                "role": "model",
            },
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 35},
}


class PhanHoiGia(io.BytesIO):
    """Đủ để `json.load` đọc được, và hỗ trợ `with`."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def gia_lap(monkeypatch, tra_ve=None, loi=None):
    def _urlopen(yeu_cau, timeout=None):
        gia_lap.yeu_cau = yeu_cau
        gia_lap.timeout = timeout
        if loi is not None:
            raise loi
        return PhanHoiGia(json.dumps(tra_ve).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)
    return gia_lap


def loi_http(ma: int, than: dict) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="http://x", code=ma, msg="loi", hdrs=None,
        fp=io.BytesIO(json.dumps(than).encode("utf-8")),
    )


def test_goi_thanh_cong_tra_ve_dung_chu_va_gui_dung_model_system_user(monkeypatch):
    goi = gia_lap(monkeypatch, tra_ve=PHAN_HOI_THAT)

    ket_qua = GeminiProvider(api_key="k").tra_loi(
        model="gemini-3.6-flash", system="S", user="U", timeout=12
    )

    assert ket_qua.startswith("Thông thường")
    assert "gemini-3.6-flash:generateContent" in goi.yeu_cau.full_url
    assert goi.timeout == 12
    than = json.loads(goi.yeu_cau.data)
    assert than["systemInstruction"]["parts"][0]["text"] == "S"
    assert than["contents"][0]["parts"][0]["text"] == "U"
    assert goi.yeu_cau.headers["X-goog-api-key"] == "k"


def test_thieu_khoa_api_la_loi_cau_hinh_va_khong_goi_mang(monkeypatch):
    def _no(*a, **kw):
        raise AssertionError("Không được gọi mạng khi chưa có khóa")

    monkeypatch.setattr("urllib.request.urlopen", _no)

    with pytest.raises(LoiCauHinh, match="GEMINI_API_KEY"):
        GeminiProvider(api_key="").tra_loi(model="m", system="S", user="U", timeout=5)


def test_phan_hoi_200_nhung_rong_thi_thanh_loi_co_ten(monkeypatch):
    """Bộ lọc an toàn của Google chặn thì vẫn là 200 — trả chuỗi rỗng ra màn hình là tệ nhất."""
    gia_lap(monkeypatch, tra_ve={"candidates": [{"content": {"parts": []}, "finishReason": "SAFETY"}]})

    with pytest.raises(LoiQuaTai, match="rỗng"):
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)


def test_404_thanh_loi_model_khong_co(monkeypatch):
    """Đã gặp thật 17/09 với `gemini-2.5-flash`."""
    gia_lap(
        monkeypatch,
        loi=loi_http(404, {"error": {"message": "This model is no longer available to new users."}}),
    )

    with pytest.raises(LoiModelKhongCo, match="no longer available"):
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)


def test_429_theo_ngay_doc_duoc_gioi_han_that_va_thoi_gian_cho(monkeypatch):
    gia_lap(
        monkeypatch,
        loi=loi_http(429, {
            "error": {
                "message": "Quota exceeded",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                        "violations": [
                            {
                                "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
                                "quotaValue": "20",
                            }
                        ],
                    },
                    {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "37s"},
                ],
            }
        }),
    )

    with pytest.raises(LoiHetQuota) as loi:
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)

    assert loi.value.theo_ngay is True
    assert loi.value.gioi_han == 20
    assert loi.value.thu_lai_sau == 38


def test_429_theo_phut_khong_bi_hieu_thanh_het_luot_ca_ngay(monkeypatch):
    """Nhầm hai loại này là bỏ oan model tới nửa đêm giờ Pacific."""
    gia_lap(
        monkeypatch,
        loi=loi_http(429, {
            "error": {
                "message": "Rate limit",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                        "violations": [
                            {"quotaId": "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"}
                        ],
                    }
                ],
            }
        }),
    )

    with pytest.raises(LoiHetQuota) as loi:
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)

    assert loi.value.theo_ngay is False
    assert loi.value.gioi_han is None


def test_429_khong_doc_duoc_chi_tiet_thi_doan_ve_phia_nhe(monkeypatch):
    """Không biết thì coi là hết lượt/phút: đoán sai kiểu này chỉ mất vài phút, không mất cả ngày."""
    gia_lap(monkeypatch, loi=loi_http(429, {"error": {"message": "Too many requests"}}))

    with pytest.raises(LoiHetQuota) as loi:
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)

    assert loi.value.theo_ngay is False


def test_503_thanh_loi_qua_tai(monkeypatch):
    """Đã gặp thật 17/09 với `gemini-flash-latest` và `gemini-3.6-flash`."""
    gia_lap(monkeypatch, loi=loi_http(503, {"error": {"message": "high demand"}}))

    with pytest.raises(LoiQuaTai, match="high demand"):
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)


@pytest.mark.parametrize("ma", [400, 401, 403])
def test_loi_khoa_hoac_request_sai_thanh_loi_cau_hinh(monkeypatch, ma):
    """Ba mã này đổi model không cứu được, nên chúng phải khác hẳn nhóm quá tải."""
    gia_lap(monkeypatch, loi=loi_http(ma, {"error": {"message": "API key not valid"}}))

    with pytest.raises(LoiCauHinh):
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)


@pytest.mark.parametrize(
    "ly_do",
    ["getaddrinfo failed", ConnectionRefusedError(10061, "actively refused")],
    ids=["dns", "tu-choi-ket-noi"],
)
def test_mat_mang_thanh_loi_ket_noi_bao_tieng_viet(monkeypatch, ly_do):
    """Vẫn là `LoiQuaTai` để còn kịp thử model khác, nhưng là loại con riêng để không đếm lượt.

    Thông điệp hiện thẳng cho người dùng nên không được lộ chuỗi tiếng Anh của urllib —
    ngày 19/09 trang lỗi từng in nguyên `<urlopen error [WinError 10061] ...>`.
    """
    gia_lap(monkeypatch, loi=urllib.error.URLError(ly_do))

    with pytest.raises(LoiKetNoi) as loi:
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)

    assert isinstance(loi.value, LoiQuaTai)
    assert "Không kết nối được" in str(loi.value)
    assert "urlopen" not in str(loi.value) and "getaddrinfo" not in str(loi.value)


def test_qua_han_cho_do_urllib_boc_lai_van_la_qua_tai_chu_khong_phai_mat_mang(monkeypatch):
    """Quá hạn chờ thì request có thể đã tới server rồi — phải còn được tính lượt."""
    gia_lap(monkeypatch, loi=urllib.error.URLError(TimeoutError("timed out")))

    with pytest.raises(LoiQuaTai) as loi:
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)

    assert not isinstance(loi.value, LoiKetNoi)


def test_qua_han_cho_thanh_loi_qua_tai(monkeypatch):
    gia_lap(monkeypatch, loi=TimeoutError("timed out"))

    with pytest.raises(LoiQuaTai):
        GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)


def test_gui_kem_thinking_budget_theo_cau_hinh(monkeypatch):
    """Đo thật 18/09: bỏ token suy nghĩ giảm độ trễ từ ~6–10s xuống ~2–3s (xem config.py)."""
    from app.config import settings

    monkeypatch.setattr(settings, "gemini_thinking_budget", 0)
    goi = gia_lap(monkeypatch, tra_ve=PHAN_HOI_THAT)

    GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)

    than = json.loads(goi.yeu_cau.data)
    assert than["generationConfig"]["thinkingConfig"]["thinkingBudget"] == 0


def test_thinking_budget_am_thi_de_model_tu_quyet(monkeypatch):
    """Ca biên: -1 nghĩa là không gửi tham số nào, dùng mặc định của model."""
    from app.config import settings

    monkeypatch.setattr(settings, "gemini_thinking_budget", -1)
    goi = gia_lap(monkeypatch, tra_ve=PHAN_HOI_THAT)

    GeminiProvider(api_key="k").tra_loi(model="m", system="S", user="U", timeout=5)

    assert "generationConfig" not in json.loads(goi.yeu_cau.data)
