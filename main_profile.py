##################################################################################
## simplified scripts that skips init by reading in model objects, for profiling
##################################################################################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import line_profiler
profile = line_profiler.LineProfiler()
import calfews_src
from calfews_src import *
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
config = ConfigObj('runtime_params_wet_dry.ini')
model_mode = 'simulation'  #config['model_mode']
short_test = int(config['short_test'])
seed = int(config['seed'])
scenario_name = config['scenario_name'] #scenarios provide information on infrastructural plans
# flow_input_type = config['flow_input_type']
flow_input_source = 'CDEC_wet_dry' # config['flow_input_source']
# total_sensitivity_factors = int(config['total_sensitivity_factors'])
# sensitivity_sample_file = config['sensitivity_sample_file']
output_list = config['output_list']
output_directory = config['output_directory']
clean_output = bool(strtobool(config['clean_output']))

# infrastructure scenario file, to be used for all sensitivity samples
with open('calfews_src/scenarios/scenarios_main.json') as f:
  scenarios = json.load(f)
scenario = scenarios[scenario_name]
results_folder = output_directory + '/' + scenario_name + '/' + model_mode + '/' + flow_input_source + '/'
os.makedirs(results_folder, exist_ok=True)
shutil.copy('runtime_params.ini', results_folder + '/runtime_params.ini')

# make separate output folder for each processor
rank = 0
# results_folder = results_folder + '/p' + str(rank)
# os.makedirs(results_folder, exist_ok=True)
if (os.path.exists(results_folder + '/results_' + flow_input_source + '.hdf5')):
  os.remove(results_folder + '/results_' + flow_input_source + '.hdf5')

# always use shorter historical dataframe for expected delta releases
expected_release_datafile = 'calfews_src/data/input/calfews_src-data.csv'
# data for actual simulation
if model_mode == 'simulation':
  demand_type = 'baseline'
  #demand_type = 'pmp'
  input_data_file = 'calfews_src/data/input/calfews_src-data-wet-dry.csv'
# elif model_mode == 'validation':
#   demand_type = 'pesticide'
#   input_data_file = 'calfews_src/data/input/calfews_src-data.csv'
# elif model_mode == 'sensitivity':
#   demand_type = 'baseline'
#   base_data_file = 'calfews_src/data/input/calfews_src-data.csv'
# elif model_mode == 'climate_ensemble':
#   demand_type = 'baseline'
#   base_data_file = 'calfews_src/data/input/calfews_src-data.csv'

print(model_mode)

if (seed > 0):
  np.random.seed(seed)
# read in k'th sample from sensitivity sample file
k = 0

#Initialize flow input scenario based on sensitivity sample
if not (os.path.exists(results_folder + '/modelno.pkl') and os.path.exists(results_folder + '/modelso.pkl')):
  print('Initializing new model objects')
  
  modelno = Model(input_data_file, expected_release_datafile, model_mode, demand_type)
  modelso = Model(input_data_file, expected_release_datafile, model_mode, demand_type)
  modelso.max_tax_free = {}
  modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
  modelso.forecastSRI = modelno.delta.forecastSRI
  modelso.southern_initialization_routine(startTime)
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
  try:
    sensitivity_factors = {}
    data_output(output_list, results_folder, clean_output, flow_input_source, sensitivity_factors, modelno, modelso)
    pd.to_pickle(modelno, results_folder + '/modelno.pkl')
    pd.to_pickle(modelso, results_folder + '/modelso.pkl')
  except:
    print('data save failure')
print ('Total run completed in ', datetime.now() - startTime)



