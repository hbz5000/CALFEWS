
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import calfews_src
from calfews_src import *
from datetime import datetime
import os
import shutil
from configobj import ConfigObj
import json
import h5py

# get example data to help get output classes. Note that if new infrastructure, banking arrangements, etc, may need to update output classes.
modelno = pd.read_pickle('calfews_src/data/results/baseline_wy2017/p0/modelno0.pkl')
modelso = pd.read_pickle('calfews_src/data/results/baseline_wy2017/p0/modelso0.pkl')

# create nested dict to hold all possible output types
d = {'north':{'reservoirs': {}, 'delta':{}}, 'south':{'reservoirs':{}, 'contracts':{}, 'districts':{}, 'private':{}, 'waterbanks':{}}}
# northern reservoirs
for name in [x.name for x in modelno.reservoir_list]:
  d['north']['reservoirs'][name] = {}
  for output in ['S', 'R', 'R_to_delta', 'available_storage', 'outflow_release', 'days_til_full', 'contract_flooded', 'reclaimed_carryover']:    # list reservoir outputs of interest here
    d['north']['reservoirs'][name][output] = True
  for input in ['Q', 'SNPK', 'downstream', 'fnf']:    # list reservoir outputs of interest here
    d['north']['reservoirs'][name][input] = True
# southern reservoirs
for name in [x.name for x in modelso.reservoir_list]:
  d['south']['reservoirs'][name] = {}
  for output in ['S', 'available_storage', 'outflow_release', 'days_til_full', 'reclaimed_carryover', 'contract_flooded', 'reclaimed_carryover', 'flood_spill', 'flood_deliveries']:    # list reservoir outputs of interest here
    d['south']['reservoirs'][name][output] = True
  if name != 'sanluisstate' and name != 'sanluisfederal':
    for input in ['Q', 'SNPK', 'downstream', 'fnf']:    # list reservoir outputs of interest here
      d['south']['reservoirs'][name][input] = True
# delta
for output in ['HRO_pump', 'TRP_pump', 'x2', 'outflow', 'inflow', 'uncontrolled_swp', 'uncontrolled_cvp', 'remaining_outflow', 'swp_allocation', 'cvp_allocation']:               # list delta outputs here
  d['north']['delta'][output] = True
for input in ['gains', 'gains_sac', 'gains_sj', 'depletions', 'vernalis_flow', 'eastside_streams', 'OMR', 'forecastSRI', 'forecastSJI']:               # list delta outputs here
  d['north']['delta'][input] = True
# contracts, need to account for discrepancy in object names between contract classes vs names in district class deliveries
contract_dict = {'friant1': 'friant1', 'friant2': 'friant2', 'tableA': 'swpdelta', 'cvpdelta': 'cvpdelta',
                 'exchange': 'cvpexchange', 'cvc': 'crossvalley', 'kern': 'kernriver', 'tule': 'tuleriver',
                 'kaweah': 'kaweahriver', 'kings': 'kingsriver'}
for name in [contract_dict[x.name] for x in modelso.contract_list]:
  d['south']['contracts'][name] = {}
  for output in ['allocation', 'available_water']:    # list contract outputs here
    d['south']['contracts'][name][output] = True
  d['south']['contracts'][name]['daily_supplies'] = {}
  for output in ['contract', 'carryover', 'turnback', 'flood', 'total_carryover']:
    d['south']['contracts'][name]['daily_supplies'][output] = True
    
# districts
for name, district_key in zip([x.name for x in modelso.district_list], [x.key for x in modelso.district_list]):
  d['south']['districts'][name] = {}
  for contract in modelso.__getattribute__(name).contract_list:
    for output in ['projected', 'delivery', 'carryover', 'recharged', 'dynamic_recharge_cap']:          # list district outputs, for contract/right allocations
      d['south']['districts'][name][contract + '_' + output] = True
  for contract in modelso.__getattribute__(name).contract_list_all:
    for output in ['flood', 'flood_irrigation']:                          # list district outputs, for contracts/rights with no allocation
      # if (np.max(modelso.__getattribute__(name).daily_supplies_full[contract + '_' + output]) > 0):
      d['south']['districts'][name][contract + '_' + output] = True
  #for bank in modelso.__getattribute__(name).delivery_location_list:
  for output in ['recharged',]:
    d['south']['districts'][name][district_key + '_' + output] = True	
  for bank in [xx.key for xx in modelso.waterbank_list]:
    for output in ['recharged',]:
      d['south']['districts'][name][bank + '_' + output] = True	
  for bank in [xx.key for xx in modelso.leiu_list]:
    for output in ['recharged',]:
      d['south']['districts'][name][bank + '_' + output] = True	
  for output in ['recover_banked', 'inleiu_irrigation', 'inleiu_recharge', 'leiupumping', 'exchanged_GW', 'exchanged_SW', 'pumping', 'irr_demand', 'tot_demand', 'dynamic_recovery_cap']:
    d['south']['districts'][name][output] = True
    
# private
for name in [x.name for x in modelso.private_list]:
  d['south']['private'][name] = {}
  for district in modelso.__getattribute__(name).district_list:
    for contract in modelso.__getattribute__(name).contract_list:
      for output in ['projected', 'delivery', 'carryover', 'recharged', 'dynamic_recharge_cap']:          # list district outputs, for contract/right allocations
        d['south']['private'][name][district + '_' + contract + '_' + output] = True
    for contract in modelso.__getattribute__(name).contract_list_all:
      for output in ['flood']:                          # list district outputs, for contracts/rights with no allocation
        # if (np.max(modelso.__getattribute__(name).daily_supplies_full[contract + '_' + output]) > 0):
        d['south']['private'][name][district + '_' + contract + '_' + output] = True
    #for bank in modelso.__getattribute__(name).delivery_location_list:
    for output in ['recharged',]:
      d['south']['private'][name][district + '_' + district + '_' + output] = True	
    for bank in [xx.key for xx in modelso.waterbank_list]:
      for output in ['recharged',]:
        d['south']['private'][name][district + '_' + bank + '_' + output] = True	
    for bank in [xx.key for xx in modelso.leiu_list]:
      for output in ['recharged',]:
        d['south']['private'][name][district + '_' + bank + '_' + output] = True	
	
    for output in ['recover_banked', 'inleiu', 'leiupumping', 'exchanged_GW', 'exchanged_SW', 'pumping', 'irr_demand', 'tot_demand', 'dynamic_recovery_cap']:
      d['south']['private'][name][district + '_' + output] = True
# private
for name in [x.name for x in modelso.city_list]:
  d['south']['private'][name] = {}
  for district in modelso.__getattribute__(name).district_list:
    for contract in modelso.__getattribute__(name).contract_list:
      for output in ['projected', 'delivery', 'carryover', 'recharged', 'dynamic_recharge_cap']:          # list district outputs, for contract/right allocations
        d['south']['private'][name][district + '_' + contract + '_' + output] = True
    for contract in modelso.__getattribute__(name).contract_list_all:
      for output in ['flood']:                          # list district outputs, for contracts/rights with no allocation
        # if (np.max(modelso.__getattribute__(name).daily_supplies_full[contract + '_' + output]) > 0):
        d['south']['private'][name][district + '_' + contract + '_' + output] = True
    for output in ['recharged',]:
      d['south']['private'][name][district + '_' + district + '_' + output] = True	
    for bank in [xx.key for xx in modelso.waterbank_list]:
      for output in ['recharged',]:
        d['south']['private'][name][district + '_' + bank + '_' + output] = True	
    for bank in [xx.key for xx in modelso.leiu_list]:
      for output in ['recharged',]:
        d['south']['private'][name][district + '_' + bank + '_' + output] = True	
	
    for output in ['recover_banked', 'inleiu', 'leiupumping', 'exchanged_GW', 'exchanged_SW', 'pumping', 'irr_demand', 'tot_demand', 'dynamic_recovery_cap']:
      d['south']['private'][name][district + '_' + output] = True


for name in [x.name for x in modelso.waterbank_list]:
  d['south']['waterbanks'][name] = {}
  for partner in modelso.__getattribute__(name).bank_timeseries.keys():
    d['south']['waterbanks'][name][partner] = True
for name in [x.name for x in modelso.leiu_list]:
  d['south']['waterbanks'][name] = {}
  for partner in modelso.__getattribute__(name).bank_timeseries.keys():
    d['south']['waterbanks'][name][partner] = True

with open('calfews_src/data/input/output_list.json', 'w') as f:
  json.dump(d, f, indent=2)

# with open('calfews_src/data/input/output_list.json', 'r') as f:
#   dat=json.load(f)

