
class Match:
  
  def __init__(self, t1, t2, t1oo, t2oo, t1o, t2o, tournament_name, odds_source, creator, date_created, color, code):
    self.t1 = t1
    self.t2 = t2
    self.t1oo = t1oo
    self.t2oo = t2oo
    self.t1o = t1o
    self.t2o = t2o

    self.tournament_name = tournament_name
    
    self.odds_source = odds_source

    #id of user that created match
    self.creator = creator

    self.date_created = date_created

    self.color = color
    
    #code is a 8 lenth hexadecimal number
    self.code = code
    
    self.bet_ids = []
    self.message_ids = []
    self.date_winner = None
    self.date_closed = None
    self.winner = 0
  

  
  def to_string(self):
    date_formatted = self.date_created.strftime("%d/%m/%Y at %H:%M:%S")
    return "Teams: " + str(self.t1) + " vs " + str(self.t2) + ", Odds: " + str(self.t1o) + " / " + str(self.t2o) +  ", Old Odds: " + str(self.t1oo) + " / " + str(self.t2oo) + ", Tournament Name: " + str(self.tournament_name) + ", Odds Source: " + str(self.odds_source) + "\nCreator: " + str(self.creator) + ", Created On: " + str(date_formatted) + ", Bet IDs: " + str(self.bet_ids) + ", Date Closed: " + str(self.date_closed) + ", Winner: " + str(self.winner) + ", Identifyer: " + str(self.code) + ", Message IDs: " + str(self.message_ids)


  def short_to_string(self):
    return "Teams: " + str(self.t1) + " vs " + str(self.t2) + ", Odds: " + str(self.t1o) + " / " + str(self.t2o)

  def winner_name(self):
    if self.winner == 0:
      return "None"
    elif self.winner == 1:
      return self.t1
    else:
      return self.t2

  def basic_to_string(self):
    return f"Match: {self.code}, Teams: {self.t1} vs {self.t2}, Odds: {self.t1o} vs {self.t2o}, Tournament Name: {self.tournament_name}"