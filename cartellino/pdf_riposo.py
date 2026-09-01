"""Compilazione del PDF AcroForm di richiesta riposo compensativo (issue #7, vedi
TODO_riposo_richiesto.md Fase 3).

Il template viene caricato una tantum dall'utente in Impostazioni (Fase 4), già
pre-personalizzato con i propri dati anagrafici dalla propria area UNISA: qui viene
compilato solo con i dati del riposo compensativo da richiedere. Campi attesi nel
template (AcroForm): `giorni`, `dalle`, `alle`, `giorno`, `giorno1`..`giorno8`,
`ore1`..`ore8`, `totaleOre`, `data`, `dal`, `al`.
"""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from model.riposo_compensativo import RiposoCompensativo

log = logging.getLogger(__name__)

_MAX_GIORNI_CONTRIBUENTI = 8


class RiposoPdfError(Exception):
    """Errore nella compilazione del PDF di richiesta riposo compensativo."""


def _formatta_ore(ore: timedelta) -> str:
    totale_minuti = int(ore.total_seconds() // 60)
    h, m = divmod(totale_minuti, 60)
    return f"{h:02}:{m:02}"


def genera_pdf_richiesta(
    template_path: Path,
    riposo: RiposoCompensativo,
    data_richiesta: str,
    current_year: int,
    output_folder: Path,
) -> Path:
    """Compila il template AcroForm coi dati di `riposo` per la richiesta d'uso alla
    data `data_richiesta` (formato DD-MM-YYYY) e salva il PDF compilato in
    `output_folder`. Solleva `RiposoPdfError` se il template non esiste, non ha i
    campi attesi, o il riposo ha più di 8 giornate contribuenti (limite del
    template)."""
    from cartellino.cartellino import Cartellino

    if not template_path.exists():
        raise RiposoPdfError(f"Template PDF non trovato: '{template_path}'")

    if len(riposo.ore_inserite) > _MAX_GIORNI_CONTRIBUENTI:
        raise RiposoPdfError(
            f"Il riposo compensativo {riposo.id} ha {len(riposo.ore_inserite)} giornate "
            f"contribuenti, ma il template supporta al massimo {_MAX_GIORNI_CONTRIBUENTI}."
        )

    try:
        reader = PdfReader(template_path)
    except Exception as e:
        raise RiposoPdfError(f"Impossibile leggere il template PDF '{template_path}': {e}") from e

    campi_template = reader.get_fields()
    if not campi_template:
        raise RiposoPdfError(f"Il template PDF '{template_path}' non contiene campi compilabili.")

    campi_attesi = {"giorni", "dalle", "alle", "giorno", "totaleOre", "data", "dal", "al"}
    campi_attesi.update(f"giorno{i}" for i in range(1, _MAX_GIORNI_CONTRIBUENTI + 1))
    campi_attesi.update(f"ore{i}" for i in range(1, _MAX_GIORNI_CONTRIBUENTI + 1))
    campi_mancanti = campi_attesi - set(campi_template.keys())
    if campi_mancanti:
        raise RiposoPdfError(
            f"Il template PDF '{template_path}' non ha i campi attesi: "
            f"{', '.join(sorted(campi_mancanti))}."
        )

    try:
        data_richiesta_dt = datetime.strptime(data_richiesta, "%d-%m-%Y")
    except ValueError as e:
        raise RiposoPdfError(f"Data richiesta non valida: '{data_richiesta}'") from e

    ore_formattate = _formatta_ore(riposo.ore_necessarie)
    valori: dict[str, str] = {
        # Nonostante il nome, nel template reale "giorni" è il numero (ore, non
        # giorni) di "di poter usufrire di n. ___ ore di riposo compensativo" —
        # stesso valore di "totaleOre" sotto.
        "giorni": ore_formattate,
        # "dal"/"al" restano vuoti: nel template reale sono gli stessi campi che
        # compaiono anche sotto "ATTESTAZIONE DI AVVENUTA CONSEGNA" (sezione
        # compilata dall'amministrazione, non dal richiedente) — compilarli
        # qui li precompilerebbe anche lì. La data della richiesta resta
        # comunque indicata dal campo "giorno" sotto.
        "dal": "",
        "al": "",
        "dalle": "",
        "alle": "",
        "giorno": data_richiesta_dt.strftime("%d/%m/%Y"),
        "data": date.today().strftime("%d/%m/%Y"),
        "totaleOre": ore_formattate,
    }
    for i in range(1, _MAX_GIORNI_CONTRIBUENTI + 1):
        valori[f"giorno{i}"] = ""
        valori[f"ore{i}"] = ""
    for i, ore in enumerate(riposo.ore_inserite, start=1):
        giorno_dt = Cartellino.get_date_from_string(ore.data, current_year)
        valori[f"giorno{i}"] = giorno_dt.strftime("%d/%m/%Y")
        valori[f"ore{i}"] = _formatta_ore(ore.ore)

    writer = PdfWriter()
    writer.append(reader)
    for page in writer.pages:
        writer.update_page_form_field_values(page, valori)

    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / f"richiesta_riposo_{riposo.id}_{data_richiesta_dt.strftime('%Y%m%d')}.pdf"
    with open(output_path, "wb") as fh:
        writer.write(fh)

    log.info(f"PDF richiesta riposo compensativo {riposo.id} generato in '{output_path}'")
    return output_path
