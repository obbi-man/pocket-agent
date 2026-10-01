# -*- coding: utf-8 -*-
from datetime import datetime

PLUGIN = {
    "name": "time",
    "description": "Текущие локальные дата и время",
    "parameters": {"type": "object", "properties": {}},
}


def run() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
