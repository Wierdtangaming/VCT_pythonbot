from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqltypes import JSONLIST, DECIMAL
from sqlalchemy.ext.mutable import MutableList
from sqlaobjs import mapper_registry, Session
from utils import mix_colors, get_date, get_random_hex_color

@mapper_registry.mapped
class Match():
  
  __tablename__ = "match"
  
  code = Column(String(8), primary_key = True, nullable=False)
  vlr_code = Column(Integer)
  t1 = Column(String(50), ForeignKey("team.name"), nullable=False)
  team1 = relationship("Team", foreign_keys=[t1], back_populates="matches_as_t1")
  t2 = Column(String(50), ForeignKey("team.name"), nullable=False)
  team2 = relationship("Team", foreign_keys=[t2], back_populates="matches_as_t2")
  t1o = Column(DECIMAL(5, 3), nullable=False)
  t2o = Column(DECIMAL(5, 3), nullable=False)
  t1oo = Column(DECIMAL(5, 3), nullable=False)
  t2oo = Column(DECIMAL(5, 3), nullable=False)
  tournament_name = Column(String(100), ForeignKey("tournament.name"), nullable=False)
  tournament = relationship("Tournament", back_populates="matches")
  
  creator = relationship("User", back_populates="matches")
  odds_source = Column(String(50), nullable=False)
  winner = Column(Integer, nullable=False)
  color_hex = Column(String(6), nullable=False)
  creator_id = Column(Integer, ForeignKey("user.code"))
  creator = relationship("User", back_populates="matches")
  date_created = Column(DateTime(timezone = True), nullable=False)
  date_winner = Column(DateTime(timezone = True))
  date_closed = Column(DateTime(timezone = True))
  bets = relationship("Bet", back_populates="match", cascade="all, delete")
  message_ids = Column(MutableList.as_mutable(JSONLIST), nullable=False) #array of int
  
  @property
  def has_bets(self):
      return bool(self.bets)
  
  def __init__(self, code, t1, t2, t1o, t2o, t1oo, t2oo, tournament_name, odds_source, color_hex, creator_id, date_created, vlr_code=None):
    self.full__init__(code, t1, t2, t1o, t2o, t1oo, t2oo, tournament_name, 0, odds_source, color_hex, creator_id, date_created, None, None, [], vlr_code)
  
  def full__init__(self, code, t1, t2, t1o, t2o, t1oo, t2oo, tournament_name, winner, odds_source, color_hex, creator_id, date_created, date_winner, date_closed, message_ids, vlr_code=None):
    self.code = code
    self.t1 = t1
    self.t2 = t2
    self.t1o = t1o
    self.t2o = t2o
    self.t1oo = t1oo
    self.t2oo = t2oo
    self.tournament_name = tournament_name
    self.winner = winner
    self.odds_source = odds_source
    self.color_hex = color_hex
    self.creator_id = creator_id
    self.date_created = date_created
    self.date_winner = date_winner
    self.date_closed = date_closed
    self.message_ids = message_ids
    self.vlr_code = vlr_code
  
  
  def __repr__(self):
    return f"<Match {self.code}>"
  
  def set_color(self, session=None):
    if session is None:
      with Session.begin() as session:
        return self.set_color(hex, session)

    team1 = self.team1
    team2 = self.team2
    color = mix_colors([(team1.color_hex, 3), (team2.color_hex, 3), (self.tournament.color_hex, 1)])
    if color == self.color_hex:
      return
    self.color_hex = color
    
    for bet in self.bets:
      bet.set_color(session)
  
  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Teams: " + str(self.t1) + " vs " + str(self.t2) + ", Odds: " + str(self.t1o) + " / " + str(self.t2o) +  ", Old Odds: " + str(self.t1oo) + " / " + str(self.t2oo) + ", Tournament Name: " + str(self.tournament_name) + ", Odds Source: " + str(self.odds_source) + ", Created On: " + str(date_formatted) + ", Date Closed: " + str(self.date_closed) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)


  def short_to_string(self):
    return "Teams: " + str(self.t1) + " vs " + str(self.t2) + ", Odds: " + str(self.t1o) + " / " + str(self.t2o)

  def winner_name(self):
    if self.winner == 0:
      return "None"
    elif self.winner == 1:
      return self.t1
    else:
      return self.t2

  def basic_to_string(self):
    return f"Match: {self.code}, Teams: {self.t1} vs {self.t2}, Odds: {self.t1o} vs {self.t2o}, Tournament Name: {self.tournament_name}"
  
  async def close(self, bot, ctx=None, session=None):
    from objembed import create_bet_list_embedded, create_match_embedded, create_bet_embedded
    from convert import edit_all_messages
    self.date_closed = get_date()
    old_hidden = []
    for bet in self.bets:
      if bet.hidden == True:
        bet.hidden = False
        bet.set_color(session)
        old_hidden.append(bet)
    embedd = create_match_embedded(self, "Closed Match: {self.t1} vs {self.t2}, {self.t1o} / {self.t2o}.", session)
    if ctx is not None:
      await ctx.respond(content=f"{self.t1} vs {self.t2} betting has closed.", embeds=[embedd, create_bet_list_embedded(f"All bets on {self.t1} vs {self.t2}:", self.bets, True, session)])
    await edit_all_messages(bot, self.message_ids, embedd)
    for bet in old_hidden:
      embedd = create_bet_embedded(bet, "Placeholder", session)
      await edit_all_messages(bot, bet.message_ids, embedd)
    
  
  
  async def set_winner(self, team_num, bot, ctx=None, session=None):
    if session is None:
      with Session.begin() as session:
        return await self.set_winner(team_num, bot, ctx, session)
    from objembed import create_match_embedded, create_bet_embedded, create_payout_list_embedded
    from dbinterface import get_all_db, get_channel_from_db
    from User import add_balance_user, get_first_place
    from convert import edit_all_messages
    
    time = get_date()
    
    self.date_winner = time
    if self.date_closed is None:
      self.date_closed = time
      
    if (team_num == 1) or (team_num == "1") or (team_num == self.t1):
      team_num = 1
    elif (team_num == 2) or (team_num == "2") or (team_num == self.t2):
      team_num = 2
    else:
      if ctx is not None:
        await ctx.respond(f"Invalid team name of {team_num} please enter {self.t1} or {self.t2}.", ephemeral = True)
      print(f"Invalid team name of {team_num} please enter {self.t1} or {self.t2}.")
      return
    
    if int(self.winner) != 0:
      if ctx is not None:
        await ctx.respond(f"Winner has already been set to {self.winner_name()}", ephemeral = True)
      print(f"Winner has already been set to {self.winner_name()}")
      return
    
    self.winner = team_num
    m_embedd = create_match_embedded(self, "Placeholder", session)
    
    odds = 0.0
    #change when autocomplete
    if team_num == 1:
      odds = self.t1o
      winner_msg = f"Winner has been set to {self.t1}."
    else:
      odds = self.t2o
      winner_msg = f"Winner has been set to {self.t2}."

    users = get_all_db("User", session)
    leader = get_first_place(users)
    msg_ids = []
    bet_user_payouts = []
    date = get_date()
    new_users = []
    for bet in self.bets:
      bet.winner = int(self.winner)
      bet.hidden = False
      payout = -bet.amount_bet
      if bet.team_num == team_num:
        payout += bet.amount_bet * odds
      user = bet.user
      new_users.append(user)
      add_balance_user(user, payout, "id_" + str(bet.code), date, session)
      while user.loan_bal() != 0 and user.get_clean_bal_loan() > 500:
        user.pay_loan(date)
      embedd = create_bet_embedded(bet, "Placeholder", session)
      msg_ids.append((bet, embedd))
      bet_user_payouts.append((bet, user, payout))

    new_leader = get_first_place(users)

    embedd = create_payout_list_embedded(f"Payouts of {self.t1} vs {self.t2}:", self, bet_user_payouts)
    channel = await bot.fetch_channel(get_channel_from_db("match", session))
    if ctx is not None:
      await ctx.respond(content=winner_msg, embed=embedd)
    else:
      if channel is not None:
        await channel.send(content=winner_msg, embed=embedd)
        
    if new_leader != leader:
      if channel is not None:
        if new_leader == None:
          await channel.send(f"leader is now tied.")
        else:
          await channel.send(f"{new_leader.username} is now the leader.")
        
      if leader != None:
        print(f"{leader.color_hex} == dbb40c, {leader.has_leader_profile()}")
        if leader.has_leader_profile():
          print("start")
          leader.set_color(get_random_hex_color(), session)
    await edit_all_messages(bot, self.message_ids, m_embedd)
    [await edit_all_messages(bot, tup[0].message_ids, tup[1], (f"Bet: {tup[0].user.username}, {tup[0].amount_bet} on {tup[0].get_team()}")) for tup in msg_ids]
  
def is_valid_match(code, t1, t2, t1o, t2o, t1oo, t2oo, tournament_name, odds_source, winner, color, creator_id, date_created, date_winner, date_closed, bet_ids, message_ids):
  errors = [False for _ in range(17)]
  if isinstance(code, str) == False or len(code) != 8:
    errors[0] = True
    print("code", code, type(code))
  if isinstance(t1, str) == False or len(t1) > 50:
    errors[1] = True
    print("t1", t1, type(t1))
  if isinstance(t2, str) == False or len(t2) > 50:
    errors[2] = True
    print("t2", t2, type(t2))
  if isinstance(t1o, Decimal) == False or t1o < 0:
    errors[3] = True
    print("t1o", t1o, type(t1o))
  if isinstance(t2o, Decimal) == False or t2o < 0:
    errors[4] = True
    print("t2o", t2o, type(t2o))
  if isinstance(t1oo, Decimal) == False or t1oo < 0:
    errors[5] = True
    print("t1oo", t1oo, type(t1oo))
  if isinstance(t2oo, Decimal) == False or t2oo < 0:
    errors[6] = True
    print("t2oo", t2oo, type(t2oo))
  if isinstance(tournament_name, str) == False or len(tournament_name) > 100:
    errors[7] = True
    print("tournament_name", tournament_name, type(tournament_name))
  if isinstance(odds_source, str) == False or len(odds_source) > 50:
    errors[8] = True
    print("odds_source", odds_source, type(odds_source))
  if isinstance(winner, int) == False or winner < 0 or winner > 2:
    errors[9] = True
    print("winner", winner, type(winner))
  if isinstance(color, str) == False or len(color) > 6:
    errors[10] = True
    print("color", color, type(color))
  if isinstance(creator_id, int) == False:
    errors[11] = True
    print("creator", creator_id, type(creator_id))
  if isinstance(date_created, datetime) == False:
    errors[12] = True
    print("date_created", date_created, type(date_created))
  if isinstance(date_winner, datetime) == False:
    errors[13] = True
    print("date_winner", date_winner, type(date_winner))
  if isinstance(date_closed, datetime) == False:
    errors[14] = True
    print("date_closed", date_closed, type(date_closed))
  if isinstance(bet_ids, list) == False:
    errors[15] = True
    print("bet_ids", bet_ids, type(bet_ids))
  if isinstance(message_ids, list) == False:
    errors[16] = True
    print("message_ids", message_ids, type(message_ids))

  return errors
