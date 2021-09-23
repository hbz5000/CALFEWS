### this script will create & run the "problem" for MORDM for FKC/banking infrastructure 
import sys
import os
import shutil
import json
import numpy as np
import pandas as pd
from configobj import ConfigObj
from distutils.util import strtobool
from multiprocessing import Process, cpu_count, Manager
from datetime import datetime
import main_cy





def setup_problem(results_folder, print_log, dvs):
  ### setup/initialize model
  sys.stdout.flush()

  try:
    os.mkdir(results_folder)  
  except:
    pass

  if print_log:
    sys.stdout = open(results_folder + '/log.txt', 'w')

  print('#######################################################')
  print('Setup problem...')   

  ### apply ownership fractions for FKC expansion based on dvs
  scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all.json'))
  if dvs[0] in [1,3]:   # 1 = FKC only, 3 = FKC+CFWB
    shares = dvs[1:]
  else:                 # 2 = CFWB only, so set FKC ownership params to 0
    shares = np.zeros(len(dvs[1:]))
  for i, k in enumerate(scenario['ownership_shares'].keys()):
    scenario['ownership_shares'][k] = shares[i]
  ### save new scenario to results folder
  with open(results_folder + '/FKC_scenario.json', 'w') as o:
    json.dump(scenario, o)

  ### apply ownership fractions for CFWB based on dvs, plus capacity params for CFWB
  scenario = json.load(open('calfews_src/scenarios/CFWB_properties__large_all.json'))
  if dvs[0] in [2,3]:   # 2 = CFWB only, 3 = FKC+CFWB
    shares = dvs[1:]
  else:                 # 2 = FKC only, so set CFWB ownership params to 0
    shares = np.zeros(len(dvs[1:]))
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
  scenario['initial_recharge'] = 300.
  scenario['tot_storage'] = 0.6
  scenario['recovery'] = 0.35
  with open(results_folder + '/CFWB_scenario.json', 'w') as o:
    json.dump(scenario, o) 




def run_sim(results_folder, model_mode, flow_input_type, flow_input_source, MC_label, uncertainty_dict, start_time, is_baseline):
  print('#######################################################')
  print('Initializing simulation...') 
  # try:
  ### setup new model
  main_cy_obj = main_cy.main_cy(results_folder, model_mode=model_mode, flow_input_type=flow_input_type, flow_input_source=flow_input_source)
  a = main_cy_obj.initialize_py(uncertainty_dict)

  if a == 0:
    print('Initialization complete, ', datetime.now() - start_time)
    sys.stdout.flush()
    ### main simulation loop
    a = main_cy_obj.run_sim_py(start_time)

    if a == 0:
      print ('Simulation complete,', datetime.now() - start_time)
      sys.stdout.flush()
      if is_baseline:
        ### for baseline runs (i.e., no new infrastructure), we need to store district-level performance for comparison
        main_cy_obj.store_baseline_results(MC_label)
        return 0

      else:
        ### for non-baseline, we calculate objectives by comparison to baseline
        objs = main_cy_obj.calc_objectives(MC_label)
        print(MC_label, objs)
        return objs

      print ('Objective calculation complete,', datetime.now() - start_time)

  # except:
  #   return {}



### run a single MC instance and fill in slot in objective dictionary
def dispatch_MC_to_procs(results_folder, start_time, model_modes, flow_input_types, flow_input_sources, MC_labels, uncertainty_dict, shared_output, proc, start, stop, is_baseline):
  for n in range(start, stop):
    print('### beginning MC run ', n, ', proc ', proc)
    shared_output[n] = run_sim(results_folder, model_modes[n], flow_input_types[n], flow_input_sources[n], MC_labels[n], uncertainty_dict, start_time, is_baseline)



### run actual problem, with decision variables as inputs
def problem_infra(dvs, num_MC, num_procs, uncertainty_dict, is_baseline=False):

  start_time = datetime.now()

  config = ConfigObj('runtime_params.ini')
  cluster_mode = bool(strtobool(config['cluster_mode']))
  print_log = bool(strtobool(config['print_log']))
  # flow_input_source = config['flow_input_source']
  scratch_dir = config['scratch_dir']

  if cluster_mode:
    results_base = scratch_dir + '/FKC_experiment/'
  else:
    results_base = 'results/'


  ### create infrastructure scenario
  results_folder = results_base + 'infra_MC/'
  if os.path.exists(results_folder):
    shutil.rmtree(results_folder)
  setup_problem(results_folder, print_log, dvs)
  
  ### list of input time series (flow_input_source) to loop over
  model_modes = ['simulation'] * num_MC
  flow_input_types = ['observations'] * num_MC
  flow_input_sources = ['CDEC_wet_dry'] * num_MC
  MC_labels = ['MC0','MC1']
  # flow_input_source_l = ['capow_50yr_wet', 'capow_50yr_median', 'capow_50yr_dry']

  # Create node-local processes
  shared_processes = []
  mgr = Manager()
  shared_output = mgr.dict()

  ### assign MC trials to processors
  nbase = int(num_MC / num_procs)
  remainder = num_MC - num_procs * nbase
  start = 0
  for proc in range(num_procs):
    num_trials = nbase if proc >= remainder else nbase + 1
    stop = start + num_trials
    p = Process(target=dispatch_MC_to_procs, args=(results_folder, start_time, model_modes, flow_input_types, flow_input_sources, MC_labels,
                                                    uncertainty_dict, shared_output, proc, start, stop, is_baseline))
    shared_processes.append(p)
    start = stop
  
  # Start processes
  for sp in shared_processes:
    sp.start()
  
  # Wait for all processes to finish
  for sp in shared_processes:
    sp.join()

  print(shared_output)

  print('Finished all processes',  datetime.now() - start_time)

  return shared_output