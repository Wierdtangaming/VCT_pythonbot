from dbinterface import get_from_list

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

    #a tuple (balance, date created, date paid)
    
    self.loans = []

  def loan_bal(self):

    loan_amount = 0
    for loan in self.loans:
      if loan[2] == None:
        loan_amount += loan[0]
    
    return loan_amount
    
  def available(self):
    used = 0
    for bet_id in self.active_bet_ids:
      temp_bet = get_from_list("bet", bet_id)
      used += temp_bet.bet_amount

    return used

  def to_string(self):
    return "Balance: " + str(self.balance)