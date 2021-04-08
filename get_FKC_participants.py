import sys
import os
import json
import numpy as np
import pandas as pd
from configobj import ConfigObj
from distutils.util import strtobool



########################################################################
### main experiment
########################################################################

start_scenarios = int(sys.argv[1])  ### number of random ownership configs to run
end_scenarios = int(sys.argv[2])
nscenarios = end_scenarios - start_scenarios

### setup mpi if using parallel mode
# get runtime params from config file
config = ConfigObj('runtime_params.ini')
cluster_mode = bool(strtobool(config['cluster_mode']))

if cluster_mode:
  results_base = '/scratch/spec823/CALFEWS_results/FKC_experiment/'
else:
  results_base = 'results/'
samples_file = results_base + 'FKC_experiment_zerodistricts.txt'
try:
  os.remove(samples_file)
except:
  pass

scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
ndistricts = len(scenario['ownership_shares'])

np.random.seed(end_scenarios)
list_zerodistricts = []

for s in range(start_scenarios, end_scenarios):

    # ### get prior choices for district ownership (list will be district positions with zero shares)
    # try:
    #   with open(samples_file, 'r') as f:
    #     list_zerodistricts = []
    #     for line in f: # read rest of lines
    #         list_zerodistricts.append([int(x) for x in line.split()])
    # except:
    #   list_zerodistricts = []

    ### randomly choose new ownership fractions for FKC expansion & CFWB, plus capacity params for CFWB
    # scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
    # ndistricts = len(scenario['ownership_shares'])
    newchoice = True
    while newchoice == True:
      nnonzero = max(np.random.poisson(8), 1)
      zerodistricts = np.random.choice(np.arange(ndistricts), ndistricts - nnonzero, replace=False)
      zerodistricts.sort()
      zerodistricts = zerodistricts.tolist()
      if zerodistricts not in list_zerodistricts:
        list_zerodistricts.append(zerodistricts)
        # with open(samples_file, 'a') as f:
        #   zd = ''
        #   for d in zerodistricts:
        #     zd += str(d) + ' '
        #   zd += '\n'
        #   f.write(zd)      
        newchoice = False

with open(samples_file, 'w') as f:
  for zerodistricts in list_zerodistricts:
    zd = ''
    for d in zerodistricts:
      zd += str(d) + ' '
    zd += '\n'
    f.write(zd)   
