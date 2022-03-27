from dbinterface import get_from_list
import math

class Bet:
  def __init__(self, code, match_id, user_id, bet_amount, team_num, date_created, t1, t2, tournament_name, color):
    
    self.t1 = t1
    self.t2 = t2
    self.tournament_name = tournament_name
    
    self.code = code
    self.match_id = match_id
    self.user_id = user_id
    self.bet_amount = bet_amount
    self.team_num = int(team_num)
    self.date_created = date_created

    self.color = color
    #team num of winner
    self.winner = 0
    self.message_ids = []

  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Match ID: " + str(self.match_id) + ", User ID: " + str(self.user_id) + ", Amount Bet: " + str(self.bet_amount) + ", Team Bet On: " + str(self.team_num) + ", Date Created: " + str(date_formatted) + ", Date Closed: " + str(self.date_closed) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)

  
  
  def get_team(self):
    if self.team_num == 1:
      return self.t1
    elif self.team_num == 2:
      return self.t2
    
  def get_match(self):
    return get_from_list("match", self.match_id)
    
  def get_team_and_payout(self):
    match = get_from_list("match", self.match_id)

    team = ""
    payout = 0.0
    print()
    if self.team_num == 1:
      team = match.t1
      payout = self.bet_amount * match.t1o - self.bet_amount
    elif self.team_num == 2:
      team = match.t2
      payout = self.bet_amount * match.t2o - self.bet_amount

    return(team, payout)

  def get_team_and_winner(self):

    team = ""
    winner = ""

    if self.team_num == 1:
      team = self.t1
    elif self.team_num == 2:
      team = self.t2

    if self.winner == 1:
      winner = self.t1
    elif self.winner == 2:
      winner = self.t2
    elif self.winner == 0:
      winner = "None"

    return(team, winner)

  async def short_to_string(self, bot):
    
    (team, payout) = self.get_team_and_payout()

    return f"User: <@!{self.user_id}>, Team: {team}, Amount: {self.bet_amount}, Payout: {int(math.floor(payout))}"

  async def basic_to_string(self, bot, match=None):
    if match is None:
      match = get_from_list("match", self.match_id)

    return f"Bet: {self.code}, User: <@!{self.user_id}>, Team: {self.get_team()}, Amount: {self.bet_amount}, Match ID: {match.code}"
  
  def balance_to_string(self, balance):
    
    match = get_from_list("match", self.match_id)
    (team, winner) = self.get_team_and_winner()

    return f"{match.t1} vs {match.t2}, Bet on: {team}, Winner: {winner}, Amount bet: {math.floor(self.bet_amount)}, Balance change: {math.floor(balance)}"

