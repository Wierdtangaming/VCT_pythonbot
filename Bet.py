from dbinterface import get_from_list, add_to_list, replace_in_list, remove_from_list, get_all_objects, smart_get_user
import math

class Bet:
  def __init__(self, code, match_id, user_id, bet_amount, team_num, date_created):
    self.code = code
    self.match_id = match_id
    self.user_id = user_id
    self.bet_amount = bet_amount
    self.team_num = int(team_num)
    self.date_created = date_created
    #team num of winner
    self.winner = 0
    self.message_ids = []

  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Match ID: " + str(self.match_id) + ", User ID: " + str(self.user_id) + ", Amount Bet: " + str(self.bet_amount) + ", Team Bet On: " + str(self.team_num) + ", Date Created: " + str(date_formatted) + ", Date Closed: " + str(self.date_closed) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)



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

  def get_team_and_winner(self, match):

    team = ""
    winner = ""

    if self.team_num == 1:
      team = match.t1
    elif self.team_num == 2:
      team = match.t2

    if self.winner == 1:
      winner = match.t1
    elif self.winner == 2:
      winner = match.t2
    elif self.winner == 0:
      winner = "None"

    return(team, winner)

  async def short_to_string(self, bot):
    
    (team, payout) = self.get_team_and_payout()

    return f"User: {(await smart_get_user(self.user_id, bot)).mention}, Team: {team}, Amount: {self.bet_amount}, Payout: {int(math.floor(payout))}"

  async def balance_to_string(self, balance):
    
    match = get_from_list("match", self.match_id)
    (team, winner) = self.get_team_and_winner(match)

    return f"{match.t1} vs {match.t2}, Bet on: {team}, Winner: {winner}, Amount bet: {math.floor(self.bet_amount)}, Balance change: {math.floor(balance)}"

