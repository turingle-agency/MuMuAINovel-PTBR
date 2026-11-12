from app.utils.text_metrics import count_words, estimate_max_tokens


def test_count_words_portugues():
    assert count_words("Olá, mundo! Tudo bem?") == 4


def test_count_words_hifen_e_apostrofo():
    assert count_words("guarda-chuva d'água") == 2


def test_count_words_cjk_conta_caracteres():
    assert count_words("你好世界") == 4


def test_count_words_misto_markdown_emoji_preco():
    assert count_words("**Promoção**: só R$ 19,90 😀") == 4  # Promoção, só, R, 19,90


def test_count_words_vazio():
    assert count_words("") == 0
    assert count_words(None) == 0


def test_estimate_max_tokens_limites():
    assert estimate_max_tokens(3000) == 6000
    assert estimate_max_tokens(100) == 2000
    assert estimate_max_tokens(50000) == 16000
    assert estimate_max_tokens(100, floor=500, ceiling=8000) == 500


async def test_db_session_cria_tabelas(db_session):
    from sqlalchemy import text

    result = await db_session.execute(text("SELECT name FROM sqlite_master WHERE name='chapters'"))
    assert result.scalar() == "chapters"
