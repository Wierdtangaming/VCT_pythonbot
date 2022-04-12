"""add a column

Revision ID: e0ae740e8088
Revises: 
Create Date: 2022-04-12 07:06:36.769795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0ae740e8088'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    print("1")
    #op.drop_column('bet', 'hidden')
    op.add_column('bet', sa.Column('hidden', sa.BOOLEAN(), nullable=False, server_default="false"))
    op.alter_column('bet','hidden', server_default=None)
    print("2")
    pass


def downgrade():
    op.drop_column('bet', 'hidden')
    pass

# alembic upgrade heads
# poetry run alembic upgrade heads