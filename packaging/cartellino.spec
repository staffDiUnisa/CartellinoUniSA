# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec per l'eseguibile standalone della TUI (Fase 6 TODO.md).

Uso: `uv run pyinstaller packaging/cartellino.spec` dalla root del repo (o via
`mise run build`). Produce una cartella "onedir" (`dist/cartellino-unisa/`) con
l'eseguibile (`cartellino-unisa[.exe]`) e tutte le librerie di supporto accanto:
Chrome resta comunque una dipendenza esterna obbligatoria (Selenium non è
imbottigliabile).

**Perché onedir e non onefile**: la prima versione di questo spec usava un
eseguibile "onefile" (tutto in un unico file). Su macOS questo si è rivelato
rotto: `pyarrow` (che pandas usa per `pd.read_feather`) falliva con
`ImportError: Import pyarrow failed` sul binario scaricato dalla Release, pur
funzionando su una build fatta ed eseguita in locale sulla stessa macchina.
Causa nota di PyInstaller su macOS (soprattutto Apple Silicon): in modalità
onefile le librerie native vengono estratte in una cartella temporanea *a
runtime*, non firmate — macOS può rifiutarsi di caricarle, specialmente per un
binario scaricato da browser (attributo di quarantena). In modalità onedir le
librerie stanno accanto all'eseguibile fin dal momento della build, senza
un'estrazione runtime in una nuova cartella temporanea ad ogni avvio.

Note sui dati bundled:
- `cartellino/tui/app.tcss`: il CSS della TUI. `CartellinoApp` (cartellino/tui/app.py)
  imposta `_BASE_PATH` in base a `sys._MEIPASS` quando "frozen", così Textual lo
  ritrova allo stesso percorso relativo usato qui (altrimenti userebbe
  `inspect.getfile(CartellinoApp)`, che non punta a un file reale una volta
  impacchettato: il modulo vive nell'archivio PYZ, non su disco).
- `pyproject.toml`: letto da `cartellino/tui/app.py::_app_version()` per mostrare
  la versione in header (il progetto ha `tool.uv.package = false`, quindi non è
  installato come pacchetto e `importlib.metadata.version()` non funzionerebbe).

Hidden imports non dichiarati esplicitamente: `keyring` (backend OS-specifici) e
`pyarrow` hanno già hook PyInstaller propri (rispettivamente in `PyInstaller.hooks`
e `_pyinstaller_hooks_contrib`) che raccolgono automaticamente submodule/metadata/
data file necessari. Il hook di `selenium` (`_pyinstaller_hooks_contrib`) raccoglie
solo i data file, non i submodule dei singoli browser: `selenium/webdriver/__init__.py`
espone `webdriver.Chrome` con un meccanismo che l'analisi statica di PyInstaller non
segue (riscontrato in produzione: `ModuleNotFoundError: No module named
'selenium.webdriver.chrome.webdriver'` all'avvio del download nel binario
impacchettato), quindi vanno dichiarati esplicitamente qui sotto.

Stesso identico problema per `textual.widgets`: nessun hook PyInstaller esiste per
`textual` (né in `_pyinstaller_hooks_contrib` né bundled col pacchetto stesso).
`textual/widgets/__init__.py` espone le classi widget (es. `MarkdownViewer`) tramite
un `__getattr__` a livello di modulo (PEP 562, lazy loading per ridurre lo startup
time) che fa `import_module(f"._{camel_to_snake(nome_classe)}", package="textual.widgets")`
— invisibile all'analisi statica di PyInstaller esattamente come per `selenium`.
La maggior parte dei widget già usati nella TUI (`DataTable`, `Select`, `Switch`,
`MaskedInput`, `RichLog`, `DirectoryTree`, ecc.) risultano comunque raggiungibili
per qualche altro percorso di import (interno a Textual stesso) e non hanno mai
richiesto una dichiarazione esplicita — ma `MarkdownViewer` (introdotto per la vista
"Riposo compensativo" in Statistiche) no: riscontrato in produzione
`ModuleNotFoundError: No module named 'textual.widgets._markdown_viewer'`
all'apertura della schermata Statistiche nel binario impacchettato. Qualunque nuovo
widget Textual introdotto in futuro va verificato allo stesso modo (build reale +
uso della schermata che lo usa) prima di assumere che funzioni nel binario
impacchettato solo perché funziona in `uv run`.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 (SPECPATH è iniettato da PyInstaller)

# Icona dell'eseguibile: solo su Windows (`icon=` di EXE() imposta l'icona
# della risorsa nel .exe; su macOS servirebbe un vero bundle .app tramite
# BUNDLE(), che questo spec non produce — l'icona del launcher .app viene
# invece impostata a parte nel workflow di release). Generata da
# packaging/generate_icons.py (packaging/build/icon.ico, gitignored),
# eseguito come step separato prima della build in CI.
_icon_ico = REPO_ROOT / "packaging" / "build" / "icon.ico"
icon = str(_icon_ico) if sys.platform == "win32" and _icon_ico.exists() else None

datas = [
    (str(REPO_ROOT / "cartellino" / "tui" / "app.tcss"), "cartellino/tui"),
    (str(REPO_ROOT / "pyproject.toml"), "."),
]

hiddenimports = [
    "selenium.webdriver.chrome.webdriver",
    "selenium.webdriver.chrome.options",
    "selenium.webdriver.chrome.service",
    "textual.widgets._markdown",
    "textual.widgets._markdown_viewer",
]

a = Analysis(  # noqa: F821
    [str(REPO_ROOT / "cartellino_tui.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cartellino-unisa",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="cartellino-unisa",
)
