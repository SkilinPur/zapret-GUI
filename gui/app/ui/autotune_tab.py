# =============================================================================
# Вкладка «Подбор» — авто-подбор рабочих стратегий
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout,
    QWidget,
)

from ..zapret import Zapret
from ..worker import CommandWorker
from .widgets import add_row, make_button, make_card, make_title


class AutotuneTab(QWidget):
    def __init__(self, zapret: Zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._build_ui()
        self.refresh_results()

    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(make_title(
            "Автоподбор стратегий",
            "Экспериментально. Перебирает стратегии и проверяет доступность сервисов.",
        ))

        # --- YouTube ---
        yt_card = make_card()
        yl = yt_card.layout()
        yt_title = QLabel("YouTube")
        yt_title.setProperty("section", True)
        yl.addWidget(yt_title)
        yt_hint = QLabel("Проверяет доступ к YouTube, сохраняет результаты в "
                         "auto_tune_youtube_results.txt")
        yt_hint.setProperty("subtitle", True)
        yt_hint.setWordWrap(True)
        yl.addWidget(yt_hint)
        self.yt_btn = make_button("▶ Запустить подбор для YouTube", primary=True)
        self.yt_btn.setFixedWidth(280)
        yl.addWidget(self.yt_btn)
        root.addWidget(yt_card)

        # --- Произвольные домены ---
        dom_card = make_card()
        dl = dom_card.layout()
        dom_title = QLabel("Произвольные домены")
        dom_title.setProperty("section", True)
        dl.addWidget(dom_title)

        self.domains_edit = QLineEdit()
        self.domains_edit.setPlaceholderText("домен1.ру домен2.com ...")
        dl.addWidget(add_row("Домены", self.domains_edit))

        self.quic_check = QCheckBox("Проверять QUIC (HTTP/3)")
        dl.addWidget(self.quic_check)

        self.dom_btn = make_button("▶ Проверить домены", primary=True)
        self.dom_btn.setFixedWidth(280)
        dl.addWidget(self.dom_btn)
        root.addWidget(dom_card)

        # --- Результаты ---
        res_card = make_card()
        rl = res_card.layout()
        res_header = QLabel(">_ результаты")
        res_header.setObjectName("logHeader")
        rl.addWidget(res_header)

        self.results_view = QPlainTextEdit()
        self.results_view.setObjectName("logView")
        self.results_view.setReadOnly(True)
        self.results_view.setMaximumBlockCount(3000)
        rl.addWidget(self.results_view, 1)

        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        self.refresh_btn = make_button("⟳ Обновить результаты")
        bl.addWidget(self.refresh_btn)
        bl.addStretch()
        rl.addWidget(btn_row)

        root.addWidget(res_card, 1)

        self.yt_btn.clicked.connect(self.run_youtube)
        self.dom_btn.clicked.connect(self.run_domains)
        self.refresh_btn.clicked.connect(self.refresh_results)

    # ------------------------------------------------------------------

    def run_youtube(self):
        if self._worker and self._worker.isRunning():
            return
        self.append_log("> запуск auto_tune_youtube.sh (долго, не прерывайте)")
        self.yt_btn.setEnabled(False)
        self._worker = CommandWorker(
            self.z.autotune_youtube_cmd(), cwd=str(self.z.repo_root), elevated=True,
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_failed)
        self._worker.success.connect(self._on_done)
        self._worker.start()

    def run_domains(self):
        if self._worker and self._worker.isRunning():
            return
        domains = self.domains_edit.text().strip()
        if not domains:
            self.append_log("! укажите хотя бы один домен")
            return
        cmd, stdin = self.z.autotune_cmd(domains, self.quic_check.isChecked())
        self.append_log(f"> проверка доменов: {domains}")
        self.dom_btn.setEnabled(False)
        self._worker = CommandWorker(
            cmd, cwd=str(self.z.repo_root), elevated=True, stdin=stdin,
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_failed)
        self._worker.success.connect(self._on_done)
        self._worker.start()

    def _on_done(self, _):
        self.yt_btn.setEnabled(True)
        self.dom_btn.setEnabled(True)
        self.append_log("> готово")
        self.refresh_results()

    def _on_failed(self, msg):
        self.yt_btn.setEnabled(True)
        self.dom_btn.setEnabled(True)
        self.append_log(f"! ошибка: {msg}")

    def refresh_results(self):
        self.results_view.clear()
        for youtube in (True, False):
            path = self.z.autotune_results_file(youtube=youtube)
            if path:
                self.results_view.appendPlainText(
                    f"== {path.name} ==")
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    self.results_view.appendPlainText(content.strip() or "(пусто)")
                except OSError as exc:
                    self.results_view.appendPlainText(f"! не удалось прочитать: {exc}")
                self.results_view.appendPlainText("")

    def append_log(self, text):
        if text:
            self.results_view.appendPlainText(text)

