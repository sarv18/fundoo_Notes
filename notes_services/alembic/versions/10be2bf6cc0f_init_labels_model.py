"""Init labels model

Revision ID: 10be2bf6cc0f
Revises: 75801b783e63
Create Date: 2024-10-03 11:39:17.075094

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10be2bf6cc0f'
down_revision: Union[str, None] = '75801b783e63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('labels',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('color', sa.String(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_labels_id'), 'labels', ['id'], unique=False)
    op.create_index(op.f('ix_labels_user_id'), 'labels', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_labels_user_id'), table_name='labels')
    op.drop_index(op.f('ix_labels_id'), table_name='labels')
    op.drop_table('labels')
    # ### end Alembic commands ###
