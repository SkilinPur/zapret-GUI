#!/usr/bin/env python3
"""Скриншоты вкладок GUI (offscreen) для README.

Запуск: QT_QPA_PLATFORM=offscreen <venv-python> tools/screenshots.py [<каталог>]
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "0")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from gui.app.theme import QSS  # noqa: E402
from gui.app.window import NAV_ITEMS, MainWindow  # noqa: E402

# скриншоты без мастера первого запуска
QSettings().setValue("wizard/done", True)

SLUGS = {
    "Как пользоваться": "help",
    "Статус": "status",
    "Конфигурация": "config",
    "Обновление": "update",
    "Сервис": "service",
    "Автоподбор": "autotune",
    "Права": "permissions",
    "Авторство": "credits",
}


def safe(name: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", name.lower()).strip("_")
    return SLUGS.get(name, s or "tab")


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs" / "screenshots")
    outdir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.resize(960, 640)
    win.show()

    for i, (name, _cls) in enumerate(NAV_ITEMS):
        win.nav.setCurrentRow(i)
        for _ in range(3):
            app.processEvents()
        pix = win.grab()
        path = outdir / f"{safe(name)}.png"
        if not pix.save(str(path)):
            print(f"! не сохранился: {path}", file=sys.stderr)
        else:
            print(f"✓ {path}")

    win.close()


if __name__ == "__main__":
    main()
