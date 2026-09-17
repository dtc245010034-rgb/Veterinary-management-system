"""Ba phép chặn nằm trong code, không phụ thuộc mô hình có nghe lời hay không.

docs/ai-safety.md mục 6 nói rõ giới hạn: system prompt là lời dặn, không phải bảo đảm. Ba
hàm ở đây là phần kiểm soát được, nên chúng phải đứng độc lập và có test riêng:

1. `la_cau_xin_thuoc` — chặn TRƯỚC khi gọi API. Câu xin thuốc không được gửi đi.
2. `chua_lieu_luong` — soát phản hồi. Mô hình lỡ đưa liều thì cả phản hồi bị thay.
3. `xoa_lien_he` — bỏ số điện thoại và email khỏi mọi văn bản tự do trước khi vào prompt.

So khớp trên chuỗi đã bỏ dấu (`services/text.chuan_hoa`) để "liều" và "lieu" như nhau, và
so theo TỪ NGUYÊN VẸN: so kiểu chứa chuỗi thì "viên" khớp luôn "nhân viên" và câu hỏi hợp
lệ bị chặn oan.
"""

import re

from app.services.text import chuan_hoa

# Từ đơn: chỉ cần xuất hiện là câu hỏi đã sang địa hạt thuốc men.
TU_THUOC = frozenset(
    """thuoc lieu paracetamol ibuprofen aspirin amoxicillin ivermectin
    dexamethasone corticoid vaccine""".split()
)

# Cụm từ: so trên chuỗi đã chuẩn hóa, có khoảng trắng hai đầu nên không dính vào từ khác.
CUM_THUOC = (
    "khang sinh", "an than", "giam dau", "ha sot", "tri ghe", "tay giun",
    "don thuoc", "ke don", "dieu tri",
)

# Số kèm đơn vị liều. \b không đủ cho tiếng Việt đã bỏ dấu nên chặn hai đầu bằng ranh giới
# từ của chính đơn vị: "2 vien" khớp, "nhan vien" không.
SO_KEM_LIEU = re.compile(r"\d+([.,]\d+)?\s*(mg|ml|cc|g|vien|giot|ong)\b")

# "mấy viên", "bao nhiêu ml" — hỏi liều mà không kèm con số. KHÔNG có "lần": "chải lông mấy
# lần một tuần" là câu chăm sóc thường ngày, còn "uống mấy lần" đã dính từ "thuốc" rồi.
HOI_LIEU = re.compile(r"(may|bao nhieu)\s+(vien|mg|ml|cc|giot|ong)\b")

SO_DIEN_THOAI = re.compile(r"(?<!\d)(\+?\d[\d\s.\-]{7,}\d)(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

DA_LUOC_BO = "[đã lược bỏ]"


def _tu(chuoi: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", chuan_hoa(chuoi)))


def la_cau_xin_thuoc(cau_hoi: str) -> bool:
    """Câu hỏi có xin thuốc, liều lượng hay cách điều trị không? — ca G-08 → G-10, G-13.

    Cố ý chặn rộng: "thuốc tẩy giun bao lâu một lần" cũng bị từ chối. Nhầm về phía từ chối
    thì khách được khuyên đi hỏi bác sĩ thú y; nhầm về phía trả lời thì hệ thống đang tư vấn
    y tế. Hai loại nhầm đó không cùng hạng.
    """
    chuoi = chuan_hoa(cau_hoi)
    if TU_THUOC & _tu(chuoi):
        return True
    if any(cum in chuoi for cum in CUM_THUOC):
        return True
    return bool(SO_KEM_LIEU.search(chuoi) or HOI_LIEU.search(chuoi))


def chua_lieu_luong(noi_dung: str) -> bool:
    """Phản hồi có con số kèm đơn vị liều không? — TC-093.

    Chạy trên MỌI phản hồi, kể cả tóm tắt hồ sơ: nhân viên có thể đã chép liều thuốc vào ghi
    chú, và bản tóm tắt nhắc lại nó thì hệ thống vẫn đang phát tán liều lượng.
    """
    return bool(SO_KEM_LIEU.search(chuan_hoa(noi_dung)))


def xoa_lien_he(van_ban: str | None) -> str:
    """Bỏ chuỗi giống số điện thoại và email khỏi văn bản tự do — US-28, ca G-14 → G-16.

    Dùng cho ghi chú hồ sơ, ghi chú thú cưng và câu hỏi lễ tân gõ: những chỗ người dùng có
    thể vô tình gõ số của khách. Trường liên hệ trong CSDL thì không bao giờ đi vào prompt —
    service.py chỉ lấy đúng các trường được phép.

    GIỚI HẠN ĐÃ BIẾT: địa chỉ nhà không có dạng nhận ra được bằng biểu thức chính quy, nên
    nó không bị lọc ở đây. Lớp chặn thật cho địa chỉ là việc không đưa trường `address` vào.
    """
    if not van_ban:
        return ""
    return SO_DIEN_THOAI.sub(DA_LUOC_BO, EMAIL.sub(DA_LUOC_BO, van_ban)).strip()
