from typing import Literal, Optional

from pydantic import BaseModel, field_validator

from .base import coerce_int, coerce_numeric


class OptionPosition(BaseModel):
    """A user's held option position."""

    symbol: Optional[str] = None
    expiration_date: Optional[str] = None
    strike_price: Optional[float] = None
    option_type: Optional[str] = None
    direction: Optional[str] = None  # "long" or "short" (debit or credit)
    quantity: Optional[float] = None
    average_price: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator(
        "strike_price",
        "quantity",
        "average_price",
        mode="before",
    )
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)


class OptionContract(BaseModel):
    symbol: str
    expiration: str
    strike: float
    type: Literal["call", "put"]
    bid: Optional[float] = None
    ask: Optional[float] = None
    mark_price: Optional[float] = None
    last_trade_price: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None
    # Greeks (populated when market data is available)
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    # Profitability
    chance_of_profit_short: Optional[float] = None
    chance_of_profit_long: Optional[float] = None

    @field_validator(
        "strike",
        "bid",
        "ask",
        "mark_price",
        "last_trade_price",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "chance_of_profit_short",
        "chance_of_profit_long",
        mode="before",
    )
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("open_interest", "volume", mode="before")
    @classmethod
    def validate_int(cls, v):
        return coerce_int(v)
