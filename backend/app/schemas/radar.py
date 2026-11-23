"""Contratos das fotografias e consultas do Radar."""
from datetime import date, datetime
from decimal import Decimal
from ipaddress import ip_address
import re
from typing import Annotated, Generic, Literal, TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator, model_validator

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


class SummaryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    evidence_ids: list[str] = Field(min_length=1, max_length=5)


class SummaryResult(BaseModel):
    status: Literal["skipped", "ok", "error"] = "skipped"
    items: list[SummaryItem] = Field(default_factory=list, max_length=8)
    detail: str | None = None


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
    summary: SummaryResult = Field(default_factory=SummaryResult)

    def citable_evidence(self) -> dict[str, EvidenceItem]:
        return {
            f"{name}:{item.id}": item
            for name, source in self.sources.items() if source.status in {"ok", "partial"}
            for item in source.items if item.url
        }


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


SourceName = Literal["firecrawl", "youtube", "trends", "amazon", "meta", "agent_reach", "apify"]
SecretSource = Literal["firecrawl", "youtube", "meta", "apify"]
CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
LanguageCode = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}(?:-[A-Z]{2})?$")]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Topic = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
BudgetLimit = Annotated[PositivePrice, Field(decimal_places=6, max_digits=12)]


class MarketProfile(BaseModel):
    country: CountryCode
    language: LanguageCode
    currency: CurrencyCode
    active: bool = False
    sources: list[SourceName] = Field(default_factory=list, max_length=7)
    kindle_categories: dict[Topic, Topic] = Field(default_factory=dict)
    price_references: dict[ProductType, PositivePrice] = Field(default_factory=dict)

    @field_validator("sources")
    @classmethod
    def unique_sources(cls, sources):
        return list(dict.fromkeys(sources))


class WeeklyEntry(BaseModel):
    topic: Topic
    country: CountryCode
    product_type: ProductType


class RadarSchedule(BaseModel):
    enabled: bool = False
    timezone: str = "America/Sao_Paulo"
    entries: list[WeeklyEntry] = Field(default_factory=list, max_length=12)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Fuso IANA inválido.") from None
        return value


class RadarBudgetConfig(BaseModel):
    monthly_limit_usd: BudgetLimit = Decimal("5")
    threshold_percent: Literal[80] = 80
    per_run_limit_usd: Literal["0.10"] = "0.10"


def default_profiles() -> list[MarketProfile]:
    return [
        MarketProfile(country=country, language=language, currency=currency, active=country == "BR")
        for country, language, currency in [
            ("BR", "pt-BR", "BRL"), ("US", "en-US", "USD"), ("GB", "en-GB", "GBP"),
            ("ES", "es-ES", "EUR"), ("PT", "pt-PT", "EUR"),
        ]
    ]


class RadarConfig(BaseModel):
    profiles: list[MarketProfile] = Field(default_factory=default_profiles, min_length=1)
    weights: Weights = Field(default_factory=Weights)
    schedule: RadarSchedule = Field(default_factory=RadarSchedule)
    budget: RadarBudgetConfig = Field(default_factory=RadarBudgetConfig)

    @model_validator(mode="after")
    def validate_profiles(self):
        codes = {p.country for p in self.profiles}
        if len(codes) != len(self.profiles):
            raise ValueError("Cada país deve ter um único perfil.")
        active = {p.country for p in self.profiles if p.active}
        if self.schedule.enabled and (
            not self.schedule.entries or any(entry.country not in active for entry in self.schedule.entries)
        ):
            raise ValueError("A agenda ativa exige combinações em mercados ativos.")
        return self


class RadarSettingsPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profiles: list[MarketProfile] | None = None
    weights: Weights | None = None
    schedule: RadarSchedule | None = None
    budget: RadarBudgetConfig | None = None
    secrets: dict[SecretSource, SecretStr | None] = Field(default_factory=dict)

    @field_validator("secrets")
    @classmethod
    def validate_secret_format(cls, secrets):
        for secret in secrets.values():
            if secret is not None and not re.fullmatch(r"[!-~]{1,1024}", secret.get_secret_value()):
                raise ValueError("Credencial inválida.")
        return secrets


class CredentialView(BaseModel):
    present: bool
    usable: bool


class CoverageView(BaseModel):
    enabled: bool
    status: Literal["ready", "not_configured", "unsupported", "disabled"]
    detail: str


class RadarSettingsView(RadarConfig):
    encryption_available: bool
    credentials: dict[SecretSource, CredentialView]
    coverage: dict[str, dict[SourceName, CoverageView]]


class SourceCheck(BaseModel):
    source: SourceName
    configured: bool
    access: Literal["ok", "error", "not_tested"] = "not_tested"
    last_status: SourceStatus | None = None
    coverage: dict[str, CoverageView]
    detail: str


class BudgetView(BaseModel):
    month: str
    limit_microusd: int
    charged_microusd: int
    reserved_microusd: int
    committed_microusd: int
    blocked: bool
    pending_count: int
