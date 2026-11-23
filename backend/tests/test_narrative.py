import pytest

from app.utils.narrative import narrative_perspective_pt


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("第一人称", "primeira pessoa"),
        ("第三人称", "terceira pessoa"),
        ("全知视角", "onisciente"),
        ("first_person", "primeira pessoa"),
        ("third_person", "terceira pessoa"),
        ("omniscient", "onisciente"),
        ("Terceira pessoa", "terceira pessoa"),
        ("primeira pessoa", "primeira pessoa"),
        ("  Onisciente ", "onisciente"),
        (None, "terceira pessoa"),
        ("", "terceira pessoa"),
        ("segunda pessoa", "segunda pessoa"),
    ],
)
def test_narrative_perspective_pt(valor, esperado):
    assert narrative_perspective_pt(valor) == esperado
