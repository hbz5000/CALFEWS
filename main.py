##################################################################################
#
# Combined Tulare Basin / SF Delta Model
# Still in development - not ready for publication
#
# This model is designed to simulate surface water flows throughout the CA Central Valley, including:
# (a) Major SWP/CVP Storage in the Sacramento River Basin
# (b) San Joaquin River controls at New Melones, Don Pedro, and Exchequer Reservoirs
# (c) Delta environmental controls, as outlined in D1641 Bay Delta Standards & NMFS Biological Opinions for the Bay-Delta System
# (d) Cordination between Delta Pumping and San Luis Reservoir
# (e) Local sources of water in Tulare Basin (8/1/18 - includes Millerton, Kaweah, Success, and Isabella Reservoirs - only Millerton & Isabella are currently albrated)
# (f) Conveyence and distribution capacities in the Kern County Canal System, including CA Aqueduct, Friant-Kern Canal, Kern River Channel system, and Cross Valley Canal
# (g) Agricultural demands & groundwater recharge/recovery capacities
# (h) Pumping off the CA Aqueduct to Urban demands in the South Bay, Central Coast, and Southern California
##################################################################################

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cord
from cord import *
from datetime import datetime
import os
import shutil
import sys
from configobj import ConfigObj
import json
from distutils.util import strtobool

startTime = datetime.now()

# get runtime params from config file
config = ConfigObj('cord/data/input/runtime_params.ini')
parallel_mode = bool(strtobool(config['parallel_mode']))
cluster_mode = bool(strtobool(config['cluster_mode']))
model_mode = config['model_mode']
short_test = int(config['short_test'])
seed = int(config['seed'])
scenario_name = config['scenario_name']
flow_input_type = config['flow_input_type']
flow_input_source = config['flow_input_source']
total_sensitivity_factors = int(config['total_sensitivity_factors'])
output_list = config['output_list']
output_directory = config['output_directory']
clean_output = bool(strtobool(config['clean_output']))
save_full = bool(strtobool(config['save_full']))

# infrastructure scenario file
with open('cord/scenarios/scenarios_main.json') as f:
  scenarios = json.load(f)
scenario = scenarios[scenario_name]
results_folder = output_directory + '/' + scenario_name
print(results_folder)
try:
  os.makedirs(results_folder, exist_ok=False)
except:
  print ('Error: Results folder ' + results_folder + ' already exists. Delete or move old data before rerunning.')
  sys.exit()
shutil.copy('cord/data/input/runtime_params.ini', results_folder + '/runtime_params.ini')

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

######################################################################################
if model_mode == 'sensitivity':
  #####FLOW GENERATOR#####
  #seed
  if (seed > 0):
    np.random.seed(seed)

  #Initialize flow input scenario
  new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode, use_sensitivity = True)
  new_inputs.run_initialization('XXX')

  ##Initialize dataframes to store sensitivity parameters and results
  sensitivity_df = pd.DataFrame()
  param_df = pd.DataFrame()
  for n in new_inputs.sensitivity_factors['factor_list']:
    param_df[n] = np.zeros(total_sensitivity_factors)
	
  #Loop through sensitivity realizations
  for x in range(0, total_sensitivity_factors):
    new_inputs.run_routine(flow_input_type, flow_input_source, x)
    input_data_file = new_inputs.export_series[flow_input_type][flow_input_source]
	
    modelno = Model(input_data_file, expected_release_datafile, model_mode, demand_type, x, new_inputs.sensitivity_factors)
    modelso = Model(input_data_file, expected_release_datafile, model_mode, demand_type, x, new_inputs.sensitivity_factors)
    modelso.max_tax_free = {}
    modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
    modelso.forecastSRI = modelno.delta.forecastSRI
    modelso.southern_initialization_routine(startTime, scenario)
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
    for t in range(0, timeseries_length):
      if (t % 365 == 364):
        print('Year ', (t+1)/365, ', ', datetime.now() - startTime)
      # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
      swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

      swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.max_tax_free, flood_release, flood_volume)
	  
    for n in new_inputs.sensitivity_factors['factor_list']:
      param_df[n][x] = new_inputs.sensitivity_factors[n]['realization']
	  
    sensitivity_df['SWP_%s' % x] = pd.Series(modelso.annual_SWP)
    sensitivity_df['CVP_%s' % x] = pd.Series(modelso.annual_CVP)
    sensitivity_df['SMI_deliver_%s' %x] = pd.Series(modelso.semitropic.annual_supplies['delivery'])
    sensitivity_df['SMI_take_%s' %x] = pd.Series(modelso.semitropic.annual_supplies['leiu_applied'])
    sensitivity_df['SMI_give_%s' %x] = pd.Series(modelso.semitropic.annual_supplies['leiu_delivered'])
    sensitivity_df['WON_land_%s' %x] = pd.Series(modelso.wonderful.annual_supplies['acreage'])

    try:
      data_output(output_list, results_folder, clean_output, x, new_inputs.sensitivity_factors, modelno, modelso)
    except:
      print('Sensitivity sample ' + str(x) + ' failed to write to hdf5')

    if (save_full):
      pd.to_pickle(modelno, results_folder + '/modelno' + str(x) + '.pkl')
      pd.to_pickle(modelso, results_folder + '/modelso' + str(x) + '.pkl')

    del modelno
    del modelso

  param_df.to_csv(results_folder + '/sensitivity_params.csv')
  sensitivity_df.to_csv(results_folder + '/sensitivity_results.csv')

######################################################################################
###validation/simulation modes
######################################################################################
elif model_mode == 'simulation' or model_mode == 'validation':
  ######################################################################################
  #   # Model Class Initialization
  ## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
  ##
  modelno = Model(input_data_file, expected_release_datafile, model_mode, demand_type)
  modelso = Model(input_data_file, expected_release_datafile, model_mode, demand_type)
  modelso.max_tax_free = {}
  modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
  modelso.forecastSRI = modelno.delta.forecastSRI
  modelso.southern_initialization_routine(startTime)

  ######################################################################################
  ###Model Simulation
  ######################################################################################
  if (short_test < 0):
    timeseries_length = min(modelno.T, modelso.T)
  else:
    timeseries_length = short_test
  ###initial parameters for northern model input
  ###generated from southern model at each timestep
  swp_release = 1
  cvp_release = 1
  swp_release2 = 1
  cvp_release2 = 1
  swp_pump = 999.0
  cvp_pump = 999.0
  proj_surplus = 0.0
  swp_available = 0.0
  cvp_available = 0.0
  ############################################
  for t in range(0, timeseries_length):
    if (t % 365 == 364):
      print('Year ', (t+1)/365, ', ', datetime.now() - startTime)
    # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
    swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

    swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.max_tax_free, flood_release, flood_volume)


  ### record results
  # district_output_list = [modelso.berrenda, modelso.belridge, modelso.buenavista, modelso.cawelo, modelso.henrymiller, modelso.ID4, modelso.kerndelta, modelso.losthills, modelso.rosedale, modelso.semitropic, modelso.tehachapi, modelso.tejon, modelso.westkern, modelso.wheeler, modelso.kcwa,
  #                         modelso.chowchilla, modelso.maderairr, modelso.arvin, modelso.delano, modelso.exeter, modelso.kerntulare, modelso.lindmore, modelso.lindsay, modelso.lowertule, modelso.porterville,
  #                         modelso.saucelito, modelso.shaffer, modelso.sosanjoaquin, modelso.teapot, modelso.terra, modelso.tulare, modelso.fresno, modelso.fresnoid,
  #                         modelso.socal, modelso.southbay, modelso.centralcoast, modelso.dudleyridge, modelso.tularelake, modelso.westlands, modelso.othercvp, modelso.othercrossvalley, modelso.otherswp, modelso.otherfriant]
  district_output_list = modelso.district_list
  district_results = modelso.results_as_df('daily', district_output_list)
  district_results.to_csv(results_folder + '/district_results_' + model_mode + '.csv')
  del district_results
  district_results = modelso.results_as_df_full('daily', district_output_list)
  district_results.to_csv(results_folder + '/district_results_full_' + model_mode + '.csv')
  del district_results
  district_results_annual = modelso.results_as_df('annual', district_output_list)
  district_results_annual.to_csv(results_folder + '/annual_district_results_' + model_mode + '.csv')
  del district_results_annual

  private_results_annual = modelso.results_as_df('annual', modelso.private_list)
  private_results_annual.to_csv(results_folder + '/annual_private_results_' + model_mode + '.csv')
  private_results = modelso.results_as_df('daily', modelso.private_list)
  private_results.to_csv(results_folder + '/annual_private_results_' + model_mode + '.csv')
  del private_results,private_results_annual

  contract_results = modelso.results_as_df('daily', modelso.contract_list)
  contract_results.to_csv(results_folder + '/contract_results_' + model_mode + '.csv')
  contract_results_annual = modelso.results_as_df('annual', modelso.contract_list)
  contract_results_annual.to_csv(results_folder + '/contract_results_annual_' + model_mode + '.csv')
  del contract_results, contract_results_annual

  northern_res_list = [modelno.shasta, modelno.folsom, modelno.oroville, modelno.yuba, modelno.newmelones,
                     modelno.donpedro, modelno.exchequer, modelno.delta]
  southern_res_list = [modelso.sanluisstate, modelso.sanluisfederal, modelso.millerton, modelso.isabella,
                     modelso.kaweah, modelso.success, modelso.pineflat]
  reservoir_results_no = modelno.results_as_df('daily', northern_res_list)
  reservoir_results_no.to_csv(results_folder + '/reservoir_results_no_' + model_mode + '.csv')
  del reservoir_results_no
  reservoir_results_so = modelso.results_as_df('daily', southern_res_list)
  reservoir_results_so.to_csv(results_folder + '/reservoir_results_so_' + model_mode + '.csv')
  del reservoir_results_so

  canal_results = modelso.results_as_df('daily', modelso.canal_list)
  canal_results.to_csv(results_folder + '/canal_results_' + model_mode + '.csv')
  del canal_results

  bank_results = modelso.bank_as_df('daily', modelso.waterbank_list)
  bank_results.to_csv(results_folder + '/bank_results_' + model_mode + '.csv')
  bank_results_annual = modelso.bank_as_df('annual', modelso.waterbank_list)
  bank_results_annual.to_csv(results_folder + '/bank_results_annual_' + model_mode + '.csv')
  del bank_results, bank_results_annual

  leiu_results = modelso.bank_as_df('daily', modelso.leiu_list)
  leiu_results.to_csv(results_folder + '/leiu_results_' + model_mode + '.csv')
  leiu_results_annual = modelso.bank_as_df('annual', modelso.leiu_list)
  leiu_results_annual.to_csv(results_folder + '/leiu_results_annual_' + model_mode + '.csv')
  del leiu_results, leiu_results_annual

print ('completed in ', datetime.now() - startTime)



