# cython: profile=True

##################################################################################
#
# Combined Tulare Basin / SF Delta Model
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
import os
import shutil
import sys
import gc
from time import sleep
from configobj import ConfigObj
import json
from distutils.util import strtobool
from calfews_src.model_cy cimport Model
from calfews_src.inputter_cy import Inputter
from calfews_src.scenario import Scenario
from calfews_src.util import *
from calfews_src.plotter import *
from datetime import datetime

cdef class main_cy():

  cdef:
    public Model modelno, modelso
    # public Inputter new_inputs

  def __init__(self):

    #path_model = './'
    #path_model = sys.argv[1]
    #print (sys.argv)
    #os.chdir(path_model)

    startTime = datetime.now()

    # get runtime params from config file
    config = ConfigObj('runtime_params.ini')
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
    with open('calfews_src/scenarios/scenarios_main.json') as f:
      scenarios = json.load(f)
    scenario = scenarios[scenario_name]
    results_folder = output_directory + '/' + scenario_name + '/' + model_mode + '/'
    os.makedirs(results_folder, exist_ok=True)

    # make separate output folder for each processor
    if rank > 0:
      results_folder = results_folder + '/' + flow_input_source + '_' + str(rank)
    elif model_mode == 'validation':
      flow_input_source = 'CDEC'
      results_folder = results_folder + '/' + flow_input_source
    else:
      results_folder = results_folder + '/' + flow_input_source

    os.makedirs(results_folder, exist_ok=False)
    shutil.copy('runtime_params.ini', results_folder + '/runtime_params.ini')

    # set random seed
    if (seed > 0):
      np.random.seed(seed)

    # always use shorter historical dataframe for expected delta releases
    expected_release_datafile = 'calfews_src/data/input/calfews_src-data.csv'
    # data for actual simulation
    if model_mode == 'simulation':
      demand_type = 'baseline'
      #demand_type = 'pmp'
      base_data_file = 'calfews_src/data/input/calfews_src-data.csv'
      new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode, results_folder)
      if new_inputs.has_full_inputs[flow_input_type][flow_input_source]:
        input_data_file = new_inputs.flow_input_source[flow_input_type][flow_input_source]
      else:
        new_inputs.run_initialization('XXX')
        new_inputs.run_routine(flow_input_type, flow_input_source)
        input_data_file = results_folder + '/' + new_inputs.export_series[flow_input_type][flow_input_source]  + "_0.csv"

    elif model_mode == 'validation':
      demand_type = 'pesticide'
      input_data_file = 'calfews_src/data/input/calfews_src-data.csv'
    elif model_mode == 'sensitivity':
      demand_type = 'baseline'
      base_data_file = 'calfews_src/data/input/calfews_src-data.csv'
    elif model_mode == 'climate_ensemble':
      demand_type = 'baseline'
      base_data_file = 'calfews_src/data/input/calfews_src-data.csv'

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
    print(model_mode)
    for k in range(start, stop):

      print('#######################################################')
      print('Sample ' + str(k) + ' start')
      sys.stdout.flush()

      # reset seed the same each sample k
      if (seed > 0):
        np.random.seed(seed)

      # put everything in "try", so error on one sample run won't crash whole job. But this makes it hard to debug, so may want to comment this out when debugging.
      # try:
        ######################################################################################
      if model_mode == 'sensitivity':
        #####FLOW GENERATOR#####

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
        print('Initialization complete, ', datetime.now() - startTime)
        for t in range(0, timeseries_length):
          if (t % 365 == 364):
            print('Year ', (t+1)/365, ', ', datetime.now() - startTime)
            sys.stdout.flush()
          # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
          swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

          swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.forecastSCWYT, modelno.delta.max_tax_free, flood_release, flood_volume)

        if (save_full):
          pd.to_pickle(modelno, results_folder + '/modelno' + str(k) + '.pkl')
          pd.to_pickle(modelso, results_folder + '/modelso' + str(k) + '.pkl')

        data_output(output_list, results_folder, flow_input_source, k, new_inputs.sensitivity_factors, modelno, modelso)

        del modelno
        del modelso
        print('Sample ' + str(k) + ' completed in ', datetime.now() - startTime)

        sys.stdout.flush()
      
      
      
      ######################################################################################
      ### climate ensemble mode ############################################################
      ######################################################################################
      elif (model_mode == 'climate_ensemble'):
        file_folder = 'calfews_src/data/CA_FNF_climate_change/'
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
                print('Initialization complete, ', datetime.now() - startTime)
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

        # new_inputs = Inputter(base_data_file, expected_release_datafile, model_mode)
        modelno = Model(input_data_file, expected_release_datafile, model_mode, demand_type)
        modelso = Model(input_data_file, expected_release_datafile, model_mode, demand_type)
        modelso.max_tax_free = {}
        modelso.omr_rule_start, modelso.max_tax_free = modelno.northern_initialization_routine(startTime)
        modelso.forecastSRI = modelno.delta.forecastSRI
        gc.collect()
        modelso.southern_initialization_routine(startTime)
        gc.collect()
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
        print('Initialization complete, ', datetime.now() - startTime)
        ############################################
        for t in range(0, timeseries_length):
          if (t % 365 == 364):
            print('Year ', (t+1)/365, ', ', datetime.now() - startTime)

          # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
          swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)
          
          swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.forecastSCWYT, modelno.delta.max_tax_free, flood_release, flood_volume)

        print('end simulation, starting data output')
        sys.stdout.flush()
        sensitivity_factors = {}
        gc.collect()
        data_output(output_list, results_folder, clean_output, flow_input_source, sensitivity_factors, modelno, modelso)
            
            
        if (save_full):
          try:
            gc.collect()
            pd.to_pickle(modelno, results_folder + '/modelno' + str(k) + '.pkl')
            del modelno
            gc.collect()
            pd.to_pickle(modelso, results_folder + '/modelso' + str(k) + '.pkl')
            del modelso
            gc.collect()
          except Exception as e:
            print(e)


        print('Sample ' + str(k) + ' completed in ', datetime.now() - startTime)

        sys.stdout.flush()


    print ('Total run completed in ', datetime.now() - startTime)
    if print_log:
      sys.stdout = sys.__stdout__



