# -*- coding: utf-8 -*-
"""Desktop GUI for Pocket Agent (PySide6)."""
from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QDoubleSpinBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from pocket_agent.agent import run_once
from pocket_agent.config import Config, load_config, save_config
from pocket_agent.paths import APP_NAME, APP_VERSION, data_dir, ensure_user_files, plugins_dir
from pocket_agent.plugins.loader import load_all_plugins


STYLE = """
QMainWindow, QWidget {
    background: #0f1419;
    color: #e7ecf3;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #243041;
    border-radius: 10px;
    top: -1px;
}
QTabBar::tab {
    background: #161d27;
    color: #9aa8bc;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:selected {
    background: #1c2736;
    color: #ffffff;
}
QPlainTextEdit, QLineEdit, QListWidget, QSpinBox, QDoubleSpinBox {
    background: #121821;
    color: #e7ecf3;
    border: 1px solid #2a374a;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #3d6df0;
}
QPushButton {
    background: #2f5bff;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background: #3d6df0; }
QPushButton:disabled { background: #2a374a; color: #7f8b9c; }
QPushButton#secondary {
    background: #1c2736;
    border: 1px solid #2a374a;
    font-weight: 500;
}
QPushButton#danger {
    background: #3a1f28;
    border: 1px solid #5a2c3a;
}
QStatusBar {
    background: #0c1016;
    color: #8b98ab;
}
QLabel#hint { color: #8b98ab; }
"""


class AgentWorker(QThread):
    finished_ok = Signal(str)
    finished_err = Signal(str)

    def __init__(self, cfg: Config, text: str, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self._text = text

    def run(self) -> None:
        try:
            out = run_once(self._cfg, self._text)
            self.finished_ok.emit(out)
        except Exception as exc:  # noqa: BLE001
            self.finished_err.emit(f"{exc}\n{traceback.format_exc()}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_user_files()
        self.cfg = load_config()
        self._worker: AgentWorker | None = None

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(980, 680)
        self.setMinimumSize(820, 560)

        tabs = QTabWidget()
        tabs.addTab(self._build_chat_tab(), "Чат")
        tabs.addTab(self._build_settings_tab(), "Настройки")
        tabs.addTab(self._build_prompt_tab(), "Системный промпт")
        tabs.addTab(self._build_plugins_tab(), "Плагины")
        self.setCentralWidget(tabs)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status = QLabel()
        sb.addWidget(self._status, 1)
        self._refresh_status()

        file_menu = self.menuBar().addMenu("Файл")
        act_reload = QAction("Перезагрузить конфиг", self)
        act_reload.triggered.connect(self._reload_all)
        file_menu.addAction(act_reload)
        act_data = QAction("Открыть папку данных", self)
        act_data.triggered.connect(lambda: self._open_path(data_dir()))
        file_menu.addAction(act_data)
        file_menu.addSeparator()
        act_quit = QAction("Выход", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        help_menu = self.menuBar().addMenu("Справка")
        act_about = QAction("О программе", self)
        act_about.triggered.connect(self._about)
        help_menu.addAction(act_about)

    def _build_chat_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel("Свой ключ → свой агент. Ответ идёт через выбранный API + плагины.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.chat = QPlainTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("Диалог появится здесь…")
        mono = QFont("Consolas")
        mono.setPointSize(11)
        self.chat.setFont(mono)
        layout.addWidget(self.chat, 1)

        row = QHBoxLayout()
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Напишите сообщение…  Ctrl+Enter — отправить")
        self.input.setFixedHeight(90)
        row.addWidget(self.input, 1)

        col = QVBoxLayout()
        self.send_btn = QPushButton("Отправить")
        self.send_btn.clicked.connect(self._send)
        clear_btn = QPushButton("Очистить")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self.chat.clear)
        col.addWidget(self.send_btn)
        col.addWidget(clear_btn)
        col.addStretch(1)
        row.addLayout(col)
        layout.addLayout(row)

        self.input.installEventFilter(self)
        return w

    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)
        self.api_key = QLineEdit(self.cfg.api_key)
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("sk-… или пусто для локального сервера")
        show = QPushButton("Показать")
        show.setObjectName("secondary")
        show.setCheckable(True)
        show.toggled.connect(
            lambda on: self.api_key.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        key_row = QHBoxLayout()
        key_row.addWidget(self.api_key, 1)
        key_row.addWidget(show)
        key_wrap = QWidget()
        key_wrap.setLayout(key_row)

        self.base_url = QLineEdit(self.cfg.base_url)
        self.model = QLineEdit(self.cfg.model)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(float(self.cfg.temperature))
        self.max_rounds = QSpinBox()
        self.max_rounds.setRange(1, 20)
        self.max_rounds.setValue(int(self.cfg.max_tool_rounds))

        form.addRow("API key", key_wrap)
        form.addRow("Base URL", self.base_url)
        form.addRow("Model", self.model)
        form.addRow("Temperature", self.temperature)
        form.addRow("Max tool rounds", self.max_rounds)
        layout.addLayout(form)

        tip = QLabel(
            "Примеры base_url: https://api.openai.com/v1 · https://openrouter.ai/api/v1 · "
            "https://api.groq.com/openai/v1 · http://127.0.0.1:8080/v1"
        )
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        btns = QHBoxLayout()
        save = QPushButton("Сохранить настройки")
        save.clicked.connect(self._save_settings)
        btns.addWidget(save)
        btns.addStretch(1)
        layout.addLayout(btns)
        layout.addStretch(1)
        return w

    def _build_prompt_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        tip = QLabel("Системный промпт читается при каждом запросе. Можно менять без переустановки.")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        self.prompt_edit = QPlainTextEdit(self.cfg.system_prompt)
        layout.addWidget(self.prompt_edit, 1)
        save = QPushButton("Сохранить промпт")
        save.clicked.connect(self._save_prompt)
        layout.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        return w

    def _build_plugins_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        tip = QLabel(
            "Положи .py файл с PLUGIN = {...} и def run(**kwargs) в папку плагинов — "
            "агент подхватит без пересборки."
        )
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        self.plugins_list = QListWidget()
        layout.addWidget(self.plugins_list, 1)

        row = QHBoxLayout()
        refresh = QPushButton("Обновить список")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self._reload_plugins)
        open_dir = QPushButton("Открыть папку плагинов")
        open_dir.clicked.connect(lambda: self._open_path(plugins_dir()))
        new_plugin = QPushButton("Создать пример…")
        new_plugin.setObjectName("secondary")
        new_plugin.clicked.connect(self._create_plugin_stub)
        row.addWidget(refresh)
        row.addWidget(open_dir)
        row.addWidget(new_plugin)
        row.addStretch(1)
        layout.addLayout(row)

        self._reload_plugins()
        return w

    def eventFilter(self, obj, event):  # noqa: N802
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent

        if obj is self.input and event.type() == QEvent.Type.KeyPress:
            assert isinstance(event, QKeyEvent)
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    def _append(self, who: str, text: str) -> None:
        self.chat.appendPlainText(f"{who}>\n{text}\n")
        self.chat.moveCursor(QTextCursor.MoveOperation.End)

    def _cfg_from_ui(self) -> Config:
        cfg = load_config()
        cfg.api_key = self.api_key.text().strip()
        cfg.base_url = self.base_url.text().strip().rstrip("/")
        cfg.model = self.model.text().strip() or "gpt-4o-mini"
        cfg.temperature = float(self.temperature.value())
        cfg.max_tool_rounds = int(self.max_rounds.value())
        cfg.system_prompt = self.prompt_edit.toPlainText().strip()
        return cfg

    def _send(self) -> None:
        text = self.input.toPlainText().strip()
        if not text:
            return
        if self._worker and self._worker.isRunning():
            return
        self.cfg = self._cfg_from_ui()
        if not self.cfg.api_key and "127.0.0.1" not in self.cfg.base_url and "localhost" not in self.cfg.base_url:
            QMessageBox.warning(
                self,
                APP_NAME,
                "Укажите API key в настройках (или локальный base_url без ключа).",
            )
            return
        self._append("you", text)
        self.input.clear()
        self.send_btn.setEnabled(False)
        self._status.setText("Думаю…")
        self._worker = AgentWorker(self.cfg, text, self)
        self._worker.finished_ok.connect(self._on_reply)
        self._worker.finished_err.connect(self._on_reply_err)
        self._worker.start()

    def _on_reply(self, text: str) -> None:
        self.send_btn.setEnabled(True)
        self._append("agent", text)
        self._refresh_status()

    def _on_reply_err(self, text: str) -> None:
        self.send_btn.setEnabled(True)
        self._append("error", text)
        self._refresh_status()

    def _save_settings(self) -> None:
        self.cfg = self._cfg_from_ui()
        path = save_config(self.cfg)
        self._refresh_status()
        QMessageBox.information(self, APP_NAME, f"Сохранено:\n{path}")

    def _save_prompt(self) -> None:
        self.cfg = self._cfg_from_ui()
        path = save_config(self.cfg)
        QMessageBox.information(self, APP_NAME, f"Промпт сохранён.\n{path.parent / 'system_prompt.txt'}")

    def _reload_plugins(self) -> None:
        self.plugins_list.clear()
        try:
            plugins = load_all_plugins(plugins_dir())
        except Exception as exc:  # noqa: BLE001
            self.plugins_list.addItem(f"[ERROR] {exc}")
            return
        for name, spec in sorted(plugins.items()):
            item = QListWidgetItem(f"{name} — {spec.description}")
            self.plugins_list.addItem(item)

    def _reload_all(self) -> None:
        self.cfg = load_config()
        self.api_key.setText(self.cfg.api_key)
        self.base_url.setText(self.cfg.base_url)
        self.model.setText(self.cfg.model)
        self.temperature.setValue(float(self.cfg.temperature))
        self.max_rounds.setValue(int(self.cfg.max_tool_rounds))
        self.prompt_edit.setPlainText(self.cfg.system_prompt)
        self._reload_plugins()
        self._refresh_status()

    def _create_plugin_stub(self) -> None:
        name, ok = QFileDialog.getSaveFileName(
            self,
            "Новый плагин",
            str(plugins_dir() / "my_plugin.py"),
            "Python (*.py)",
        )
        if not ok or not name:
            return
        path = Path(name)
        if path.exists():
            QMessageBox.warning(self, APP_NAME, "Файл уже есть.")
            return
        stem = path.stem.replace("-", "_")
        path.write_text(
            f'PLUGIN = {{\n'
            f'    "name": "{stem}",\n'
            f'    "description": "Описание плагина {stem}",\n'
            f'    "parameters": {{\n'
            f'        "type": "object",\n'
            f'        "properties": {{"text": {{"type": "string"}}}},\n'
            f'    }},\n'
            f"}}\n\n\n"
            f"def run(text: str = \"\") -> str:\n"
            f'    return f"[{stem}] {{text}}"\n',
            encoding="utf-8",
        )
        self._reload_plugins()
        self._open_path(path.parent)

    def _open_path(self, path: Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _refresh_status(self) -> None:
        key = "key✓" if self.cfg.api_key else "key—"
        self._status.setText(
            f"{self.cfg.model} · {self.cfg.base_url} · {key} · data: {data_dir()}"
        )

    def _about(self) -> None:
        QMessageBox.information(
            self,
            f"О {APP_NAME}",
            f"{APP_NAME} {APP_VERSION}\n\n"
            "BYOK AI-агент: свой API-ключ, свой system prompt, плагины .py.\n"
            "https://github.com/obbi-man/pocket-agent\n\n"
            f"Данные: {data_dir()}",
        )


def run_gui() -> int:
    ensure_user_files()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    return app.exec()
