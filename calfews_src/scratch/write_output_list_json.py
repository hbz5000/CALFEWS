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
modelso = main_cy_obj.modelso
modelno = main_cy_obj.modelno

# create nested dict to hold all possible output types
d = {'north': {'reservoirs': {}, 'delta': {}},
     'south': {'reservoirs': {}, 'contracts': {}, 'districts': {}, 'privates': {}, 'waterbanks': {}}}

# northern reservoirs
for name in [x.name for x in modelno.reservoir_list]:
    d['north']['reservoirs'][name] = {}
    for output in ['S', 'R', 'R_to_delta', 'available_storage', 'outflow_release', 'days_til_full','contract_flooded',
                   'reclaimed_carryover','flood_spill','flood_deliveries','Q','SNPK','downstream','fnf']:  # list reservoir outputs of interest here
        d['north']['reservoirs'][name][output] = True

# southern reservoirs
for name in [x.name for x in modelso.reservoir_list]:
    d['south']['reservoirs'][name] = {}
    for output in ['S', 'R', 'available_storage', 'outflow_release', 'days_til_full','contract_flooded',
                   'reclaimed_carryover','flood_spill','flood_deliveries','Q','SNPK','downstream','fnf']:  # list reservoir outputs of interest here
        d['south']['reservoirs'][name][output] = True

# delta
for output in ['HRO_pump', 'TRP_pump', 'x2', 'outflow', 'inflow', 'OMR', 'forecastSRI', 'forecastSJI',
               'uncontrolled_swp','uncontrolled_cvp','remaining_outflow','swp_allocation','cvp_allocation',
               'gains','gains_sac','gains_sj','depletions','vernalis_flow','eastside_streams']:  # list delta outputs here
    d['north']['delta'][output] = True

# contracts, need to account for discrepancy in object names between contract classes vs names in district class deliveries
contract_dict = {'friant1': 'friant1', 'friant2': 'friant2', 'tableA': 'swpdelta', 'cvpdelta': 'cvpdelta',
                 'exchange': 'cvpexchange', 'cvc': 'crossvalley', 'kern': 'kernriver', 'tule': 'tuleriver',
                 'kaweah': 'kaweahriver', 'kings': 'kingsriver'}
for name in [contract_dict[x.name] for x in modelso.contract_list]:
    d['south']['contracts'][name] = {}
    for output in ['allocation', 'available_water']:  # list contract outputs here
        d['south']['contracts'][name][output] = True
    d['south']['contracts'][name]['daily_supplies'] = {}
    for output in ['contract', 'carryover', 'turnback', 'flood','total_carryover']:
        d['south']['contracts'][name]['daily_supplies'][output] = True

# districts
for name in [x.name for x in modelso.district_list + modelso.urban_list]:
    d['south']['districts'][name] = {}
    for key in modelso.__getattribute__(name).daily_supplies_full.keys():
        d['south']['districts'][name][key] = True

# private
for name in [x.name for x in modelso.private_list + modelso.city_list]:
    d['south']['privates'][name] = {}
    for key in modelso.__getattribute__(name).daily_supplies_full.keys():
        d['south']['privates'][name][key] = True

# waterbanks
for name in [x.name for x in modelso.waterbank_list]:
    d['south']['waterbanks'][name] = {}
    d['south']['waterbanks'][name]['bank_timeseries'] = {}
    for partner in modelso.__getattribute__(name).bank_timeseries.keys():
        d['south']['waterbanks'][name]['bank_timeseries'][partner] = True

with open('calfews_src/data/input/output_list.json', 'w') as f:
    json.dump(d, f, indent=2)