"""bet add hidden

Revision ID: 49008a61dc01
Revises: 
Create Date: 2022-04-12 16:02:10.864335

"""
from alembic import op
from sqlalchemy import Column, BOOLEAN


# revision identifiers, used by Alembic.
revision = '49008a61dc01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
	with op.batch_alter_table('bet') as batch_op:
		batch_op.add_column(Column('hidden', BOOLEAN, nullable=False, default=False))
		batch_op.alter_column('hidden', default=None)



def downgrade():
	with op.batch_alter_table('bet') as batch_op:
		batch_op.drop_column('hidden')
