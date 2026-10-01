# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

from pocket_agent.client import LLMError, chat_completions
from pocket_agent.config import Config
from pocket_agent.plugins.loader import PluginSpec, load_all_plugins, to_openai_tools


def _assistant_message(choice: dict[str, Any]) -> dict[str, Any]:
    msg = choice.get("message")
    if isinstance(msg, dict):
        return msg
    return {"role": "assistant", "content": str(choice.get("text") or "")}


def _run_tool(plugins: dict[str, PluginSpec], name: str, arguments: str) -> str:
    spec = plugins.get(name)
    if not spec:
        return f"[ERROR] неизвестный инструмент: {name}"
    try:
        args = json.loads(arguments or "{}")
        if not isinstance(args, dict):
            args = {}
    except json.JSONDecodeError:
        args = {}
    try:
        out = spec.run(**args)
    except TypeError:
        # allow run() without kwargs
        try:
            out = spec.run()
        except Exception as exc:  # noqa: BLE001
            return f"[ERROR] {name}: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR] {name}: {exc}"
    return str(out)


def run_once(cfg: Config, user_text: str) -> str:
    plugins = load_all_plugins(cfg.plugins_dir)
    tools = to_openai_tools(plugins)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": cfg.system_prompt},
        {"role": "user", "content": user_text},
    ]

    for _ in range(cfg.max_tool_rounds):
        try:
            choice = chat_completions(cfg, messages, tools=tools or None)
        except LLMError as exc:
            return f"[ERROR] {exc}"

        msg = _assistant_message(choice)
        messages.append(msg)
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            content = (msg.get("content") or "").strip()
            return content or "[INFO] Пустой ответ модели."

        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            fn = call.get("function") if isinstance(call.get("function"), dict) else {}
            name = str(fn.get("name") or "")
            arguments = str(fn.get("arguments") or "{}")
            result = _run_tool(plugins, name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(call.get("id") or name),
                    "content": result,
                }
            )

    return "[INFO] Достигнут лимит tool-раундов. Уточните запрос."


def run_repl(cfg: Config) -> None:
    print(f"Pocket Agent · model={cfg.model} · base={cfg.base_url}")
    print("Команды: /quit  /plugins  /prompt")
    plugins = load_all_plugins(cfg.plugins_dir)
    print(f"Плагинов: {len(plugins)} ({', '.join(sorted(plugins)[:8])}{'…' if len(plugins) > 8 else ''})")

    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in {"/quit", "/exit", ":q"}:
            break
        if line == "/plugins":
            for name, spec in sorted(plugins.items()):
                print(f"  - {name}: {spec.description}")
            continue
        if line == "/prompt":
            print(cfg.system_prompt[:1200])
            continue
        answer = run_once(cfg, line)
        print(f"agent> {answer}")
