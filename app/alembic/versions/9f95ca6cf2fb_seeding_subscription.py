"""seeding subscription

Revision ID: 9f95ca6cf2fb
Revises: ce9704c6c9e1
Create Date: 2024-02-26 13:10:02.867361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f95ca6cf2fb'
down_revision: Union[str, None] = 'ce9704c6c9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO subscriptions (subscription_name, product_id, price_id, subscription_amount, subscription_product_link, is_active, created_at, updated_at)
        VALUES 
        ('Silver package - 50 p/m', 'prod_PObofYE98g5BCv', 'price_1OZoaoEbLTf7azJEL5qS9EFs', '50', 'https://buy.stripe.com/test_14k7t66Vg7oF7qE7st', 'true', NOW(), NOW()),
        ('Gold package - 80 p/m', 'prod_PObsLnDzgWHWFK', 'price_1OZoeoEbLTf7azJEcfPQ8imD', '80', 'https://buy.stripe.com/test_dR6eVyfrM8sJaCQ3ce', 'true', NOW(), NOW());
    """)



def downgrade() -> None:
    pass
