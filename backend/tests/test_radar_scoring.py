from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.radar import EvidenceItem, ResearchSnapshot, SourceResult, Weights
from app.services.radar_scoring import comparable_scores, score_research


def fonte(nome, items=(), **kwargs):
    return SourceResult(source=nome, collected_at=datetime(2026, 11, 23, tzinfo=timezone.utc),
                        scope="BR", method_version="1", items=items, **kwargs)


def exemplo():
    fim = date(2026, 11, 22)
    trends = [
        EvidenceItem(id=str(i), kind="trend", label="Série", observed_date=fim - timedelta(days=i),
                     data={"value": 60 if i < 28 else 45})
        for i in range(56)
    ]
    ads = [
        EvidenceItem(id=str(i), kind="ad", label="Anúncio",
                     data={"active": True, "commercial": True})
        for i in range(8)
    ]
    livros = [
        EvidenceItem(id=str(i), kind="book", label="Livro", data={
            "asin": f"ASIN{i}", "format": "kindle", "price": preco,
            "currency": "BRL", "price_kind": "purchase",
        })
        for i, preco in enumerate((20, 30, 40))
    ]
    return ResearchSnapshot(input={
        "query": "Tema", "country": "BR", "language": "pt-BR", "currency": "BRL",
        "product_type": "lowticket", "start_date": fim - timedelta(days=55), "end_date": fim,
    }, price_reference=40, sources={
        "trends": fonte("trends", trends, status="ok"),
        "meta": fonte("meta", ads, status="ok", limits={"exhausted": True, "sample_limit": 20}),
        "amazon": fonte("amazon", livros, status="ok"),
    })


def test_score_reference_case():
    result = score_research(exemplo())
    assert (result.demand, result.competition, result.price, result.score) == (60, 60, 75, 63.0)
    assert (result.direction_points, result.amazon_average, result.amazon_count) == (15, 30, 3)


def test_sparse_series_mixed_currency_duplicate_ids_and_weight_zero():
    snapshot = exemplo()
    snapshot.sources["trends"].items.pop()
    snapshot.sources["meta"].limits.exhausted = False
    amazon = snapshot.sources["amazon"]
    livro = amazon.items[-1]
    livro.data.currency = "USD"
    amazon.items.append(amazon.items[0])
    result = score_research(snapshot)
    assert (result.demand, result.competition, result.price, result.score) == (None, None, None, None)
    assert result.amazon_count == 2

    livro.data.currency = "BRL"
    snapshot.price_reference = None
    assert score_research(snapshot).amazon_average == 30
    snapshot.sources["meta"] = fonte("meta", status="empty")
    assert score_research(snapshot).competition == 100
    snapshot.sources["meta"] = fonte("meta", status="ok", items=[
        EvidenceItem(id=str(i), kind="ad", label="Anúncio",
                     data={"active": True, "commercial": True})
        for i in range(21)
    ])
    assert score_research(snapshot).competition == 0
    snapshot.weights = Weights(demand=100, competition=0, price=0)
    snapshot.sources["trends"] = exemplo().sources["trends"]
    assert score_research(snapshot).score == 60


@pytest.mark.parametrize("mudanca", ["peso", "referencia", "moeda", "categoria", "escopo", "versao", "janela"])
def test_comparison_rejects_changes_in_inputs_or_method(mudanca):
    snapshot = exemplo()
    outro = exemplo()
    outro.input.start_date -= timedelta(days=7)
    outro.input.end_date -= timedelta(days=7)
    for item in outro.sources["trends"].items:
        item.observed_date -= timedelta(days=7)
    assert comparable_scores(score_research(snapshot), score_research(outro))
    if mudanca == "peso":
        outro.weights = Weights(demand=50, competition=40, price=10)
    elif mudanca == "referencia":
        outro.price_reference = 60
    elif mudanca == "moeda":
        outro.input.currency = "USD"
    elif mudanca == "categoria":
        outro.input.category = "romance"
    elif mudanca == "escopo":
        outro.sources["meta"].scope = "ES"
    elif mudanca == "versao":
        outro.sources["meta"].method_version = "2"
    else:
        outro.input.start_date -= timedelta(days=1)
    anterior, atual = score_research(snapshot), score_research(outro)
    assert anterior.method_key != atual.method_key
    assert not comparable_scores(anterior, atual)


def test_evidence_removes_secrets_and_keeps_public_links():
    item = EvidenceItem(
        id="video:1", kind="content", label="Comentário",
        url="https://www.youtube.com/watch?v=abc&utm_source=x&token=segredo#frag",
        data={"excerpt": "a" * 600, "author": "Fulano", "raw_html": "<b>texto</b>", "token": "segredo"},
    )
    assert item.url == "https://www.youtube.com/watch?v=abc"
    assert len(item.data.excerpt) == 500
    serialized = item.model_dump_json()
    assert all(v not in serialized for v in ("Fulano", "raw_html", "segredo"))
    assert item.model_copy(update={"url": None}).url is None


@pytest.mark.parametrize("campos", [{"weights": {"demand": 100, "competition": 1, "price": 0}},
                                    {"price_reference": 0}, {"price_reference": "-1"}])
def test_snapshot_rejects_invalid_scoring_settings(campos):
    with pytest.raises(ValidationError):
        ResearchSnapshot(**campos)
