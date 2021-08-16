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



def prep_sim(trial, rank, results_folder, print_log):
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
  print('Trial ', trial, 'processor ', rank)
  print('#######################################################')
  print('Begin initialization...')    




def run_sim(results_folder, runtime_file, start_time):
  ### setup new model
  main_cy_obj = main_cy.main_cy(results_folder, runtime_file)
  a = main_cy_obj.initialize_py()

  if a == 0:
    print('Initialization complete, ', datetime.now() - start_time)
    sys.stdout.flush()
    ### main simulation loop
    a = main_cy_obj.run_sim_py(start_time)

    if a == 0:
      print ('Simulation complete,', datetime.now() - start_time)
#      sys.stdout.flush()
#      ### calculate objectives
#      main_cy_obj.calc_objectives()
#      print ('Objective calculation complete,', datetime.now() - start_time)

#      ### output results
#      main_cy_obj.output_results()

#      ### remove results for scaling trial
#      print ('Data output complete,', datetime.now() - start_time)
      sys.stdout.flush()



########################################################################
### main experiment
########################################################################

experiment_name = sys.argv[1] ### 1 if we want to rerun zero-ownership & full-ownership cases
start_scenarios = int(sys.argv[2])  ### number of random ownership configs to run
end_scenarios = int(sys.argv[3])
nscenarios = end_scenarios - start_scenarios

# get runtime params from config file
runtime_file = 'runtime_params.ini'

config = ConfigObj(runtime_file)
parallel_mode = bool(strtobool(config['parallel_mode']))
cluster_mode = bool(strtobool(config['cluster_mode']))
print_log = bool(strtobool(config['print_log']))
flow_input_source = config['flow_input_source']
scratch_dir = config['scratch_dir']

if cluster_mode:
  results_base = scratch_dir + '/stampede2_scaling/'
else:
  results_base = 'results/'

if parallel_mode:
  from mpi4py import MPI
  comm = MPI.COMM_WORLD
  rank = comm.Get_rank()
  nprocs = comm.Get_size()
  count = int(math.floor(nscenarios/nprocs))
  remainder = nscenarios % nprocs
  ### Use the processor rank to determine the chunk of work each processor will do
  if rank < remainder:
    start = rank*(count+1) + start_scenarios
    stop = start + count + 1 
  else:
    start = remainder*(count+1) + (rank-remainder)*count + start_scenarios
    stop = start + count 
else:
  nprocs = 1
  rank = 0
  start = start_scenarios
  stop = end_scenarios



### loop through scenarios 
for s in range(start, stop):

  ### first run with both FKC expansion and CFWB
  start_time = datetime.now()
  results_folder = results_base + '/' + experiment_name + '/trial_' + str(s) + '_' + flow_input_source + '/'

  try:
    prep_sim(s, rank, results_folder, print_log)

    run_sim(results_folder, runtime_file, start_time)

#    print('result size: ', os.path.getsize(results_folder + '/results.hdf5'))
#    os.remove(results_folder + '/results.hdf5')

  except:
    print('EXPERIMENT FAIL: ', results_folder)








