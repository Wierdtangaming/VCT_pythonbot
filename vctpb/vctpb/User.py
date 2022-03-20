from dbinterface import get_from_list, replace_in_list
import discord
import io
import matplotlib.pyplot as plt
from PIL import Image

class User:
  def __init__(self, code, username, color, date_created):
    self.code = code
    self.username = username
    self.color = color
    
    self.show_on_lb = True
    #a tuple (bet_id, balance after change, date)
    #bet_id = id_[bet_id]: bet id
    #bet_id = award_[award_id]: awards
    #bet_id = start: start balance
    #bet_id = reset: changed balance with command
    
    self.balance = [("start", 500, date_created)]
    
    self.active_bet_ids = []

    #a tuple (balance, date created, date paid)
    
    self.loans = []

  def active_bet_ids_bets(self):
    return [active_id[0] for active_id in self.active_bet_ids]

  def active_bet_ids_matches(self):
    return [active_id[1] for active_id in self.active_bet_ids]
  
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
    active_bet_ids_bets = self.active_bet_ids_bets()
    for bet_id in active_bet_ids_bets:
      temp_bet = get_from_list("bet", bet_id)
      if temp_bet == None:
        print(bet_id)
        ids = [t for t in self.active_bet_ids if bet_id == t[0]]
        for id in ids:
          self.active_bet_ids.remove(id)
        replace_in_list("user", self.code, self)
        continue
      used += temp_bet.bet_amount

    return used

  def get_balance(self):
    bal = self.balance[-1][1]
    bal -= self.unavailable()
    bal += self.loan_bal()
    return bal

  def get_clean_bal_loan(self):
    return self.balance[-1][1] + self.loan_bal()

  def avaliable_nonloan_bal(self):
    return self.balance[-1][1] - self.unavailable()

  def get_resets(self):
    return [i for i, x in enumerate(self.balance) if x[0].startswith("reset_")]
    
  def get_sets(self):
    set_list = [i for i, x in enumerate(self.balance) if (x[0].startswith("reset_") or x[0] == "start")]
    set_list.append(len(self.balance))
    return set_list
    
  def get_reset_range(self, index):
    resets = self.get_sets()
    if index == -1:
      return range(resets[len(resets)-2], resets[len(resets)-1])
      
    for reset in resets:
      rrange = range(reset, resets[1 + resets.index(reset)])
      if reset == len(self.balance)-1:
        return None
      if index in rrange:
        return rrange
    return None

  def get_to_reset_range(self, index):
    return range(index, self.get_reset_range(index).stop)

  def to_string(self):
    return "Balance: " + str(self.balance)

  def remove_balance_id(self, id):
    for balance in self.balance:
      if balance[0] == id:
        self.balance.remove(balance)
        break
    replace_in_list("user", self.code, self)

  
  def get_new_balance_changes_embeds(self, amount):

    if amount <= 0:
      return None
    if amount >= len(self.balance):
      amount = len(self.balance)
      before = 0
      
    sorted_balances = sorted(self.balance, key=lambda x: x[2])
    new_balances = self.balance[-amount:]
    new_balances = sorted(new_balances, key=lambda x: x[2])
    new_balances.reverse()
    before = self.balance[-2][1]
    embed_amount = int((amount - 1) / 25) + 1
    
    embeds = [discord.Embed(title=f"Balance Log Part {x + 1}:", color=discord.Color.from_rgb(*tuple(int((self.color)[i : i + 2], 16) for i in (0, 2, 4)))) for x in range(embed_amount)]
    embed_index = 0
    
    bal_index = 3
    print(len(embeds))
    for balance in new_balances:
      print(balance[0], embed_index)
      endex = int(embed_index / 25)
      #a tuple (bet_id, balance after change, date)
      #bet_id = id_[bet_id]: bet id
      #bet_id = award_[award_id]: awards
      #bet_id = start: start balance
      #bet_id = reset_: changed balance with command
      balance_change = balance[1] - before
      if balance[0].startswith("id_"):
        #bet id
        bet = get_from_list("bet", balance[0][3:])

        embeds[endex].add_field(name=f"Bet: {bet.code}", value=bet.balance_to_string(balance_change), inline=False)
        
      elif balance[0].startswith("award_"):
        text = f""
        if balance_change >= 0:
          text = f"{round(balance_change)} added because {balance[0][6:]}"
        else:
          text = f"{round(-balance_change)} removed because {balance[0][6:]}"
        embeds[endex].add_field(name="Award:", value=text, inline=False)
        #award
      elif balance[0] == "start":
        embeds[endex].add_field(name="Start Balance:", value=str(balance_change), inline=False)
        #start
      elif balance[0].startswith("manual"):
        #should not be here
        print("why manual", str(balance))
        embeds[endex].add_field(name="Set To:", value=f"Manually set to {balance[1]}", inline=False)
      elif balance[0].startswith("reset_"):
        #reset
        embeds[endex].add_field(name="Reset To:", value=f"Balance set to {balance[1]} because of {balance[0][6:]}", inline=False)
      else:
        embeds[endex].add_field(name=f"Invalid Balance Update {balance[0]}:", value=f"Balance set to {balance[1]} and changed by {balance_change}", inline=False)
        print("error condition not found", str(balance))
      if bal_index < len(sorted_balances):
        before = sorted_balances[-bal_index][1]
        bal_index += 1
      else:
        before = 0
      embed_index += 1
      
    if len(embeds) == 0:
      return None
    return embeds

  def get_graph_image(self, balance_range_ambig):
    if type(balance_range_ambig) == list:
      balances = balance_range_ambig
    elif type(balance_range_ambig) == str:
      if balance_range_ambig == "all":
        balances = self.balance
      elif balance_range_ambig == "current":
        balances = [self.balance[x] for x in self.get_reset_range(-1)]
      else:
        return None
    else:
      balances = [self.balance[x] for x in balance_range_ambig]

    print(len(balances))
      
    label = []
    balance = []
    colors = []
    line_colors = []
    before = None
    for bet_id, amount, date in balances:
      if not before == None:
        if amount > before:
          line_colors.append('g')
        elif amount < before:
          line_colors.append('r')
        else:
          line_colors.append('k')
      before = amount
      if bet_id.startswith('id_'):
        label.append(bet_id[3:])
        balance.append(amount)
        colors.append('b')
      elif bet_id.startswith('award_'):
        label.append(bet_id[6:])
        balance.append(amount)
        colors.append('xkcd:gold')
      elif bet_id == 'start':
        label.append('start')
        balance.append(amount)
        colors.append('k')
      elif bet_id.startswith('reset_'):
        label.append('reset')
        balance.append(amount)
        colors.append('k')
      else:
        label.append(bet_id)
        balance.append(amount)
        colors.append('k')
    
    #make a 800 x 800 figure
    fig, ax = plt.subplots(figsize=(8,8))
    #plot the balance
    for i in range(len(line_colors)-1):
      ax.plot([i, i+1], [balance[i], balance[i+1]], label=[label[i], ""], color=line_colors[i])
    
    llc = len(line_colors)
    ax.plot([llc-1, llc], [balance[llc-1], balance[llc]], label=[label[llc-1], label[llc]], color=line_colors[llc-1], zorder=1)
    ax.scatter(range(len(balances)), balance, s=30, color = colors, zorder=10)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    im = Image.open(buf)
    return im


    
def get_multi_graph_image(users, balance_range_ambig):
  all_balances = []
  for user in users:
    for balance in user.balance:
      all_balances.append((balance[0], balance[2]))

  all_balances = sorted(all_balances, key=lambda x: x[1])
  if type(balance_range_ambig) == str:
    if balance_range_ambig == "full":
      balances = self.balance
    elif balance_range_ambig == "current":
      balances = [self.balance[x] for x in self.get_reset_range(-1)]
    else:
      return None
  else:
    return None

  print(len(balances))
    
  label = []
  balance = []
  colors = []
  line_colors = []
  before = None
  for bet_id, amount, date in balances:
    if not before == None:
      if amount > before:
        line_colors.append('g')
      elif amount < before:
        line_colors.append('r')
      else:
        line_colors.append('k')
    before = amount
    if bet_id.startswith('id_'):
      label.append(bet_id[3:])
      balance.append(amount)
      colors.append('b')
    elif bet_id.startswith('award_'):
      label.append(bet_id[6:])
      balance.append(amount)
      colors.append('xkcd:gold')
    elif bet_id == 'start':
      label.append('start')
      balance.append(amount)
      colors.append('k')
    elif bet_id.startswith('reset_'):
      label.append('reset')
      balance.append(amount)
      colors.append('k')
    else:
      label.append(bet_id)
      balance.append(amount)
      colors.append('k')
  
  #make a 800 x 800 figure
  fig, ax = plt.subplots(figsize=(8,8))
  #plot the balance
  for i in range(len(line_colors)-1):
    ax.plot([i, i+1], [balance[i], balance[i+1]], label=[label[i], ""], color=line_colors[i])
  
  llc = len(line_colors)
  ax.plot([llc-1, llc], [balance[llc-1], balance[llc]], label=[label[llc-1], label[llc]], color=line_colors[llc-1], zorder=1)
  ax.scatter(range(len(balances)), balance, s=30, color = colors, zorder=10)
  
  buf = io.BytesIO()
  plt.savefig(buf, format='png')
  buf.seek(0)
  im = Image.open(buf)
  return im
    
