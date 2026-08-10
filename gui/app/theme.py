# =============================================================================
# Тема GUI — гибрид Discord + хакинг, красно-чёрная гамма
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

COLORS = {
    "bg": "#0a0a0c",
    "panel": "#141417",
    "panel_alt": "#1a1a1e",
    "sidebar": "#101013",
    "border": "#26262b",
    "border_soft": "#33333a",
    "accent": "#e53935",
    "accent_hover": "#ff4d4d",
    "accent_pressed": "#c62828",
    "accent_glow": "rgba(229, 57, 53, 0.25)",
    "accent_dim": "rgba(229, 57, 53, 0.15)",
    "text": "#d1d1d1",
    "text_secondary": "#9e9e9e",
    "text_dim": "#616161",
    "running": "#e53935",
    "stopped": "#616161",
    "danger": "#e53935",
}

QSS = """
* {
    font-family: 'Cantarell', 'Ubuntu', 'DejaVu Sans', 'Noto Sans', sans-serif;
    color: #d1d1d1;
    outline: none;
}

QMainWindow, #rootWidget {
    background-color: #0a0a0c;
}

/* ---------- Шапка ---------- */
#headerBar {
    background-color: #0a0a0c;
    border-bottom: 1px solid #26262b;
}

#brandLabel {
    color: #e53935;
    font-size: 17px;
    font-weight: bold;
    letter-spacing: 1px;
}

#subtitleLabel {
    color: #9e9e9e;
    font-size: 13px;
}

#cursorLabel {
    color: #e53935;
    font-size: 16px;
    font-weight: bold;
}

/* ---------- Боковая панель ---------- */
#sidebarWidget {
    background-color: #101013;
    border-right: 1px solid #26262b;
}

#sidebarList {
    background-color: transparent;
    border: none;
    outline: none;
}

#sidebarList::item {
    color: #9e9e9e;
    height: 42px;
    padding-left: 10px;
    border-radius: 6px;
    margin: 2px 8px;
    font-size: 14px;
}

#sidebarList::item:hover {
    color: #d1d1d1;
    background-color: #1a1a1e;
}

#sidebarList::item:selected {
    color: #e53935;
    background-color: rgba(229, 57, 53, 0.15);
    border-left: 3px solid #e53935;
}

#sidebarFooter {
    color: #e53935;
    font-size: 13px;
    font-weight: bold;
}

#sidebarFooterHint {
    color: #616161;
    font-size: 10px;
}

/* ---------- Карточки ---------- */
QFrame[card="true"] {
    background-color: #141417;
    border: 1px solid #26262b;
    border-radius: 10px;
}

QFrame[card="true"]:hover {
    border-color: #33333a;
}

QLabel[title="true"] {
    color: #e53935;
    font-size: 18px;
    font-weight: bold;
}

QLabel[subtitle="true"] {
    color: #9e9e9e;
    font-size: 13px;
}

QLabel[section="true"] {
    color: #d1d1d1;
    font-size: 14px;
    font-weight: bold;
}

/* ---------- Статус ---------- */
#statusLabel {
    font-family: 'DejaVu Sans Mono', 'Ubuntu Mono', monospace;
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 1px;
}

#statusConfigLabel, #statusMetaLabel {
    font-family: 'DejaVu Sans Mono', 'Ubuntu Mono', monospace;
    font-size: 13px;
    color: #9e9e9e;
}

/* ---------- Кнопки ---------- */
QPushButton {
    background-color: #1a1a1e;
    color: #d1d1d1;
    border: 1px solid #33333a;
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton:hover {
    border-color: #e53935;
    background-color: #222226;
}

QPushButton:pressed {
    background-color: #2a2a2e;
}

QPushButton:disabled {
    color: #616161;
    border-color: #26262b;
    background-color: #101013;
}

QPushButton[primary="true"] {
    background-color: #e53935;
    color: #ffffff;
    border: none;
    font-weight: bold;
}

QPushButton[primary="true"]:hover {
    background-color: #ff4d4d;
}

QPushButton[primary="true"]:pressed {
    background-color: #c62828;
}

QPushButton[danger="true"] {
    background-color: transparent;
    color: #e53935;
    border: 1px solid #e53935;
}

QPushButton[danger="true"]:hover {
    background-color: rgba(229, 57, 53, 0.15);
}

QPushButton[accent="true"] {
    color: #e53935;
    border: 1px solid #e53935;
    background-color: transparent;
}

QPushButton[accent="true"]:hover {
    background-color: rgba(229, 57, 53, 0.15);
}

/* ---------- Поля и выбор ---------- */
QLineEdit, QComboBox, QPlainTextEdit {
    background-color: #0a0a0c;
    border: 1px solid #26262b;
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: #e53935;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
    border-color: #e53935;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #9e9e9e;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #141417;
    border: 1px solid #26262b;
    selection-background-color: rgba(229, 57, 53, 0.25);
    selection-color: #ffffff;
    outline: none;
}

QCheckBox {
    spacing: 8px;
    font-size: 14px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #33333a;
    background-color: #0a0a0c;
}

QCheckBox::indicator:hover {
    border-color: #e53935;
}

QCheckBox::indicator:checked {
    background-color: #e53935;
    border-color: #e53935;
}

QCheckBox:disabled {
    color: #616161;
}

/* ---------- Лог ---------- */
#logView {
    background-color: #0a0a0c;
    border: 1px solid #26262b;
    border-radius: 8px;
    font-family: 'DejaVu Sans Mono', 'Ubuntu Mono', monospace;
    font-size: 12px;
    color: #b0b0b0;
    padding: 8px;
}

#logHeader {
    color: #e53935;
    font-family: 'DejaVu Sans Mono', 'Ubuntu Mono', monospace;
    font-size: 13px;
    font-weight: bold;
}

/* ---------- Списки ---------- */
QListWidget#strategyList, QListWidget#plainList {
    background-color: #0a0a0c;
    border: 1px solid #26262b;
    border-radius: 8px;
    padding: 4px;
}

QListWidget#strategyList::item, QListWidget#plainList::item {
    padding: 6px 8px;
    border-radius: 4px;
    color: #d1d1d1;
}

QListWidget#strategyList::item:hover, QListWidget#plainList::item:hover {
    background-color: #1a1a1e;
}

QListWidget#strategyList::item:selected, QListWidget#plainList::item:selected {
    background-color: rgba(229, 57, 53, 0.25);
    color: #ffffff;
}

/* ---------- Скроллбары ---------- */
QScrollBar:vertical {
    background: #0a0a0c;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #2a2a2e;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #e53935;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0a0a0c;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #2a2a2e;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #e53935;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ---------- Прогресс ---------- */
QProgressBar {
    background-color: #0a0a0c;
    border: 1px solid #26262b;
    border-radius: 6px;
    text-align: center;
    color: #d1d1d1;
    font-size: 12px;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #e53935;
    border-radius: 5px;
}

/* ---------- Сплиттеры / разделители ---------- */
QToolTip {
    background-color: #141417;
    color: #d1d1d1;
    border: 1px solid #e53935;
    padding: 4px;
}
"""

