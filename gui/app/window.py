# =============================================================================
# Главное окно — шапка, боковая панель, контент
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QMainWindow, QStackedWidget,
    QVBoxLayout, QWidget,
)

from .zapret import Zapret
from .ui.autotune_tab import AutotuneTab
from .ui.config_tab import ConfigTab
from .ui.credits_tab import CreditsTab
from .ui.help_tab import HelpTab
from .ui.permissions_tab import PermissionsTab
from .ui.service_tab import ServiceTab
from .ui.status_tab import StatusTab
from .ui.strategies_tab import StrategiesTab

NAV_ITEMS = [
    ("Как пользоваться", HelpTab),
    ("Статус", StatusTab),
    ("Конфигурация", ConfigTab),
    ("Стратегии", StrategiesTab),
    ("Сервис", ServiceTab),
    ("Автоподбор", AutotuneTab),
    ("Права", PermissionsTab),
    ("Авторство", CreditsTab),
]

SIDEBAR_WIDTH = 190


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.zapret = Zapret()
        self._tabs = []
        self._build_ui()
        self.setWindowTitle("InIProject — Zapret Discord YouTube")
        self.resize(960, 640)

    # ------------------------------------------------------------------

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

        self.cursor = QLabel("▮")
        self.cursor.setObjectName("cursorLabel")

        subtitle = QLabel("Zapret Discord YouTube — обход замедления")
        subtitle.setObjectName("subtitleLabel")

        layout.addWidget(brand)
        layout.addWidget(self.cursor)
        layout.addSpacing(8)
        layout.addWidget(subtitle)
        layout.addStretch()

        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._blink_cursor)
        self._cursor_timer.start(500)

        return header

    def _blink_cursor(self):
        self.cursor.setVisible(not self.cursor.isVisible())

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
            self.nav.addItem(f"  {name}")

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
        return self.stack

    def _change_tab(self, row):
        if 0 <= row < len(self._tabs):
            self.stack.setCurrentIndex(row)
            refresh = getattr(self._tabs[row], "refresh_strategies", None)
            if refresh is not None:
                refresh()

    def closeEvent(self, event):
        for tab in self._tabs:
            if hasattr(tab, "daemon") and tab.daemon and tab.daemon.isRunning():
                tab.daemon.terminate()
        event.accept()

