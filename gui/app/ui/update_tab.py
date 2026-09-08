# =============================================================================
# Вкладка «Обновление» — проверка версии и обновление программы
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import getpass
import os
import sys

from PySide6.QtCore import Qt, Signal
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
        self._comp_zapret = ""
        self._comp_flowseal = ""
        self.latest_tag = ""
        self.latest_notes = ""
        self._versions = []
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

        # --- Компоненты: ядро nfqws и стратегии Flowseal -----------------
        comp_card = make_card()
        cml = comp_card.layout()
        comp_header = QLabel(">_ компоненты")
        comp_header.setObjectName("logHeader")
        cml.addWidget(comp_header)

        self.nfqws_text = QLabel("—")
        self.nfqws_text.setObjectName("valueLabel")
        self.nfqws_text.setWordWrap(True)
        self.nfqws_btn = make_button("Скачать nfqws")
        self.nfqws_btn.setMinimumWidth(150)
        cml.addWidget(add_row("Ядро nfqws", self._row(self.nfqws_text, self.nfqws_btn)))

        self.strat_text = QLabel("—")
        self.strat_text.setObjectName("valueLabel")
        self.strat_text.setWordWrap(True)
        self.strat_btn = make_button("Обновить стратегии")
        self.strat_btn.setMinimumWidth(150)
        cml.addWidget(add_row("Стратегии Flowseal", self._row(self.strat_text, self.strat_btn)))

        self.comp_status = QLabel("Нажмите «Проверить обновления» — обновит и компоненты")
        self.comp_status.setObjectName("subtitleLabel")
        self.comp_status.setWordWrap(True)
        cml.addWidget(self.comp_status)
        root.addWidget(comp_card)

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
        self.version_combo.currentIndexChanged.connect(self._show_selected_version)
        self.nfqws_btn.clicked.connect(lambda: self._run_component("nfqws"))
        self.strat_btn.clicked.connect(lambda: self._run_component("strat"))
        self._load_changelog()
        self._refresh_component_installed()

    # ------------------------------------------------------------------
    # Компоненты (ядро nfqws и стратегии Flowseal)
    # ------------------------------------------------------------------

    def _row(self, text_label, button):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(text_label, 1)
        layout.addWidget(button)
        return row

    def _refresh_component_installed(self):
        """Обновляет «установлено» по локальным данным (без сети)."""
        nfqws = self.z.nfqws_installed_version()
        strat = _short(self.z.flowseal_installed_rev())
        self._comp_nfqws_installed = nfqws
        self._comp_strat_installed = strat
        self._set_component_texts()

    def _set_component_texts(self):
        nfqws = getattr(self, "_comp_nfqws_installed", "") or "—"
        strat = getattr(self, "_comp_strat_installed", "") or "—"
        if self._comp_zapret:
            nfqws += f"  ·  доступно {self._comp_zapret}"
        if self._comp_flowseal:
            strat += f"  ·  доступно {_short(self._comp_flowseal)}"
        self.nfqws_text.setText(nfqws)
        self.strat_text.setText(strat)

    def _on_components(self, res):
        self._comp_zapret, self._comp_flowseal, error = res
        if error:
            self.comp_status.setText(f"! {error}")
        else:
            self.comp_status.setText("✓ версии компонентов получены")
        self._set_component_texts()

    def _run_component(self, which):
        if self._worker and self._worker.isRunning():
            self.append_log("! команда уже выполняется")
            return
        cmd = self.z.download_nfqws_cmd() if which == "nfqws" else self.z.update_strategies_cmd()
        self.append_log(f"> {'download-nfqws' if which == 'nfqws' else 'update-strategies'}")
        self.comp_status.setText("> выполняется…")
        self._worker = CommandWorker(cmd, cwd=str(self.z.repo_root), elevated=True)
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(lambda msg: self._on_component_failed(msg, which))
        self._worker.success.connect(lambda _: self._on_component_done(which))
        self._worker.start()

    def _on_component_done(self, which):
        name = "ядро nfqws" if which == "nfqws" else "стратегии Flowseal"
        self.append_log(f"> {name}: обновлено")
        self.comp_status.setText(f"✓ {name} обновлено")
        self._refresh_component_installed()
        # Свежая доступная версия стратегий изменилась — переспрашиваем компоненты
        self._start_components_check()

    def _on_component_failed(self, msg, which):
        self.append_log(f"! ошибка: {msg}")

    def _start_components_check(self):
        if self._comp_worker and self._comp_worker.isRunning():
            return
        self._comp_worker = ComponentsWorker(parent=self)
        self._comp_worker.result.connect(self._on_components)
        self._comp_worker.start()

    # ------------------------------------------------------------------

    def _load_changelog(self):
        """Читает CHANGELOG.md и заполняет список версий."""
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
        """Добавляет новую версию сверху списка и выбирает её."""
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
        """Текст changelog для самой свежей доступной версии."""
        tag = self.latest_tag[1:] if self.latest_tag.startswith("v") else self.latest_tag
        return self._version_body(tag)

    def check_now(self, show_dialog=False):
        if self._checker and self._checker.isRunning():
            return
        self.status_label.setText("> проверка обновлений…")
        self.check_btn.setEnabled(False)
        self.comp_status.setText("> проверка версий компонентов…")
        self._start_components_check()
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
        if is_newer(tag):
            self._prepend_new_version(tag, notes)
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

    # ------------------------------------------------------------------

    def do_update(self):
        if self._worker and self._worker.isRunning():
            self.append_log("! обновление уже идёт")
            return
        self.update_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.status_label.setText("> обновление…")
        repo_root = str(self.z.repo_root)
        zapret_dir = os.path.join(repo_root, "zapret-latest")
        if os.path.exists(zapret_dir) and not os.access(zapret_dir, os.W_OK):
            self._start_ownership_fix(repo_root)
            return
        self._run_git_pull(repo_root)

    def _start_ownership_fix(self, repo_root):
        """zapret-latest создан от root и не даёт писать — пробуем вернуть владельца."""
        user = getpass.getuser()
        self.append_log(
            f"! {os.path.join(repo_root, 'zapret-latest')} не доступен для записи (создан от root)"
        )
        self.status_label.setText("> восстанавливаю права на файлы…")
        self._worker = CommandWorker(["chown", "-R", user, repo_root], elevated=True)
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_ownership_fix_failed)
        self._worker.success.connect(lambda _: self._run_git_pull(repo_root))
        self._worker.start()

    def _on_ownership_fix_failed(self, msg):
        self.update_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        user = getpass.getuser()
        repo_root = str(self.z.repo_root)
        self.status_label.setText(f"! ошибка обновления: {msg}")
        self.append_log(f"! не удалось восстановить права: {msg}")
        self.append_log(f'! выполните в терминале: sudo chown -R {user} "{repo_root}"')
        self.append_log("! затем нажмите «Обновить» ещё раз")

    def _run_git_pull(self, repo_root):
        self.append_log("> git pull (обновление программы)")
        self._worker = CommandWorker(
            git_pull_cmd(repo_root), cwd=repo_root,
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
        log_line(self.log_view, text)
