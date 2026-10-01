# Pocket Agent — свой ИИ-агент на твоём API-ключе

> **Вставил ключ в настройки → получил своего агента.**  
> Меняешь системный промпт, подключаешь любой OpenAI-совместимый endpoint, дописываешь плагины без фреймворков.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Зачем

Большинство «агентов» тащат тяжёлый стек и прячут промпт. Pocket Agent — наоборот:

1. **BYOK** — свой ключ OpenAI / OpenRouter / Groq / локальный llama.cpp / что угодно с `/v1/chat/completions`
2. **Свой system prompt** — один текстовый файл, без перекомпиляции
3. **Плагины = обычные `.py` файлы** — положил в папку, агент подхватил
4. Без облачного аккаунта продукта и без телеметрии

Это **не** Pulsar Desktop. Это маленький открытый каркас, если хочешь своего агента «на коленке».

## Быстрый старт

```bash
git clone https://github.com/obbi-man/pocket-agent.git
cd pocket-agent
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
# впиши api_key / base_url / model
python -m pocket_agent
```

Интерактивный чат:

```text
you> сколько сейчас времени?
agent> [time] 2026-10-01 22:10:00
```

Одноразовый запрос:

```bash
python -m pocket_agent -q "перечисли доступные плагины"
```

## Настройки (`config.json`)

```json
{
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "system_prompt_file": "system_prompt.txt",
  "plugins_dir": "plugins_user",
  "temperature": 0.3,
  "max_tool_rounds": 6
}
```

| Поле | Смысл |
|------|--------|
| `api_key` | Любой ключ провайдера (или пусто для локального сервера без auth) |
| `base_url` | OpenAI-совместимый корень (`…/v1`) |
| `model` | Имя модели у провайдера |
| `system_prompt_file` | Путь к файлу с системным промптом |
| `plugins_dir` | Папка с твоими плагинами |

Примеры `base_url`:

- OpenAI: `https://api.openai.com/v1`
- OpenRouter: `https://openrouter.ai/api/v1`
- Groq: `https://api.groq.com/openai/v1`
- Локально (llama.cpp / vLLM): `http://127.0.0.1:8080/v1`

## Системный промпт

Редактируй `system_prompt.txt` — агент читает его при каждом запуске.

```text
Ты краткий ассистент. Используй инструменты, когда они реально нужны.
Отвечай на языке пользователя.
```

## Плагины

Файл в `plugins_user/hello.py`:

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

Встроенные: `echo`, `time`, `list_plugins`.

Загрузчик ищет любой `.py` с словарём `PLUGIN` и функцией `run(**kwargs)`.

## CLI

```bash
python -m pocket_agent                  # REPL
python -m pocket_agent -q "..."         # один вопрос
python -m pocket_agent --list-plugins   # что подключено
python -m pocket_agent --config path.json
```

## Структура

```
pocket-agent/
├── pocket_agent/          # ядро
│   ├── agent.py           # цикл tool-calling
│   ├── client.py          # HTTP к /v1/chat/completions
│   ├── config.py
│   └── plugins/           # loader + builtin
├── plugins_user/          # твои плагины (gitignored примеры ок)
├── system_prompt.txt
├── config.example.json
└── requirements.txt
```

## Безопасность

- Ключ лежит только у тебя в `config.json` (в `.gitignore`)
- Плагины выполняются **локально с полными правами процесса** — ставь только свой код
- Нет скрытых сетевых вызовов кроме выбранного `base_url`

## Лицензия

MIT © [obbi-man](https://github.com/obbi-man)

Связано с экосистемой [Pulsar](https://www.pulsar-agent.ru/open-source), но живёт отдельно.
