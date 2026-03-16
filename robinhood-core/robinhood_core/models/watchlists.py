from pydantic import BaseModel
from typing import List


class Watchlist(BaseModel):
    id: str
    name: str
    symbols: List[str]
