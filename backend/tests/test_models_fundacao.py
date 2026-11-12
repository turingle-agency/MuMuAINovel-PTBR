from decimal import Decimal

from sqlalchemy import select

from app.constants.languages import language_name
from app.database import Base  # noqa: F401  (importar antes de app.models evita o ciclo)
from app.models import Offer, OfferItem, Project


async def test_projeto_tem_idioma_padrao(db_session):
    p = Project(user_id="u1", title="T")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    assert p.language == "pt-BR" and p.project_type == "fiction"


async def test_oferta_com_itens(db_session):
    o = Offer(user_id="u1")
    db_session.add(o)
    await db_session.flush()
    db_session.add(OfferItem(offer_id=o.id, role="order_bump", suggested_price=Decimal("9.90"), currency="BRL"))
    await db_session.commit()
    rows = (await db_session.execute(select(OfferItem).where(OfferItem.offer_id == o.id))).scalars().all()
    assert rows[0].role == "order_bump" and rows[0].suggested_price == Decimal("9.90")


def test_language_name_fallback():
    assert language_name("es-MX") == "espanhol (México)"
    assert language_name("xx") == "português do Brasil"
    assert language_name(None) == "português do Brasil"
