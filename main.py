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

path_model = './'
path_model = sys.argv[1]
#print (sys.argv)
os.chdir(path_model)

startTime = datetime.now()

# get runtime params from config file
config = ConfigObj('cord/data/input/runtime_params.ini')
parallel_mode = bool(strtobool(config['parallel_mode']))
model_mode = config['model_mode']
short_test = int(config['short_test'])
print_log = bool(strtobool(config['print_log']))
seed = int(config['seed'])
scenario_name = config['scenario_name'] #scenarios provide information on infrastructural plans
flow_input_type = config['flow_input_type']
flow_input_source = config['flow_input_source']
total_sensitivity_factors = int(config['total_sensitivity_factors'])
sensitivity_sample_file = config['sensitivity_sample_file']
output_list = config['output_list']
output_directory = config['output_directory']
clean_output = bool(strtobool(config['clean_output']))
save_full = bool(strtobool(config['save_full']))

if parallel_mode == True:
  from mpi4py import MPI
  import math
  import time

  # =============================================================================
  # Experiment set up
  # =============================================================================
  # Functions or anything else that will be called
  #
  # =============================================================================
  # Start parallelization
  # =============================================================================

  # Parallel simulation
  comm = MPI.COMM_WORLD

  # Number of processors and the rank of processors
  rank = comm.Get_rank()
  nprocs = comm.Get_size()

  # Determine the chunk which each processor will neeed to do
  count = int(math.floor(total_sensitivity_factors/nprocs))
  remainder = total_sensitivity_factors % nprocs

  # Use the processor rank to determine the chunk of work each processor will do
  if rank < remainder:
    start = rank*(count+1)
    stop = start + count + 1
  else:
    start = remainder*(count+1) + (rank-remainder)*count
    stop = start + count

else: # non-parallel mode
  start = 0
  stop = total_sensitivity_factors
  rank = 0

# infrastructure scenario file, to be used for all sensitivity samples
with open('cord/scenarios/scenarios_main.json') as f:
  scenarios = json.load(f)
scenario = scenarios[scenario_name]
results_folder = output_directory + '/' + scenario_name
os.makedirs(results_folder, exist_ok=True)
shutil.copy('cord/data/input/runtime_params.ini', results_folder + '/runtime_params.ini')

# make separate output folder for each processor
results_folder = results_folder + '/p' + str(rank)
os.makedirs(results_folder, exist_ok=True)

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

# output all print statements to log file. separate for each processor.
if print_log:
  sys.stdout = open(results_folder + '/log_p' + str(rank) + '.txt', 'w')

if parallel_mode:
  print ("Processor rank: %d , out of %d !" % (comm.rank, comm.size))
  print ("Hello from rank %d out of %d !" % (comm.rank, comm.size))


# =============================================================================
# Loop though all samples, run sensitivity analysis. If parallel, k runs only through subset of samples for each processor.
# =============================================================================
if model_mode == 'simulation' or model_mode == 'validation':
  stop = 1
print(start)
print(stop)
print(model_mode)
for k in range(start, stop):

  print('#######################################################')
  print('Sample ' + str(k) + ' start')
  sys.stdout.flush()

  # put everything in "try", so error on one sample run won't crash whole job. But this makes it hard to debug, so may want to comment this out when debugging.
  # try:
    ######################################################################################
  if model_mode == 'sensitivity':
    #####FLOW GENERATOR#####
    #seed
    if (seed > 0):
      np.random.seed(seed)
    print(k)
    # read in k'th sample from sensitivity sample file
    sensitivity_sample = np.genfromtxt(sensitivity_sample_file, delimiter='\t', skip_header=k+1, max_rows=1)[1:]
    with open(sensitivity_sample_file, 'r') as f:
      sensitivity_sample_names = f.readlines()[0].split('\n')[0]
    np.savetxt(results_folder + '/sample' + str(k) + '.txt', sensitivity_sample.reshape(1, len(sensitivity_sample)), delimiter=',', header=sensitivity_sample_names)
    sensitivity_sample_names = sensitivity_sample_names.split('\t')[1:]

    #Initialize flow input scenario based on sensitivity sample
    new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode, results_folder, k, sensitivity_sample_names, sensitivity_sample, use_sensitivity = False)
    new_inputs.run_initialization('XXX')
    new_inputs.run_routine(flow_input_type, flow_input_source)
    input_data_file = results_folder + '/' + new_inputs.export_series[flow_input_type][flow_input_source]  + "_"  + str(k) + ".csv"
    modelno = Model(input_data_file, expected_release_datafile, model_mode, demand_type, k, sensitivity_sample_names, sensitivity_sample, new_inputs.sensitivity_factors)
    modelso = Model(input_data_file, expected_release_datafile, model_mode, demand_type, k, sensitivity_sample_names, sensitivity_sample, new_inputs.sensitivity_factors)
    modelso.max_tax_free = {}
    modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
    modelso.forecastSRI = modelno.delta.forecastSRI
    modelso.southern_initialization_routine(startTime, scenario)
    sys.stdout.flush()
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
        sys.stdout.flush()
      # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
      swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

      swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.forecastSCWYT, modelno.delta.max_tax_free, flood_release, flood_volume)

    # for n in new_inputs.sensitivity_factors['factor_list']:
    #   param_df[n][k] = new_inputs.sensitivity_factors[n]['realization']
    #
    # sensitivity_df['SWP_%s' % k] = pd.Series(modelso.annual_SWP)
    # sensitivity_df['CVP_%s' % k] = pd.Series(modelso.annual_CVP)
    # sensitivity_df['SMI_deliver_%s' %k] = pd.Series(modelso.semitropic.annual_supplies['delivery'])
    # sensitivity_df['SMI_take_%s' %k] = pd.Series(modelso.semitropic.annual_supplies['leiu_applied'])
    # sensitivity_df['SMI_give_%s' %k] = pd.Series(modelso.semitropic.annual_supplies['leiu_delivered'])
    # sensitivity_df['WON_land_%s' %k] = pd.Series(modelso.wonderful.annual_supplies['acreage'])

    #try:
    if (save_full):
      pd.to_pickle(modelno, results_folder + '/modelno' + str(k) + '.pkl')
      pd.to_pickle(modelso, results_folder + '/modelso' + str(k) + '.pkl')

    data_output(output_list, results_folder, clean_output, rank, k, new_inputs.sensitivity_factors, modelno, modelso)
    #except Exception as e: print(e)

    del modelno
    del modelso
    print('Sample ' + str(k) + ' completed in ', datetime.now() - startTime)

    sys.stdout.flush()
  # param_df.to_csv(results_folder + '/sens_out/sens_param_scr_' + str(k) + '.csv') #keyvan
  # sensitivity_df.to_csv(results_folder + '/sens_out/sens_results_scr_'+ str(k) + '.csv') #keyvan
  
  
  
  ######################################################################################
  ### climate ensemble mode ############################################################
  ######################################################################################
  elif (model_mode == 'climate_ensemble'):
    file_folder = 'cord/data/CA_FNF_climate_change/'
    model_name_list = ['gfdl-esm2m', 'canesm2', 'ccsm4', 'cnrm-cm5', 'csiro-mk3-6-0', 'gfdl-cm3', 'hadgem2-cc', 'hadgem2-es', 'inmcm4', 'ipsl-cm5a-mr', 'miroc5']
    proj_list = ['rcp45', 'rcp85']
    total_model_proj = len(model_name_list) * len(proj_list)


    # Use the processor rank to determine the chunk of work each processor will do
    if parallel_mode==True:
      # Determine the chunk which each processor will neeed to do
      count = int(math.floor(total_model_proj / nprocs))
      remainder = total_model_proj % nprocs
      if rank < remainder:
        start = rank * (count + 1)
        stop = start + count + 1
      else:
        start = remainder * (count + 1) + (rank - remainder) * count
        stop = start + count
    else:
      start = 0
      stop = total_model_proj

    #####FLOW GENERATOR#####
    new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode, results_folder)

    # new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode)
    new_inputs.run_initialization('XXX')

    model_proj_count = 0
    for model_name in model_name_list:
      for projection in proj_list:
        # put everything in "try", so error on one sample run won't crash whole job. But this makes it hard to debug, so may want to comment this out when debugging.
        try:
          flow_input_source = model_name + '_' + projection
          if ((model_proj_count >= start) & (model_proj_count < stop)):
            print('Starting ' + flow_input_source)
            new_inputs.run_routine(flow_input_type, flow_input_source)

            input_data_file = results_folder + '/' + new_inputs.export_series[flow_input_type][flow_input_source] + "_0" + ".csv"

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
                print('Year ', (t + 1) / 365, ', ', datetime.now() - startTime)
                sys.stdout.flush()

              # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
              swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

              swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t,swp_pumping,cvp_pumping,swp_alloc,cvp_alloc,proj_surplus,max_pumping,swp_forgo,cvp_forgo,swp_AF,cvp_AF,swp_AS,cvp_AS,modelno.delta.forecastSJWYT, modelno.delta.max_tax_free,flood_release,flood_volume)

            # try:
            data_output_climate_ensemble(output_list, results_folder, clean_output, rank, flow_input_source, modelno, modelso)
            # except Exception as e: print(e)

            # save full model objects for single sensitivity run, useful to know object structure in postprocessing
            if (model_proj_count == 0):
              pd.to_pickle(modelno, results_folder + '/modelno' + str(model_proj_count) + '.pkl')
              pd.to_pickle(modelso, results_folder + '/modelso' + str(model_proj_count) + '.pkl')

            del modelno
            del modelso
            print('rank ' + str(rank) + ', ' + flow_input_source + ' completed in ', datetime.now() - startTime)

        except Exception as e: print(e)
        model_proj_count += 1
        sys.stdout.flush()


  
  
  
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

      swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.forecastSCWYT, modelno.delta.max_tax_free, flood_release, flood_volume)

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
    private_results = modelso.results_as_df_full('daily', modelso.private_list)
    private_results.to_csv(results_folder + '/private_results_' + model_mode + '.csv')
    del private_results,private_results_annual

    city_results_annual = modelso.results_as_df('annual', modelso.city_list)
    city_results_annual.to_csv(results_folder + '/annual_city_results_' + model_mode + '.csv')
    city_results = modelso.results_as_df_full('daily', modelso.city_list)
    city_results.to_csv(results_folder + '/city_results_' + model_mode + '.csv')
    del city_results,city_results_annual


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
  # except:
  #   print('ERROR: SAMPLE ' + str(k) + ' FAILED')


print ('Total run completed in ', datetime.now() - startTime)
if print_log:
  sys.stdout = sys.__stdout__



