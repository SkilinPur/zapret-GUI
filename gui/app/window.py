# =============================================================================
# Главное окно — шапка, боковая панель, контент
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QMainWindow, QStackedWidget,
    QSystemTrayIcon, QVBoxLayout, QWidget,
)

from .zapret import Zapret, log_to_file
from .tray import install_tray, make_icon, make_led_icon
from .worker import CommandWorker, DaemonWorker
from .ui.autotune_tab import AutotuneTab
from .ui.config_tab import ConfigTab
from .ui.credits_tab import CreditsTab
from .ui.help_tab import HelpTab
from .ui.permissions_tab import PermissionsTab
from .ui.service_tab import ServiceTab
from .ui.status_tab import StatusTab
from .ui.strategies_tab import StrategiesTab
from .ui.update_tab import UpdateTab

NAV_ITEMS = [
    ("📖 Как пользоваться", HelpTab),
    ("🟢 Статус", StatusTab),
    ("⚙️ Конфигурация", ConfigTab),
    ("📁 Стратегии", StrategiesTab),
    ("⬆️ Обновление", UpdateTab),
    ("🛠️ Сервис", ServiceTab),
    ("🎯 Автоподбор", AutotuneTab),
    ("🔑 Права", PermissionsTab),
    ("👥 Авторство", CreditsTab),
]

SIDEBAR_WIDTH = 190


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.zapret = Zapret()
        self._tabs = []
        self._really_quit = False
        self._tray_daemon = None
        self._was_running = None
        self._build_ui()
        self.setWindowTitle("InIProject — Zapret Discord YouTube")
        self.resize(960, 640)
        self.setWindowIcon(make_icon())

        self._tray = install_tray(self)

        # Индикатор статуса в шапке и трее обновляем раз в 3 секунды
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status_indicator)
        self._status_timer.start(3000)
        self._update_status_indicator()

        QTimer.singleShot(1200, self._auto_check_updates)

    # ------------------------------------------------------------------

    def _auto_check_updates(self):
        # Тихая проверка при старте — без всплывающего диалога.
        for tab in self._tabs:
            if isinstance(tab, UpdateTab):
                tab.check_now(show_dialog=False)
                break

    # ------------------------------------------------------------------

    def _update_status_indicator(self):
        running = self.zapret.nfqws_running()
        color = "#66bb6a" if running else "#616161"
        self.header_status.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: bold;"
        )
        self.header_status.setToolTip(
            "zapret работает" if running else "zapret остановлен"
        )

        # Уведомление о падении nfqws
        if self._was_running is True and not running:
            log_to_file("nfqws перестал работать")
            if self._tray is not None:
                self._tray.showMessage(
                    "Zapret Discord YouTube",
                    "nfqws остановлен или упал.",
                    QSystemTrayIcon.Warning,
                    4000,
                )
        self._was_running = running

        if self._tray is not None:
            self._tray.setIcon(make_led_icon(running))
            self._tray.setToolTip(
                f"Zapret Discord YouTube — {'работает' if running else 'остановлен'}"
            )
            self._tray.start_action.setEnabled(not running)
            self._tray.stop_action.setEnabled(running)

    # ------------------------------------------------------------------

    def tray_start_zapret(self):
        """Быстрый запуск из трея (фоновый демон)."""
        if self._tray_daemon and self._tray_daemon.isRunning():
            return
        log_to_file("tray: запуск zapret")
        self._tray_daemon = DaemonWorker(
            self.zapret.daemon_cmd(), cwd=str(self.zapret.repo_root), elevated=True,
        )
        self._tray_daemon.failed.connect(self._on_tray_daemon_failed)
        self._tray_daemon.start()
        if self._tray is not None:
            self._tray.showMessage(
                "Zapret Discord YouTube",
                "Запуск zapret…",
                QSystemTrayIcon.Information,
                1500,
            )
        self._update_status_indicator()

    def tray_stop_zapret(self):
        """Быстрая остановка из трея."""
        log_to_file("tray: остановка zapret")
        w = CommandWorker(
            self.zapret.kill_cmd(), cwd=str(self.zapret.repo_root), elevated=True,
        )
        w.failed.connect(lambda msg: log_to_file(f"tray: ошибка остановки: {msg}"))
        w.start()
        if self._tray_daemon and self._tray_daemon.isRunning():
            self._tray_daemon.terminate()
            self._tray_daemon = None
        if self._tray is not None:
            self._tray.showMessage(
                "Zapret Discord YouTube",
                "zapret остановлен",
                QSystemTrayIcon.Information,
                1500,
            )
        self._update_status_indicator()

    def _on_tray_daemon_failed(self, msg):
        log_to_file(f"tray: ошибка запуска: {msg}")
        if self._tray is not None:
            self._tray.showMessage(
                "Zapret Discord YouTube",
                f"Не удалось запустить zapret: {msg}",
                QSystemTrayIcon.Critical,
                4000,
            )

    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("rootWidget")
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        body_layout.addWidget(self._build_sidebar())
        body_layout.addWidget(self._build_content(), 1)

        outer.addWidget(body, 1)

    def _build_header(self):
        header = QWidget()
        header.setObjectName("headerBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(12)

        brand = QLabel("InIProject")
        brand.setObjectName("brandLabel")

        subtitle = QLabel("Zapret Discord YouTube — обход замедления")
        subtitle.setObjectName("subtitleLabel")

        self.header_status = QLabel("●")
        self.header_status.setObjectName("headerStatus")

        layout.addWidget(brand)
        layout.addSpacing(8)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.header_status)

        return header

    def _build_sidebar(self):
        side = QWidget()
        side.setObjectName("sidebarWidget")
        side.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(side)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)

        self.nav = QListWidget()
        self.nav.setObjectName("sidebarList")
        for name, _ in NAV_ITEMS:
            self.nav.addItem(f"{name}")

        layout.addWidget(self.nav, 1)

        footer = QLabel("InIProject")
        footer.setObjectName("sidebarFooter")
        footer.setAlignment(Qt.AlignCenter)

        footer_hint = QLabel("zapret-discord-youtube-linux")
        footer_hint.setObjectName("sidebarFooterHint")
        footer_hint.setAlignment(Qt.AlignCenter)

        layout.addWidget(footer)
        layout.addWidget(footer_hint)

        self.nav.currentRowChanged.connect(self._change_tab)
        self.nav.setCurrentRow(0)

        return side

    def _build_content(self):
        self.stack = QStackedWidget()
        for name, tab_cls in NAV_ITEMS:
            tab = tab_cls(self.zapret)
            self._tabs.append(tab)
            self.stack.addWidget(tab)
            if isinstance(tab, UpdateTab):
                tab.go_to_tab.connect(lambda: self._change_tab(self._tabs.index(tab)))
        return self.stack

    def _change_tab(self, row):
        if 0 <= row < len(self._tabs):
            self.stack.setCurrentIndex(row)
            refresh = getattr(self._tabs[row], "refresh_strategies", None)
            if refresh is not None:
                refresh()

    def show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_from_tray(self):
        self._really_quit = True
        self.close()

    def closeEvent(self, event):
        # Если есть трей — закрытие прячет окно, zapret продолжает работать.
        # По-настоящему выйти можно из трея: «Завершить программу».
        if self._tray is not None and not self._really_quit:
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "Zapret Discord YouTube",
                "Программа свернута в трей. ЛКМ по иконке — меню.",
                QSystemTrayIcon.Information,
                3000,
            )
            return
        if self._tray_daemon and self._tray_daemon.isRunning():
            self._tray_daemon.terminate()
        for tab in self._tabs:
            if hasattr(tab, "daemon") and tab.daemon and tab.daemon.isRunning():
                tab.daemon.terminate()
        event.accept()

