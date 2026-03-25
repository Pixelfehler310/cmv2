from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy import inspect, text


logger = logging.getLogger("schema_migrations")

MigrationFn = Callable[[object], None]


def apply_schema_migrations(sync_conn) -> None:
    """Apply idempotent, versioned schema migrations.

    This provides a minimal migration baseline for MVP environments that do not
    yet run Alembic while keeping startup deterministic across restarts.
    """

    _ensure_schema_migrations_table(sync_conn)
    applied = _get_applied_versions(sync_conn)

    migrations: list[tuple[str, MigrationFn]] = [
        ("20260325_01_integrity_hardening", _migration_integrity_hardening),
    ]

    for version, migration in migrations:
        if version in applied:
            continue
        migration(sync_conn)
        _record_applied_version(sync_conn, version)
        logger.info("Applied schema migration: %s", version)


def _ensure_schema_migrations_table(sync_conn) -> None:
    sync_conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migration_versions (
                version VARCHAR PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _get_applied_versions(sync_conn) -> set[str]:
    rows = sync_conn.execute(
        text("SELECT version FROM schema_migration_versions")
    ).fetchall()
    return {str(row[0]) for row in rows}


def _record_applied_version(sync_conn, version: str) -> None:
    sync_conn.execute(
        text(
            "INSERT INTO schema_migration_versions (version) VALUES (:version)"
        ),
        {"version": version},
    )


def _migration_integrity_hardening(sync_conn) -> None:
    inspector = inspect(sync_conn)
    table_names = set(inspector.get_table_names())
    dialect = sync_conn.dialect.name

    if "user_social_auths" in table_names:
        _dedupe_user_social_auths(sync_conn)
        sync_conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_user_social_auths_provider_provider_user_id
                ON user_social_auths(provider, provider_user_id)
                """
            )
        )

    if "campaign_members" in table_names:
        _dedupe_campaign_members(sync_conn)
        sync_conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_campaign_members_campaign_id_user_id
                ON campaign_members(campaign_id, user_id)
                """
            )
        )

    if dialect == "postgresql":
        if "items" in table_names:
            sync_conn.execute(
                text(
                    """
                    ALTER TABLE items
                    ALTER COLUMN weight TYPE DOUBLE PRECISION
                    USING weight::double precision
                    """
                )
            )

        if "monsters" in table_names:
            sync_conn.execute(
                text(
                    """
                    ALTER TABLE monsters
                    ALTER COLUMN challenge_rating TYPE DOUBLE PRECISION
                    USING challenge_rating::double precision
                    """
                )
            )
    else:
        logger.info(
            "Skipping numeric column type coercion migration for dialect=%s; ORM model types still updated.",
            dialect,
        )


def _dedupe_user_social_auths(sync_conn) -> None:
    sync_conn.execute(
        text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY provider, provider_user_id
                        ORDER BY created_at ASC, id ASC
                    ) AS row_num
                FROM user_social_auths
                WHERE provider IS NOT NULL
                  AND provider_user_id IS NOT NULL
            )
            DELETE FROM user_social_auths
            WHERE id IN (
                SELECT id
                FROM ranked
                WHERE row_num > 1
            )
            """
        )
    )


def _dedupe_campaign_members(sync_conn) -> None:
    sync_conn.execute(
        text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY campaign_id, user_id
                        ORDER BY created_at ASC, id ASC
                    ) AS row_num
                FROM campaign_members
                WHERE campaign_id IS NOT NULL
                  AND user_id IS NOT NULL
            )
            DELETE FROM campaign_members
            WHERE id IN (
                SELECT id
                FROM ranked
                WHERE row_num > 1
            )
            """
        )
    )
