"""Add result channel id

Revision ID: d10a938363d7
Revises: e91d1c670166
Create Date: 2023-06-24 08:44:48.138538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd10a938363d7'
down_revision = 'e91d1c670166'
branch_labels = None
depends_on = None


def upgrade():
  with op.batch_alter_table('channels') as batch_op:
    batch_op.add_column(sa.Column('result_channel_id', sa.Integer(), nullable=True))


def downgrade():
  with op.batch_alter_table('channels') as batch_op:
    batch_op.drop_column('result_channel_id')
