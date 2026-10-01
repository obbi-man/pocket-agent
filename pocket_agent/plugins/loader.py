# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import importlib
import importlib.util
import sys


@dataclass
class PluginSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    run: Callable[..., Any]
    path: Path | None = None


def _load_module(path: Path):
    mod_name = f"pocket_plugin_{path.stem}_{abs(hash(str(path))) % 10_000_000}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _spec_from_module(module: Any, path: Path | None = None) -> PluginSpec | None:
    meta = getattr(module, "PLUGIN", None)
    run = getattr(module, "run", None)
    if not isinstance(meta, dict) or not callable(run):
        return None
    name = str(meta.get("name") or (path.stem if path else "")).strip()
    if not name:
        return None
    params = meta.get("parameters") if isinstance(meta.get("parameters"), dict) else {
        "type": "object",
        "properties": {},
    }
    return PluginSpec(
        name=name,
        description=str(meta.get("description") or name),
        parameters=params,
        run=run,
        path=path,
    )


def load_builtin_plugins() -> dict[str, PluginSpec]:
    out: dict[str, PluginSpec] = {}
    # Import by module path — works in frozen builds
    for mod_name in (
        "pocket_agent.plugins.builtin.echo",
        "pocket_agent.plugins.builtin.time",
    ):
        try:
            mod = importlib.import_module(mod_name)
            spec = _spec_from_module(mod)
        except Exception:
            continue
        if spec:
            out[spec.name] = spec

    # Dev fallback: also scan folder if present as files
    builtin_dir = Path(__file__).resolve().parent / "builtin"
    if builtin_dir.is_dir():
        for path in sorted(builtin_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            if path.stem in out:
                continue
            try:
                mod = _load_module(path)
                spec = _spec_from_module(mod, path)
            except Exception:
                continue
            if spec:
                out[spec.name] = spec
    return out


def load_user_plugins(directory: Path) -> dict[str, PluginSpec]:
    out: dict[str, PluginSpec] = {}
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            mod = _load_module(path)
            spec = _spec_from_module(mod, path)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] plugin {path.name}: {exc}")
            continue
        if spec:
            out[spec.name] = spec
    return out


def load_all_plugins(user_dir: Path) -> dict[str, PluginSpec]:
    plugins = load_builtin_plugins()
    plugins.update(load_user_plugins(user_dir))

    def _list_plugins() -> str:
        keys = sorted(k for k in plugins.keys() if k != "list_plugins")
        if not keys:
            return "Плагинов нет."
        lines = [f"- {n}: {plugins[n].description}" for n in keys]
        return "Доступные плагины:\n" + "\n".join(lines)

    plugins["list_plugins"] = PluginSpec(
        name="list_plugins",
        description="Список подключённых плагинов",
        parameters={"type": "object", "properties": {}},
        run=_list_plugins,
    )
    return plugins


def to_openai_tools(plugins: dict[str, PluginSpec]) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for spec in plugins.values():
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                },
            }
        )
    return tools
