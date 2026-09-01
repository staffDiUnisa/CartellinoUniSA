"""Stato persistito e matching FIFO delle richieste di riposo compensativo (issue #7,
vedi TODO_riposo_richiesto.md Fase 2).

Introduce lo stato intermedio "richiesto per <data>" tra "completo non ancora usato" e
"usato" (quest'ultimo resta gestito da `riposi_usati.txt`/`SRC`, non toccato qui):
`applica_richieste` assegna `RiposoCompensativo.data_richiesta` in ordine FIFO ai riposi
completi (`ore_mancanti() == timedelta(0)`) che non hanno ancora né `data` né
`data_richiesta`, secondo l'uso rigorosamente sequenziale deciso con l'utente (nessun
selettore: si può richiedere solo il *prossimo* disponibile).
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from model.riposo_compensativo import RiposoCompensativo

log = logging.getLogger(__name__)

_SEPARATORE = "|"


@dataclass
class RichiestaRiposo:
    data_richiesta: str
    """Data per cui è stato richiesto il riposo, formato DD-MM-YYYY (stesso formato di
    `date_escluse.txt`/`data_ticket.txt`)."""
    pdf_path: str
    """Percorso del PDF di richiesta generato (`genera_pdf_richiesta`, Fase 3)."""


def carica_richieste(path: Path) -> list[RichiestaRiposo]:
    if not path.exists():
        return []
    richieste = []
    with open(path, "r") as fh:
        for riga in fh:
            riga = riga.strip()
            if not riga:
                continue
            data_richiesta, pdf_path = riga.split(_SEPARATORE, 1)
            richieste.append(RichiestaRiposo(data_richiesta=data_richiesta, pdf_path=pdf_path))
    return richieste


def salva_richieste(path: Path, richieste: list[RichiestaRiposo]) -> None:
    contenuto = "\n".join(f"{r.data_richiesta}{_SEPARATORE}{r.pdf_path}" for r in richieste)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contenuto + ("\n" if contenuto else ""))


def applica_richieste(
    riposi: list[RiposoCompensativo], richieste: list[RichiestaRiposo]
) -> list[RiposoCompensativo]:
    """Secondo passaggio dopo `OreEccedenti.raggruppa()`: assegna `.data_richiesta` in
    ordine FIFO ai riposi completi non ancora usati (`data is None`). Non modifica i
    riposi in-place (coerente con `RiposoCompensativo` essendo un `BaseModel`)."""
    code_richieste = list(richieste)
    risultato = []
    for riposo in riposi:
        if code_richieste and riposo.data is None and riposo.ore_mancanti() <= timedelta(0):
            richiesta = code_richieste.pop(0)
            riposo = riposo.model_copy(update={"data_richiesta": richiesta.data_richiesta})
        risultato.append(riposo)
    return risultato


def prossimo_riposo_disponibile(riposi: list[RiposoCompensativo]) -> RiposoCompensativo | None:
    """Il prossimo riposo compensativo completo, non ancora usato né richiesto — l'unico
    richiedibile, secondo l'uso rigorosamente sequenziale deciso con l'utente."""
    for riposo in riposi:
        if (
            riposo.data is None
            and riposo.data_richiesta is None
            and riposo.ore_mancanti() <= timedelta(0)
        ):
            return riposo
    return None


def annulla_richiesta_da(path: Path, indice: int) -> None:
    """Tronca la lista delle richieste pendenti da `indice` (incluso) in poi ed elimina i
    PDF già generati per le richieste troncate — annullare una richiesta annulla anche
    tutte quelle successive già in coda (decisione confermata con l'utente)."""
    richieste = carica_richieste(path)
    if indice < 0 or indice >= len(richieste):
        return
    troncate = richieste[indice:]
    for richiesta in troncate:
        pdf_path = Path(richiesta.pdf_path)
        try:
            pdf_path.unlink(missing_ok=True)
        except OSError as e:
            log.warning(f"Impossibile eliminare il PDF '{pdf_path}': {e}")
    salva_richieste(path, richieste[:indice])
