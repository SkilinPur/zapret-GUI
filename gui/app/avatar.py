# =============================================================================
# Аватарки авторов — загрузка из GitHub с кэшем и fallback-инициалами
# =============================================================================

import urllib.request
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap

CACHE_DIR = Path.home() / ".cache" / "zapret-gui" / "avatars"
USER_AGENT = "zapret-gui"
TIMEOUT = 8


def download_avatar(username, size=160):
    """Скачивает аватар GitHub в кэш. Возвращает путь или None."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / f"{username}.png"
        if path.exists() and path.stat().st_size > 0:
            return path
        url = f"https://github.com/{username}.png?size={size}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
        if not data:
            return None
        path.write_bytes(data)
        return path
    except Exception:
        return None


def _circular_scaled(source: QPixmap, size: int) -> QPixmap:
    out = QPixmap(size, size)
    out.fill(Qt.transparent)
    scaled = source.scaled(
        size, size,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation,
    )
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    x = (scaled.width() - size) // 2
    y = (scaled.height() - size) // 2
    painter.drawPixmap(0, 0, scaled.copy(QRect(x, y, size, size)))
    painter.end()
    return out


def avatar_pixmap_from_path(path, size):
    """Загружает аватар из файла и делает круглым. None при ошибке."""
    try:
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return None
        return _circular_scaled(pixmap, size)
    except Exception:
        return None


def initials_pixmap(letter, size, bg="#e53935"):
    """Fallback: круг с первой буквой ника."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(bg))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(max(10, size // 3))
    painter.setFont(font)
    painter.drawText(pm.rect(), Qt.AlignCenter, letter[0].upper())
    painter.end()
    return pm
