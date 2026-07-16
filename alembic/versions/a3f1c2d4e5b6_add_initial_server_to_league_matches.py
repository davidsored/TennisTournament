"""add initial_server to league_matches

Revision ID: a3f1c2d4e5b6
Revises: 088fdecc7f16
Create Date: 2026-07-16 12:00:00.000000

Sacador inicial elegido en el marcador (1 = home, 2 = away). Nullable a
propósito: NULL significa "aún no elegido" para las filas existentes y para
los partidos nuevos hasta que el usuario responda al modal de saque.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3f1c2d4e5b6'
down_revision: Union[str, Sequence[str], None] = '088fdecc7f16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('league_matches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('initial_server', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('league_matches', schema=None) as batch_op:
        batch_op.drop_column('initial_server')
