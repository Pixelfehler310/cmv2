"""add schema_version check constraint for dnd5e compendium definitions

Revision ID: 20260407_01
Revises: 20260328_01
Create Date: 2026-04-07 00:00:00

"""

from typing import Sequence, Union

from alembic import op  # type: ignore[attr-defined]


# revision identifiers, used by Alembic.
revision: str = "20260407_01"
down_revision: Union[str, Sequence[str], None] = "20260328_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("dnd5e_compendium_definitions") as batch_op:
        batch_op.create_check_constraint(
            "ck_dnd5e_compendium_definitions_schema_version",
            "schema_version >= 1",
        )


def downgrade() -> None:
    with op.batch_alter_table("dnd5e_compendium_definitions") as batch_op:
        batch_op.drop_constraint(
            "ck_dnd5e_compendium_definitions_schema_version",
            type_="check",
        )
