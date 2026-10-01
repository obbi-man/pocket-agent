# -*- coding: utf-8 -*-
"""Пример пользовательского плагина — скопируй и меняй."""

PLUGIN = {
    "name": "hello",
    "description": "Поздороваться по имени",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Имя человека"},
        },
        "required": ["name"],
    },
}


def run(name: str = "друг") -> str:
    return f"Привет, {name}! Это плагин hello из plugins_user/."
