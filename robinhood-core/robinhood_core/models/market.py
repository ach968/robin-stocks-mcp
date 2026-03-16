from pydantic import BaseModel, field_validator
from typing import Optional
from .base import coerce_numeric, coerce_timestamp


class Quote(BaseModel):
    symbol: str
    last_price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    timestamp: str
    previous_close: Optional[float] = None
    change_percent: Optional[float] = None

    @field_validator(
        "last_price", "bid", "ask", "previous_close", "change_percent", mode="before"
    )
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)


class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @field_validator("open", "high", "low", "close", mode="before")
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("volume", mode="before")
    @classmethod
    def validate_int(cls, v):
        from .base import coerce_int

        return coerce_int(v)

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)
