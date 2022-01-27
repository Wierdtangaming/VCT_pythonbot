class Bet:
  def __init__(self, code, match_id, user_id, bet_amount, team_num, date_created):
    self.code = code
    self.match_id = match_id
    self.user_id = user_id
    self.bet_amount = bet_amount
    self.team_num = int(team_num)
    self.date_created = date_created
    self.date_closed = None
    #team num of winner
    self.winner = 0
    self.message_ids = []

  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Match ID: " + str(self.match_id) + ", User ID: " + str(self.user_id) + ", Amount Bet: " + str(self.bet_amount) + ", Team Bet On: " + str(self.team_num) + ", Date Created: " + str(date_formatted) + ", Date Closed: " + str(self.date_closed) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)