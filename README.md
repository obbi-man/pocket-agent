# Pocket Agent — свой ИИ-агент на твоём API-ключе

> **Поставил как программу → вставил ключ в настройках → получил своего агента.**  
> Меняешь системный промпт, любой OpenAI-совместимый endpoint, дописываешь плагины `.py` без фреймворков.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/Windows-installer-blue.svg)](https://github.com/obbi-man/pocket-agent/releases)

## Что это

Небольшой **десктопный** агент с GUI:

1. **BYOK** — свой ключ OpenAI / OpenRouter / Groq / локальный llama.cpp / vLLM
2. **Свой system prompt** — вкладка в приложении, файл в `%LOCALAPPDATA%\Pocket Agent\`
3. **Плагины = обычные `.py`** — положил в папку, нажал «Обновить»
4. Без аккаунта продукта и без телеметрии

Это **не** Pulsar Desktop — отдельный открытый каркас.

## Установка (Windows)

### Готовый установщик

1. Скачай `PocketAgentSetup-0.2.0.exe` из [Releases](https://github.com/obbi-man/pocket-agent/releases)
2. Установи → ярлык **Pocket Agent**
3. Открой вкладку **Настройки** → API key / Base URL / Model → **Сохранить**
4. Пиши в **Чат** (Ctrl+Enter)

Данные лежат в:

```text
%LOCALAPPDATA%\Pocket Agent\
  config.json
  system_prompt.txt
  plugins\
```

### Сборка у себя

```bat
git clone https://github.com/obbi-man/pocket-agent.git
cd pocket-agent
build.bat
```

Получишь:

- `dist\PocketAgent\PocketAgent.exe` — портативная папка
- `dist\PocketAgentSetup-0.2.0.exe` — инсталлятор (нужен [Inno Setup 6](https://jrsoftware.org/isinfo.php))

## Запуск из исходников

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pocket_agent          # GUI
python -m pocket_agent --cli    # текстовый REPL
python -m pocket_agent -q "..." # один вопрос
```

## Настройки

| Поле | Смысл |
|------|--------|
| API key | Ключ провайдера (можно пусто для localhost) |
| Base URL | Корень `…/v1` |
| Model | Имя модели |
| System prompt | Текст роли агента |
| Plugins | Папка `%LOCALAPPDATA%\Pocket Agent\plugins` |

Примеры `base_url`:

- `https://api.openai.com/v1`
- `https://openrouter.ai/api/v1`
- `https://api.groq.com/openai/v1`
- `http://127.0.0.1:8080/v1`

## Плагины

Файл `plugins\weather_stub.py`:

```python
PLUGIN = {
    "name": "hello",
    "description": "Поздороваться по имени",
    "parameters": {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    },
}


def run(name: str = "друг") -> str:
    return f"Привет, {name}!"
```

В GUI: **Плагины → Открыть папку / Создать пример / Обновить список**.

Встроенные: `echo`, `time`, `list_plugins`.

## Безопасность

- Ключ только у тебя в `%LOCALAPPDATA%\Pocket Agent\config.json`
- Плагины выполняются локально с правами процесса — ставь только свой код
- Сеть — только на выбранный `base_url`

## Структура

```
pocket-agent/
├── app.py                 # entry для .exe
├── pocket_agent/
│   ├── gui.py             # PySide6 UI
│   ├── agent.py           # tool-calling loop
│   ├── client.py          # /v1/chat/completions
│   ├── config.py / paths.py
│   └── plugins/           # loader + builtin
├── PocketAgent.spec       # PyInstaller
├── Setup.iss              # Inno Setup
└── build.bat
```

## Лицензия

MIT © [obbi-man](https://github.com/obbi-man)

Связано с экосистемой [Pulsar Open Source](https://www.pulsar-agent.ru/open-source), но живёт отдельно.
