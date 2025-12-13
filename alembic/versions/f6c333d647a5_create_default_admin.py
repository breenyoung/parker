"""create default admin

Revision ID: f6c333d647a5
Revises: 23bc0e2cee25
Create Date: 2025-12-13 11:50:24.008539

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from passlib.hash import bcrypt



# revision identifiers, used by Alembic.
revision: str = 'f6c333d647a5'
down_revision: Union[str, None] = '23bc0e2cee25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    users = table(
        'users',
        column('id', sa.Integer),
        column('username', sa.String),
        column('password', sa.String),
        column('is_admin', sa.Boolean),
    )

    # Insert only if table is empty
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM users"))
    count = result.scalar()

    if count == 0:
        conn.execute(
            users.insert().values(
                username="admin",
                password=bcrypt.hash("admin"),
                is_admin=True
            )
        )



def downgrade() -> None:
    pass
