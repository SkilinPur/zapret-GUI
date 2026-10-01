# =============================================================================
# Вкладка «Telegram» — Tg WS Proxy (локальный MTProto-прокси для Telegram Desktop)
# =============================================================================

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..worker import CommandWorker
from .widgets import log_line, make_button, make_card, make_title


class TelegramTab(QWidget):
    def __init__(self, zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(3000)
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        root.addWidget(make_title(
            "Telegram",
            "Tg WS Proxy — локальный MTProto-прокси для Telegram Desktop",
        ))

        card = make_card()
        cl = card.layout()
        self.state_label = QLabel()
        self.state_label.setObjectName("statusLabel")
        cl.addWidget(self.state_label)

        self.info = QLabel("—")
        self.info.setObjectName("statusMetaLabel")
        self.info.setWordWrap(True)
        cl.addWidget(self.info)

        desc = QLabel(
            "Помогает, когда Telegram тормозит/грузится плохо: трафик идёт "
            "через WebSocket к дата-центрам Telegram. Нужен один раз: запустить, "
            "в его окне нажать «Открыть в Telegram» (или подключиться вручную)."
        )
        desc.setObjectName("statusMetaLabel")
        desc.setWordWrap(True)
        cl.addWidget(desc)

        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(10)
        self.start_btn = make_button("▶ Запустить Tg WS Proxy", primary=True)
        self.stop_btn = make_button("⏹ Остановить", danger=True)
        self.connect_btn = make_button("🔗 Подключить в Telegram")
        self.update_btn = make_button("⬇ Скачать/обновить")
        for b in (self.start_btn, self.stop_btn, self.connect_btn, self.update_btn):
            b.setMinimumWidth(180)
        rl.addWidget(self.start_btn)
        rl.addWidget(self.stop_btn)
        rl.addWidget(self.connect_btn)
        rl.addWidget(self.update_btn)
        rl.addStretch()
        cl.addWidget(row)
        root.addWidget(card)

        log_card = make_card()
        ll = log_card.layout()
        header = QLabel(">_ журнал")
        header.setObjectName("logHeader")
        ll.addWidget(header)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        ll.addWidget(self.log_view, 1)
        root.addWidget(log_card, 1)

        self.start_btn.clicked.connect(self._start)
        self.stop_btn.clicked.connect(self._stop)
        self.update_btn.clicked.connect(self._download)
        self.connect_btn.clicked.connect(self._open_telegram)

    # ------------------------------------------------------------------

    def _download(self):
        if self._worker and self._worker.isRunning():
            self.append_log("! операция уже выполняется")
            return
        self.append_log("> скачивание Tg WS Proxy…")
        self.update_btn.setEnabled(False)
        self._worker = CommandWorker(
            self.z.telegram_download_cmd(), cwd=str(self.z.repo_root),
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(lambda m: self.append_log(f"! {m}"))
        self._worker.success.connect(self._on_done)
        self._worker.start()

    def _start(self):
        if self.z.telegram_running():
            self.append_log("! Tg WS Proxy уже запущен")
            return
        if self.z.telegram_start():
            self.append_log("> запущен Tg WS Proxy (откроется окно настроек)")
        else:
            self.append_log("! не скачан — нажмите «Скачать/обновить»")
        self.refresh()

    def _stop(self):
        self.z.telegram_stop()
        self.append_log("> Tg WS Proxy остановлен")
        self.refresh()

    def _on_done(self, _):
        self.update_btn.setEnabled(True)
        self.append_log("> готово")
        self.refresh()

    def _open_telegram(self):
        import webbrowser
        link = self.z.telegram_connect_link()
        if not link:
            self.append_log("! secret ещё не создан — сначала запустите Tg WS Proxy "
                            "и один раз настройте его в окне")
            return
        try:
            webbrowser.open(link)
            self.append_log(f"> открываю: {link}")
        except Exception as exc:
            self.append_log(f"! не удалось открыть: {exc}")

    def refresh(self):
        running = self.z.telegram_running()
        cfg = self.z.telegram_config()
        inst = self.z.telegram_installed() or "не скачан"
        if running:
            self.state_label.setText("[TG WS PROXY: РАБОТАЕТ]")
            self.state_label.setStyleSheet("color: #66bb6a;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.state_label.setText("[TG WS PROXY: ОСТАНОВЛЕН]")
            self.state_label.setStyleSheet("color: #616161;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
        host = cfg.get("host", "127.0.0.1")
        port = cfg.get("port", 1443)
        secret = "задан" if cfg.get("secret") else "ещё нет (нужен первый запуск)"
        self.info.setText(
            f"Компонент: {inst}\nПрокси: {host}:{port} · secret: {secret}"
        )

    def append_log(self, text):
        log_line(self.log_view, text)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
