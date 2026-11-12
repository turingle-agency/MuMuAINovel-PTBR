"""colunas de API de reserva (fallback) para o provider Codex

Revision ID: 20261112_fallback
Revises: 20261112_drop_upstream
Create Date: 2026-11-12 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261112_fallback'
down_revision: Union[str, None] = '20261112_drop_upstream'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUNAS = (
    ('fallback_api_provider', 50),
    ('fallback_api_key', 500),
    ('fallback_api_base_url', 500),
    ('fallback_llm_model', 100),
)


def upgrade() -> None:
    existentes = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('settings')}
    with op.batch_alter_table('settings', schema=None) as batch_op:
        for nome, tamanho in COLUNAS:
            # Bancos novos (create_all) já nascem com as colunas.
            if nome not in existentes:
                batch_op.add_column(sa.Column(nome, sa.String(tamanho), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('settings', schema=None) as batch_op:
        for nome, _ in COLUNAS:
            batch_op.drop_column(nome)
