"""Onboarding screen (Fase 2 TODO_gui.md), mirror di ``cartellino/tui/screens/onboarding.py``.

Setup iniziale: mostrata quando manca `config.toml`. Stessa logica di dominio
riusata senza modifiche (`UserConfig.save`, `set_credentials`), solo i widget
cambiano (Qt nativi al posto di quelli Textual).
"""

import logging
from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cartellino.credentials import set_credentials
from cartellino.user_config import UserConfig

log = logging.getLogger(__name__)


class OnboardingScreen(QWidget):
    """Setup iniziale: mostrata quando manca `config.toml`."""

    saved = Signal()
    """Emesso dopo un salvataggio riuscito — il chiamante (MainWindow) reagisce
    ricaricando la configurazione e instradando alla schermata successiva,
    mirror di ``self.app.reload_config_and_route()`` nella TUI."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Benvenuto in Cartellino UniSA.\n"
                "Configura anno e credenziali per iniziare "
                "(le credenziali sono opzionali qui: puoi impostarle anche dopo, da Impostazioni)."
            )
        )

        layout.addWidget(QLabel("Anno corrente *"))
        self.input_anno = QLineEdit(str(datetime.now().year))
        self.input_anno.setPlaceholderText("2026")
        self.input_anno.setValidator(QRegularExpressionValidator(r"\d*"))
        layout.addWidget(self.input_anno)

        layout.addWidget(QLabel("Data minima riposi compensativi usati (MM-DD, opzionale)"))
        self.input_min_date = QLineEdit()
        self.input_min_date.setPlaceholderText("01-01")
        layout.addWidget(self.input_min_date)

        layout.addWidget(QLabel("Username UniSA (opzionale)"))
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("mario.rossi")
        layout.addWidget(self.input_username)

        layout.addWidget(QLabel("Password UniSA (opzionale)"))
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_password)

        self.switch_headless = QCheckBox("Download headless (solo per Credenziali UNISA)")
        layout.addWidget(self.switch_headless)

        self.errore_label = QLabel("")
        self.errore_label.setStyleSheet("color: red;")
        layout.addWidget(self.errore_label)

        button_row = QHBoxLayout()
        self.btn_salva = QPushButton("💾 Salva e continua")
        self.btn_salva.setObjectName("btn-salva")
        self.btn_salva.clicked.connect(self._salva)
        button_row.addStretch()
        button_row.addWidget(self.btn_salva)
        layout.addLayout(button_row)
        layout.addStretch()

    def _salva(self) -> None:
        anno_str = self.input_anno.text().strip()
        min_date = self.input_min_date.text().strip() or None
        username = self.input_username.text().strip()
        password = self.input_password.text()
        headless = self.switch_headless.isChecked()

        if not anno_str.isdigit():
            self.errore_label.setText("Anno corrente obbligatorio e numerico.")
            return

        user_config = UserConfig(
            current_year=int(anno_str),
            min_date_riposi_usati=min_date,
            headless=headless,
        )
        user_config.save()

        if username and password:
            set_credentials(username, password)

        log.info(f"Configurazione iniziale salvata (anno {anno_str}).")
        self.errore_label.setText("")
        self.saved.emit()
