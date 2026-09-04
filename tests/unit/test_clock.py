"""Test cho app/services/clock.py — điểm lấy thời gian duy nhất của hệ thống.

Mọi nơi cần "bây giờ" phải gọi clock.now() thay vì datetime.now(). Nhờ vậy test cố định
được thời gian, và các ca phụ thuộc ngày ở P3 (đặt lịch trong quá khứ) cùng P4 (đến hạn
tiêm trong 30 ngày) viết được ổn định, không phụ thuộc ngày chạy test.

Theo CLAUDE.md mục 7, thời gian hệ thống là một trong hai ranh giới ngoài duy nhất được
phép thay thế khi test.
"""

from datetime import datetime, timedelta

from app.services import clock


def test_now_tra_ve_thoi_diem_hien_tai():
    truoc = datetime.now()
    ket_qua = clock.now()
    sau = datetime.now()

    assert truoc <= ket_qua <= sau


def test_trong_freeze_now_tra_ve_dung_moc_da_dat():
    moc = datetime(2026, 1, 15, 9, 30)

    with clock.freeze(moc):
        assert clock.now() == moc


def test_freeze_giu_nguyen_moc_qua_nhieu_lan_goi():
    """Cùng một lần freeze, mọi lời gọi now() phải cho cùng giá trị.

    Nếu không, một hàm nghiệp vụ gọi now() hai lần sẽ thấy hai thời điểm khác nhau
    và test trở nên chập chờn.
    """
    moc = datetime(2026, 1, 15, 9, 30)

    with clock.freeze(moc):
        lan_1 = clock.now()
        lan_2 = clock.now()

    assert lan_1 == lan_2 == moc


def test_ra_khoi_freeze_thoi_gian_chay_lai_binh_thuong():
    moc = datetime(2026, 1, 15, 9, 30)

    with clock.freeze(moc):
        pass

    assert clock.now() - datetime.now() < timedelta(seconds=1)
    assert clock.now() != moc
