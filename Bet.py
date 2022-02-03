from dbinterface import get_from_list, add_to_list, replace_in_list, remove_from_list, get_all_objects


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

  def short_to_string(self):
    match = get_from_list("match", self.match_id)

    team = ""
    payout = 0.0
    if self.team_num == 1:
      team = match.t1
      payout = self.bet_amount * match.t1o - self.bet_amount
    elif self.team_num == 2:
      team = match.t2
      payout = self.bet_amount * match.t1o - self.bet_amount

    return f"Team: {team}, Amount: {self.bet_amount}, Payout: {int(round(payout, 5))}"
