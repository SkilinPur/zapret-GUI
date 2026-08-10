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
            "Файлы .bat из custom-strategies и zapret-latest (поставляются в комплекте)",
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
        self.strategies_btn = make_button("⬇ Обновить стратегии", primary=True)
        self.nfqws_btn = make_button("⬇ Скачать nfqws")
        bl.addWidget(self.refresh_btn)
        bl.addStretch()
        bl.addWidget(self.strategies_btn)
        bl.addWidget(self.nfqws_btn)
        cl.addWidget(btn_row)

        root.addWidget(card, 1)

        log_card = make_card()
        ll = log_card.layout()
        header = QLabel(">_ вывод")
        header.setObjectName("logHeader")
        ll.addWidget(header)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        ll.addWidget(self.log_view, 1)
        root.addWidget(log_card, 1)

        self.refresh_btn.clicked.connect(self.reload_strategies)
        self.strategies_btn.clicked.connect(self.update_strategies)
        self.nfqws_btn.clicked.connect(self.download_nfqws)

    # ------------------------------------------------------------------

    def reload_strategies(self):
        self.strategy_list.clear()
        self.strategy_list.addItems(self.z.strategies())
        self.append_log(
            f"> найдено стратегий: {self.strategy_list.count()} "
            f"(nfqws {'скачан' if self.z.nfqws_present() else 'НЕ скачан'})"
        )

    def _guard_running(self):
        if self._worker and self._worker.isRunning():
            self.append_log("! команда уже выполняется")
            return True
        return False

    def update_strategies(self):
        if self._guard_running():
            return
        self.append_log("> запуск update-strategies (git clone из Flowseal, sudo)")
        self._run(self.z.update_strategies_cmd(), self.strategies_btn)

    def download_nfqws(self):
        if self._guard_running():
            return
        self.append_log("> запуск download-nfqws (sudo)")
        self._run(self.z.download_nfqws_cmd(), self.nfqws_btn)

    def _run(self, cmd, button):
        button.setEnabled(False)
        self._worker = CommandWorker(cmd, cwd=str(self.z.repo_root), elevated=True)
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(lambda msg: self._on_failed(msg, button))
        self._worker.success.connect(lambda _: self._on_done(button))
        self._worker.start()

    def _on_done(self, button):
        button.setEnabled(True)
        self.append_log("> готово")
        self.reload_strategies()

    def _on_failed(self, msg, button):
        button.setEnabled(True)
        self.append_log(f"! ошибка: {msg}")

    def append_log(self, text):
        log_line(self.log_view, text)

