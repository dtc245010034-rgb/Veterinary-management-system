"""Kết nối cơ sở dữ liệu và session SQLAlchemy.

Base ở đây là lớp cha của mọi model. get_db() là dependency của FastAPI, và cũng là
điểm để test thay bằng CSDL in-memory qua app.dependency_overrides.
"""

import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite: cho phép dùng qua nhiều luồng
)

# expire_on_commit để mặc định (True): tắt nó thì collection quan hệ giữ nguyên giá trị
# cũ sau commit — owner.pets sẽ không thấy thú cưng vừa thêm.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


@event.listens_for(Engine, "connect")
def _bat_khoa_ngoai(dbapi_connection, connection_record):
    """SQLite mặc định KHÔNG kiểm tra khóa ngoại — phải bật thủ công từng kết nối.

    Không bật thì mọi ràng buộc FK trong ERD chỉ là chú thích, và các ca như "xóa chủ nuôi
    còn thú cưng thì bị chặn" sẽ âm thầm không hoạt động.

    Gắn vào lớp Engine chứ không vào riêng `engine` ở trên: fixture test dựng engine
    in-memory của nó, và listener gắn cho một engine cụ thể sẽ không áp dụng cho engine đó.
    Hậu quả là test chạy trong môi trường không có khóa ngoại còn production thì có — mọi
    test về ràng buộc FK sẽ cho kết quả không đúng với thực tế.
    """
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db():
    """Cấp một session cho mỗi request và đóng lại khi xong."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
