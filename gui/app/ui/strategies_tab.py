# =============================================================================
# Вкладка «Стратегии» — список стратегий и загрузка зависимостей
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..zapret import Zapret
from ..worker import CommandWorker
from .widgets import log_line, make_button, make_card, make_title


class StrategiesTab(QWidget):
    def __init__(self, zapret: Zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._build_ui()
        self.reload_strategies()

    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(make_title(
            "Стратегии",
            "Файлы .bat из custom-strategies и zapret-latest",
        ))

        card = make_card()
        cl = card.layout()

        self.strategy_list = QListWidget()
        self.strategy_list.setObjectName("strategyList")
        cl.addWidget(self.strategy_list, 1)

        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)
        self.refresh_btn = make_button("⟳ Обновить список")
        self.download_btn = make_button("⬇ Скачать/обновить зависимости", primary=True)
        bl.addWidget(self.refresh_btn)
        bl.addStretch()
        bl.addWidget(self.download_btn)
        cl.addWidget(btn_row)

        root.addWidget(card, 1)

        log_card = make_card()
        ll = log_card.layout()
        header = QLabel(">_ вывод download-deps")
        header.setObjectName("logHeader")
        ll.addWidget(header)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        ll.addWidget(self.log_view, 1)
        root.addWidget(log_card, 1)

        self.refresh_btn.clicked.connect(self.reload_strategies)
        self.download_btn.clicked.connect(self.download_deps)

    # ------------------------------------------------------------------

    def reload_strategies(self):
        self.strategy_list.clear()
        self.strategy_list.addItems(self.z.strategies())
        self.append_log(
            f"> найдено стратегий: {self.strategy_list.count()} "
            f"(зависимости {'скачаны' if self.z.downloads_present() else 'НЕ скачаны'})"
        )

    def download_deps(self):
        if self._worker and self._worker.isRunning():
            self.append_log("! скачивание уже идёт")
            return
        self.append_log("> запуск download-deps --default (sudo)")
        self.download_btn.setEnabled(False)
        self._worker = CommandWorker(
            self.z.download_deps_cmd(), cwd=str(self.z.repo_root), elevated=True,
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_failed)
        self._worker.success.connect(self._on_done)
        self._worker.start()

    def _on_done(self, _):
        self.download_btn.setEnabled(True)
        self.append_log("> зависимости обновлены")
        self.reload_strategies()

    def _on_failed(self, msg):
        self.download_btn.setEnabled(True)
        self.append_log(f"! ошибка: {msg}")

    def append_log(self, text):
        log_line(self.log_view, text)

