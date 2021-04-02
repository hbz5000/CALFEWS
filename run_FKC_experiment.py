import sys
import os
import shutil
import json
import time
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
nscenarios = int(sys.argv[2])  ### number of random ownership configs to run

try:
  os.remove('results/FKC_experiment_zerodistricts.txt')
except:
  pass


### setup mpi if using parallel mode
# get runtime params from config file
config = ConfigObj('runtime_params.ini')
parallel_mode = bool(strtobool(config['parallel_mode']))
print_log = bool(strtobool(config['print_log']))

if parallel_mode:
  from mpi4py import MPI
  import math
  import time
  # Parallel simulation
  comm = MPI.COMM_WORLD
  # Number of processors and the rank of processors
  rank = comm.Get_rank()
  nprocs = comm.Get_size()
  # Determine the chunk which each processor will neeed to do
  count = int(math.floor(nscenarios/nprocs))
  remainder = nscenarios % nprocs
  # Use the processor rank to determine the chunk of work each processor will do
  if rank < remainder:
    start = rank*(count+1)
    stop = start + count + 1
  else:
    start = remainder*(count+1) + (rank-remainder)*count
    stop = start + count
else: # non-parallel mode
  start = 0
  stop = nscenarios
  rank = 0




for s in range(start, stop):
  start_time = datetime.now()

  np.random.seed(s)

  ### first run with both FKC expansion and NFWB
  results_folder = 'results/FKC_experiment_' + str(s) + '_FKC_NFWB'
  
  # try:
  prep_sim(str(s) + ', FKC + NFWB', results_folder, print_log)

  ### get prior choices for district ownership (list will be district positions with zero shares)
  try:
    with open('results/FKC_experiment_zerodistricts.txt', 'r') as f:
      list_zerodistricts = []
      for line in f: # read rest of lines
          list_zerodistricts.append([int(x) for x in line.split()])
  except:
    list_zerodistricts = []

  ### randomly choose new ownership fractions for FKC expansion & NFWB, plus capacity params for NFWB
  scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
  ndistricts = len(scenario['ownership_shares'])
  shares = np.random.uniform(size=ndistricts)
  newchoice = True
  while newchoice == True:
    nnonzero = max(np.random.poisson(8), 1)
    zerodistricts = np.random.choice(np.arange(ndistricts), ndistricts - nnonzero, replace=False)
    zerodistricts.sort()
    zerodistricts = zerodistricts.tolist()
    if zerodistricts not in list_zerodistricts:
      with open('results/FKC_experiment_zerodistricts.txt', 'a') as f:
        zd = ''
        for d in zerodistricts:
          zd += str(d) + ' '
        zd += '\n'
        f.write(zd)      
      newchoice = False
  shares[zerodistricts] = 0.0
  shares /= shares.sum()
  for i, k in enumerate(scenario['ownership_shares'].keys()):
    scenario['ownership_shares'][k] = shares[i]
  ### save new scenario to results folder
  with open(results_folder + '/FKC_scenario.json', 'w') as o:
    json.dump(scenario, o)

  ### now do similar to choose random params for NFWB. Use same ownership fractions from FKC.
  scenario = json.load(open('calfews_src/scenarios/NFWB_properties__large_all.json'))
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
  scenario['initial_recharge'] = np.random.uniform(0.0, 1000.0)
  scenario['tot_storage'] = np.random.uniform(0.0, 2.0)
  scenario['recovery'] = np.random.uniform(0.0, 1.0)
  with open(results_folder + '/NFWB_scenario.json', 'w') as o:
    json.dump(scenario, o)

  run_sim(results_folder, start_time)

  # except:
  #   print('EXPERIMENT FAIL: ', results_folder)

  # ################
  # ### now rerun with only FKC expansion
  # results_folder_both = results_folder
  # results_folder = 'results/FKC_experiment_' + str(s) + '_FKC'

  # try:
  #   prep_sim(str(s) + ', FKC only', results_folder, print_log)

  #   shutil.copy(results_folder_both + '/FKC_scenario.json', results_folder)

  #   scenario = json.load(open('calfews_src/scenarios/NFWB_properties__large_all.json'))
  #   scenario['participant_list'] = []
  #   scenario['ownership'] = {}
  #   scenario['bank_cap'] = {}
  #   scenario['initial_recharge'] = 0.0
  #   scenario['tot_storage'] = 0.0
  #   scenario['recovery'] = 0.0
  #   with open(results_folder + '/NFWB_scenario.json', 'w') as o:
  #     results_folder + '/NFWB_scenario.json'
  #     json.dump(scenario, o)

  #   run_sim(results_folder, start_time)

  # except:
  #   print('EXPERIMENT FAIL: ', results_folder)    

  # ################
  # ### now rerun with only NFWB
  # results_folder = 'results/FKC_experiment_' + str(s) + '_NFWB'

  # try:
  #   prep_sim(str(s) + ', NFWB only', results_folder, print_log)

  #   shutil.copy(results_folder_both + '/NFWB_scenario.json', results_folder)

  #   scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
  #   for i, k in enumerate(scenario['ownership_shares'].keys()):
  #     scenario['ownership_shares'][k] = 0.0
  #   with open(results_folder + '/FKC_scenario.json', 'w') as o:
  #     json.dump(scenario, o)

  #   run_sim(results_folder, start_time)
  # except:
  #   print('EXPERIMENT FAIL: ', results_folder)






##### GRAVEYARD ####################################

# if rerun_baselines == 1:
#   results_folder = 'results/FKC_experiment_none'

#   ### setup/initialize model
#   print('#######################################################')
#   print('Experiment: no districts allowed')
#   print('#######################################################')
#   print('Begin initialization...')
#   sys.stdout.flush()

#   ### remove any old results
#   try:
#     shutil.rmtree(results_folder)
#   except:
#     pass
#   try:
#     os.mkdir(results_folder)  
#   except:
#     pass

#   ### no districts given access to FKC expansion, baseline case
#   scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
#   ndistricts = len(scenario['ownership_shares'])
#   shares = np.zeros(ndistricts)
#   for i, k in enumerate(scenario['ownership_shares'].keys()):
#     scenario['ownership_shares'][k] = shares[i]
#   ### save new scenario to results folder
#   with open(results_folder + '/FKC_scenario.json', 'w') as o:
#     json.dump(scenario, o)

#   ### no districts given access to NFWB, baseline case
#   scenario = json.load(open('calfews_src/scenarios/NFWB_properties__large_all.json'))
#   for i, k in enumerate(scenario['ownership'].keys()):
#     scenario['ownership'][k] = shares[i]
#     if shares[i] == 0.0:
#       scenario['bank_cap'][k] = 0.0
#   ### save new scenario to results folder
#   with open(results_folder + '/NFWB_scenario.json', 'w') as o:
#     json.dump(scenario, o)

#   ### setup new model
#   main_cy_obj = main_cy.main_cy(results_folder)
#   a = main_cy_obj.initialize_py()

#   if a == 0:
#     print('Initialization complete, ', datetime.now() - start_time)
#     sys.stdout.flush()
#     ### main simulation loop
#     a = main_cy_obj.run_sim_py(start_time)

#     if a == 0:
#       print ('Simulation complete,', datetime.now() - start_time)
#       sys.stdout.flush()
#       ### calculate objectives
#       main_cy_obj.calc_objectives()
#       print ('Objective calculation complete,', datetime.now() - start_time)

#       ### output results
#       main_cy_obj.output_results()
#       print ('Data output complete,', datetime.now() - start_time)
#       sys.stdout.flush()



#   ### all districts given access, baseline case
#   results_folder = 'results/FKC_experiment_all'

#   ### setup/initialize model
#   print('#######################################################')
#   print('Experiment: all districts allowed')
#   print('#######################################################')
#   print('Begin initialization...')
#   sys.stdout.flush()

#   ### remove any old results
#   try:
#     shutil.rmtree(results_folder)
#   except:
#     pass
#   try:
#     os.mkdir(results_folder)  
#   except:
#     pass

#   ### all districts given access to FKC expansion, baseline case
#   scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all_withbanks.json'))
#   ndistricts = len(scenario['ownership_shares'])
#   shares = np.ones(ndistricts)
#   for i, k in enumerate(scenario['ownership_shares'].keys()):
#     scenario['ownership_shares'][k] = shares[i]
#   ### save new scenario to results folder
#   with open(results_folder + '/FKC_scenario.json', 'w') as o:
#     json.dump(scenario, o)

#   ### all districts given access to FKC expansion, baseline case
#   scenario = json.load(open('calfews_src/scenarios/NFWB_properties__large_all.json'))
#   for i, k in enumerate(scenario['ownership'].keys()):
#     scenario['ownership'][k] = shares[i]
#     if shares[i] == 0.0:
#       scenario['bank_cap'][k] = 0.0
#   ### save new scenario to results folder
#   with open(results_folder + '/NFWB_scenario.json', 'w') as o:
#     json.dump(scenario, o)

#   ### setup new model
#   main_cy_obj = main_cy.main_cy(results_folder)
#   a = main_cy_obj.initialize_py()

#   if a == 0:
#     print('Initialization complete, ', datetime.now() - start_time)
#     sys.stdout.flush()
#     ### main simulation loop
#     a = main_cy_obj.run_sim_py(start_time)

#     if a == 0:
#       print ('Simulation complete,', datetime.now() - start_time)
#       sys.stdout.flush()
#       ### calculate objectives
#       main_cy_obj.calc_objectives()
#       print ('Objective calculation complete,', datetime.now() - start_time)

#       ### output results
#       main_cy_obj.output_results()
#       print ('Data output complete,', datetime.now() - start_time)
#       sys.stdout.flush()