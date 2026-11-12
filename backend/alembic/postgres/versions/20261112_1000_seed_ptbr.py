"""dados semeados em PT-BR: tipos de relação e estilos de escrita globais

Revision ID: 20261112_seed_ptbr
Revises: 20261112_fundacao
Create Date: 2026-11-12 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261112_seed_ptbr'
down_revision: Union[str, None] = '20261112_fundacao'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# nome antigo (chinês) -> (name, reverse_name, description) em PT-BR.
# Mantenha igual a RELATIONSHIP_TYPES em app/init_relationship_types.py.
RELATIONSHIP_TYPES_PTBR = {
    "父亲": ("pai", "filho(a)", "Relação de pai com filho ou filha"),
    "母亲": ("mãe", "filho(a)", "Relação de mãe com filho ou filha"),
    "兄弟": ("irmão", "irmão", "Relação entre irmãos"),
    "姐妹": ("irmã", "irmã", "Relação entre irmãs"),
    "子女": ("filho(a)", "pai/mãe", "Relação de filho ou filha com os pais"),
    "配偶": ("cônjuge", "cônjuge", "Relação de casamento"),
    "恋人": ("par romântico", "par romântico", "Relação amorosa"),
    "师父": ("mestre", "discípulo", "Relação de mestre e discípulo (ponto de vista do mestre)"),
    "徒弟": ("discípulo", "mestre", "Relação de mestre e discípulo (ponto de vista do discípulo)"),
    "朋友": ("amigo", "amigo", "Relação de amizade"),
    "同学": ("colega de classe", "colega de classe", "Relação entre colegas de escola ou turma"),
    "邻居": ("vizinho", "vizinho", "Relação entre vizinhos"),
    "知己": ("confidente", "confidente", "Amigo próximo, de total confiança"),
    "上司": ("chefe", "subordinado", "Relação hierárquica (ponto de vista do chefe)"),
    "下属": ("subordinado", "chefe", "Relação hierárquica (ponto de vista do subordinado)"),
    "同事": ("colega de trabalho", "colega de trabalho", "Relação entre colegas de trabalho"),
    "合作伙伴": ("parceiro de negócios", "parceiro de negócios", "Relação de cooperação"),
    "敌人": ("inimigo", "inimigo", "Relação de inimizade"),
    "仇人": ("inimigo mortal", "inimigo mortal", "Relação de ódio profundo"),
    "竞争对手": ("rival", "rival", "Relação de competição"),
    "宿敌": ("nêmesis", "nêmesis", "Inimigo predestinado"),
}

# preset_id -> (name, description, prompt_content) em PT-BR
WRITING_STYLES_PTBR = {
    "natural": (
        "Natural e fluido",
        "Estilo narrativo natural e fluido, indicado para romance contemporâneo, urbano e realista",
        """Requisitos de estilo:
1. Linguagem simples e direta, próxima da fala atual
2. Frases curtas, com ritmo fluido
3. Atenção aos detalhes emocionais, que surgem de forma natural
4. Evite enfeites excessivos e construções complexas""",
    ),
    "classical": (
        "Clássico e elegante",
        "Estilo clássico e refinado, indicado para romance de época, fantasia e narrativas de cultivo",
        """Requisitos de estilo:
1. Use linguagem erudita ou um registro formal e elegante
2. Empregue com moderação imagens da poesia clássica
3. Cuide da atmosfera e da ressonância poética
4. Mantenha a beleza clássica nos diálogos e nas descrições""",
    ),
    "modern": (
        "Moderno e enxuto",
        "Estilo moderno e enxuto, indicado para light novels e narrativas de ritmo acelerado",
        """Requisitos de estilo:
1. Linguagem direta e concisa, com alta densidade de informação
2. Use diálogos para conduzir a trama
3. Evite descrições longas e destaque as ações-chave
4. Ritmo ágil, próprio para leitura rápida""",
    ),
    "literary": (
        "Literário e delicado",
        "Estilo literário e delicado, com foco na psicologia dos personagens e na atmosfera",
        """Requisitos de estilo:
1. Dê atenção à vida interior e aos detalhes emocionais
2. Use descrições do ambiente para construir a atmosfera
3. Linguagem bela e de qualidade literária
4. Use com critério metáforas, símbolos e outras figuras de linguagem""",
    ),
    "suspense": (
        "Tenso e de suspense",
        "Estilo tenso e de suspense, indicado para mistério, policial e thriller",
        """Requisitos de estilo:
1. Crie uma atmosfera tensa e opressiva
2. Use frases curtas para acelerar o ritmo
3. Saiba plantar suspense e pistas
4. Cuide dos detalhes, deixando indícios para a investigação""",
    ),
    "humorous": (
        "Bem-humorado",
        "Estilo bem-humorado e divertido, indicado para histórias leves e cômicas",
        """Requisitos de estilo:
1. Linguagem viva e espirituosa, com tiradas bem-humoradas
2. Dê atenção ao efeito cômico dos diálogos
3. Use exageros e reviravoltas para criar graça
4. Mantenha um tom leve e alegre""",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()

    for old_name, (name, reverse_name, description) in RELATIONSHIP_TYPES_PTBR.items():
        bind.execute(
            sa.text(
                "UPDATE relationship_types "
                "SET name = :name, reverse_name = :reverse_name, description = :description "
                "WHERE name = :old_name"
            ),
            {"name": name, "reverse_name": reverse_name, "description": description, "old_name": old_name},
        )

    for preset_id, (name, description, prompt_content) in WRITING_STYLES_PTBR.items():
        bind.execute(
            sa.text(
                "UPDATE writing_styles "
                "SET name = :name, description = :description, prompt_content = :prompt_content "
                "WHERE user_id IS NULL AND preset_id = :preset_id"
            ),
            {"name": name, "description": description, "prompt_content": prompt_content, "preset_id": preset_id},
        )


def downgrade() -> None:
    # Migração de dados sem volta: os textos originais em chinês não são restaurados.
    pass
