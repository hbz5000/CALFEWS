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
from csv import writer
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
  def __init__(self, str results_folder, str runtime_file='', str model_mode='', str flow_input_type='', str flow_input_source='', str flow_input_addition=''):
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
    # extra string for adding to flow_input_source to get input file for similarly-named MC samples
    self.flow_input_addition = flow_input_addition


    


################################################################################################################################
### Northern/southern model initialization
################################################################################################################################
  def initialize_py(self, uncertainty_dict={}):
    return self.initialize(uncertainty_dict)

  cdef int initialize(self, dict uncertainty_dict) except -1:  
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
    #shutil.copy(self.runtime_file, self.results_folder + '/' + self.runtime_file)

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
        if 'generic' in self.flow_input_source.split('_'):
          input_data_file += self.flow_input_addition + '.csv'
        new_inputs_df = ''
      else:
        # run initialization routine
        new_inputs.run_initialization('XXX')
        # end simulation if error has been through within inner cython/c code (i.e. keyboard interrupt)
        PyErr_CheckSignals()
        if True:
          new_inputs_df = new_inputs.run_routine(self.flow_input_type, self.flow_input_source, self.flow_input_addition)
          input_data_file = ''
          # input_data_file = self.results_folder + '/' + new_inputs.export_series[self.flow_input_type][self.flow_input_source]  + "_0.csv"

    elif self.model_mode == 'validation':
      demand_type = 'pesticide'
      input_data_file = 'calfews_src/data/input/calfews_src-data.csv'
      new_inputs_df = ''

    ### reset seed again to match old code
    if (self.seed > 0):
      np.random.seed(self.seed)

    ### setup northern & southern models & run initialization
    PyErr_CheckSignals()
    if True:
      self.modelno = Model(input_data_file, expected_release_datafile, self.model_mode, demand_type, new_inputs_df)
    PyErr_CheckSignals()
    if True:
      self.modelso = Model(input_data_file, expected_release_datafile, self.model_mode, demand_type, new_inputs_df)
    del new_inputs_df
    PyErr_CheckSignals()
    if True:
      self.modelso.max_tax_free = {}
      self.modelso.omr_rule_start, self.modelso.max_tax_free = self.modelno.northern_initialization_routine(scenario, uncertainty_dict)
    PyErr_CheckSignals()
    if True:
      self.modelso.forecastSRI = self.modelno.delta.forecastSRI
      self.modelso.southern_initialization_routine(scenario, uncertainty_dict)
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

  def output_results(self):
    ### data output function from calfews_src/util.py
    data_output(self.output_list, self.results_folder, self.clean_output, {}, self.modelno, self.modelso, self.objs) 
        
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



# ################################################################################################################################
# ### MORDM-specific functions for infrastructure experiment
# ################################################################################################################################

  def get_district_results(self, results_folder, MC_label, shared_objs_array, MC_count, is_baseline):
    ## shared_objs_array is a multiprocessing Array that can be accessed/written to by all MC samples in concurrent processes. MC_count is the index of this sample.
    ### get district-level results 

    district_results = {}
    other_results = {}
    wy = np.array(self.modelso.water_year)
    ny = self.modelno.number_years
    
    for dobj in self.modelso.district_list:
      d = dobj.key
      df = pd.DataFrame(index=wy)
      ### get relevant data
      for k, timeseries in dobj.daily_supplies_full.items():
        if ('delivery' in k.split('_')) or ('flood' in k.split('_')) or ('recharged' in k.split('_')) or ('exchanged' in k.split('_')) \
              or ('inleiu' in k.split('_')) or ('leiupumping' in k.split('_')) or ('banked' in k.split('_')):
          df[k] = timeseries 

      ## undo summation over years
      for y in range(wy.min() + 1, wy.max() + 1):
        maxprevious = df.loc[wy < y, :].iloc[-1, :]
        df.loc[wy == y, :] += maxprevious
      df.iloc[1:, :] = df.diff().iloc[1:, :]

      ### also add data that doesnt sum over years (pumping)
      keys = ['pumping']
      for k in keys:
        try:
          df[k] = dobj.daily_supplies_full[k]
        except:
          df[k] = np.zeros(len(wy))

      ## get total captured water = *district*_*contract*_delivery + *district*_*contract*_flood + *district*_*contract*_flood_irrigation - *district*_exchanged_GW + *district*_exchanged_SW
      df['captured_water'] = 0.0
      for (wtype, position) in [('delivery', 1), ('flood', 1), ('SW', 1)]:
        for c in df.columns:
          try:
            if c.split('_')[position] == wtype:
              df['captured_water'] += df[c]
          except:
            pass    
      for (wtype, position) in [('GW', 1)]:
        for c in df.columns:
          try:
            if c.split('_')[position] == wtype:
              df['captured_water'] -= df[c]
          except:
            pass

      results_dict = {'avg_captured_water': df['captured_water'].groupby(wy).sum().mean(), 'min_captured_water': df['captured_water'].groupby(wy).sum().min(),
                                'std_captured_water': df['captured_water'].groupby(wy).sum().std(),
                              'avg_pumping': df['pumping'].groupby(wy).sum().mean(), 'max_pumping': df['pumping'].groupby(wy).sum().max(),
                              'std_pumping': df['pumping'].groupby(wy).sum().std()}
      if is_baseline or \
            ((type(self.modelso.fkc.ownership_shares) is dict) and (d in self.modelso.fkc.ownership_shares) and (self.modelso.fkc.ownership_shares[d] > 0)) or \
            ((type(self.modelso.centralfriantwb.ownership) is dict) and (d in self.modelso.centralfriantwb.ownership) and (self.modelso.centralfriantwb.ownership[d] > 0)):
        district_results[d] = results_dict
      else:
        other_results[d] = results_dict
  
    ### for baseline, write results as json
    if is_baseline:
      with open(results_folder + '/../' + MC_label + '_baseline.json', 'w') as o:
        json.dump(district_results, o)
      return []
    ### for infra scenario, compare results to baseline
    else:
      # ### first write infra results as themselves
      # with open(results_folder + '/' + MC_label + '_infra_partners.json', 'w') as o:
      #   json.dump(district_results, o)
      ### read baseline results for same MC sample w/ no infra
      baseline_results = json.load(open(results_folder + '/../' + MC_label + '_baseline.json'))

      ### get gains for each district
      district_gains = {}
      for d in district_results.keys():
        district_gains[d] = {}
        for k,v in district_results[d].items():
          district_gains[d][k] = v - baseline_results[d][k]
      # ### write gains to json
      # with open(results_folder + '/' + MC_label + '_infra_gains.json', 'w') as o:
      #   json.dump(district_gains, o)
      ### get gains for each non-partner
      other_gains = {}
      for d in other_results.keys():
        other_gains[d] = {}
        for k,v in other_results[d].items():
          other_gains[d][k] = v - baseline_results[d][k]

      #### get annual paymetns for infrastructure
      FKC_participant_payment = 50e6
      CFWB_cost = 50e6
      interest_annual = 0.03
      time_horizon = 30
      cap = 1000
      principle = {'FKC': FKC_participant_payment, 'CFWB': CFWB_cost, 'FKC_CFWB': FKC_participant_payment + CFWB_cost}
      payments_per_yr = 1
      interest_rt = interest_annual / payments_per_yr
      num_payments = time_horizon * payments_per_yr
      annual_debt_payment_dict = {k: principle[k] / (((1 + interest_rt) ** num_payments - 1) / (interest_rt * (1 + interest_rt) ** num_payments)) for k in principle}

      ### now aggregate objs over districts 
      # total captured water gains for partnership (kAF/year)
      total_captured_water_gain = sum([v['avg_captured_water'] for v in district_gains.values()])
      # total pumping reduction for partnership (kAF/year)
      total_pump_red = sum([-v['avg_pumping'] for v in district_gains.values()])
      # total captured water gains for non-partners (kAF/year)
      total_nonpartner_captured_water_gain = sum([v['avg_captured_water'] for v in other_gains.values()])

      print(district_gains)
      print(total_captured_water_gain, total_pump_red, total_nonpartner_captured_water_gain)

      annual_debt_payment = 0.
      try:
        if len(self.modelso.centralfriantwb.participant_list) > 0:
          annual_debt_payment += annual_debt_payment_dict['CFWB']
      except:
        pass
      try:
        if sum(self.modelso.fkc.ownership_shares.values()) > 0:
          annual_debt_payment += annual_debt_payment_dict['FKC']
      except:
        pass
      print('payment: ', annual_debt_payment)
      ### cost of water gains for partnership ($/AF)
      #cost_water_gains_pship = (annual_debt_payment / total_captured_water_gain / 1000) if (total_captured_water_gain > 0) else 1e7
      
      ### worst-off partner costs
      cost_water_gains_worst = -1.
      for d,v in district_gains.items():
        try:
          partner_debt_payment = annual_debt_payment * self.modelso.centralfriantwb.ownership[d]
        except:
          partner_debt_payment = annual_debt_payment * self.modelso.fkc.ownership_shares[d]
        cost_water_gains_partner = (partner_debt_payment / v['avg_captured_water'] / 1000) if (v['avg_captured_water'] > 0) else 1e7
        if cost_water_gains_partner > cost_water_gains_worst:
          cost_water_gains_worst = cost_water_gains_partner
      
      ###& store in shared memory array
      objs_MC = [total_captured_water_gain,
                  total_pump_red,
                  total_nonpartner_captured_water_gain,
                  min(cost_water_gains_worst,1e7),
                  len(district_gains)]
      print(MC_label, objs_MC)
      shared_objs_array[MC_count*len(objs_MC):(MC_count+1)*len(objs_MC)] = objs_MC

      ### objs: max(0) CWG - mean over years - sum over partners - mean over MC
      ###       max(1) pumping reduction - mean over years - sum over partners - mean over MC
      ###       max(2) CWG - mean over years - sum over non-partners - mean over MC
      ###       min(3) cost CWG - mean over years - max over partners - max over MC
      ###       max(4) number partners - no agg needed
      ### cons: (1) obj 3 < 2000
      ###       (2) obj 4 > 0
      print('end district results', results_folder, [MC_label] + objs_MC)      
      with open(results_folder + '/objs.csv', 'a') as f:
        w = writer(f)
        w.writerow([MC_label] + objs_MC)
        

  
  
  def calc_objectives(self):
    ### "starter" objectives: (1) avg water deliveries for friant contracts; (2) min annual water deliveries for friant contracts
    nt = len(self.modelno.shasta.baseline_inf)
    with open(self.output_list, 'r') as f:
      output_list = json.load(f)

    objs = {}
    total_delivery = np.zeros(self.modelno.T)
    for c in ['friant1', 'friant2']:#, 'cvpdelta', 'swpdelta', 'cvpexchange']:
      for cc in ['contract', 'flood']:
        # try:
        print(c,cc)
        total_delivery += self.modelso.__getattribute__(c).daily_supplies[cc]                  
        # except:
          # pass    

    total_delivery = pd.DataFrame({'ts': total_delivery, 'wy': self.modelno.water_year})
    total_wy_delivery = total_delivery.groupby('wy').max()['ts'].values
    objs['avg_friant_delivery'] = np.mean(total_wy_delivery)
    objs['min_friant_delivery'] = np.min(total_wy_delivery)
    objs['timeseries_wys'] = len(total_wy_delivery)
    print(objs)

    return objs

