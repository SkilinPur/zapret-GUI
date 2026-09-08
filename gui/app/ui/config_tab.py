# =============================================================================
# Вкладка «Конфигурация» — редактирование conf.env
# =============================================================================
# Автор GUI: SkilinPur (https://github.com/SkilinPur) | Репозиторий: https://github.com/SkilinPur/zapret-GUI

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..zapret import Zapret
from ..worker import CommandWorker
from .widgets import add_row, log_line, make_button, make_card, make_title


class ConfigTab(QWidget):
    def __init__(self, zapret: Zapret, parent=None):
        super().__init__(parent)
        self.z = zapret
        self._worker = None
        self._build_ui()
        self.load_config()

    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(make_title(
            "Конфигурация",
            "Настройки zapret, сохраняются в conf.env",
        ))

        card = make_card()
        cl = card.layout()

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(self.z.strategies())
        cl.addWidget(add_row("Стратегия", self.strategy_combo))

        self.strategy_desc = QLabel("—")
        self.strategy_desc.setObjectName("statusMetaLabel")
        self.strategy_desc.setWordWrap(True)
        cl.addWidget(self.strategy_desc)

        self.strategy_combo.currentIndexChanged.connect(self._update_strategy_desc)

        self.interface_combo = QComboBox()
        self.interface_combo.addItems(self.z.interfaces())
        cl.addWidget(add_row("Интерфейс", self.interface_combo))

        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["auto"] + self.z.backends())
        cl.addWidget(add_row("Бэкенд фаервола", self.backend_combo))

        gf_row = QWidget()
        gfl = QVBoxLayout(gf_row)
        gfl.setContentsMargins(0, 0, 0, 0)
        self.gt_check = QCheckBox("GameFilterTCP (игровые порты TCP)")
        self.gt_check.setToolTip(
            "Обход замедления для TCP-трафика игр (порты 1024–65535 по полному "
            "списку IP). Включайте, если игра или её лаунчер не работают "
            "при включённом zapret."
        )
        self.gu_check = QCheckBox("GameFilterUDP (игровые порты UDP)")
        self.gu_check.setToolTip(
            "Обход замедления для UDP-трафика игр (игровой трафик, голос). "
            "Включайте, если голос/матчи в играх не работают при включённом zapret."
        )
        gfl.addWidget(self.gt_check)
        gfl.addWidget(self.gu_check)
        gf_hint = QLabel(
            "Зачем: zapret по умолчанию обходит только 80/443 и список сайтов. "
            "GameFilter дополнительно обрабатывает игровой трафик, который идёт "
            "не через 80/443 (порты 1024–65535 по полному IP-списку): TCP — "
            "соединения и лаунчеры, UDP — матчи и голос. Обычно не нужен — "
            "включайте, если игры не работают при активном zapret."
        )
        gf_hint.setObjectName("statusMetaLabel")
        gf_hint.setWordWrap(True)
        gfl.addWidget(gf_hint)
        cl.addWidget(add_row("GameFilter", gf_row))

        btn_row = QWidget()
        btl = QVBoxLayout(btn_row)
        btl.setContentsMargins(0, 0, 0, 0)
        btl.setSpacing(6)
        self.save_btn = make_button("💾 Сохранить конфигурацию", primary=True)
        self.save_btn.setFixedWidth(240)
        btl.addWidget(self.save_btn)
        btl.addStretch()
        cl.addWidget(btn_row)

        root.addWidget(card)

        log_card = make_card()
        ll = log_card.layout()
        header = QLabel(">_ вывод")
        header.setObjectName("logHeader")
        ll.addWidget(header)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        ll.addWidget(self.log_view, 1)
        root.addWidget(log_card, 1)

        self.save_btn.clicked.connect(self.save_config)

    # ------------------------------------------------------------------

    def refresh_strategies(self):
        cfg = self.z.read_config()
        current = cfg.get("strategy") or self.strategy_combo.currentText()
        self.strategy_combo.clear()
        self.strategy_combo.addItems(self.z.strategies())
        idx = self.strategy_combo.findText(current)
        if idx >= 0:
            self.strategy_combo.setCurrentIndex(idx)
        self._update_strategy_desc()

    def _update_strategy_desc(self):
        name = self.strategy_combo.currentText()
        desc = self.z.strategy_description(name) if name else ""
        self.strategy_desc.setText(desc or "Описание не найдено")

    def load_config(self):
        cfg = self.z.read_config()

        strategy = cfg.get("strategy", "")
        if strategy:
            idx = self.strategy_combo.findText(strategy)
            if idx >= 0:
                self.strategy_combo.setCurrentIndex(idx)

        interface = cfg.get("interface", "any")
        idx = self.interface_combo.findText(interface)
        if idx >= 0:
            self.interface_combo.setCurrentIndex(idx)

        backend = cfg.get("firewall_backend", "auto")
        idx = self.backend_combo.findText(backend)
        if idx >= 0:
            self.backend_combo.setCurrentIndex(idx)

        self.gt_check.setChecked(cfg.get("gamefiltertcp") == "true")
        self.gu_check.setChecked(cfg.get("gamefilterudp") == "true")

        self._update_strategy_desc()

    def save_config(self):
        if self._worker and self._worker.isRunning():
            self.append_log("! предыдущее сохранение ещё выполняется")
            return
        strategy = self.strategy_combo.currentText()
        interface = self.interface_combo.currentText()
        backend = self.backend_combo.currentText()
        gt = self.gt_check.isChecked()
        gu = self.gu_check.isChecked()

        if not strategy:
            self.append_log("! стратегия не выбрана")
            return

        self.append_log(
            f"> сохранение: {strategy} | {interface} | {backend} | "
            f"gf={('tcp' if gt else '') + ('udp' if gu else '') or 'выкл'}"
        )
        cmd = self.z.config_set_cmd(
            strategy, interface, gt, gu, firewall_backend=backend, restart=False,
        )
        self._worker = CommandWorker(
            cmd, cwd=str(self.z.repo_root), elevated=True,
        )
        self._worker.output.connect(self.append_log)
        self._worker.failed.connect(lambda msg: self.append_log(f"! {msg}"))
        self._worker.success.connect(lambda _: self.append_log("> конфигурация сохранена"))
        self._worker.start()

    def append_log(self, text):
        log_line(self.log_view, text)

