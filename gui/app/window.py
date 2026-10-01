# =============================================================================
# Главное окно — шапка, боковая панель, контент
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

import os

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QListWidget, QMainWindow, QPushButton,
    QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from .zapret import Zapret, log_to_file
from .tray import install_tray, make_icon, make_led_icon
from .theme import build_qss
from .worker import CommandWorker, DaemonWorker
from .ui.autotune_tab import AutotuneTab
from .ui.config_tab import ConfigTab
from .ui.credits_tab import CreditsTab
from .ui.help_tab import HelpTab
from .ui.status_tab import StatusTab
from .ui.system_tab import SystemTab
from .ui.telegram_tab import TelegramTab
from .ui.update_tab import UpdateTab
from .ui.user_lists_tab import UserListsTab

NAV_ITEMS = [
    ("🟢 Статус", StatusTab),
    ("⚙️ Настройки", ConfigTab),
    ("⬆️ Обновление", UpdateTab),
    ("✈️ Telegram", TelegramTab),
    ("🛠️ Система", SystemTab),
    ("🎯 Подбор способа", AutotuneTab),
    ("📝 Списки", UserListsTab),
    ("📖 Справка", HelpTab),
]

# Вкладки, которые скрываются в «Простом» режиме
ADVANCED_TABS = {SystemTab, AutotuneTab, UserListsTab}

# Словарик-подсказки для вкладок
NAV_HINTS = {
    StatusTab: "Запуск/остановка обхода и его состояние.",
    ConfigTab: "Способ обхода и дополнительные параметры.",
    UpdateTab: "Версии и обновление программы, ядра и стратегий.",
    TelegramTab: "Локальный прокси Tg WS Proxy для Telegram Desktop.",
    SystemTab: "Автозапуск при включении ПК и работа без пароля.",
    AutotuneTab: "Автоматический подбор рабочего способа.",
    UserListsTab: "Свои домены/IP для обхода и исключений.",
    HelpTab: "Краткое руководство.",
}

SIDEBAR_WIDTH = 190


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.zapret = Zapret()
        self._tabs = []
        self._really_quit = False
        self._tray_daemon = None
        self._tray_worker = None
        self._was_running = None
        self._build_ui()
        self.setWindowTitle("InIProject — Zapret Discord YouTube")
        self.resize(960, 640)
        self.setWindowIcon(make_icon())

        # Режим интерфейса (простой/продвинутый) — из настроек
        simple = QSettings().value("ui/simple_mode", False, type=bool)
        self.mode_btn.blockSignals(True)
        self.mode_btn.setChecked(simple)
        self.mode_btn.blockSignals(False)
        self._apply_mode()
        theme = QSettings().value("ui/theme", "dark")
        self.theme_btn.setText("Тема: светлая" if theme == "light" else "Тема: тёмная")

        # Тост-уведомления
        self.toast = QLabel(self)
        self.toast.setObjectName("toast")
        self.toast.setWordWrap(True)
        self.toast.hide()

        self._tray = install_tray(self)

        # Мастер первого запуска
        QTimer.singleShot(500, self._maybe_show_wizard)

        # Индикатор статуса в шапке и трее обновляем раз в 3 секунды
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status_indicator)
        self._status_timer.start(3000)
        self._update_status_indicator()

        self._auto_check_timer = QTimer.singleShot(1200, self._auto_check_updates)

    # ------------------------------------------------------------------

    def _maybe_show_wizard(self):
        if self._really_quit:
            return
        if QSettings().value("wizard/done", False, type=bool):
            return
        from .ui.wizard import FirstRunWizard
        wiz = FirstRunWizard(
            self.zapret, request_start=self.tray_start_zapret, parent=self,
        )
        wiz.exec()

    # ------------------------------------------------------------------

    def _auto_check_updates(self):
        if self._really_quit:
            return
        # Для smoke/скриншотов (CI) автопроверку отключаем — иначе CheckWorker
        # живёт дольше скрипта и роняет процесс на выходе.
        if os.environ.get("ZAPRET_GUI_NOAUTOUPDATE"):
            return
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
            self.show_toast("Обход остановлен", "info")
            if self._tray is not None:
                self._tray.showMessage(
                    "Zapret Discord YouTube",
                    "nfqws остановлен или упал.",
                    QSystemTrayIcon.Warning,
                    4000,
                )
        elif self._was_running is False and running:
            self.show_toast("Обход включён", "success")
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
        # Ссылку держим, пока поток не завершится — иначе QThread упадёт.
        self._tray_daemon.finished.connect(self._on_tray_daemon_done)
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
        if self._tray_worker and self._tray_worker.isRunning():
            return
        log_to_file("tray: остановка zapret")
        w = CommandWorker(
            self.zapret.kill_cmd(), cwd=str(self.zapret.repo_root), elevated=True,
        )
        # Держим воркер живым до завершения потока (иначе GC уронит приложение)
        self._tray_worker = w
        w.finished.connect(self._on_tray_worker_done)
        w.failed.connect(lambda msg: log_to_file(f"tray: ошибка остановки: {msg}"))
        w.start()
        if self._tray_daemon and self._tray_daemon.isRunning():
            self._tray_daemon.terminate()
        if self._tray is not None:
            self._tray.showMessage(
                "Zapret Discord YouTube",
                "zapret остановлен",
                QSystemTrayIcon.Information,
                1500,
            )
        self._update_status_indicator()

    def _on_tray_worker_done(self):
        self._tray_worker = None

    def _on_tray_daemon_done(self):
        self._tray_daemon = None

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

        self.help_btn = QPushButton("?")
        self.help_btn.setObjectName("helpBtn")
        self.help_btn.setFixedSize(30, 30)
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setToolTip("Справка")
        self.help_btn.clicked.connect(self._open_help)

        self.theme_btn = QPushButton("Тема")
        self.theme_btn.setObjectName("modeToggleBtn")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("Переключить тёмную/светлую тему")
        self.theme_btn.clicked.connect(self._toggle_theme)

        self.mode_btn = QPushButton()
        self.mode_btn.setObjectName("modeToggleBtn")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setCursor(Qt.PointingHandCursor)
        self.mode_btn.setToolTip("Простой режим скрывает технические вкладки")
        self.mode_btn.toggled.connect(self._apply_mode)

        layout.addWidget(brand)
        layout.addSpacing(8)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.theme_btn)
        layout.addWidget(self.mode_btn)
        layout.addWidget(self.help_btn)
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
        layout.addWidget(self.nav, 1)

        footer = QLabel("InIProject")
        footer.setObjectName("sidebarFooter")
        footer.setAlignment(Qt.AlignCenter)

        footer_hint = QLabel("zapret-discord-youtube-linux")
        footer_hint.setObjectName("sidebarFooterHint")
        footer_hint.setAlignment(Qt.AlignCenter)

        self.credits_btn = QPushButton("👥 Авторство")
        self.credits_btn.setObjectName("creditsBtn")
        self.credits_btn.setCursor(Qt.PointingHandCursor)
        self.credits_btn.setToolTip("Fork by InIProject — SkilinPur")
        self.credits_btn.clicked.connect(self._show_credits)

        layout.addWidget(footer)
        layout.addWidget(footer_hint)
        layout.addWidget(self.credits_btn)

        self.nav.currentRowChanged.connect(self._change_tab)

        return side

    def _build_content(self):
        self.stack = QStackedWidget()
        for name, tab_cls in NAV_ITEMS:
            tab = tab_cls(self.zapret)
            # Мастеру (в справке) нужен способ запуска демона от окна
            if hasattr(tab, "request_start"):
                tab.request_start = self.tray_start_zapret
            self._tabs.append(tab)
            self.stack.addWidget(tab)
            if isinstance(tab, UpdateTab):
                tab.go_to_tab.connect(lambda: self._change_tab(self._tabs.index(tab)))
        # «Авторство» — отдельная вкладка вне меню, открывается из подвала
        self.credits_tab = CreditsTab(self.zapret)
        self._tabs.append(self.credits_tab)
        self.stack.addWidget(self.credits_tab)
        return self.stack

    def _open_help(self):
        help_idx = [c for _, c in NAV_ITEMS].index(HelpTab)
        try:
            row = self._nav_stack.index(help_idx)
            self.nav.setCurrentRow(row)
        except ValueError:
            pass

    def _show_credits(self):
        self.stack.setCurrentIndex(len(self._tabs) - 1)

    def _toggle_theme(self):
        cur = QSettings().value("ui/theme", "dark")
        new = "light" if cur != "light" else "dark"
        QSettings().setValue("ui/theme", new)
        QApplication.instance().setStyleSheet(build_qss(new))
        self.theme_btn.setText("Тема: светлая" if new == "light" else "Тема: тёмная")

    def show_toast(self, text, kind="info"):
        self.toast.setProperty("kind", kind)
        self.toast.setText(text)
        self.toast.setFixedWidth(240)
        self.toast.adjustSize()
        cw = self.centralWidget()
        if cw is not None:
            x = cw.width() - self.toast.width() - 24
            y = cw.height() - self.toast.height() - 24
            self.toast.move(max(0, x), max(0, y))
        self.toast.raise_()
        self.toast.show()
        self.toast.style().unpolish(self.toast)
        self.toast.style().polish(self.toast)
        QTimer.singleShot(3000, self.toast.hide)

    def _apply_mode(self, *_):
        simple = self.mode_btn.isChecked()
        QSettings().setValue("ui/simple_mode", simple)
        self.mode_btn.setText("🧭 Простой" if simple else "🧭 Продвинутый")
        visible = [(n, c) for n, c in NAV_ITEMS
                   if (not simple) or c not in ADVANCED_TABS]
        classes = [c for _, c in NAV_ITEMS]
        self._nav_stack = [classes.index(c) for _, c in visible]
        self.nav.blockSignals(True)
        self.nav.clear()
        for name, cls in visible:
            self.nav.addItem(name)
            item = self.nav.item(self.nav.count() - 1)
            if item is not None and cls in NAV_HINTS:
                item.setToolTip(NAV_HINTS[cls])
        self.nav.blockSignals(False)
        self.nav.setCurrentRow(0)

    def _change_tab(self, row):
        nav = getattr(self, "_nav_stack", None)
        idx = nav[row] if nav and 0 <= row < len(nav) else row
        if 0 <= idx < len(self._tabs):
            self.stack.setCurrentIndex(idx)
            tab = self._tabs[idx]
            refresh = getattr(tab, "refresh_strategies", None)
            if refresh is not None:
                refresh()
            # При открытии «Обновления» сразу проверяем версии
            if isinstance(tab, UpdateTab):
                tab.check_now(show_dialog=False)

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
        self._stop_thread(self._tray_daemon)
        self._stop_thread(self._tray_worker)
        for tab in self._tabs:
            self._stop_thread(getattr(tab, "daemon", None))
            for attr in ("_worker", "_current_worker", "_checker"):
                self._stop_thread(getattr(tab, attr, None))

        # Останавливаем таймеры, чтобы они не сработали после закрытия окна
        self._status_timer.stop()
        if self._auto_check_timer is not None:
            self._auto_check_timer.stop()
            self._auto_check_timer = None
        event.accept()

    @staticmethod
    def _stop_thread(thread, timeout=2000):
        """Безопасно завершает фоновый поток перед выходом.

        Иначе QThread уничтожается, пока его поток ещё работает, и PySide6
        роняет приложение («QThread: Destroyed while thread is still running»).
        """
        if thread is None or not thread.isRunning():
            return
        stop = getattr(thread, "stop", None)
        if callable(stop):
            stop()          # CommandWorker: завершает подпроцесс
        else:
            thread.terminate()  # DaemonWorker/CheckWorker: принудительно
        thread.wait(timeout)

