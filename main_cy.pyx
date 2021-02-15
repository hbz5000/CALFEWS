# cython: profile=True

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
import gc
import shutil
import sys
from configobj import ConfigObj
import json
from distutils.util import strtobool
from calfews_src.model_cy cimport Model
from calfews_src.inputter_cy import Inputter
from calfews_src.scenario import Scenario
from calfews_src.util import *
from datetime import datetime

cdef class main_cy():

  def __init__(self):
    self.progress = 0.0
    self.running_sim = 1
    
    print('#######################################################')
    print('Begin initialization...')
    sys.stdout.flush()

  def run_py(self, str results_folder, str model_mode='', str flow_input_type='', str flow_input_source=''):
    self.run(results_folder, model_mode, flow_input_type, flow_input_source)
    
  cdef void run(self, str results_folder, str model_mode, str flow_input_type, str flow_input_source):  

    startTime = datetime.now()

    # get runtime params from config file
    config = ConfigObj('runtime_params.ini')
    parallel_mode = bool(strtobool(config['parallel_mode']))
    short_test = int(config['short_test'])
    print_log = bool(strtobool(config['print_log']))
    seed = int(config['seed'])
    scenario_name = config['scenario_name'] #scenarios provide information on infrastructural plans
    total_sensitivity_factors = int(config['total_sensitivity_factors'])
    sensitivity_sample_file = config['sensitivity_sample_file']
    output_list = config['output_list']
    clean_output = bool(strtobool(config['clean_output']))
    save_full = bool(strtobool(config['save_full']))
    if model_mode == '':
      model_mode = config['model_mode']
      flow_input_type = config['flow_input_type']
      flow_input_source = config['flow_input_source']

    start = 0
    stop = total_sensitivity_factors
    rank = 0

    # infrastructure scenario file, to be used for all sensitivity samples
    with open('calfews_src/scenarios/scenarios_main.json') as f:
      scenarios = json.load(f)
    scenario = scenarios[scenario_name]

    if model_mode == 'validation':
      flow_input_source = 'CDEC'

    ### copy runtime file for future use
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


    stop = 1    
     
    for k in range(start, stop):

      # reset seed the same each sample k
      if (seed > 0):
        np.random.seed(seed)


      ######################################################################################
      if model_mode == 'simulation' or model_mode == 'validation':

        ######################################################################################
        #   # Model Class Initialization
        ## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
        ##

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
        print('Begin simulation, ', datetime.now() - startTime)
        print(results_folder)
        
        ############################################
        for t in range(0, timeseries_length):
          self.progress = (t + 1) / timeseries_length
          if (t % 365 == 364):
            print('Year ', (t+1)/365, ', ', datetime.now() - startTime)

          # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
          swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

          swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.forecastSCWYT, modelno.delta.max_tax_free, flood_release, flood_volume)
            
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
        
        self.running_sim = False


    print ('Simulation complete,', datetime.now() - startTime)
    if print_log:
      sys.stdout = sys.__stdout__



