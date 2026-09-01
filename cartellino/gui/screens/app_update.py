"""App update dialog (Fase 11 TODO_gui.md), mirror di
``cartellino/tui/screens/app_update.py``.

Esito del controllo aggiornamenti dell'app — distinto dall'Update screen (Fase
4), che riguarda l'aggiornamento dei *dati* del cartellino, non dell'app
stessa. Niente self-update automatico (stesso motivo della TUI: binario
onedir, `.pkg` macOS firmato/notarizzato, `.exe` Windows in esecuzione): il
pulsante apre la pagina della release nel browser di sistema
(`QDesktopServices.openUrl`), l'installazione resta manuale.

Sostituisce il `QMessageBox` usato provvisoriamente da
``DashboardScreen._mostra_esito_aggiornamento`` (Fase 3) con una schermata
dedicata che mostra anche le note di rilascio in Markdown.
"""

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout

from cartellino.update_checker import ReleaseInfo


class AppUpdateDialog(QDialog):
    def __init__(self, current_version: str, release: ReleaseInfo | None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Controllo aggiornamenti")
        self._release = release

        layout = QVBoxLayout(self)

        if release is None:
            layout.addWidget(QLabel(f"Nessun aggiornamento disponibile (versione attuale: {current_version})."))
            # Senza un widget "expanding" nel layout (il QTextBrowser del ramo
            # sotto, con stretch=1), un ridimensionamento manuale del dialog
            # distribuirebbe lo spazio extra tra i widget invece che in fondo
            # — questo stretch lo assorbe, coerente col comportamento già
            # naturale del ramo con release.
            layout.addStretch()
        else:
            layout.addWidget(QLabel(f"Nuova versione disponibile: {release.version} (attuale: {current_version})"))
            viewer = QTextBrowser()
            viewer.setMarkdown(release.body or "_Nessuna nota di rilascio._")
            layout.addWidget(viewer, stretch=1)

        button_row = QHBoxLayout()
        button_row.addStretch()
        if release is not None:
            btn_apri = QPushButton("Apri pagina di download")
            btn_apri.clicked.connect(self._apri_download)
            button_row.addWidget(btn_apri)
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.clicked.connect(self.accept)
        button_row.addWidget(btn_chiudi)
        layout.addLayout(button_row)

    def _apri_download(self) -> None:
        if self._release is not None:
            QDesktopServices.openUrl(QUrl(self._release.html_url))
