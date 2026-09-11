"""Test hook của agent trong `.claude/hooks/` — thứ giữ cho log phiên không thành rác.

Hook là PowerShell nên test chạy thẳng script thật trên một bản sao dự án dựng trong
thư mục tạm: hook tự tìm thư mục gốc từ vị trí của chính nó (`..\\..`), nên chép nó vào
`<tạm>/.claude/hooks/` là nó làm việc trên `<tạm>/docs/sessions/`, không đụng repo thật.
"""

import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]

# Hook là PowerShell; máy không có PowerShell thì không có gì để chạy. Đây là giới hạn
# nền tảng chứ không phải skip để lấy màu xanh — dự án chạy trên Windows.
can_powershell = pytest.mark.skipif(
    shutil.which("powershell") is None, reason="Máy không có PowerShell để chạy hook"
)

# Khung log y như hook SessionStart tạo: 5 ô chưa ghi.
KHUNG_RONG = """# Phien {ten}

- **Ngay:** 2026-09-01
- **Muc tieu phien:** _(chua ghi)_

## Quyet dinh

_(chua ghi)_

## File da thay doi

_(chua ghi)_

## Ket qua test

_(chua ghi)_

## Con do / phien sau lam gi

_(chua ghi)_
"""


def _chay_hook_dong_phien(goc_tam: Path) -> None:
    thu_muc_hook = goc_tam / ".claude" / "hooks"
    thu_muc_hook.mkdir(parents=True)
    ban_sao = thu_muc_hook / "session-stop.ps1"
    shutil.copy(GOC / ".claude" / "hooks" / "session-stop.ps1", ban_sao)

    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ban_sao)],
        check=True,
        capture_output=True,
        timeout=60,
    )


@can_powershell
def test_hook_dong_phien_don_moi_log_rong_khong_chi_file_moi_nhat(tmp_path):
    """Lỗi thật 11/09: hook chỉ xét file log MỚI NHẤT của hôm nay.

    Một lần mở phiên không có lượt nào (chỉ gõ `/plugin`, `/model`) để lại
    `2026-09-11-01.md` rỗng; phiên sau tạo `-02`, và hook chỉ nhìn `-02` nên file rỗng
    kia nằm lại mãi — làm phép canh đếm log phiên trong test_architecture.py đỏ.
    """
    phien = tmp_path / "docs" / "sessions"
    phien.mkdir(parents=True)
    hom_nay = date.today().isoformat()

    rong_ngay_cu = phien / "2026-09-01-01.md"
    rong_hom_nay = phien / f"{hom_nay}-01.md"
    da_dien = phien / f"{hom_nay}-02.md"
    # Ca biên: log mới điền một phần vẫn là công việc thật, không được xóa.
    dien_do = phien / "2026-09-02-01.md"
    quy_uoc = phien / "README.md"

    rong_ngay_cu.write_text(KHUNG_RONG.format(ten="2026-09-01-01"), encoding="utf-8")
    rong_hom_nay.write_text(KHUNG_RONG.format(ten=f"{hom_nay}-01"), encoding="utf-8")
    da_dien.write_text("# Phien\n\nDa ghi day du.\n", encoding="utf-8")
    dien_do.write_text(
        KHUNG_RONG.format(ten="2026-09-02-01").replace("_(chua ghi)_", "Da ghi", 3),
        encoding="utf-8",
    )
    quy_uoc.write_text("# Quy uoc\n", encoding="utf-8")

    _chay_hook_dong_phien(tmp_path)

    con_lai = sorted(p.name for p in phien.iterdir())
    assert con_lai == sorted([da_dien.name, dien_do.name, quy_uoc.name]), con_lai
