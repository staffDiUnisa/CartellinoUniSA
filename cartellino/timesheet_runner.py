from pathlib import Path

from cartellino.cartellino import Cartellino
from cartellino.config import Config
from cartellino.timesheet_progetto import ConfigTimesheet, TimesheetProgetto


def esegui_timesheet_progetto(config: Config, ts_path: Path) -> ConfigTimesheet:
    """Genera il timesheet mensile di progetto (e il rendiconto Excel, se configurato)
    a partire da uno YAML `ts_path` (vedi `templates/timesheet_progetto_template.yaml`).

    Condivisa da `cartellino_v2.py` (CLI) e dalla TUI così le due interfacce non
    duplicano la stessa sequenza di chiamate.
    """
    cartellino = Cartellino.from_config(config)
    ts_config = ConfigTimesheet.from_yaml(ts_path)
    ts = TimesheetProgetto(
        oo_diu=cartellino.oo_diu,
        config=ts_config,
        output_folder=config.output_folder,
    )
    ts.salva()

    if ts_config.template_rendiconto is not None:
        from cartellino.rendiconto_excel import RendicontoExcel
        RendicontoExcel(
            config=ts_config,
            monthly_data=ts.calcola(),
            output_folder=config.output_folder,
        ).genera()

    return ts_config


def risolvi_percorso_timesheet(nome_o_percorso: str, timesheet_folder: Path) -> Path:
    """Risolve `--timesheet-progetto`/selezione TUI: percorso assoluto/esistente così
    com'è, altrimenti cercato dentro `timesheet_folder` (comportamento storico di
    `cartellino_v2.py`)."""
    ts_path = Path(nome_o_percorso)
    if not ts_path.is_absolute() and not ts_path.exists():
        ts_path = timesheet_folder / ts_path
    if not ts_path.exists():
        raise FileNotFoundError(
            f"File non trovato: '{nome_o_percorso}' (cercato anche in '{timesheet_folder / nome_o_percorso}')"
        )
    return ts_path
