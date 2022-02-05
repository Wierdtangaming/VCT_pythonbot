class User:
  def __init__(self, code, color_code, date_created):
    self.code = code
    self.color_code = color_code

    #a tuple (bet_id, balance after change, date)
    #bet_id = id_[bet_id]: bet id
    #bet_id = award_[award_id]: awards
    #bet_id = start: start balance
    #bet_id = manual: changed balance with command
    #bet_id = reset: changed balance with command
    
    self.balance = [("start", 500, date_created)]
    
    self.active_bet_ids = []

    #a tuple (balance due, start balance, date)
    self.loans = []


  def to_string(self):
    return "Balance: " + str(self.balance)