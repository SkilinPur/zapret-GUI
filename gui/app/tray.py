# =============================================================================
# Системный трей: сворачивание окна в трей
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def make_icon():
    """Иконка приложения: фиолетовая плашка с белой буквой Z."""
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#7C5CFC"))
    p.drawRoundedRect(4, 4, 56, 56, 16, 16)

    font = QFont()
    font.setBold(True)
    font.setPixelSize(34)
    p.setFont(font)
    p.setPen(QColor("#ffffff"))
    p.drawText(pm.rect(), Qt.AlignCenter, "Z")
    p.end()
    return QIcon(pm)


def install_tray(window):
    """Создаёт иконку в системном трее. Возвращает объект или None."""
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    app = QApplication.instance()
    tray = QSystemTrayIcon(make_icon(), app)
    tray.setToolTip("Zapret Discord YouTube")

    show_action = QAction("Показать окно", tray)
    quit_action = QAction("Завершить программу", tray)
    show_action.triggered.connect(window.show_from_tray)
    quit_action.triggered.connect(window.quit_from_tray)

    menu = QMenu()
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
