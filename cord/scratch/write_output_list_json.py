
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

# get example data to help get output classes. Note that if new infrastructure, banking arrangements, etc, may need to update output classes.
modelno = pd.read_pickle('cord/data/results/baseline_wy2017/p0/modelno0.pkl')
modelso = pd.read_pickle('cord/data/results/baseline_wy2017/p0/modelso0.pkl')

# create nested dict to hold all possible output types
d = {'north':{'reservoirs': {}, 'delta':{}}, 'south':{'reservoirs':{}, 'contracts':{}, 'districts':{}, 'waterbanks':{}}}
# northern reservoirs
for name in [x.name for x in modelno.reservoir_list]:
  d['north']['reservoirs'][name] = {}
  for output in ['S', 'R', 'R_to_delta', 'available_storage']:    # list reservoir outputs of interest here
    d['north']['reservoirs'][name][output] = True
# southern reservoirs
for name in [x.name for x in modelso.reservoir_list]:
  d['south']['reservoirs'][name] = {}
  for output in ['S', 'R', 'available_storage']:    # list reservoir outputs of interest here
    d['south']['reservoirs'][name][output] = True
# delta
for output in ['HRO_pump', 'TRP_pump', 'x2', 'outflow', 'OMR', 'forecastSRI', 'forecastSJI']:               # list delta outputs here
  d['north']['delta'][output] = True
# contracts, need to account for discrepancy in object names between contract classes vs names in district class deliveries
contract_dict = {'friant1': 'friant1', 'friant2': 'friant2', 'tableA': 'swpdelta', 'cvpdelta': 'cvpdelta',
                 'exchange': 'cvpexchange', 'cvc': 'crossvalley', 'kern': 'kernriver', 'tule': 'tuleriver',
                 'kaweah': 'kaweahriver', 'kings': 'kingsriver'}
for name in [contract_dict[x.name] for x in modelso.contract_list]:
  d['south']['contracts'][name] = {}
  for output in ['allocation', 'available_water']:    # list contract outputs here
    d['south']['contracts'][name][output] = True
  d['south']['contracts'][name]['daily_supplies'] = {}
  for output in ['contract', 'carryover', 'turnback', 'flood']:
    d['south']['contracts'][name]['daily_supplies'][output] = True
    
# districts
for name in [x.name for x in modelso.district_list]:
  d['south']['districts'][name] = {'deliveries':{}}
  for contract in modelso.__getattribute__(name).contract_list:
    for output in ['delivery', 'carryover']:          # list district outputs, for contract/right allocations
      d['south']['districts'][name]['deliveries'][contract + '_' + output] = True
  for contract in modelso.__getattribute__(name).contract_list_all:
    for output in ['flood']:                          # list district outputs, for contracts/rights with no allocation
      # if (np.max(modelso.__getattribute__(name).daily_supplies_full[contract + '_' + output]) > 0):
      d['south']['districts'][name]['deliveries'][contract + '_' + output] = True
	
  for output in ['recover_banked', 'inleiu_irrigation', 'inleiu_recharge', 'leiupumping', 'recharged', 'exchanged_GW', 'exchanged_SW']:
    d['south']['districts'][name][output] = {}
    
for name in [x.name for x in modelso.waterbank_list]:
  d['south']['waterbanks'][name] = {}
  d['south']['waterbanks'][name]['bank_timeseries'] = {}
  for partner in modelso.__getattribute__(name).bank_timeseries.keys():
    d['south']['waterbanks'][name]['bank_timeseries'][partner] = True

with open('cord/data/input/output_list.json', 'w') as f:
  json.dump(d, f, indent=2)

# with open('cord/data/input/output_list.json', 'r') as f:
#   dat=json.load(f)