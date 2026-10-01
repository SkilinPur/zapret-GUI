# =============================================================================
# Вкладка «Система» — автозапуск и работа без пароля (объединяет Сервис+Права)
# =============================================================================

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .permissions_tab import PermissionsTab
from .service_tab import ServiceTab
from .widgets import make_title


class SystemTab(QWidget):
    def __init__(self, zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(make_title(
            "Система",
            "Автозапуск при включении ПК и работа без пароля",
        ))

        self.tabs = QTabWidget()
        self.tabs.addTab(ServiceTab(self.z), "🛠️ Автозапуск")
        self.tabs.addTab(PermissionsTab(self.z), "🔑 Без пароля")
        root.addWidget(self.tabs, 1)
