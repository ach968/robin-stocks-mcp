from pydantic import BaseModel, field_validator
from typing import Optional
from .base import coerce_numeric


class PortfolioSummary(BaseModel):
    equity: float
    cash: float
    buying_power: float
    unrealized_pl: Optional[float] = None
    day_change: Optional[float] = None

    @field_validator(
        "equity", "cash", "buying_power", "unrealized_pl", "day_change", mode="before"
    )
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)


class Position(BaseModel):
    symbol: str
    quantity: float
    average_cost: float
    market_value: Optional[float] = None
    unrealized_pl: Optional[float] = None

    @field_validator("average_cost", "market_value", "unrealized_pl", mode="before")
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v):
        return coerce_numeric(v)
