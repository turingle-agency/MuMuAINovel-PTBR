from app.database import Base  # noqa: F401  (importar antes de app.models evita o ciclo)
from app.services.character_state_update_service import CharacterStateUpdateService as S


def test_delta_numerico_tem_prioridade():
    assert S._calculate_intimacy_delta({"change": "traição", "intimacy_delta": -25}) == -25


def test_delta_limitado():
    assert S._calculate_intimacy_delta({"change": "x", "intimacy_delta": 99}) == 30
    assert S._calculate_intimacy_delta({"change": "x", "intimacy_delta": -99}) == -30


def test_delta_dict_sem_numero_usa_palavras_chave():
    assert S._calculate_intimacy_delta({"change": "traição"}) < 0
    assert S._calculate_intimacy_delta({"change": "traição", "intimacy_delta": "abc"}) < 0


def test_delta_por_palavra_chave_pt():
    assert S._calculate_intimacy_delta("a relação melhorou muito") > 0
    assert S._calculate_intimacy_delta("traição") < 0


def test_desconfianca_nao_conta_como_confianca():
    assert S._calculate_intimacy_delta("desconfiança crescente") < 0


def test_delta_formato_antigo_chines_continua():
    assert S._calculate_intimacy_delta("背叛") == -30


def test_delta_sem_palavra_chave_e_zero():
    assert S._calculate_intimacy_delta("eles conversaram sobre o tempo") == 0
