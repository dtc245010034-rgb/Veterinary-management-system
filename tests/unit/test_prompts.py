"""Test cho app/ai/prompts.py — dựng prompt và chèn khuyến cáo.

TC-096, TC-088 · docs/ai-safety.md mục 2 và 3. Hàm ở đây thuần nên test không cần CSDL.
"""

import pytest

from app.ai import prompts


def test_moi_tinh_nang_co_system_prompt_rieng_va_dung_gioi_han_cua_no():
    """TC-096: gắn nhầm prompt là tính năng hỏi đáp mất hết giới hạn về thuốc và bệnh."""
    assert set(prompts.SYSTEM_THEO_TINH_NANG) == {"reminder", "summary", "qa"}

    assert "tin nhắn nhắc lịch" in prompts.SYSTEM_THEO_TINH_NANG["reminder"]
    assert "tóm tắt lịch sử chăm sóc" in prompts.SYSTEM_THEO_TINH_NANG["summary"]

    qa = prompts.SYSTEM_THEO_TINH_NANG["qa"]
    assert "KHÔNG chẩn đoán bệnh" in qa
    assert "liều lượng" in qa


def test_system_prompt_hoi_dap_dan_mo_hinh_dung_tu_viet_khuyen_cao():
    """Quyết định Q10: code luôn nối DISCLAIMER, mô hình viết thêm nữa là lặp hai lần."""
    assert "Không tự viết câu khuyến cáo" in prompts.SYSTEM_THEO_TINH_NANG["qa"]


def test_prompt_nhac_lich_hen_neu_du_ten_dich_vu_va_gio():
    """TC-082: thiếu một trong ba thì tin nhắn nhắc thành vô dụng."""
    p = prompts.prompt_nhac_lich_hen(
        {
            "thu_cung": "Mực",
            "loai": "Chó",
            "dich_vu": "Tắm và sấy",
            "bat_dau": "09:00 ngày 20/03/2026",
            "ghi_chu": "",
        }
    )

    assert "Mực" in p and "Tắm và sấy" in p and "09:00 ngày 20/03/2026" in p


def test_prompt_nhac_lich_hen_bo_dong_ghi_chu_khi_khong_co():
    """Ca biên: dòng "Ghi chú: " rỗng chỉ làm mô hình bịa ra nội dung cho nó."""
    p = prompts.prompt_nhac_lich_hen(
        {"thu_cung": "Mực", "loai": "Chó", "dich_vu": "Tắm", "bat_dau": "09:00", "ghi_chu": ""}
    )

    assert "Ghi chú" not in p


def test_prompt_nhac_lich_tiem_neu_vac_xin_va_han_nhac():
    """TC-083."""
    p = prompts.prompt_nhac_lich_tiem(
        {
            "thu_cung": "Mun",
            "loai": "Mèo",
            "vac_xin": "Dại",
            "ngay_tiem": "01/03/2025",
            "han_nhac": "01/03/2026",
        }
    )

    assert "Dại" in p and "01/03/2026" in p


def test_prompt_tom_tat_liet_ke_tung_ho_so_theo_ngay():
    p = prompts.prompt_tom_tat(
        {"ten": "Mực", "loai": "Chó"},
        [
            {"ngay": "01/03/2026", "dich_vu": "Tắm", "tinh_trang": "Da khô", "dan_do": "Dưỡng ẩm"},
            {"ngay": "10/03/2026", "dich_vu": "Cắt móng", "tinh_trang": "Bình thường"},
        ],
    )

    assert "Mực" in p
    assert "01/03/2026" in p and "10/03/2026" in p
    assert "Da khô" in p and "Dưỡng ẩm" in p


def test_them_disclaimer_noi_dung_cau_khuyen_cao_chuan():
    """TC-088: chèn ở tầng code, không phụ thuộc mô hình có nghe lời hay không."""
    ket_qua = prompts.them_disclaimer("Tắm 2 tuần một lần.")

    assert ket_qua.startswith("Tắm 2 tuần một lần.")
    assert ket_qua.endswith(prompts.DISCLAIMER)


def test_them_disclaimer_khong_lap_lai_khi_da_co_san():
    """Ca biên: mô hình đã tự chép đúng câu khuyến cáo thì đừng dán thêm lần nữa."""
    goc = f"Tắm 2 tuần một lần.\n\n{prompts.DISCLAIMER}"

    assert prompts.them_disclaimer(goc) == goc


@pytest.mark.parametrize("goc", ["", "   ", None])
def test_them_disclaimer_vao_noi_dung_rong_thi_chi_con_khuyen_cao(goc):
    assert prompts.them_disclaimer(goc) == prompts.DISCLAIMER


def test_cau_tu_choi_thuoc_khong_chua_ten_thuoc_hay_lieu():
    """Câu từ chối mà lỡ nêu tên thuốc thì chính nó thành lời khuyên dùng thuốc."""
    from app.ai import guardrail

    assert guardrail.chua_lieu_luong(prompts.TU_CHOI_THUOC) is False
    assert "bác sĩ thú y" in prompts.TU_CHOI_THUOC
