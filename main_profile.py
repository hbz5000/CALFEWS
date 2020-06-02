##################################################################################
## simplified scripts that skips init by reading in model objects, for profiling
##################################################################################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import line_profiler
profile = line_profiler.LineProfiler()
import cord
from cord import *
from datetime import datetime
import os
import shutil
import sys
from configobj import ConfigObj
import json
from distutils.util import strtobool


#path_model = './'
#path_model = sys.argv[1]
#print (sys.argv)
#os.chdir(path_model)

startTime = datetime.now()

# get runtime params from config file
config = ConfigObj('cord/data/input/runtime_params.ini')
model_mode = 'sensitivity'  #config['model_mode']
short_test = int(config['short_test'])
seed = int(config['seed'])
scenario_name = config['scenario_name'] #scenarios provide information on infrastructural plans
flow_input_type = config['flow_input_type']
flow_input_source = 'CDEC_wet_dry' # config['flow_input_source']
total_sensitivity_factors = int(config['total_sensitivity_factors'])
sensitivity_sample_file = config['sensitivity_sample_file']
output_list = config['output_list']
output_directory = config['output_directory']
clean_output = bool(strtobool(config['clean_output']))

# infrastructure scenario file, to be used for all sensitivity samples
with open('cord/scenarios/scenarios_main.json') as f:
  scenarios = json.load(f)
scenario = scenarios[scenario_name]
results_folder = output_directory + '/' + scenario_name
os.makedirs(results_folder, exist_ok=True)
shutil.copy('cord/data/input/runtime_params.ini', results_folder + '/runtime_params.ini')

# make separate output folder for each processor
rank = 0
results_folder = results_folder + '/p' + str(rank)
os.makedirs(results_folder, exist_ok=True)
if (os.path.exists(results_folder + '/results_p0.hdf5')):
  os.remove(results_folder + '/results_p0.hdf5')

# always use shorter historical dataframe for expected delta releases
expected_release_datafile = 'cord/data/input/cord-data.csv'
# data for actual simulation
if model_mode == 'simulation':
  demand_type = 'baseline'
  #demand_type = 'pmp'
  input_data_file = 'cord/data/input/cord-data-sim.csv'
elif model_mode == 'validation':
  demand_type = 'pesticide'
  input_data_file = 'cord/data/input/cord-data.csv'
elif model_mode == 'sensitivity':
  demand_type = 'baseline'
  base_data_file = 'cord/data/input/cord-data.csv'
elif model_mode == 'climate_ensemble':
  demand_type = 'baseline'
  base_data_file = 'cord/data/input/cord-data.csv'

print(model_mode)
if model_mode == 'sensitivity':
  #####FLOW GENERATOR#####
  #seed
  if (seed > 0):
    np.random.seed(seed)
  # read in k'th sample from sensitivity sample file
  k = 0
  sensitivity_sample = np.genfromtxt(sensitivity_sample_file, delimiter='\t', skip_header=k+1, max_rows=1)[1:]
  with open(sensitivity_sample_file, 'r') as f:
    sensitivity_sample_names = f.readlines()[0].split('\n')[0]
  np.savetxt(results_folder + '/sample' + str(k) + '.txt', sensitivity_sample.reshape(1, len(sensitivity_sample)), delimiter=',', header=sensitivity_sample_names)
  sensitivity_sample_names = sensitivity_sample_names.split('\t')[1:]

  #Initialize flow input scenario based on sensitivity sample
  if not (os.path.exists(results_folder + '/modelno.pkl') and os.path.exists(results_folder + '/modelso.pkl')):
    print('Initializing new model objects')
    new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode, results_folder, k, sensitivity_sample_names, sensitivity_sample, use_sensitivity = False)
    new_inputs.run_initialization('XXX')
    new_inputs.run_routine(flow_input_type, flow_input_source)
    input_data_file = results_folder + '/' + new_inputs.export_series[flow_input_type][flow_input_source]  + "_"  + str(k) + ".csv"
    modelno = Model(input_data_file, expected_release_datafile, model_mode, demand_type, k, sensitivity_sample_names, sensitivity_sample, new_inputs.sensitivity_factors)
    modelso = Model(input_data_file, expected_release_datafile, model_mode, demand_type, k, sensitivity_sample_names, sensitivity_sample, new_inputs.sensitivity_factors)
    del new_inputs
    modelso.max_tax_free = {}
    modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
    modelso.forecastSRI = modelno.delta.forecastSRI
    modelso.southern_initialization_routine(startTime, scenario)
    pd.to_pickle(modelno, results_folder + '/modelno.pkl')
    pd.to_pickle(modelso, results_folder + '/modelso.pkl')

  else:
    print('Reading in initialized model objects')
    if (seed > 0):
      np.random.seed(seed + 1)  # make sure seed always same, whether initialize or read in model object
    modelno = pd.read_pickle(results_folder + '/modelno.pkl')
    modelso = pd.read_pickle(results_folder + '/modelso.pkl')
    if (short_test < 0):
      timeseries_length = min(modelno.T, modelso.T)
    else:
      timeseries_length = short_test
    swp_release = 1
    cvp_release = 1
    swp_release2 = 1
    cvp_release2 = 1
    swp_pump = 999.0
    cvp_pump = 999.0
    proj_surplus = 0.0
    swp_available = 0.0
    cvp_available = 0.0
    print('Initialization complete, ', datetime.now() - startTime)
    for t in range(0, timeseries_length):
      if (t % 365 == 364):
        print('Year ', (t+1)/365, ', ', datetime.now() - startTime)
      # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
      swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

      swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.forecastSCWYT, modelno.delta.max_tax_free, flood_release, flood_volume)

    # save output as hdf5
    data_output(modelno, modelso, output_list, results_folder, clean_output, rank, k)

print ('Total run completed in ', datetime.now() - startTime)



