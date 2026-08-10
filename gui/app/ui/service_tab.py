# =============================================================================
# Вкладка «Сервис» — управление системным сервисом
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..zapret import Zapret
from ..worker import CommandWorker
from .widgets import add_row, log_line, make_button, make_card, make_title

SERVICE_NAME = "zapret_discord_youtube"

STATUS_MAP = {
    1: "не установлен",
    2: "установлен и активен",
    3: "установлен, но не активен",
}


class ServiceTab(QWidget):
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
            "Сервис",
            "Системная служба автозагрузки zapret",
        ))

        card = make_card()
        cl = card.layout()

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        cl.addWidget(self.status_label)

        self.meta_label = QLabel()
        self.meta_label.setObjectName("statusMetaLabel")
        cl.addWidget(self.meta_label)

        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(10)

        self.install_btn = make_button("Установить", primary=True)
        self.remove_btn = make_button("Удалить", danger=True)
        self.start_btn = make_button("Запустить")
        self.stop_btn = make_button("Остановить")
        self.restart_btn = make_button("Перезапустить")
        self.refresh_btn = make_button("⟳ Обновить статус")
        self.logs_btn = make_button("Показать логи")

        for btn in (self.install_btn, self.remove_btn, self.start_btn,
                    self.stop_btn, self.restart_btn):
            btn.setFixedWidth(130)
        rl.addWidget(self.install_btn)
        rl.addWidget(self.remove_btn)
        rl.addWidget(self.start_btn)
        rl.addWidget(self.stop_btn)
        rl.addWidget(self.restart_btn)
        rl.addStretch()
        cl.addWidget(row)

        row2 = QWidget()
        rl2 = QHBoxLayout(row2)
        rl2.setContentsMargins(0, 0, 0, 0)
        rl2.addWidget(self.refresh_btn)
        rl2.addWidget(self.logs_btn)
        rl2.addStretch()
        cl.addWidget(row2)

        root.addWidget(card)

        log_card = make_card()
        ll = log_card.layout()
        header = QLabel(f">_ логи сервиса ({SERVICE_NAME})")
        header.setObjectName("logHeader")
        ll.addWidget(header)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        ll.addWidget(self.log_view, 1)
        root.addWidget(log_card, 1)

        self.install_btn.clicked.connect(lambda: self._run("install"))
        self.remove_btn.clicked.connect(lambda: self._run("remove"))
        self.start_btn.clicked.connect(lambda: self._run("start"))
        self.stop_btn.clicked.connect(lambda: self._run("stop"))
        self.restart_btn.clicked.connect(lambda: self._run("restart"))
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.logs_btn.clicked.connect(self.show_logs)

    # ------------------------------------------------------------------

    def refresh_status(self):
        code = self.z.service_status_code()
        text = STATUS_MAP.get(code, f"неизвестно ({code})")
        if code == 2:
            self.status_label.setText(f"[СЕРВИС: {text.upper()}]")
            self.status_label.setStyleSheet("color: #e53935;")
        else:
            self.status_label.setText(f"[СЕРВИС: {text.upper()}]")
            self.status_label.setStyleSheet("color: #616161;")

        init = self.z.init_system()
        self.meta_label.setText(
            f"init: {init} | имя службы: {SERVICE_NAME} | "
            f"статус nfqws: {'работает' if self.z.nfqws_running() else 'остановлен'}"
        )

        installed = code in (2, 3)
        self.install_btn.setEnabled(not installed)
        self.remove_btn.setEnabled(installed)
        self.start_btn.setEnabled(code == 3)
        self.stop_btn.setEnabled(code == 2)
        self.restart_btn.setEnabled(installed)

    def _run(self, action):
        if self._worker and self._worker.isRunning():
            self.append_log("! команда уже выполняется")
            return
        self.append_log(f"> service {action}")
        self._worker = CommandWorker(
            self.z.service_cmd(action), cwd=str(self.z.repo_root), elevated=True,
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(lambda msg: self.append_log(f"! {msg}"))
        self._worker.success.connect(lambda _: self._after_action(action))
        self._worker.start()

    def _after_action(self, action):
        self.append_log(f"> service {action} — готово")
        self.refresh_status()

    def show_logs(self):
        if self._worker and self._worker.isRunning():
            self.append_log("! команда уже выполняется")
            return
        if self.z.init_system() == "systemd":
            cmd = ["journalctl", "-u", SERVICE_NAME, "-n", "200", "--no-pager"]
        else:
            cmd = ["journalctl", "-u", SERVICE_NAME, "-n", "200", "--no-pager"]
        self.append_log("> чтение логов...")
        self._worker = CommandWorker(cmd, elevated=True)
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(lambda msg: self.append_log(f"! {msg}"))
        self._worker.success.connect(lambda _: self.append_log("> лог загружен"))
        self._worker.start()

    def append_log(self, text):
        log_line(self.log_view, text)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

