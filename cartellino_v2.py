from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

DATA_FOLDER = Path("data/v2")
TIMESHEET_FOLDER = Path("timesheet")

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
) -> None:
    if aggiorna_cartellino:
        from get import ottieni_cartellino
        ottieni_cartellino(DATA_FOLDER)

    from cartellino import CartellinoProcessor
    processor = CartellinoProcessor.from_env(data_folder=DATA_FOLDER)
    processor.run()

    if timesheet_progetto is not None:
        from cartellino.cartellino import Cartellino
        from cartellino.timesheet_progetto import ConfigTimesheet, TimesheetProgetto

        ts_path = Path(timesheet_progetto)
        if not ts_path.is_absolute() and not ts_path.exists():
            ts_path = TIMESHEET_FOLDER / ts_path
        if not ts_path.exists():
            raise typer.BadParameter(
                f"File non trovato: '{timesheet_progetto}' "
                f"(cercato anche in '{TIMESHEET_FOLDER / timesheet_progetto}')",
                param_hint="--timesheet-progetto",
            )

        cfg = processor.config
        cartellino = Cartellino.from_config(cfg)
        ts_config = ConfigTimesheet.from_yaml(ts_path)
        ts = TimesheetProgetto(
            oo_diu=cartellino.oo_diu,
            config=ts_config,
            output_folder=cfg.output_folder,
        )
        ts.salva()

        if ts_config.template_rendiconto is not None:
            from cartellino.rendiconto_excel import RendicontoExcel
            RendicontoExcel(
                config=ts_config,
                monthly_data=ts.calcola(),
                output_folder=cfg.output_folder,
            ).genera()


if __name__ == "__main__":
    print(
        "Esegue lo script per l'estrazione dei dati dal cartellino.\n"
        "Se scegli di non aggiornare i dati, salterà il processo di aggiornamento "
        "i dati da https://presenze.unisa.it."
    )
    app()
