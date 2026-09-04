"""Lỗi nghiệp vụ dùng chung cho tầng services.

Tách khỏi lỗi HTTP và lỗi CSDL: router bắt LoiNghiepVu và trả 400 kèm đúng thông báo
tiếng Việt trong đó, thay vì để IntegrityError của SQLAlchemy đi thẳng ra thành lỗi 500.
"""


class LoiNghiepVu(Exception):
    """Dữ liệu hoặc thao tác vi phạm quy tắc nghiệp vụ.

    Thông điệp của lớp này được hiển thị thẳng cho người dùng, nên phải viết bằng tiếng
    Việt và nói rõ phải làm gì tiếp.
    """
