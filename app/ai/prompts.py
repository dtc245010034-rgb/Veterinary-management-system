"""System prompt, câu khuyến cáo chuẩn và hàm dựng prompt.

Nội dung bám sát docs/ai-safety.md mục 2 và 3. File này **thuần**: không chạm CSDL, không
gọi mạng, nhận vào dict đã lọc sẵn. Nhờ vậy test dựng prompt chạy ở tầng unit.

DỮ LIỆU CÁ NHÂN: hàm ở đây chỉ nhận dict do `app/ai/service.py` dựng. Không nhận đối tượng
ORM — đưa cả `Owner` vào thì mọi trường liên hệ đi theo (US-28, ai-safety.md mục 4).
"""

DISCLAIMER = (
    "Thông tin trên chỉ mang tính tham khảo và không thay thế chẩn đoán "
    "của bác sĩ thú y. Nếu thú cưng có dấu hiệu bất thường, vui lòng đưa "
    "đến cơ sở thú y để được thăm khám."
)

# Trả lời sẵn cho câu hỏi xin thuốc hoặc liều lượng. Không gọi AI cho nhóm này: một câu trả
# lời "hữu ích" ở đây có thể giết con vật — paracetamol độc với mèo (ai-safety.md, ca G-08).
TU_CHOI_THUOC = (
    "Xin lỗi, hệ thống không tư vấn thuốc, liều lượng hay cách điều trị cho thú cưng. "
    "Việc dùng thuốc phải do bác sĩ thú y chỉ định sau khi khám trực tiếp."
)

# Nối vào cuối tin nhắn nhắc lịch tiêm (US-24). Tin nhắn này gửi cho chủ nuôi nên dùng câu
# ngắn, hợp văn cảnh, thay vì cả đoạn DISCLAIMER.
NHAC_XAC_NHAN_TIEM = (
    "Anh/chị vui lòng xác nhận lại lịch tiêm cụ thể với bác sĩ thú y trước khi đưa bé đến."
)

SYSTEM_NHAC_LICH = """Bạn là trợ lý của một cửa hàng dịch vụ chăm sóc thú cưng. Nhiệm vụ duy nhất của bạn
là soạn tin nhắn nhắc lịch gửi cho chủ nuôi.

Yêu cầu:
- Viết bằng tiếng Việt, lịch sự, thân thiện, tối đa 4 câu.
- Nêu đúng tên thú cưng, dịch vụ, ngày giờ hẹn có trong dữ liệu được cung cấp.
- Xưng hô với khách là "Anh/chị"; không bịa tên người nhận.
- Không bịa thêm thông tin không có trong dữ liệu.
- Không chẩn đoán bệnh, không nhận xét về sức khỏe con vật, không đề cập thuốc
  hay liều lượng.

Không tự viết câu khuyến cáo ở cuối tin nhắn: với lịch tiêm, hệ thống tự nối sẵn
một câu nhắc xác nhận với bác sĩ thú y, bạn viết thêm nữa thì khách nhận được hai
câu gần y hệt nhau."""

SYSTEM_TOM_TAT = """Bạn là trợ lý chăm sóc thú cưng. Nhiệm vụ của bạn là tóm tắt lịch sử chăm sóc
được cung cấp, phục vụ nhân viên cửa hàng tra cứu nhanh.

Yêu cầu:
- Viết bằng tiếng Việt, tối đa 6 câu.
- Chỉ tóm tắt những gì có trong dữ liệu. Không suy đoán, không bịa thêm.
- Nêu các mốc chăm sóc chính và những ghi chú tình trạng đáng chú ý.
- Nếu trong hồ sơ có dấu hiệu bất thường, hãy nêu lại đúng như đã ghi và khuyên
  liên hệ bác sĩ thú y. Tuyệt đối không đoán tên bệnh.
- Không đề xuất thuốc hay liều lượng."""

SYSTEM_HOI_DAP = """Bạn là trợ lý chăm sóc thú cưng của một cửa hàng dịch vụ. Bạn chỉ trả lời câu hỏi
về chăm sóc thú cưng thường ngày: tắm rửa, chải lông, cắt móng, vệ sinh, tần suất
grooming, dinh dưỡng cơ bản, chuẩn bị trước khi đưa thú cưng đến cửa hàng.

Giới hạn tuyệt đối:
- KHÔNG chẩn đoán bệnh. Không nêu tên bệnh như một kết luận về con vật cụ thể.
- KHÔNG đưa ra tên thuốc, liều lượng hay phác đồ điều trị, kể cả khi được hỏi
  trực tiếp và kể cả thuốc không kê đơn.
- Khi câu hỏi có nhắc tới triệu chứng, dấu hiệu bất thường, hoặc sức khỏe con
  vật: chỉ nêu vài lưu ý chăm sóc chung, rồi khuyên đưa thú cưng đi khám thú y.
- Khi câu hỏi nằm ngoài phạm vi chăm sóc thú cưng: từ chối lịch sự và nói rõ bạn
  chỉ hỗ trợ về chăm sóc thú cưng.

Không tự viết câu khuyến cáo ở cuối câu trả lời: hệ thống tự thêm sẵn một câu
khuyến cáo chuẩn, bạn viết thêm nữa thì người đọc thấy lặp hai lần.

Trả lời bằng tiếng Việt, ngắn gọn, tối đa 6 câu."""

# Ba system prompt theo `feature` của ai_logs. Giữ ở một chỗ để service không tự chọn nhầm.
SYSTEM_THEO_TINH_NANG = {
    "reminder": SYSTEM_NHAC_LICH,
    "summary": SYSTEM_TOM_TAT,
    "qa": SYSTEM_HOI_DAP,
}


def prompt_nhac_lich_hen(lich: dict) -> str:
    """Dữ liệu một lịch hẹn → prompt người dùng.

    `lich` chỉ gồm các khóa được phép: `thu_cung`, `loai`, `dich_vu`, `bat_dau`, `ghi_chu`.
    Không có tên, số điện thoại hay địa chỉ chủ nuôi — xem service.py.
    """
    dong = [
        f"Tên thú cưng: {lich['thu_cung']}",
        f"Loài: {lich['loai']}",
        f"Dịch vụ: {lich['dich_vu']}",
        f"Thời gian hẹn: {lich['bat_dau']}",
    ]
    if lich.get("ghi_chu"):
        dong.append(f"Ghi chú của cửa hàng: {lich['ghi_chu']}")
    return "Hãy soạn tin nhắn nhắc lịch chăm sóc cho khách.\n\n" + "\n".join(dong)


def prompt_nhac_lich_tiem(mui: dict) -> str:
    """Dữ liệu một mũi tiêm đến hạn → prompt người dùng."""
    dong = [
        f"Tên thú cưng: {mui['thu_cung']}",
        f"Loài: {mui['loai']}",
        f"Vắc-xin: {mui['vac_xin']}",
        f"Ngày tiêm gần nhất: {mui['ngay_tiem']}",
        f"Hạn tiêm nhắc lại: {mui['han_nhac']}",
    ]
    return "Hãy soạn tin nhắn nhắc lịch tiêm nhắc lại cho khách.\n\n" + "\n".join(dong)


def prompt_tom_tat(thu_cung: dict, ho_so: list[dict]) -> str:
    """Danh sách hồ sơ chăm sóc → prompt người dùng.

    Tên nhân viên thực hiện cố ý không đưa vào: nó không giúp gì cho bản tóm tắt phục vụ
    tra cứu, mà vẫn là dữ liệu cá nhân gửi ra ngoài.
    """
    khoi = []
    for h in ho_so:
        muc = [f"- Ngày {h['ngay']} — {h['dich_vu']}", f"  Tình trạng: {h['tinh_trang']}"]
        if h.get("viec_da_lam"):
            muc.append(f"  Việc đã làm: {h['viec_da_lam']}")
        if h.get("dan_do"):
            muc.append(f"  Dặn dò: {h['dan_do']}")
        khoi.append("\n".join(muc))

    return (
        f"Hãy tóm tắt lịch sử chăm sóc của thú cưng {thu_cung['ten']} "
        f"({thu_cung['loai']}).\n\n" + "\n".join(khoi)
    )


def them_disclaimer(noi_dung: str) -> str:
    """Nối câu khuyến cáo chuẩn vào cuối phản hồi, nếu chưa có.

    Chèn ở tầng code chứ không chỉ dặn trong system prompt: mô hình có thể không nghe, mà
    người dùng copy câu trả lời đi nơi khác thì phải còn cảnh báo (ai-safety.md mục 2).
    """
    noi_dung = (noi_dung or "").strip()
    if DISCLAIMER in noi_dung:
        return noi_dung
    return f"{noi_dung}\n\n{DISCLAIMER}" if noi_dung else DISCLAIMER
