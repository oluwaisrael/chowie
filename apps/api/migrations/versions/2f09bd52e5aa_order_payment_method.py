"""record customer payment choice"""

from alembic import op
import sqlalchemy as sa

revision = "2f09bd52e5aa"
down_revision = "9c2a49d6f48b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column("payment_method", sa.String(length=24), server_default="paystack", nullable=False),
    )
    op.create_check_constraint(
        "ck_orders_payment_method",
        "orders",
        "payment_method IN ('paystack','pay_on_delivery')",
    )


def downgrade():
    op.drop_constraint("ck_orders_payment_method", "orders", type_="check")
    op.drop_column("orders", "payment_method")
