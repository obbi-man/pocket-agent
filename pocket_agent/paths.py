# -*- coding: utf-8 -*-
"""User-data paths for installed Pocket Agent (Windows APPDATA)."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_NAME = "Pocket Agent"
APP_VERSION = "0.2.0"


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> Path:
    """Directory with packaged resources (or repo root in dev)."""
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    """Writable config / prompts / plugins."""
    override = (os.environ.get("POCKET_AGENT_DATA") or "").strip()
    if override:
        path = Path(override)
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        path = base / APP_NAME
    else:
        path = Path.home() / ".pocket-agent"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return data_dir() / "config.json"


def prompt_path() -> Path:
    return data_dir() / "system_prompt.txt"


def plugins_dir() -> Path:
    path = data_dir() / "plugins"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_user_files() -> None:
    """Seed defaults into APPDATA on first launch."""
    root = bundle_root()
    cfg = config_path()
    if not cfg.is_file():
        example = root / "config.example.json"
        if example.is_file():
            text = example.read_text(encoding="utf-8")
            text = text.replace('"system_prompt_file": "system_prompt.txt"', '"system_prompt_file": "system_prompt.txt"')
            text = text.replace('"plugins_dir": "plugins_user"', '"plugins_dir": "plugins"')
            cfg.write_text(text, encoding="utf-8")
        else:
            cfg.write_text(
                "{\n"
                '  "api_key": "",\n'
                '  "base_url": "https://api.openai.com/v1",\n'
                '  "model": "gpt-4o-mini",\n'
                '  "system_prompt_file": "system_prompt.txt",\n'
                '  "plugins_dir": "plugins",\n'
                '  "temperature": 0.3,\n'
                '  "max_tool_rounds": 6\n'
                "}\n",
                encoding="utf-8",
            )

    prompt = prompt_path()
    if not prompt.is_file():
        src = root / "system_prompt.txt"
        if src.is_file():
            shutil.copy2(src, prompt)
        else:
            prompt.write_text(
                "Ты локальный ассистент пользователя (Pocket Agent).\n"
                "Отвечай коротко и по делу. Используй инструменты, когда они нужны.\n",
                encoding="utf-8",
            )

    plugs = plugins_dir()
    # seed example plugin once
    hello = plugs / "hello.py"
    if not hello.is_file():
        sample = root / "plugins_user" / "hello.py"
        if sample.is_file():
            shutil.copy2(sample, hello)
        else:
            hello.write_text(
                'PLUGIN = {\n'
                '    "name": "hello",\n'
                '    "description": "Поздороваться по имени",\n'
                '    "parameters": {\n'
                '        "type": "object",\n'
                '        "properties": {"name": {"type": "string"}},\n'
                '        "required": ["name"],\n'
                "    },\n"
                "}\n\n\n"
                'def run(name: str = "друг") -> str:\n'
                '    return f"Привет, {name}!"\n',
                encoding="utf-8",
            )
