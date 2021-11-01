### this script will create & run the "problem" for MORDM for FKC/banking infrastructure 
import sys
import os
import shutil
import json
from csv import writer
import numpy as np
import pandas as pd
from configobj import ConfigObj
from distutils.util import strtobool
from multiprocessing import Process, Array
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

  ### set project type to integer
  dv_project = int(dvs[0])

  ### apply ownership fractions for FKC expansion based on dvs
  scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all.json'))
  if dv_project in [1,3]:   # 1 = FKC only, 3 = FKC+CFWB
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
  if dv_project in [2,3]:   # 2 = CFWB only, 3 = FKC+CFWB
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
  scenario['proj_type'] = dv_project
  with open(results_folder + '/CFWB_scenario.json', 'w') as o:
    json.dump(scenario, o) 

  ### create objective file headers
  with open(results_folder + '/objs.csv', 'w') as f:
    w = writer(f)
    w.writerow(['sample','j1','j2','j3','j4','j5'])


def run_sim(results_folder, start_time, model_mode, flow_input_type, flow_input_source, MC_label, uncertainty_dict, shared_objs_array, MC_count, is_baseline):
  print('#######################################################')
  print('Initializing simulation...', MC_label, is_baseline) 
  # try:
  ### setup new model
  main_cy_obj = main_cy.main_cy(results_folder, model_mode=model_mode, flow_input_type=flow_input_type, flow_input_source=flow_input_source, flow_input_addition=MC_label)
  a = main_cy_obj.initialize_py(uncertainty_dict)

  if a == 0:
    print('Initialization complete, ', datetime.now() - start_time)
    sys.stdout.flush()
    ### main simulation loop
    a = main_cy_obj.run_sim_py(start_time)

    if a == 0:
      print ('Simulation complete,', datetime.now() - start_time)
      sys.stdout.flush()
      ### for baseline runs (i.e., no new infrastructure), we need to store district-level performance for comparison. 
      ### for non-baseline, we will compare performance to baseline and output deltas, then aggregate over districts, and store MC results in shared_objs_array
      main_cy_obj.get_district_results(results_folder, MC_label, shared_objs_array, MC_count, is_baseline)
      print(MC_label)
      print('Objectives complete,', MC_label, is_baseline, datetime.now() - start_time)




### run a single MC instance and fill in slot in objective dictionary
def dispatch_MC_to_procs(results_folder, start_time, model_modes, flow_input_types, flow_input_sources, MC_labels, uncertainty_dict, shared_objs_array, proc, start, stop, is_baseline):
  for MC_count in range(start, stop):
    print('### beginning MC run ', MC_count, ', proc ', proc)
    run_sim(results_folder, start_time, model_modes[MC_count], flow_input_types[MC_count], flow_input_sources[MC_count], MC_labels[MC_count], uncertainty_dict, shared_objs_array, MC_count, is_baseline)



### run actual problem, with decision variables as inputs
def problem_infra(*dvs, is_baseline=False):
  start_time = datetime.now()


  ### define MC sampling problem/parallelization
  num_MC = 3
  num_procs = 3
  model_modes = ['simulation'] * num_MC
  flow_input_types = ['synthetic'] * num_MC
  flow_input_sources = ['capow_50yr_wet', 'capow_50yr_median', 'capow_50yr_dry']
#  MC_labels = [str(i) for i in range(num_MC)]     #['wet','dry']
  MC_labels = ['wet','median','dry']

  ### uncertainties
  uncertainty_dict = {}
  # uncertainty_dict['MDD_multiplier'] = 1.1
  # uncertainty_dict['ag_demand_multiplier'] = {'crop': {'maj_orchardvineyard':1.1, 'maj_other':0.8}, 'friant': {'friant': 0.9, 'non_friant': 1.0}}
  # uncertainty_dict['env_min_flow_base'] = {'MIL': 150., 'PFT': 150., 'KWH': 35., 'SUC': 15., 'ISB':75, 'SHA': 3000, 'ORO':1500}
  # uncertainty_dict['env_min_flow_peak_multiplier'] = {'MIL': 1.1, 'PFT': 1.1, 'KWH': 1.1, 'SUC': 1.1, 'ISB': 1.1, 'SHA': 2, 'ORO':1.5}
  # uncertainty_dict['delta_min_outflow_base'] = 3500
  # uncertainty_dict['delta_min_outflow_peak_multiplier'] = 1.2


  ### execution params to control 
  config = ConfigObj('runtime_params.ini')
  cluster_mode = bool(strtobool(config['cluster_mode']))
  print_log = bool(strtobool(config['print_log']))
  # flow_input_source = config['flow_input_source']

  #if cluster_mode:
  #  scratch_dir = config['scratch_dir']
  #  results_base = scratch_dir + '/FKC_experiment/'
  #else:
  results_base = 'results/'

  ### create infrastructure scenario
  results_folder = results_base + 'infra_borg/dvhash' + str(hash(frozenset(dvs))) + '/'
  # if is_baseline and os.path.exists(results_folder):
  #   shutil.rmtree(results_folder)
  setup_problem(results_folder, print_log, dvs)
  
  # Create node-local processes
  shared_processes = []
  num_objs = 5
  shared_objs_array = Array('d', num_MC*num_objs)

  ### assign MC trials to processors
  nbase = int(num_MC / num_procs)
  remainder = num_MC - num_procs * nbase
  start = 0
  for proc in range(num_procs):
    num_trials = nbase if proc >= remainder else nbase + 1
    stop = start + num_trials
    p = Process(target=dispatch_MC_to_procs, args=(results_folder, start_time, model_modes, flow_input_types, flow_input_sources, MC_labels,
                                                    uncertainty_dict, shared_objs_array, proc, start, stop, is_baseline))
    shared_processes.append(p)
    start = stop
  
  # Start processes
  for sp in shared_processes:
    sp.start()
  
  # Wait for all processes to finish
  for sp in shared_processes:
    sp.join()
  print('end join procs')

  ### aggregate over MC trials
      ### objs: max(0) CWG - mean over years - sum over partners - mean over MC
      ###       max(1) pumping reduction - mean over years - sum over partners - mean over MC
      ###       max(2) CWG - mean over years - sum over non-partners - mean over MC
      ###       min(3) cost CWG - mean over years - max over partners - max over MC
      ###       max(4) number partners - no agg needed
      ### cons: (1) obj 3 < 2000
  cost_constraint = 2000
  objs_allMC = np.array(shared_objs_array).reshape(num_MC, num_objs)
  objs_MCagg = [-objs_allMC[:,0].mean(),
                -objs_allMC[:,1].mean(),
                -objs_allMC[:,2].mean(),
                objs_allMC[:,3].max(),
                -objs_allMC[0,4]]
  constrs_MCagg = [max(0.0, objs_MCagg[3] - cost_constraint)]
  print(objs_MCagg)
  print('Finished all processes', datetime.now() - start_time)
  print(objs_MCagg, constrs_MCagg)

  return objs_MCagg, constrs_MCagg
