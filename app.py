# -*- coding: utf-8 -*-
"""Frozen / pythonw entrypoint for Pocket Agent GUI."""
from __future__ import annotations

import sys


def main() -> int:
    # GUI by default when launched as .exe / pythonw
    if "--cli" not in sys.argv and "-q" not in sys.argv and "--query" not in sys.argv:
        if "--gui" not in sys.argv:
            sys.argv.append("--gui")
    from pocket_agent.__main__ import main as _main

    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
