from __future__ import division
import json

class Scenario():

  def __init__(self):
    for k,v in json.load(open('cord/scenarios/scenarios.json')).items():
        setattr(self,k,v)










