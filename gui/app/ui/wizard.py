# =============================================================================
# Мастер первого запуска — права, ядро, способ обхода, запуск
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import getpass

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ..zapret import Zapret
from ..worker import CommandWorker
from .widgets import log_line, make_button, make_card

_GREEN = "#66bb6a"
_YELLOW = "#ffb74d"
_GRAY = "#616161"


class FirstRunWizard(QDialog):
    """Проводник первого запуска (показывается один раз)."""

    def __init__(self, zapret: Zapret, request_start=None, parent=None):
        super().__init__(parent)
        self.z = zapret
        self.request_start = request_start
        self._workers = []
        self._advance_pending = False
        self._strategy_applied = False
        self.setWindowTitle("Настройка Zapret Discord YouTube")
        self.setModal(True)
        self.setMinimumSize(720, 540)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(12)

        self.stack = QStackedWidget()
        self._pages = [
            self._build_intro(),
            self._build_rights(),
            self._build_core(),
            self._build_strategy(),
            self._build_done(),
        ]
        for page in self._pages:
            self.stack.addWidget(page)
        root.addWidget(self.stack, 1)

        # Навигация
        nav = QHBoxLayout()
        nav.setSpacing(10)
        self.back_btn = make_button("← Назад")
        self.back_btn.setMinimumWidth(120)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        self.next_btn = make_button("Далее →", primary=True)
        self.next_btn.setMinimumWidth(140)
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

        self.back_btn.clicked.connect(self._go_back)
        self.next_btn.clicked.connect(self._go_next)
        self._index = 0
        self._update_nav()
        self._refresh_statuses()

    # ------------------------------------------------------------------
    # Страницы
    # ------------------------------------------------------------------

    def _base_page(self, title, desc):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        t = QLabel(title)
        t.setProperty("title", True)
        layout.addWidget(t)
        d = QLabel(desc)
        d.setProperty("subtitle", True)
        d.setWordWrap(True)
        layout.addWidget(d)
        return page, layout

    def _build_intro(self):
        page, layout = self._base_page(
            "Добро пожаловать",
            "За пару шагов настроим обход замедления для YouTube и Discord. "
            "Понадобится один раз ввести пароль от вашей учётной записи.",
        )
        card = make_card()
        cl = card.layout()
        for line in (
            "1. Разрешим запуск без запроса пароля (один раз).",
            "2. Проверим ядро nfqws.",
            "3. Выберем способ обхода.",
            "4. Включим.",
        ):
            cl.addWidget(QLabel(line))
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_rights(self):
        page, layout = self._base_page(
            "Работа без пароля",
            "Для включения/выключения обхода нужны права администратора. "
            "Настроим их один раз — дальше программа будет работать сама.",
        )
        self.rights_status = QLabel()
        self.rights_status.setObjectName("statusLabel")
        layout.addWidget(self.rights_status)

        self.rights_btn = make_button("🔑 Ввести пароль и настроить", primary=True)
        self.rights_btn.setMinimumWidth(300)
        layout.addWidget(self.rights_btn)
        self.rights_btn.clicked.connect(self._setup_rights)

        self.rights_log = QPlainTextEdit()
        self.rights_log.setObjectName("logView")
        self.rights_log.setReadOnly(True)
        self.rights_log.setMaximumHeight(120)
        self.rights_log.setVisible(False)
        layout.addWidget(self.rights_log)
        layout.addStretch()
        return page

    def _build_core(self):
        page, layout = self._base_page(
            "Ядро nfqws",
            "Это движок, который выполняет обход. Если его нет — скачаем.",
        )
        self.core_status = QLabel()
        self.core_status.setObjectName("statusLabel")
        layout.addWidget(self.core_status)

        self.core_btn = make_button("⬇ Скачать ядро nfqws", primary=True)
        self.core_btn.setMinimumWidth(300)
        layout.addWidget(self.core_btn)
        self.core_btn.clicked.connect(self._download_core)

        self.core_log = QPlainTextEdit()
        self.core_log.setObjectName("logView")
        self.core_log.setReadOnly(True)
        self.core_log.setMaximumHeight(160)
        self.core_log.setVisible(False)
        layout.addWidget(self.core_log)
        layout.addStretch()
        return page

    def _build_strategy(self):
        page, layout = self._base_page(
            "Способ обхода",
            "Способ обхода — как именно обманывать замедление. Рекомендованная "
            "обычно работает; если нет — всегда можно поменять в «Конфигурации».",
        )
        self.strategy_combo = QComboBox()
        self.strategy_combo.setMinimumHeight(34)
        layout.addWidget(self.strategy_combo)
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)

        self.strategy_desc = QLabel("—")
        self.strategy_desc.setObjectName("statusMetaLabel")
        self.strategy_desc.setWordWrap(True)
        layout.addWidget(self.strategy_desc)

        self.strategy_btn = make_button("💾 Применить способ", primary=True)
        self.strategy_btn.setMinimumWidth(300)
        layout.addWidget(self.strategy_btn)
        self.strategy_btn.clicked.connect(self._save_strategy)

        self.strategy_log = QPlainTextEdit()
        self.strategy_log.setObjectName("logView")
        self.strategy_log.setReadOnly(True)
        self.strategy_log.setMaximumHeight(120)
        self.strategy_log.setVisible(False)
        layout.addWidget(self.strategy_log)
        layout.addStretch()
        return page

    def _build_done(self):
        page, layout = self._base_page(
            "Готово!",
            "Настройка завершена. Можете сразу включить обход или сделать это "
            "позже со вкладки «Статус».",
        )
        self.summary = QLabel()
        self.summary.setObjectName("statusMetaLabel")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.start_check = QCheckBox("Включить обход после закрытия мастера")
        self.start_check.setChecked(True)
        layout.addWidget(self.start_check)
        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Навигация
    # ------------------------------------------------------------------

    def _update_nav(self):
        self.back_btn.setEnabled(self._index > 0)
        if self._index == len(self._pages) - 1:
            self.next_btn.setText("Завершить")
        else:
            self.next_btn.setText("Далее →")
        # На странице прав можно идти дальше без настройки, но напомним
        if self._index == 1:
            self.next_btn.setText("Пропустить →")

    def _go_back(self):
        if self._index > 0:
            self._index -= 1
            self.stack.setCurrentIndex(self._index)
            self._update_nav()

    def _go_next(self):
        # На странице способа обхода применяем выбранное, если оно отличается
        if self._index == 3 and not self._strategy_applied:
            self.next_btn.setEnabled(False)
            self._save_strategy(advance=True)
            return
        self._do_advance()

    def _maybe_advance(self):
        if self._advance_pending:
            self._advance_pending = False
            self.next_btn.setEnabled(True)
            self._do_advance()

    def _do_advance(self):
        if self._index >= len(self._pages) - 1:
            self._finish()
            return
        self._index += 1
        self.stack.setCurrentIndex(self._index)
        self._update_nav()

    def _finish(self):
        QSettings().setValue("wizard/done", True)
        if self.start_check.isChecked() and self.request_start is not None:
            try:
                self.request_start()
            except Exception:
                pass
        self.accept()

    # ------------------------------------------------------------------
    # Шаг: права
    # ------------------------------------------------------------------

    def _setup_rights(self):
        if any(w.isRunning() for w in self._workers):
            return
        self.rights_log.setVisible(True)
        self._log_view = self.rights_log
        self._log(self.rights_log, "> настройка прав…")
        self.rights_btn.setEnabled(False)
        user = getpass.getuser()

        if self.z.sudo_available():
            self._run(self.z.setup_permissions_cmd(user), elevated=True,
                      on_done=self._rights_done, on_fail=self._rights_fail)
            return

        password, ok = QInputDialog.getText(
            self, "Пароль sudo",
            f"Введите пароль пользователя {user}\n(нужен один раз):",
            QLineEdit.Password,
        )
        if not ok or not password:
            self.rights_btn.setEnabled(True)
            self._log(self.rights_log, "! отменено")
            return
        self._run(self.z.setup_permissions_cmd(user), elevated=False,
                  password=password, on_done=self._rights_done,
                  on_fail=self._rights_fail)

    def _rights_done(self):
        self.rights_btn.setEnabled(True)
        self._log(self.rights_log, "> настройка завершена")
        self._refresh_statuses()

    def _rights_fail(self, msg):
        self.rights_btn.setEnabled(True)
        self._log(self.rights_log, f"! ошибка: {msg}")
        self._log(self.rights_log, "! можно повторить позже во вкладке «Права»")
        self._refresh_statuses()

    # ------------------------------------------------------------------
    # Шаг: ядро
    # ------------------------------------------------------------------

    def _download_core(self):
        if any(w.isRunning() for w in self._workers):
            return
        self.core_log.setVisible(True)
        self._log_view = self.core_log
        self._log(self.core_log, "> скачивание ядра…")
        self.core_btn.setEnabled(False)
        self._run(self.z.download_nfqws_cmd(), elevated=True,
                  on_done=self._core_done, on_fail=self._core_fail)

    def _core_done(self):
        self.core_btn.setEnabled(True)
        self._log(self.core_log, "> ядро готово")
        self._refresh_statuses()

    def _core_fail(self, msg):
        self.core_btn.setEnabled(True)
        self._log(self.core_log, f"! ошибка: {msg}")
        if "пароль" in msg.lower() or "nopasswd" in msg.lower():
            self._log(self.core_log,
                      "! Сначала настройте права на предыдущем шаге или во вкладке «Права».")
        self._refresh_statuses()

    # ------------------------------------------------------------------
    # Шаг: стратегия
    # ------------------------------------------------------------------

    def _refresh_strategy_list(self):
        current = self.z.read_config().get("strategy", "")
        self.strategy_combo.blockSignals(True)
        self.strategy_combo.clear()
        self.strategy_combo.addItems(self.z.strategies())
        idx = self.strategy_combo.findText(current) if current else -1
        if idx < 0:
            idx = self.strategy_combo.findText("general.bat")
        self.strategy_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.strategy_combo.blockSignals(False)
        self._on_strategy_changed()

    def _on_strategy_changed(self):
        self._update_strategy_desc()
        cfg = self.z.read_config().get("strategy", "")
        name = self.strategy_combo.currentText()
        self._strategy_applied = bool(name and name == cfg)
        if self._strategy_applied:
            self.strategy_btn.setText("💾 Применить способ")
        else:
            self.strategy_btn.setText("💾 Применить способ (изменён)")

    def _update_strategy_desc(self):
        name = self.strategy_combo.currentText()
        desc = self.z.strategy_description(name) if name else ""
        self.strategy_desc.setText(desc or "Описание не найдено")

    def _save_strategy(self, advance=False):
        if any(w.isRunning() for w in self._workers):
            if advance:
                self._advance_pending = True
            return
        name = self.strategy_combo.currentText()
        if not name:
            self._log(self.strategy_log, "! выберите способ")
            return
        self.strategy_log.setVisible(True)
        self._log_view = self.strategy_log
        self.strategy_btn.setEnabled(False)
        self._advance_pending = advance
        cfg = self.z.read_config()
        cmd = self.z.config_set_cmd(
            name,
            cfg.get("interface", "any"),
            cfg.get("gamefiltertcp") == "true",
            cfg.get("gamefilterudp") == "true",
            firewall_backend=cfg.get("firewall_backend", "auto"),
            restart=False,
        )
        self._log(self.strategy_log, f"> применяю способ: {name}")
        self._run(cmd, elevated=True,
                  on_done=self._strategy_done, on_fail=self._strategy_fail)

    def _strategy_done(self):
        self.strategy_btn.setEnabled(True)
        self._log(self.strategy_log, "> способ сохранён")
        self._on_strategy_changed()
        self._refresh_summary()
        self._maybe_advance()

    def _strategy_fail(self, msg):
        self.strategy_btn.setEnabled(True)
        self._log(self.strategy_log, f"! не удалось сохранить: {msg}")
        self._log(self.strategy_log,
                  "! можно повторить «Применить» или продолжить без сохранения "
                  "(способ можно выбрать позже во вкладке «Конфигурация»)")
        self._strategy_applied = True
        self.next_btn.setEnabled(True)
        self._advance_pending = False

    # ------------------------------------------------------------------
    # Состояния и служебное
    # ------------------------------------------------------------------

    def _refresh_statuses(self):
        # Права
        if self.z.sudo_available():
            self.rights_status.setText("[ПРАВА: ГОТОВО]")
            self.rights_status.setStyleSheet(f"color: {_GREEN};")
            self.rights_btn.setText("🔑 Переустановить права")
        else:
            self.rights_status.setText("[ПРАВА: НЕ НАСТРОЕНЫ]")
            self.rights_status.setStyleSheet(f"color: {_YELLOW};")
            self.rights_btn.setText("🔑 Ввести пароль и настроить")

        # Ядро
        if self.z.nfqws_present():
            ver = self.z.nfqws_installed_version()
            self.core_status.setText(f"[ЯДРО: {ver or 'УСТАНОВЛЕНО'}]")
            self.core_status.setStyleSheet(f"color: {_GREEN};")
            self.core_btn.setText("⬇ Переустановить ядро")
        else:
            self.core_status.setText("[ЯДРО: НЕ СКАЧАНО]")
            self.core_status.setStyleSheet(f"color: {_YELLOW};")
            self.core_btn.setText("⬇ Скачать ядро nfqws")

    def _run(self, cmd, elevated=False, password=None, on_done=None, on_fail=None):
        w = CommandWorker(cmd, cwd=str(self.z.repo_root),
                          elevated=elevated, password=password)
        w.output.connect(lambda t: self._log(self._log_view, t))
        if on_fail:
            w.failed.connect(on_fail)
        if on_done:
            w.success.connect(on_done)
        self._workers.append(w)
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        w.start()

    @staticmethod
    def _log(view, text):
        log_line(view, text)
        sb = view.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def _refresh_summary(self):
        cfg = self.z.read_config()
        strategy = cfg.get("strategy", "") or self.strategy_combo.currentText() or "—"
        rights = "настроены" if self.z.sudo_available() else "не настроены"
        core = self.z.nfqws_installed_version() or ("скачано" if self.z.nfqws_present() else "не скачано")
        self.summary.setText(
            f"Права: {rights}\nЯдро nfqws: {core}\nСпособ обхода: {strategy}\n\n"
            "Если что-то не получилось на каком-то шаге — просто пропустите, "
            "потом всё можно доделать во вкладках «Права», «Обновление» и «Конфигурация»."
        )

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_strategy_list()
        self._refresh_statuses()
        self._refresh_summary()

    def closeEvent(self, event):
        for w in self._workers:
            if w.isRunning():
                w.stop()
        event.accept()
