"""fundacao: idioma do projeto, series, pesquisa de nicho e ofertas

Revision ID: 20261112_fundacao
Revises: 20260914_knowledge
Create Date: 2026-11-12 09:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261112_fundacao'
down_revision: Union[str, None] = '20260914_knowledge'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'series',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), server_default='pt-BR', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_series_user_id'), 'series', ['user_id'], unique=False)

    op.create_table(
        'niche_researches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('topic', sa.String(length=300), nullable=False),
        sa.Column('country', sa.String(length=10), nullable=True),
        sa.Column('product_type', sa.String(length=50), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('signals', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_niche_researches_user_id'), 'niche_researches', ['user_id'], unique=False)

    op.create_table(
        'offers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('niche_research_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['niche_research_id'], ['niche_researches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_offers_user_id'), 'offers', ['user_id'], unique=False)
    op.create_index(op.f('ix_offers_niche_research_id'), 'offers', ['niche_research_id'], unique=False)

    op.add_column('projects', sa.Column('language', sa.String(length=10), server_default='pt-BR', nullable=False))
    op.add_column('projects', sa.Column('project_type', sa.String(length=20), server_default='fiction', nullable=False))
    op.add_column('projects', sa.Column('series_id', sa.String(length=36), nullable=True))
    op.add_column('projects', sa.Column('volume_number', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_projects_series_id'), 'projects', ['series_id'], unique=False)
    op.create_foreign_key('fk_projects_series_id', 'projects', 'series', ['series_id'], ['id'], ondelete='SET NULL')
    op.create_check_constraint('check_project_type', 'projects', "project_type IN ('fiction', 'lowticket')")

    op.create_table(
        'offer_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('offer_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('suggested_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('price_rationale', sa.Text(), nullable=True),
        sa.CheckConstraint(
            "role IN ('main', 'order_bump', 'upsell', 'downsell')",
            name='check_offer_item_role',
        ),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_offer_items_offer_id'), 'offer_items', ['offer_id'], unique=False)
    op.create_index(op.f('ix_offer_items_project_id'), 'offer_items', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_offer_items_project_id'), table_name='offer_items')
    op.drop_index(op.f('ix_offer_items_offer_id'), table_name='offer_items')
    op.drop_table('offer_items')

    op.drop_constraint('check_project_type', 'projects', type_='check')
    op.drop_constraint('fk_projects_series_id', 'projects', type_='foreignkey')
    op.drop_index(op.f('ix_projects_series_id'), table_name='projects')
    op.drop_column('projects', 'volume_number')
    op.drop_column('projects', 'series_id')
    op.drop_column('projects', 'project_type')
    op.drop_column('projects', 'language')

    op.drop_index(op.f('ix_offers_niche_research_id'), table_name='offers')
    op.drop_index(op.f('ix_offers_user_id'), table_name='offers')
    op.drop_table('offers')
    op.drop_index(op.f('ix_niche_researches_user_id'), table_name='niche_researches')
    op.drop_table('niche_researches')
    op.drop_index(op.f('ix_series_user_id'), table_name='series')
    op.drop_table('series')
