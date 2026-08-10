# =============================================================================
# Вкладка «Права» — настройка работы без пароля (NOPASSWD sudo)
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtWidgets import (
    QInputDialog, QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget,
)

import getpass

from ..zapret import Zapret
from ..worker import CommandWorker
from .widgets import log_line, make_button, make_card, make_title


class PermissionsTab(QWidget):
    def __init__(self, zapret: Zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._build_ui()
        self.refresh_status()

    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(make_title(
            "Права",
            "Настройка запуска zapret без ввода пароля",
        ))

        card = make_card()
        cl = card.layout()

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        cl.addWidget(self.status_label)

        hint = QLabel(
            "Для запуска/остановки zapret нужны права root. Кнопка добавляет "
            "в sudoers NOPASSWD-правила для nft/iptables/nfqws/pkill и запуска "
            "service.sh, чтобы GUI мог работать без пароля.\n"
            "Будет запрошен ваш пароль sudo (пароль учётной записи, не root). "
            "Если NOPASSWD уже работает — кнопка просто обновит правила "
            "(например, после обновления программы)."
        )
        hint.setProperty("subtitle", True)
        hint.setWordWrap(True)
        cl.addWidget(hint)

        self.setup_btn = make_button("🔑 Настроить работу без пароля", primary=True)
        self.setup_btn.setFixedWidth(280)
        cl.addWidget(self.setup_btn)

        root.addWidget(card)

        log_card = make_card()
        ll = log_card.layout()
        header = QLabel(">_ вывод")
        header.setObjectName("logHeader")
        ll.addWidget(header)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(1000)
        ll.addWidget(self.log_view, 1)
        root.addWidget(log_card, 1)

        self.setup_btn.clicked.connect(self.setup_permissions)

    # ------------------------------------------------------------------

    def refresh_status(self):
        ok = self.z.sudo_available()
        if ok:
            self.status_label.setText("[ПРАВА: NOPASSWD РАБОТАЕТ]")
            self.status_label.setStyleSheet("color: #2e7d32;")
            self.setup_btn.setText("🔑 Переустановить права (NOPASSWD уже работает)")
        else:
            self.status_label.setText("[ПРАВА: ПАРОЛЬ ТРЕБУЕТСЯ]")
            self.status_label.setStyleSheet("color: #616161;")
            self.setup_btn.setText("🔑 Настроить работу без пароля")
        self.setup_btn.setEnabled(True)

    def setup_permissions(self):
        if self._worker and self._worker.isRunning():
            return
        user = getpass.getuser()
        self.append_log("> запуск setup-permissions")
        self.setup_btn.setEnabled(False)

        if self.z.sudo_available():
            # NOPASSWD уже работает — достаточно обновить правила
            self._start_worker(user, elevated=True, password=None)
            return

        password, ok = QInputDialog.getText(
            self,
            "Пароль sudo",
            f"Введите пароль пользователя {user}\n"
            "(нужен один раз для настройки прав):",
            QLineEdit.Password,
        )
        if not ok or not password:
            self.setup_btn.setEnabled(True)
            self.append_log("! отменено")
            return
        self._start_worker(user, elevated=False, password=password)
        password = ""

    def _start_worker(self, user, elevated=False, password=None):
        self._worker = CommandWorker(
            self.z.setup_permissions_cmd(user),
            cwd=str(self.z.repo_root),
            elevated=elevated,
            password=password,
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(self._on_failed)
        self._worker.success.connect(self._on_done)
        self._worker.start()

    def _on_done(self, _):
        self.setup_btn.setEnabled(True)
        self.append_log("> настройка завершена")
        self.refresh_status()

    def _on_failed(self, msg):
        self.setup_btn.setEnabled(True)
        self.append_log(f"! ошибка: {msg}")
        user = getpass.getuser()
        self.append_log(
            f'! если не получилось — выполните в терминале:'
            f' sudo bash "{self.z.service}" setup-permissions {user}'
        )
        self.refresh_status()

    def append_log(self, text):
        log_line(self.log_view, text)

