"""subscription nulable

Revision ID: d47341398d0f
Revises: 9f95ca6cf2fb
Create Date: 2024-02-29 12:48:17.164795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd47341398d0f'
down_revision: Union[str, None] = '9f95ca6cf2fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user_subscription', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('user_subscription', 'subscription_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user_subscription', 'subscription_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('user_subscription', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
