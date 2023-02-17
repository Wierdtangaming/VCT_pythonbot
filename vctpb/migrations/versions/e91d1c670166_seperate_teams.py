"""seperate teams

Revision ID: e91d1c670166
Revises: 49008a61dc01
Create Date: 2023-02-14 15:32:48.837761

"""
from alembic import op
from sqlalchemy import Column, String, ForeignKey, Integer


# revision identifiers, used by Alembic.
revision = 'e91d1c670166'
down_revision = '49008a61dc01'
branch_labels = None
depends_on = None


def upgrade():
  # create a team table with name as primary key, 
  #   color_name that points to a color's primary key, 
  #   and color_hex that is constrained to the color's hex when color_name is not null
  op.create_table(
    'team',
    Column('name', String(50), primary_key=True, nullable=False),
    Column('vlr_code', Integer, unique=True),
    Column('color_name', String(32), ForeignKey('color.name')),
    Column('color_hex', String(6), nullable=False),
  )
  
  # create a tournament table with name as primary key, 
  #   color_name that points to a color's primary key, 
  #   and color_hex that is constrained to the color's hex when color_name is not null
  op.create_table(
    'tournament',
    Column('name', String(100), primary_key=True, nullable=False),
    Column('vlr_code', Integer, unique=True),
    Column('color_name', String(32), ForeignKey('color.name')),
    Column('color_hex', String(6), nullable=False),
  )
  
  # remove color_name from match and bet
  with op.batch_alter_table('match') as batch_op:
    batch_op.drop_column('color_name')
    #add vlr_code to match but it has to be unique
    batch_op.add_column(Column('vlr_code', Integer))
    batch_op.create_unique_constraint('u1_vlr_code', ['vlr_code'])
    
  with op.batch_alter_table('bet') as batch_op:
    batch_op.drop_column('color_name')
    
  # get all teams in matches t1, t2 and add to array
  teams = []
  for t1, t2 in op.get_bind().execute('SELECT t1, t2 FROM match').fetchall():
    if t1 not in teams:
      teams.append(t1)
    if t2 not in teams:
      teams.append(t2)
  print(teams)
  # insert all teams into team table
  for team in teams:
    op.execute(f'INSERT INTO team (name, color_hex) VALUES (\'{team}\', \'000000\')')
  
  # get all tournaments in matches and bets and add to array
  tournaments = []
  for tournament in op.get_bind().execute('SELECT tournament_name FROM match').fetchall():
    tournament = tournament[0]
    if tournament not in tournaments:
      tournaments.append(tournament)
  for tournament in op.get_bind().execute('SELECT tournament_name FROM bet').fetchall():
    tournament = tournament[0]
    if tournament not in tournaments:
      tournaments.append(tournament)
  print(tournaments)
  
  # insert all tournaments into tournament table
  for tournament in tournaments:
    op.execute(f'INSERT INTO tournament (name, color_hex) VALUES (\'{tournament}\', \'000000\')')
  
  with op.batch_alter_table('match') as batch_op:
    batch_op.create_foreign_key("fk_t1_name", 'team', ['t1'], ['name'])
    batch_op.create_foreign_key("fk_t2_name", 'team', ['t2'], ['name'])
    batch_op.create_foreign_key("fk_tournament_name", 'tournament', ['tournament_name'], ['name'])
    
  with op.batch_alter_table('bet') as batch_op:
    batch_op.create_foreign_key("fk_t1_name", 'team', ['t1'], ['name'])
    batch_op.create_foreign_key("fk_t2_name", 'team', ['t2'], ['name'])
    batch_op.create_foreign_key("fk_tournament_name", 'tournament', ['tournament_name'], ['name'])
    
  
def downgrade():
    pass
