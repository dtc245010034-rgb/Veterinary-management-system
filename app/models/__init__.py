"""Gom mọi model vào một chỗ.

Base.metadata.create_all() chỉ tạo những bảng đã đăng ký vào metadata, mà việc đăng ký
xảy ra lúc module model được import. Nếu chỗ gọi create_all không import đủ model, bảng
sẽ thiếu và lỗi chỉ lộ ra khi truy vấn tới bảng đó — thông báo "no such table" không nói
gì về nguyên nhân thật.

Import ở đây một lần để mọi nơi chỉ cần `import app.models`.
"""

from app.models.ai_log import AiLog
from app.models.ai_quota import AiQuota
from app.models.appointment import Appointment
from app.models.care_record import CareRecord
from app.models.invoice import Invoice, InvoiceItem
from app.models.owner import Owner
from app.models.payment import Payment
from app.models.pet import Pet
from app.models.service import Service
from app.models.service_package import PackageItem, ServicePackage
from app.models.user import User
from app.models.vaccination import Vaccination

__all__ = [
    "AiLog",
    "AiQuota",
    "Appointment",
    "CareRecord",
    "Invoice",
    "InvoiceItem",
    "Owner",
    "Payment",
    "PackageItem",
    "Pet",
    "Service",
    "ServicePackage",
    "User",
    "Vaccination",
]
