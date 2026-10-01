# =============================================================================
# Системный трей: сворачивание окна в трей
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _draw_bolt(p, x, y, w, h, color):
    """Плоская молния (логотип)."""
    f = [(0.62, 0.02), (0.22, 0.55), (0.46, 0.55), (0.38, 0.98),
         (0.82, 0.40), (0.54, 0.40)]
    poly = QPolygonF([QPointF(x + fx * w, y + fy * h) for fx, fy in f])
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawPolygon(poly)


def make_icon():
    """Иконка приложения: плоская красная молния на прозрачном фоне."""
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_bolt(p, 10, 5, 44, 54, "#E53935")
    p.end()
    return QIcon(pm)


def make_led_icon(running=True):
    """Иконка трея: молния + точка статуса (зелёная = работает, серая = нет)."""
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    _draw_bolt(p, 8, 2, 44, 54, "#E53935")
    led = QColor("#66bb6a") if running else QColor("#616161")
    p.setBrush(led)
    p.drawEllipse(44, 44, 16, 16)
    p.end()
    return QIcon(pm)


def install_tray(window):
    """Создаёт иконку в системном трее с управлением zapret. Возвращает объект или None."""
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    app = QApplication.instance()
    tray = QSystemTrayIcon(make_led_icon(False), app)
    tray.setToolTip("Zapret Discord YouTube")

    # Быстрое управление zapret прямо из трея
    tray.start_action = QAction("▶ Запустить zapret", tray)
    tray.stop_action = QAction("⏹ Остановить zapret", tray)
    tray.start_action.triggered.connect(window.tray_start_zapret)
    tray.stop_action.triggered.connect(window.tray_stop_zapret)
    tray.stop_action.setEnabled(False)

    show_action = QAction("Показать окно", tray)
    quit_action = QAction("Завершить программу", tray)
    show_action.triggered.connect(window.show_from_tray)
    quit_action.triggered.connect(window.quit_from_tray)

    menu = QMenu()
    menu.addAction(tray.start_action)
    menu.addAction(tray.stop_action)
    menu.addSeparator()
    menu.addAction(show_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    def on_activated(reason):
        # ЛКМ по иконке — меню с действиями (по правой кнопке меню и так видно)
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            menu.exec(QCursor.pos())

    tray.activated.connect(on_activated)
    tray.show()
    return tray
