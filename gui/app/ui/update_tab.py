# =============================================================================
# Вкладка «Обновление» — проверка версии и обновление программы
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import os
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..updater import APP_VERSION, CheckWorker, git_pull_cmd, is_newer
from ..worker import CommandWorker
from .widgets import add_row, make_button, make_card, make_title

DEFAULT_NOTES = (
    "Обновление содержит исправления и улучшения.\n"
    "Подробный список изменений — в CHANGELOG.md репозитория."
)


class UpdateTab(QWidget):
    go_to_tab = Signal()

    def __init__(self, zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._checker = None
        self.latest_tag = ""
        self.latest_notes = ""
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(make_title(
            "Обновление",
            "Проверка новой версии и обновление программы",
        ))

        info_card = make_card()
        il = info_card.layout()
        self.current_value = QLabel(APP_VERSION)
        self.current_value.setObjectName("valueLabel")
        il.addWidget(add_row("Текущая версия", self.current_value))
        self.latest_value = QLabel("—")
        self.latest_value.setObjectName("valueLabel")
        il.addWidget(add_row("Доступная версия", self.latest_value))

        self.status_label = QLabel("Для проверки нажмите «Проверить обновления»")
        self.status_label.setObjectName("subtitleLabel")
        self.status_label.setWordWrap(True)
        il.addWidget(self.status_label)
        root.addWidget(info_card)

        notes_card = make_card()
        nl = notes_card.layout()
        header = QLabel(">_ что изменилось")
        header.setObjectName("logHeader")
        nl.addWidget(header)
        self.notes_view = QPlainTextEdit()
        self.notes_view.setObjectName("logView")
        self.notes_view.setReadOnly(True)
        self.notes_view.setPlaceholderText("Здесь появится описание обновления")
        nl.addWidget(self.notes_view, 1)
        root.addWidget(notes_card, 1)

        log_card = make_card()
        ll = log_card.layout()
        log_header = QLabel(">_ вывод обновления")
        log_header.setObjectName("logHeader")
        ll.addWidget(log_header)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        ll.addWidget(self.log_view, 1)
        root.addWidget(log_card, 1)

        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)
        self.check_btn = make_button("⟳ Проверить обновления")
        self.update_btn = make_button("⬇ Обновить", primary=True)
        self.update_btn.setEnabled(False)
        bl.addWidget(self.check_btn)
        bl.addStretch()
        bl.addWidget(self.update_btn)
        root.addWidget(btn_row)

        self.check_btn.clicked.connect(lambda: self.check_now(show_dialog=False))
        self.update_btn.clicked.connect(self.do_update)

    # ------------------------------------------------------------------

    def check_now(self, show_dialog=False):
        if self._checker and self._checker.isRunning():
            return
        self.status_label.setText("> проверка обновлений…")
        self.check_btn.setEnabled(False)
        self._checker = CheckWorker(parent=self)
        self._checker.result.connect(lambda res: self._on_check(res, show_dialog))
        self._checker.start()

    def _on_check(self, res, show_dialog):
        tag, notes, error = res
        self.check_btn.setEnabled(True)
        if error:
            self.status_label.setText(f"! не удалось проверить обновления: {error}")
            return
        self.latest_tag = tag
        self.latest_notes = notes
        self.latest_value.setText(tag or "—")
        self.notes_view.setPlainText(notes or DEFAULT_NOTES)
        if is_newer(tag):
            self.status_label.setText(f"✓ доступна новая версия {tag}")
            self.update_btn.setEnabled(True)
            if show_dialog:
                self._show_update_dialog()
        else:
            self.status_label.setText("✓ у вас актуальная версия")
            self.update_btn.setEnabled(False)

    # ------------------------------------------------------------------

    def _show_update_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Доступно обновление")
        dlg.setModal(True)
        dlg.setMinimumWidth(460)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"Доступна новая версия {self.latest_tag}")
        title.setProperty("title", True)
        layout.addWidget(title)

        sub = QLabel(f"Текущая версия: {APP_VERSION} → {self.latest_tag}")
        sub.setObjectName("subtitleLabel")
        layout.addWidget(sub)

        notes = QPlainTextEdit()
        notes.setObjectName("logView")
        notes.setReadOnly(True)
        notes.setPlainText(self.latest_notes or DEFAULT_NOTES)
        notes.setMinimumHeight(180)
        layout.addWidget(notes)

        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)
        later = make_button("Позже")
        update = make_button("Обновить сейчас", primary=True)
        bl.addStretch()
        bl.addWidget(later)
        bl.addWidget(update)
        layout.addWidget(btn_row)

        later.clicked.connect(dlg.reject)
        update.clicked.connect(dlg.accept)
        dlg.exec()

        if dlg.result():
            self.go_to_tab.emit()
            self.do_update()

    # ------------------------------------------------------------------

    def do_update(self):
        if self._worker and self._worker.isRunning():
            self.append_log("! обновление уже идёт")
            return
        self.update_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.status_label.setText("> обновление…")
        self.append_log("> git pull (обновление программы)")
        self._worker = CommandWorker(
            git_pull_cmd(str(self.z.repo_root)), cwd=str(self.z.repo_root),
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_failed)
        self._worker.success.connect(self._on_done)
        self._worker.start()

    def _on_done(self, _):
        self.check_btn.setEnabled(True)
        self.status_label.setText("✓ обновление установлено. Перезапустите приложение")
        self.append_log("> обновление завершено. Перезапустите приложение")
        if self._ask_restart():
            self._restart_app()

    def _on_failed(self, msg):
        self.update_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        self.status_label.setText(f"! ошибка обновления: {msg}")
        self.append_log(f"! ошибка: {msg}")

    def _ask_restart(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Перезапуск")
        dlg.setModal(True)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        label = QLabel("Обновление установлено. Перезапустить приложение сейчас?")
        label.setWordWrap(True)
        layout.addWidget(label)
        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)
        later = make_button("Позже")
        restart = make_button("Перезапустить", primary=True)
        bl.addStretch()
        bl.addWidget(later)
        bl.addWidget(restart)
        layout.addWidget(btn_row)
        later.clicked.connect(dlg.reject)
        restart.clicked.connect(dlg.accept)
        dlg.exec()
        return bool(dlg.result())

    def _restart_app(self):
        os.chdir(str(self.z.repo_root))
        os.execv(sys.executable, [sys.executable, "-m", "gui.app.main"])

    def append_log(self, text):
        if text:
            self.log_view.appendPlainText(text)
