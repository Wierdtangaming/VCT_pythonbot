
class Match:
  def __init__(self, t1, t2, t1o, t2o, tournament_name, odds_source, creator, identifyer):
    self.t1 = t1
    self.t2 = t2
    self.t1o = t1o
    self.t20 = t2o

    self.tournament_name = tournament_name
    
    self.odds_source = odds_source

    #user that created match
    self.creator = creator

    #identifyer is a 4 lenth hexadecimal number
    #match db keys are M[identifyer]
    self.identifyer = identifyer
