# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys

from pocket_agent.agent import run_once, run_repl
from pocket_agent.config import load_config, resolve_path
from pocket_agent.plugins.loader import load_all_plugins


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pocket-agent",
        description="BYOK AI agent: свой ключ, свой промпт, свои плагины.",
    )
    parser.add_argument("--config", "-c", default="config.json", help="Путь к config.json")
    parser.add_argument("-q", "--query", default="", help="Один вопрос без REPL")
    parser.add_argument("--list-plugins", action="store_true", help="Показать плагины и выйти")
    args = parser.parse_args(argv)

    cfg_path = resolve_path(args.config)
    if not cfg_path.is_file():
        example = resolve_path("config.example.json")
        print(
            f"[!] Нет {cfg_path.name}. Скопируй {example.name} → config.json и впиши api_key.",
            file=sys.stderr,
        )
        return 1

    cfg = load_config(cfg_path)

    if args.list_plugins:
        plugins = load_all_plugins(cfg.plugins_dir)
        if not plugins:
            print("Плагинов нет.")
            return 0
        for name, spec in sorted(plugins.items()):
            print(f"- {name}: {spec.description}")
        return 0

    if args.query.strip():
        print(run_once(cfg, args.query.strip()))
        return 0

    run_repl(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
