from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator

from .base import coerce_numeric, coerce_timestamp


class OrderExecution(BaseModel):
    """A single execution (fill) within an order."""

    price: Optional[float] = None
    quantity: Optional[float] = None
    settlement_date: Optional[str] = None
    timestamp: Optional[str] = None
    id: Optional[str] = None

    @field_validator("price", "quantity", mode="before")
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)


class StockOrder(BaseModel):
    """A historical stock order."""

    id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None  # "buy" or "sell"
    type: Optional[str] = None  # "market", "limit", etc.
    state: Optional[str] = (
        None  # "filled", "cancelled", "confirmed", "queued", "failed"
    )
    quantity: Optional[float] = None
    cumulative_quantity: Optional[float] = None
    price: Optional[float] = None
    average_price: Optional[float] = None
    stop_price: Optional[float] = None
    executions: List[OrderExecution] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_transaction_at: Optional[str] = None
    time_in_force: Optional[str] = None  # "gtc", "gfd"
    extended_hours: Optional[bool] = None

    @field_validator(
        "quantity",
        "cumulative_quantity",
        "price",
        "average_price",
        "stop_price",
        mode="before",
    )
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("created_at", "updated_at", "last_transaction_at", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)


class OptionOrder(BaseModel):
    """A historical option order."""

    id: Optional[str] = None
    chain_symbol: Optional[str] = None
    direction: Optional[str] = None  # "credit" or "debit"
    type: Optional[str] = None  # "market", "limit"
    state: Optional[str] = None
    quantity: Optional[float] = None
    pending_quantity: Optional[float] = None
    processed_quantity: Optional[float] = None
    price: Optional[float] = None
    premium: Optional[float] = None
    processed_premium: Optional[float] = None
    opening_strategy: Optional[str] = None
    closing_strategy: Optional[str] = None
    legs: Optional[list] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    time_in_force: Optional[str] = None

    @field_validator(
        "quantity",
        "pending_quantity",
        "processed_quantity",
        "price",
        "premium",
        "processed_premium",
        mode="before",
    )
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)


class CryptoOrder(BaseModel):
    """A historical crypto order."""

    id: Optional[str] = None
    currency_pair_id: Optional[str] = None
    side: Optional[str] = None  # "buy" or "sell"
    type: Optional[str] = None
    state: Optional[str] = None
    quantity: Optional[float] = None
    cumulative_quantity: Optional[float] = None
    price: Optional[float] = None
    average_price: Optional[float] = None
    executions: Optional[list] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    time_in_force: Optional[str] = None

    @field_validator(
        "quantity",
        "cumulative_quantity",
        "price",
        "average_price",
        mode="before",
    )
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)


class OrderHistory(BaseModel):
    """Unified order history response."""

    stock_orders: List[StockOrder] = []
    option_orders: List[OptionOrder] = []
    crypto_orders: List[CryptoOrder] = []
