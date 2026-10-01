# -*- coding: utf-8 -*-
PLUGIN = {
    "name": "echo",
    "description": "Вернуть тот же текст (для проверки tool-calling)",
    "parameters": {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "Текст"}},
        "required": ["text"],
    },
}


def run(text: str = "") -> str:
    return str(text)
