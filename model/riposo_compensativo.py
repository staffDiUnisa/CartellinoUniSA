from typing import Annotated
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from model.ore_inserite import OreInserite


class RiposoCompensativo(BaseModel):
    id : Annotated[int, Field(description="ID del riposo compensativo")]
    data : Annotated[str, Field(description="Data del riposo compensativo in formato YYYY-MM-DD", default=None)]
    data_richiesta : Annotated[str | None, Field(description="Data per cui è stato richiesto il riposo compensativo (PDF già compilato, non ancora confermato/usato)", default=None)]
    ore_necessarie : Annotated[timedelta, Field(description="Ore necessarie per il riposo compensativo", default=timedelta(hours=7, minutes=12))]
    ore_inserite: list[OreInserite] = Field(default_factory=list, description="Ore inserite per il riposo compensativo")

    def ore_mancanti(self) -> timedelta:
        """
        Calcola le ore mancanti per il riposo compensativo.
        """
        if len(self.ore_inserite) == 0:
            return self.ore_necessarie

        ore_inserite_totali = timedelta(hours=0, minutes=0)
        for ore in self.ore_inserite:
            ore_inserite_totali += ore.ore

        return self.ore_necessarie - ore_inserite_totali
