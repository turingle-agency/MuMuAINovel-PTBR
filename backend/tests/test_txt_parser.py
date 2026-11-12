from app.services.txt_parser_service import txt_parser_service


def test_parser_capitulos_pt():
    chapters = txt_parser_service.split_chapters(
        "Capítulo 1 - Início\n" + "texto " * 300 + "\nCapítulo 2\n" + "mais " * 300
    )
    assert [c["title"] for c in chapters][:2] == ["Capítulo 1 - Início", "Capítulo 2"]


def test_parser_parte_e_chapter():
    text = "Parte 1\n" + "a " * 300 + "\nChapter 2\n" + "b " * 300
    titles = [c["title"] for c in txt_parser_service.split_chapters(text)]
    assert titles[:2] == ["Parte 1", "Chapter 2"]


def test_parser_numeral_romano():
    text = "CAPÍTULO IV\n" + "a " * 300 + "\nCapitulo 5\n" + "b " * 300
    titles = [c["title"] for c in txt_parser_service.split_chapters(text)]
    assert titles[:2] == ["CAPÍTULO IV", "Capitulo 5"]


def test_fallback_usa_titulo_pt():
    chapters = txt_parser_service.split_chapters("palavra, " * 800)
    assert chapters and chapters[0]["title"] == "Capítulo 1"
