from pydantic import BaseModel, field_validator
from typing import Optional
from .base import coerce_timestamp


class NewsItem(BaseModel):
    id: str
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: str

    @field_validator("published_at", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)
