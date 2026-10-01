# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys

from pocket_agent.config import load_config, resolve_path
from pocket_agent.paths import ensure_user_files, config_path
from pocket_agent.plugins.loader import load_all_plugins


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pocket-agent",
        description="BYOK AI agent: свой ключ, свой промпт, свои плагины.",
    )
    parser.add_argument("--config", "-c", default="", help="Путь к config.json (по умолчанию APPDATA)")
    parser.add_argument("-q", "--query", default="", help="Один вопрос без GUI/REPL")
    parser.add_argument("--cli", action="store_true", help="Текстовый REPL вместо GUI")
    parser.add_argument("--gui", action="store_true", help="Запустить GUI (по умолчанию)")
    parser.add_argument("--list-plugins", action="store_true", help="Показать плагины и выйти")
    args = parser.parse_args(argv)

    ensure_user_files()
    cfg_path = args.config.strip() or str(config_path())

    if not resolve_path(cfg_path).is_file() and args.config.strip():
        print(f"[!] Нет конфига: {cfg_path}", file=sys.stderr)
        return 1

    cfg = load_config(cfg_path if args.config.strip() else None)

    if args.list_plugins:
        plugins = load_all_plugins(cfg.plugins_dir)
        if not plugins:
            print("Плагинов нет.")
            return 0
        for name, spec in sorted(plugins.items()):
            print(f"- {name}: {spec.description}")
        return 0

    if args.query.strip():
        from pocket_agent.agent import run_once

        print(run_once(cfg, args.query.strip()))
        return 0

    if args.cli:
        from pocket_agent.agent import run_repl

        run_repl(cfg)
        return 0

    # default: GUI
    from pocket_agent.gui import run_gui

    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
