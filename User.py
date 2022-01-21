class User:
  def __init__(self, user_id, starting_bal):
    self.user_id = user_id
    self.balance = starting_bal
    self.bet_ids = []