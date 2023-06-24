"""Add alert

Revision ID: e38bf530c0ed
Revises: d10a938363d7
Create Date: 2023-06-24 09:12:07.578649

"""
from alembic import op
from sqlalchemy import Column, ForeignKey, Boolean, false, String

# revision identifiers, used by Alembic.
revision = 'e38bf530c0ed'
down_revision = 'd10a938363d7'
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
    "alert_association_table",
    Column("user_id", String(8), ForeignKey("user.id"), primary_key=True),
    Column("tournament_id", String(100), ForeignKey("tournament.id"), primary_key=True),
  )
  with op.batch_alter_table('match') as batch_op:
    batch_op.add_column(Column('alert', Boolean, nullable=False, server_default=false()))
    
  pass


def downgrade():
  pass
