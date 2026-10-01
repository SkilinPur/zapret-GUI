# =============================================================================
# Вкладка «Списки» — редактирование пользовательских списков (user-lists)
# =============================================================================

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..worker import CommandWorker
from .widgets import add_row, make_button, make_card, make_title


class UserListsTab(QWidget):
    def __init__(self, zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._build_ui()
        self._load_list()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        root.addWidget(make_title(
            "Списки",
            "Свои домены/IP для обхода и исключений",
        ))

        card = make_card()
        cl = card.layout()

        self.combo = QComboBox()
        for key, label, _path in self.z.user_lists_info():
            self.combo.addItem(label, key)
        cl.addWidget(add_row("Список", self.combo))

        hint = QLabel(
            "Один адрес на строку (домен или IP/CIDR). Сохраняется в user-lists "
            "и применяется при следующем запуске обхода."
        )
        hint.setObjectName("statusMetaLabel")
        hint.setWordWrap(True)
        cl.addWidget(hint)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("logView")
        self.editor.setPlaceholderText("Один адрес на строку (домен или IP/CIDR)…")
        cl.addWidget(self.editor, 1)

        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        self.save_btn = make_button("💾 Сохранить список", primary=True)
        self.save_btn.setMinimumWidth(220)
        self.status = QLabel("")
        self.status.setObjectName("statusMetaLabel")
        rl.addWidget(self.save_btn)
        rl.addWidget(self.status, 1)
        cl.addWidget(row)
        root.addWidget(card)

        self.combo.currentIndexChanged.connect(self._load_list)
        self.save_btn.clicked.connect(self._save)

    def _load_list(self):
        key = self.combo.currentData()
        self.editor.setPlainText(self.z.read_user_list(key))
        self.status.setText("")

    def _save(self):
        if self._worker and self._worker.isRunning():
            return
        key = self.combo.currentData()
        text = self.editor.toPlainText()
        self.save_btn.setEnabled(False)
        self.status.setText("сохранение…")
        self._worker = CommandWorker(
            self.z.save_user_list_cmd(key), cwd=str(self.z.repo_root),
            elevated=True, stdin=text,
        )
        self._worker.failed.connect(lambda m: self._on_done(f"! ошибка: {m}"))
        self._worker.success.connect(lambda _: self._on_done("✓ сохранено"))
        self._worker.start()

    def _on_done(self, msg):
        self.save_btn.setEnabled(True)
        self.status.setText(msg)
        self._worker = None
