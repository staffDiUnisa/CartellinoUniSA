import logging
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

import platformdirs
import tomli_w

log = logging.getLogger(__name__)

_APP_NAME = "cartellino-unisa"
_CONFIG_FILENAME = "config.toml"

DEFAULT_DASHBOARD_EXCEPTION_CODES = ["ERIT", "SCN"]
DEFAULT_DASHBOARD_BALANCE_CODES = ["CRE", "OE-DIU", "SCN"]


def config_file_path() -> Path:
    return Path(platformdirs.user_config_dir(_APP_NAME)) / _CONFIG_FILENAME


@dataclass
class UserConfig:
    current_year: int
    min_date_riposi_usati: str | None = None
    headless: bool = False
    export_format: str = "xlsx"
    dashboard_exception_codes: list[str] = field(
        default_factory=lambda: list(DEFAULT_DASHBOARD_EXCEPTION_CODES)
    )
    dashboard_balance_codes: list[str] = field(
        default_factory=lambda: list(DEFAULT_DASHBOARD_BALANCE_CODES)
    )

    @classmethod
    def load(cls, path: Path | None = None) -> "UserConfig | None":
        path = path or config_file_path()
        if not path.exists():
            return None
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
        return cls(
            current_year=data["current_year"],
            min_date_riposi_usati=data.get("min_date_riposi_usati"),
            headless=data.get("headless", False),
            export_format=data.get("export_format", "xlsx"),
            dashboard_exception_codes=data.get(
                "dashboard_exception_codes", list(DEFAULT_DASHBOARD_EXCEPTION_CODES)
            ),
            dashboard_balance_codes=data.get(
                "dashboard_balance_codes", list(DEFAULT_DASHBOARD_BALANCE_CODES)
            ),
        )

    def save(self, path: Path | None = None) -> None:
        path = path or config_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            tomli_w.dump(asdict(self), fh)


def migrate_from_env_if_needed(env_file: Path = Path(".env")) -> UserConfig | None:
    """Migrazione one-shot da `.env` legacy a `config.toml` + keyring.

    Non fa nulla se esiste già un `config.toml`, o se non c'è un `.env` con i
    valori necessari. Va invocata prima di ogni lettura di configurazione
    (vedi `Config.load`), così da coprire sia CLI che (in futuro) TUI.
    """
    if config_file_path().exists():
        return None
    if not env_file.exists():
        return None

    from dotenv import dotenv_values
    values = dotenv_values(env_file)
    current_year = values.get("CURRENT_YEAR")
    if not current_year:
        return None

    user_config = UserConfig(
        current_year=int(current_year),
        min_date_riposi_usati=values.get("MIN_DATE_RIPOSI_USATI"),
        headless=values.get("HEADLESS") == "True",
    )
    user_config.save()

    username = values.get("USERNAME")
    password = values.get("PASSWORD")
    if username and password:
        from cartellino.credentials import set_credentials
        set_credentials(username, password)

    log.info(
        f"Migrazione automatica da '.env' completata: configurazione salvata in "
        f"'{config_file_path()}'"
        + (" e credenziali salvate nel keyring di sistema." if username and password else ".")
        + f" Puoi eliminare il file '{env_file}' in sicurezza."
    )
    return user_config
