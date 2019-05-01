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
# # scenario = 'baseline'  # run baseline scenario: friant @ wy2010, no change to LWT
# # simulation_scenarios = Scenario()
# scenario = {}
# # # simulation_scenarios.FKC_capacity_normal.keys()
# scenario['FKC_capacity_normal'] = 'normal_wy2017'
# # # simulation_scenarios.LWT_in_district_direct_recharge.keys()
# scenario['LWT_in_district_direct_recharge'] = 'baseline'
# scenario['LWT_in_leiu_banking'] = 'false'
# # scenario['LWT_participant_list'] = 'KRT'
# # scenario['LWT_leiu_ownership'] = 'LWT_only'
# # scenario['LWT_inleiucap'] = 'none'
# # scenario['LWT_leiu_recovery'] = 'same_ARV'

# # folder for results (no backslash at end)
# results_folder = 'cord/data/results/friant_wy2017'
# os.makedirs(results_folder, exist_ok=True)

scenario1 = {}
scenario1['FKC_capacity_normal'] = 'normal_wy2017'
scenario1['LWT_in_district_direct_recharge'] = 'baseline'
scenario1['LWT_in_leiu_banking'] = 'false'

scenario2 = {}
scenario2['FKC_capacity_normal'] = 'normal'
scenario2['LWT_in_district_direct_recharge'] = 'baseline'
scenario2['LWT_in_leiu_banking'] = 'false'

scenario3 = {}
scenario3['FKC_capacity_normal'] = 'normal_rehab_wy2019'
scenario3['LWT_in_district_direct_recharge'] = 'baseline'
scenario3['LWT_in_leiu_banking'] = 'false'

scenario4 = {}
scenario4['FKC_capacity_normal'] = 'normal_rehab_wy2019_kings_5ave_full'
scenario4['LWT_in_district_direct_recharge'] = 'baseline'
scenario4['LWT_in_leiu_banking'] = 'false'

scenario5 = {}
scenario5['FKC_capacity_normal'] = 'normal_rehab_wy2019'
scenario5['LWT_in_district_direct_recharge'] = 'double'
scenario5['LWT_in_leiu_banking'] = 'false'

scenario6 = {}
scenario6['FKC_capacity_normal'] = 'normal_rehab_wy2019'
scenario6['LWT_in_district_direct_recharge'] = 'double'
scenario6['LWT_in_leiu_banking'] = 'true'
scenario6['LWT_participant_list'] = 'KRT'
scenario6['LWT_leiu_ownership'] = 'LWT_only'
scenario6['LWT_inleiucap'] = 'none'
scenario6['LWT_leiu_recovery'] = 'same_ARV'

scenarios = [scenario1, scenario2, scenario3, scenario4, scenario5, scenario6]
results_folders = ['cord/data/results/friant_wy2017',
                   'cord/data/results/friant_rehab_full',
                   'cord/data/results/friant_rehab_wy2019',
                   'cord/data/results/friant_rehab_wy2019_kings_5ave_full',
                   'cord/data/results/friant_rehab_wy2019__LWT_recharge_double',
                   'cord/data/results/friant_rehab_wy2019__LWT_recharge_double__LWT_in_leiu_banking_KRT']

for i in range(len(scenarios)):
  try:
    scenario = scenarios[i]
    results_folder = results_folders[i]
    os.makedirs(results_folder, exist_ok=True)
    ##################################################################

    # always use shorter historical dataframe for expected delta releases
    expected_release_datafile = 'cord/data/input/cord-data.csv'

    # data for actual simulation
    sd = '10-01-1905'
    input_data_file = 'cord/data/input/cord-data-sim.csv'

    ######################################################################################
    # Model Class Initialization
    ## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
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

  except:
    print(results_folder + ' `failed')

