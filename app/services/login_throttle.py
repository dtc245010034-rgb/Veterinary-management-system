"""Giới hạn đăng nhập sai theo cặp (IP, tên đăng nhập) — R-1, rà soát 02/10.

Sai MIEN_PHI lần liên tiếp thì bị khóa KHOA_DAU_GIAY giây; mỗi lần sai tiếp sau khi hết khóa, thời
gian khóa gấp đôi, tối đa KHOA_TOI_DA_GIAY. Đăng nhập đúng thì xóa bộ đếm.

Khóa theo CẶP chứ không riêng tên đăng nhập: khóa theo tên thì kẻ lạ gõ sai `quanly` là khóa được
quản lý thật. Đánh đổi chấp nhận: nhiều người chung một IP (NAT) chia nhau độ trễ của cùng một tên.

Lưu trong bộ nhớ tiến trình, không ra CSDL: khởi động lại thì bộ đếm về 0 (đủ cho một worker SQLite),
và bước kiểm tra không tốn truy vấn nào. Chạy nhiều worker thì mỗi worker đếm riêng — chưa phải
trường hợp của dự án này.

Không import fastapi.
"""

import math
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services import clock

MIEN_PHI = 5
KHOA_DAU_GIAY = 30
KHOA_TOI_DA_GIAY = 900
# Sai rải rác cách nhau quá lâu thì không cộng dồn: gõ nhầm 4 lần mỗi tuần không phải tấn công.
QUEN_SAU_GIAY = 3600
TOI_DA_MUC_NHO = 10_000


def tao_khoa(ip: str, ten_dang_nhap: str) -> tuple[str, str]:
    return (ip, ten_dang_nhap.strip().lower())


@dataclass
class _Muc:
    so_lan_sai: int = 0
    lan_cuoi: datetime | None = None
    khoa_den: datetime | None = None


class GioiHanDangNhap:
    def __init__(self) -> None:
        self._muc: dict[tuple[str, str], _Muc] = {}
        self._khoa_luong = threading.Lock()

    def con_phai_cho(self, khoa: tuple[str, str]) -> int:
        """Số giây còn phải chờ (làm tròn lên); 0 nghĩa là được thử. Chỉ đọc, không kéo dài khóa."""
        with self._khoa_luong:
            muc = self._muc.get(khoa)
            if muc is None or muc.khoa_den is None:
                return 0
            con_lai = (muc.khoa_den - clock.now()).total_seconds()
            return max(0, math.ceil(con_lai))

    def ghi_that_bai(self, khoa: tuple[str, str]) -> None:
        with self._khoa_luong:
            bay_gio = clock.now()
            self._don_dep(bay_gio)
            muc = self._muc.setdefault(khoa, _Muc())
            if muc.lan_cuoi is not None and bay_gio - muc.lan_cuoi > timedelta(seconds=QUEN_SAU_GIAY):
                muc.so_lan_sai = 0
            muc.so_lan_sai += 1
            muc.lan_cuoi = bay_gio
            if muc.so_lan_sai >= MIEN_PHI:
                nac = min(muc.so_lan_sai - MIEN_PHI, 20)
                giay = min(KHOA_DAU_GIAY * 2**nac, KHOA_TOI_DA_GIAY)
                muc.khoa_den = bay_gio + timedelta(seconds=giay)

    def xoa(self, khoa: tuple[str, str]) -> None:
        with self._khoa_luong:
            self._muc.pop(khoa, None)

    def reset(self) -> None:
        with self._khoa_luong:
            self._muc.clear()

    def _don_dep(self, bay_gio: datetime) -> None:
        if len(self._muc) < TOI_DA_MUC_NHO:
            return
        han = timedelta(seconds=QUEN_SAU_GIAY)
        for k in [k for k, m in self._muc.items() if m.lan_cuoi is None or bay_gio - m.lan_cuoi > han]:
            del self._muc[k]


gioi_han_dang_nhap = GioiHanDangNhap()
