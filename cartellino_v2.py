from pathlib import Path

import typer
from typing_extensions import Annotated

DATA_FOLDER = Path("data/v2")

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
) -> None:
    if aggiorna_cartellino:
        from get import ottieni_cartellino
        ottieni_cartellino(DATA_FOLDER)

    from cartellino import CartellinoProcessor
    CartellinoProcessor.from_env(data_folder=DATA_FOLDER).run()


if __name__ == "__main__":
    print(
        "Esegue lo script per l'estrazione dei dati dal cartellino.\n"
        "Se scegli di non aggiornare i dati, salterà il processo di aggiornamento "
        "i dati da https://presenze.unisa.it."
    )
    app()
