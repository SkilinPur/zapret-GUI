# =============================================================================
# Вкладка «Обновление» — версии и обновление программы, ядра и стратегий
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import getpass
import os
import sys

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..changelog import changelog_versions
from ..updater import APP_VERSION, CheckWorker, ComponentsWorker, git_pull_cmd, is_newer
from ..worker import CommandWorker
from .widgets import add_row, log_line, make_button, make_card, make_title

DEFAULT_NOTES = (
    "Обновление содержит исправления и улучшения.\n"
    "Подробный список изменений — в CHANGELOG.md репозитория."
)


def _short(rev):
    return rev if not rev else (rev[:10] + "…" if len(rev) > 10 else rev)


class UpdateTab(QWidget):
    go_to_tab = Signal()

    def __init__(self, zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._checker = None
        self._comp_worker = None
        self._pending = []          # очередь обновлений для «Обновить всё»
        self.latest_tag = ""
        self.latest_notes = ""
        self._comp_zapret = ""
        self._comp_flowseal = ""
        self._versions = []
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(make_title(
            "Обновление",
            "Версии и обновление программы, ядра nfqws и стратегий Flowseal",
        ))

        # --- Верхние общие действия ------------------------------------
        top_row = QWidget()
        tl = QHBoxLayout(top_row)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(10)
        self.check_btn = make_button("⟳ Проверить всё")
        self.update_all_btn = make_button("⬇ Обновить всё", primary=True)
        self.update_all_btn.setEnabled(False)
        tl.addWidget(self.check_btn)
        tl.addStretch()
        tl.addWidget(self.update_all_btn)
        root.addWidget(top_row)

        # --- Модуль: программа ------------------------------------------
        prog_card = make_card()
        pl = prog_card.layout()
        prog_header = QLabel(">_ программа (GUI)")
        prog_header.setObjectName("logHeader")
        pl.addWidget(prog_header)

        self.current_value = QLabel(APP_VERSION)
        self.current_value.setObjectName("valueLabel")
        pl.addWidget(add_row("Текущая версия", self.current_value))
        self.latest_value = QLabel("—")
        self.latest_value.setObjectName("valueLabel")
        pl.addWidget(add_row("Доступная версия", self.latest_value))

        self.program_status = QLabel("Для проверки нажмите «Проверить всё»")
        self.program_status.setObjectName("subtitleLabel")
        self.program_status.setWordWrap(True)
        pl.addWidget(self.program_status)

        self.program_btn = make_button("Обновить программу")
        self.program_btn.setMinimumWidth(190)
        self.program_btn.setEnabled(False)
        pl.addWidget(self._right_row(self.program_btn))
        root.addWidget(prog_card)

        # --- Модуль: ядро nfqws ----------------------------------------
        core_card = make_card()
        cl = core_card.layout()
        core_header = QLabel(">_ ядро nfqws (bol-van/zapret)")
        core_header.setObjectName("logHeader")
        cl.addWidget(core_header)

        self.core_current_value = QLabel("—")
        self.core_current_value.setObjectName("valueLabel")
        cl.addWidget(add_row("Установлено", self.core_current_value))
        self.core_latest_value = QLabel("—")
        self.core_latest_value.setObjectName("valueLabel")
        cl.addWidget(add_row("Доступно", self.core_latest_value))

        self.core_status = QLabel("—")
        self.core_status.setObjectName("subtitleLabel")
        cl.addWidget(self.core_status)

        self.core_btn = make_button("Обновить ядро")
        self.core_btn.setMinimumWidth(190)
        self.core_btn.setEnabled(False)
        cl.addWidget(self._right_row(self.core_btn))
        root.addWidget(core_card)

        # --- Модуль: стратегии Flowseal --------------------------------
        strat_card = make_card()
        sl = strat_card.layout()
        strat_header = QLabel(">_ стратегии (Flowseal/zapret-discord-youtube)")
        strat_header.setObjectName("logHeader")
        sl.addWidget(strat_header)

        self.strat_current_value = QLabel("—")
        self.strat_current_value.setObjectName("valueLabel")
        sl.addWidget(add_row("Установлено", self.strat_current_value))
        self.strat_latest_value = QLabel("—")
        self.strat_latest_value.setObjectName("valueLabel")
        sl.addWidget(add_row("Доступно", self.strat_latest_value))

        self.strat_status = QLabel("—")
        self.strat_status.setObjectName("subtitleLabel")
        sl.addWidget(self.strat_status)

        self.strat_btn = make_button("Обновить стратегии")
        self.strat_btn.setMinimumWidth(190)
        self.strat_btn.setEnabled(False)
        sl.addWidget(self._right_row(self.strat_btn))
        root.addWidget(strat_card)

        # --- Что изменилось (changelog программы) -----------------------
        notes_card = make_card()
        nl = notes_card.layout()
        head_row = QWidget()
        hl = QHBoxLayout(head_row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)
        header = QLabel(">_ что изменилось")
        header.setObjectName("logHeader")
        hl.addWidget(header)
        hl.addStretch()
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(180)
        hl.addWidget(self.version_combo)
        nl.addWidget(head_row)
        self.notes_view = QPlainTextEdit()
        self.notes_view.setObjectName("logView")
        self.notes_view.setReadOnly(True)
        self.notes_view.setPlaceholderText("Здесь появится описание обновления")
        nl.addWidget(self.notes_view, 1)
        root.addWidget(notes_card, 1)

        # --- Лог обновления ---------------------------------------------
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

        self.check_btn.clicked.connect(lambda: self.check_now(show_dialog=False))
        self.update_all_btn.clicked.connect(self.do_update_all)
        self.version_combo.currentIndexChanged.connect(self._show_selected_version)
        self.program_btn.clicked.connect(self.do_update)
        self.core_btn.clicked.connect(lambda: self._run_update("core"))
        self.strat_btn.clicked.connect(lambda: self._run_update("strat"))
        self._load_changelog()
        self._refresh_installed()

    # ------------------------------------------------------------------
    # Вспомогательные
    # ------------------------------------------------------------------

    def _right_row(self, button):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(button)
        return row

    def _refresh_installed(self):
        """Установленные версии (локально, без сети)."""
        core = self.z.nfqws_installed_version()
        strat = self.z.flowseal_installed_rev()
        self.core_current_value.setText(core or "не установлено")
        self.strat_current_value.setText(_short(strat) if strat else "—")
        self._update_availability()

    def _update_availability(self):
        """Пересчитывает статусы и активность кнопок по известным версиям."""
        # Программа
        tag = self.latest_tag
        if not tag:
            self.program_btn.setEnabled(False)
        elif is_newer(tag):
            self.program_btn.setEnabled(True)
            self.program_status.setText(f"✓ доступна новая версия {tag}")
        else:
            self.program_btn.setEnabled(False)
            self.program_status.setText("✓ актуальная версия")

        # Ядро
        installed = self.z.nfqws_installed_version()
        latest = self._comp_zapret
        if not latest:
            self.core_btn.setEnabled(False)
            self.core_status.setText("—")
        elif not installed or installed != latest:
            self.core_btn.setEnabled(True)
            self.core_status.setText(f"доступно обновление: {latest}")
        else:
            self.core_btn.setEnabled(False)
            self.core_status.setText("✓ ядро актуально")

        # Стратегии
        rev = self.z.flowseal_installed_rev()
        head = self._comp_flowseal
        if not head:
            self.strat_btn.setEnabled(False)
            self.strat_status.setText("—")
        elif not rev or rev != head:
            self.strat_btn.setEnabled(True)
            self.strat_status.setText(f"доступно обновление: {_short(head)}")
        else:
            self.strat_btn.setEnabled(False)
            self.strat_status.setText("✓ стратегии актуальны")

        self.update_all_btn.setEnabled(
            bool((self.latest_tag and is_newer(self.latest_tag))
                 or self.core_btn.isEnabled() or self.strat_btn.isEnabled())
        )

    def _any_run(self):
        return (self._worker and self._worker.isRunning())

    # ------------------------------------------------------------------
    # Проверка версий
    # ------------------------------------------------------------------

    def check_now(self, show_dialog=False):
        if self._checker and self._checker.isRunning():
            return
        self.program_status.setText("> проверка…")
        self._start_components_check()
        self._checker = CheckWorker(parent=self)
        self._checker.result.connect(lambda res: self._on_check(res, show_dialog))
        self._checker.start()

    def _start_components_check(self):
        if self._comp_worker and self._comp_worker.isRunning():
            return
        self._comp_worker = ComponentsWorker(parent=self)
        self._comp_worker.result.connect(self._on_components)
        self._comp_worker.start()

    def _on_check(self, res, show_dialog):
        tag, notes, error = res
        if error:
            self.program_status.setText(f"! не удалось проверить обновления: {error}")
            return
        self.latest_tag = tag
        self.latest_notes = notes
        self.latest_value.setText(tag or "—")
        if is_newer(tag):
            self._prepend_new_version(tag, notes)
            self.program_status.setText(f"✓ доступна новая версия {tag}")
            if show_dialog:
                self._show_update_dialog()
        else:
            self.program_status.setText("✓ актуальная версия")
        self._update_availability()

    def _on_components(self, res):
        zapret_tag, flowseal_head, error = res
        if error:
            self.core_status.setText(f"! {error}")
            self.strat_status.setText(f"! {error}")
            return
        self._comp_zapret = zapret_tag
        self._comp_flowseal = flowseal_head
        self.core_latest_value.setText(zapret_tag or "—")
        self.strat_latest_value.setText(_short(flowseal_head) if flowseal_head else "—")
        self._update_availability()

    # ------------------------------------------------------------------
    # Changelog
    # ------------------------------------------------------------------

    def _load_changelog(self):
        self._versions = changelog_versions(self.z.repo_root)
        self.version_combo.clear()
        for version, date, _ in self._versions:
            self.version_combo.addItem(version if not date else f"{version} — {date}")
        if not self._versions:
            self.notes_view.setPlaceholderText("CHANGELOG.md не найден")
            return
        index = next(
            (i for i, (v, _, _) in enumerate(self._versions) if v == APP_VERSION), 0
        )
        self.version_combo.setCurrentIndex(index)

    def _show_selected_version(self, _index):
        index = self.version_combo.currentIndex()
        if 0 <= index < len(self._versions):
            self.notes_view.setPlainText(self._versions[index][2])

    def _version_body(self, version):
        for v, _, body in self._versions:
            if v == version:
                return body
        return ""

    def _prepend_new_version(self, tag, notes):
        version = tag[1:] if tag.startswith("v") else tag
        if any(v == version for v, _, _ in self._versions):
            self.version_combo.setCurrentIndex(
                next(i for i, (v, _, _) in enumerate(self._versions) if v == version)
            )
            return
        body = notes.strip() or (
            f"Список изменений для версии {version} появится после обновления."
        )
        self._versions.insert(0, (version, "", body))
        self.version_combo.insertItem(0, version)
        self.version_combo.setCurrentIndex(0)

    def _new_version_body(self):
        tag = self.latest_tag[1:] if self.latest_tag.startswith("v") else self.latest_tag
        return self._version_body(tag)

    # ------------------------------------------------------------------
    # Обновление модулей
    # ------------------------------------------------------------------

    def _run_update(self, which):
        """Запускает обновление одного модуля: program | core | strat."""
        if self._any_run():
            self.append_log("! команда уже выполняется")
            return
        if which == "core":
            self.append_log("> скачивание nfqws (ядро)")
            self._worker = CommandWorker(
                self.z.download_nfqws_cmd(), cwd=str(self.z.repo_root), elevated=True,
            )
        elif which == "strat":
            self.append_log("> обновление стратегий Flowseal")
            self._worker = CommandWorker(
                self.z.update_strategies_cmd(), cwd=str(self.z.repo_root), elevated=True,
            )
        else:
            self._start_program_update()
            return
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_step_failed)
        self._worker.success.connect(lambda _: self._on_step_done(which))
        self._worker.start()

    def _start_program_update(self):
        repo_root = str(self.z.repo_root)
        zapret_dir = os.path.join(repo_root, "zapret-latest")
        if os.path.exists(zapret_dir) and not os.access(zapret_dir, os.W_OK):
            self.append_log(f"! {zapret_dir} не доступен для записи (создан от root)")
            self._start_ownership_fix(repo_root)
            return
        self.append_log("> git pull (обновление программы)")
        self._worker = CommandWorker(git_pull_cmd(repo_root), cwd=repo_root)
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_step_failed)
        self._worker.success.connect(lambda _: self._on_program_done())
        self._worker.start()

    def _start_ownership_fix(self, repo_root):
        user = getpass.getuser()
        self.program_status.setText("> восстанавливаю права на файлы…")
        self._worker = CommandWorker(["chown", "-R", user, repo_root], elevated=True)
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_ownership_fix_failed)
        self._worker.success.connect(lambda _: self._start_program_update())
        self._worker.start()

    def _on_ownership_fix_failed(self, msg):
        user = getpass.getuser()
        repo_root = str(self.z.repo_root)
        self.program_status.setText(f"! ошибка обновления: {msg}")
        self.append_log(f"! не удалось восстановить права: {msg}")
        self.append_log(f'! выполните в терминале: sudo chown -R {user} "{repo_root}"')
        self.append_log("! затем нажмите «Обновить программу» ещё раз")
        self._next_step()

    def _on_step_done(self, which):
        name = {"core": "ядро nfqws", "strat": "стратегии"}[which]
        self.append_log(f"> {name}: обновлено")
        self._next_step()

    def _on_program_done(self):
        self.append_log("> обновление программы завершено. Перезапустите приложение")
        self.program_status.setText("✓ обновление установлено. Перезапустите приложение")
        self._next_step()
        if self._ask_restart():
            self._restart_app()

    def _on_step_failed(self, msg):
        self.append_log(f"! ошибка: {msg}")
        self._next_step()

    def _next_step(self):
        """После завершения шага: обновляем статусы и запускаем следующий из очереди."""
        self._refresh_installed()
        self._start_components_check()
        if self._pending:
            self._run_update(self._pending.pop(0))

    # ------------------------------------------------------------------
    # Обновить всё
    # ------------------------------------------------------------------

    def do_update_all(self):
        if self._any_run():
            self.append_log("! команда уже выполняется")
            return
        order = []
        if self.core_btn.isEnabled():
            order.append("core")
        if self.strat_btn.isEnabled():
            order.append("strat")
        if self.latest_tag and is_newer(self.latest_tag):
            order.append("program")
        if not order:
            self.append_log("> всё актуально, обновлять нечего")
            return
        self._pending = order
        self.append_log(f"> обновляю: {', '.join(order)}")
        self._run_update(self._pending.pop(0))

    # ------------------------------------------------------------------
    # Программа: диалог, перезапуск
    # ------------------------------------------------------------------

    def do_update(self):
        if self._any_run():
            self.append_log("! команда уже выполняется")
            return
        self._run_update("program")

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
        notes.setPlainText(self.latest_notes or self._new_version_body() or DEFAULT_NOTES)
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
        log_line(self.log_view, text)
