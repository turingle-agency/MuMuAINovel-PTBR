"""Contratos das fotografias e consultas do Radar."""
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

ProductType = Literal["lowticket", "fiction"]
ResearchMode = Literal["manual", "weekly"]


class ResearchSnapshot(BaseModel):
    version: Literal[1] = 1


class ResearchInput(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    country: str
    product_type: ProductType
    mode: ResearchMode
    input_key: str
    week_key: str | None = None
    snapshot: ResearchSnapshot


class PageFilters(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ResearchFilters(PageFilters):
    country: str | None = None
    product_type: ProductType | None = None
    mode: ResearchMode | None = None
    week_key: str | None = None


ResearchRow = TypeVar("ResearchRow")


class ResearchPage(BaseModel, Generic[ResearchRow], arbitrary_types_allowed=True):
    items: list[ResearchRow]
    total: int
    page: int
    page_size: int
