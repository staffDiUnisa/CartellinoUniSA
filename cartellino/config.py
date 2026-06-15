import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    current_year: int
    min_date: datetime | None
    data_folder: Path
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

    @classmethod
    def from_env(cls, data_folder: Path = Path("data")) -> "Config":
        current_year = int(os.getenv("CURRENT_YEAR"))
        min_date_str = os.getenv("MIN_DATE_RIPOSI_USATI")
        try:
            min_date = datetime.strptime(f"{current_year}-{min_date_str}", "%Y-%m-%d")
            print(f"Data da cui verranno considerati i Riposi Compensativi Usati: {min_date.strftime('%d-%m-%Y')}")
        except (ValueError, TypeError):
            print(
                "Errore nel processare MIN_DATE_RIPOSI_USATI. "
                "Userò il file dei riposi usati, se disponibile."
            )
            min_date = None
        return cls(current_year=current_year, min_date=min_date, data_folder=data_folder)
