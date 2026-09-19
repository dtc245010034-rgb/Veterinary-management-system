"""Ba tính năng AI, lọc dữ liệu cá nhân, chèn khuyến cáo và ghi nhật ký.

Đây là **cửa duy nhất** router được gọi (CLAUDE.md mục 8, có phép canh trong
tests/unit/test_architecture.py). Gọi thẳng `gemini.py` từ router là bỏ qua cả ba việc nói
trên cùng một lúc.

Thứ tự bên trong mỗi tính năng luôn là:

1. Kiểm dữ liệu — thiếu dữ liệu thì **không gọi API** (ca G-20).
2. Dựng dict tối thiểu: chỉ các trường được phép, văn bản tự do đã lọc liên hệ (US-28).
3. Gọi AI qua `quota.goi_co_xoay` — có xoay ca model.
4. Hậu kiểm phản hồi, chèn khuyến cáo.
5. Ghi `ai_logs`, kể cả khi lỗi (ca G-18).
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ai import guardrail, prompts, quota
from app.ai.fake import FakeProvider
from app.ai.provider import AIProvider, LoiAI
from app.config import settings
from app.models.ai_log import AiLog
from app.models.appointment import Appointment
from app.models.pet import Pet
from app.models.vaccination import Vaccination
from app.services import care_records, clock
from app.services.errors import LoiKhongTimThay, LoiNghiepVu
from app.services.scheduling import TRANG_THAI_SUA_DUOC

# Số hồ sơ đưa vào một prompt tóm tắt. Con vật nuôi mười năm có thể có hàng trăm buổi; gửi
# hết vừa tốn token vừa làm loãng phần mới nhất, mà nhân viên tra cứu cần đúng phần đó.
SO_HO_SO_TOM_TAT = 20


@dataclass(frozen=True)
class KetQuaAI:
    noi_dung: str
    model: str | None  # None khi không có lời gọi nào đi ra
    log_id: int


def lay_provider() -> AIProvider:
    """Dependency của FastAPI. `AI_PROVIDER=gemini` mới gọi API thật.

    Test override dependency này bằng `FakeProvider`, nên bộ test không bao giờ chạm mạng.
    """
    if settings.ai_provider == "gemini":
        from app.ai.gemini import GeminiProvider

        return GeminiProvider()
    return FakeProvider(tinh_quota=False)


# --- Ba tính năng -----------------------------------------------------------------


def nhac_lich_hen(db: Session, provider: AIProvider, nguoi_dung_id: int, lich_id: int) -> KetQuaAI:
    """US-24: soạn nháp tin nhắn nhắc một lịch hẹn sắp tới."""
    lich = db.get(Appointment, lich_id)
    if lich is None:
        raise LoiKhongTimThay("Không tìm thấy lịch hẹn.")
    if lich.status not in TRANG_THAI_SUA_DUOC:
        raise LoiNghiepVu(
            f"Lịch ở trạng thái “{lich.ten_trang_thai}” nên không cần nhắc nữa."
        )
    if lich.start_at < clock.now():
        raise LoiNghiepVu("Buổi này đã qua giờ hẹn, không nhắc nữa.")

    ngu_canh = {
        "thu_cung": lich.pet.name,
        "loai": lich.pet.species,
        "dich_vu": lich.service.name,
        "bat_dau": f"{lich.start_at:%H:%M ngày %d/%m/%Y}",
        "ghi_chu": guardrail.xoa_lien_he(lich.note),
    }
    return _goi(
        db, provider, nguoi_dung_id,
        tinh_nang="reminder",
        prompt=prompts.prompt_nhac_lich_hen(ngu_canh),
    )


def nhac_lich_tiem(db: Session, provider: AIProvider, nguoi_dung_id: int, mui_id: int) -> KetQuaAI:
    """US-24: soạn nháp tin nhắn nhắc một mũi tiêm tới hạn.

    Nối sẵn câu khuyên xác nhận lịch tiêm với bác sĩ thú y: đây là tin nhắn gửi cho khách,
    và hệ thống chỉ nhắc lại ngày người dùng đã ghi, không phải chỉ định y tế (US-17).
    """
    mui = db.get(Vaccination, mui_id)
    if mui is None:
        raise LoiKhongTimThay("Không tìm thấy mũi tiêm.")
    if mui.next_due_at is None:
        raise LoiNghiepVu("Mũi tiêm này không có hạn nhắc lại nên không soạn nhắc được.")

    ngu_canh = {
        "thu_cung": mui.pet.name,
        "loai": mui.pet.species,
        "vac_xin": mui.vaccine_name,
        "ngay_tiem": f"{mui.given_at:%d/%m/%Y}",
        "han_nhac": f"{mui.next_due_at:%d/%m/%Y}",
    }
    ket_qua = _goi(
        db, provider, nguoi_dung_id,
        tinh_nang="reminder",
        prompt=prompts.prompt_nhac_lich_tiem(ngu_canh),
    )
    return _them_cau_nhac_tiem(db, ket_qua)


def tom_tat_ho_so(db: Session, provider: AIProvider, nguoi_dung_id: int, thu_cung_id: int) -> KetQuaAI:
    """US-25: tóm tắt lịch sử chăm sóc. Chưa có hồ sơ thì KHÔNG gọi API (ca G-20)."""
    thu_cung = db.get(Pet, thu_cung_id)
    if thu_cung is None:
        raise LoiKhongTimThay("Không tìm thấy thú cưng.")

    ho_so = care_records.lich_su(db, thu_cung_id)[:SO_HO_SO_TOM_TAT]
    if not ho_so:
        raise LoiNghiepVu(
            f"“{thu_cung.name}” chưa có hồ sơ chăm sóc nào nên chưa đủ dữ liệu để tóm tắt."
        )

    prompt = prompts.prompt_tom_tat(
        {"ten": thu_cung.name, "loai": thu_cung.species},
        [
            {
                "ngay": f"{h.performed_at:%d/%m/%Y}",
                "dich_vu": h.lich_hen.service.name,
                "tinh_trang": guardrail.xoa_lien_he(h.condition_note),
                "viec_da_lam": guardrail.xoa_lien_he(h.actions_taken),
                "dan_do": guardrail.xoa_lien_he(h.next_advice),
            }
            for h in ho_so
        ],
    )
    return _goi(db, provider, nguoi_dung_id, tinh_nang="summary", prompt=prompt, khuyen_cao=True)


def hoi_dap(
    db: Session,
    provider: AIProvider,
    nguoi_dung_id: int,
    cau_hoi: str,
    ghim_model: str | None = None,
) -> KetQuaAI:
    """US-26, US-27: trả lời câu hỏi chăm sóc thường ngày.

    Câu xin thuốc hoặc liều bị từ chối **trước khi gọi API**: không gửi đi thì không phụ
    thuộc việc mô hình có nghe lời hay không (ca G-08 → G-10, G-13).
    """
    cau_hoi = guardrail.xoa_lien_he(cau_hoi)
    if not cau_hoi:
        raise LoiNghiepVu("Chưa nhập câu hỏi.")

    if guardrail.la_cau_xin_thuoc(cau_hoi):
        log = _ghi_log(
            db, nguoi_dung_id, "qa", cau_hoi,
            phan_hoi=prompts.them_disclaimer(prompts.TU_CHOI_THUOC),
        )
        return KetQuaAI(noi_dung=log.response, model=None, log_id=log.id)

    return _goi(
        db, provider, nguoi_dung_id,
        tinh_nang="qa", prompt=cau_hoi, khuyen_cao=True, ghim_model=ghim_model,
    )


# --- Dùng chung -------------------------------------------------------------------


def _goi(
    db: Session,
    provider: AIProvider,
    nguoi_dung_id: int,
    tinh_nang: str,
    prompt: str,
    khuyen_cao: bool = False,
    ghim_model: str | None = None,
) -> KetQuaAI:
    """Gọi AI, hậu kiểm, ghi log. Lỗi AI vẫn để lại một dòng log rồi mới ném lên.

    `ghim_model` chỉ dùng cho lệnh chạy bộ ca guardrail: cả lượt chạy phải do cùng một model
    trả lời thì bảng kết quả mới so sánh được model nào tuân thủ tới đâu.
    """
    try:
        noi_dung, model = quota.goi_co_xoay(
            db, provider,
            system=prompts.SYSTEM_THEO_TINH_NANG[tinh_nang],
            user=prompt,
            ghim_model=ghim_model,
        )
    except LoiAI:
        _ghi_log(db, nguoi_dung_id, tinh_nang, prompt, phan_hoi=None, loi=True)
        raise

    if guardrail.chua_lieu_luong(noi_dung):
        # Mô hình vượt rào: thay cả phản hồi thay vì cắt bớt. Cắt bớt thì phần còn lại vẫn
        # là lời khuyên y tế đứt đoạn, đọc còn nguy hiểm hơn.
        noi_dung = prompts.TU_CHOI_THUOC
        khuyen_cao = True

    if khuyen_cao:
        noi_dung = prompts.them_disclaimer(noi_dung)

    log = _ghi_log(db, nguoi_dung_id, tinh_nang, prompt, phan_hoi=noi_dung, model=model)
    return KetQuaAI(noi_dung=noi_dung, model=model, log_id=log.id)


def _them_cau_nhac_tiem(db: Session, ket_qua: KetQuaAI) -> KetQuaAI:
    if prompts.NHAC_XAC_NHAN_TIEM in ket_qua.noi_dung:
        return ket_qua

    noi_dung = f"{ket_qua.noi_dung}\n\n{prompts.NHAC_XAC_NHAN_TIEM}"
    log = db.get(AiLog, ket_qua.log_id)
    log.response = noi_dung
    db.commit()
    return KetQuaAI(noi_dung=noi_dung, model=ket_qua.model, log_id=ket_qua.log_id)


def _ghi_log(
    db: Session,
    nguoi_dung_id: int,
    tinh_nang: str,
    prompt: str,
    phan_hoi: str | None,
    model: str | None = None,
    loi: bool = False,
) -> AiLog:
    log = AiLog(
        user_id=nguoi_dung_id,
        feature=tinh_nang,
        prompt=prompt,
        response=phan_hoi,
        is_error=loi,
        model=model,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# --- Cho trang quản lý và CLI -------------------------------------------------------


def bang_quota(db: Session) -> list[quota.DongQuota]:
    return quota.bang_quota(db)


def moc_reset_ke_tiep():
    return quota.moc_reset_ke_tiep()


def dat_lai_quota(db: Session) -> int:
    return quota.dat_lai(db)


def lay_log(db: Session, log_id: int) -> AiLog:
    log = db.get(AiLog, log_id)
    if log is None:
        raise LoiKhongTimThay("Không tìm thấy kết quả AI này.")
    return log
