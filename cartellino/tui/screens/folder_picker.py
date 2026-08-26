from pathlib import Path
from typing import Iterable, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Static


class _SoloCartelle(DirectoryTree):
    """DirectoryTree che mostra solo le sottocartelle (i file non sono selezionabili
    come cartella di destinazione)."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [p for p in paths if p.is_dir()]


class FolderPickerScreen(ModalScreen[Optional[Path]]):
    """Modale per selezionare una cartella: naviga con l'albero (aggiorna il campo
    in alto) oppure scrivi/incolla direttamente il percorso. "Conferma" ritorna il
    `Path` scritto nel campo (anche se non esiste ancora: verrà creato dal chiamante),
    "Annulla" ritorna `None`."""

    BINDINGS = [("escape", "annulla", "Annulla")]

    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()
        start = start_path if start_path and start_path.exists() else Path.cwd()
        self._start = start.resolve()

    def compose(self) -> ComposeResult:
        with Vertical(id="folder-picker"):
            yield Static("Seleziona una cartella (o scrivi/incolla il percorso)")
            yield Input(value=str(self._start), id="fp-input")
            yield _SoloCartelle(self._start, id="fp-tree")
            with Horizontal(classes="button-row"):
                yield Button("Conferma", id="fp-conferma", variant="primary")
                yield Button("Annulla", id="fp-annulla")

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.query_one("#fp-input", Input).value = str(event.path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fp-conferma":
            valore = self.query_one("#fp-input", Input).value.strip()
            self.dismiss(Path(valore) if valore else None)
        elif event.button.id == "fp-annulla":
            self.dismiss(None)

    def action_annulla(self) -> None:
        self.dismiss(None)
