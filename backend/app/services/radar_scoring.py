"""Cálculo determinístico da nota de oportunidade v1."""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json

from app.schemas.radar import CollectorInput, EvidenceItem, ResearchSnapshot, ScoreResult, SourceResult

OBSERVED = {"ok", "empty", "partial"}
COMPETITION_LIMIT = 20


def _demand(source: SourceResult | None, input: CollectorInput):
    if not source or source.status not in OBSERVED or (
        source.limits.insufficient_volume or not source.limits.comparable
    ):
        return None, None
    days = {
        item.observed_date: Decimal(str(item.data.value))
        for item in source.items
        if item.kind == "trend" and item.observed_date and item.data.value is not None
    }
    expected = [input.end_date - timedelta(days=i) for i in range(56)]
    if input.start_date != expected[-1] or not all(day in days for day in expected):
        return None, None
    recent = sum(days[day] for day in expected[:28]) / 28
    previous = sum(days[day] for day in expected[28:]) / 28
    return recent, recent - previous


def _kindle(item: EvidenceItem, category: str | None) -> bool:
    data = item.data
    return (
        item.kind == "book" and bool(data.asin) and data.format == "kindle"
        and (category is None or data.category == category)
    )


def _competition(source: SourceResult | None, input: CollectorInput):
    if not source or source.status not in OBSERVED:
        return None
    if input.product_type == "fiction":
        if not input.category:
            return None
        ids = {
            item.data.asin.upper() for item in source.items
            if _kindle(item, input.category) and item.data.sponsored is False
        }
    else:
        ids = {
            item.id for item in source.items
            if item.kind == "ad" and item.data.active is True and item.data.commercial is True
        }
    if len(ids) < COMPETITION_LIMIT and not (
        source.status == "empty" or (source.status == "ok" and source.limits.exhausted)
    ):
        return None
    return Decimal(100) * (COMPETITION_LIMIT - min(len(ids), COMPETITION_LIMIT)) / COMPETITION_LIMIT


def _amazon_prices(source: SourceResult | None, input: CollectorInput):
    prices = {}
    if source and source.status in OBSERVED:
        category = input.category if input.product_type == "fiction" else None
        for item in source.items:
            data = item.data
            if (_kindle(item, category) and data.price_kind == "purchase"
                    and data.price is not None and data.currency == input.currency):
                prices.setdefault(data.asin.upper(), data.price)
    count = len(prices)
    return (sum(prices.values()) / count if count >= 3 else None), count


def _method_key(snapshot, input, source_names):
    methods = {}
    for name in source_names:
        source = snapshot.sources.get(name)
        if source:
            methods[name] = [source.source, source.scope, source.method_version, source.limits.sample_limit]
    method = {
        "formula": 1,
        "weights": snapshot.weights.model_dump(),
        "price_reference": str(snapshot.price_reference.normalize()) if snapshot.price_reference else None,
        "input": input.model_dump(mode="json", exclude={"start_date", "end_date"}),
        "window_days": (input.end_date - input.start_date).days + 1,
        "sources": methods,
    }
    return sha256(json.dumps(method, sort_keys=True).encode()).hexdigest()


def score_research(snapshot: ResearchSnapshot) -> ScoreResult:
    input = snapshot.input
    if input is None:
        return ScoreResult()
    competitor = "meta" if input.product_type == "lowticket" else "amazon"
    demand, direction = _demand(snapshot.sources.get("trends"), input)
    competition = _competition(snapshot.sources.get(competitor), input)
    average, count = _amazon_prices(snapshot.sources.get("amazon"), input)
    price = None
    if average is not None and snapshot.price_reference is not None:
        price = min(Decimal(100), 100 * average / snapshot.price_reference)
    components = {"demand": demand, "competition": competition, "price": price}
    weighted = [
        (components[key], weight)
        for key, weight in snapshot.weights.model_dump().items() if weight
    ]
    score = None
    if all(value is not None for value, _ in weighted):
        score = (sum(value * weight for value, weight in weighted) / 100).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP,
        )
    return ScoreResult(
        **components, score=score, direction_points=direction,
        amazon_average=average, amazon_count=count,
        method_key=_method_key(snapshot, input, ("trends", competitor, "amazon")),
    )


def comparable_scores(a: ScoreResult, b: ScoreResult) -> bool:
    return (
        a.score is not None and b.score is not None and bool(a.method_key)
        and a.method_key == b.method_key
    )
