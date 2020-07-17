from __future__ import division
import json

class Scenario():

  def __init__(self):
    for k,v in json.load(open('calfews_src/scenarios/scenarios.json')).items():
        setattr(self,k,v)










