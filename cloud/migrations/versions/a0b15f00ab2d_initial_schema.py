"""initial_schema

Revision ID: a0b15f00ab2d
Revises:
Create Date: 2026-06-06 15:34:06.638072

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "a0b15f00ab2d"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # TODO: 迁移到 PG 时，将 cloud/app/schema.py 的 SCHEMA_SQL 复制到此处
    # 并适配 PG 语法（AUTOINCREMENT -> SERIAL, TEXT dates -> TIMESTAMP）
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
