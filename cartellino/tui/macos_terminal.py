from pathlib import Path

import platformdirs

_FILENAME = "macos_terminal.txt"

TERMINAL_CHOICES: list[tuple[str, str]] = [
    ("Terminale", "com.apple.Terminal"),
    ("Ghostty", "com.mitchellh.ghostty"),
    ("iTerm2", "com.googlecode.iterm2"),
]
"""Tuple (etichetta, bundle id): l'ordine segue la convenzione di
`textual.widgets.Select`, che si aspetta `(RenderableType, SelectType)` — la
prima posizione è ciò che viene mostrato, la seconda è il valore vero e
proprio confrontato con `value=`."""


def terminal_choice_file() -> Path:
    """File di stato separato da `config.toml`/`UserConfig`: il picker del terminale in
    `packaging/macos/launcher.applescript` gira prima di qualunque cosa Python (quindi prima
    dell'onboarding, quando `UserConfig` non è costruibile perché `current_year` è
    obbligatorio). Stessa cartella di `config.toml` per scoperta/coerenza, ma file distinto,
    letto/scritto anche in AppleScript senza bisogno di parsing TOML."""
    return Path(platformdirs.user_config_dir("cartellino-unisa")) / _FILENAME


def load_terminal_bundle_id() -> str | None:
    path = terminal_choice_file()
    if not path.exists():
        return None
    return path.read_text().strip() or None


def save_terminal_bundle_id(bundle_id: str) -> None:
    path = terminal_choice_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bundle_id + "\n")


def installed_terminal_choices() -> list[tuple[str, str]]:
    """Sottoinsieme di `TERMINAL_CHOICES` effettivamente installato (Terminale sempre incluso,
    è l'app di sistema)."""
    app_paths = {
        "com.mitchellh.ghostty": Path("/Applications/Ghostty.app"),
        "com.googlecode.iterm2": Path("/Applications/iTerm.app"),
    }
    return [
        (label, bundle_id)
        for label, bundle_id in TERMINAL_CHOICES
        if bundle_id not in app_paths or app_paths[bundle_id].exists()
    ]
