"""Cấu hình Jinja2 dùng chung cho mọi router."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _tien(so) -> str:
    """150000 -> '150.000đ'. Đăng ký làm filter: `{{ s.price|tien }}`.

    Trước P5 đây là macro trong services.html. P5 cần nó ở ba template nữa, nên đăng ký
    một lần ở đây thay vì chép sang từng file — chép đi chép lại thì mỗi bản một kiểu
    hiển thị tiền.
    """
    return f"{so:,.0f}".replace(",", ".") + "đ"


templates.env.filters["tien"] = _tien
