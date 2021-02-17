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

################################################################################################################################
### Initial model setup
################################################################################################################################
  def __init__(self, str results_folder, str model_mode='', str flow_input_type='', str flow_input_source=''):
    self.progress = 0.0
    self.running_sim = 1

    # get runtime params from config file
    config = ConfigObj('runtime_params.ini')
    # self.parallel_mode = bool(strtobool(config['parallel_mode']))
    self.short_test = int(config['short_test'])
    self.print_log = bool(strtobool(config['print_log']))
    self.seed = int(config['seed'])
    self.scenario_name = config['scenario_name'] #scenarios provide information on infrastructural plans
    # self.total_sensitivity_factors = int(config['total_sensitivity_factors'])
    # self.sensitivity_sample_file = config['sensitivity_sample_file']
    self.output_list = config['output_list']
    self.clean_output = bool(strtobool(config['clean_output']))
    self.save_full = bool(strtobool(config['save_full']))
    if model_mode == '':
      self.model_mode = config['model_mode']
      self.flow_input_type = config['flow_input_type']
      self.flow_input_source = config['flow_input_source']
    else:
      self.model_mode = model_mode
      self.flow_input_type = flow_input_type
      self.flow_input_source = flow_input_source
    self.results_folder = results_folder

    ### Initialize northern & southern models
    self.initialize()

    


################################################################################################################################
### Northern/southern model initialization
################################################################################################################################
  cdef void initialize(self):  
    cdef:
      str expected_release_datafile, demand_type, base_data_file, input_data_file
    
    # infrastructure scenario file, to be used for all sensitivity samples
    with open('calfews_src/scenarios/scenarios_main.json') as f:
      scenarios = json.load(f)
    scenario = scenarios[self.scenario_name]

    if self.model_mode == 'validation':
      self.flow_input_source = 'CDEC'

    ### copy runtime file for future use
    shutil.copy('runtime_params.ini', self.results_folder + '/runtime_params.ini')

    # set random seed
    if (self.seed > 0):
      np.random.seed(self.seed)

    # always use shorter historical dataframe for expected delta releases
    expected_release_datafile = 'calfews_src/data/input/calfews_src-data.csv'
    # data for actual simulation
    if self.model_mode == 'simulation':
      demand_type = 'baseline'
      #demand_type = 'pmp'
      base_data_file = 'calfews_src/data/input/calfews_src-data.csv'
      new_inputs = Inputter(base_data_file, expected_release_datafile, self.model_mode, self.results_folder)
      if new_inputs.has_full_inputs[self.flow_input_type][self.flow_input_source]:
        input_data_file = new_inputs.flow_input_source[self.flow_input_type][self.flow_input_source]
      else:
        new_inputs.run_initialization('XXX')
        new_inputs.run_routine(self.flow_input_type, self.flow_input_source)
        input_data_file = self.results_folder + '/' + new_inputs.export_series[self.flow_input_type][self.flow_input_source]  + "_0.csv"

    elif self.model_mode == 'validation':
      demand_type = 'pesticide'
      input_data_file = 'calfews_src/data/input/calfews_src-data.csv'

    ### setup northern & southern models & run initialization
    self.modelno = Model(input_data_file, expected_release_datafile, self.model_mode, demand_type)
    self.modelso = Model(input_data_file, expected_release_datafile, self.model_mode, demand_type)
    self.modelso.max_tax_free = {}
    self.modelso.omr_rule_start, self.modelso.max_tax_free = self.modelno.northern_initialization_routine()
    self.modelso.forecastSRI = self.modelno.delta.forecastSRI
    self.modelso.southern_initialization_routine()
    gc.collect()    



# ################################################################################################################################
# ### Main simulation
# ################################################################################################################################

  def run_sim_py(self, start_time):
    self.run_sim(start_time)
    
  cdef void run_sim(self, start_time):  
    cdef:
      int timeseries_length, swp_release, cvp_release, swp_release2, cvp_release2, t
      # double swp_pump, cvp_pump, proj_surplus, swp_available, cvp_available


    # # reset seed the same each sample k
    # if (self.seed > 0):
    #   np.random.seed(self.seed)

    ### simulation length (days)
    if (self.short_test < 0):
      timeseries_length = min(self.modelno.T, self.modelso.T)
    else:
      timeseries_length = self.short_test

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
    print('Begin simulation, ', datetime.now() - start_time)
    print(self.results_folder)
    
    ############################################
    for t in range(0, timeseries_length):
      self.progress = (t + 1) / timeseries_length
      if (t % 365 == 364):
        print('Year ', (t+1)/365, ', ', datetime.now() - start_time)

      # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
      swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = self.modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

      swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = self.modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, self.modelno.delta.forecastSJWYT, self.modelno.delta.forecastSCWYT, self.modelno.delta.max_tax_free, flood_release, flood_volume)
        
    gc.collect()



# ################################################################################################################################
# ### Data output
# ################################################################################################################################

  def output_results(self):
    ### data output function from calfews_src/util.py
    data_output(self.output_list, self.results_folder, self.clean_output, {}, self.modelno, self.modelso) 
        
    if (self.save_full):
      try:
        gc.collect()
        pd.to_pickle(self.modelno, self.results_folder + '/modelno' + str(k) + '.pkl')
        del self.modelno
        gc.collect()
        pd.to_pickle(self.modelso, self.results_folder + '/modelso' + str(k) + '.pkl')
        del self.modelso
        gc.collect()
      except Exception as e:
        print(e)
    
    self.running_sim = False

    if self.print_log:
      sys.stdout = sys.__stdout__



