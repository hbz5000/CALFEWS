
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cord
from cord import *
from datetime import datetime
import os
import shutil
from configobj import ConfigObj
import json
import h5py

modelno = pd.read_pickle('cord/data/results/baseline_wy2017/modelno0.pkl')
modelso = pd.read_pickle('cord/data/results/baseline_wy2017/modelso0.pkl')

d = {'north':{'reservoirs': {'any':True}}, 'south':{'reservoirs':{'any':True}}}
for name in [x.name for x in modelno.reservoir_list]:
  d['north']['reservoirs'][name] = {}
  for output in ['any', 'baseline_inf', 'snowflood_inf']:
    d['north']['reservoirs'][name][output] = True




with open('cord/data/input/output_list.json', 'w') as f:
  json.dump(d, f, indent=True)

# with open('cord/data/input/output_list.json', 'r') as f:
#   dat=json.load(f)