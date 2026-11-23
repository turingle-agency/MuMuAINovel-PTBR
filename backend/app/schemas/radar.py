"""Contratos das fotografias e consultas do Radar."""
from datetime import date, datetime
from decimal import Decimal
from ipaddress import ip_address
import re
from typing import Annotated, Generic, Literal, TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ProductType = Literal["lowticket", "fiction"]
ResearchMode = Literal["manual", "weekly"]
ResearchStatus = Literal["pending", "running", "complete", "partial", "failed"]
SourceStatus = Literal[
    "ok", "empty", "not_configured", "unsupported", "budget_blocked", "error",
    "partial", "not_applicable",
]
PositivePrice = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


class Weights(BaseModel):
    demand: int = Field(default=50, strict=True, ge=0, le=100)
    competition: int = Field(default=30, strict=True, ge=0, le=100)
    price: int = Field(default=20, strict=True, ge=0, le=100)

    @model_validator(mode="after")
    def validate_total(self):
        if self.demand + self.competition + self.price != 100:
            raise ValueError("A soma dos pesos deve ser 100.")
        return self


class CollectorInput(BaseModel):
    query: str
    country: str
    language: str
    currency: str
    product_type: ProductType
    category: str | None = None
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("A data inicial deve preceder a data final.")
        return self


def public_url(value: str | None) -> str | None:
    if not value or any(ord(char) <= 32 for char in value) or "\\" in value:
        return None
    try:
        url = urlsplit(value)
        host = url.hostname
        port = url.port
    except ValueError:
        return None
    if url.scheme not in ("https", "http") or not host or url.username is not None:
        return None
    if port not in (None, 80, 443) or host.lower().rstrip(".").endswith((".localhost", ".local")):
        return None
    try:
        address = ip_address(host)
    except ValueError:
        if not re.fullmatch(r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z][a-zA-Z0-9-]*\.?$", host):
            return None
    else:
        if not address.is_global:
            return None
    query = []
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com") and url.path == "/watch":
        query = [
            (key, val) for key, val in parse_qsl(url.query)
            if key in {"v", "lc"} and re.fullmatch(r"[A-Za-z0-9_-]{1,120}", val)
        ]
    return urlunsplit((url.scheme, url.netloc, url.path, urlencode(query), ""))


class EvidenceData(BaseModel):
    value: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    asin: str | None = None
    category: str | None = None
    rank: int | None = Field(default=None, gt=0)
    search_position: int | None = Field(default=None, gt=0)
    format: Literal["kindle", "print", "other"] | None = None
    price: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    currency: str | None = None
    price_kind: Literal["purchase", "subscription", "list"] | None = None
    sponsored: bool | None = None
    active: bool | None = None
    commercial: bool | None = None
    started_at: date | None = None
    excerpt: str | None = None
    related_query: str | None = None

    @field_validator("excerpt", "related_query")
    @classmethod
    def limit_text(cls, value):
        return " ".join(re.sub(r"<[^>]*>", "", value).split())[:500] if value else value


class EvidenceItem(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    url: str | None = None
    label: str = Field(min_length=1, max_length=500)
    observed_date: date | None = None
    kind: Literal["trend", "related", "book", "ad", "content"]
    data: EvidenceData = Field(default_factory=EvidenceData)

    _clean_url = field_validator("url")(public_url)


class SourceLimits(BaseModel):
    sample_limit: int | None = Field(default=None, ge=1)
    exhausted: bool = False
    insufficient_volume: bool = False
    comparable: bool = True
    notes: list[str] = Field(default_factory=list)


class SourceResult(BaseModel):
    source: str
    status: SourceStatus
    collected_at: datetime
    from_cache: bool = False
    scope: str
    method_version: str
    limits: SourceLimits = Field(default_factory=SourceLimits)
    items: list[EvidenceItem] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def unique_items(cls, items):
        unique = {}
        for item in items:
            unique.setdefault(item.id, item)
        return list(unique.values())


class ScoreResult(BaseModel):
    score: float | None = None
    demand: float | None = None
    competition: float | None = None
    price: float | None = None
    direction_points: float | None = None
    amazon_average: Decimal | None = None
    amazon_count: int = 0
    method_key: str = ""
    formula_version: Literal[1] = 1


class ResearchProgress(BaseModel):
    done: int = 0
    total: int = 0
    current_source: str | None = None


class ResearchSnapshot(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    version: Literal[1] = 1
    input: CollectorInput | None = None
    writing_language: str = "pt-BR"
    weights: Weights = Field(default_factory=Weights)
    price_reference: PositivePrice | None = None
    enabled_sources: list[str] = Field(default_factory=list)
    sources: dict[str, SourceResult] = Field(default_factory=dict)
    progress: ResearchProgress = Field(default_factory=ResearchProgress)
    score: ScoreResult | None = None


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
