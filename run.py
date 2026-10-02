#!/usr/bin/env python3
"""Chạy dự án bằng một lệnh, trên máy sạch — chỉ dùng thư viện chuẩn.

    python run.py                  tạo .venv, cài thư viện, tạo .env, seed, chạy web, mở trình duyệt
    python run.py --port 9000      chọn cổng (mặc định 8000, bận thì báo lỗi nếu bạn tự chọn)
    python run.py --no-open        không mở trình duyệt
    python run.py --reload         uvicorn tự nạp lại khi sửa code
    python run.py --check          chạy thử: đợi /login trả 200 rồi tắt (dùng trong CI)
    python run.py status           xem tình trạng môi trường
    python run.py reset            xóa CSDL SQLite (hỏi xác nhận); lần `up` sau seed lại
    python run.py test [...]       chạy pytest, chuyển nguyên tham số: python run.py test -k dang_nhap

Cam kết: `.env` đã có thì KHÔNG BAO GIỜ bị ghi đè. Chỉ khi thiếu hoặc còn SECRET_KEY mặc định
thì dòng SECRET_KEY được thay bằng chuỗi ngẫu nhiên; mọi dòng khác giữ nguyên từng byte.
"""

import argparse
import hashlib
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MIN_PYTHON = (3, 11)
DEFAULT_PORT = 8000
SECRET_KEY_MAC_DINH = "doi-thanh-chuoi-ngau-nhien-truoc-khi-chay-that"
DEFAULT_DATABASE_URL = "sqlite:///./petcare.db"
COMMANDS = ("up", "reset", "status", "test")


class Fail(Exception):
    """Lỗi người dùng đọc được; main() in ra và thoát mã 1, không in traceback."""


def setup_console():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


# --- .env -----------------------------------------------------------------------------


def parse_env(text):
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def new_secret_key():
    return secrets.token_urlsafe(48)


def _set_secret_key(raw, key):
    """Thay (hoặc thêm) đúng một dòng SECRET_KEY, giữ nguyên mọi byte còn lại và kiểu xuống dòng."""
    lines = raw.decode("utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("#") and stripped.partition("=")[0].strip() == "SECRET_KEY":
            ending = line[len(line.rstrip("\r\n")):]
            lines[i] = "SECRET_KEY=%s%s" % (key, ending or "\n")
            return "".join(lines).encode("utf-8")
    if lines and not lines[-1].endswith(("\n", "\r")):
        lines[-1] += "\n"
    lines.append("SECRET_KEY=%s\n" % key)
    return "".join(lines).encode("utf-8")


def ensure_env(root):
    """Trả "tao" (tạo mới), "dat_khoa" (chỉ thay dòng SECRET_KEY) hoặc "giu" (không đụng gì)."""
    env_file = root / ".env"
    if not env_file.exists():
        mau = root / ".env.example"
        if not mau.exists():
            raise Fail("Thiếu cả .env lẫn .env.example — không có gì để tạo .env từ đó.")
        env_file.write_bytes(_set_secret_key(mau.read_bytes(), new_secret_key()))
        _chmod_private(env_file)
        return "tao"

    raw = env_file.read_bytes()
    khoa = parse_env(raw.decode("utf-8")).get("SECRET_KEY", "")
    if khoa and khoa != SECRET_KEY_MAC_DINH:
        return "giu"
    env_file.write_bytes(_set_secret_key(raw, new_secret_key()))
    return "dat_khoa"


def _chmod_private(path):
    try:
        path.chmod(0o600)
    except OSError:
        pass


# --- cổng, đường dẫn, CSDL ------------------------------------------------------------


def port_busy(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def pick_port(start, limit=20, is_busy=port_busy):
    for port in range(start, start + limit):
        if not is_busy(port):
            return port
    raise Fail("Không tìm được cổng trống trong khoảng %d–%d." % (start, start + limit - 1))


def venv_python(root, os_name=os.name):
    if os_name == "nt":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def db_file(url, root):
    """Đường dẫn file của CSDL SQLite; None nếu không phải SQLite dạng file (không đoán mò để xóa)."""
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return None
    path = url[len(prefix):].split("?", 1)[0]
    if not path or path.startswith(":memory:"):
        return None
    p = Path(path)
    return p if p.is_absolute() else root / p


def wait_healthy(port, path="/login", timeout=60.0, interval=0.5):
    deadline = time.time() + timeout
    url = "http://127.0.0.1:%d%s" % (port, path)
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except OSError:
            pass
        time.sleep(interval)
    return False


# --- dòng lệnh ------------------------------------------------------------------------


def parse_args(argv):
    if argv and argv[0] == "test":
        return argparse.Namespace(command="test", pytest_args=list(argv[1:]))

    parser = argparse.ArgumentParser(
        prog="run.py", description="Chạy dự án quản lý thú cưng. Không ghi lệnh = `up`."
    )
    parser.add_argument("command", nargs="?", default="up", choices=COMMANDS)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--yes", action="store_true", help="reset: bỏ qua bước xác nhận")
    # Cho phép `python run.py --port 9000` (không có lệnh con): chèn "up" nếu đầu vào bắt đầu bằng cờ.
    if not argv or argv[0].startswith("-"):
        argv = ["up"] + list(argv)
    return parser.parse_args(argv)


# --- lệnh -----------------------------------------------------------------------------


def log(msg):
    print("[run] " + msg, flush=True)


def run_cmd(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], cwd=str(ROOT), **kw)


def ensure_venv():
    py = venv_python(ROOT)
    if not py.exists():
        log("Tạo môi trường ảo .venv ...")
        if run_cmd([sys.executable, "-m", "venv", ROOT / ".venv"]).returncode != 0:
            raise Fail("Không tạo được .venv. Trên Debian/Ubuntu thử: sudo apt install python3-venv")
    req = ROOT / "requirements.txt"
    dau_van_tay = ROOT / ".venv" / ".requirements.sha256"
    bam = hashlib.sha256(req.read_bytes()).hexdigest()
    if not dau_van_tay.exists() or dau_van_tay.read_text().strip() != bam:
        log("Cài thư viện từ requirements.txt ...")
        if run_cmd([py, "-m", "pip", "install", "-r", req]).returncode != 0:
            raise Fail("pip install thất bại — xem lỗi phía trên.")
        dau_van_tay.write_text(bam)
    return py


def current_db_path():
    env = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        env = parse_env(env_file.read_text(encoding="utf-8"))
    url = os.environ.get("DATABASE_URL") or env.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    return db_file(url, ROOT)


def cmd_up(args):
    py = ensure_venv()
    hanh_dong = ensure_env(ROOT)
    if hanh_dong == "tao":
        log("Đã tạo .env từ .env.example với SECRET_KEY ngẫu nhiên.")
    elif hanh_dong == "dat_khoa":
        log("Đã đặt SECRET_KEY ngẫu nhiên vào .env (các dòng khác giữ nguyên).")

    db = current_db_path()
    if db is not None and not db.exists():
        log("CSDL chưa có — nạp dữ liệu mẫu (python -m app.seed) ...")
        if run_cmd([py, "-m", "app.seed"]).returncode != 0:
            raise Fail("Seed thất bại — xem lỗi phía trên.")

    if args.port is not None:
        if port_busy(args.port):
            raise Fail("Cổng %d đang bận. Chọn cổng khác bằng --port, hoặc bỏ --port để tự chọn." % args.port)
        port = args.port
    else:
        port = pick_port(DEFAULT_PORT)
        if port != DEFAULT_PORT:
            log("Cổng %d bận, dùng cổng %d." % (DEFAULT_PORT, port))

    cmd = [py, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", port]
    if args.reload:
        cmd.append("--reload")
    url = "http://127.0.0.1:%d" % port
    log("Chạy %s  (Ctrl+C để dừng)" % url)
    proc = subprocess.Popen([str(c) for c in cmd], cwd=str(ROOT))
    try:
        if args.check:
            ok = wait_healthy(port)
            log("/login trả 200." if ok else "Hết thời gian mà /login chưa trả 200.")
            return 0 if ok else 1
        if not args.no_open:
            threading.Thread(
                target=lambda: wait_healthy(port) and webbrowser.open(url + "/login"), daemon=True
            ).start()
        return proc.wait()
    except KeyboardInterrupt:
        log("Đã dừng.")
        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


def cmd_reset(args):
    db = current_db_path()
    if db is None:
        raise Fail("DATABASE_URL không phải file SQLite — run.py không xóa thứ nó không chắc là file.")
    if not db.exists():
        log("Không có %s — không có gì để xóa." % db.name)
        return 0
    if not args.yes:
        print("Sắp xóa %s (toàn bộ dữ liệu trong đó)." % db)
        if input("Gõ 'xoa' để xác nhận: ").strip().lower() != "xoa":
            log("Đã hủy, không xóa gì.")
            return 1
    for suffix in ("", "-wal", "-shm"):
        f = Path(str(db) + suffix)
        if f.exists():
            f.unlink()
    log("Đã xóa. Lần `python run.py` sau sẽ seed lại dữ liệu mẫu.")
    return 0


def cmd_status(_args):
    env_file = ROOT / ".env"
    khoa = parse_env(env_file.read_text(encoding="utf-8")).get("SECRET_KEY", "") if env_file.exists() else ""
    db = current_db_path()
    rows = [
        ("Python", "%d.%d.%d" % sys.version_info[:3]),
        (".venv", "có" if venv_python(ROOT).exists() else "chưa"),
        (".env", "có" if env_file.exists() else "chưa"),
        ("SECRET_KEY", "đã đặt" if khoa and khoa != SECRET_KEY_MAC_DINH else "chưa đặt (app sẽ từ chối chạy)"),
        ("CSDL", ("có (%s)" % db.name if db.exists() else "chưa") if db else "không phải file SQLite"),
        ("Cổng %d" % DEFAULT_PORT, "đang bận" if port_busy(DEFAULT_PORT) else "trống"),
    ]
    for ten, giatri in rows:
        print("%-12s %s" % (ten, giatri))
    return 0


def cmd_test(args):
    py = venv_python(ROOT)
    if not py.exists():
        py = ensure_venv()
    return run_cmd([py, "-m", "pytest", *args.pytest_args]).returncode


def main(argv=None):
    setup_console()
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        if sys.version_info < MIN_PYTHON:
            raise Fail("Cần Python %d.%d trở lên, máy đang có %d.%d." % (MIN_PYTHON + sys.version_info[:2]))
        return {"up": cmd_up, "reset": cmd_reset, "status": cmd_status, "test": cmd_test}[args.command](args)
    except Fail as e:
        print("[run] LỖI: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
