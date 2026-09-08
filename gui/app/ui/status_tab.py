# =============================================================================
# Вкладка «Статус» — индикатор, запуск/остановка, живой лог
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from ..zapret import Zapret
from ..worker import CommandWorker, DaemonWorker
from .widgets import log_line, make_button, make_card, make_title

MODE_DAEMON = 0
MODE_SERVICE = 1

_RUNNING_COLOR = "#66bb6a"
_STOPPED_COLOR = "#616161"


class StatusTab(QWidget):
    def __init__(self, zapret: Zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self.daemon = None
        self._current_worker = None
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_status)
        self._timer.start(3000)
        self.refresh_status()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(make_title(
            "Статус",
            "Текущее состояние zapret и управление запуском",
        ))

        # --- Карточка статуса ---
        status_card = make_card()
        sc = status_card.layout()

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignLeft)
        sc.addWidget(self.status_label)

        self.config_label = QLabel()
        self.config_label.setObjectName("statusConfigLabel")
        self.config_label.setTextFormat(Qt.RichText)
        self.config_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sc.addWidget(self.config_label)

        mode_row = QWidget()
        ml = QHBoxLayout(mode_row)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(8)
        mode_lbl = QLabel("Режим запуска:")
        mode_lbl.setProperty("section", True)
        self.mode_btns = []
        for idx, text in enumerate(["Фоновый демон", "systemd-сервис"]):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("modeBtn", True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, i=idx: self._on_mode_changed())
            self.mode_btns.append(btn)
            ml.addWidget(btn)
        self.mode_btns[MODE_DAEMON].setChecked(True)
        ml.addStretch()
        sc.addWidget(mode_row)

        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)
        self.start_btn = make_button("▶ Старт", primary=True)
        self.stop_btn = make_button("⏹ Стоп", danger=True)
        self.start_btn.setMinimumWidth(130)
        self.stop_btn.setMinimumWidth(130)
        bl.addWidget(self.start_btn)
        bl.addWidget(self.stop_btn)
        bl.addStretch()
        sc.addWidget(btn_row)

        root.addWidget(status_card)

        # --- Лог ---
        log_card = make_card()
        ll = log_card.layout()
        header = QLabel(">_ live log")
        header.setObjectName("logHeader")
        ll.addWidget(header)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        ll.addWidget(self.log_view, 1)

        root.addWidget(log_card, 1)

        # --- Сигналы ---
        self.start_btn.clicked.connect(self.start_zapret)
        self.stop_btn.clicked.connect(self.stop_zapret)

    # ------------------------------------------------------------------
    # Действия
    # ------------------------------------------------------------------

    def _on_mode_changed(self):
        self.refresh_status()

    def _mode_index(self):
        for idx, btn in enumerate(self.mode_btns):
            if btn.isChecked():
                return idx
        return MODE_DAEMON

    def start_zapret(self):
        self.append_log("> запрос на запуск")
        if self._mode_index() == MODE_DAEMON:
            self._start_daemon()
        else:
            self._run_worker(self.z.service_cmd("start"), elevated=True,
                             busy=self.start_btn)

    def stop_zapret(self):
        self.append_log("> запрос на остановку")
        if self._mode_index() == MODE_DAEMON:
            self._stop_daemon()
        else:
            self._run_worker(self.z.service_cmd("stop"), elevated=True,
                             busy=self.stop_btn)

    # --- Фоновый демон ---

    def _start_daemon(self):
        if self.daemon and self.daemon.isRunning():
            self.append_log("! демон уже запущен")
            return
        self.append_log("> запуск демона (sudo service.sh daemon)")
        self.daemon = DaemonWorker(
            self.z.daemon_cmd(), cwd=str(self.z.repo_root), elevated=True,
        )
        self.daemon.output.connect(self.append_log)
        self.daemon.stopped.connect(self._on_daemon_stopped)
        self.daemon.failed.connect(self._on_daemon_failed)
        self.daemon.start()

    def _on_daemon_stopped(self):
        self.append_log("> демон остановлен")
        self.daemon = None
        self.refresh_status()

    def _on_daemon_failed(self, msg):
        self.append_log(f"! ошибка запуска демона: {msg}")

    def _stop_daemon(self):
        self.append_log("> остановка (sudo service.sh kill)")
        self._run_worker(self.z.kill_cmd(), elevated=True, after=self._after_kill)

    def _after_kill(self):
        if self.daemon and self.daemon.isRunning():
            self.daemon.terminate()
        self.refresh_status()

    # --- Универсальный воркер ---

    def _run_worker(self, cmd, elevated=False, after=None, busy=None):
        if self._current_worker and self._current_worker.isRunning():
            self.append_log("! предыдущая команда ещё выполняется")
            return
        if busy is not None:
            busy.setEnabled(False)
            busy.setText("выполняется…")
        w = CommandWorker(cmd, cwd=str(self.z.repo_root), elevated=elevated)
        w.output.connect(self.append_log)
        w.failed.connect(self._on_worker_failed)
        w.success.connect(lambda _: self._finish_worker(after, busy))
        w.start()
        self._current_worker = w

    def _on_worker_failed(self, msg):
        self.append_log(f"! {msg}")
        self._current_worker = None
        self.refresh_status()

    def _finish_worker(self, after=None, busy=None):
        self._current_worker = None
        if busy is not None:
            busy.setText("▶ Старт" if busy is self.start_btn else "⏹ Стоп")
        if after:
            after()
        else:
            self.refresh_status()

    # ------------------------------------------------------------------
    # Отображение
    # ------------------------------------------------------------------

    def append_log(self, text):
        log_line(self.log_view, text)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def refresh_status(self):
        running = self.z.nfqws_running()
        count = self.z.nfqws_count()
        cfg = self.z.read_config()

        if running:
            self.status_label.setText("[СТАТУС: РАБОТАЕТ]")
            self.status_label.setStyleSheet(f"color: {_RUNNING_COLOR};")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.status_label.setText("[СТАТУС: ОСТАНОВЛЕН]")
            self.status_label.setStyleSheet(f"color: {_STOPPED_COLOR};")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

        strategy = cfg.get("strategy", "—")
        interface = cfg.get("interface", "—")
        gt = "tcp" if cfg.get("gamefiltertcp") == "true" else ""
        gu = "udp" if cfg.get("gamefilterudp") == "true" else ""
        gf = "+".join(x for x in (gt, gu) if x) or "выкл"
        backend = cfg.get("firewall_backend", "auto")

        html = (
            f'<span style="color:#9e9e9e;">&gt;_ стратегия:</span> '
            f'<span style="color:#e53935;">{strategy}</span><br>'
            f'<span style="color:#9e9e9e;">&gt;_ интерфейс:</span> {interface} &nbsp;|&nbsp; '
            f'<span style="color:#9e9e9e;">gamefilter:</span> {gf} &nbsp;|&nbsp; '
            f'<span style="color:#9e9e9e;">бэкенд:</span> {backend}<br>'
            f'<span style="color:#9e9e9e;">&gt;_ nfqws:</span> {count} процес(с/са) '
            f'&nbsp;|&nbsp; <span style="color:#9e9e9e;">init:</span> {self.z.init_system()}'
        )
        self.config_label.setText(html)

        if running:
            self.status_label.setToolTip("zapret работает")
        else:
            self.status_label.setToolTip("zapret остановлен")

