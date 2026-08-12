#!/usr/bin/env python3
# =============================================================================
# Точка входа GUI для zapret-discord-youtube-linux
#
# GUI: SkilinPur (https://github.com/SkilinPur/zapret-GUI)
# Базируется на: Sergeydigl3/zapret-discord-youtube-linux
# =============================================================================

import os
import sys

from PySide6.QtWidgets import QApplication

from .theme import QSS
from .window import MainWindow


def main():
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Zapret Discord YouTube")
    app.setOrganizationName("InIProject")
    app.setStyleSheet(QSS)

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

