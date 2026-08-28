import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

log = logging.getLogger(__name__)

_RELEASES_LATEST_URL = "https://api.github.com/repos/staffDiUnisa/CartellinoUniSA/releases/latest"
_TIMEOUT_SECONDS = 5


@dataclass
class ReleaseInfo:
    version: str
    html_url: str
    body: str


def _parse_version(version: str) -> tuple[int, ...] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", version.strip())
    if not match:
        return None
    return tuple(int(g) for g in match.groups())


def check_for_update(current_version: str) -> ReleaseInfo | None:
    """Confronta `current_version` (`_app_version()`, `cartellino/tui/app.py`) con l'ultima
    release pubblicata su GitHub (non-draft, non-prerelease). Ritorna `None` se non c'è una
    versione più recente, se `current_version` non è nel formato `X.Y.Z` (es. `"dev"` in
    ambiente non "frozen"), o in caso di qualunque errore di rete/parsing — il chiamante decide
    se e come segnalarlo (silenzioso in avvio, esplicito on-demand)."""
    current = _parse_version(current_version)
    if current is None:
        return None

    request = urllib.request.Request(
        _RELEASES_LATEST_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "cartellino-unisa",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            data = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        log.warning(f"Controllo aggiornamenti fallito: {e}")
        return None

    latest = _parse_version(data.get("tag_name", ""))
    if latest is None or latest <= current:
        return None

    return ReleaseInfo(
        version=".".join(str(p) for p in latest),
        html_url=data.get("html_url", ""),
        body=data.get("body") or "",
    )
