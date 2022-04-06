import discord
import io
import matplotlib.pyplot as plt
import matplotlib as mpl
from PIL import Image
from decimal import Decimal
import random
import math
import secrets
import sys
from sqlalchemy import Column, String, BOOLEAN, ForeignKey
from sqlalchemy.orm import relationship
from sqltypes import JSONLIST
from sqlalchemy.ext.mutable import MutableList
from sqlaobjs import mapper_registry, Session

@mapper_registry.mapped
class User():
  __tablename__ = "user"
  
  code = Column(String(8), primary_key=True)
  username = Column(String(32), nullable=False)
  color_name = Column(String(32), ForeignKey("color.name"))
  color = relationship("Color", back_populates="users")
  color_hex = Column(String(6), nullable=False)
  hidden = Column(BOOLEAN, nullable=False)
  balances = Column(MutableList.as_mutable(JSONLIST), nullable=False) #array of Tuple(bet_id, balance after change, date)
  active_bets = relationship("Bet", primaryjoin="and_(Bet.user_id == User.code, Bet.winner == 0)", overlaps="active_bets, user", cascade="all, delete")
  loans = Column(MutableList.as_mutable(JSONLIST), nullable=False) #array of Tuple(balance, date created, date paid)
  bets = relationship("Bet", back_populates="user", cascade="all, delete", overlaps="active_bets, user")
  matches = relationship("Match", back_populates="creator")
  
  def __init__(self, code, username, color, date_created):
    self.code = code
    self.username = username
    self.set_color(color)
    
    self.hidden = True
    #a tuple (bet_id, balances after change, date)
    #if change is None then it is a reset
    #bet_id = id_[bet_id]: bet id
    #bet_id = award_[award_id]_[name]: awards
    #bet_id = start: start balances
    #bet_id = reset_[reset_id]_[reset_name]: changed balances with command
    
    self.balances = [("start", Decimal(500), date_created)]

    #a tuple (balances, date created, date paid)
    
    self.loans = []

  def __init__(self, code, username, color, hidden, balances, loans):
    self.code = code
    self.username = username
    self.set_color(color)
    self.hidden = hidden
    self.balances = balances
    self.loans = loans
  
  def set_color(self, color):
    if isinstance(color, str):
      self.color_name = None
      self.color_hex = color
      return
    
    self.color_name = color.name
    self.color_hex = color.hex
  
  def __repr__(self):
    return f"<User {self.code}, {self.username}>"

  def get_unique_code(self, prefix):
    #test
    #test
    #test
    #test
    #test
    #test
    #test
    #combine all_bal into one array
    prefix_bal = [x for x in self.balances if x[0].startswith(prefix)]
    codes = [bal[0][len(prefix):len(prefix)+8] for bal in prefix_bal]
    for bal in self.balances:
      split = bal.split("_")
      if len(split) > 1:
        codes.append(split[1])
    print(codes)
    for code in codes:
      if len(code) != 8:
        print(code)
        quit()
    code = ""
    copy = True
    while copy:
      copy = False

      random.seed()
      code = str(secrets.token_hex(4))
      for k in codes:
        if k == code:
          copy = True
    return code

  
  def get_open_loans(self):
    open_loans = []
    for loan in self.loans:
      if loan[2] is None:
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

  def unavailable(self, session=None):
    if session is None:
      with Session.begin() as session:
        return self.unavailable(session)
      
    used = 0
    bets = self.active_bets
    
    for bet in bets:
      used += bet.amount_bet

    return used

  def get_balance(self, session=None):
    bal = self.balances[-1][1]
    bal -= self.unavailable(session)
    bal += self.loan_bal()
    return bal

  def get_clean_bal_loan(self):
    return self.balances[-1][1] + self.loan_bal()

  def avaliable_nonloan_bal(self, session=None):
    return self.balances[-1][1] - self.unavailable(session)

  def get_resets(self):
    return [i for i, x in enumerate(self.balances) if x[0].startswith("reset_")]
    
  def get_sets(self):
    set_list = [i for i, x in enumerate(self.balances) if (x[0].startswith("reset_") or x[0] == "start")]
    set_list.append(len(self.balances))
    return set_list
    
  def get_reset_range(self, index):
    resets = self.get_sets()
    if index == -1:
      return range(resets[len(resets)-2], resets[len(resets)-1])
      
    for reset in resets:
      rrange = range(reset, resets[1 + resets.index(reset)])
      if reset == len(self.balances)-1:
        return None
      if index in rrange:
        return rrange
    return None

  def get_to_reset_range(self, index):
    return range(index, self.get_reset_range(index).stop)

  def to_string(self):
    return "Balance: " + str(self.balances)

  def remove_balance_id(self, id):
    for balance in self.balances:
      if balance[0] == id:
        self.balances.remove(balance)
        break
    replace_in_list("User", self.code, self)

  def change_award_name(self, award_label, name, session=None):
    if session is None:
      with Session.begin() as session:
        self.change_award_name(award_label, name, session=session)
    for balance in self.balances:
      if balance[0].startswith("award_") and balance[0][6:14] == award_label[-8:]:
        self.balances[self.balances.index(balance)] = (balance[0][:15] + name, balance[1], balance[2])
        break
    else:
      return None
    return self
  
  
  def get_award_strings(self):
    last_amount = Decimal(0)
    awards_id_changes = []
    for balance_t in self.balances:
      if balance_t[0].startswith("award"):
        awards_id_changes.append((balance_t[0], balance_t[1]-last_amount))
      last_amount = balance_t[1]
    
    award_labels = []
    for awards_id_change in awards_id_changes:
      label = f"{awards_id_change[0][15:]}, {math.floor(awards_id_change[1])}, ID: {awards_id_change[0][6:14]}"
      if len(label) >= 99:
        label = f"{awards_id_change[0][15:80]}..., {math.floor(awards_id_change[1])}, ID: {awards_id_change[0][6:14]}"
      award_labels.append(label)
      
    return award_labels
  
  def get_new_balance_changes_embeds(self, amount):
    if amount <= 0:
      return None
    if amount >= len(self.balances):
      amount = len(self.balances)
      before = 0
      
    sorted_balances = sorted(self.balances, key=lambda x: x[2])
    new_balances = self.balances[-amount:]
    new_balances = sorted(new_balances, key=lambda x: x[2])
    new_balances.reverse()
    before = self.balances[-2][1]
    embed_amount = int((amount - 1) / 25) + 1
    
    embeds = [discord.Embed(title=f"Balance Log Part {x + 1}:", color=discord.Color.from_rgb(*tuple(int((self.color)[i : i + 2], 16) for i in (0, 2, 4)))) for x in range(embed_amount)]
    embed_index = 0
    
    bal_index = 3
    
    for balance in new_balances:
      endex = int(embed_index / 25)
      
      balance_change = balance[1] - before
      if balance[0].startswith("id_"):
        #bet id
        bet = get_from_list("Bet", balance[0][3:])

        embeds[endex].add_field(name=f"Bet: {bet.code}", value=bet.balance_to_string(balance_change), inline=False)
        
      elif balance[0].startswith("award_"):
        text = f""
        if balance_change >= 0:
          text = f"{round(balance_change)} added because {balance[0][15:]}"
        else:
          text = f"{round(-balance_change)} removed because {balance[0][15:]}"
        embeds[endex].add_field(name="Award:", value=text, inline=False)
        #award
      elif balance[0] == "start":
        embeds[endex].add_field(name="Start balance:", value=str(balance_change), inline=False)
        #start
      elif balance[0].startswith("manual"):
        #should not be here
        print("why manual", str(balance))
        embeds[endex].add_field(name="Set To:", value=f"Manually set to {balance[1]}", inline=False)
      elif balance[0].startswith("reset_"):
        #reset
        embeds[endex].add_field(name="Reset:", value=f"Balance set to {round(balance[1])} because of {balance[0][15:]}", inline=False)
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
    xlabel = ""
    if isinstance(balance_range_ambig, list):
      balance = balance_range_ambig
    elif isinstance(balance_range_ambig, str):
      if balance_range_ambig == "all":
        balance = self.balances
        xlabel = "All Time"
      elif balance_range_ambig == "current":
        balance = [self.balances[x] for x in self.get_reset_range(-1)]
        resets = self.get_resets()
        if len(resets) > 0:
          xlabel = self.balances[resets[-1]][0][15:]
        else:
          users = get_all_objects("user")
          for user in users:
            resets = user.get_resets()
            if len(resets) > 0:
              xlabel = user.balance[resets[-1]][0][15:]
              break
    elif isinstance(balance_range_ambig, int):
      balance = self.balances[-balance_range_ambig:]
      xlabel = f"Last {balance_range_ambig}"
    else:
      return f"Invalid range of {balance_range_ambig}."
      
    labels = []
    label_colors = []
    balances = []
    colors = []
    line_colors = []
    resets = []
    before = None
    min = 0
    max = 500
    for bet_id, amount, date in balance:
      if amount < min:
        min = amount
      if amount > max:
        max = amount
      if not before is None:
        if amount > before:
          line_colors.append('g')
        elif amount < before:
          line_colors.append('r')
        else:
          line_colors.append('k')
      before = amount
      if bet_id.startswith('id_'):
        bet = get_from_list("Bet", bet_id[3:])
        match = bet.get_match()
        t1 = match.t1
        t2 = match.t2
        if match.winner == 1:
          t1 = fr"$\bf{t1}$"
        elif match.winner == 2:
          t2 = fr"$\bf{t2}$"
        label = f"{t1} vs {t2}"
        labels.append(label)
        label_colors.append(f"#{match.color}")
        balances.append(amount)
        colors.append('b')
        last_id = f"id_{match.code}"
      elif bet_id.startswith('award_'):
        label = bet_id[15:]
        if len(label) > 40:
          label = label.split(":")[-1]
          if len(label) > 40:
            if label.lower().endswith("pick'em") or label.lower().endswith("pick’em"):
              label = "Pick'em"
            else:
              label = bet_id[6:14]
        labels.append(label)
        label_colors.append('xkcd:gold')
        balances.append(amount)
        colors.append('xkcd:gold')
      elif bet_id == 'start':
        labels.append('start')
        label_colors.append('k')
        balances.append(amount)
        colors.append('k')
      elif bet_id.startswith('reset_'):
        label = bet_id[15:]
        labels.append(label)
        label_colors.append('k')
        if len(line_colors) != 0:
          resets.append(len(line_colors))
          line_colors[-1] = None
        balances.append(amount)
        colors.append('k')
      else:
        labels.append(bet_id)
        label_colors.append('k')
        balances.append(amount)
        colors.append('k')
    
    #make a 800 x 800 figure
    #fig, ax = plt.subplots(figsize=(8,8))
    #plot the balances
    x_length = len(balances) / 6.5 + 0.8
    if x_length < 8:
      x_length = 8
    plt.clf()
    with mpl.rc_context({"figure.figsize": (x_length,8), 'figure.dpi': 200, 'figure.autolayout': True}):
      fig, ax = plt.subplots()
      for i in range(len(line_colors)):
        if line_colors[i] is None:
          continue
        ax.plot([i, i+1], [balances[i], balances[i+1]], color=line_colors[i])
      ax.axhline(y=0, color='grey', linestyle='--')
      max = int(math.ceil((max * Decimal("1.05")) / Decimal("100"))) * 100
      if min != 0:
        min = int(math.floor((min - max * Decimal("0.05")) / Decimal("100"))) * 100

      x = [*range(len(balances))]
      ax.fill_between(x, 0, 1, where=[((xs in resets) or ((xs+1) in resets)) for xs in x], color='grey', alpha=0.5, transform=ax.get_xaxis_transform())

      ax.set_ylim([min, max])
      #plt.scatter(range(len(balances)), balances, s=30, color = colors, zorder=10)
      ax.set_xticks(range(len(balances)), labels, rotation='vertical')
      ax.set_xlabel(xlabel)

      for ticklabel, tickcolor in zip(ax.get_xticklabels(), label_colors):
        ticklabel.set_color(tickcolor)

      ax.xaxis.grid(linestyle=':')

      ax.margins(x=1/((x_length-0.8)*6))

      plt.tight_layout()
      fig_width, fig_height = fig.get_size_inches()
      fig.set_size_inches(x_length, fig_height)

      buf = io.BytesIO()
      plt.savefig(buf, format='png')
      buf.seek(0)
      im = Image.open(buf)
      print(sys.getsizeof(im.tobytes()))
      #if sys.getsizeof(im.tobytes()):


      return im
  

    
def get_multi_graph_image(users, balance_range_ambig):
  all_balances = []
  xlabel = ""
  if type(balance_range_ambig) == str:
    if balance_range_ambig == "all":
      xlabel = "All Time"
      for i, user in enumerate(users):
        for balance in user.balances:
          all_balances.append((i, balance))
    elif balance_range_ambig == "current":
      for i, user in enumerate(users):
        for balance_index in user.get_reset_range(-1):
          all_balances.append((i, user.balances[balance_index]))
      for user in users:
        resets = user.get_resets()
        if len(resets) > 0:
          xlabel = user.balances[resets[-1]][0][15:]
          break
  elif isinstance(balance_range_ambig, int):
    for i, user in enumerate(users):
      for balance in user.balances:
        all_balances.append((i, balance))
    xlabel = f"Last {balance_range_ambig}"
  else:
    return f"invalid range of {balance_range_ambig}"
  
  all_balances = sorted(all_balances, key=lambda x: x[1][2])
  
  if isinstance(balance_range_ambig, int):
    unique = 0
    x = 0
    last = None
    #for all_balances reversed
    for balance in all_balances[::-1]:
      if balance[1][0] != last:
        unique += 1
      last = balance[1][0]
      if unique > balance_range_ambig:
        break
      x += 1
    all_balances = all_balances[-x:]

  
  x = []
  y = []
  labels = []
  label_colors = []
  user_color = [user.color for user in users]
  lines_x = [[] for _ in users]
  lines_y = [[] for _ in users]
  resets = [[] for _ in users]
  reset_breaks = [0]
  xval = -1
  last_id = None
  for user_index, balance in all_balances:
    bet_id, amount = balance[:2]

    if bet_id.startswith('id_'):
      bet = get_from_list("Bet", bet_id[3:])
      match = bet.get_match()
      bet_id = f"id_{match.code}"

    if not last_id == bet_id:
      xval += 1
      last_id = bet_id
      if bet_id.startswith('id_'):
        t1 = match.t1
        t2 = match.t2
        if match.winner == 1:
          t1 = fr"$\bf{t1}$"
        elif match.winner == 2:
          t2 = fr"$\bf{t2}$"
        label = f"{t1} vs {t2}"
        labels.append(label)
        label_colors.append(f"#{match.color}")
        last_id = f"id_{match.code}"
      elif bet_id.startswith('award_'):
        label = bet_id[15:]
        if len(label) > 40:
          label = label.split(":")[-1]
          if len(label) > 40:
            if label.lower().endswith("pick'em") or label.lower().endswith("pick’em"):
              label = "Pick'em"
            else:
              label = bet_id[6:14]
              
        labels.append(label)
        label_colors.append('xkcd:gold')
      elif bet_id == 'start':
        labels.append('start')
        label_colors.append('k')
      elif bet_id.startswith('reset_'):
        label = bet_id[15:]
        labels.append(label)
        label_colors.append('k')
        reset_breaks.append(xval)
      else:
        labels.append(bet_id)
        label_colors.append('k')
    
    if bet_id.startswith('reset_'):
      resets[user_index].append((len(lines_x[user_index]), xval))

    x.append(xval)
    y.append(amount)
    lines_x[user_index].append(xval)
    lines_y[user_index].append(amount)
  x_length = (xval+1) / 6.5 + 0.8
  if x_length < 8:
    x_length = 8
  
  if reset_breaks[:2] == [0, 0]:
    reset_breaks = [0]
    
  for reset in resets:
    if len(reset) > 0:
      if reset[0] == (0,0):
        reset.pop(0)
    
  plt.clf()
  with mpl.rc_context({"figure.figsize": (x_length,8), 'figure.dpi': 200, 'figure.autolayout': True}):
    fig, ax = plt.subplots()
    for user_index, line_x in enumerate(lines_x):
      if len(line_x) <= 1:
        return f"Not enough data for {users[user_index].username}"
    
    x = 0
    
    for line_x, line_y in zip(lines_x, lines_y):
      
      new_line_x = []
      new_line_y = []
      
      
      last_reset = (0, 0)
      for reset in resets[x]:
        if reset[0] == len(line_x):
          break
        x_range = line_x[last_reset[0]:reset[0]]
        y_range = line_y[last_reset[0]:reset[0]]
        

        closest_back_break = 0
        
        if len(reset_breaks) == 1:
          closest_next_break = len(labels)-2
        else:
          closest_next_break = reset_breaks[1]-1
          for reset_break in reset_breaks[1:]:
            if reset_break > x_range[0]:
              break
            closest_back_break = reset_break
            next_index = reset_breaks.index(reset_break)+1
          
            if len(reset_breaks) == next_index:
              
              closest_next_break = len(labels)-2
            else:
              closest_next_break = reset_breaks[next_index]-1
            
            
        if reset[1] == line_x[-1]:
          line_x.pop(-1)
          line_y.pop(-1)
        
        
        if x_range[0] != closest_back_break:
          x_range.insert(0, closest_back_break)
          y_range.insert(0, y_range[0])


        if x_range[-1] != closest_next_break:
          x_range.append(closest_next_break)
          y_range.append(y_range[-1])


        new_line_x.append(x_range)
        new_line_y.append(y_range)
        last_reset = reset
      else:
        
        new_line_x.append(line_x[last_reset[0]:])
        new_line_y.append(line_y[last_reset[0]:])

      label = f"{users[x].username}"
      for line_x, line_y in zip(new_line_x, new_line_y):
        ax.plot(line_x, line_y, "-o", markersize=3, color=f"#{user_color[x]}", label=label)
        label = None
      x += 1
    
    ax.axhline(y=0, color='grey', linestyle='--')

    #for user_index in range(len(users)):
    #  ax.plot(lines_x[user_index], lines_y[user_index], "-o", markersize=3, color=f"#{user_color[user_index]}", label=f"{users[user_index].username}")
    ax.legend()
    x = [*range(xval+1)]
    reset_breaks.pop(0)
    ax.fill_between(x, 0, 1, where=[((xs in reset_breaks) or ((xs+1) in reset_breaks)) for xs in x], color='grey', alpha=0.5, transform=ax.get_xaxis_transform())


    ax.set_xticks(range(xval+1), labels, rotation='vertical')
    ax.set_xlabel(xlabel)

    for ticklabel, tickcolor in zip(ax.get_xticklabels(), label_colors):
      ticklabel.set_color(tickcolor)

    ax.xaxis.grid(linestyle=':')
    ax.margins(x=1/((x_length-0.8)*6))

    plt.tight_layout()

    fig_width, fig_height = fig.get_size_inches()
    fig.set_size_inches(x_length, fig_height)


    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    im = Image.open(buf)
    byte = im.tell()
    print(byte)

    return im
    
def all_user_unique_code(prefix, users):
  all_bal = [user.balances for user in users]
  #combine all_bal into one array
  prefix_bal = []
  for bal in all_bal:
    prefix_bal += [x for x in bal if x[0].startswith(prefix)]
    
  codes = [bal[0][len(prefix)+1:len(prefix)+9] for bal in prefix_bal]
  code = ""
  copy = True
  while copy:
    copy = False

    random.seed()
    code = str(secrets.token_hex(4))
    for k in codes:
      if k == code:
        copy = True
  return code


def get_all_unique_balance_ids(users):
  all_bal = [user.balances for user in users]
  #combine all_bal into one array
  prefix_bal = []
  for bal in all_bal:
    prefix_bal += [x for x in bal]

  unique_bal_ids = []
  unique = 0
  last = None
  for bal in prefix_bal:
    if bal[0] != last:
      unique += 1
      unique_bal_ids.append(bal[0])
    last = bal[0]
  return unique_bal_ids

def award_label_to_user(award_label):
  award_t = award_label.split(", ")

  name = ", ".join(award_t[:-2])
  
  
  id = award_t[-1][4:]
  
  return f"award_{id}_{name}"

def num_of_bal_with_name(name, users):
  name = award_label_to_user(name)
  
  balance_ids = get_all_unique_balance_ids(users)
  
  num = 0
  for bal in balance_ids:
    if bal == name:
      num += 1
      
  return num


def is_valid_user(code, username, color, hidden, balances, loans):
  errors = [False for _ in range(7)]
  if isinstance(code, int) == False or len(str(code)) > 20:
    errors[0] = True
  if isinstance(username, str) == False or len(username) > 32:
    errors[1] = True
  if isinstance(color, str) == False or len(color) > 6:
    errors[2] = True
  if isinstance(hidden, bool) == False:
    errors[3] = True
  if isinstance(balances, list) == False:
    errors[4] = True
  errors[5] = True
  if isinstance(loans, list) == False:
    errors[6] = True
  return errors
