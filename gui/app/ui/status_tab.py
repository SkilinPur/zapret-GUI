# =============================================================================
# Вкладка «Статус» — пульт: состояние, включение/выключение, готовность
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from ..zapret import Zapret
from ..worker import CommandWorker, DaemonWorker
from .widgets import log_line, make_button, make_card, make_title

MODE_DAEMON = 0
MODE_SERVICE = 1

_COLOR_RUN = "#66bb6a"
_COLOR_STOP = "#e53935"
_COLOR_IDLE = "#616161"
_COLOR_WARN = "#ffb74d"


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
        root.setSpacing(12)

        root.addWidget(make_title(
            "Статус",
            "Что происходит и как это включить",
        ))

        # --- Большой пульт ---------------------------------------------
        power_card = make_card(margins=(20, 18, 20, 18))
        pc = power_card.layout()

        top = QHBoxLayout()
        top.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(4)
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        left.addWidget(self.status_label)
        self.hint_label = QLabel()
        self.hint_label.setObjectName("subtitleLabel")
        self.hint_label.setWordWrap(True)
        left.addWidget(self.hint_label)
        top.addLayout(left, 1)

        self.power_btn = QPushButton()
        self.power_btn.setFixedHeight(64)
        self.power_btn.setMinimumWidth(220)
        self.power_btn.setCursor(Qt.PointingHandCursor)
        top.addWidget(self.power_btn, 0, Qt.AlignVCenter)
        pc.addLayout(top)

        # Режим запуска (мелко, под основным управлением)
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_lbl = QLabel("Режим запуска:")
        mode_lbl.setProperty("section", True)
        self.mode_btns = []
        for idx, text in enumerate(["В фоне (рекомендуется)", "Как служба"]):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("modeBtn", True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, i=idx: self._on_mode_changed())
            self.mode_btns.append(btn)
            mode_row.addWidget(btn)
        self.mode_btns[MODE_DAEMON].setChecked(True)
        mode_row.addStretch()
        pc.addLayout(mode_row)

        root.addWidget(power_card)

        # --- Готовность ------------------------------------------------
        health_card = make_card()
        hc = health_card.layout()
        health_header = QLabel("Готовность к работе")
        health_header.setObjectName("logHeader")
        hc.addWidget(health_header)
        self.health_label = QLabel()
        self.health_label.setObjectName("statusConfigLabel")
        self.health_label.setTextFormat(Qt.RichText)
        self.health_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        hc.addWidget(self.health_label)
        root.addWidget(health_card)

        # --- Журнал (сворачиваемый) ------------------------------------
        self.log_toggle = make_button("▾ Показать журнал")
        self.log_toggle.setFixedWidth(180)
        self.log_toggle.clicked.connect(self._toggle_log)
        log_card = make_card()
        ll = log_card.layout()
        header_row = QHBoxLayout()
        header = QLabel(">_ журнал")
        header.setObjectName("logHeader")
        header_row.addWidget(header)
        header_row.addStretch()
        hide_btn = make_button("Скрыть")
        hide_btn.setFixedWidth(110)
        hide_btn.clicked.connect(self._toggle_log)
        header_row.addWidget(hide_btn)
        ll.addLayout(header_row)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        ll.addWidget(self.log_view, 1)
        self.log_card = log_card
        self.log_visible = False
        log_card.setVisible(False)

        root.addWidget(self.log_toggle)
        root.addWidget(log_card, 1)

        self.power_btn.clicked.connect(self._toggle_power)

    # ------------------------------------------------------------------
    # Пульт
    # ------------------------------------------------------------------

    def _toggle_power(self):
        if self.z.nfqws_running():
            self.stop_zapret()
        else:
            self.start_zapret()

    def _style_power(self, running):
        if running:
            self.power_btn.setText("⏹  Выключить")
            self.power_btn.setProperty("danger", True)
            self.power_btn.setProperty("primary", False)
        else:
            self.power_btn.setText("▶  Включить")
            self.power_btn.setProperty("danger", False)
            self.power_btn.setProperty("primary", True)
        self.power_btn.style().unpolish(self.power_btn)
        self.power_btn.style().polish(self.power_btn)

    def _busy(self, busy_state):
        self.power_btn.setEnabled(not busy_state)
        if busy_state:
            self.power_btn.setText("выполняется…")

    def _toggle_log(self):
        self.log_visible = not self.log_visible
        self.log_card.setVisible(self.log_visible)
        self.log_toggle.setText("▴ Скрыть журнал" if self.log_visible else "▾ Показать журнал")

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
        self._busy(True)
        if self._mode_index() == MODE_DAEMON:
            self._start_daemon()
        else:
            self._run_worker(self.z.service_cmd("start"), elevated=True)

    def stop_zapret(self):
        self.append_log("> запрос на остановку")
        self._busy(True)
        if self._mode_index() == MODE_DAEMON:
            self._stop_daemon()
        else:
            self._run_worker(self.z.service_cmd("stop"), elevated=True)

    # --- Фоновый демон ---

    def _start_daemon(self):
        if self.daemon and self.daemon.isRunning():
            self.append_log("! демон уже запущен")
            return
        self.append_log("> запуск в фоне (sudo service.sh daemon)")
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
        self.append_log(f"! ошибка запуска: {msg}")
        self._busy(False)
        self.refresh_status()

    def _stop_daemon(self):
        self.append_log("> остановка (sudo service.sh kill)")
        self._run_worker(self.z.kill_cmd(), elevated=True, after=self._after_kill)

    def _after_kill(self):
        if self.daemon and self.daemon.isRunning():
            self.daemon.terminate()
        self.refresh_status()

    # --- Универсальный воркер ---

    def _run_worker(self, cmd, elevated=False, after=None):
        if self._current_worker and self._current_worker.isRunning():
            self.append_log("! предыдущая команда ещё выполняется")
            return
        w = CommandWorker(cmd, cwd=str(self.z.repo_root), elevated=elevated)
        w.output.connect(self.append_log)
        w.failed.connect(self._on_worker_failed)
        w.success.connect(lambda _: self._finish_worker(after))
        w.start()
        self._current_worker = w

    def _on_worker_failed(self, msg):
        self.append_log(f"! {msg}")
        self._current_worker = None
        self._busy(False)
        self.refresh_status()

    def _finish_worker(self, after=None):
        self._current_worker = None
        self._busy(False)
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
        cfg = self.z.read_config()

        self._style_power(running)
        if running:
            self.status_label.setText("[РАБОТАЕТ]")
            self.status_label.setStyleSheet(f"color: {_COLOR_RUN};")
            self.hint_label.setText(
                "Обход активен — YouTube и Discord работают в обход замедления."
            )
        else:
            self.status_label.setText("[ОСТАНОВЛЕН]")
            self.status_label.setStyleSheet(f"color: {_COLOR_IDLE};")
            self.hint_label.setText(
                "Сейчас обход выключен. Нажмите «Включить», чтобы ускорить "
                "YouTube и Discord."
            )

        self.health_label.setText(self._health_html(cfg))

    def _health_html(self, cfg):
        items = []

        # Ядро
        if self.z.nfqws_present():
            ver = self.z.nfqws_installed_version()
            items.append((True, f"Ядро nfqws установлено{(' (' + ver + ')') if ver else ''}"))
        else:
            items.append((False, "Ядро nfqws не скачано — откройте вкладку «Обновление» → «Ядро nfqws»"))

        # Права sudo
        if self.z.sudo_available():
            items.append((True, "Работа без пароля настроена"))
        else:
            items.append((False, "Не настроена работа без пароля — вкладка «Права»"))

        # Стратегия
        strategy = cfg.get("strategy", "")
        if strategy:
            items.append((True, f"Способ обхода: {strategy}"))
        else:
            items.append((False, "Способ обхода не выбран — вкладка «Конфигурация»"))

        ok = all(ok for ok, _ in items)
        head = "✓ Всё готово к запуску — нажмите «Включить»." if ok \
            else "Не хватает пары шагов (см. ниже)."
        lines = [self._item(o, t) for o, t in items]
        return f'<span style="color:{_COLOR_RUN if ok else _COLOR_WARN};">{head}</span><br>' + "<br>".join(lines)

    @staticmethod
    def _item(ok, text):
        mark = "✓" if ok else "✗"
        color = _COLOR_RUN if ok else _COLOR_WARN
        return f'<span style="color:{color};">{mark}</span> {text}'
