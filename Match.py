
class Match:
  
  def __init__(self, t1, t2, t1oo, t2oo, t1o, t2o, tournament_name, odds_source, creator, date_created, identifyer):
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
    #identifyer is a 8 lenth hexadecimal number
    #match db keys are Match_[identifyer]
    self.identifyer = identifyer

    self.bets_open = True

    self.bet_ids = []

    self.date_closed = None
  
