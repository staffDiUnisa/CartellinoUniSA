from datetime import timedelta
from typing import Annotated
from pydantic import BaseModel, Field

class OreInserite(BaseModel):
    id: Annotated[int, Field(description="ID dell'ora inserita")]
    data: Annotated[str , Field(description="Data dell'ora inserita in formato YYYY-MM-DD")]
    ore: Annotated[timedelta , Field(description="Ore inserite")]
    stato: Annotated[str, Field(description="Stato dell'ora inserita", default="ELAB GG")]