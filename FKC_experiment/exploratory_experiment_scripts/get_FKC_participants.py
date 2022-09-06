import sys
import os
import json
import numpy as np
import pandas as pd
from configobj import ConfigObj
from distutils.util import strtobool




start_scenarios = int(sys.argv[1])  ### random ownership configs to run
end_scenarios = int(sys.argv[2])
nscenarios = end_scenarios - start_scenarios

# get runtime params from config file
config = ConfigObj('runtime_params.ini')
cluster_mode = bool(strtobool(config['cluster_mode']))
scratch_dir = config['scratch_dir']

if cluster_mode:
  results_base = scratch_dir + 'FKC_experiment/'
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

### for each scenario, randomly sample a set of districts to exclude from partnership (zero ownership)
for s in range(start_scenarios, end_scenarios):
    newchoice = True
    while newchoice == True:
      nnonzero = max(np.random.poisson(8), 1)
      zerodistricts = np.random.choice(np.arange(ndistricts), ndistricts - nnonzero, replace=False)
      zerodistricts.sort()
      zerodistricts = zerodistricts.tolist()
      if zerodistricts not in list_zerodistricts:
        list_zerodistricts.append(zerodistricts)
        newchoice = False

### write to file, to be input for simulations
with open(samples_file, 'w') as f:
  for zerodistricts in list_zerodistricts:
    zd = ''
    for d in zerodistricts:
      zd += str(d) + ' '
    zd += '\n'
    f.write(zd)   
