from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from .base import coerce_numeric, coerce_int


class OptionContract(BaseModel):
    symbol: str
    expiration: str
    strike: float
    type: Literal["call", "put"]
    bid: Optional[float] = None
    ask: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None

    @field_validator('strike', 'bid', 'ask', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator('open_interest', 'volume', mode='before')
    @classmethod
    def validate_int(cls, v):
        return coerce_int(v)
