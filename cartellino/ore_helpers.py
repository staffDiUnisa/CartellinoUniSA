import re

import pandas as pd

_ORE_RE = re.compile(r'\d\d\.')
_MINUTI_RE = re.compile(r'\.\d\d')


def estrai_ore_minuti(voci_base: str) -> tuple[int, int]:
    """Estrae (ore, minuti) dal pattern numerico `HH.MM` di una voce base
    (es. "02.30" -> (2, 30)). Usato per OE-DIU, e riusabile per qualsiasi altro
    codice con lo stesso formato (es. SCN, CRE)."""
    ore = int(_ORE_RE.search(voci_base).group()[:-1])
    minuti = int(_MINUTI_RE.search(voci_base).group()[1:])
    return ore, minuti


def somma_ore_per_codici(df: pd.DataFrame, codici: list[str]) -> pd.DataFrame:
    """Filtra il cartellino sui `codici` indicati ed estrae ore/minuti dalla
    colonna "Voci Base" con lo stesso pattern regex di `estrai_ore_minuti`.

    `df` è il DataFrame grezzo di `Cartellino` (con colonna "Codice" già
    calcolata). Non marca i codici come "usati": chi chiama e vuole tracciarli
    deve passare per `Cartellino._filter`/le property dedicate.
    """
    filtrato = df[df["Codice"].isin(codici)].copy()
    ore_minuti = filtrato["Voci Base"].apply(estrai_ore_minuti)
    filtrato["ore"] = ore_minuti.apply(lambda x: x[0])
    filtrato["minuti"] = ore_minuti.apply(lambda x: x[1])
    return filtrato


# Codici il cui valore va sottratto (non sommato) nel calcolo di un saldo —
# oggi solo SCN, uno scostamento negativo (issue GitHub #8: es. base +00:07,
# SCN 00:26 -> saldo corretto -00:19). Hardcoded volutamente invece di un
# meccanismo di configurazione generico: è un fatto noto sul sistema di
# rilevazione presenze, non una preferenza dell'utente, e ad oggi ha un solo
# membro noto. Se in futuro emergessero altri codici con la stessa semantica,
# aggiungerli qui; se l'insieme crescesse oltre 1-2 elementi, valutare di
# spostarlo in configurazione.
SUBTRACTIVE_CODES = {"SCN"}


def calcola_saldo_minuti(df: pd.DataFrame, codici: list[str]) -> int:
    """Somma con segno, in minuti, le ore/minuti dei `codici` indicati nel
    DataFrame già filtrato (es. per mese/anno). I codici in
    `SUBTRACTIVE_CODES` vengono sottratti anziché sommati."""
    filtrato = somma_ore_per_codici(df, codici)
    segno = filtrato["Codice"].apply(lambda c: -1 if c in SUBTRACTIVE_CODES else 1)
    return int((segno * (filtrato["ore"] * 60 + filtrato["minuti"])).sum())
