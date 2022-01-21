class Bet:
  def __init__(self, id, match_id, user_id, bet_amount, team_num, date_created, editable):
    self.id = id
    self.match_id = match_id
    self.user_id = user_id
    self.bet_amount = bet_amount
    self.team_num = team_num