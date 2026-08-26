import logging
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

logging.basicConfig(level=logging.INFO, format="%(message)s")

DATA_FOLDER = Path("data/v2")
TIMESHEET_FOLDER = Path("timesheet")

_AUTH_METHOD_MAP = {"unisa": "Credenziali UNISA", "spid": "SPID", "cie": "CIE"}
_EXPORT_FORMATS = ("xlsx", "csv")

app = typer.Typer(
    help="Versione OO dello script per l'estrazione dei dati dal cartellino.\n"
         "Se aggiorna_cartellino non è impostato, salterà il processo di aggiornamento "
         "i dati da https://presenze.unisa.it."
)


@app.command()
def main(
    aggiorna_cartellino: Annotated[
        bool,
        typer.Option(
            prompt="Vuoi aggiornare i dati del cartellino (L'aggiornamento funziona solo dalla rete universitaria.)?",
            help="Aggiorna i dati da https://presenze.unisa.it. Di default usa solo i dati già scaricati in data/v2/input/cartellino.xlsx.",
        ),
    ] = False,
    timesheet_progetto: Annotated[
        Optional[str],
        typer.Option(
            "--timesheet-progetto",
            help=(
                "Nome (o percorso) del file YAML di configurazione per il timesheet di progetto. "
                "Se viene fornito solo il nome del file (es. 'mio_progetto.yaml'), "
                "viene cercato automaticamente nella cartella timesheet/. "
                "Genera i fogli mensili in data/v2/{anno}/output/ore_svolte_per_giorno/{nome_progetto}/. "
                "Usa templates/timesheet_progetto_template.yaml come punto di partenza."
            ),
        ),
    ] = None,
    auth_method: Annotated[
        Optional[str],
        typer.Option(
            "--auth-method",
            help=(
                "Metodo di autenticazione per il download (unisa, spid, cie). Se omesso e "
                "--aggiorna-cartellino è attivo, viene chiesto interattivamente a schermo."
            ),
        ),
    ] = None,
    export_format: Annotated[
        Optional[str],
        typer.Option(
            "--export-format",
            help=(
                "Formato di export dei report (xlsx o csv). Se omesso usa quello configurato "
                "in config.toml/Impostazioni TUI (default xlsx)."
            ),
        ),
    ] = None,
) -> None:
    if aggiorna_cartellino:
        metodo = None
        if auth_method is not None:
            metodo = _AUTH_METHOD_MAP.get(auth_method.lower())
            if metodo is None:
                raise typer.BadParameter(
                    f"Valore non valido: '{auth_method}'. Scegli tra: {', '.join(_AUTH_METHOD_MAP)}.",
                    param_hint="--auth-method",
                )
        from get import ottieni_cartellino
        ottieni_cartellino(DATA_FOLDER, metodo=metodo)

    from cartellino import CartellinoProcessor
    processor = CartellinoProcessor.from_env(data_folder=DATA_FOLDER)
    if export_format is not None:
        if export_format not in _EXPORT_FORMATS:
            raise typer.BadParameter(
                f"Valore non valido: '{export_format}'. Scegli tra: {', '.join(_EXPORT_FORMATS)}.",
                param_hint="--export-format",
            )
        processor.config.export_format = export_format
    processor.run()

    if timesheet_progetto is not None:
        from cartellino.timesheet_runner import esegui_timesheet_progetto, risolvi_percorso_timesheet

        try:
            ts_path = risolvi_percorso_timesheet(timesheet_progetto, TIMESHEET_FOLDER)
        except FileNotFoundError as e:
            raise typer.BadParameter(str(e), param_hint="--timesheet-progetto")

        esegui_timesheet_progetto(processor.config, ts_path)


if __name__ == "__main__":
    print(
        "Esegue lo script per l'estrazione dei dati dal cartellino.\n"
        "Se scegli di non aggiornare i dati, salterà il processo di aggiornamento "
        "i dati da https://presenze.unisa.it."
    )
    app()
