"""initial cdp schema

Revision ID: 0001
Revises:
Create Date: 2026-04-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── Schema ──────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS cdp")
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ─── sources ─────────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("write_key", sa.String(), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="cdp",
    )

    # ─── admin_users ─────────────────────────────────────────────────────
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="analyst"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="cdp",
    )

    # ─── profiles ────────────────────────────────────────────────────────
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(), unique=True, nullable=True),
        sa.Column("phone", sa.String(), unique=True, nullable=True),
        sa.Column("loyalty_member_id", sa.String(), unique=True, nullable=True),
        sa.Column("sales_customer_id", sa.String(), unique=True, nullable=True),
        sa.Column("traits", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("merged_into", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merged_into"], ["cdp.profiles.id"], name="fk_profile_merged_into"),
        schema="cdp",
    )
    op.create_index("idx_profiles_email", "profiles", ["email"], schema="cdp", postgresql_where=sa.text("email IS NOT NULL"))
    op.create_index("idx_profiles_phone", "profiles", ["phone"], schema="cdp", postgresql_where=sa.text("phone IS NOT NULL"))
    op.create_index("idx_profiles_loyalty", "profiles", ["loyalty_member_id"], schema="cdp")
    op.create_index("idx_profiles_traits", "profiles", ["traits"], schema="cdp", postgresql_using="gin")

    # ─── identities ──────────────────────────────────────────────────────
    op.create_table(
        "identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id_type", sa.String(), nullable=False),
        sa.Column("id_value", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["cdp.profiles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("id_type", "id_value", name="uq_identity_type_value"),
        schema="cdp",
    )
    op.create_index("idx_identities_profile", "identities", ["profile_id"], schema="cdp")
    op.create_index("idx_identities_lookup", "identities", ["id_type", "id_value"], schema="cdp")

    # ─── events (partitioned) ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE cdp.events (
            id            UUID NOT NULL DEFAULT gen_random_uuid(),
            profile_id    UUID REFERENCES cdp.profiles(id),
            anonymous_id  TEXT,
            session_id    TEXT,
            event_type    TEXT NOT NULL,
            event_name    TEXT NOT NULL,
            properties    JSONB NOT NULL DEFAULT '{}',
            context       JSONB NOT NULL DEFAULT '{}',
            source        TEXT NOT NULL,
            received_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            occurred_at   TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (id, occurred_at)
        ) PARTITION BY RANGE (occurred_at)
    """)
    # Create partitions for current year + next year
    for year in [2025, 2026, 2027]:
        for month in range(1, 13):
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            op.execute(f"""
                CREATE TABLE IF NOT EXISTS cdp.events_{year}_{month:02d}
                PARTITION OF cdp.events
                FOR VALUES FROM ('{year}-{month:02d}-01') TO ('{next_year}-{next_month:02d}-01')
            """)
    op.execute("CREATE INDEX idx_events_profile ON cdp.events (profile_id, occurred_at DESC)")
    op.execute("CREATE INDEX idx_events_anon    ON cdp.events (anonymous_id, occurred_at DESC)")
    op.execute("CREATE INDEX idx_events_type    ON cdp.events (event_type, occurred_at DESC)")
    op.execute("CREATE INDEX idx_events_props   ON cdp.events USING GIN (properties)")

    # ─── segments ────────────────────────────────────────────────────────
    op.create_table(
        "segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rules", postgresql.JSONB(), nullable=False),
        sa.Column("refresh_mode", sa.String(), nullable=False, server_default="scheduled"),
        sa.Column("refresh_cron", sa.String(), nullable=True, server_default="0 2 * * *"),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_computed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="cdp",
    )

    # ─── segment_members ─────────────────────────────────────────────────
    op.create_table(
        "segment_members",
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["segment_id"], ["cdp.segments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["cdp.profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("segment_id", "profile_id"),
        schema="cdp",
    )
    op.create_index("idx_seg_members_profile", "segment_members", ["profile_id"], schema="cdp")

    # ─── destinations ────────────────────────────────────────────────────
    op.create_table(
        "destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="cdp",
    )

    # ─── activations ─────────────────────────────────────────────────────
    op.create_table(
        "activations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("profiles_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["segment_id"], ["cdp.segments.id"]),
        sa.ForeignKeyConstraint(["destination_id"], ["cdp.destinations.id"]),
        schema="cdp",
    )

    # ─── activation_events ───────────────────────────────────────────────
    op.create_table(
        "activation_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("activation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["activation_id"], ["cdp.activations.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["cdp.profiles.id"]),
        schema="cdp",
    )
    op.create_index("idx_act_events_activation", "activation_events", ["activation_id"], schema="cdp")
    op.create_index("idx_act_events_profile", "activation_events", ["profile_id"], schema="cdp")

    # ─── audit_log ───────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="cdp",
    )
    op.create_index("idx_audit_created", "audit_log", ["created_at"], schema="cdp", postgresql_using="btree")

    # ─── Trigger: auto-update profiles.updated_at ─────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION cdp.update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_profiles_updated_at
        BEFORE UPDATE ON cdp.profiles
        FOR EACH ROW EXECUTE FUNCTION cdp.update_updated_at()
    """)
    op.execute("""
        CREATE TRIGGER trg_segments_updated_at
        BEFORE UPDATE ON cdp.segments
        FOR EACH ROW EXECUTE FUNCTION cdp.update_updated_at()
    """)


def downgrade() -> None:
    op.execute("DROP SCHEMA cdp CASCADE")
