##################################################################################
# Separate script to run alternative infrastructure/contract/ect scenarios, for comparison to baseline
##################################################################################

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cord
from cord import *
from datetime import datetime

startTime = datetime.now()

################################################################
# parameters for run-type
#################################################################
# only run alternative scenarios in simulation mode
model_mode = 'simulation'

# To run full dataset, short_test = -1. Else enter number of days to run, starting at sd. e.g. 365 for 1 year only.
short_test = -1

### simulation scenarios for testing (see model.set_regulations_current_south)
scenarios = []

scenario1 = {}
scenario1['results_folder'] = 'cord/data/results/FKC_capacity_wy2017'
scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_wy2017.json'
scenario1['LWT'] = 'baseline'
scenarios.append(scenario1)

scenario1 = {}
scenario1['results_folder'] = 'cord/data/results/FKC_capacity_rehab_full'
scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_rehab_full.json'
scenario1['LWT'] = 'baseline'
scenarios.append(scenario1)

scenario1 = {}
scenario1['results_folder'] = 'cord/data/results/FKC_capacity_wy2017__LWT_inleiubank_ARV_0'
scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_wy2017.json'
scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_ARV_0.json'
scenarios.append(scenario1)

scenario1 = {}
scenario1['results_folder'] = 'cord/data/results/FKC_capacity_rehab_full__LWT_inleiubank_ARV_0'
scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_rehab_full.json'
scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_ARV_0.json'
scenarios.append(scenario1)

scenario1 = {}
scenario1['results_folder'] = 'cord/data/results/FKC_capacity_wy2017__LWT_inleiubank_ARV_withRecharge_100'
scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_wy2017.json'
scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_ARV_withRecharge_100.json'
scenarios.append(scenario1)

scenario1 = {}
scenario1['results_folder'] = 'cord/data/results/FKC_capacity_rehab_full__LWT_inleiubank_withRecharge_100'
scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_rehab_full.json'
scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_ARV_withRecharge_100.json'
scenarios.append(scenario1)

# scenario1 = {}
# scenario1['results_folder'] = 'cord/data/results/FKC_capacity_wy2017__LWT_inleiubank_ARV_025'
# scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_wy2017.json'
# scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_ARV_025.json'
# scenarios.append(scenario1)

# scenario1 = {}
# scenario1['results_folder'] = 'cord/data/results/FKC_capacity_wy2017__LWT_inleiubank_DLEKRTSSJSFW_0'
# scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_wy2017.json'
# scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_DLEKRTSSJSFW_0.json'
# scenarios.append(scenario1)
#
# scenario1 = {}
# scenario1['results_folder'] = 'cord/data/results/FKC_capacity_rehab_full__LWT_inleiubank_DLEKRTSSJSFW_0'
# scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_rehab_full.json'
# scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_DLEKRTSSJSFW_0.json'
# scenarios.append(scenario1)

# scenario1 = {}
# scenario1['results_folder'] = 'cord/data/results/FKC_capacity_wy2017__LWT_inleiubank_DLEKRTSSJSFW_0125'
# scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_wy2017.json'
# scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_DLEKRTSSJSFW_0125.json'
# scenarios.append(scenario1)

# scenario1 = {}
# scenario1['results_folder'] = 'cord/data/results/FKC_capacity_rehab_full__LWT_inleiubank_DLEKRTSSJSFW_0125'
# scenario1['FKC'] = 'cord/scenarios/FKC_properties__capacity_rehab_full.json'
# scenario1['LWT'] = 'cord/scenarios/LWT_properties__inleiubank_DLEKRTSSJSFW_0125.json'
# scenarios.append(scenario1)

for i in [4,5]:
  # try:
    scenario = scenarios[i]
    results_folder = scenarios[i]['results_folder']
    print(results_folder)
    os.makedirs(results_folder, exist_ok=True)
    pd.to_pickle(scenario, results_folder + '/scenario.pkl')
    ##################################################################

    # always use shorter historical dataframe for expected delta releases
    expected_release_datafile = 'cord/data/input/cord-data.csv'

    # data for actual simulation
    sd = '10-01-1905'
    input_data_file = 'cord/data/input/cord-data-sim.csv'

    ######################################################################################
    # Model Class Initialization
    ## There are two instances of the class 'Model', one for the Northern System and one for the Southern System
    ##
    modelno = Model(input_data_file, expected_release_datafile, sd, model_mode)
    modelso = Model(input_data_file, expected_release_datafile, sd, model_mode)
    modelso.max_tax_free = {}
    modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
    modelso.forecastSRI = modelno.delta.forecastSRI
    modelso.southern_initialization_routine(startTime, modelno.delta.forecastSRI, scenario)

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
        print('Year ', (t + 1) / 365, ', ', datetime.now() - startTime)
      # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
      swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, \
      swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2,
                                                                           cvp_release2, swp_pump, cvp_pump)

      swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping,
                                                                                                        cvp_pumping,
                                                                                                        swp_alloc,
                                                                                                        cvp_alloc,
                                                                                                        proj_surplus,
                                                                                                        max_pumping,
                                                                                                        swp_forgo,
                                                                                                        cvp_forgo, swp_AF,
                                                                                                        cvp_AF, swp_AS,
                                                                                                        cvp_AS,
                                                                                                        modelno.delta.forecastSJWYT,
                                                                                                        modelno.delta.max_tax_free,
                                                                                                        flood_release,
                                                                                                        flood_volume)

    ######################################################################################
    ###Record Simulation Results
    ######################################################################################

    # district_output_list = [modelso.rosedale, modelso.semitropic, modelso.chowchilla, modelso.maderairr, modelso.arvin,
    #                         modelso.delano, modelso.exeter, modelso.kerntulare, modelso.lindmore, modelso.lindsay,
    #                         modelso.lowertule, modelso.porterville, modelso.saucelito, modelso.shaffer, modelso.sosanjoaquin,
    #                         modelso.teapot, modelso.terra, modelso.tulare, modelso.fresno, modelso.fresnoid,
    #                         modelso.socal, modelso.southbay, modelso.centralcoast,modelso.tularelake, modelso.othercvp,
    #                         modelso.othercrossvalley, modelso.otherfriant]
    district_output_list = modelso.district_list
    district_results = modelso.results_as_df('daily', district_output_list)
    district_results.to_csv(results_folder + '/district_results_' + model_mode + '.csv')
    del district_results

    district_results = modelso.results_as_df_full('daily', district_output_list)
    district_results.to_csv(results_folder + '/district_results_full_' + model_mode + '.csv')
    del district_results
    district_results_annual = modelso.results_as_df('annual', district_output_list)
    district_results_annual.to_csv(results_folder + '/annual_district_results_' + model_mode + '.csv')
    # del district_results_annual
    private_results_annual = modelso.results_as_df('annual', modelso.private_list)
    private_results_annual.to_csv(results_folder + '/annual_private_results_' + model_mode + '.csv')
    private_results = modelso.results_as_df('daily', modelso.private_list)
    private_results.to_csv(results_folder + '/annual_private_results_' + model_mode + '.csv')
    del private_results, private_results_annual

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

    print('completed ' + results_folder + ' in ', datetime.now() - startTime)

  # except:
  #   print(results_folder + ' `failed')

