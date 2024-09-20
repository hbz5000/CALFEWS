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
import os
from configobj import ConfigObj
import json
from distutils.util import strtobool
from cpython.exc cimport PyErr_CheckSignals
from calfews_src.model_cy cimport Model
from calfews_src.inputter_cy cimport Inputter
from calfews_src.scenario import Scenario
from calfews_src.util import *
from datetime import datetime

cdef class main_cy():

################################################################################################################################
### Initial model setup
################################################################################################################################
  def __init__(self, str results_folder, str runtime_file='', str model_mode='', str flow_input_type='', str flow_input_source=''):
    self.progress = 0.0
    self.running_sim = 1

    # get runtime params from config file
    if runtime_file == '':
      self.runtime_file = 'runtime_params.ini'
    else:
      self.runtime_file = runtime_file
    config = ConfigObj(self.runtime_file)
    self.parallel_mode = bool(strtobool(config['parallel_mode']))
    self.short_test = int(config['short_test'])
    self.print_log = bool(strtobool(config['print_log']))
    self.seed = int(config['seed'])
    self.scenario_name = config['scenario_name'] #scenarios provide information on infrastructural plans
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


    


################################################################################################################################
### Northern/southern model initialization
################################################################################################################################
  def initialize_py(self):
    return self.initialize()

  cdef int initialize(self) except -1:  
    cdef:
      str expected_release_datafile, demand_type, base_data_file, input_data_file
    
    # infrastructure scenario file, to be used for all sensitivity samples
    with open('calfews_src/scenarios/scenarios_main.json') as f:
      scenarios = json.load(f)
    scenario = scenarios[self.scenario_name]

    # new scenario file is created and saved to results folder for each experiment (FKC experiment)
    for k, v in scenario.items():
      if v == 'localfile':
        scenario[k] = self.results_folder + '/' + k + '_scenario.json'

    if self.model_mode == 'validation':
      self.flow_input_source = 'CDEC'

    ### copy runtime file for future use
    shutil.copy(self.runtime_file, self.results_folder + '/' + self.runtime_file)

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
        # run initialization routine
        new_inputs.run_initialization('XXX')
        # end simulation if error has been through within inner cython/c code (i.e. keyboard interrupt)
        PyErr_CheckSignals()
        if True:
          new_inputs.run_routine(self.flow_input_type, self.flow_input_source)
          input_data_file = self.results_folder + '/' + new_inputs.export_series[self.flow_input_type][self.flow_input_source]  + "_0.csv"

    elif self.model_mode == 'validation':
      demand_type = 'pesticide'
      #demand_type = 'landiq'
      input_data_file = 'calfews_src/data/input/calfews_src-data.csv'

    elif self.model_mode == 'climate_ensemble':
      demand_type = 'pesticide'
      #demand_type = 'landiq'
      base_data_file = 'calfews_src/data/input/calfews_src-data.csv'
      new_inputs = Inputter(base_data_file, expected_release_datafile, self.model_mode, self.results_folder)
      if new_inputs.has_full_inputs[self.flow_input_type][self.flow_input_source]:
        input_data_file = new_inputs.flow_input_source[self.flow_input_type][self.flow_input_source]
      else:
        # run initialization routine
        new_inputs.run_initialization('XXX')
        # end simulation if error has been through within inner cython/c code (i.e. keyboard interrupt)
        PyErr_CheckSignals()
        if True:
          new_inputs.run_routine(self.flow_input_type, self.flow_input_source)
          input_data_file = self.results_folder + '/' + new_inputs.export_series[self.flow_input_type][self.flow_input_source]  + "_0.csv"

    ### reset seed again to match old code
    if (self.seed > 0):
      np.random.seed(self.seed)
    ### setup northern & southern models & run initialization
    PyErr_CheckSignals()
    if True:
      self.modelno = Model(input_data_file, expected_release_datafile, self.model_mode, demand_type)
    PyErr_CheckSignals()
    if True:
      self.modelso = Model(input_data_file, expected_release_datafile, self.model_mode, demand_type)
    PyErr_CheckSignals()
    if True:
      self.modelso.max_tax_free = {}
      self.modelso.omr_rule_start, self.modelso.max_tax_free = self.modelno.northern_initialization_routine(scenario)
    PyErr_CheckSignals()
    if True:
      self.modelso.forecastSRI = self.modelno.delta.forecastSRI
      self.modelso.southern_initialization_routine(scenario)
      try:
        #remove input data file (only if created for simulation), since data will be stored more efficiently in hdf5
        os.remove(self.results_folder + '/' + new_inputs.export_series[self.flow_input_type][self.flow_input_source]  + "_0.csv")
      except:
        pass
    gc.collect()    

    return 0



# ################################################################################################################################
# ### Main simulation
# ################################################################################################################################

  def run_sim_py(self, start_time):
    return self.run_sim(start_time)
    
  cdef int run_sim(self, start_time) except -1:  
    cdef:
      int timeseries_length, t, swp_release, cvp_release, swp_release2, cvp_release2
      double swp_pump, cvp_pump, swp_forgone, cvp_forgone, swp_AF, cvp_AF, swp_AS, cvp_AS, 
      dict proj_surplus, max_pumping, max_tax_free, flood_release, flood_volume
      str wyt, wytSC


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
    print('Begin simulation, ', datetime.now() - start_time)
    print(self.results_folder)
    sys.stdout.flush()

    
    ############################################
    # while True:
    for t in range(0, timeseries_length):
      self.progress = (t + 1) / timeseries_length
      if (t % 365 == 364):
        print('Year ', (t+1)/365, ', ', datetime.now() - start_time)
        sys.stdout.flush()

      # the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
      swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, flood_release, flood_volume = self.modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump)

      swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = self.modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, self.modelno.delta.forecastSJWYT, self.modelno.delta.forecastSCWYT, self.modelno.delta.max_tax_free, flood_release, flood_volume)

      # end simulation if error has been through within inner cython/c code (i.e. keyboard interrupt)
      PyErr_CheckSignals()

    gc.collect()

    return 0



# ################################################################################################################################
# ### Data output
# ################################################################################################################################
  def calc_objectives(self):
    ### "starter" objectives: (1) avg water deliveries for friant contracts; (2) min annual water deliveries for friant contracts
    nt = len(self.modelno.shasta.baseline_inf)

    self.objs = {}
    total_delivery = np.zeros(self.modelno.T)
    for c in ['friant1', 'friant2']:
      for cc in ['contract', 'flood']:
        try:
          total_delivery += self.modelso.__getattribute__(c).daily_supplies[cc]                  
        except:
          pass    

    total_delivery = pd.DataFrame({'ts': total_delivery, 'wy': self.modelno.water_year})
    total_wy_delivery = total_delivery.groupby('wy').max()['ts'].values
    self.objs['avg_friant_delivery'] = np.mean(total_wy_delivery)
    self.objs['min_friant_delivery'] = np.min(total_wy_delivery)




# ################################################################################################################################
# ### Data output
# ################################################################################################################################

  def output_results(self):
    ### data output function from calfews_src/util.py
    data_output(self.results_folder, self.clean_output, self.modelno, self.modelso, self.objs)
        
    if (self.save_full):
      try:
        gc.collect()
        pd.to_pickle(self.modelno, self.results_folder + '/modelno.pkl')
        del self.modelno
        gc.collect()
        pd.to_pickle(self.modelso, self.results_folder + '/modelso.pkl')
        del self.modelso
        gc.collect()
      except Exception as e:
        print(e)
    
    self.running_sim = False



