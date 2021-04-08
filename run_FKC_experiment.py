import sys
import os
import shutil
import json
import math
import numpy as np
import pandas as pd
from configobj import ConfigObj
from distutils.util import strtobool
from datetime import datetime
import main_cy



def prep_sim(exp_name, results_folder, print_log):
  ### setup/initialize model
  sys.stdout.flush()

  ### remove any old results
  try:
    shutil.rmtree(results_folder)
  except:
    pass
  try:
    os.mkdir(results_folder)  
  except:
    pass

  if print_log:
    sys.stdout = open(results_folder + '/log.txt', 'w')

  print('#######################################################')
  print('Experiment ', exp_name)
  print('#######################################################')
  print('Begin initialization...')    




def run_sim(results_folder, start_time):
  ### setup new model
  main_cy_obj = main_cy.main_cy(results_folder)
  a = main_cy_obj.initialize_py()

  if a == 0:
    print('Initialization complete, ', datetime.now() - start_time)
    sys.stdout.flush()
    ### main simulation loop
    a = main_cy_obj.run_sim_py(start_time)

    if a == 0:
      print ('Simulation complete,', datetime.now() - start_time)
      sys.stdout.flush()
      ### calculate objectives
      main_cy_obj.calc_objectives()
      print ('Objective calculation complete,', datetime.now() - start_time)

      ### output results
      main_cy_obj.output_results()
      print ('Data output complete,', datetime.now() - start_time)
      sys.stdout.flush()



########################################################################
### main experiment
########################################################################

rerun_baselines = int(sys.argv[1]) ### 1 if we want to rerun zero-ownership & full-ownership cases
start_scenarios = int(sys.argv[2])  ### number of random ownership configs to run
end_scenarios = int(sys.argv[3])
nscenarios = end_scenarios - start_scenarios

rank = int(sys.argv[4])
nprocs = int(sys.argv[5])
count = int(math.floor(nscenarios/nprocs))
remainder = nscenarios % nprocs
# Use the processor rank to determine the chunk of work each processor will do
if rank < remainder:
  start = rank*(count+1) + start_scenarios
  stop = start + count + 1 
else:
  start = remainder*(count+1) + (rank-remainder)*count + start_scenarios
  stop = start + count 

print('Hello from processor ',rank, ' out of ', nprocs, ', running samples ', start, '-', stop-1)

# get runtime params from config file
config = ConfigObj('runtime_params.ini')
# parallel_mode = bool(strtobool(config['parallel_mode']))
cluster_mode = bool(strtobool(config['cluster_mode']))
print_log = bool(strtobool(config['print_log']))
flow_input_source = config['flow_input_source']

if cluster_mode:
  results_base = '/scratch/spec823/CALFEWS_results/FKC_experiment/'
else:
  results_base = 'results/'

for s in range(start, stop):

  np.random.seed(s)

  ### first run with both FKC expansion and CFWB
  start_time = datetime.now()
  results_folder = results_base + 'FKC_experiment_' + flow_input_source + '_' + str(s) + '_FKC_CFWB'

  try:
    prep_sim(str(s) + ', FKC + CFWB', results_folder, print_log)

    ### get prior choices for district ownership (list will be district positions with zero shares)
    with open(results_base + 'FKC_experiment_zerodistricts.txt', 'r') as f:
      count = 0
      for line in f: # read rest of lines
        if count == s:
          zerodistricts = [int(x) for x in line.split()]
        count += 1
    
    ### randomly choose new ownership fractions for FKC expansion & CFWB, plus capacity params for CFWB
    scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
    ndistricts = len(scenario['ownership_shares'])
    shares = np.random.uniform(size=ndistricts)
    shares[zerodistricts] = 0.0
    shares /= shares.sum()
    for i, k in enumerate(scenario['ownership_shares'].keys()):
      scenario['ownership_shares'][k] = shares[i]
    ### save new scenario to results folder
    with open(results_folder + '/FKC_scenario.json', 'w') as o:
      json.dump(scenario, o)

    ### now do similar to choose random params for CFWB. Use same ownership fractions from FKC.
    scenario = json.load(open('calfews_src/scenarios/CFWB_properties__large_all.json'))
    removeddistricts = []
    for i, k in enumerate(scenario['ownership'].keys()):
      if shares[i] > 0.0:
        scenario['ownership'][k] = shares[i]
      else:  
        removeddistricts.append(k)
    for k in removeddistricts:
      scenario['participant_list'].remove(k)    
      del scenario['ownership'][k]
      del scenario['bank_cap'][k]
    scenario['initial_recharge'] = np.random.uniform(0.0, 600.0)
    scenario['tot_storage'] = np.random.uniform(0.0, 1.2)
    scenario['recovery'] = np.random.uniform(0.0, 0.7)
    with open(results_folder + '/CFWB_scenario.json', 'w') as o:
      json.dump(scenario, o)

    run_sim(results_folder, start_time)

  except:
    print('EXPERIMENT FAIL: ', results_folder)

  ################
  ### now rerun with only FKC expansion
  results_folder_both = results_folder
  results_folder = results_base + 'FKC_experiment_' + flow_input_source + '_' + str(s) + '_FKC'
  start_time = datetime.now()

  try:
    prep_sim(str(s) + ', FKC only', results_folder, print_log)

    shutil.copy(results_folder_both + '/FKC_scenario.json', results_folder)

    scenario = json.load(open('calfews_src/scenarios/CFWB_properties__large_all.json'))
    scenario['participant_list'] = []
    scenario['ownership'] = {}
    scenario['bank_cap'] = {}
    scenario['initial_recharge'] = 0.0
    scenario['tot_storage'] = 0.0
    scenario['recovery'] = 0.0
    with open(results_folder + '/CFWB_scenario.json', 'w') as o:
      results_folder + '/CFWB_scenario.json'
      json.dump(scenario, o)

    run_sim(results_folder, start_time)

  except:
    print('EXPERIMENT FAIL: ', results_folder)    

  ################
  ### now rerun with only CFWB
  results_folder = results_base + 'FKC_experiment_' + flow_input_source + '_' + str(s) + '_CFWB'
  start_time = datetime.now()

  try:
    prep_sim(str(s) + ', CFWB only', results_folder, print_log)

    shutil.copy(results_folder_both + '/CFWB_scenario.json', results_folder)

    scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
    for i, k in enumerate(scenario['ownership_shares'].keys()):
      scenario['ownership_shares'][k] = 0.0
    with open(results_folder + '/FKC_scenario.json', 'w') as o:
      json.dump(scenario, o)

    run_sim(results_folder, start_time)
  except:
    print('EXPERIMENT FAIL: ', results_folder)



### run basline without FKC or CFWB, if argv1 == 1 and processor rank == last
if rerun_baselines == 1 and rank == (nprocs - 1):

  results_folder = results_base + 'FKC_experiment_' + flow_input_source + '_none'
  start_time = datetime.now()

  try:
    prep_sim('None', results_folder, print_log)

    scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
    for i, k in enumerate(scenario['ownership_shares'].keys()):
      scenario['ownership_shares'][k] = 0.0
    with open(results_folder + '/FKC_scenario.json', 'w') as o:
      json.dump(scenario, o)

    scenario = json.load(open('calfews_src/scenarios/CFWB_properties__large_all.json'))
    scenario['participant_list'] = []
    scenario['ownership'] = {}
    scenario['bank_cap'] = {}
    scenario['initial_recharge'] = 0.0
    scenario['tot_storage'] = 0.0
    scenario['recovery'] = 0.0
    with open(results_folder + '/CFWB_scenario.json', 'w') as o:
      results_folder + '/CFWB_scenario.json'
      json.dump(scenario, o)
      
    run_sim(results_folder, start_time)
  except:
    print('EXPERIMENT FAIL: ', results_folder)





