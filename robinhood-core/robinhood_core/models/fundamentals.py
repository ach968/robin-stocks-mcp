from pydantic import BaseModel, field_validator
from typing import Optional
from .base import coerce_numeric


class Fundamentals(BaseModel):
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None

    @field_validator("*", mode="before")
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)
