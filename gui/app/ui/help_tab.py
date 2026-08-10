# =============================================================================
# Вкладка «Как пользоваться» — руководство по программе
# =============================================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from .widgets import make_card, make_title


def _step(num, text):
    """Строка-шаг: номер красным моноширинным + описание."""
    row = QWidget()
    layout = QGridLayout(row)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setHorizontalSpacing(10)

    num_lbl = QLabel(f"{num:02d}")
    num_lbl.setStyleSheet(
        "color:#e53935; font-family:monospace; font-weight:bold; font-size:16px;"
    )
    num_lbl.setFixedWidth(26)
    layout.addWidget(num_lbl, 0, 0, Qt.AlignTop)

    txt = QLabel(text)
    txt.setProperty("subtitle", True)
    txt.setWordWrap(True)
    layout.addWidget(txt, 0, 1)
    layout.setColumnStretch(1, 1)
    return row


def _bullet(text):
    row = QWidget()
    layout = QGridLayout(row)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setHorizontalSpacing(10)
    bullet = QLabel(">_")
    bullet.setStyleSheet("color:#e53935; font-family:monospace; font-weight:bold;")
    bullet.setFixedWidth(26)
    layout.addWidget(bullet, 0, 0, Qt.AlignTop)
    txt = QLabel(text)
    txt.setProperty("subtitle", True)
    txt.setWordWrap(True)
    layout.addWidget(txt, 0, 1)
    layout.setColumnStretch(1, 1)
    return row


class HelpTab(QWidget):
    def __init__(self, zapret=None, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer.addWidget(scroll)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        root = QVBoxLayout(body)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(make_title(
            "Как пользоваться",
            "Краткое руководство по настройке и запуску.",
        ))

        # --- Обзор ---
        overview = make_card()
        ol = overview.layout()
        title = QLabel("Обзор")
        title.setProperty("section", True)
        ol.addWidget(title)
        desc = QLabel(
            "GUI — это обёртка над zapret-discord-youtube-linux. Он не содержит "
            "собственной логики обхода, а управляет существующими bash-скриптами "
            "адаптера. Все действия выполняются теми же командами, что и через CLI."
        )
        desc.setProperty("subtitle", True)
        desc.setWordWrap(True)
        ol.addWidget(desc)
        root.addWidget(overview)

        # --- Быстрый старт ---
        quick = make_card()
        ql = quick.layout()
        title = QLabel("Быстрый старт")
        title.setProperty("section", True)
        ql.addWidget(title)
        ql.addWidget(_step(
            1,
            "Стратегии уже в комплекте (23 шт.) — ничего скачивать не нужно. "
            "Единственное, что может понадобиться — вкладка «Стратегии» → "
            "«Скачать nfqws», если он ещё не установлен.",
        ))
        ql.addWidget(_step(
            2,
            "Настроить права — вкладка «Права» → «Настроить работу без пароля». "
            "Потребуется ввести пароль в терминале один раз.",
        ))
        ql.addWidget(_step(
            3,
            "Запустить — вкладка «Статус» → кнопка «Старт». "
            "Индикатор станет красным «[СТАТУС: РАБОТАЕТ]».",
        ))
        ql.addWidget(_step(
            4,
            "Проверить — откройте YouTube или Discord. Если работает медленно, "
            "попробуйте другие стратегии или автоподбор.",
        ))
        root.addWidget(quick)

        # --- Вкладки ---
        tabs = make_card()
        tl = tabs.layout()
        title = QLabel("Что делает каждая вкладка")
        title.setProperty("section", True)
        tl.addWidget(title)
        tl.addWidget(_bullet(
            "<b>Статус</b> — индикатор работы, запуск/остановка, режим запуска "
            "(фоновый демон или systemd-сервис), живой лог.",
        ))
        tl.addWidget(_bullet(
            "<b>Конфигурация</b> — стратегия, интерфейс, бэкенд фаервола, "
            "GameFilterTCP/UDP. Сохраняется в conf.env.",
        ))
        tl.addWidget(_bullet(
            "<b>Стратегии</b> — список файлов .bat (23 в комплекте), "
            "обновление стратегий и скачивание nfqws по отдельности.",
        ))
        tl.addWidget(_bullet(
            "<b>Сервис</b> — установка/удаление службы автозагрузки, "
            "запуск/остановка/перезапуск, просмотр логов.",
        ))
        tl.addWidget(_bullet(
            "<b>Автоподбор</b> — автоматический подбор рабочей стратегии "
            "(экспериментально).",
        ))
        tl.addWidget(_bullet(
            "<b>Права</b> — настройка работы без пароля (NOPASSWD sudo) "
            "для запуска/остановки zapret.",
        ))
        root.addWidget(tabs)

        # --- Проблемы ---
        tips = make_card()
        tl2 = tips.layout()
        title = QLabel("Если что-то не работает")
        title.setProperty("section", True)
        tl2.addWidget(title)
        tl2.addWidget(_bullet(
            "Убедитесь, что nfqws скачан (вкладка «Стратегии»).",
        ))
        tl2.addWidget(_bullet(
            "Убедитесь, что настроены права (вкладка «Права»).",
        ))
        tl2.addWidget(_bullet(
            "Попробуйте другие стратегии или «Автоподбор».",
        ))
        tl2.addWidget(_bullet(
            "Подробности в документации порта: "
            "Sergeydigl3/zapret-discord-youtube-linux.",
        ))
        root.addWidget(tips)

        root.addStretch()
        scroll.setWidget(body)
