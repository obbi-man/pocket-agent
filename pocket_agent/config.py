# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pocket_agent.paths import (
    config_path as default_config_path,
    ensure_user_files,
    plugins_dir as default_plugins_dir,
    prompt_path as default_prompt_path,
)


def resolve_path(path: str | Path, *, base: Path | None = None) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    root = base or default_config_path().parent
    return root / p


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
    system_prompt_file: str = "system_prompt.txt"

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "system_prompt_file": self.system_prompt_file or "system_prompt.txt",
            "plugins_dir": "plugins" if self.plugins_dir.name == "plugins" else str(self.plugins_dir),
            "temperature": self.temperature,
            "max_tool_rounds": self.max_tool_rounds,
        }


def load_config(path: str | Path | None = None) -> Config:
    ensure_user_files()
    cfg_path = Path(path) if path else default_config_path()
    if not cfg_path.is_absolute():
        cfg_path = resolve_path(cfg_path)
    if not cfg_path.is_file():
        ensure_user_files()
        cfg_path = default_config_path()

    data: dict[str, Any] = json.loads(cfg_path.read_text(encoding="utf-8"))
    base = cfg_path.parent

    prompt_rel = str(data.get("system_prompt_file") or "system_prompt.txt")
    prompt_file = resolve_path(prompt_rel, base=base)
    if not prompt_file.is_file():
        prompt_file = default_prompt_path()
    if prompt_file.is_file():
        system_prompt = prompt_file.read_text(encoding="utf-8").strip()
    else:
        system_prompt = str(data.get("system_prompt") or "You are a helpful assistant.").strip()

    plugins_rel = str(data.get("plugins_dir") or "plugins")
    plugins = resolve_path(plugins_rel, base=base)
    if not plugins.is_dir():
        plugins = default_plugins_dir()
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
        system_prompt_file=prompt_rel,
    )


def save_config(cfg: Config) -> Path:
    ensure_user_files()
    cfg_path = cfg.config_path or default_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    payload = cfg.to_dict()
    cfg_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    prompt_file = resolve_path(cfg.system_prompt_file or "system_prompt.txt", base=cfg_path.parent)
    prompt_file.write_text((cfg.system_prompt or "").rstrip() + "\n", encoding="utf-8")
    return cfg_path
