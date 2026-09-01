"""Settings screen (Fase 8 TODO_gui.md), mirror di ``cartellino/tui/screens/settings.py``.

La schermata più estesa del piano. Differenze intenzionali rispetto alla TUI:
- niente campo "Terminale (solo macOS)" — non applicabile alla GUI (lancio
  come app nativa, nessun terminale da scegliere all'avvio).
- cartella dati/output selezionate con `QFileDialog.getExistingDirectory`
  nativo, al posto del `FolderPickerScreen` custom (semplificazione già
  prevista dal piano — nessun equivalente da scrivere).
- contenuto avvolto in un `QScrollArea` (Fase 14, QA): senza, su una finestra
  piccola il layout costringeva la finestra a crescere oltre la dimensione
  richiesta pur di mostrare tutti i campi (nessun clipping, ma niente scroll
  nemmeno su schermi piccoli dove la finestra non può crescere oltre lo
  schermo) — mirror del `VerticalScroll` già usato dalla stessa schermata
  nella TUI.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cartellino.config import Config
from cartellino.credentials import delete_credentials, get_credentials
from cartellino.gui.screens.credentials import CredentialsDialog
from cartellino.user_config import (
    DEFAULT_DASHBOARD_BALANCE_CODES,
    DEFAULT_DASHBOARD_EXCEPTION_CODES,
    UserConfig,
)

log = logging.getLogger(__name__)

_DATA_TICKET_REGEX = r"\d{0,2}-?\d{0,2}-?\d{0,4}"


class SettingsScreen(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_folder = None
        self._template_riposo_sorgente: str | None = None
        """Percorso del PDF appena selezionato con "Sfoglia...", da copiare in
        `Config.template_riposo_file` al salvataggio (vedi `_salva`). `None` finché
        l'utente non sceglie un nuovo file."""

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)

        top_row = QHBoxLayout()
        self.btn_indietro = QPushButton("Indietro")
        self.btn_indietro.clicked.connect(self._torna_indietro)
        top_row.addWidget(self.btn_indietro)
        top_row.addStretch()
        layout.addLayout(top_row)

        layout.addWidget(QLabel("Anno corrente"))
        self.input_anno = QLineEdit()
        self.input_anno.setValidator(QRegularExpressionValidator(r"\d*"))
        layout.addWidget(self.input_anno)

        layout.addWidget(QLabel("Data minima riposi compensativi usati (MM-DD, opzionale)"))
        self.input_min_date = QLineEdit()
        layout.addWidget(self.input_min_date)

        layout.addWidget(QLabel("Formato export report"))
        self.select_formato = QComboBox()
        self.select_formato.addItems(["xlsx", "csv"])
        layout.addWidget(self.select_formato)

        layout.addWidget(QLabel("Codici eccezione dashboard (separati da virgola)"))
        self.input_codici_eccezione = QLineEdit()
        layout.addWidget(self.input_codici_eccezione)

        layout.addWidget(QLabel("Codici saldo mensile dashboard (separati da virgola)"))
        self.input_codici_saldo = QLineEdit()
        layout.addWidget(self.input_codici_saldo)

        self.switch_headless = QCheckBox("Download headless (solo Credenziali UNISA)")
        layout.addWidget(self.switch_headless)

        self.switch_check_updates = QCheckBox("Controlla aggiornamenti dell'app all'avvio")
        layout.addWidget(self.switch_check_updates)

        layout.addWidget(QLabel("Cartella dati (dove viene salvato cartellino.feather)"))
        data_folder_row = QHBoxLayout()
        self.input_data_folder = QLineEdit()
        self.btn_sfoglia_data_folder = QPushButton("Sfoglia...")
        self.btn_sfoglia_data_folder.clicked.connect(lambda: self._sfoglia(self.input_data_folder))
        data_folder_row.addWidget(self.input_data_folder)
        data_folder_row.addWidget(self.btn_sfoglia_data_folder)
        layout.addLayout(data_folder_row)

        layout.addWidget(QLabel("Cartella output report (vuoto = predefinita: {cartella dati}/{anno}/output)"))
        output_folder_row = QHBoxLayout()
        self.input_output_folder = QLineEdit()
        self.btn_sfoglia_output_folder = QPushButton("Sfoglia...")
        self.btn_sfoglia_output_folder.clicked.connect(lambda: self._sfoglia(self.input_output_folder))
        output_folder_row.addWidget(self.input_output_folder)
        output_folder_row.addWidget(self.btn_sfoglia_output_folder)
        layout.addLayout(output_folder_row)

        layout.addWidget(QLabel("Buoni pasto accreditati fino al (data_ticket.txt, DD-MM-YYYY)"))
        self.input_data_ticket = QLineEdit()
        self.input_data_ticket.setPlaceholderText("DD-MM-YYYY")
        self.input_data_ticket.setValidator(QRegularExpressionValidator(_DATA_TICKET_REGEX))
        layout.addWidget(self.input_data_ticket)

        self.btn_date_escluse = QPushButton("Gestisci date escluse (date_escluse.txt)")
        self.btn_date_escluse.setEnabled(False)
        self.btn_date_escluse.setToolTip("Non ancora implementato in GUI (Fase 9, vedi TODO_gui.md)")
        layout.addWidget(self.btn_date_escluse)

        layout.addWidget(QLabel("Template PDF richiesta riposo compensativo (issue #7)"))
        template_row = QHBoxLayout()
        self.input_template_riposo = QLineEdit()
        self.input_template_riposo.setReadOnly(True)
        self.btn_sfoglia_template_riposo = QPushButton("Sfoglia...")
        self.btn_sfoglia_template_riposo.clicked.connect(self._sfoglia_template_riposo)
        template_row.addWidget(self.input_template_riposo)
        template_row.addWidget(self.btn_sfoglia_template_riposo)
        layout.addLayout(template_row)

        self.stato_credenziali_label = QLabel("")
        layout.addWidget(self.stato_credenziali_label)

        cred_row = QHBoxLayout()
        self.btn_modifica_cred = QPushButton("Modifica credenziali")
        self.btn_modifica_cred.clicked.connect(self._apri_modifica_credenziali)
        self.btn_rimuovi_cred = QPushButton("Rimuovi credenziali")
        self.btn_rimuovi_cred.clicked.connect(self._rimuovi_credenziali)
        cred_row.addWidget(self.btn_modifica_cred)
        cred_row.addWidget(self.btn_rimuovi_cred)
        layout.addLayout(cred_row)

        self.errore_label = QLabel("")
        self.errore_label.setStyleSheet("color: red;")
        layout.addWidget(self.errore_label)

        save_row = QHBoxLayout()
        self.btn_salva = QPushButton("Salva")
        self.btn_salva.clicked.connect(self._salva)
        save_row.addStretch()
        save_row.addWidget(self.btn_salva)
        layout.addLayout(save_row)
        layout.addStretch()

    def refresh(self) -> None:
        window = self.window()
        self.data_folder = getattr(window, "data_folder", None)
        config: Config | None = getattr(window, "config", None)

        default_year = config.current_year if config else datetime.now().year
        user_config = UserConfig.load() or UserConfig(current_year=default_year)

        self.input_anno.setText(str(user_config.current_year))
        self.input_min_date.setText(user_config.min_date_riposi_usati or "")
        self.select_formato.setCurrentText(user_config.export_format)
        self.input_codici_eccezione.setText(",".join(user_config.dashboard_exception_codes))
        self.input_codici_saldo.setText(",".join(user_config.dashboard_balance_codes))
        self.switch_headless.setChecked(user_config.headless)
        self.switch_check_updates.setChecked(user_config.check_updates_on_startup)
        self.input_data_folder.setText(user_config.data_folder or (str(config.data_folder) if config else ""))
        self.input_output_folder.setText(user_config.output_folder or "")
        self.input_data_ticket.setText(self._leggi_data_ticket_esistente(config) if config else "")
        self._template_riposo_sorgente = None
        self._aggiorna_stato_template_riposo(config)
        self.errore_label.setText("")
        self._aggiorna_stato_credenziali()

    @staticmethod
    def _leggi_data_ticket_esistente(config: Config) -> str:
        try:
            return config.data_ticket_file.read_text().strip()
        except FileNotFoundError:
            return ""

    def _aggiorna_stato_template_riposo(self, config: Config | None) -> None:
        if config is not None and config.template_riposo_file.exists():
            self.input_template_riposo.setText(f"Impostato ({config.template_riposo_file})")
        else:
            self.input_template_riposo.setText("Non impostato")

    @staticmethod
    def _testo_stato_credenziali() -> str:
        credenziali_esistenti = get_credentials()
        if credenziali_esistenti is not None:
            username_esistente, _ = credenziali_esistenti
            return f"Credenziali UniSA: impostate (username: {username_esistente})"
        return "Credenziali UniSA: non impostate"

    def _aggiorna_stato_credenziali(self) -> None:
        self.stato_credenziali_label.setText(self._testo_stato_credenziali())

    def _apri_modifica_credenziali(self) -> None:
        dialog = CredentialsDialog(self)
        if dialog.exec() == CredentialsDialog.DialogCode.Accepted:
            self._aggiorna_stato_credenziali()

    def _rimuovi_credenziali(self) -> None:
        delete_credentials()
        log.info("Credenziali UniSA rimosse dal keyring.")
        self._aggiorna_stato_credenziali()

    def _sfoglia(self, campo: QLineEdit) -> None:
        start = campo.text().strip() or str(Path.home())
        path = QFileDialog.getExistingDirectory(self, "Seleziona cartella", start)
        if path:
            campo.setText(path)

    def _sfoglia_template_riposo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona template PDF", str(Path.home()), "PDF (*.pdf)")
        if path:
            self._template_riposo_sorgente = path
            self.input_template_riposo.setText(f"Da copiare al salvataggio: {path}")

    def _salva(self) -> None:
        anno_str = self.input_anno.text().strip()
        if not anno_str.isdigit():
            self.errore_label.setText("Anno corrente obbligatorio e numerico.")
            return

        data_ticket_valore = self.input_data_ticket.text().strip()
        if data_ticket_valore:
            try:
                datetime.strptime(data_ticket_valore, "%d-%m-%Y")
            except ValueError:
                self.errore_label.setText("Data ticket non valida (formato DD-MM-YYYY).")
                return

        data_folder_valore = self.input_data_folder.text().strip()
        if not data_folder_valore:
            self.errore_label.setText("La cartella dati non può essere vuota.")
            return
        # Risolto in path assoluto prima di salvare: un path relativo digitato a mano
        # verrebbe altrimenti interpretato al prossimo avvio relativamente alla cwd da
        # cui parte l'eseguibile, vanificando APP_DATA_DIR (cartellino_gui.py) pensata
        # per essere indipendente da dove viene lanciato — stesso motivo della TUI.
        data_folder_valore = str(Path(data_folder_valore).expanduser().resolve())
        output_folder_valore = self.input_output_folder.text().strip() or None
        if output_folder_valore:
            output_folder_valore = str(Path(output_folder_valore).expanduser().resolve())

        min_date = self.input_min_date.text().strip() or None
        export_format = self.select_formato.currentText()
        codici_eccezione = [c.strip() for c in self.input_codici_eccezione.text().split(",") if c.strip()]
        codici_saldo = [c.strip() for c in self.input_codici_saldo.text().split(",") if c.strip()]
        headless = self.switch_headless.isChecked()
        check_updates_on_startup = self.switch_check_updates.isChecked()

        UserConfig(
            current_year=int(anno_str),
            min_date_riposi_usati=min_date,
            headless=headless,
            export_format=export_format,
            dashboard_exception_codes=codici_eccezione or list(DEFAULT_DASHBOARD_EXCEPTION_CODES),
            dashboard_balance_codes=codici_saldo or list(DEFAULT_DASHBOARD_BALANCE_CODES),
            data_folder=data_folder_valore,
            output_folder=output_folder_valore,
            check_updates_on_startup=check_updates_on_startup,
        ).save()

        # data_ticket.txt e il template PDF vanno scritti nella NUOVA cartella dati
        # (Config va ricaricato per avere i path corretti, dato che data_folder può
        # essere appena cambiato in questo stesso salvataggio).
        if data_ticket_valore or self._template_riposo_sorgente:
            nuovo_config = Config.load(data_folder=self.data_folder)
            if data_ticket_valore:
                nuovo_config.data_ticket_file.write_text(data_ticket_valore + "\n")
            if self._template_riposo_sorgente:
                # Copiato (non solo referenziato) nella cartella dati: il file
                # sorgente scelto con "Sfoglia..." può essere spostato/rinominato
                # dall'utente in seguito, la richiesta di riposo deve continuare a
                # funzionare — resta usato finché non viene sovrascritto da un
                # nuovo caricamento.
                shutil.copy(self._template_riposo_sorgente, nuovo_config.template_riposo_file)
                self._template_riposo_sorgente = None

        log.info("Impostazioni salvate.")
        self.errore_label.setText("")
        window = self.window()
        if hasattr(window, "reload_config_and_route"):
            window.reload_config_and_route()

    def _torna_indietro(self) -> None:
        window = self.window()
        if hasattr(window, "show_dashboard"):
            window.show_dashboard()
        elif hasattr(window, "reload_config_and_route"):
            window.reload_config_and_route()
