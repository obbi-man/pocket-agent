# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return p


@dataclass
class Config:
    api_key: str
    base_url: str
    model: str
    system_prompt: str
    plugins_dir: Path
    temperature: float = 0.3
    max_tool_rounds: int = 6
    config_path: Path | None = None


def load_config(path: str | Path) -> Config:
    cfg_path = resolve_path(path)
    data: dict[str, Any] = json.loads(cfg_path.read_text(encoding="utf-8"))

    prompt_file = resolve_path(str(data.get("system_prompt_file") or "system_prompt.txt"))
    if prompt_file.is_file():
        system_prompt = prompt_file.read_text(encoding="utf-8").strip()
    else:
        system_prompt = str(data.get("system_prompt") or "You are a helpful assistant.").strip()

    plugins = resolve_path(str(data.get("plugins_dir") or "plugins_user"))
    plugins.mkdir(parents=True, exist_ok=True)

    return Config(
        api_key=str(data.get("api_key") or "").strip(),
        base_url=str(data.get("base_url") or "https://api.openai.com/v1").rstrip("/"),
        model=str(data.get("model") or "gpt-4o-mini").strip(),
        system_prompt=system_prompt,
        plugins_dir=plugins,
        temperature=float(data.get("temperature") or 0.3),
        max_tool_rounds=max(1, int(data.get("max_tool_rounds") or 6)),
        config_path=cfg_path,
    )
