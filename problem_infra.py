### this script will create & run the "problem" for MORDM for FKC/banking infrastructure 
import sys
import os
import contextlib
import shutil
import json
import time
from csv import writer
import numpy as np
import pandas as pd
from configobj import ConfigObj
from distutils.util import strtobool
#from multiprocessing import Process, Array
#from mpi4py import MPI
import subprocess
from datetime import datetime
import main_cy





def setup_problem(results_folder, print_log, disable_print, dvs, uncertainty_dict):
  ### setup/initialize model
  sys.stdout.flush()

  try:
    os.mkdir(results_folder)  
  except:
    pass

  if print_log and not disable_print:
    sys.stdout = open(results_folder + '/log.txt', 'w')

  print('#######################################################')
  print('Setup problem...')   
  sys.stdout.flush()

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
  # set lower bound of 1% ownership. renormalize others.
  lb = 0.01
  shares[(shares < lb) & (shares > 0.)] = lb
  shares[shares > lb] /= shares[shares > lb].sum()

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
  scenario['recovery'] = 0.35
  scenario['proj_type'] = dv_project
  with open(results_folder + '/CFWB_scenario.json', 'w') as o:
    json.dump(scenario, o) 

  ### create objective file headers
  with open(results_folder + '/objs.csv', 'w') as f:
    w = writer(f)
    w.writerow(['sample','j1','j2','j3','j4','j5'])

  ### also write uncertainty dict to json
  with open(results_folder + '/uncertainty_dict.json', 'w') as o:
    json.dump(uncertainty_dict, o)






### run actual problem, with decision variables as inputs
def problem_infra(*dvs, is_baseline=False):
  start_time = datetime.now()

  ### define MC sampling problem/parallelization (note: this gets overwritten from submit_scaling.sh)
  num_MC = 10
  num_procs_FE = 5
  
  num_objs = 5
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

  results_base = 'results/'

  ### create infrastructure scenario
  baseline_folder = results_base + 'infra_MC/'
  if is_baseline:
    results_folder = baseline_folder
  else:
    sub_folder = '16task_10node/'
    results_folder = results_base + 'infra_scaling/' + sub_folder + '/dvhash' + str(hash(frozenset(dvs))) + '/'


  ### disable printing (make sure disable_print is True in runtime_params.ini too)
#  with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
  ### use this instead if don't want to disable printing (make sure disable_print is False in runtime_params.ini too. 
  ### probably better way to do this, but good enough for now
  with contextlib.nullcontext():
    from mpi4py import MPI
  #  from single_MC import single_MC_mainProc
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    universe_size = comm.Get_attr(MPI.UNIVERSE_SIZE)

    ### setup problem from FE master proc
    setup_problem(results_folder, print_log, disable_print, dvs, uncertainty_dict)    

    ### run MC trials (make sure num_MC % num_procs_FE == 0)
    MC_run = 0
    while MC_run < num_MC:
      ### due to comm bottlenecks, occasionally MPI proc may not have opened back up yet. Loop until it does (within reason, otherwise something else may have gone wrong)
      failed_spawns = 0
      while failed_spawns < 50:
        try: 
          ### first dispatch (num_procs_FE) to new spawned processes
          args = [['-W ignore', 'problem_infra.py', results_folder, baseline_folder, datetime.strftime(start_time, '%c'), model_modes[i], flow_input_types[i], flow_input_sources[i], MC_labels[i], str(i), str(is_baseline)] for i in range(MC_run, MC_run + num_procs_FE - 1)]
          innercomm = MPI.COMM_SELF.Spawn_multiple([sys.executable]*(num_procs_FE-1), args=args, maxprocs=[1]*(num_procs_FE-1))
          break
        except:
          time.sleep(3)
          failed_spawns += 1

      ### now run one more on this main processor
      i = MC_run + num_procs_FE - 1
      objs_mainProc = run_sim(results_folder, baseline_folder, start_time, model_modes[i], flow_input_types[i], flow_input_sources[i], MC_labels[i], i, is_baseline)

      objs_spawns = innercomm.gather(None, root=MPI.ROOT)
   
      innercomm.Barrier()
      innercomm.Disconnect()
      time.sleep(3)
 
      ### join data
      if MC_run == 0:
        objs_allMC = objs_mainProc
      else:
        objs_allMC = np.concatenate((objs_allMC, objs_mainProc))
      for objs_spawn in objs_spawns:
        objs_allMC = np.concatenate((objs_allMC, objs_spawn))
#      print(MC_run, objs_allMC)
      MC_run += num_procs_FE

    objs_allMC = np.reshape(objs_allMC, (int(len(objs_allMC)/num_objs), num_objs))

    ### aggregate over MC trials
        ### objs: max(0) CWG - mean over years - sum over partners - mean over MC
        ###       max(1) pumping reduction - mean over years - sum over partners - mean over MC
        ###       max(2) CWG - mean over years - sum over non-partners - mean over MC
        ###       min(3) cost CWG - mean over years - max over partners - max over MC
        ###       max(4) number partners - no agg needed
        ### cons: (1) obj 3 < 2000
        ###       (2) obj 4 > 0
    cost_constraint = 2000
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


    print(objs_MCagg)
    print('Finished all processes', datetime.now() - start_time)
    print(objs_MCagg, constrs_MCagg)

    return objs_MCagg, constrs_MCagg




### run simulation MC sample. THis version runs as a function in same program as problem_infra(), as opposed to spawn version below which is run from terminal.
def run_sim(results_folder, baseline_folder, start_time, model_mode, flow_input_type, flow_input_source, MC_label, MC_count, is_baseline, spawn_rank=-1):
  print('#######################################################')
  print('Initializing simulation...', MC_label, is_baseline, spawn_rank)
  ### setup new model
  try:
    main_cy_obj = main_cy.main_cy(results_folder, model_mode=model_mode, flow_input_type=flow_input_type, flow_input_source=flow_input_source, flow_input_addition=MC_label)
    uncertainty_dict = json.load(open(results_folder + '/uncertainty_dict.json'))
    a = main_cy_obj.initialize_py(uncertainty_dict)

    print('Initialization complete, ', datetime.now() - start_time)
    sys.stdout.flush()
    ### main simulation loop
    a = main_cy_obj.run_sim_py(start_time)

    print ('Simulation complete,', datetime.now() - start_time)
    sys.stdout.flush()
    ### for baseline runs (i.e., no new infrastructure), we need to store district-level performance for comparison.
    ### for non-baseline, we will compare performance to baseline and output deltas, then aggregate over districts, and output MC results
    objs = main_cy_obj.get_district_results(results_folder, baseline_folder, MC_label, MC_count, is_baseline)
    ### if objs all 0's, something went wrong. reset to high (bad) values so doesn't mess with Pareto set
    if np.sum(objs) == 0.0:
      objs = np.array([-1e6, -1e6, -1e6, 1e6, -1e6])

    print('Objectives complete,', MC_label, is_baseline, datetime.now() - start_time)
    return objs

  except:
    print('fail in run sim', MC_label, spawn_rank)
    return np.array([-1e6, -1e6, -1e6, 1e6, -1e6])







### if this file is run directly by MPI spawned process, get args from argv, run sim, and send results back to parent
if __name__ == '__main__':
  ### args from 
  results_folder = sys.argv[1]
  baseline_folder = sys.argv[2]
  start_time = datetime.strptime(sys.argv[3], '%c')
  model_mode = sys.argv[4]
  flow_input_type = sys.argv[5]
  flow_input_source = sys.argv[6]
  MC_label = sys.argv[7]
  MC_count = int(sys.argv[8])
  from distutils.util import strtobool
  is_baseline = bool(strtobool(sys.argv[9]))

  ### get MPI rank within spawned children of parent
  from mpi4py import MPI
  innercomm = MPI.COMM_WORLD.Get_parent() 
  rank = innercomm.Get_rank()

  ### get sim, get objectives
  try:
    objs = run_sim(results_folder, baseline_folder, start_time, model_mode, flow_input_type, flow_input_source, MC_label, MC_count, is_baseline, rank)
  except:
    objs = np.array([-1e6, -1e6, -1e6, 1e6, -1e6])

  ### now send results back to MPI parent
  objs = innercomm.gather(objs, root=0)

  innercomm.Barrier()
  innercomm.Disconnect()













