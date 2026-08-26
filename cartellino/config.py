import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from cartellino.user_config import (
    DEFAULT_DASHBOARD_BALANCE_CODES,
    DEFAULT_DASHBOARD_EXCEPTION_CODES,
    UserConfig,
    migrate_from_env_if_needed,
)

load_dotenv()

log = logging.getLogger(__name__)


@dataclass
class Config:
    current_year: int
    min_date: datetime | None
    data_folder: Path
    headless: bool = False
    export_format: str = "xlsx"
    dashboard_exception_codes: list[str] = field(
        default_factory=lambda: list(DEFAULT_DASHBOARD_EXCEPTION_CODES)
    )
    dashboard_balance_codes: list[str] = field(
        default_factory=lambda: list(DEFAULT_DASHBOARD_BALANCE_CODES)
    )
    input_folder: Path = field(init=False)
    output_folder: Path = field(init=False)
    excluded_dates_file: Path = field(init=False)
    riposi_usati_file: Path = field(init=False)

    def __post_init__(self) -> None:
        self.input_folder = self.data_folder / str(self.current_year) / "input"
        self.output_folder = self.data_folder / str(self.current_year) / "output"
        self.excluded_dates_file = self.input_folder / "date_escluse.txt"
        self.riposi_usati_file = self.input_folder / "riposi_usati.txt"

        self.input_folder.mkdir(parents=True, exist_ok=True)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse_min_date(current_year: int, min_date_str: str | None) -> datetime | None:
        try:
            min_date = datetime.strptime(f"{current_year}-{min_date_str}", "%Y-%m-%d")
            log.info(f"Data da cui verranno considerati i Riposi Compensativi Usati: {min_date.strftime('%d-%m-%Y')}")
            return min_date
        except (ValueError, TypeError):
            log.warning(
                "Errore nel processare MIN_DATE_RIPOSI_USATI. "
                "Userò il file dei riposi usati, se disponibile."
            )
            return None

    @classmethod
    def from_env(cls, data_folder: Path = Path("data")) -> "Config":
        current_year = int(os.getenv("CURRENT_YEAR"))
        min_date = cls._parse_min_date(current_year, os.getenv("MIN_DATE_RIPOSI_USATI"))
        return cls(
            current_year=current_year,
            min_date=min_date,
            data_folder=data_folder,
            headless=os.getenv("HEADLESS") == "True",
        )

    @classmethod
    def load(cls, data_folder: Path = Path("data")) -> "Config":
        """Legge la configurazione da `config.toml` (keyring/platformdirs, Fase 2 TODO.md).

        Se `config.toml` non esiste ancora ma è presente un `.env` legacy, esegue
        la migrazione automatica one-shot (`migrate_from_env_if_needed`) prima di
        procedere. In assenza sia di `config.toml` che di `.env` valido, ricade su
        `from_env` per compatibilità con ambienti che impostano le variabili
        direttamente (es. CI).
        """
        user_config = UserConfig.load() or migrate_from_env_if_needed()
        if user_config is None:
            return cls.from_env(data_folder=data_folder)

        min_date = cls._parse_min_date(user_config.current_year, user_config.min_date_riposi_usati)
        return cls(
            current_year=user_config.current_year,
            min_date=min_date,
            data_folder=data_folder,
            headless=user_config.headless,
            export_format=user_config.export_format,
            dashboard_exception_codes=list(user_config.dashboard_exception_codes),
            dashboard_balance_codes=list(user_config.dashboard_balance_codes),
        )
