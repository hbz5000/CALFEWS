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
from cord import *


#model_mode = 'simulation'
#model_mode = 'validation'
model_mode = 'forecast'
if model_mode == 'simulation':
  sd = '10-01-1905'
  input_data_file = 'cord/data/cord-data-sim.csv'
elif model_mode == 'validation':
  sd = '10-01-1996'
  input_data_file = 'cord/data/cord-data.csv'
elif model_mode == 'forecast':
  sd = '01-01-1950'
  base_data_file = 'cord/data/cord-data.csv'
if model_mode == 'simulation' or model_mode == 'validation':
  ######################################################################################
  # Model Class Initialization
  ## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
  ## 
  modelno = Model(input_data_file, sd)
  modelso = Model(input_data_file, sd)
  modelso.max_tax_free = {}
  modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(model_mode)
  modelso.southern_initialization_routine(model_mode)
  ######################################################################################
  ###Model Simulation
  ######################################################################################
  timeseries_length = min(modelno.T, modelso.T)
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
    print(t)
    #the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
    swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF ,swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump, model_mode)
  
    swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.max_tax_free, flood_release, flood_volume, model_mode)
######################################################################################
else:
  #####FLOW GENERATOR#####
  file_folder = 'cord/data/CA_FNF_climate_change/'
  model_name_list = ['gfdl-esm2m', 'canesm2', 'ccsm4', 'cnrm-cm5', 'csiro-mk3-6-0', 'gfdl-cm3', 'hadgem2-cc', 'hadgem2-es', 'inmcm4', 'ipsl-cm5a-mr', 'miroc5']
  proj_list = ['rcp45', 'rcp85']
  new_inputs = Inputter(base_data_file, model_mode)
  new_inputs.initialize_reservoirs()
  new_inputs.generate_relationships('XXX')
  new_inputs.autocorrelate_residuals('XXX')
  new_inputs.fill_snowpack('XXX')
  new_inputs.generate_relationships_delta('XXX')
  new_inputs.autocorrelate_residuals_delta('XXX')
  for model_name in model_name_list:
    for projection in proj_list:
      file_name = 'CA_FNF_' + model_name + '_' + projection + '_r1i1p1.csv'
      new_inputs.run_routine(file_folder, file_name, 'daily', 1, 150, 2, '1/1/1950', '12/31/2099', 1950)
      input_data_file = file_folder + 'cord-data-' + file_name

      ######################################################################################
      # Model Class Initialization
      ## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
      ## 
      modelno = Model(input_data_file, sd)
      modelso = Model(input_data_file, sd)
      modelso.max_tax_free = {}
      modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(model_mode)
      modelso.southern_initialization_routine(model_mode)
      ######################################################################################
      ###Model Simulation
      ######################################################################################
      timeseries_length = min(modelno.T, modelso.T)
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
        print(t)
        #the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
        swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF ,swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump, model_mode)
  
        swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.max_tax_free, flood_release, flood_volume, model_mode)
        ######################################################################################
      release_df = pd.DataFrame(index = modelno.index)
      northern_res_list = [modelno.shasta, modelno.folsom, modelno.oroville, modelno.yuba, modelno.newmelones, modelno.donpedro, modelno.exchequer]
      southern_res_list = [modelso.millerton, modelso.success, modelso.kaweah, modelso.isabella]
      canal_list = [modelso.fkc, modelso.madera, modelso.kernriverchannel, modelso.kaweahriverchannel, modelso.tuleriverchannel]
      canal_turnout_list = ['OFK', 'MAD', 'CWY', 'OKW', 'OTL']
      pump_list = [modelno.delta.TRP_pump, modelno.delta.HRO_pump, modelso.calaqueduct.daily_flow['OSW'], modelso.calaqueduct.daily_flow['WRM'], modelso.calaqueduct.daily_flow['SOC']]
      pump_names = ['TRP_pump', 'HRO_pump', 'DOS_pump', 'BVA_pump', 'EDM_pump']
      for x in northern_res_list:
        temp_df = pd.DataFrame(index = modelno.index)
        temp_df['%s_release' % x.key] = pd.Series(x.R, index = modelno.index)
        release_df = pd.concat([release_df, temp_df], axis = 1)
      for x in southern_res_list:
        temp_df = pd.DataFrame(index = modelno.index)
        temp_df['%s_release' % x.key] = pd.Series(x.R, index = modelso.index)
        release_df = pd.concat([release_df, temp_df], axis = 1)
      for x,y in zip(canal_list, canal_turnout_list):
        temp_df = pd.DataFrame(index = modelno.index)
        temp_df['%s_release' % x.key] = pd.Series(x.daily_flow[y], index = modelso.index)
        release_df = pd.concat([release_df, temp_df], axis = 1)
      for x,y in zip(pump_list, pump_names):
        temp_df = pd.DataFrame(index = modelno.index)
        temp_df[y] = pd.Series(x, index = modelso.index)
        release_df = pd.concat([release_df, temp_df], axis = 1)
      release_df.to_csv('cord/data/release_results_' + file_name)
	  
      del modelno
      del modelso
      del release_df

######################################################################################
###Record Simulation Results
######################################################################################
if model_mode == 'validation' or model_mode == 'simulation':  
  district_results = modelso.results_as_df('daily', modelso.district_list)
  district_results.to_csv('cord/data/district_results_' + model_mode + '.csv')
  district_results_annual = modelso.results_as_df('annual', modelso.district_list)
  district_results_annual.to_csv('cord/data/annual_district_results_' + model_mode + '.csv')

  contract_results = modelso.results_as_df('daily', modelso.contract_list)
  contract_results.to_csv('cord/data/contract_results_' + model_mode + '.csv')
  contract_results_annual = modelso.results_as_df('annual', modelso.contract_list)
  contract_results_annual.to_csv('cord/data/contract_results_annual_' + model_mode + '.csv')

  northern_res_list = [modelno.shasta, modelno.folsom, modelno.oroville, modelno.yuba, modelno.newmelones, modelno.donpedro, modelno.exchequer, modelno.delta]
  southern_res_list = [modelso.sanluisstate, modelso.sanluisfederal, modelso.millerton, modelso.isabella]

  reservoir_results_no = modelno.results_as_df('daily', northern_res_list)
  reservoir_results_no.to_csv('cord/data/reservoir_results_no_' + model_mode + '.csv')
  reservoir_results_so = modelso.results_as_df('daily', southern_res_list)
  reservoir_results_so.to_csv('cord/data/reservoir_results_so_' + model_mode + '.csv')

  canal_results = modelso.results_as_df('daily', modelso.canal_list)
  canal_results.to_csv('cord/data/canal_results_' + model_mode + '.csv')

  bank_results = modelso.bank_as_df('daily', modelso.waterbank_list)
  bank_results.to_csv('cord/data/bank_results_' + model_mode + '.csv')
  bank_results_annual = modelso.bank_as_df('annual', modelso.waterbank_list)
  bank_results_annual.to_csv('cord/data/bank_results_annual_' + model_mode + '.csv')


  leiu_results = modelso.bank_as_df('daily', modelso.leiu_list)
  leiu_results.to_csv('cord/data/leiu_results_' + model_mode + '.csv')
  leiu_results_annual = modelso.bank_as_df('annual', modelso.leiu_list)
  leiu_results_annual.to_csv('cord/data/leiu_results_annual_' + model_mode + '.csv')




