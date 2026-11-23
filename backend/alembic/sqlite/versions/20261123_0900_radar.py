"""Persistência inicial do Radar de Nichos."""

from alembic import op
import sqlalchemy as sa

revision = "20261123_radar"
down_revision = "20261112_fallback"
branch_labels = None
depends_on = None

RESEARCH = "niche_researches"
FIELDS = {
    "input_key": sa.String(64),
    "topic_key": sa.Text(),
    "topic_hash": sa.String(64),
    "mode": sa.String(10),
    "week_key": sa.String(8),
    "lease_until": sa.DateTime(),
    "finished_at": sa.DateTime(),
}
INDEXES = {
    "ux_niche_researches_input_key": (["input_key"], True),
    "ix_niche_researches_claim": (["status", "created_at", "id"], False),
    "ix_niche_researches_history": (["user_id", "topic_hash", "created_at", "id"], False),
}


def upgrade():
    for name, type_ in FIELDS.items():
        op.add_column(RESEARCH, sa.Column(name, type_))
    for name, (fields, unique) in INDEXES.items():
        op.create_index(name, RESEARCH, fields, unique=unique)

    op.create_table(
        "radar_settings",
        sa.Column("admin_id", sa.String(100), primary_key=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("encrypted_secrets", sa.JSON(), nullable=False),
    )
    op.create_table(
        "radar_source_cache",
        sa.Column("admin_id", sa.String(100), primary_key=True),
        sa.Column("cache_key", sa.String(64), primary_key=True),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "radar_budget_months",
        sa.Column("admin_id", sa.String(100), primary_key=True),
        sa.Column("month", sa.String(7), primary_key=True),
        sa.Column("charged_microusd", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reserved_microusd", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_table(
        "radar_budget_reservations",
        sa.Column("research_id", sa.String(36), sa.ForeignKey(f"{RESEARCH}.id", ondelete="RESTRICT"),
                  primary_key=True),
        sa.Column("source", sa.String(40), primary_key=True),
        sa.Column("admin_id", sa.String(100), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("reserved_microusd", sa.BigInteger(), nullable=False),
        sa.Column("charged_microusd", sa.BigInteger()),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("remote_run_id", sa.String(100)),
    )
    op.create_table(
        "writing_briefs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admin_id", sa.String(100), nullable=False),
        sa.Column("research_id", sa.String(36), sa.ForeignKey(f"{RESEARCH}.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ready"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("research_id", name="uq_writing_briefs_research"),
    )
    op.create_index("ix_writing_briefs_admin_id", "writing_briefs", ["admin_id"])


def downgrade():
    for table in (
        "writing_briefs", "radar_budget_reservations", "radar_budget_months", "radar_source_cache",
        "radar_settings",
    ):
        op.drop_table(table)
    for name in INDEXES:
        op.drop_index(name, table_name=RESEARCH)
    with op.batch_alter_table(RESEARCH) as batch:
        for name in FIELDS:
            batch.drop_column(name)
