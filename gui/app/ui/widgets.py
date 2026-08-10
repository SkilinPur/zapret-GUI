# =============================================================================
# Общие виджеты и помощники для вкладок
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)


def make_card(widget=None, margins=(16, 16, 16, 16)):
    """Карточка с тёмным фоном, рамкой и скруглением."""
    frame = QFrame()
    frame.setProperty("card", True)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(*margins)
    layout.setSpacing(10)
    if widget is not None:
        layout.addWidget(widget)
    return frame


def make_button(text, primary=False, danger=False, accent=False):
    """Кнопка с нужным стилем."""
    btn = QPushButton(text)
    if primary:
        btn.setProperty("primary", True)
    elif danger:
        btn.setProperty("danger", True)
    elif accent:
        btn.setProperty("accent", True)
    return btn


def make_title(text, subtitle=None):
    """Заголовок вкладки с опциональным подзаголовком."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)

    title = QLabel(text)
    title.setProperty("title", True)
    layout.addWidget(title)

    if subtitle:
        sub = QLabel(subtitle)
        sub.setProperty("subtitle", True)
        sub.setWordWrap(True)
        layout.addWidget(sub)
    return widget


def add_row(label_text, widget):
    """Строка формы: подпись слева, контрол справа."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    label = QLabel(label_text)
    label.setProperty("section", True)
    label.setFixedWidth(180)
    layout.addWidget(label)
    layout.addWidget(widget, 1)
    return row

