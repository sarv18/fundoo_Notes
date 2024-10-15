"""Updated note model for collaborator

Revision ID: e5ce9770dc6f
Revises: ec326d863cb4
Create Date: 2024-10-15 10:27:42.217549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5ce9770dc6f'
down_revision: Union[str, None] = 'ec326d863cb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notes', 'collaborators')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notes', sa.Column('collaborators', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
