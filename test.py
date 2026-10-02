#!/usr/bin/env python3
"""Chạy toàn bộ test của dự án.

    python test.py                 mọi test
    python test.py tests/unit -x   truyền thẳng tham số cho pytest

Mã thoát 0 = đạt, khác 0 = không đạt. Đây chỉ là lối tắt của: python run.py test
"""
import sys

import run

if __name__ == "__main__":
    sys.exit(run.main(["test", *sys.argv[1:]]))
