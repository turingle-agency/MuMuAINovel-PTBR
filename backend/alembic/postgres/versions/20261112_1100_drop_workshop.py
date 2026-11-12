"""remove tabelas do projeto original: oficina de prompts e anúncios

Revision ID: 20261112_drop_upstream
Revises: 20261112_seed_ptbr
Create Date: 2026-11-12 11:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261112_drop_upstream'
down_revision: Union[str, None] = '20261112_seed_ptbr'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Ordem importa: likes e submissions dependem de prompt_workshop_items.
TABELAS_REMOVIDAS = (
    'prompt_workshop_likes',
    'prompt_submissions',
    'prompt_workshop_items',
    'announcements',
)


def upgrade() -> None:
    existentes = set(sa.inspect(op.get_bind()).get_table_names())
    for tabela in TABELAS_REMOVIDAS:
        # Bancos novos (create_all) podem nunca ter tido essas tabelas.
        if tabela in existentes:
            op.drop_table(tabela)


def downgrade() -> None:
    # Sem-op intencional: as tabelas pertenciam a recursos do projeto original
    # (oficina de prompts e anúncios) que foram removidos do código; recriá-las
    # vazias não teria nenhum uso.
    pass
