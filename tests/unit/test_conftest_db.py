"""Canh fixture `db` của conftest: mỗi test một CSDL riêng, đủ bảng, dù schema được sao từ ảnh dựng sẵn.

Hai test dưới đây PHẢI đứng liền nhau và chạy theo thứ tự khai báo (pytest mặc định làm vậy):
test đầu commit một dòng, test sau chứng minh dòng đó không sang được. Nếu fixture `db` bị đổi
thành dùng chung CSDL giữa các test thì test sau đỏ.
"""

from sqlalchemy import inspect, select

from app.db import Base
from app.models.user import User


def test_db_co_du_bang_cua_moi_model(db):
    co_san = set(inspect(db.get_bind()).get_table_names())

    assert set(Base.metadata.tables) <= co_san


def test_db_a_commit_mot_dong(db):
    db.add(User(username="roi_rac", full_name="Roi Rac", role="manager", password_hash="x"))
    db.commit()

    assert db.scalars(select(User)).all()


def test_db_b_khong_thay_dong_cua_test_truoc(db):
    assert db.scalars(select(User)).all() == []
