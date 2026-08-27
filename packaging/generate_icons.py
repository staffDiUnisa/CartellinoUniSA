"""Genera packaging/build/icon.ico da resources/logo.png.

Usato dal workflow di release (packaging/cartellino.spec, EXE su Windows) per
impostare l'icona dell'eseguibile/installer Windows. L'equivalente macOS
(.icns per il launcher .app) è generato a parte nel workflow stesso con i
tool nativi sips/iconutil, non serviti da questo script.

Uso: `uv run python packaging/generate_icons.py` dalla root del repo.
"""

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "resources" / "logo.png"
OUTPUT = REPO_ROOT / "packaging" / "build" / "icon.ico"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE) as img:
        img.convert("RGBA").save(
            OUTPUT, sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)]
        )


if __name__ == "__main__":
    main()
