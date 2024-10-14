"""Update date model

Revision ID: 1ffae1733935
Revises: 2448436d8657
Create Date: 2024-10-10 12:42:37.610748

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ffae1733935'
down_revision: Union[str, None] = '2448436d8657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('note_label_association',
    sa.Column('note_id', sa.BigInteger(), nullable=False),
    sa.Column('label_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['label_id'], ['labels.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('note_id', 'label_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('note_label_association')
    # ### end Alembic commands ###
