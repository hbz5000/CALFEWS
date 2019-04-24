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


#model_mode = 'simulation'
model_mode = 'validation'
# model_mode = 'forecast'

startTime = datetime.now()

# To run full dataset, short_test = -1. Else enter number of days to run, starting at sd. e.g. 365 for 1 year only.
short_test = 3650

# always use shorter historical dataframe for expected delta releases
expected_release_datafile = 'cord/data/input/cord-data.csv'

# data for actual simulation
if model_mode == 'simulation':
  # sd = '10-01-1996'
  # input_data_file = 'cord/data/input/cord-data.csv'
  sd = '10-01-1905'
  input_data_file = 'cord/data/input/cord-data-sim.csv'
elif model_mode == 'validation':
  sd = '10-01-1996'
  input_data_file = 'cord/data/input/cord-data.csv'
elif model_mode == 'forecast':
  sd = '01-01-1950'
  base_data_file = 'cord/data/input/cord-data.csv'
if model_mode == 'simulation' or model_mode == 'validation':
  ######################################################################################
  # Model Class Initialization
  ## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
  ##
  modelno = Model(input_data_file, expected_release_datafile, sd, model_mode)
  modelso = Model(input_data_file, expected_release_datafile, sd, model_mode)
  modelso.max_tax_free = {}
  modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
  modelso.forecastSRI = modelno.delta.forecastSRI
  modelso.southern_initialization_routine(startTime, modelno.delta.forecastSRI)

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
######################################################################################
else:
  #####FLOW GENERATOR#####
  #seed
  np.random.seed(1001)

  file_folder = 'cord/data/CA_FNF_climate_change/'
  model_name_list = ['gfdl-esm2m']#, 'canesm2', 'ccsm4', 'cnrm-cm5', 'csiro-mk3-6-0', 'gfdl-cm3', 'hadgem2-cc', 'hadgem2-es', 'inmcm4', 'ipsl-cm5a-mr', 'miroc5']
  proj_list = ['rcp45']#, 'rcp85']
  new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode)
  new_inputs.initialize_reservoirs()
  new_inputs.generate_relationships('XXX')
  new_inputs.autocorrelate_residuals('XXX')
  new_inputs.fill_snowpack('XXX')
  new_inputs.generate_relationships_delta('XXX')
  new_inputs.autocorrelate_residuals_delta('XXX')
  for model_name in model_name_list:
    for projection in proj_list:
      file_name = 'CA_FNF_' + model_name + '_' + projection + '_r1i1p1.csv'
      print('Starting ' + file_name)
      new_inputs.run_routine(file_folder, file_name, 'daily', 1, 150, 2, '1/1/1950', '12/31/2099', 1950)
      input_data_file = file_folder + 'cord-data-' + file_name

      ######################################################################################
      # Model Class Initialization
      ## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
      ##
      modelno = Model(input_data_file, expected_release_datafile, sd, model_mode)
      modelso = Model(input_data_file, expected_release_datafile, sd, model_mode)
      modelso.max_tax_free = {}
      modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
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
          print('Year ', (t+1)/365, ', ', datetime.now() - startTime)        # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
        swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

        swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.max_tax_free, flood_release, flood_volume)
        ######################################################################################
      release_df = pd.DataFrame(index=modelno.index)
      northern_res_list = [modelno.shasta, modelno.folsom, modelno.oroville, modelno.yuba, modelno.newmelones,
                           modelno.donpedro, modelno.exchequer]
      southern_res_list = [modelso.millerton, modelso.success, modelso.kaweah, modelso.isabella]
      canal_list = [modelso.fkc, modelso.madera, modelso.kernriverchannel, modelso.kaweahriverchannel,
                    modelso.tuleriverchannel]
      canal_turnout_list = ['OFK', 'MAD', 'CWY', 'OKW', 'OTL']
      pump_list = [modelno.delta.TRP_pump, modelno.delta.HRO_pump, modelso.calaqueduct.daily_flow['OSW'],
                   modelso.calaqueduct.daily_flow['WRM'], modelso.calaqueduct.daily_flow['SOC']]
      pump_names = ['TRP_pump', 'HRO_pump', 'DOS_pump', 'BVA_pump', 'EDM_pump']
      for x in northern_res_list:
        temp_df = pd.DataFrame(index=modelno.index)
        temp_df['%s_release' % x.key] = pd.Series(x.R, index=modelno.index)
        release_df = pd.concat([release_df, temp_df], axis=1)
      for x in southern_res_list:
        temp_df = pd.DataFrame(index=modelno.index)
        temp_df['%s_release' % x.key] = pd.Series(x.R, index=modelso.index)
        release_df = pd.concat([release_df, temp_df], axis=1)
      for x, y in zip(canal_list, canal_turnout_list):
        temp_df = pd.DataFrame(index=modelno.index)
        temp_df['%s_release' % x.key] = pd.Series(x.daily_flow[y], index=modelso.index)
        release_df = pd.concat([release_df, temp_df], axis=1)
      for x, y in zip(pump_list, pump_names):
        temp_df = pd.DataFrame(index=modelno.index)
        temp_df[y] = pd.Series(x, index=modelso.index)
        release_df = pd.concat([release_df, temp_df], axis=1)
      release_df.to_csv('cord/data/results/release_results_' + file_name)

      # del modelno
      # del modelso
      # del release_df

######################################################################################
###Record Simulation Results
######################################################################################

if model_mode == 'validation' or model_mode == 'simulation':
  district_output_list = [modelso.berrenda, modelso.belridge, modelso.buenavista, modelso.cawelo, modelso.henrymiller, modelso.ID4, modelso.kerndelta, modelso.losthills, modelso.rosedale, modelso.semitropic, modelso.tehachapi, modelso.tejon, modelso.westkern, modelso.wheeler, modelso.kcwa,
                          modelso.arvin, modelso.delano, modelso.exeter, modelso.kerntulare, modelso.lindmore, modelso.lindsay, modelso.lowertule, modelso.porterville,
                          modelso.saucelito, modelso.shaffer, modelso.sosanjoaquin, modelso.teapot, modelso.terra, modelso.tulare, modelso.fresno, modelso.fresnoid,
                          modelso.socal, modelso.southbay, modelso.centralcoast, modelso.dudleyridge, modelso.tularelake, modelso.westlands, modelso.othercvp, modelso.othercrossvalley, modelso.otherswp, modelso.otherfriant]
  district_results = modelso.results_as_df('daily', district_output_list)
  district_results.to_csv('cord/data/results/district_results_' + model_mode + '.csv')
  del district_results

  district_results = modelso.results_as_df_full('daily', district_output_list)
  district_results.to_csv('cord/data/results/district_results_full_' + model_mode + '.csv')
  del district_results
  district_results_annual = modelso.results_as_df('annual', district_output_list)
  district_results_annual.to_csv('cord/data/results/annual_district_results_' + model_mode + '.csv')
  #del district_results_annual
  private_results_annual = modelso.results_as_df('annual', modelso.private_list)
  private_results_annual.to_csv('cord/data/annual_private_reults_' + model_mode + '.csv')
  private_results = modelso.results_as_df('daily', modelso.private_list)
  private_results.to_csv('cord/data/annual_private_reults_' + model_mode + '.csv')

  contract_results = modelso.results_as_df('daily', modelso.contract_list)
  contract_results.to_csv('cord/data/results/contract_results_' + model_mode + '.csv')
  contract_results_annual = modelso.results_as_df('annual', modelso.contract_list)
  contract_results_annual.to_csv('cord/data/results/contract_results_annual_' + model_mode + '.csv')
  del contract_results, contract_results_annual

  northern_res_list = [modelno.shasta, modelno.folsom, modelno.oroville, modelno.yuba, modelno.newmelones,
                     modelno.donpedro, modelno.exchequer, modelno.delta]
  southern_res_list = [modelso.sanluisstate, modelso.sanluisfederal, modelso.millerton, modelso.isabella,
                     modelso.kaweah, modelso.success, modelso.pineflat]
  reservoir_results_no = modelno.results_as_df('daily', northern_res_list)
  reservoir_results_no.to_csv('cord/data/results/reservoir_results_no_' + model_mode + '.csv')
  del reservoir_results_no
  
  reservoir_results_so = modelso.results_as_df('daily', southern_res_list)
  reservoir_results_so.to_csv('cord/data/results/reservoir_results_so_' + model_mode + '.csv')
  del reservoir_results_so

  canal_results = modelso.results_as_df('daily', modelso.canal_list)
  canal_results.to_csv('cord/data/results/canal_results_' + model_mode + '.csv')
  del canal_results

  bank_results = modelso.bank_as_df('daily', modelso.waterbank_list)
  bank_results.to_csv('cord/data/results/bank_results_' + model_mode + '.csv')
  bank_results_annual = modelso.bank_as_df('annual', modelso.waterbank_list)
  bank_results_annual.to_csv('cord/data/results/bank_results_annual_' + model_mode + '.csv')
  del bank_results, bank_results_annual

  leiu_results = modelso.bank_as_df('daily', modelso.leiu_list)
  leiu_results.to_csv('cord/data/results/leiu_results_' + model_mode + '.csv')
  leiu_results_annual = modelso.bank_as_df('annual', modelso.leiu_list)
  leiu_results_annual.to_csv('cord/data/results/leiu_results_annual_' + model_mode + '.csv')
  del leiu_results, leiu_results_annual

print ('completed in ', datetime.now() - startTime)



