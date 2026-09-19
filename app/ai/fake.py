"""Nhà cung cấp giả: trả lời cố định, ghi lại mọi lời gọi, và giả lập được lỗi theo model.

Dùng cho toàn bộ test tự động (docs/testing/test-strategy.md mục 3): nhanh, tất định, không
tốn quota. Đây là một trong hai ranh giới ngoài duy nhất được phép thay khi test.

Hai chi tiết quan trọng:

- **Ghi lại `(model, system, user)`** — không có nó thì US-28 ("prompt không chứa dữ liệu cá
  nhân") chỉ là một dòng chữ trong tài liệu, không kiểm chứng được.
- **Cài lỗi theo từng model** — nhờ vậy luật xoay ca model kiểm được bằng provider thật của
  tầng test, không phải bằng cách mock chính hàm đang kiểm (CLAUDE.md mục 7, luật 1).
"""

from dataclasses import dataclass, field

from app.ai.provider import LoiAI


@dataclass
class LoiGoi:
    model: str
    system: str
    user: str


@dataclass
class FakeProvider:
    """`tra_loi` trả `phan_hoi`, hoặc ném lỗi đã cài cho model đó.

    `loi_theo_model` nhận một lỗi (ném mãi) hoặc danh sách lỗi (ném lần lượt, hết thì thôi)
    — danh sách để dựng ca "model quá tải lần đầu, lần sau chạy lại được".
    """

    phan_hoi: str = "Bạn nên tắm cho chó khoảng hai đến bốn tuần một lần."
    phan_hoi_theo_model: dict[str, str] = field(default_factory=dict)
    loi_theo_model: dict[str, LoiAI | list[LoiAI]] = field(default_factory=dict)
    loi_chung: LoiAI | None = None
    da_goi: list[LoiGoi] = field(default_factory=list)
    # Test dùng lớp này ĐÓNG VAI Gemini để kiểm luật xoay ca và đếm lượt, nên mặc định có
    # tính quota. Chế độ AI_PROVIDER=fake của ứng dụng thì tắt — xem service.lay_provider.
    tinh_quota: bool = True

    def tra_loi(self, model: str, system: str, user: str, timeout: float) -> str:
        self.da_goi.append(LoiGoi(model=model, system=system, user=user))

        loi = self.loi_theo_model.get(model, self.loi_chung)
        if isinstance(loi, list):
            loi = loi.pop(0) if loi else None
        if loi is not None:
            raise loi

        return self.phan_hoi_theo_model.get(model, self.phan_hoi)

    @property
    def lan_cuoi(self) -> LoiGoi:
        assert self.da_goi, "Chưa có lời gọi nào tới provider"
        return self.da_goi[-1]

    @property
    def cac_model_da_thu(self) -> list[str]:
        return [g.model for g in self.da_goi]
