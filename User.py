from dbinterface import get_from_list
import discord

class User:
  def __init__(self, code, color_code, date_created):
    self.code = code
    self.color_code = color_code

    #a tuple (bet_id, balance after change, date)
    #bet_id = id_[bet_id]: bet id
    #bet_id = award_[award_id]: awards
    #bet_id = start: start balance
    #bet_id = reset: changed balance with command
    
    self.balance = [("start", 500, date_created)]
    
    self.active_bet_ids = []

    #a tuple (balance, date created, date paid)
    
    self.loans = []

  def get_open_loans(self):
    open_loans = []
    for loan in self.loans:
      if loan[2] == None:
        open_loans.append(loan)
    return open_loans

  def loan_bal(self):

    loan_amount = 0
    loans = self.get_open_loans()
    if loans == 0:
      return 0
    for loan in loans:
      loan_amount += loan[0]
    
    return loan_amount

  def unavailable(self):
    used = 0
    for bet_id in self.active_bet_ids:
      temp_bet = get_from_list("bet", bet_id)
      used += temp_bet.bet_amount

    return used

  def get_balance(self):
    bal = self.balance[-1][1]
    bal -= self.unavailable()
    bal += self.loan_bal()
    return bal


  def avaliable_nonloan_bal(self):
    return self.balance[-1][1] - self.unavailable()



  def to_string(self):
    return "Balance: " + str(self.balance)



async def get_new_balance_changes(self, amount):
  if amount >= len(self.balance):
    amount = len(self.balance)
    before = 0
  new_balances = self.balance[-amount:]
  new_balances.reverse()
  before = self.balance[len(self.balance)-amount-1][1]

  embed = discord.Embed(title="Balance Log:", color=discord.Color.from_rgb(*tuple(int((self.color_code[0:8])[i : i + 2], 16) for i in (0, 2, 4))))

  for balance in new_balances:
    #a tuple (bet_id, balance after change, date)
    #bet_id = id_[bet_id]: bet id
    #bet_id = award_[award_id]: awards
    #bet_id = start: start balance
    #bet_id = reset_: changed balance with command
    balance_change = balance[1] - before
    if balance[0].starts_with("id_"):
      #bet id
      bet = get_from_list("bet", balance[0][3:])

      embed.add_field(name="Bet:" + bet.code, value=await bet.balance_to_string(balance_change), inline=False)
      
    elif balance[0].starts_with("award_"):
      text = f""
      if balance_change >= 0:
        text = f"{balance_change} added because {balance[0][6:]}"
      else:
        text = f"{-balance_change} removed because {balance[0][6:]}"
      embed.add_field(name="Award:", value=text, inline=False)
      #award
    elif balance[0] == "start":
      embed.add_field(name="Start Balance:", value=str(balance_change), inline=False)
      #start
    elif balance[0].starts_with("manual"):
      #should not be here
      print("why manual", str(balance))
      embed.add_field(name="Set To:", value=f"Manually set to {balance[1]}", inline=False)
    elif balance[0].starts_with("reset_"):
      #reset
      embed.add_field(name="Reset To:", value=f"Balance set to {balance[1]} because of a reset", inline=False)
    else:
      print("error condition not found", str(balance))
      embed.add_field(name=f"Invalid Balance Update {balance[0]}:", value=f"Balance set to {balance[1]} and changed by {balance_change}", inline=False)
    before = balance[1]
  return embed
