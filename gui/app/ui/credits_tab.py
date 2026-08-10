# =============================================================================
# Вкладка «Авторство» — авторы проекта с аватарками и ссылками
# =============================================================================

import threading

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from .. import avatar
from .widgets import make_card, make_title

AVATAR_SIZE = 64

# (роль, имя, ссылка на автора, имя репозитория, ссылка на репозиторий)
AUTHORS = [
    (
        "GUI (графический интерфейс)",
        "SkilinPur",
        "https://github.com/SkilinPur",
        "zapret-GUI",
        "https://github.com/SkilinPur/zapret-GUI",
    ),
    (
        "Порт на Linux (адаптер)",
        "Sergeydigl3",
        "https://github.com/Sergeydigl3",
        "zapret-discord-youtube-linux",
        "https://github.com/Sergeydigl3/zapret-discord-youtube-linux",
    ),
    (
        "Исходник (стратегии)",
        "Flowseal",
        "https://github.com/Flowseal",
        "zapret-discord-youtube",
        "https://github.com/Flowseal/zapret-discord-youtube",
    ),
    (
        "Ядро zapret (nfqws)",
        "bol-van",
        "https://github.com/bol-van",
        "zapret",
        "https://github.com/bol-van/zapret",
    ),
]


def _link(text, url):
    return f'<a style="color:#e53935;" href="{url}">{text}</a>'


def _mono(text, color="#9e9e9e"):
    return f'<span style="font-family:monospace; color:{color};">{text}</span>'


class AvatarLoader(QObject):
    """Фоновая загрузка аватарок из GitHub (daemon-поток, не блокирует UI)."""

    ready = Signal(str, str)  # username, путь к файлу ("" при неудаче)

    def __init__(self, users, parent=None):
        super().__init__(parent)
        self._users = users

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        for username in self._users:
            path = avatar.download_avatar(username)
            self.ready.emit(username, str(path) if path else "")


class CreditsTab(QWidget):
    def __init__(self, zapret=None, parent=None):
        super().__init__(parent)
        self._avatars = {}
        self._build_ui()
        self._start_avatar_loading()

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
            "Авторство",
            "Проект собран вокруг порта на Linux от Sergeydigl3: "
            "исходные стратегии — Flowseal, ядро — bol-van.",
        ))

        intro = make_card()
        il = intro.layout()
        desc = QLabel(
            "<p>Этот GUI является обёрткой вокруг "
            + _link("zapret-discord-youtube-linux",
                    "https://github.com/Sergeydigl3/zapret-discord-youtube-linux")
            + " и не содержит собственной логики обхода: весь функционал "
            "выполняется существующими скриптами адаптера.</p>"
            "<p>Ссылки открываются в вашем браузере.</p>"
        )
        desc.setProperty("subtitle", True)
        desc.setWordWrap(True)
        desc.setTextInteractionFlags(Qt.TextBrowserInteraction)
        desc.setOpenExternalLinks(True)
        il.addWidget(desc)
        root.addWidget(intro)

        self._cards = []
        for role, name, name_url, repo_name, repo_url in AUTHORS:
            card, avatar_label = self._author_card(
                role, name, name_url, repo_name, repo_url
            )
            self._cards.append(card)
            self._avatars[name] = avatar_label
            root.addWidget(card)

        root.addStretch()
        scroll.setWidget(body)

    def _start_avatar_loading(self):
        users = [a[1] for a in AUTHORS]
        self._loader = AvatarLoader(users, self)
        self._loader.ready.connect(self._on_avatar_ready)
        self._loader.start()

    def _on_avatar_ready(self, username, path):
        label = self._avatars.get(username)
        if not label:
            return
        if path:
            pm = avatar.avatar_pixmap_from_path(path, AVATAR_SIZE)
            if pm and not pm.isNull():
                label.setPixmap(pm)
                return
        label.setPixmap(avatar.initials_pixmap(username, AVATAR_SIZE))

    def _author_card(self, role, name, name_url, repo_name, repo_url):
        card = make_card(margins=(14, 12, 14, 12))

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        avatar_label = QLabel()
        avatar_label.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        avatar_label.setPixmap(avatar.initials_pixmap(name, AVATAR_SIZE))
        row.addWidget(avatar_label, 0, Qt.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(6)
        info.setContentsMargins(0, 0, 0, 0)

        role_lbl = QLabel(role)
        role_lbl.setProperty("section", True)
        info.addWidget(role_lbl)

        author = QLabel(_mono(">_ автор: ") + _link(name, name_url))
        author.setTextInteractionFlags(Qt.TextBrowserInteraction)
        author.setOpenExternalLinks(True)
        info.addWidget(author)

        repo = QLabel(_mono(">_ репозиторий: ") + _link(repo_name, repo_url))
        repo.setTextInteractionFlags(Qt.TextBrowserInteraction)
        repo.setOpenExternalLinks(True)
        info.addWidget(repo)

        info.addStretch()
        row.addLayout(info, 1)

        card.layout().addLayout(row)
        return card, avatar_label
