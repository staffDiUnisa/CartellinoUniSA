"""Credentials dialog (Fase 10 TODO_gui.md), mirror di
``cartellino/tui/screens/credentials.py``.

A differenza delle altre schermate (pagine dello ``QStackedWidget``), questa è
un ``QDialog`` modale con valore di ritorno — stessa distinzione descritta in
``cartellino/gui/app.py::MainWindow``: `exec()` blocca finché l'utente non
salva o annulla, e ``result() == QDialog.DialogCode.Accepted`` dice al
chiamante (Impostazioni) se aggiornare la riga di stato delle credenziali,
mirror del `Screen[bool]`/`dismiss(True/False)` della TUI.
"""

import logging

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from cartellino.credentials import set_credentials

log = logging.getLogger(__name__)


class CredentialsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Credenziali UniSA")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Username UniSA"))
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("mario.rossi")
        layout.addWidget(self.input_username)

        layout.addWidget(QLabel("Password UniSA"))
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_password)

        self.errore_label = QLabel("")
        self.errore_label.setStyleSheet("color: red;")
        layout.addWidget(self.errore_label)

        # Pulsanti custom invece di QDialogButtonBox: i pulsanti "standard" di
        # Qt (Save/Cancel) sono etichettati in inglese salvo caricare le
        # traduzioni Qt integrate (qttranslations, non bundled) — incoerente
        # con un'app interamente in italiano, stesso pattern (QPushButton
        # esplicito) già usato in tutte le altre schermate.
        layout.addStretch()
        button_row = QHBoxLayout()
        button_row.addStretch()
        self.btn_annulla = QPushButton("✖️ Annulla")
        self.btn_annulla.setObjectName("btn-annulla")
        self.btn_annulla.clicked.connect(self.reject)
        self.btn_salva = QPushButton("💾 Salva")
        self.btn_salva.setObjectName("btn-salva")
        self.btn_salva.clicked.connect(self._salva)
        button_row.addWidget(self.btn_annulla)
        button_row.addWidget(self.btn_salva)
        layout.addLayout(button_row)

    def _salva(self) -> None:
        username = self.input_username.text().strip()
        password = self.input_password.text()
        if not username or not password:
            self.errore_label.setText("Username e password sono obbligatori.")
            return
        set_credentials(username, password)
        log.info("Credenziali UniSA aggiornate.")
        self.accept()
