# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec per l'eseguibile standalone della TUI (Fase 6 TODO.md).

Uso: `uv run pyinstaller packaging/cartellino.spec` dalla root del repo (o via
`mise run build`). Produce un eseguibile "onefile" (`dist/cartellino-unisa[.exe]`)
che bundla Python + tutte le dipendenze: Chrome resta comunque una dipendenza
esterna obbligatoria (Selenium non è imbottigliabile).

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
data file necessari; stesso discorso per `selenium` (raccoglie i suoi data file).
"""

from pathlib import Path

REPO_ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 (SPECPATH è iniettato da PyInstaller)

datas = [
    (str(REPO_ROOT / "cartellino" / "tui" / "app.tcss"), "cartellino/tui"),
    (str(REPO_ROOT / "pyproject.toml"), "."),
]

a = Analysis(  # noqa: F821
    [str(REPO_ROOT / "cartellino_tui.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name="cartellino-unisa",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
