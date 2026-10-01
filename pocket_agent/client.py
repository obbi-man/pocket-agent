# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

import httpx

from pocket_agent.config import Config


class LLMError(RuntimeError):
    pass


def chat_completions(
    cfg: Config,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    url = f"{cfg.base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"

    body: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, json=body)
    except httpx.HTTPError as exc:
        raise LLMError(f"Сеть: {exc}") from exc

    if resp.status_code >= 400:
        raise LLMError(f"HTTP {resp.status_code}: {resp.text[:500]}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise LLMError(f"Не JSON от API: {resp.text[:300]}") from exc

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMError(f"Пустой ответ API: {json.dumps(data)[:400]}")
    return choices[0]
