import typer

from typing_extensions import Annotated

app = typer.Typer(help="Esegue lo script per l'estrazione dei dati dal cartellino.\n"
                       "Se aggiorna_cartellino non è impostato, salterà il processo di aggiornamento "
                       "i dati da https://presenze.unisa.it.")

@app.command()
def main(aggiorna_cartellino: Annotated[
        bool,
        typer.Option(prompt="Vuoi aggiornare i dati del cartellino (L'aggiornamento funziona solo dalla rete "
                            "universitaria.)?",
                     help="Aggiorna i dati da https://presenze.unisa.it. Di default usa solo i dati già scaricati in "
                          "data/input/cartellino.xlsx.")]
         = False) -> None:


    from process import run as processa
    from get import run as get_data

    if aggiorna_cartellino:
        get_data()

    processa()

if __name__ == "__main__":
    print("Esegue lo script per l'estrazione dei dati dal cartellino.\n"
          "Se scegli di non aggiornare i dati, salterà il processo di aggiornamento "
          "i dati da https://presenze.unisa.it.")
    app()