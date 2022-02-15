### this script will create & run the "problem" for MORDM for FKC/banking infrastructure 
import sys
import os
import contextlib
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


### get effective decision variables after enforcing number of districts and min share size
def get_effective_dvs(dvs, min_share):
  ### set project type to integer
  dv_project = int(dvs[0])
  ### get number of partners, renormalize shares
  npartners = int(dvs[1])
  shares = np.array(dvs[2:])
  # get indices of npartners largest shares
  partners = np.argpartition(shares, -npartners)[-npartners:]
  nonpartners = np.argpartition(shares, -npartners)[:-npartners]
  shares[nonpartners] = 0.
  # normalize to sum to 1
  shares = shares / shares.sum()
  # set lower bound of 1% ownership. renormalize others so that total sum is 1.
  min_share = 0.01
  shares[(shares < min_share) & (shares > 0.)] = min_share
  shares[shares > min_share] *= (1 - shares[shares == min_share].sum()) / shares[shares > min_share].sum()

  return dv_project, shares



### compare effective dvs for the current eval to all past evals. If within epsilon, return objs/constrs from past eval rather than running again.
def get_prev_eval(dv_project_current, shares_current, evaluationFile, epsilon):
  ndv = len(shares_current) + 2
  ### get past evals from text file
  prev = np.genfromtxt(evaluationFile, dtype=np.double)
  
  ### loop over lines in prev eval file, test if all dv's within epsilon.
  for i in range(prev.shape[0]):
    dv_project_prev, shares_prev = get_effective_dvs(prev[i,:ndv])
    if dv_project_prev == dv_project_current:
      shares_maxDiff = np.max(np.abs(shares_prev - shares_current))
      if shares_maxDiff < epsilon:
        objs = prev[i, ndv:-2]
        constrs = prev[i, -2:]
#        print(i, objs, constrs)
        return objs, constrs
 
  ## if no matches, return 0
  return 0,0


def setup_problem(results_folder, print_log, disable_print, dvs):
  ### setup/initialize model
  sys.stdout.flush()

  try:
    os.mkdir(results_folder)  
  except:
    pass

  if print_log and not disable_print:
    sys.stdout = open(results_folder + '/log.txt', 'w')

#  print('#######################################################')
#  print('Setup problem...')   
#  sys.stdout.flush()

  ### get effective project shares/type after enforcing max number of districts, min share size, & normalization
  min_share = 0.1
  dv_project, shares = get_effective_dvs(dvs, min_share)

  ### check if we've already evaluated a very similar solution, if so then just return previous objs/constrs
  seed = 1
  evaluationFile = results_folder + '../evaluations/s' + str(seed) + '.evaluations'
  dv_epsilon = 0.0025
  objs_prev, constrs_prev = get_prev_eval(dv_project, shares, evaluationFile, 0.0025)

  ### apply ownership fractions for FKC expansion based on dvs
  scenario = json.load(open('calfews_src/scenarios/FKC_properties__rehab_ownership_all.json'))
  for i, k in enumerate(scenario['ownership_shares'].keys()):
    if dv_project in [1,3]:   #1=FKC only, 3=FKC+CFWB
      scenario['ownership_shares'][k] = shares[i]
    else:                     #2=CFWB only, so set FKC ownership params to 0
      scenario['ownership_shares'][k] = 0.
  ### save new scenario to results folder
  with open(results_folder + '/FKC_scenario.json', 'w') as o:
    json.dump(scenario, o)

  ### apply ownership fractions for CFWB based on dvs, plus capacity params for CFWB
  scenario = json.load(open('calfews_src/scenarios/CFWB_properties__large_all.json'))
  removeddistricts = []
  for i, k in enumerate(scenario['ownership'].keys()):
    if dv_project in [2,3]:   #2=CFWB only, 3=FKC+CFWB
      share = shares[i]
    else:                     #1=FKC only
      share = 0.
    if share > 0.0:
      scenario['ownership'][k] = share
    else:  
      removeddistricts.append(k)
  for k in removeddistricts:
    scenario['participant_list'].remove(k)    
    del scenario['ownership'][k]
    del scenario['bank_cap'][k]
  scenario['initial_recharge'] = 300.
  scenario['tot_storage'] = 0.6
  scenario['recovery'] = 0.2
  scenario['proj_type'] = dv_project
  with open(results_folder + '/CFWB_scenario.json', 'w') as o:
    json.dump(scenario, o) 

  ### create objective file headers
  with open(results_folder + '/objs.csv', 'w') as f:
    w = writer(f)
    w.writerow(['sample','j1','j2','j3','j4','j5'])

  ### return objs, constrs. these will generally be 0 if no previous match found. 
  return objs_prev, constrs_prev



def run_sim(results_folder, baseline_folder, start_time, model_mode, flow_input_type, flow_input_source, MC_label, uncertainty_dict, shared_objs_array, MC_count, is_baseline):
#  print('#######################################################')
#  print('Initializing simulation...', MC_label, is_baseline) 
  try:
    main_cy_obj = main_cy.main_cy(results_folder, model_mode=model_mode, flow_input_type=flow_input_type, flow_input_source=flow_input_source, flow_input_addition=MC_label)
    a = main_cy_obj.initialize_py(uncertainty_dict)

#    print('Initialization complete, ', datetime.now() - start_time)
#    sys.stdout.flush()
    ### main simulation loop
    a = main_cy_obj.run_sim_py(start_time)

#    print ('Simulation complete,', datetime.now() - start_time)
#    sys.stdout.flush()
    ### for baseline runs (i.e., no new infrastructure), we need to store district-level performance for comparison. 
    ### for non-baseline, we will compare performance to baseline and output deltas, then aggregate over districts, and store MC results in shared_objs_array
    main_cy_obj.get_district_results(results_folder, baseline_folder, MC_label, shared_objs_array, MC_count, is_baseline)
#      print(MC_label)
#    print('Objectives complete,', MC_label, is_baseline, datetime.now() - start_time)
  except:
    print('fail in run sim', results_folder, MC_label)
    objs_MC = np.array([-1e6, -1e6, -1e6, 1e6, -1e6])
    shared_objs_array[MC_count*len(objs_MC):(MC_count+1)*len(objs_MC)] = objs_MC



### run a single MC instance and fill in slot in objective dictionary
def dispatch_MC_to_procs(results_folder, baseline_folder, start_time, model_modes, flow_input_types, flow_input_sources, MC_labels, uncertainty_dict, shared_objs_array, proc, start, stop, is_baseline):
  for MC_count in range(start, stop):
#    print('### beginning MC run ', MC_count, ', proc ', proc)
    run_sim(results_folder, baseline_folder, start_time, model_modes[MC_count], flow_input_types[MC_count], flow_input_sources[MC_count], MC_labels[MC_count], uncertainty_dict, shared_objs_array, MC_count, is_baseline)



### run actual problem, with decision variables as inputs
def problem_infra(*dvs, is_baseline=False):
  start_time = datetime.now()


  ### define MC sampling problem/parallelization
  num_MC = 8
  num_procs = 8
  model_modes = ['simulation'] * num_MC
  flow_input_types = ['synthetic'] * num_MC
  flow_input_sources = ['mghmm_30yr_generic'] * num_MC
  MC_labels = [str(i) for i in range(num_MC)]     #['wet','dry']

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
  disable_print = bool(strtobool(config['disable_print']))
  # flow_input_source = config['flow_input_source']

  #if cluster_mode:
  #  scratch_dir = config['scratch_dir']
  #  results_base = scratch_dir + '/FKC_experiment/'
  #else:
  results_base = 'results/'

  ### create infrastructure scenario
  baseline_folder = results_base + 'infra_MC/'
  if is_baseline:
    results_folder = baseline_folder
  else:
    sub_folder = 'seed1/'
    results_folder = results_base + 'infra_moo/' + sub_folder + '/dvhash' + str(hash(frozenset(dvs))) + '/'
  # if is_baseline and os.path.exists(results_folder):
  #   shutil.rmtree(results_folder)

#  print(results_folder, dvs)
#  sys.stdout.flush()

  ### disable printing (make sure disable_print is True in runtime_params.ini too)
#  with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
  ### use this instead if don't want to disable printing (make sure disable_print is False in runtime_params.ini too. 
  ### probably better way to do this, but good enough for now
  with contextlib.nullcontext():
    ### setup folder & scenario files for ownership configuration. check if previous evaluation had very similar effective params, if so just use those values instead of rerunning.
    objs_prev, constrs_prev = setup_problem(results_folder, print_log, disable_print, dvs)

    ### if no previous evaluation, run MC ensemble.
    if objs_prev is 0:
      
      # Create node-local processes
      shared_processes = []
      num_objs = 5
      shared_objs_array = Array('d', num_MC*num_objs)

      ### assign MC trials to processors
      nbase = int(num_MC / num_procs)
      remainder = num_MC - num_procs * nbase
      start = 0

      ### try context for multiprocessing with spawn (https://pythonspeed.com/articles/python-multiprocessing/)
      #with get_context('spawn').Process() as spawn_Process:

      for proc in range(num_procs):
        num_trials = nbase if proc >= remainder else nbase + 1
        stop = start + num_trials
        p = Process(target=dispatch_MC_to_procs, args=(results_folder, baseline_folder, start_time, model_modes, flow_input_types, flow_input_sources, MC_labels,
                                                      uncertainty_dict, shared_objs_array, proc, start, stop, is_baseline))
        shared_processes.append(p)
        start = stop
  
      # Start processes
      for sp in shared_processes:
        sp.start()
  
      # Wait for all processes to finish
      for sp in shared_processes:
        sp.join()
  #    print('end join procs')

      ### aggregate over MC trials
        ### objs: max(0) CWG - mean over years - sum over partners - mean over MC
        ###       max(1) pumping reduction - mean over years - sum over partners - mean over MC
        ###       max(2) CWG - mean over years - sum over non-partners - mean over MC
        ###       min(3) cost CWG - mean over years - max over partners - max over MC
        ###       max(4) number partners - no agg needed
        ### cons: (1) obj 3 < 2000
        ###       (2) obj 4 > 0
      cost_constraint = 1000
      objs_allMC = np.array(shared_objs_array).reshape(num_MC, num_objs)
      objs_MCagg = [-objs_allMC[:,0].mean(),
                    -objs_allMC[:,1].mean(),
                    -objs_allMC[:,2].mean(),
                    objs_allMC[:,3].max(),
                    -objs_allMC[0,4]]
      constrs_MCagg = [max(0.0, objs_MCagg[3] - cost_constraint),
                       0. if objs_MCagg[-1] < 0 else 1.]

      ### if it's all 0.0, that means there was an error somewhere. reset to less desirable values
      if sum(np.abs(objs_MCagg)) == 0.:
        objs_MCagg = [1e6, 1e6, 1e6, 1e6, 1e6]

  #  print(objs_MCagg)
 #   print('Finished all processes', datetime.now() - start_time)
  #  print(objs_MCagg, constrs_MCagg)

      #print(type(objs_MCagg), objs_MCagg, type(constrs_MCagg), constrs_MCagg)  
      return objs_MCagg, constrs_MCagg

    ### else if previous eval has very similar effective decision vector, just return those values instead of rerunning
    else:
      #print(type(objs_prev), objs_prev, type(constrs_prev), constrs_prev)
      return objs_prev.tolist(), constrs_prev.tolist()
