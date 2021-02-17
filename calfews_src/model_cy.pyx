# cython: profile=True
import numpy as np
import pandas as pd
import collections as cl
import sys
import calendar
import json
import matplotlib.pyplot as plt
from .util import *

cdef class Model():
 
  def __init__(self, input_data_file, expected_release_datafile, model_mode, demand_type, sensitivity_sample_number=-1, sensitivity_sample_names=[], sensitivity_sample=[], sensitivity_factors = None):
    ##Set model dataset & index length
    self.df = []
    self.df.append(pd.read_csv(input_data_file, index_col=0, parse_dates=True))
    self.model_mode = model_mode
    self.demand_type = demand_type
    self.T = len(self.df[0])
    self.day_year = [int(_) for _ in self.df[0].index.dayofyear]
    self.day_month = [int(_) for _ in self.df[0].index.day]
    self.month = [int(_) for _ in self.df[0].index.month]
    self.year = [int(_) for _ in self.df[0].index.year]
    self.starting_year = self.year[0]
    self.ending_year = self.year[-1]
    self.number_years = self.ending_year - self.starting_year
    self.dowy = water_day(self.day_year, self.year)
    self.water_year = water_year(self.month, self.year, self.starting_year)
    self.leap = leap(np.arange(min(self.year), max(self.year) + 2))
    year_list = np.arange(min(self.year), max(self.year) + 2)
    self.days_in_month = days_in_month(year_list, self.leap)
    self.dowy_eom = dowy_eom(year_list, self.leap)
    self.non_leap_year = first_non_leap_year(self.dowy_eom)
    self.first_d_of_month = first_d_of_month(self.dowy_eom, self.days_in_month)

    self.df_short = []
    self.df_short.append(pd.read_csv(expected_release_datafile, index_col=0, parse_dates=True))
    self.T_short = len(self.df_short[0])
    self.short_day_year = [int(_) for _ in self.df_short[0].index.dayofyear]
    self.short_day_month = [int(_) for _ in self.df_short[0].index.day]
    self.short_month = [int(_) for _ in self.df_short[0].index.month]
    self.short_year = [int(_) for _ in self.df_short[0].index.year]
    self.short_starting_year = self.short_year[0]
    self.short_ending_year = self.short_year[-1]
    self.short_number_years = self.short_ending_year - self.short_starting_year
    self.short_dowy = water_day(self.short_day_year, self.short_year)
    self.short_water_year = water_year(self.short_month, self.short_year, self.short_starting_year)
    short_year_list = np.arange(min(self.short_year), max(self.short_year)+2)
    short_leap = leap(short_year_list)
    self.short_days_in_month = days_in_month(short_year_list, short_leap)
    

    if sensitivity_sample_number == -1:
      self.use_sensitivity = False
    else:
      self.use_sensitivity = True
      self.sensitivity_sample_number = sensitivity_sample_number
      self.sensitivity_sample_names = sensitivity_sample_names
      self.sensitivity_sample = sensitivity_sample
      self.sensitivity_factors = sensitivity_factors
      self.set_sensitivity_factors()


  def object_equals(self, other, return_full=False):
    ##This function compares two instances of a model object, returns True if all attributes are identical.
    equality = {}
    if (self.__dict__.keys() != other.__dict__.keys()):
      return ('Different Attributes')
    else:
      differences = 0
      for i in self.__dict__.keys():
        if ((type(self.__getattribute__(i)) is Canal) | (type(self.__getattribute__(i)) is Contract) |
                (type(self.__getattribute__(i)) is District) | (type(self.__getattribute__(i)) is Private) |
                (type(self.__getattribute__(i)) is Reservoir) | (type(self.__getattribute__(i)) is Waterbank)):
          equality[i] = self.__getattribute__(i).object_equals(other.__getattribute__(i))
        elif type(self.__getattribute__(i)) is dict:
          equality[i] = True
          for j in self.__getattribute__(i).keys():
            if (type(self.__getattribute__(i)[j] == other.__getattribute__(i)[j]) is bool):
              if ((self.__getattribute__(i)[j] == other.__getattribute__(i)[j]) == False):
                equality[i] = False
            else:
              if ((self.__getattribute__(i)[j] == other.__getattribute__(i)[j]).all() == False):
                equality[i] = False
        else:
          if (type(self.__getattribute__(i) == other.__getattribute__(i)) is bool):
            equality[i] = (self.__getattribute__(i) == other.__getattribute__(i))
          else:
            equality[i] = np.array(self.__getattribute__(i) == other.__getattribute__(i)).all()
        if (equality[i] == False):
          differences += 1
    if return_full:
      return (equality)
    else:
      return (differences == 0)




  #####################################################################################################################
#############################     Object Creation     ###############################################################
#####################################################################################################################
  def northern_initialization_routine(self):
    ######################################################################################
    ######################################################################################
    # preprocessing for the northern system
    ######################################################################################
    # initialize reservoirs
    # generates - regression coefficients & standard deviations for flow predictions (fnf & inf)
    # (at each reservoir)
    # self.res.rainflood_fnf; self.res.snowflood_fnf
    # self.res.rainflood_inf; self.res.snowflood_inf; self.res.baseline_inf
    # self.res.rainfnf_stds; self.res.snowfnf_stds
    # self.res.raininf_stds; self.res.snowinf_stds; self.res.baseinf_stds
    # self.res.flow_shape - monthly fractions of total period flow
    self.initialize_northern_res()
    # initialize delta rules, calcluate expected environmental releases at each reservoir
    # generates - cumulative environmental/delta releases remaining (at each reservoir)
    # self.res.cum_min_release; self.res.aug_sept_min_release; self.res.oct_nov_min_release
    self.initialize_delta_ops()

    ######
    # calculate projection-based flow year indicies using flow & snow inputs
    ##note: these values are pre-processed, but represent no 'foresight' WYT & WYI index use
    # snow-based projections to forecast flow, calculate running WY index & WYT
    # generates:
    # self.delta.forecastSJI (self.T x 1) - forecasts for san joaquin river index
    # self.delta.forecastSRI (self.T x 1) - forecasts for sacramento river index
    self.find_running_WYI()

    ######
    # calculate expected 'unstored' pumping at the delta (for predictions into San Luis)
    # this generates:
    # self.delta_gains_regression (365x2) - linear coeffecicients for predicting total unstored pumping, oct-mar, based on ytd full natural flow
    # self.delta_gains_regression2 (365x2) - linear coeffecicients for predicting total unstored pumping, apr-jul, based on ytd full natural flow
    # self.month_averages (12x1) - expected fraction of unstored pumping to come in each month (fraction is for total period flow, so 0.25 in feb is 25% of total oct-mar unstored flow)
    self.predict_delta_gains()
    if self.model_mode == 'validation':
      self.set_regulations_historical_north()
    else:
      self.set_regulations_current_north()
	
    return self.delta.omr_rule_start, self.delta.max_tax_free
    ######################################################################################

  def southern_initialization_routine(self, scenario='baseline'):
    ######################################################################################
    # preprocessing for the southern system
    ######################################################################################
    # initialize the southern reservoirs -
    # generates - same values as initialize_northern_res(), but for southern reservoirs
    self.initialize_southern_res()
    # initialize water districts for southern model
    # generates - water district parameters (see calfews_src-combined/calfews_src/districts/readme.txt)
    # self.district_list - list of district objects
    # self.district_keys - dictionary pairing district keys w/district class objects
    self.initialize_water_districts(scenario)
    # initialize water contracts for southern model
    # generates - water contract parameters (see calfews_src-combined/calfews_src/contracts/readme.txt)
    # self.contract_list - list of contract objects
    # self.contract_keys - dictionary pairing contract keys w/contract class objects
    # self.res.contract_carryover_list - record of carryover space afforded to each contract (for all district)
    self.initialize_sw_contracts()
    # initialize water banks for southern model
    # generates - water bank parameters (see calfews_src-combined/calfews_src/banks/readme.txt)
    # self.waterbank_list - list of waterbank objects
    # self.leiu_list - list of district objects that also operate as 'in leiu' or 'direct recharge' waterbanks
    self.initialize_water_banks()
    # initialize canals/waterways for southern model
    # generates - canal parameters (see calfews_src-combined/calfews_src/canals/readme.txt)
    # self.canal_list - list of canal objects
    self.initialize_canals(scenario)
    if self.model_mode == 'validation':
      self.set_regulations_historical_south(scenario)
    else:
      self.set_regulations_current_south(scenario)
    # create dictionaries that structure the relationships between
    # reservoirs, canals, districts, waterbanks, and contracts
    # generates:
    # self.canal_district - dict keys are canals, object lists place reservoirs, waterbanks, districts & other canals in order on a given canal
    # self.canal_priority - dict keys are canals, object lists are the 'main' canals that have 'priority' on the other canals (through turnouts)
    # self.reservoir_contract - dict keys are reservoirs, object lists are contracts stored in that reservoir
    # self.contract_reservoir - dict keys are contracts, objects (single) are reservoirs where that contract is stored (inverse of reservoir_contract)
    # self.canal_contract - dict keys are canals, object lists are contracts that have priority on those canals (primarily for flood flows)
    # self.reservoir_canal - dict keys are reservoirs, object lists are canal(s) that connect to the reservoir (note - only millerton has more than one canal)
    # Also initializes some canal properties
    # self.canal.demand - dictionary for the different types of demand that can be created at each canal node (note - these values are updated within model steps)
    # self.canal.flow - vector recording flow to a node on a canal (note - these values are updated within model steps)
    # self.canal.turnout_use - vector recording diversions to a node on a canal (note - these values are updated within model steps)
    self.create_object_associations()	
    ###Applies initial carryover balances to districts
    ##based on initial reservoir storage conditions
    ##PLEASE NOTE CARRYOVER STORAGE IN SAN LUIS IS HARD-CODED
    self.find_initial_carryover()
    ##initial recovery capacities for districts, based on
    ##ownership stakes in waterbanks (direct + inleui)
    self.init_tot_recovery()
    ##initial recharge capacities (projected out 12 months) for districts,
    ##based on ownership stakes in waterbanks (direct + inleui + indistrict)
    urban_datafile = 'calfews_src/data/input/calfews_src-data-urban.csv'
    urban_datafile_cvp = 'calfews_src/data/input/pump-data-cvp.csv'
    project_pumping_datafile = 'calfews_src/data/input/reservoir_results_no_validation.csv'
    self.project_urban(urban_datafile, urban_datafile_cvp, project_pumping_datafile)
    # calculate how much recharge capacity is reachable from each reservoir
    # that is owned by surface water contracts held at that reservoir - used to determine
    # how much flood water can be released and 'taken' by a contractor
    self.find_all_triggers()



  def initialize_northern_res(self):

    #########################################################################################
	#reservoir initialization for the northern delta system
    #########################################################################################
    cdef Reservoir reservoir_obj

    #4 Sacramento River Reservoirs (CVP & SWP)
    self.shasta = Reservoir(self, 'shasta', 'SHA', self.model_mode)
    self.folsom = Reservoir(self, 'folsom', 'FOL', self.model_mode)
    self.oroville = Reservoir(self, 'oroville', 'ORO', self.model_mode)
    self.yuba = Reservoir(self, 'yuba', 'YRS', self.model_mode)

    #3 San Joaquin River Reservoirs (to meet Vernalis flow targets)
    self.newmelones = Reservoir(self, 'newmelones', 'NML', self.model_mode)
    self.donpedro = Reservoir(self, 'donpedro', 'DNP', self.model_mode)
    self.exchequer = Reservoir(self, 'exchequer', 'EXC', self.model_mode)

    self.reservoir_list = [self.shasta, self.oroville, self.yuba, self.folsom, self.newmelones, self.donpedro,
                           self.exchequer]

    #Millerton Reservoir (flows used to calculate San Joaquin River index, not in northern simulation)
    self.millerton = Reservoir(self, 'millerton', 'MIL', self.model_mode)
    reservoir_list = [self.shasta, self.oroville, self.folsom, self.yuba, self.newmelones, self.donpedro, self.exchequer, self.millerton]
    ##Regression flow & standard deviations read from file
    #### Find regression information for all 8 reservoirs

    if self.model_mode == 'climate_ensemble':
      ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      # df_res_process = pd.DataFrame()
      # df_res_annual = pd.DataFrame()
      for reservoir_obj in reservoir_list:
        reservoir_obj.find_release_func(self)
      ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
      ###that is expected to come, regressed against the total flow already observed in that period
      ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      for reservoir_obj in reservoir_list:
        reservoir_obj.create_flow_shapes(self)
    elif self.model_mode == 'validation':
	  ## 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      # df_res_process = pd.DataFrame()
      # df_res_annual = pd.DataFrame()
      for reservoir_obj in reservoir_list:
        reservoir_obj.find_release_func(self)
        # df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        # df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        # df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        # df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        # df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)
        #
        # df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        # df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        # df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        # df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        # df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
      # df_res_process.to_csv('calfews_src/data/input/temp_output/no_res_preprocess_daily.csv')
      # df_res_annual.to_csv('calfews_src/data/input/temp_output/no_res_preprocess_annual.csv')

      #flow_estimates = pd.read_csv('calfews_src/data/temp_output/input/no_res_preprocess_daily.csv', index_col=0, parse_dates=True)
      #std_estimates = pd.read_csv('calfews_src/data/temp_output/input/no_res_preprocess_annual.csv')
      #for x in reservoir_list:
        #x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]##FNF, OCT-MAR, LINEAR COEF
        #x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]##FNF, APR-JUL, LINEAR COEF
        #x.rainflood_inf = flow_estimates['%s_raininf' % x.key]##INF, OCT-MAR, LINEAR COEF
        #x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]##INF, APR-JUL, LINEAR COEF
        #x.baseline_inf = flow_estimates['%s_baseinf' % x.key]##INF, AUG-SEPT, LINEAR COEF
        #x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]##FNF, OCT-MAR, STD
        #x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]##FNF, APR-JUL, STD
        #x.raininf_stds = std_estimates['%s_raininfstd' % x.key]##INF, OCT-MAR, STD
        #x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]##INF, APR-JUL, STD
        #x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]##INF, AUG-SEPT, STD
      ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      #df_flow_shape_no = pd.DataFrame()
      for reservoir_obj in reservoir_list:
        reservoir_obj.create_flow_shapes(self)
    else:
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      # df_res_process = pd.DataFrame()
      # df_res_annual = pd.DataFrame()
      for reservoir_obj in reservoir_list:
        reservoir_obj.find_release_func(self)
        # df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        # df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        # df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        # df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        # df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)
        #
        # df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        # df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        # df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        # df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        # df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
      # df_res_process.to_csv('calfews_src/data/input/temp_output/no_res_preprocess_simulation_daily.csv')
      # df_res_annual.to_csv('calfews_src/data/input/temp_output/no_res_preprocess_simulation_annual.csv')

      #flow_estimates = pd.read_csv('calfews_src/data/input/temp_output/no_res_preprocess_simulation_daily.csv')
      #std_estimates = pd.read_csv('calfews_src/data/input/temp_output/no_res_preprocess_simulation_annual.csv')
      #for x in reservoir_list:
        #x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]##FNF, OCT-MAR, LINEAR COEF
        #x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]##FNF, APR-JUL, LINEAR COEF
        #x.rainflood_inf = flow_estimates['%s_raininf' % x.key]##INF, OCT-MAR, LINEAR COEF
        #x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]##INF, APR-JUL, LINEAR COEF
        #x.baseline_inf = flow_estimates['%s_baseinf' % x.key]##INF, AUG-SEPT, LINEAR COEF
        #x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]##FNF, OCT-MAR, STD
        #x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]##FNF, APR-JUL, STD
        #x.raininf_stds = std_estimates['%s_raininfstd' % x.key]##INF, OCT-MAR, STD
        #x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]##INF, APR-JUL, STD
        #x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]##INF, AUG-SEPT, STD
	  
	  ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      #df_flow_shape_no = pd.DataFrame()
      for reservoir_obj in reservoir_list:
        reservoir_obj.create_flow_shapes(self)
    #########################################################################################

  def initialize_delta_ops(self):
	#########################################################################################
    ##initialization of the delta rules
    #########################################################################################
    cdef Reservoir reservoir_obj

    self.delta = Delta(self, 'delta', 'DEL', self.model_mode)
    
    if self.use_sensitivity:
      self.delta.set_sensitivity_factors(self.sensitivity_factors['delta_outflow_multiplier']['realization'], self.sensitivity_factors['omr_flow']['realization'], self.sensitivity_factors['omr_probability']['realization'])

	###Find expected reservoir releases to meet delta requirements - used in flow forecasting
    ###these use the flow 'gains' on each tributary stretch to find the expected extra releases required to meet env & delta mins
    gains_sac_short = self.df_short[0].SAC_gains * cfs_tafd
    gains_sj_short = self.df_short[0].SJ_gains * cfs_tafd
    depletions_short = self.df_short[0].delta_depletions * cfs_tafd
    eastside_streams_short = self.df_short[0].EAST_gains * cfs_tafd
    inflow_list = [self.shasta, self.folsom, self.yuba, self.oroville, self.newmelones, self.donpedro, self.exchequer]

    for reservoir_obj in inflow_list:
      reservoir_obj.downstream_short = [_ * cfs_tafd for _ in self.df_short[0]['%s_gains'% reservoir_obj.key].values]
 
    ##in addition to output variables, this generates:
	#self.max_tax_free (5x2x365) - using delta outflow min, calculate how much pumping can occur without paying any additional I/E 'tax' (b/c some inflow is already used for delta outflow requirements)
    expected_outflow_req, expected_depletion = self.delta.calc_expected_delta_outflow(self,self.shasta.downstream_short,self.oroville.downstream_short,self.yuba.downstream_short,self.folsom.downstream_short, self.shasta.temp_releases, self.oroville.temp_releases, self.yuba.temp_releases, self.folsom.temp_releases, gains_sac_short, gains_sj_short, depletions_short, eastside_streams_short)
	#these requirements are then passed back to the reservoirs so that they know how much water to hold on to
    #Calculated the expected releases for environmental flows & delta outflow requirements
    #pre-processed to help with forecasts of available storage for export
    ##Yuba has an extra flow catagorization for environmental minimum flows,
    ## 'extra critical' - use critical year delta outflow requirements in that year type
    expected_outflow_req = self.delta.min_outflow
    expected_outflow_req['EC'] = expected_outflow_req['C']
    #generates:
    #x.cum_min_release (5 x 365) - daily values of remaining enviromental releases through the end of july, in each wyt
    #x.aug_sept_min_release (5 x 365) - daily values of remaining enviromental releases during the aug-sept period, in each wyt
    #x.oct_nov_min_release (5 x 365) - daily values of remaining enviromental releases during the oct-nov period, in each wyt
    for reservoir_obj in inflow_list:
      reservoir_obj.calc_expected_min_release(self, expected_outflow_req, expected_depletion, 0)
	  
    self.delta.create_flow_shapes_omr(self)

  def initialize_southern_res(self):
    ############################################################################
    ###Reservoir Initialization
	############################################################################
    cdef Reservoir reservoir_obj

    self.millerton = Reservoir(self, 'millerton', 'MIL', self.model_mode)
    self.pineflat = Reservoir(self, 'pineflat', 'PFT', self.model_mode)
    self.kaweah = Reservoir(self, 'kaweah', 'KWH', self.model_mode)
    self.success = Reservoir(self, 'success', 'SUC', self.model_mode)
    self.isabella = Reservoir(self, 'isabella', 'ISB', self.model_mode)
    ###San Luis is initialized as a Reservoir, but
    ###has none of the watershed data that goes along with the other reservoirs
    self.sanluis = Reservoir(self, 'sanluis', 'SNL', self.model_mode)
    self.sanluisstate = Reservoir(self, 'sanluisstate', 'SLS', self.model_mode)
    self.sanluisfederal = Reservoir(self, 'sanluisfederal', 'SLF', self.model_mode)
    self.reservoir_list = [self.sanluisstate, self.sanluisfederal, self.millerton, self.isabella, self.success, self.kaweah, self.pineflat]

    if self.model_mode == 'climate_ensemble':
      ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      for reservoir_obj in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
        reservoir_obj.find_release_func(self)
      for reservoir_obj in [self.pineflat, self.millerton, self.isabella, self.success, self.kaweah]:
        reservoir_obj.create_flow_shapes(self)
    elif self.model_mode == 'validation':	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      # df_res_process = pd.DataFrame()
      # df_res_annual = pd.DataFrame()
      for reservoir_obj in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
        reservoir_obj.find_release_func(self)
        # df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        # df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        # df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        # df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        # df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)
        #
        # df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        # df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        # df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        # df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        # df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
      # df_res_process.to_csv('calfews_src/data/input/temp_output/res_preprocess_daily.csv')
      # df_res_annual.to_csv('calfews_src/data/input/temp_output/res_presprocess_annual.csv')
	  
      ##Regression flow & standard deviations read from file (see end of function for code to generate files)	  
      #flow_estimates = pd.read_csv('calfews_src/data/input/temp_output/res_preprocess_daily.csv', index_col=0, parse_dates=True)
      #std_estimates = pd.read_csv('calfews_src/data/input/temp_output/res_presprocess_annual.csv')
	  #### Find regression information for all 8 reservoirs 
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      #for x in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
        #x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]#FNF, Oct-Mar, Linear coefficients
        #x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]#FNF, Apr-Jul, Linear coefficients
        #x.rainflood_inf = flow_estimates['%s_raininf' % x.key]#INF, Oct-Mar, Linear coefficients
        #x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]#INF, Apr-Jul, Linear coefficients
        #x.baseline_inf = flow_estimates['%s_baseinf' % x.key]#INF, Aug-Sept, Linear coefficients
        #x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]#FNF, Oct-Mar, STD
        #x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]#FNF, Apr-Jul, STD
        #x.raininf_stds = std_estimates['%s_raininfstd' % x.key]#INF, Oct-Mar, STD
        #x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]#INF, Apr-Jul, STD
        #x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]#INF, Aug-Sept, STD
		
      ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      for reservoir_obj in [self.pineflat, self.millerton, self.isabella, self.success, self.kaweah]:
        reservoir_obj.create_flow_shapes(self)
    else:
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      reservoir_list = [self.millerton, self.isabella, self.pineflat, self.kaweah, self.success]
      # df_res_process = pd.DataFrame()
      # df_res_annual = pd.DataFrame()
      for reservoir_obj in reservoir_list:
        reservoir_obj.find_release_func(self)
        # df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        # df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        # df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        # df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        # df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)
        #
        # df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        # df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        # df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        # df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        # df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
      # df_res_process.to_csv('calfews_src/data/input/temp_output/so_res_preprocess_simulation_daily.csv')
      # df_res_annual.to_csv('calfews_src/data/input/temp_output/so_res_preprocess_simulation_annual.csv')

      #flow_estimates = pd.read_csv('calfews_src/data/input/temp_output/so_res_preprocess_simulation_daily.csv')
      #std_estimates = pd.read_csv('calfews_src/data/input/temp_output/so_res_preprocess_simulation_annual.csv')
      #for x in reservoir_list:
        #x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]##FNF, OCT-MAR, LINEAR COEF
        #x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]##FNF, APR-JUL, LINEAR COEF
        #x.rainflood_inf = flow_estimates['%s_raininf' % x.key]##INF, OCT-MAR, LINEAR COEF
        #x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]##INF, APR-JUL, LINEAR COEF
        #x.baseline_inf = flow_estimates['%s_baseinf' % x.key]##INF, AUG-SEPT, LINEAR COEF
        #x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]##FNF, OCT-MAR, STD
        #x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]##FNF, APR-JUL, STD
        #x.raininf_stds = std_estimates['%s_raininfstd' % x.key]##INF, OCT-MAR, STD
        #x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]##INF, APR-JUL, STD
        #x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]##INF, AUG-SEPT, STD
	  
	  ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      for reservoir_obj in reservoir_list:
        reservoir_obj.create_flow_shapes(self)
    #########################################################################################	  

    #Tulare Basin Reservoirs do not need to release to the delta, so they only use their own
    #environmental flow requirements when calculating expected environmental releases
	#arguements passed into the function here are equal to zero
    expected_outflow_releases = {}
    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      expected_outflow_releases[wyt] = np.zeros(366)
    inflow_list = [self.millerton, self.pineflat, self.kaweah, self.success, self.isabella]
    for reservoir_obj in inflow_list:
      reservoir_obj.downstream_short = [_ * cfs_tafd for _ in self.df_short[0]['%s_gains'% reservoir_obj.key].values]

    for reservoir_obj in inflow_list:
      #generates:
      #x.cum_min_release (5 x 365) - daily values of remaining enviromental releases through the end of july, in each wyt
      #x.aug_sept_min_release (5 x 365) - daily values of remaining enviromental releases during the aug-sept period, in each wyt
      #x.oct_nov_min_release (5 x 365) - daily values of remaining enviromental releases during the oct-nov period, in each wyt
      if reservoir_obj.key == "MIL":
        if self.model_mode == 'validation':
          sjrr_toggle_value = 0
        else:
          sjrr_toggle_value = 1
        reservoir_obj.calc_expected_min_release(self, expected_outflow_releases, np.zeros(12), sjrr_toggle_value)
      else:
        reservoir_obj.calc_expected_min_release(self, expected_outflow_releases, np.zeros(12), 0)
	  
    ##Code to calculate snow/flow regressions and save to file
	############################################################################
    self.pineflat.find_release_func(self)
    self.kaweah.find_release_func(self)
    self.success.find_release_func(self)
    self.isabella.find_release_func(self)
    self.millerton.find_release_func(self)	
    # df_res_process = pd.DataFrame()
    # df_res_annual = pd.DataFrame()
    # for x in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
    #   df_res_process['%s_rainfnf' % x.key] = pd.Series(x.rainflood_fnf, index = self.index)
    #   df_res_process['%s_snowfnf' % x.key] = pd.Series(x.snowflood_fnf, index = self.index)
    #   df_res_process['%s_raininf' % x.key] = pd.Series(x.rainflood_inf, index = self.index)
    #   df_res_process['%s_snowinf' % x.key] = pd.Series(x.snowflood_inf, index = self.index)
    #   df_res_process['%s_baseinf' % x.key] = pd.Series(x.baseline_inf, index = self.index)
    #   df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
    #   df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
    #   df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
    #   df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
    #   df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
    # df_res_process.to_csv('calfews_src/data/input/temp_output/res_preprocess_daily.csv')
    # df_res_annual.to_csv('calfews_src/data/input/temp_output/res_presprocess_annual.csv')
	

  def initialize_water_districts(self, scenario = 'baseline'):
    ############################################################################
    ###District Initialization
	############################################################################
    cdef District district_obj
    cdef Private private_obj

	##Kern County Water Agency Member Units
    self.berrenda = District(self, 'berrenda', 'BDM')
    self.belridge = District(self, 'belridge', 'BLR')
    self.buenavista = District(self, 'buenavista', 'BVA')
    self.cawelo = District(self, 'cawelo', 'CWO')
    self.henrymiller = District(self, 'henrymiller', 'HML')
    self.ID4 = District(self, 'ID4', 'ID4')
    self.kerndelta = District(self, 'kerndelta', 'KND')
    self.losthills = District(self, 'losthills', 'LHL')
    self.rosedale = District(self, 'rosedale', 'RRB')
    self.semitropic = District(self, 'semitropic', 'SMI')
    self.tehachapi = District(self, 'tehachapi', 'THC')
    self.tejon = District(self, 'tejon', 'TJC')
    self.westkern = District(self, 'westkern', 'WKN')
    self.wheeler = District(self, 'wheeler', 'WRM')
    self.kcwa = District(self, 'kcwa', 'KCWA')
	##Other Kern County
    self.bakersfield = District(self, 'bakersfield', 'COB')
    self.northkern = District(self, 'northkern', 'NKN')
    ##Friant Kern Contractors
    self.arvin = District(self, 'arvin', 'ARV')
    self.pixley = District(self, 'pixley', 'PIX')
    self.delano = District(self, 'delano', 'DLE')
    self.exeter = District(self, 'exeter', 'EXE')
    self.kerntulare = District(self, 'kerntulare', 'KRT')
    self.lindmore = District(self, 'lindmore', 'LND')
    self.lindsay = District(self, 'lindsay', 'LDS')
    if (scenario == 'baseline'):
      self.lowertule = District(self, 'lowertule', 'LWT')
    elif (scenario['LWT'] == 'baseline'):
      self.lowertule = District(self, 'lowertule', 'LWT')
    else:
      self.lowertule = District(self, 'lowertule', 'LWT', scenario['LWT'])
    self.porterville = District(self, 'porterville', 'PRT')
    self.saucelito = District(self, 'saucelito', 'SAU')
    self.shaffer = District(self, 'shaffer', 'SFW')
    self.sosanjoaquin = District(self, 'sosanjoaquin', 'SSJ')
    self.teapot = District(self, 'teapot', 'TPD')
    self.terra = District(self, 'terra', 'TBA')
    self.tulare = District(self, 'tulare', 'TUL')
    self.fresno = District(self, 'fresno', 'COF')
    self.fresnoid = District(self, 'fresnoid', 'FRS')
    ##Canal Boundaries
    self.socal = District(self, 'socal', 'SOC')
    self.southbay = District(self, 'southbay', 'SOB')
    self.centralcoast = District(self, 'centralcoast', 'CCA')
    ##demands at canal boundaries are taken from observed pumping into canal brannch

    ##Other Agencies
    self.dudleyridge = District(self, 'dudleyridge', 'DLR')
    self.tularelake = District(self, 'tularelake', 'TLB')
    self.kaweahdelta = District(self, 'kaweahdelta', 'KWD')
    self.westlands = District(self, 'westlands', 'WSL')
    self.sanluiswater = District(self, 'sanluiswater', 'SNL')
    self.panoche = District(self, 'panoche', 'PNC')
    self.delpuerto = District(self, 'delpuerto', 'DLP')
    self.chowchilla = District(self, 'chowchilla', 'CWC')
    self.maderairr = District(self, 'maderairr', 'MAD')
    self.othertule = District(self, 'othertule', 'OTL')
    self.otherkaweah = District(self, 'otherkaweah', 'OKW')
    self.otherfriant = District(self, 'otherfriant', 'OFK')
    self.othercvp = District(self, 'othercvp', 'OCD')
    self.otherexchange = District(self, 'otherexchange', 'OEX')
    self.othercrossvalley = District(self, 'othercrossvalley', 'OXV')
    self.otherswp = District(self, 'otherswp', 'OSW')
    self.consolidated = District(self, 'consolidated', 'CNS')
    self.alta = District(self, 'alta', 'ALT')
    self.krwa = District(self, 'krwa', 'KRWA')
    # self.krwa.turnback_use = 0
	
    ##Private water users
    self.wonderful = Private(self, 'wonderful', 'WON', 1.0)
    self.metropolitan = Private(self, 'metropolitan', 'MET', 1.0)
    self.castaic = Private(self, 'castaic', 'CTL', 1.0)
    self.coachella = Private(self, 'coachella', 'CCH', 1.0)
	
	##List of all intialized districts for looping
    self.district_list = [self.berrenda, self.belridge, self.buenavista, self.cawelo, self.henrymiller, self.ID4, self.kerndelta, self.losthills, self.rosedale, self.semitropic, self.tehachapi, self.tejon, self.westkern, self.wheeler, self.kcwa, self.bakersfield, self.northkern, self.arvin, self.delano, self.pixley, self.exeter, self.kerntulare, self.lindmore, self.lindsay, self.lowertule, self.porterville, self.saucelito, self.shaffer, self.sosanjoaquin, self.teapot, self.terra, self.tulare, self.fresno, self.fresnoid, self.socal, self.southbay, self.centralcoast, self.dudleyridge, self.tularelake, self.westlands, self.chowchilla, self.maderairr, self.othertule, self.otherkaweah, self.otherfriant, self.othercvp, self.otherexchange, self.othercrossvalley, self.otherswp, self.consolidated, self.alta, self.krwa, self.kaweahdelta, self.sanluiswater, self.panoche, self.delpuerto]
    #list of all california aqueduct branch urban users (their demands are generated from pumping data - different than other district objects)
    self.urban_list = [self.socal, self.centralcoast, self.southbay]
    self.private_list = [self.wonderful]
    self.city_list = [self.metropolitan, self.castaic, self.coachella]
	
    ##District Keys - dictionary to be able to call the member from its key
    self.district_keys = {}
    self.district_keys_len = {}
    for district_obj in self.district_list:
      self.district_keys[district_obj.key] = district_obj
      self.district_keys_len[district_obj.key] = len(district_obj)
    for private_obj in self.private_list:
      self.district_keys[private_obj.key] = private_obj###Private interests in the Kern Water Bank (Westside Mutual)  
      self.district_keys_len[private_obj.key] = len(private_obj)###Private interests in the Kern Water Bank (Westside Mutual)  
    for private_obj in self.city_list:
      self.district_keys[private_obj.key] = private_obj
      self.district_keys_len[private_obj.key] = len(private_obj)
    
    if self.demand_type == 'pesticide':
      self.load_pesticide_acreage()
    elif self.demand_type == 'pmp':
      self.load_pmp_model()
    
    self.allocate_private_contracts()
	
    for district_obj in self.district_list:
      district_obj.find_baseline_demands(0, self.non_leap_year, self.days_in_month)
    for private_obj in self.private_list:
      private_obj.find_baseline_demands(self.non_leap_year, self.days_in_month)
      private_obj.turnout_list = {}
      for district_key in private_obj.district_list:
        # district_obj = self.district_keys[district_key] 
        self.district_keys[district_key].has_private = 1
        private_obj.turnout_list[district_key] = self.district_keys[district_key].turnout_list
    for private_obj in self.city_list:
      private_obj.turnout_list = {}
      for district_key in private_obj.district_list:
        # district_obj = self.district_keys[district_key] 
        self.district_keys[district_key].has_private = 1
        private_obj.turnout_list[district_key] = self.district_keys[district_key].turnout_list

	
  def initialize_sw_contracts(self):
    ############################################################################
    ###Contract Initialization
	############################################################################
    cdef Contract contract_obj
    cdef District district_obj
    cdef Private private_obj

   	#Project Contracts/Water Rights
    self.friant1 = Contract(self, 'friant1', 'FR1')
    self.friant2 = Contract(self, 'friant2', 'FR2')
    self.swpdelta = Contract(self, 'swpdelta', 'SLS')
    self.cvpdelta = Contract(self, 'cvpdelta', 'SLF')
    self.cvpexchange = Contract(self, 'cvpexchange', 'ECH')
    self.crossvalley = Contract(self, 'crossvalley', 'CVC')
    self.kernriver = Contract(self, 'kernriver', 'KRR')
    self.tuleriver = Contract(self, 'tuleriver', 'TRR')
    self.kaweahriver = Contract(self, 'kaweahriver', 'WRR')
    self.kingsriver = Contract(self, 'kingsriver', 'KGR')
	
	##List of all intialized contracts for looping
    self.contract_list = [self.friant1, self.friant2, self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley, self.kernriver, self.tuleriver, self.kaweahriver, self.kingsriver]

    ##Contract Keys - dictionary to be able to call the member from its key	
    self.contract_keys = {}
    for contract_obj in self.contract_list:
      self.contract_keys[contract_obj.name] = contract_obj
	  
    ##For each district on the district list, find the total carryover storage
    ##they have associated with each contract
    ##Dictionary is a part of the district class, and dictionary keys are the names of contract types
    for district_obj in self.district_list:
      for contract_key in district_obj.contract_list:
        contract_object = self.contract_keys[contract_key]
        if contract_object.type == "contract":
          if district_obj.has_pesticide:
            district_obj.contract_carryover_list[contract_key] = contract_object.carryover*district_obj.project_contract[contract_key]*(1.0-min(district_obj.private_fraction))
          else:
            district_obj.contract_carryover_list[contract_key] = contract_object.carryover*district_obj.project_contract[contract_key]*(1.0-district_obj.private_fraction[0])

        elif contract_object.type == "right":
          if district_obj.has_pesticide:
            district_obj.contract_carryover_list[contract_key] = contract_object.carryover*district_obj.rights[contract_key]['carryover']*(1.0-min(district_obj.private_fraction))
          else:
            district_obj.contract_carryover_list[contract_key] = contract_object.carryover*district_obj.rights[contract_key]['carryover']*(1.0-district_obj.private_fraction[0])
        if contract_key == "tableA":
          district_obj.initial_table_a = district_obj.project_contract[contract_key]

    for private_obj in self.private_list:
      private_obj.contract_list = []
      for district_key in private_obj.district_list:
        district = self.district_keys[district_key]
        for contract_key in district.contract_list:
          if contract_key not in private_obj.contract_list:
            private_obj.contract_list.append(contract_key)
      for district_key in private_obj.district_list:
        district_obj = self.district_keys[district_key]
        for contract_key in district_obj.contract_list:
          contract_object = self.contract_keys[contract_key]
          if contract_object.type == "contract":
            private_obj.contract_carryover_list[district_key][contract_key] = contract_object.carryover*district_obj.project_contract[contract_key]*max(private_obj.private_fraction[district_key])
          elif contract_object.type == "right":
            private_obj.contract_carryover_list[district_key][contract_key] = contract_object.carryover*district_obj.rights[contract_key]['carryover']*max(private_obj.private_fraction[district_key])

    for private_obj in self.city_list:
      private_obj.contract_list = []
      for district_key in private_obj.district_list:
        district = self.district_keys[district_key]
        for contract_key in district.contract_list:
          if contract_key not in private_obj.contract_list:
            private_obj.contract_list.append(contract_key)
      for district_key in private_obj.district_list:
        district_obj = self.district_keys[district_key]
        for contract_key in district_obj.contract_list:
          contract_object = self.contract_keys[contract_key]
          if contract_object.type == "contract":
            private_obj.contract_carryover_list[district_key][contract_key] = contract_object.carryover*district_obj.project_contract[contract_key]*max(private_obj.private_fraction[district_key])
          elif contract_object.type == "right":
            private_obj.contract_carryover_list[district_key][contract_key] = contract_object.carryover*district_obj.rights[contract_key]['carryover']*max(private_obj.private_fraction[district_key])

    ###Find Risk in Contract Delivery
    self.determine_recharge_recovery_risk()


  def initialize_water_banks(self, scenario='baseline'):
    ############################################################################
    ###Water Bank Initialization
	############################################################################
    cdef Waterbank waterbank_obj
    cdef District district_obj, leiu_obj
    cdef Private private_obj

	##Water Banks
    self.stockdale = Waterbank(self, 'stockdale', 'STOCK')
    self.kernriverbed = Waterbank(self, 'kernriverbed', 'KRC')
    self.poso = Waterbank(self, 'poso', 'POSO')
    self.pioneer = Waterbank(self, 'pioneer', 'PIO')
    self.kwb = Waterbank(self, 'kwb', 'KWB')
    self.berrendawb = Waterbank(self, 'berrendawb', 'BRM')
    self.b2800 = Waterbank(self, 'b2800', 'B2800')
    self.aewb = Waterbank(self, 'aewb', 'AEMWD')
    self.wkwb = Waterbank(self, 'wkwb', 'WKB')
    self.irvineranch = Waterbank(self, 'irvineranch', 'IVR')
    self.northkernwb = Waterbank(self, 'northkernwb', 'NKB')
	
    self.waterbank_list = [self.stockdale, self.kernriverbed, self.poso, self.pioneer, self.kwb, self.berrendawb, self.b2800, self.wkwb, self.irvineranch, self.northkernwb]
    self.leiu_list = []

    for district_obj in self.district_list:
      if (district_obj.in_leiu_banking == 1):
        self.leiu_list.append(district_obj)

    for district_obj in self.district_list:
      district_obj.delivery_location_list = []
      district_obj.delivery_location_list.append(district_obj.key)
      # district_obj.daily_supplies_full[district_obj.key + '_recharged'] = np.zeros(self.T)
      district_obj.deliveries[district_obj.key + '_recharged'] = np.zeros(self.number_years)
      for waterbank_obj in self.waterbank_list:
        # district_obj.daily_supplies_full[waterbank_obj.key + '_recharged'] = np.zeros(self.T)
        district_obj.deliveries[waterbank_obj.key + '_recharged'] = np.zeros(self.number_years)
        district_obj.delivery_location_list.append(waterbank_obj.key)
      for leiu_obj in self.leiu_list:
        # district_obj.daily_supplies_full[leiu_obj.key + '_recharged'] = np.zeros(self.T)
        district_obj.deliveries[leiu_obj.key + '_recharged'] = np.zeros(self.number_years)
        district_obj.delivery_location_list.append(leiu_obj.key)
    for private_obj in self.private_list:
      private_obj.delivery_location_list = {}
      for district_key in private_obj.district_list:
        private_obj.delivery_location_list[district_key] = []
        private_obj.delivery_location_list[district_key].append(district_key)
        # private_obj.daily_supplies_full[district_key + '_' +  district_key + '_recharged'] = np.zeros(self.T)
        private_obj.deliveries[district_key][district_key + '_recharged'] = np.zeros(self.number_years)
      for waterbank_obj in self.waterbank_list:
        for district_key in private_obj.district_list:
          private_obj.delivery_location_list[district_key].append(waterbank_obj.key)
          # private_obj.daily_supplies_full[district_key + '_' + waterbank_obj.key + '_recharged'] = np.zeros(self.T)
          private_obj.deliveries[district_key][waterbank_obj.key + '_recharged'] = np.zeros(self.number_years)
      for lb in self.leiu_list:
        for district_key in private_obj.district_list:
          private_obj.delivery_location_list[district_key].append(lb.key)
          # private_obj.daily_supplies_full[district_key + '_' + lb.key + '_recharged'] = np.zeros(self.T)
          private_obj.deliveries[district_key][lb.key + '_recharged'] = np.zeros(self.number_years)
    for private_obj in self.city_list:
      private_obj.delivery_location_list = {}
      for district_key in private_obj.district_list:
        private_obj.delivery_location_list[district_key] = []
        private_obj.delivery_location_list[district_key].append(district_key)
        # private_obj.daily_supplies_full[district_key + '_' +  district_key + '_recharged'] = np.zeros(self.T)
        private_obj.deliveries[district_key][district_key + '_recharged'] = np.zeros(self.number_years)
      for waterbank_obj in self.waterbank_list:
        for district_key in private_obj.district_list:
          private_obj.delivery_location_list[district_key].append(waterbank_obj.key)
          # private_obj.daily_supplies_full[district_key + '_' + waterbank_obj.key + '_recharged'] = np.zeros(self.T)
          private_obj.deliveries[district_key][waterbank_obj.key + '_recharged'] = np.zeros(self.number_years)
      for lb in self.leiu_list:
        for district_key in private_obj.district_list:
          private_obj.delivery_location_list[district_key].append(lb.key)
          # private_obj.daily_supplies_full[district_key + '_' + lb.key + '_recharged'] = np.zeros(self.T)
          private_obj.deliveries[district_key][lb.key + '_recharged'] = np.zeros(self.number_years)
        
    if self.model_mode == 'validation':
      self.semitropic.inleiubanked['MET'] = 175.8
      self.semitropic.inleiubanked['SOB'] = 46.0
      self.kwb.banked['ID4'] = 91.7
      self.kwb.banked['DLR'] = 260.0 * 0.0962/ 0.9038 
      self.kwb.banked['SMI'] = 260.0 * 0.0667/ 0.9038 
      self.kwb.banked['TJC'] = 260.0 * 0.02/ 0.9038 
      self.kwb.banked['WON'] = 260.0 * 0.4806/ 0.9038 
      self.kwb.banked['WRM'] = 260.0 * 0.2403/ 0.9038 
    elif self.model_mode == 'simulation':
      self.semitropic.inleiubanked['MET'] = 750.0
      self.semitropic.inleiubanked['SOB'] = 750.0
      self.kwb.banked['ID4'] = 500.0
      self.kwb.banked['DLR'] = 500.0
      self.kwb.banked['SMI'] = 500.0
      self.kwb.banked['TJC'] = 500.0
      self.kwb.banked['WON'] = 500.0
      self.kwb.banked['WRM'] = 500.0

  def initialize_canals(self, scenario = 'baseline'):
    ############################################################################
    ###Canal Initialization
	############################################################################
    #Waterways
    if (scenario == 'baseline'):
      self.fkc = Canal('fkc', 'FKC')
    elif (scenario['FKC'] == 'baseline'):
      self.fkc = Canal('fkc', 'FKC')
    else:
      self.fkc = Canal('fkc', 'FKC', scenario['FKC'])

    self.xvc = Canal('xvc', 'XVC')
    self.madera = Canal('madera', 'MDC')
    self.calaqueduct = Canal('calaqueduct', 'CAA')
    self.kwbcanal = Canal('kwbcanal', 'KBC')
    self.aecanal = Canal('aecanal', 'AEC')
    self.kerncanal = Canal('kerncanal', 'KNC')
    self.calloway = Canal('calloway', 'CWY')
    self.lerdo = Canal('lerdo', 'LRD')
    self.beardsley = Canal('beardsley', 'BLY')
    self.kernriverchannel = Canal('kernriverchannel', 'KNR')
    self.kaweahriverchannel = Canal('kaweahriverchannel', 'KWR')
    self.tuleriverchannel = Canal('tuleriverchannel', 'TLR')
    self.kingsriverchannel = Canal('kingsriverchannel', 'KGR')
	
    self.canal_list = [self.fkc, self.madera, self.xvc, self.calaqueduct, self.kwbcanal, self.aecanal, self.kerncanal, self.calloway, self.lerdo, self.beardsley, self.kernriverchannel, self.kaweahriverchannel, self.tuleriverchannel, self.kingsriverchannel]

    #initialize variables to store pumping from delta	
    self.trp_pumping = [0.0 for _ in range(self.T)]
    self.hro_pumping = [0.0 for _ in range(self.T)]
    self.cvp_allocation = [0.0 for _ in range(self.T)]
    self.swp_allocation = [0.0 for _ in range(self.T)]
    self.annual_SWP = [0.0 for _ in range(self.number_years)]
    self.annual_CVP = [0.0 for _ in range(self.number_years)]
    self.ytd_pump_trp = [0.0 for _ in range(self.T)]
    self.ytd_pump_hro = [0.0 for _ in range(self.T)]


	
  def create_object_associations(self):
    cdef Private private_obj
    cdef District district_obj
    cdef Canal canal_obj, canal_obj2
    cdef Contract contract_obj
    cdef Reservoir reservoir_obj

    ##Canal Structure Dictionary
    #This is the dictionary that holds the structure of the canal system.  The dictionary is made up of lists, with the objects in the lists representing delivery nodes on the canal (canal is denoted by dictionary key)
	#Objects can be districts, waterbanks, or other canals.  Canal objects show an intersection with the canal represented by the dictionary 'key' that holds the list.  Dictionary keys are all canal keys.  If a canal is located on a list, the canal associated with that list's key will also be on the list associated with the canal of the first key (i.e., if self.fkc is on the list with the key 'self.canal_district['xvc'], then the object self.xvc will be on the list with the key self.canal_district['fkc'] - these intersections help to organize these lists into a structure that models the interconnected canal structure
	#The first object on each list is either a reservoir or another canal
    self.canal_district = {}
    self.canal_district['fkc'] = [self.millerton, self.fresno, self.fresnoid, self.kingsriverchannel, self.otherfriant, self.tulare, self.kaweahdelta, self.otherkaweah, self.kaweahriverchannel, self.exeter, self.lindsay, self.lindmore, self.porterville, self.lowertule, self.othertule, self.tuleriverchannel, self.teapot, self.saucelito, self.terra, self.othercrossvalley, self.pixley, self.delano, self.kerntulare, self.sosanjoaquin, self.shaffer, self.northkern, self.northkernwb, self.xvc, self.kernriverchannel, self.aecanal]
    self.canal_district['mdc'] = [self.millerton, self.maderairr, self.chowchilla]
    self.canal_district['caa'] = [self.sanluis, self.southbay, self.sanluiswater, self.panoche, self.delpuerto, self.otherswp, self.othercvp, self.otherexchange, self.westlands, self.centralcoast, self.tularelake, self.dudleyridge, self.losthills, self.berrenda, self.belridge, self.semitropic, self.buenavista, self.wkwb, self.xvc, self.kwbcanal, self.kernriverchannel, self.henrymiller, self.wheeler, self.aecanal, self.tejon, self.tehachapi, self.socal]
    self.canal_district['xvc'] = [self.calaqueduct, self.buenavista, self.kwb, self.irvineranch, self.pioneer, self.b2800, self.berrendawb, self.rosedale, self.ID4, self.kernriverchannel, self.fkc, self.aecanal, self.beardsley]
    self.canal_district['kbc'] = [self.calaqueduct, self.kwb, self.kerncanal]
    self.canal_district['aec'] = [self.fkc, self.xvc, self.kernriverchannel, self.arvin, self.calaqueduct]
    self.canal_district['knr'] = [self.isabella, self.calloway, self.kerndelta, self.lerdo, self.xvc, self.aecanal, self.fkc, self.kerncanal, self.rosedale, self.bakersfield, self.berrendawb, self.b2800, self.pioneer, self.kwb, self.buenavista, self.calaqueduct]
    self.canal_district['knc'] = [self.kernriverchannel, self.kerndelta, self.ID4, self.pioneer, self.buenavista, self.kwb]
    #self.canal_district['gsl'] = [self.kernriverchannel, self.xvc, self.rosedale21]
    self.canal_district['cwy'] = [self.kernriverchannel, self.beardsley, self.cawelo, self.northkern, self.poso, self.northkernwb]
    self.canal_district['lrd'] = [self.kernriverchannel, self.cawelo, self.northkern, self.poso, self.northkernwb]
    self.canal_district['bly'] = [self.xvc, self.calloway]
    self.canal_district['kwr'] = [self.kaweah, self.otherkaweah, self.tulare, self.fkc, self.kaweahdelta, self.tularelake]
    self.canal_district['tlr'] = [self.success, self.othertule, self.lowertule, self.porterville, self.fkc, self.tularelake]
    self.canal_district['kgr'] = [self.pineflat, self.consolidated, self.alta, self.krwa, self.fresnoid, self.fkc, self.kaweahdelta, self.tularelake]

    self.canal_district_len = {}
    for key in ['fkc','mdc','caa','xvc','kbc','aec','knr','knc','cwy','lrd','bly','kwr','tlr','kgr']:
      self.canal_district_len[key] = len(self.canal_district[key])

    for private_obj in self.private_list:
      private_obj.seepage = {}
      private_obj.must_fill = {}
      private_obj.seasonal_connection = {}
      for district_key in private_obj.district_list:
        district_obj = self.district_keys[district_key]
        private_obj.seepage[district_key] = district_obj.seepage
        private_obj.must_fill[district_key] = district_obj.must_fill
        private_obj.seasonal_connection[district_key] = district_obj.seasonal_connection
    for private_obj in self.city_list:
      private_obj.seepage = {}
      private_obj.must_fill = {}
      private_obj.seasonal_connection = {}
      for district_key in private_obj.district_list:
        district_obj = self.district_keys[district_key]
        private_obj.seepage[district_key] = district_obj.seepage
        private_obj.must_fill[district_key] = district_obj.must_fill
        private_obj.seasonal_connection[district_key] = district_obj.seasonal_connection
  
    ###After the canal structure is defined, each of the nodes on the list
    ###has a demand initialized.  There are many different types of demands
    ###depending on the surface water availabilities
    for canal_obj in self.canal_list:
      canal_obj.num_sites = self.canal_district_len[canal_obj.name]
      canal_obj.turnout_use = [0.0 for _ in range(canal_obj.num_sites)] ##how much water diverted at a node
      canal_obj.flow = [0.0 for _ in range(canal_obj.num_sites+1)] ##how much water passing through a node (inc. diversions)
      canal_obj.demand = {}
      canal_obj.turnout_frac = {}
      canal_obj.recovery_flow_frac = {}
      canal_obj.daily_flow = {}
      canal_obj.daily_turnout = {}
      for i in range(len(self.canal_district[canal_obj.name])):
        canal_obj.daily_flow[self.canal_district[canal_obj.name][i].key] = np.zeros(self.T)
        canal_obj.daily_turnout[self.canal_district[canal_obj.name][i].key] = np.zeros(self.T)
      for z in ['contractor', 'turnout', 'excess', 'priority', 'secondary', 'initial', 'supplemental']:
        canal_obj.demand[z] = np.zeros(canal_obj.num_sites)
        canal_obj.turnout_frac[z] = np.zeros(canal_obj.num_sites)
        canal_obj.recovery_flow_frac[z] = np.ones(canal_obj.num_sites)
      for canal_obj2 in [self.calaqueduct, self.fkc, self.madera, self.kernriverchannel, self.tuleriverchannel, self.kaweahriverchannel]:
        canal_obj.demand[canal_obj2.name] = np.zeros(canal_obj.num_sites)##for irrigation deliveries
        canal_obj.turnout_frac[canal_obj2] = np.zeros(canal_obj.num_sites)
        canal_obj.recovery_flow_frac[canal_obj2] = np.ones(canal_obj.num_sites)

    ##There are 6 main canals (fkc, madera, calaqueduct, kernriverchannel, kaweahriverchannel, and tuleriverchannel) that are directly connected to surface water storage
    ##The other canals connect these major arteries, but sometimes water from one canal will have 'priority' to use the connecting canals
    ##mainly shows that the California Aqueduct has first priority to use the Cross Valley Canal
	##and the Kern River has first priority over the kern river canal
    self.canal_priority = {}
    self.canal_priority['fkc'] = [self.fkc]
    self.canal_priority['mdc'] = [self.madera]
    self.canal_priority['caa'] = [self.calaqueduct]
    self.canal_priority['xvc'] = [self.calaqueduct]
    self.canal_priority['kbc'] = [self.calaqueduct, self.kernriverchannel]
    self.canal_priority['aec'] = [self.calaqueduct, self.fkc]
    self.canal_priority['knr'] = [self.kernriverchannel]
    self.canal_priority['knc'] = [self.kernriverchannel]
    self.canal_priority['gsl'] = [self.calaqueduct, self.fkc, self.kernriverchannel]
    self.canal_priority['cwy'] = [self.calaqueduct, self.fkc, self.kernriverchannel]
    self.canal_priority['lrd'] = [self.calaqueduct, self.fkc, self.kernriverchannel]
    self.canal_priority['bly'] = [self.calaqueduct, self.fkc, self.kernriverchannel]
    self.canal_priority['kwr'] = [self.kaweahriverchannel]
    self.canal_priority['tlr'] = [self.tuleriverchannel]    
    self.canal_priority['kgr'] = [self.kingsriverchannel]    

    ##Linkages between reservoirs, canals, and surface water contracts
    ##Reservoir-Contract Relationships (reservoirs are dictionary key, contracts are list objects)
    self.reservoir_contract = {}
    self.reservoir_contract['SLF'] = [self.crossvalley, self.cvpdelta, self.cvpexchange]
    self.reservoir_contract['SLS'] = [self.swpdelta]
    self.reservoir_contract['MIL'] = [self.friant2, self.friant1]
    self.reservoir_contract['ISB'] = [self.kernriver]
    self.reservoir_contract['SUC'] = [self.tuleriver]
    self.reservoir_contract['KWH'] = [self.kaweahriver]
    self.reservoir_contract['PFT'] = [self.kingsriver]
	
    for district_obj in self.district_list:
      district_obj.carryover_rights = {}
      for contract_obj in self.contract_list:
        if contract_obj.type == 'right':
          if district_obj.has_pesticide:
            district_obj.carryover_rights[contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*(1.0-district_obj.private_fraction[0])
          else:
            district_obj.carryover_rights[contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*(1.0-district_obj.private_fraction[0])
        else:
          district_obj.carryover_rights[contract_obj.name] = 0.0

    for private_obj in self.private_list:
      private_obj.carryover_rights = {}
      for district_key in private_obj.district_list:
        district_obj = self.district_keys[district_key]
        private_obj.carryover_rights[district_key] = {}
        for contract_obj in self.contract_list:
          if contract_obj.type == 'right':
            private_obj.carryover_rights[district_key][contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*private_obj.private_fraction[district_key][0]
          else:
            private_obj.carryover_rights[district_key][contract_obj.name] = 0.0

    for private_obj in self.city_list:
      private_obj.carryover_rights = {}
      for district_key in private_obj.district_list:
        district_obj = self.district_keys[district_key]
        private_obj.carryover_rights[district_key] = {}
        for contract_obj in self.contract_list:
          if contract_obj.type == 'right':
            private_obj.carryover_rights[district_key][contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*private_obj.private_fraction[district_key][0]
          else:
            private_obj.carryover_rights[district_key][contract_obj.name] = 0.0
		
	##Use reservoir/contract dictionary to develop
	##a list linking individual districts to reservoirs,
	##based on their individual contracts
    for district_obj in self.district_list:
      district_obj.reservoir_contract = {}
      for reservoir_obj in self.reservoir_list:
        use_reservoir = 0
        for contract_obj in self.reservoir_contract[reservoir_obj.key]:
          for contract_key_dis in district_obj.contract_list:
            if contract_obj.name == contract_key_dis:
              use_reservoir = 1
              break
        if use_reservoir == 1:
          district_obj.reservoir_contract[reservoir_obj.key] = 1
        else:
          district_obj.reservoir_contract[reservoir_obj.key] = 0

    for private_obj in self.private_list:
      private_obj.reservoir_contract = {}
      for reservoir_obj in self.reservoir_list:
        use_reservoir = 0
        for contract_obj in self.reservoir_contract[reservoir_obj.key]:
          for district_key in private_obj.district_list:
            district_obj = self.district_keys[district_key]
            for contract_key_dis in district_obj.contract_list:
              if contract_obj.name == contract_key_dis:
                use_reservoir = 1
                break
        if use_reservoir == 1:
          private_obj.reservoir_contract[reservoir_obj.key] = 1
        else:
          private_obj.reservoir_contract[reservoir_obj.key] = 0

    for private_obj in self.city_list:
      private_obj.reservoir_contract = {}
      for reservoir_obj in self.reservoir_list:
        use_reservoir = 0
        for contract_obj in self.reservoir_contract[reservoir_obj.key]:
          for district_key in private_obj.district_list:
            district_obj = self.district_keys[district_key]
            for contract_key_dis in district_obj.contract_list:
              if contract_obj.name == contract_key_dis:
                use_reservoir = 1
                break
        if use_reservoir == 1:
          private_obj.reservoir_contract[reservoir_obj.key] = 1
        else:
          private_obj.reservoir_contract[reservoir_obj.key] = 0
		  
    ##Contract-Reservoir Relationships (contracts are dictionary key, reservoirs are list objects)
    self.contract_reservoir = {}
    self.contract_reservoir['FR1'] = self.millerton
    self.contract_reservoir['FR2'] = self.millerton
    self.contract_reservoir['KRR'] = self.isabella
    self.contract_reservoir['KGR'] = self.pineflat
    self.contract_reservoir['TRR'] = self.success
    self.contract_reservoir['WRR'] = self.kaweah
    self.contract_reservoir['SLS'] = self.sanluisstate
    self.contract_reservoir['SLF'] = self.sanluisfederal
    self.contract_reservoir['ECH'] = self.sanluisfederal
    self.contract_reservoir['CVC'] = self.sanluisfederal

    ##Canal-Contract Relationships (canals are dictionary key, contracts are list objects)
    self.canal_contract = {}
    self.canal_contract['fkc'] = [self.friant1, self.friant2]
    self.canal_contract['mdc'] = [self.friant1, self.friant2]
    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]
    self.canal_contract['knr'] = [self.kernriver]
    self.canal_contract['tlr'] = [self.tuleriver]
    self.canal_contract['kwr'] = [self.kaweahriver]
    self.canal_contract['kgr'] = [self.kingsriver]
    self.canal_contract['xvc'] = []
	
    ##Contracts-Canal Relationships (which canals can be physically reached with contracts)	
    self.contract_turnouts = {}
    self.contract_turnouts['friant1'] = ['fkc', 'mdc', 'xvc', 'kbc', 'aec', 'knr', 'knc', 'gsl', 'cwy', 'lrd', 'bly']
    self.contract_turnouts['friant2'] = ['fkc', 'mdc', 'xvc', 'kbc', 'aec', 'knr', 'knc', 'gsl', 'cwy', 'lrd', 'bly']
    self.contract_turnouts['tableA'] = ['caa', 'xvc', 'kbc', 'aec', 'knr', 'knc', 'gsl', 'cwy', 'lrd', 'bly']
    self.contract_turnouts['cvpdelta'] = ['caa', 'xvc', 'kbc', 'aec', 'knr', 'knc', 'gsl', 'cwy', 'lrd', 'bly']
    self.contract_turnouts['exchange'] = ['caa', 'xvc', 'kbc', 'aec', 'knr', 'knc', 'gsl', 'cwy', 'lrd', 'bly']
    self.contract_turnouts['cvc'] = ['caa', 'xvc', 'kbc', 'aec', 'knr', 'knc', 'gsl', 'cwy', 'lrd', 'bly']
    self.contract_turnouts['kern'] = ['caa', 'xvc', 'kbc', 'aec', 'knr', 'knc', 'gsl', 'cwy', 'lrd', 'bly']
    self.contract_turnouts['tule'] = ['kwr', 'fkc']
    self.contract_turnouts['kaweah'] = ['tlr', 'fkc']
    self.contract_turnouts['kings'] = ['kgr', 'fkc']

	
    ##Reservoir-Canal Relationships (reservoirs are dictionary key, canals are list objects)
    self.reservoir_canal = {}
    self.reservoir_canal['SLS'] = [self.calaqueduct]
    self.reservoir_canal['SLF'] = [self.calaqueduct]
    self.reservoir_canal['SNL'] = [self.calaqueduct]
    self.reservoir_canal['MIL'] = [self.fkc, self.madera]
    self.reservoir_canal['ISB'] = [self.kernriverchannel]
    self.reservoir_canal['SUC'] = [self.tuleriverchannel]
    self.reservoir_canal['KWH'] = [self.kaweahriverchannel]
    self.reservoir_canal['PFT'] = [self.kingsriverchannel]
	
    self.canal_reservoir = {}
    self.canal_reservoir['fkc'] = [self.millerton]
    self.canal_reservoir['caa'] = [self.sanluisstate]
    self.canal_reservoir['knr'] = [self.isabella]
    for reservoir_obj in self.reservoir_list:	
      reservoir_obj.total_capacity = 0.0
      for canal_obj in self.reservoir_canal[reservoir_obj.key]:
        reservoir_obj.total_capacity += canal_obj.capacity['normal'][0]
	
    self.pumping_turnback = {}
    self.allocation_losses = {}
    for z in ['SLS', 'SLF', 'MIL', 'ISB', 'SUC', 'KWH', 'PFT']:
      self.pumping_turnback[z] = 0.0
      self.allocation_losses[z] = 0.0
####################################################################################################################
#####################################################################################################################
	  
	  
#####################################################################################################################
#############################     Pre processing functions    #######################################################
#####################################################################################################################

  def set_sensitivity_factors(self):
    for sensitivity_factor in self.sensitivity_factors['district_factor_list']:
      # set model sensitivity factors equal to sample values from input file
      index = [x == sensitivity_factor for x in self.sensitivity_sample_names]
      index = np.where(index)[0][0]
      self.sensitivity_factors[sensitivity_factor]['realization'] = self.sensitivity_sample[index]


  def find_running_WYI(self):
    cdef Reservoir reservoir_obj

    ###Pre-processing function
	##Finds the 8 River, Sacramento, and San Joaquin indicies based on flow projections
    lastYearSRI = 10.26 # WY 1996
    lastYearSJI = 4.12 # WY 1996
    startMonth = self.month[0]
    startYear = self.starting_year
    rainflood_sac_obs = 0.0
    snowflood_sac_obs = 0.0
    rainflood_sj_obs = 0.0
    snowflood_sj_obs = 0.0
    index_exceedence = 2
    reservoir_list = [self.shasta, self.folsom, self.oroville, self.yuba, self.newmelones, self.donpedro, self.exchequer, self.millerton]
    sac_list = [self.shasta, self.folsom, self.oroville, self.yuba]
    sj_list = [self.newmelones, self.donpedro, self.exchequer, self.millerton]
    for t in range(0,self.T):
      year_index = self.year[t] - startYear
      m = self.month[t]
      da = self.day_month[t]
      dowy = self.dowy[t]
      index_exceedence_sac = 9
      index_exceedence_sj = 5
	  ##8 River Index
      for reservoir_obj in reservoir_list:
        self.delta.eri[m-startMonth + year_index*12] + reservoir_obj.fnf[t]*1000
	  ####################Sacramento Index#############################################################################################
	  ##Individual Rainflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
      if m >=10:
        self.delta.forecastSJI[t] = lastYearSJI
        self.delta.forecastSRI[t] = lastYearSRI
      else:
        res_rain_forecast = 0.0
        for reservoir_obj in sac_list:
          res_rain_forecast += reservoir_obj.rainflood_fnf[t] + reservoir_obj.rainfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL RAIN
        if m >= 4 and m < 10:
          sac_rain = rainflood_sac_obs
        else:
          sac_rain = max(rainflood_sac_obs, res_rain_forecast)
	    ##Individual Snowflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_snow_forecast = 0.0
        for reservoir_obj in sac_list:
          res_snow_forecast += reservoir_obj.snowflood_fnf[t] + reservoir_obj.snowfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL SNOW
        if m >= 8 and m < 10:
          sac_snow = snowflood_sac_obs
        else:
          sac_snow = max(snowflood_sac_obs, res_snow_forecast)
	  #######################################################################################################################################
	  #####################San Joaquin Index################################################################################################
        ##Individual Rainflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_rain_forecast = 0.0
        for reservoir_obj in sj_list:
          res_rain_forecast += reservoir_obj.rainflood_fnf[t] + reservoir_obj.rainfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SJ TOTAL RAIN
        if m >= 4 and m < 10:
          sj_rain = rainflood_sj_obs
        else:
          sj_rain = max(rainflood_sj_obs, res_rain_forecast)
	    ##Individual Snowflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_snow_forecast = 0.0
        for reservoir_obj in sj_list:
          res_snow_forecast += reservoir_obj.snowflood_fnf[t] + reservoir_obj.snowfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL SNOW
        if m >= 8 and m < 10:
          sj_snow = snowflood_sj_obs
        else:
          sj_snow = max(snowflood_sj_obs, res_snow_forecast)

      ###INDEX FORECASTS########################################################################################################################
        self.delta.forecastSJI[t] = min(lastYearSJI,4.5)*0.2 + sj_rain*0.2 + sj_snow*0.6
        self.delta.forecastSRI[t] = min(lastYearSRI,10)*0.3 + sac_rain*0.3 + sac_snow*0.4

      ##REAL-TIME OBSERVATIONS
      if m >= 10 or m <= 3:
        rainflood_sac_obs += self.shasta.fnf[t] + self.oroville.fnf[t] + self.folsom.fnf[t] + self.yuba.fnf[t]
        rainflood_sj_obs += self.newmelones.fnf[t] + self.donpedro.fnf[t] + self.exchequer.fnf[t] + self.millerton.fnf[t]
      elif m < 8:
        snowflood_sac_obs += self.shasta.fnf[t] + self.oroville.fnf[t] + self.folsom.fnf[t] + self.yuba.fnf[t]
        snowflood_sj_obs += self.newmelones.fnf[t] + self.donpedro.fnf[t] + self.exchequer.fnf[t] + self.millerton.fnf[t]
		
	##SAVE INDEX FROM EACH YEAR (FOR USE IN NEXT YEAR'S FORECAST	
      if m == 9 and da == 30:
        lastYearSRI = 0.3*min(lastYearSRI,10) + 0.3*rainflood_sac_obs + 0.4*snowflood_sac_obs
        lastYearSJI = 0.2*min(lastYearSJI,4.5) + 0.2*rainflood_sj_obs + 0.6*snowflood_sj_obs
        rainflood_sac_obs = 0.0
        snowflood_sac_obs = 0.0
        rainflood_sj_obs = 0.0
        snowflood_sj_obs = 0.0
    # df_wyi = pd.DataFrame()
    # df_wyi['SRI'] = pd.Series(self.delta.forecastSRI, index = self.index)
    # df_wyi['SJI'] = pd.Series(self.delta.forecastSJI, index = self.index)
    # df_wyi.to_csv(self.results_folder + '/water_year_index_simulation.csv')
		

  def predict_delta_gains(self):
    cdef Reservoir reservoir_obj

    ##this function uses a regression to find expected 'unstored' flows coming to the
    ##delta, to better project flow into San Luis
    gains_sac_short = self.df_short[0].SAC_gains * cfs_tafd
    gains_sj_short = self.df_short[0].SJ_gains * cfs_tafd
    eastside_streams_short = self.df_short[0].EAST_gains * cfs_tafd
    depletions_short = self.df_short[0].delta_depletions * cfs_tafd
	
    sac_list = [self.shasta, self.folsom, self.oroville, self.yuba]
    for reservoir_obj in sac_list:
      reservoir_obj.fnf_short = [_ / 1000000.0 for _ in self.df_short[0]['%s_fnf'% reservoir_obj.key].values]
      reservoir_obj.downstream_short = [_ * cfs_tafd for _ in self.df_short[0]['%s_gains'% reservoir_obj.key].values]

	##########################################################################################
    #Initialize gains matricies
	##Unstored flow will be regressed against total FNF expected in that year
    numYears_short = self.short_number_years
    self.running_fnf = [[0.0 for i in range(numYears_short)] for j in range(365)]
    ##Total gains in each month
    monthly_gains = np.zeros((12,numYears_short))
    startYear = self.short_starting_year
    ##########################################################################################
    ##########################################################################################
    #Read flow from historical record
	##########################################################################################
    prev_gains = 0.0
    prev_fnf = 0.0
    for t in range(0,self.T_short):
      ##Get date information
      da = self.short_day_month[t]
      m = self.short_month[t]
      dowy = self.short_dowy[t]
      wateryear = self.short_water_year[t]
		
      #Calculate the total daily unstored gains to the delta
      this_day_fnf = 0.0
      fnf_off = 0.0
      this_day_gains = 0.0
      for reservoir_obj in sac_list:
        this_day_fnf += reservoir_obj.fnf_short[t]
        min_release = reservoir_obj.env_min_flow[self.delta.forecastSCWYT][m-1]*cfs_tafd
        gauge_min = reservoir_obj.temp_releases[self.delta.forecastSCWYT][m-1]*cfs_tafd
        this_day_gains += max(max(reservoir_obj.downstream_short[t] + min_release, 0.0), gauge_min)
        if t >= 30:
          fnf_off += reservoir_obj.fnf_short[t-30]

      this_day_gains += gains_sac_short[t]
      this_day_gains += gains_sj_short[t]
      this_day_gains += eastside_streams_short[t]
		  
      prev_fnf += this_day_fnf
      prev_fnf -= fnf_off
      if t < 30:
        self.running_fnf[dowy][wateryear] = min(prev_fnf*30.0/(t+1), 4.0)
      else:
        self.running_fnf[dowy][wateryear] = min(prev_fnf, 4.0)

      ##Calculate the max daily 'unstored pumping'
      #'unstored pumping' is the minimum of three constraints on the 'gains' flows
      volume_constraint = this_day_gains - self.delta.min_outflow[self.delta.forecastSCWYT][m-1]*cfs_tafd + depletions_short[t]#extra gains after delta outflow requirements
      flow_ratio_constraint = this_day_gains*self.delta.export_ratio[self.delta.forecastSCWYT][m-1]#portion of gains that can be exported 
      state_pumping = np.interp(da, self.delta.pump_max['swp']['d'], self.delta.pump_max['swp']['intake_limit'])#max state pumping
      fed_pumping = np.interp(da, self.delta.pump_max['cvp']['d'], self.delta.pump_max['cvp']['intake_limit'])#max fed pumping
      pumping_constraint = (state_pumping + fed_pumping) * cfs_tafd#max pumping
	  
      ##Monthly
      monthly_gains[m-1][wateryear] += max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
    ##########################################################################################
    ##########################################################################################
    #Perform linear regression - FNF used for running prediction of total 'unstored' flow to delta in oct-mar; apr-jul period
	##########################################################################################
    self.delta_gains_regression = {}
    self.delta_gains_regression['slope'] = np.zeros((365,12))
    self.delta_gains_regression['intercept'] = np.zeros((365,12))

    for x in range(0,365): 
      #fig = plt.figure()
      #coef_save = np.zeros((12,2))
      #regress for gains in oct-mar period and april-jul period
      for mm in range(0,12):
        if x <= self.dowy_eom[self.non_leap_year][mm]:
          one_year_runfnf = self.running_fnf[x]
          monthly_gains_predict = monthly_gains[mm]
        else:
          monthly_gains_predict = np.zeros(numYears_short-1)
          one_year_runfnf = np.zeros(numYears_short-1)
          for yy in range(1,numYears_short):
            monthly_gains_predict[yy-1] = monthly_gains[mm][yy]
            one_year_runfnf[yy-1] = self.running_fnf[x][yy-1]


        coef = np.polyfit(one_year_runfnf, monthly_gains_predict, 1)
        self.delta_gains_regression['slope'][x][mm] = coef[0]
        self.delta_gains_regression['intercept'][x][mm] = coef[1]
        #r = np.corrcoef(one_year_runfnf,monthly_gains_predict)[0,1]
        #coef_save[mm] = coef
      #for mm in range(0,12):
        #ax1 = fig.add_subplot(4,3,mm+1)
        #if x <= self.dowy_eom[mm]:
          #monthly_gains_predict = monthly_gains[mm]
          #one_year_runfnf = self.running_fnf[x]
        #else:
          #monthly_gains_predict = np.zeros(numYears_short-1)
          #one_year_runfnf = np.zeros(numYears_short-1)
          #for yy in range(1,numYears_short):
            #monthly_gains_predict[yy-1] = monthly_gains[mm][yy]
            #one_year_runfnf[yy-1] = self.running_fnf[x][yy-1]

        #ax1.scatter(one_year_runfnf, monthly_gains_predict, s=50, c='red', edgecolor='none', alpha=0.7)
        #ax1.plot([0.0, np.max(one_year_runfnf)], [coef_save[mm][1], (np.max(one_year_runfnf)*coef_save[mm][0] + coef_save[mm][1])],c='red')
      #ax1.set_xlim([np.min(one_year_runfnf), np.max(one_year_runfnf)])
      #plt.show()
      #plt.close()
	  
		
  def find_all_triggers(self):
    #########################################################################################
    #this function searches through canals to find the maximum amount of
	#water that can be taken from each reservoir at one time.  
    #########################################################################################
    cdef Reservoir reservoir_obj
    cdef Canal canal_obj
    cdef District district_obj
    cdef Waterbank waterbank_obj

	#The value self.reservoir.flood_flow_min is used to determine when uncontrolled releases
	#are initiated at the reservoir
    for reservoir_obj in [self.isabella, self.millerton, self.kaweah, self.success, self.pineflat]:
    #for each reservoir, clear the demands of each object
      for district_obj in self.district_list:
        district_obj.current_requested = 0.0
      for waterbank_obj in self.waterbank_list:
        waterbank_obj.current_requested = 0.0
      reservoir_obj.flood_flow_min = 0.0
      for canal_obj in self.reservoir_canal[reservoir_obj.key]:
        #find all demands that can be reached from the reservoir
        reservoir_obj.flood_flow_min += self.find_flood_trigger(canal_obj, reservoir_obj.key, canal_obj.name, 'normal','recharge')
    
	#also calculate for san luis - but split federal and state portions (uncontrolled releases are made seperately)
    #only want the demands that are associated w/ nodes that have a contract
    self.canal_contract['caa'] = [self.swpdelta]
    for district_obj in self.district_list:
      district_obj.current_requested = 0.0
    for waterbank_obj in self.waterbank_list:
      waterbank_obj.current_requested = 0.0
    self.sanluisstate.flood_flow_min = self.find_flood_trigger(self.calaqueduct, self.sanluis.key, self.calaqueduct.name, 'normal', 'recharge')
    #same thing for the federal portion
    self.canal_contract['caa'] = [self.cvpdelta, self.cvpexchange, self.crossvalley]
    for district_obj in self.district_list:
      district_obj.current_requested = 0.0
    for waterbank_obj in self.waterbank_list:
      waterbank_obj.current_requested = 0.0
    self.sanluisfederal.flood_flow_min = self.find_flood_trigger(self.calaqueduct, self.sanluis.key, self.calaqueduct.name, 'normal', 'recharge')
    #return the contract association on the california aqeuduct to all CVP & SWP delta contracts
    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]


  def find_flood_trigger(self, Canal canal, prev_canal, contract_canal, flow_dir,flow_type):
    #########################################################################################
    #this function loops through the canal nodes looking for recharge storage attached
	#to particular contracts.
    #########################################################################################
    cdef Canal canal_obj
    cdef Reservoir reservoir_obj
    cdef Contract contract_obj
    cdef District district_obj
    cdef Waterbank waterbank_obj

	#finds where on the canal to begin (if coming from another canal), and 
	#where to end (either the end or beginning of canal, depending on flow direction)
    # for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
    for starting_point in range(len(self.canal_district[canal.name])):
      if self.canal_district[canal.name][starting_point].key == prev_canal:#find canal intersections
        break
    if flow_dir == "normal":
      canal_size = self.canal_district_len[canal.name]
      canal_range = range((starting_point+1),canal_size)
    elif flow_dir == "reverse":
      canal_range = range((starting_point-1),0,-1)
    else:
      return (0.0)

    tot_contractor_demand = 0.0#initialize total demand on the canal
    for canal_loc in canal_range:#loop through the flow range on the canal (determined above)
      if self.canal_district[canal.name][canal_loc].is_District == 1:
        district_obj = self.canal_district[canal.name][canal_loc]
        new_loc_demand = 0.0
        contractor_toggle = 0
		#find if the node has a particular contract
        for contract_obj in self.canal_contract[contract_canal]:
          for contract_key in district_obj.contract_list:
            if contract_obj.name == contract_key:
              contractor_toggle = 1
        #calculate teh maximium recharge storage
        if contractor_toggle == 1:
          new_loc_demand = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd, max(district_obj.in_district_storage - district_obj.current_requested, 0.0))
          tot_contractor_demand += new_loc_demand
          district_obj.current_requested += new_loc_demand
		
      elif self.canal_district[canal.name][canal_loc].is_Waterbank == 1:
        waterbank_obj = self.canal_district[canal.name][canal_loc]
        new_loc_demand = 0.0
        #at a waterbank, find if the bank member has a contract
        for district_key in waterbank_obj.participant_list:
          contractor_toggle = 0
          for wb_member in self.district_keys[district_key]:
            for contract_obj in self.canal_contract[contract_canal]:
              for contract_key in wb_member.contract_list:
                if contract_obj.name == contract_key:
                  contractor_toggle = 1
                  break
              if contractor_toggle == 1:
                break
            if contractor_toggle == 1:
              break
          if contractor_toggle == 1:
            new_loc_demand += max(waterbank_obj.tot_storage*waterbank_obj.ownership[district_key],0.0)#only account for member-owned storage
        new_loc_demand -= waterbank_obj.current_requested
        #make sure storage doesn't exceed the turnout capacity
        if new_loc_demand > canal.turnout[flow_dir][canal_loc]*cfs_tafd:
          new_loc_demand = canal.turnout[flow_dir][canal_loc]*cfs_tafd	  
        waterbank_obj.current_requested += new_loc_demand
        tot_contractor_demand += new_loc_demand

      #if a node is a canal node, jump to that canal (function calls itself, but for another canal) 
      elif self.canal_district[canal.name][canal_loc].is_Canal == 1:
        canal_obj = self.canal_district[canal.name][canal_loc]
        new_loc_demand = 0.0
        if canal.turnout[flow_dir][canal_loc] > 0.0:
          new_flow_dir = canal.flow_directions[flow_type][canal_obj.name]
          new_loc_demand = self.find_flood_trigger(canal_obj, canal.key, contract_canal, new_flow_dir,flow_type)
          if new_loc_demand > canal.turnout[flow_dir][canal_loc]*cfs_tafd:
            new_loc_demand = canal.turnout[flow_dir][canal_loc]*cfs_tafd
          tot_contractor_demand += new_loc_demand
	#return total demand on the canal
    return tot_contractor_demand
	
	
  def find_initial_carryover(self):
    #########################################################################################
	#takes the storage that exists at the start of the simulation and applies it either to 
	#carryover storage or to the next year's (first year of simulation) allocation
    #########################################################################################
    cdef Contract contract_obj, contract_obj2
    cdef District district_obj
    cdef Reservoir reservoir_obj

    tot_state = self.sanluisstate.S[0]
    tot_federal = self.sanluisfederal.S[0]
    total_alloc_state = self.swpdelta.total
    total_alloc_federal = self.cvpdelta.total + self.cvpexchange.total
    for contract_obj in self.contract_list:
      reservoir_obj = self.contract_reservoir[contract_obj.key]
      #then find all the contracts associated with that reservoir
      this_reservoir_all_contract = self.reservoir_contract[reservoir_obj.key]
      #need to find the total deliveries already made from the reservoir,
	  #total carryover storage at the reservoir, and the total priority/secondary allocations
	  #at that reservoir
      priority_allocation = 0.0
      secondary_allocation = 0.0
      for contract_obj2 in this_reservoir_all_contract:
        if contract_obj2.allocation_priority == 1:
          priority_allocation += contract_obj2.total
        else:
          secondary_allocation += contract_obj2.total

      if contract_obj.allocation_priority == 1:
        if priority_allocation > 0.0:
          contract_obj.tot_new_alloc = (reservoir_obj.S[0] - reservoir_obj.dead_pool)*max(contract_obj.total/priority_allocation, 1.0)
        else:
          contract_obj.tot_new_alloc = 0.0
      else:
        if secondary_allocation > 0.0:
          contract_obj.tot_new_alloc = max(reservoir_obj.S[0] - reservoir_obj.dead_pool - priority_allocation, 0.0)*contract_obj.total/secondary_allocation
        else:
          contract_obj.tot_new_alloc = 0.0

      for district_obj in self.district_list:
        district_obj.carryover[contract_obj.name] = 0.0
		
		
  def allocate_private_contracts(self):
    cdef District district_obj
    cdef Private private_obj

    crop_life = 25
    for district_obj in self.district_list:
      district_obj.private_acreage = {}
      if district_obj.has_pesticide:
        district_obj.private_fraction = [0.0 for _ in range(self.number_years)]
        for crops in district_obj.acreage_by_year:
          district_obj.private_acreage[crops] = np.zeros(self.number_years)
      elif district_obj.has_pmp:
        for crops in district_obj.pmp_acreage:
          district_obj.private_acreage[crops] = 0.0
      else:
        district_obj.private_fraction = [0.0]
        for crops in district_obj.crop_list:
          district_obj.private_acreage[crops] = 0.0

    for private_obj in self.private_list:
      private_obj.acreage = {}
      private_obj.contract_fraction = {}
      private_obj.private_fraction = {}
      private_obj.contract_list = []
      private_obj.initial_planting = {}
      private_obj.has_pesticide = {}
      private_obj.has_pmp = {}
      for district_key in private_obj.district_list:
        district_land = self.district_keys[district_key]
        if district_land.has_pesticide:
          private_obj.has_pesticide[district_key] = 1
          private_obj.has_pmp[district_key] = 0
        else:
          private_obj.has_pesticide[district_key] = 0
          if district_land.has_pmp:
            private_obj.has_pmp[district_key] = 1
          else:
            private_obj.has_pmp[district_key] = 0
      for district_key in private_obj.district_list:
        private_obj.acreage[district_key] = {}
        private_obj.initial_planting[district_key] = {}
        for crops in private_obj.crop_list:
          if private_obj.has_pesticide[district_key]:
            private_obj.initial_planting[district_key][crops] = np.zeros(self.number_years)
          else:
            private_obj.initial_planting[district_key][crops] = 0.0
        for private_crop_types in private_obj.crop_list:
          private_obj.acreage[district_key][private_crop_types] = np.zeros(crop_life)
		  
        district_land = self.district_keys[district_key]
        for contract_key in district_land.contract_list:
          if contract_key not in private_obj.contract_list:
            private_obj.contract_list.append(contract_key)
			
        if district_land.has_pesticide:
          private_obj.private_fraction[district_key] = np.zeros(self.number_years)
          total_acres = np.zeros(self.number_years)
          private_acres = np.zeros(self.number_years)
        else:
          private_obj.private_fraction[district_key] = np.zeros(self.number_years)
          total_acres = 0.0
          private_acres = 0.0
        if district_land.has_pesticide:
          for crops in district_land.acreage_by_year:
            for private_crops in private_obj.crop_list:
              if private_crops == crops:
                for future_year in range(0, self.number_years):
                  private_acres[future_year] += private_obj.contract_fractions[district_key]*district_land.acreage_by_year[crops][future_year]
                  district_land.private_acreage[private_crops][future_year] += private_obj.contract_fractions[district_key]*district_land.acreage_by_year[crops][future_year]
                  if future_year == 0:
                    private_obj.initial_planting[district_key][private_crops][future_year] = private_obj.contract_fractions[district_key]*district_land.acreage_by_year[crops][future_year]/float(crop_life)
                  else:
                    #private_obj.initial_planting[district_key][private_crops][future_year] = private_obj.initial_planting[district_key][private_crops][future_year-1] + max(private_obj.contract_fractions[district_key]*(district_land.acreage_by_year[crops][future_year] - district_land.acreage_by_year[crops][future_year-1]),0.0)
                    private_obj.initial_planting[district_key][private_crops][future_year] = private_obj.contract_fractions[district_key]*district_land.acreage_by_year[crops][future_year]/float(crop_life)

					
                for crop_year in range(0,crop_life):
                  if private_obj.has_pesticide[district_key]:
                    private_obj.acreage[district_key][private_crops][crop_year] += private_obj.initial_planting[district_key][private_crops][0]
                  else:
                    private_obj.acreage[district_key][private_crops][crop_year] += private_obj.initial_planting[district_key][private_crops]
					
            if crops != 'idle':
              for future_year in range(0, self.number_years):
                total_acres[future_year] += district_land.acreage_by_year[crops][future_year]

        elif district_land.has_pmp:
          for crops in district_land.pmp_acreage:
            for private_crops in private_obj.crop_list:
              if private_crops == crops:
                private_acres += private_obj.contract_fractions[district_key]*district_land.pmp_acreage[crops]
                district_land.private_acreage[private_crops] += private_obj.contract_fractions[district_key]*district_land.pmp_acreage[crops]
                if private_obj.has_pesticide[district_key]:
                  for future_year in range(0, self.number_years):
                    private_obj.initial_planting[district_key][private_crops][future_year] = private_obj.contract_fractions[district_key]*district_land.pmp_acreage[crops]/float(crop_life)
                else:
                  private_obj.initial_planting[district_key][private_crops] = private_obj.contract_fractions[district_key]*district_land.pmp_acreage[crops]/float(crop_life)

                for crop_year in range(0,crop_life):
                  if private_obj.has_pesticide[district_key]:
                    private_obj.acreage[district_key][private_crops][crop_year] += private_obj.initial_planting[district_key][private_crops][0]
                  else:
                    private_obj.acreage[district_key][private_crops][crop_year] += private_obj.initial_planting[district_key][private_crops]

            if crops != 'idle':
              total_acres += district_land.pmp_acreage[crops]

				
        else:
          for i,crops in enumerate(district_land.crop_list):
            for private_crops in private_obj.crop_list:
              if private_crops == crops:
                private_acres += private_obj.contract_fractions[district_key]*district_land.acreage['BN'][i]
                district_land.private_acreage[private_crops] += private_obj.contract_fractions[district_key]*district_land.acreage['BN'][i]
                if private_obj.has_pesticide[district_key]:
                  for future_year in range(0, self.number_years):
                    private_obj.initial_planting[district_key][private_crops][future_year] = private_obj.contract_fractions[district_key]*district_land.acreage['BN'][i]/float(crop_life)
                else:
                  private_obj.initial_planting[district_key][private_crops] = private_obj.contract_fractions[district_key]*district_land.acreage['BN'][i]/float(crop_life)

                for crop_year in range(0,crop_life):
                  if private_obj.has_pesticide[district_key]:
                    private_obj.acreage[district_key][private_crops][crop_year] += private_obj.initial_planting[district_key][private_crops][0]
                  else:
                    private_obj.acreage[district_key][private_crops][crop_year] += private_obj.initial_planting[district_key][private_crops]
				
                
            if crops != 'idle':
              total_acres += district_land.acreage['BN'][i]

        if district_land.has_pesticide:
          for future_year in range(0, self.number_years):
            private_obj.private_fraction[district_key][future_year] += private_acres[future_year]/total_acres[future_year]
            district_land.private_fraction[future_year] += private_acres[future_year]/total_acres[future_year]
            #if district_land.private_fraction[future_year] > 1.0:
              #print("You have overallocated private lands in " + district_land.key)
        else:
          for future_year in range(0, self.number_years):
            private_obj.private_fraction[district_key][future_year] += private_acres/total_acres

          district_land.private_fraction[0] += private_acres/total_acres
          #if district_land.private_fraction > 1.0:
            #print("You have overallocated private lands in " + district_land.key)

    for private_obj in self.city_list:
      private_obj.contract_fraction = {}
      private_obj.private_fraction = {}
      private_obj.contract_list = []
      for pump_keys in private_obj.district_list:
        pump = self.district_keys[pump_keys]
        private_obj.private_fraction[pump_keys] = np.zeros(self.number_years)
        for future_years in range(0, self.number_years):
          private_obj.private_fraction[pump_keys][future_years] = private_obj.pump_out_fraction[pump_keys]
        pump.private_fraction[0] += private_obj.pump_out_fraction[pump_keys]
        for contract_key in pump.contract_list:
          if contract_key not in private_obj.contract_list:
            private_obj.contract_list.append(contract_key)


  def determine_recharge_recovery_risk(self):
    cdef Contract contract_obj
    cdef Private private_obj
    cdef District district_obj

    contract_estimates = pd.read_csv('calfews_src/data/input/contract_risks.csv')
    delivery_values = {}
    for contract_obj in self.contract_list:
      total_available = contract_estimates[contract_obj.key + '_contract'] + contract_estimates[contract_obj.key + '_flood'] + contract_estimates[contract_obj.key + '_carryover'] + contract_estimates[contract_obj.key + '_turnback']
      delivery_values[contract_obj.key] = total_available
    for private_obj in self.private_list:
      private_obj.target_annual_demand = [0. for _ in range(self.number_years)]
      for district_key in private_obj.district_list:
          district_obj = self.district_keys[district_key]
          for contracts in district_obj.contract_list:
            contract_obj = self.contract_keys[contracts]
            for future_year in range(0, self.number_years):
              private_obj.target_annual_demand[future_year] += np.mean(delivery_values[contract_obj.key])*district_obj.project_contract[contract_obj.name]*private_obj.private_fraction[district_key][future_year]

      private_obj.delivery_risk = [0.0 for _ in range(len(total_available))]
      private_obj.delivery_risk_rate = [0.0 for _ in range(len(total_available))]
      cumulative_balance = 0.0
      cumulative_years = 0.0
      total_delivery_record = np.zeros(len(total_available))
      for hist_year in range(0, len(total_available)):
        private_deliveries = 0.0
        for district_key in private_obj.district_list:
          district_obj = self.district_keys[district_key]
          for contract_key in district_obj.contract_list:
            contract_obj = self.contract_keys[contract_key]
            if contract_obj.type == 'contract':
              private_deliveries += delivery_values[contract_obj.key][hist_year]*district_obj.project_contract[contract_obj.name]*private_obj.private_fraction[district_key][0]
            else:
              private_deliveries += delivery_values[contract_obj.key][hist_year]*district_obj.rights[contract_obj.name]['capacity']*private_obj.private_fraction[district_key][0]

        total_delivery_record[hist_year] = private_deliveries
        annual_balance = private_deliveries - private_obj.target_annual_demand[0]
        cumulative_balance += annual_balance
        cumulative_years += 1.0
        if cumulative_balance > 0.0:
          cumulative_balance = 0.0
          cumulative_years = 0.0
        private_obj.delivery_risk[hist_year] = cumulative_balance
        private_obj.delivery_risk_rate[hist_year] = cumulative_years
      # df = pd.DataFrame()
      # df['delivery_risk'] = pd.Series(x.delivery_risk)
      # df['deliveries'] = pd.Series(total_delivery_record)
      # df['average_demand'] = pd.Series(np.ones(len(x.delivery_risk))*x.target_annual_demand[0])
      # df.to_csv(self.results_folder + '/delivery_risk_' + x.key + '.csv')
		     		

  def init_tot_recovery(self):
    #########################################################################################
    ###this function finds the total GW recovery
    ###capacity available to all district objects
    #########################################################################################
    cdef Private private_obj
    cdef District district_obj, leiu_obj
    cdef Waterbank waterbank_obj

    for district_obj in self.district_list:
      district_obj.max_recovery = 0.0
    for private_obj in self.private_list:
      private_obj.max_recovery = 0.0
    for private_obj in self.city_list:
      private_obj.max_recovery = 0.0
    #each waterbank has a list of district participants -
	#they get credit for their ownership share of the total recovery capacity
    for waterbank_obj in self.waterbank_list:
      for district_key in waterbank_obj.participant_list:
        num_districts = self.district_keys_len[district_key]
        for irr_district in self.district_keys[district_key]:
          irr_district.max_recovery += waterbank_obj.ownership[district_key]*waterbank_obj.recovery/num_districts
    #same for 'in leiu' banks (districts)
    for leiu_obj in self.leiu_list:
      for district_key in leiu_obj.participant_list:
        num_districts = self.district_keys_len[district_key]
        if district_key != leiu_obj.key:
          for irr_district in self.district_keys[district_key]:
            irr_district.max_recovery += leiu_obj.leiu_ownership[district_key]*leiu_obj.leiu_recovery/num_districts
      

  def load_pesticide_acreage(self):
    cdef District district_obj

    id_dict = {}
    id_dict['ALT'] = 'Alta Irrigation District'
    id_dict['ARV'] = 'Arvin - Edison Water Storage District'
    id_dict['BDM'] = 'Berrenda Mesa Water District'
    id_dict['BVA'] = 'Buena Vista Water Storage District'
    id_dict['CWO'] = 'Cawelo Water District'
    id_dict['CNS'] = 'Consolidated Irrigation District'
    id_dict['COR'] = 'Corcoran Irrigation District'
    id_dict['DLE'] = 'Delano - Earlimart Irrigation District'
    id_dict['DLR'] = 'Dudley Ridge Water District'
    id_dict['FRB'] = 'Firebaugh Canal Company'
    id_dict['FRS'] = 'Fresno Irrigation District'
    id_dict['JMS'] = 'James Irrigation District'
    id_dict['KRT'] = 'Kern - Tulare Water District'
    id_dict['KND'] = 'Kern Delta Water District'
    id_dict['KRWD'] = 'Kings River Water District'
    id_dict['LND'] = 'Lindmore Irrigation District'
    id_dict['LHL'] = 'Lost Hills Water District'
    id_dict['LWT'] = 'Lower Tule River Irrigation District'
    id_dict['NKN'] = 'North Kern Water Storage District'
    id_dict['ORC'] = 'Orange Cove Irrigation District'
    id_dict['PNC'] = 'Panoche Water District'
    id_dict['PIX'] = 'Pixley Irrigation District'
    id_dict['RVD'] = 'Riverdale Irrigation District'
    id_dict['SMI'] = 'Semitropic Water Service District'
    id_dict['SFW'] = 'Shafter - Wasco Irrigation District'
    id_dict['TUL'] = 'Tulare Irrigation District'
    id_dict['TLB'] = 'Tulare Lake Basin Water Storage District'
    id_dict['WSL'] = 'Westlands Water District'
    id_dict['WRM'] = 'Wheeler Ridge - Maricopa Water Storage District'
    for district_obj in self.district_list:
      if district_obj.key in id_dict:
        district_obj.has_pesticide = 1
        district_obj.acreage_by_year = {}
        district_filename = id_dict[district_obj.key]
        pesticide_data = pd.read_csv('calfews_src/data/input/pesticide_acreage/' + district_filename + '.csv', index_col = 0)
        data_start_year = 0
        for crop_type in pesticide_data:
          district_obj.acreage_by_year[crop_type] = np.zeros(self.number_years)
          for y in range(0, self.number_years):
            district_obj.acreage_by_year[crop_type][y] = pesticide_data[crop_type][y+data_start_year]


  def load_pmp_model(self):
    cdef District district_obj

    color_list = ['black', 'gray', 'firebrick', 'red', 'darksalmon', 'sandybrown', 'gold', 'chartreuse', 'seagreen', 'deepskyblue', 'royalblue', 'darkorchid', 'darkcyan', 'crimson', 'fuchsia', 'cyan', 'green', 'yellowgreen', 'coral', 'orange', 'hotpink', 'thistle', 'azure', 'yellow', 'dimgray', 'turquoise', 'navy', 'mediumspringgreen']

    pmp_coef = {}
    pmp_coef_list = ['TAU', 'GAMMA', 'ETA', 'DELTA', 'BETA', 'LEONTIEF', 'INPUTS', 'REV']
    for x in pmp_coef_list:
      pmp_coef[x] = pd.read_csv('calfews_src/data/input/pmp_modelling/BASE' + x + '.csv', index_col = None)

    econ_data = {}
    econ_data_list = ['PRICE', 'WSOU', 'WCST', 'LANDCOST', 'LABOR', 'SUPPL']
    for x in econ_data_list:
      econ_data[x] = pd.read_excel('calfews_src/data/input/pmp_modelling/Aligned_OAE_Kern_V05.xlsx', sheet_name = x, index_col = None) 
    
    self.district_codes = {}
    self.district_codes['D02'] = 'KND'
    self.district_codes['D03'] = 'WRM'
    self.district_codes['D04'] = 'WKN'
    self.district_codes['D05'] = 'BDM'
    self.district_codes['D06'] = 'SMI'
    self.district_codes['D07'] = 'RRB'
    self.district_codes['D08'] = 'BVA'
    self.district_codes['D09'] = 'CWO'
    self.district_codes['D10'] = 'HML'
    self.district_codes['D11'] = 'LHL'
    self.district_codes['fk01'] = 'DLE'
    self.district_codes['fk02'] = 'EXE'
    self.district_codes['fk03'] = 'KRT'
    self.district_codes['fk04'] = 'LND'
    self.district_codes['fk05'] = 'LDS'
    self.district_codes['fk06'] = 'LWT'
    self.district_codes['fk07'] = 'PRT'
    self.district_codes['fk08'] = 'SAU'
    self.district_codes['fk09'] = 'SFW'
    self.district_codes['fk10'] = 'SSJ'
    self.district_codes['fk11'] = 'TPD'
    self.district_codes['fk12'] = 'TBA'
    self.district_codes['fk13'] = 'TLR'
    self.district_codes['fk14'] = 'VAN'
    self.district_codes['ot1'] = 'DLR'
    self.district_codes['ot2'] = 'NKN'
    self.district_codes['ot3'] = 'OLC'
	
    self.source_codes = {}
    self.source_codes['SWP'] = ['tableA',]
    self.source_codes['CVP'] = ['cvpdelta',]
    self.source_codes['CLASS1'] = ['friant1',]
    self.source_codes['CLASS2'] = ['friant2',]
    self.source_codes['LDIV'] = ['kern', 'kings', 'tule', 'kaweah']
    legend_dict = {}
    xx = 0
    for district in self.district_codes:
      district_id = self.district_codes[district]
      if district_id in self.district_keys:
        district_obj = self.district_keys[district_id]
        district_obj.has_pmp = 1
        district_obj.irrdemand.set_pmp_parameters(pmp_coef, district)
        district_obj.irrdemand.make_crop_list()
        district_obj.irrdemand.set_econ_parameters(econ_data, district)
        district_obj.total_water_base = 0.0
        land_constraint = 0.0
        for crop in district_obj.irrdemand.crop_list:
          district_obj.total_water_base += district_obj.irrdemand.baseline_inputs['WATER'][crop]##base case water inputs to validate pmp model - within timestep use self.source_codes to get contracts
          land_constraint += district_obj.irrdemand.baseline_inputs['LAND'][crop]
        water_constraint_by_source = {}
        for source in district_obj.irrdemand.water_source_list:
          water_constraint_by_source[source] = district_obj.irrdemand.econ_factors[source]*district_obj.total_water_base
		  
        x0 = np.zeros(len(district_obj.irrdemand.crop_list))
        district_obj.set_pmp_acreage(water_constraint_by_source, land_constraint, x0)		
        observed_acreage = {}
        for crop in district_obj.irrdemand.crop_list:
          district_crops = district_obj.irrdemand.crop_keys[crop]
          if district_crops in observed_acreage:
            observed_acreage[district_crops] += district_obj.irrdemand.baseline_inputs['LAND'][crop]
          else:
            observed_acreage[district_crops] = district_obj.irrdemand.baseline_inputs['LAND'][crop]
        i = 0
        calculated = np.zeros(len(observed_acreage))
        observed = np.zeros(len(observed_acreage))
        total_land = 0.0
        for crop in observed_acreage:
          calculated[i] = district_obj.pmp_acreage[crop]
          observed[i] = observed_acreage[crop]
          total_land += calculated[i]
          i += 1
		  
        #legend_dict[district] = plt.plot(calculated, observed, 'o', color = color_list[xx])
        xx += 1
    #legend_obj = tuple([legend_dict[e] for e in legend_dict])
    #legend_names = tuple([self.district_codes[e] for e in legend_dict])
    #plt.xlabel('Calculated Acreage')
    #plt.ylabel('Observed Acreage')
    #plt.legend(legend_names)
    #plt.show()
    #plt.close()

		  

  def project_urban(self, datafile, datafile_cvp, datafile_pumping):
    #########################################################################################
    ###initializes variables needed for district objects that are pumping plants on branches
	###of the california aqueduct (southern california, central coast, and the south bay)
    #########################################################################################
    cdef District district_obj
    cdef Private private_obj

    ##This function finds linear regression coefficients between urban CA AQ branch pumpning and delta pumping
	##to predict water use in southbay, centralcoast, and socal district objects
	##NOTE!!! More detailed MWD/Southern Cal demand data would improve the model
    df_urban = pd.read_csv(datafile, index_col=0, parse_dates=True)
    if self.model_mode == 'validation':      
      simulation_dates = pd.to_datetime(self.df[0].index)
      urban_dates = pd.to_datetime(df_urban.index)
      start_date = simulation_dates[0]
      end_date = simulation_dates[-1]
      date_mask = (urban_dates >= start_date) & (urban_dates <= end_date)
      df_urban = df_urban[date_mask]

    df_urban_monthly_cvp = pd.read_csv(datafile_cvp, index_col=0, parse_dates=True)
    df_pumping_prediction_control = pd.read_csv(datafile_pumping, index_col=0, parse_dates=True)
    index_urban = df_urban.index
    urban_historical_T = len(df_urban)
    index_urban_d = index_urban.dayofyear
    index_urban_m = index_urban.month
    index_urban_y = index_urban.year
    index_urban_dowy = water_day(index_urban_d, index_urban_y)
    urban_startYear = index_urban_y[0]
    urban_start_regression_year = 2003
    urban_start_regression = int(urban_start_regression_year - urban_startYear - 1)
    index_urban_water_year = water_year(index_urban_m, index_urban_y, urban_startYear)
    numYears_urban = index_urban_y[urban_historical_T - 1] - index_urban_y[0]
    urban_list = [self.socal, self.centralcoast, self.southbay]
    self.observed_hro = (df_urban['HRO_pump'].values *cfs_tafd).tolist()
    self.observed_trp = (df_urban['TRP_pump'].values *cfs_tafd).tolist()
    self.observed_hro_pred = df_pumping_prediction_control['DEL_SWP_allocation'].tolist()
    SRI_forecast = df_urban['DEL_SCINDEX'].values
    regression_annual_hro = [0.0 for _ in range(numYears_urban)]
    regression_annual_trp = [0.0 for _ in range(numYears_urban)]
    regression_percent = {}
    for district_obj in urban_list:
      regression_percent[district_obj] = np.zeros((365,numYears_urban))
      district_obj.delivery_percent_coefficient = {}
      district_obj.delivery_percent_coefficient[0] = np.zeros((365,4))
    for private_obj in self.city_list:
      private_obj.delivery_percent_coefficient = {}
      regression_percent[private_obj] = {}
      for district_key in private_obj.district_list:
        private_obj.delivery_percent_coefficient[district_key] = np.zeros((365,4))
        regression_percent[private_obj][district_key] = np.zeros((365,numYears_urban))
    
#     sim_y = self.year
#     sim_m = self.month
#     sim_d = self.day_month
#     start_counter = 0
#     sri_regression = np.zeros(numYears_urban - urban_start_regression)
#     for simt in range(0, self.T):
#       if sim_y[simt] == urban_start_regression_year:
#         start_counter = 1
#       if start_counter == 1 and sim_m[simt] == 9 and sim_d[simt] == 1:
#         sri_regression[sim_y[simt] - urban_start_regression_year] = self.forecastSRI[simt]
    urban_leap = leap(np.arange(min(index_urban_y), max(index_urban_y) + 2))
    urban_year_list = np.arange(min(index_urban_y), max(index_urban_y) + 2)
    urban_days_in_month = days_in_month(urban_year_list, urban_leap)

    hist_pumping = {}
    regression_annual = {}
    for district_obj in urban_list:
      hist_pumping[district_obj] = [float(_) for _ in df_urban[district_obj.key+ '_pump'].values]
      regression_annual[district_obj] = [0.0 for _ in range(numYears_urban)]

    for xx in range(0, len(hist_pumping[self.southbay])):
      m = index_urban_m[xx]
      wateryear = index_urban_water_year[xx]
      year_index = index_urban_y[xx]-urban_startYear
      hist_pumping[self.southbay][xx] += df_urban_monthly_cvp['PCH_pump'][m-1 + wateryear*12]*1000.0/urban_days_in_month[year_index][m-1]

    for t in range(0,urban_historical_T):
      wateryear = index_urban_water_year[t]
	  
	  ##Find annual pumping at each branch (and @ delta)
      regression_annual_hro[wateryear] += self.observed_hro[t]
      regression_annual_trp[wateryear] += self.observed_trp[t]
      for district_obj in urban_list:
        regression_annual[district_obj][wateryear] += hist_pumping[district_obj][t]/1000.0
		
    for district_obj in urban_list:
      district_obj.pumping = {}
      district_obj.pumping[0] = hist_pumping[district_obj]
      district_obj.annual_pumping = {}
      district_obj.annual_pumping[0] = regression_annual[district_obj]
      # for xx in range(0, len(hist_pumping[district_obj])):
      #   district_obj.pumping.append(hist_pumping[district_obj][xx] * 1.0)
      # for xx in range(0, len(regression_annual[district_obj])):
      #   district_obj.annual_pumping.append(regression_annual[district_obj][xx] * 1.0)

    metropolitan_demand = [584.0, 352.0, 681.0, 1252.0, 1075.5, 1408.8, 1592.0, 1865.7, 1431.1, 1501.6, 1646.8, 1077.5, 1020.2, 1123.1, 1335.7, 1065.6, 989.1, 476.8, 704.8, 1106.4]
    if self.model_mode == 'validation':      
      metropolitan_adjust = self.starting_year - 1996
    else:
      metropolitan_adjust = 0
		
    for private_obj in self.city_list:
      private_obj.pumping = {}
      private_obj.annual_pumping = {}
      for district_key in private_obj.district_list:
        if private_obj.key == "MET":
          private_obj.pumping[district_key] = np.zeros(urban_historical_T)
          private_obj.annual_pumping[district_key] = np.zeros(numYears_urban)
          recalc_pumping = np.zeros(numYears_urban)
          district_obj = self.district_keys[district_key]
          for year_counter in range(0, len(private_obj.annual_pumping[district_key])):
            if district_key == "SOC":
              private_obj.annual_pumping[district_key][year_counter] = metropolitan_demand[year_counter + metropolitan_adjust]
            else:
              private_obj.annual_pumping[district_key][year_counter] = 0.0
          if district_key == "SOC":
            for pumping_counter in range(0, len(private_obj.pumping[district_key])):
              wateryear = index_urban_water_year[pumping_counter]
              real_ratio = private_obj.annual_pumping[district_key][wateryear]/(district_obj.annual_pumping[0][wateryear]*private_obj.pump_out_fraction[district_key])
              private_obj.pumping[district_key][pumping_counter] = district_obj.pumping[0][pumping_counter]*private_obj.pump_out_fraction[district_key]*real_ratio
              recalc_pumping[wateryear] += private_obj.pumping[district_key][pumping_counter]
          else:
            for pumping_counter in range(0, len(private_obj.pumping[district_key])):
              private_obj.pumping[district_key][pumping_counter] = district_obj.pumping[0][pumping_counter]*private_obj.pump_out_fraction[district_key]
        else:
          private_obj.pumping[district_key] = np.zeros(urban_historical_T)
          private_obj.annual_pumping[district_key] = np.zeros(numYears_urban)
          district_obj = self.district_keys[district_key]
          for pump_counter in range(0,len(private_obj.pumping[district_key])):
            private_obj.pumping[district_key][pump_counter] += district_obj.pumping[0][pump_counter]*private_obj.pump_out_fraction[district_key]
          for year_counter in range(0, len(private_obj.annual_pumping[district_key])):
            private_obj.annual_pumping[district_key][year_counter] +=  district_obj.annual_pumping[0][year_counter]*private_obj.pump_out_fraction[district_key]
			  
    for private_obj in self.city_list:
      for district_key in private_obj.district_list:
        recalc_pumping = np.zeros(numYears_urban)
        district_obj = self.district_keys[district_key]
        for pump_counter in range(0, len(private_obj.pumping[district_key])):
          wateryear = index_urban_water_year[pump_counter]
          district_obj.pumping[0][pump_counter] -= private_obj.pumping[district_key][pump_counter]
          if district_obj.pumping[0][pump_counter] < 0.0:
            private_obj.pumping[district_key][pump_counter] += district_obj.pumping[0][pump_counter]
            district_obj.pumping[0][pump_counter] = 0.0
          recalc_pumping[wateryear] += private_obj.pumping[district_key][pump_counter]
        for year_counter in range(0, len(private_obj.annual_pumping[district_key])):
          district_obj.annual_pumping[0][year_counter] -= private_obj.annual_pumping[district_key][year_counter]
          if district_obj.annual_pumping[0][year_counter] < 0.0:
            private_obj.annual_pumping[district_key][year_counter] += district_obj.annual_pumping[0][year_counter]
            district_obj.annual_pumping[0][year_counter] = 0.0
		  
    for district_obj in urban_list:
      for t in range(0, urban_historical_T):
        wateryear = index_urban_water_year[t]
        dowy = index_urban_dowy[t]
        regression_percent[district_obj][dowy][wateryear] = district_obj.annual_pumping[0][wateryear]/self.observed_hro_pred[t]
		  
    for private_obj in self.city_list:
      for district_key in private_obj.district_list:
        for t in range(0, urban_historical_T):
          wateryear = index_urban_water_year[t]
          dowy = index_urban_dowy[t]
          regression_percent[private_obj][district_key][dowy][wateryear] = private_obj.annual_pumping[district_key][wateryear]/self.observed_hro_pred[t]
          #regression_percent[private_obj][district_key][y] = private_obj.annual_pumping[district_key][y]	
		

    sri_forecast_dowy = np.zeros((365,numYears_urban))
    pumping_forecast_dowy = np.zeros((365, numYears_urban))
    pumping_forecast_timeseries = np.zeros(365 * numYears_urban)
    for t in range(0, urban_historical_T):
      wateryear = index_urban_water_year[t]
      dowy = index_urban_dowy[t]
      sri_forecast_dowy[dowy][wateryear] = SRI_forecast[t]
      pumping_forecast_dowy[dowy][wateryear] = self.observed_hro_pred[t]
      if wateryear >= urban_start_regression:
        pumping_forecast_timeseries[(wateryear - urban_start_regression)*365 + dowy] = pumping_forecast_dowy[dowy][wateryear] * 1.0

    regression_errors = {}
    regression_errors_timeseries = {}
    for district_obj in urban_list:
      counter1 = 1
      regression_errors[district_obj] = np.zeros((365,numYears_urban - urban_start_regression))
      regression_errors_timeseries[district_obj] = np.zeros(365*(numYears_urban-urban_start_regression))
      error_changes = np.zeros((365, numYears_urban-urban_start_regression))
      pumping_changes = np.zeros((365, numYears_urban-urban_start_regression))      

      for wateryear_day in range(0,365):
        #coef = np.polyfit(sri_forecast_dowy[wateryear_day][urban_start_regression:-1], regression_percent[district_obj][urban_start_regression:-1],1)
        coef = np.polyfit(pumping_forecast_dowy[wateryear_day][urban_start_regression:], regression_percent[district_obj][wateryear_day][urban_start_regression:],1)
        if self.use_sensitivity:
          district_obj.delivery_percent_coefficient[0][wateryear_day][0] = self.sensitivity_factors['urban_wet_year_demand_reduction']['realization']*coef[0]
        else:
          district_obj.delivery_percent_coefficient[0][wateryear_day][0] = coef[0]
        district_obj.delivery_percent_coefficient[0][wateryear_day][1] = coef[1]


        if district_obj.key == 'xxx':
          fig = plt.figure() 
          sri = np.zeros(numYears_urban)
          percent = np.zeros(numYears_urban)
          ax1 = fig.add_subplot(4,5,counter1)

          
          for yy in range(urban_start_regression,numYears_urban):
            sri[yy] = pumping_forecast_dowy[wateryear_day][yy]
            percent[yy] = regression_percent[district_obj][wateryear_day][yy]	
          ax1.scatter(sri[urban_start_regression:], percent[urban_start_regression:], s=50, c='red', edgecolor='none', alpha=0.7)
          ax1.plot([np.max(sri), 0.0], [(np.max(sri)*coef[0] + coef[1]), coef[1]],c='red')
          ax1.set_xlim([np.min(sri), np.max(sri)])
          counter1 += 1
          if counter1 == 21:
            plt.show()
            plt.close()
            fig = plt.figure()
            counter1 = 1


        for wateryear_count in range(urban_start_regression,numYears_urban):
          regression_errors[district_obj][wateryear_day][wateryear_count - urban_start_regression] = pumping_forecast_dowy[wateryear_day][wateryear_count]*district_obj.delivery_percent_coefficient[0][wateryear_day][0] + district_obj.delivery_percent_coefficient[0][wateryear_day][1] - regression_percent[district_obj][wateryear_day][wateryear_count]

          regression_errors_timeseries[district_obj][(wateryear_count - urban_start_regression)*365 + wateryear_day] = pumping_forecast_dowy[wateryear_day][wateryear_count]*district_obj.delivery_percent_coefficient[0][wateryear_day][0] + district_obj.delivery_percent_coefficient[0][wateryear_day][1] - regression_percent[district_obj][wateryear_day][wateryear_count]

      for wateryear_count in range(urban_start_regression,numYears_urban):
        for wateryear_day in range(0, 365):
          if (wateryear_count - urban_start_regression)*365 + wateryear_day > 0:
            error_changes[wateryear_day][wateryear_count - urban_start_regression] = regression_errors_timeseries[district_obj][(wateryear_count - urban_start_regression)*365 + wateryear_day]*min(wateryear_day/240.0, 1.0) - regression_errors_timeseries[district_obj][(wateryear_count - urban_start_regression)*365 + wateryear_day - 1]*min((wateryear_day-1.0)/240.0, 1.0)
            pumping_changes[wateryear_day][wateryear_count - urban_start_regression] = pumping_forecast_timeseries[(wateryear_count - urban_start_regression)*365 + wateryear_day] - pumping_forecast_timeseries[(wateryear_count - urban_start_regression)*365 + wateryear_day - 1]


      pumping_forecast_min = -500.0
      pumping_forecast_max = 500.0
      counter1 = 1
      district_obj.demand_auto_errors = {}
      district_obj.demand_auto_errors[0] = np.zeros((365, numYears_urban - urban_start_regression))
      for wateryear_day in range(0, 365):
        day_error_changes = error_changes[wateryear_day]
        day_pumping_changes = pumping_changes[wateryear_day]
        np_list_1_logi = np.logical_and(day_pumping_changes > pumping_forecast_min, day_pumping_changes < pumping_forecast_max)
        day_error_cleaned = day_error_changes[np_list_1_logi]
        day_pumping_cleaned = day_pumping_changes[np_list_1_logi]
        coef = np.polyfit(day_pumping_cleaned, day_error_cleaned, 1)
        district_obj.delivery_percent_coefficient[0][wateryear_day][2] = coef[0]
        district_obj.delivery_percent_coefficient[0][wateryear_day][3] = coef[1]
        for y in range(urban_start_regression, numYears_urban):
          district_obj.demand_auto_errors[0][wateryear_day][y-urban_start_regression] = pumping_changes[wateryear_day][y - urban_start_regression] * district_obj.delivery_percent_coefficient[0][wateryear_day][2] + district_obj.delivery_percent_coefficient[0][wateryear_day][3] - error_changes[wateryear_day][y - urban_start_regression]
        
        if district_obj.key == 'XXX':
          fig = plt.figure()
          ax1 = fig.add_subplot(4,5,counter1)
          ax1.scatter(day_pumping_changes, day_error_changes, s=50, c='red', edgecolor='none', alpha=0.7)
          ax1.plot([np.max(day_pumping_changes), np.min(day_pumping_changes)], [(np.max(day_pumping_changes)*coef[0] + coef[1]), np.min(day_pumping_changes)*coef[0] + coef[1]],c='red')
          ax1.set_xlim([np.min(day_pumping_changes), np.max(day_pumping_changes)])
          ax1.set_title(wateryear_day)
          counter1 += 1
          if counter1 == 21:
            plt.show()
            plt.close()
            fig = plt.figure() 
            counter1 = 1


    for private_obj in self.city_list:
      regression_errors[private_obj] = {}
      regression_errors_timeseries[private_obj] = {}
      private_obj.demand_auto_errors = {}
      for district_key in private_obj.district_list:
        regression_errors[private_obj][district_key] = np.zeros((365,numYears_urban-urban_start_regression))
        regression_errors_timeseries[private_obj][district_key] = np.zeros(365*(numYears_urban-urban_start_regression))
        
        error_changes = np.zeros((365, numYears_urban-urban_start_regression))
        pumping_changes = np.zeros((365, numYears_urban-urban_start_regression))      

        counter1 = 1
        #fig = plt.figure() 
        for wateryear_day in range(0,365):

          #coef = np.polyfit(sri_forecast_dowy[wateryear_day][urban_start_regression:-1], regression_percent[private_obj][district_key][urban_start_regression:-1],1)
          coef = np.polyfit(pumping_forecast_dowy[wateryear_day][urban_start_regression:], regression_percent[private_obj][district_key][wateryear_day][urban_start_regression:],1)
          if self.use_sensitivity:
            private_obj.delivery_percent_coefficient[district_key][wateryear_day][0] = self.sensitivity_factors['urban_wet_year_demand_reduction']['realization']*coef[0]
          else:
            private_obj.delivery_percent_coefficient[district_key][wateryear_day][0] = coef[0]
		  
          private_obj.delivery_percent_coefficient[district_key][wateryear_day][1] = coef[1]
          for wateryear_count in range(urban_start_regression,numYears_urban):
            regression_errors[private_obj][district_key][wateryear_day][wateryear_count-urban_start_regression] = pumping_forecast_dowy[wateryear_day][wateryear_count]*private_obj.delivery_percent_coefficient[district_key][wateryear_day][0] + private_obj.delivery_percent_coefficient[district_key][wateryear_day][1] - regression_percent[private_obj][district_key][wateryear_day][wateryear_count]
            regression_errors_timeseries[private_obj][district_key][(wateryear_count - urban_start_regression)*365 + wateryear_day] = pumping_forecast_dowy[wateryear_day][wateryear_count]*private_obj.delivery_percent_coefficient[district_key][wateryear_day][0] + private_obj.delivery_percent_coefficient[district_key][wateryear_day][1] - regression_percent[private_obj][district_key][wateryear_day][wateryear_count]

        for wateryear_count in range(urban_start_regression,numYears_urban):
          for wateryear_day in range(0, 365):
            if (wateryear_count - urban_start_regression)*365 + wateryear_day > 0:
              error_changes[wateryear_day][wateryear_count - urban_start_regression] = regression_errors_timeseries[private_obj][district_key][(wateryear_count - urban_start_regression)*365 + wateryear_day]*min(wateryear_day/240.0, 1.0) - regression_errors_timeseries[private_obj][district_key][(wateryear_count - urban_start_regression)*365 + wateryear_day - 1]*min((wateryear_day-1.0)/240.0, 1.0)
              pumping_changes[wateryear_day][wateryear_count - urban_start_regression] = pumping_forecast_timeseries[(wateryear_count - urban_start_regression)*365 + wateryear_day] - pumping_forecast_timeseries[(wateryear_count - urban_start_regression)*365 + wateryear_day - 1]

        private_obj.demand_auto_errors[district_key] = np.zeros((365,numYears_urban-urban_start_regression))
        pumping_forecast_min = -500.0
        pumping_forecast_max = 500.0
        counter1 = 1
        for wateryear_day in range(0, 365):
          day_error_changes = error_changes[wateryear_day]
          day_pumping_changes = pumping_changes[wateryear_day]
          np_list_1_logi = np.logical_and(day_pumping_changes > pumping_forecast_min, day_pumping_changes < pumping_forecast_max)
          day_error_cleaned = day_error_changes[np_list_1_logi]
          day_pumping_cleaned = day_pumping_changes[np_list_1_logi]
          coef = np.polyfit(day_pumping_cleaned, day_error_cleaned, 1)
          private_obj.delivery_percent_coefficient[district_key][wateryear_day][2] = coef[0]
          private_obj.delivery_percent_coefficient[district_key][wateryear_day][3] = coef[1]
          for y in range(urban_start_regression, numYears_urban):
            private_obj.demand_auto_errors[district_key][wateryear_day][y-urban_start_regression] = pumping_changes[wateryear_day][y - urban_start_regression] * private_obj.delivery_percent_coefficient[district_key][wateryear_day][2] + private_obj.delivery_percent_coefficient[district_key][wateryear_day][3] - error_changes[wateryear_day][y - urban_start_regression]

          if private_obj.key == 'XXX':
            fig = plt.figure()
            ax1 = fig.add_subplot(4,5,counter1)
            ax1.scatter(day_pumping_changes, day_error_changes, s=50, c='red', edgecolor='none', alpha=0.7)
            ax1.plot([np.max(day_pumping_changes), np.min(day_pumping_changes)], [(np.max(day_pumping_changes)*coef[0] + coef[1]), np.min(day_pumping_changes)*coef[0] + coef[1]],c='red')
            ax1.set_xlim([np.min(day_pumping_changes), np.max(day_pumping_changes)])
            ax1.set_title(wateryear_day)
            counter1 += 1
            if counter1 == 21:
              plt.show()
              plt.close()
              fig = plt.figure() 
              counter1 = 1

		
    for private_obj in self.city_list:
      for district_key in private_obj.district_list:
        counter1 = 1
        for wateryear_day in range(0,365):
          coef = np.polyfit(pumping_forecast_dowy[wateryear_day][urban_start_regression:], regression_percent[private_obj][district_key][wateryear_day][urban_start_regression:],1)
          if private_obj.key == "XXX":
            fig = plt.figure() 
            r = np.corrcoef(pumping_forecast_dowy[wateryear_day][urban_start_regression:], regression_percent[private_obj][district_key][wateryear_day][urban_start_regression:])[0,1]
            sri = np.zeros(numYears_urban)
            percent = np.zeros(numYears_urban)
            ax1 = fig.add_subplot(4,5,counter1)
          
            for yy in range(urban_start_regression,numYears_urban):
              sri[yy] = pumping_forecast_dowy[wateryear_day][yy]
              percent[yy] = regression_percent[private_obj][district_key][wateryear_day][yy]	
            ax1.scatter(sri, percent, s=50, c='red', edgecolor='none', alpha=0.7)
            ax1.plot([np.max(sri), 0.0], [(np.max(sri)*coef[0] + coef[1]), coef[1]],c='red')
            ax1.set_xlim([np.min(sri), np.max(sri)])
            counter1 += 1
            if counter1 == 21:
              plt.show()
              plt.close()
              fig = plt.figure() 
              counter1 = 1
        #plt.show()
        #plt.close()
        
          
    if self.model_mode == 'simulation' or self.model_mode == 'climate_ensemble' or self.model_mode == 'sensitivity':
      ytd_pumping_int = {}
      for district_obj in urban_list:
        district_obj.hist_demand_dict = {}
        ytd_pumping_int[district_obj] = np.zeros(numYears_urban)
        district_obj.hist_demand_dict['annual_sorted'] = {}
        district_obj.hist_demand_dict['sorted_index'] = {}
        for wateryear_day in range(0, 365):
          district_obj.hist_demand_dict['annual_sorted'][wateryear_day] = np.sort(regression_annual_hro[urban_start_regression:-1])
          district_obj.hist_demand_dict['sorted_index'][wateryear_day] = np.argsort(regression_annual_hro[urban_start_regression:-1])
        district_obj.hist_demand_dict['daily_fractions'] = np.zeros((len(regression_annual[district_obj]) - urban_start_regression,366))
      for private_obj in self.city_list:
        private_obj.hist_demand_dict = {}
        ytd_pumping_int[private_obj] = {}
        for district_key in private_obj.district_list:
          private_obj.hist_demand_dict[district_key] = {}	
          ytd_pumping_int[private_obj][district_key] = np.zeros(numYears_urban)
          private_obj.hist_demand_dict[district_key]['annual_sorted'] = {}
          private_obj.hist_demand_dict[district_key]['sorted_index'] = {}
          for wateryear_day in range(0, 365):
            private_obj.hist_demand_dict[district_key]['annual_sorted'][wateryear_day] = np.sort(regression_annual_hro[urban_start_regression:-1])
            private_obj.hist_demand_dict[district_key]['sorted_index'][wateryear_day] = np.argsort(regression_annual_hro[urban_start_regression:-1])
          private_obj.hist_demand_dict[district_key]['daily_fractions'] = np.zeros((numYears_urban - urban_start_regression,366))
        
      for t in range(0,urban_historical_T):
        dowy = index_urban_dowy[t]
        wateryear = index_urban_water_year[t]
        if wateryear >= urban_start_regression:
          for district_obj in urban_list:
            predicted_annual_demand = 1000.0 * self.observed_hro_pred[t] * ((self.observed_hro_pred[t] * district_obj.delivery_percent_coefficient[0][dowy][0] + district_obj.delivery_percent_coefficient[0][dowy][1])*max(240.0 - dowy, 0.0)/240.0 + regression_percent[district_obj][dowy][wateryear]*min(dowy, 240.0)/240.0)
            if predicted_annual_demand - ytd_pumping_int[district_obj][wateryear] > 0.0:
              district_obj.hist_demand_dict['daily_fractions'][wateryear - urban_start_regression][dowy] = (district_obj.pumping[0][t])/(predicted_annual_demand - ytd_pumping_int[district_obj][wateryear])
            else:
              district_obj.hist_demand_dict['daily_fractions'][wateryear - urban_start_regression][dowy] = 0.0/365.0
            ytd_pumping_int[district_obj][wateryear] += district_obj.pumping[0][t]

          for private_obj in self.city_list:
            for district_key in private_obj.district_list:
              predicted_annual_demand = 1000.0 * self.observed_hro_pred[t] * ((self.observed_hro_pred[t] * private_obj.delivery_percent_coefficient[district_key][dowy][0] + private_obj.delivery_percent_coefficient[district_key][dowy][1])*max(240.0 - dowy, 0.0)/240.0 + regression_percent[private_obj][district_key][dowy][wateryear]*min(dowy, 240.0)/240.0)
              if predicted_annual_demand - ytd_pumping_int[private_obj][district_key][wateryear] > 0.0:
                private_obj.hist_demand_dict[district_key]['daily_fractions'][wateryear - urban_start_regression][dowy] = (private_obj.pumping[district_key][t])/(predicted_annual_demand - ytd_pumping_int[private_obj][district_key][wateryear])
              else:
                private_obj.hist_demand_dict[district_key]['daily_fractions'][wateryear - urban_start_regression][dowy] = 0.0/365.0
              ytd_pumping_int[private_obj][district_key][wateryear] += private_obj.pumping[district_key][t]

      for private_obj in self.city_list:
        private_obj.annual_pumping = {}
        private_obj.pumping = {}
        for district_key in private_obj.district_list:
          private_obj.annual_pumping[district_key] = np.zeros(self.number_years)
          private_obj.pumping[district_key] = np.zeros(self.T)
      for district_obj in urban_list:
        district_obj.annual_pumping = {}
        district_obj.pumping = {}
        district_obj.annual_pumping[0] = np.zeros(self.number_years)
        district_obj.pumping[0] = np.zeros(self.T)

    for district_obj in urban_list:
      district_obj.ytd_pumping = {}
      district_obj.ytd_pumping[0] = np.zeros(self.number_years)
    for private_obj in self.city_list:
      private_obj.ytd_pumping = {}
      for district_key in private_obj.district_list:
        private_obj.ytd_pumping[district_key] = np.zeros(self.number_years)
	  
	###ACTUAL regression coefficients - picked to pass the 'eye test' 
    #self.southbay.urb_coef[0] = 0.01
    #self.centralcoast.urb_coef[0] = 0.0
    #self.socal.urb_coef[0] = 0.5
    #self.southbay.urb_coef[1] = 104.0
    #self.centralcoast.urb_coef[1] = 110.0
    #self.socal.urb_coef[1] = 200.0
	
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


#####################################################################################################################
#############################     Main simulation (North & South)     ###############################################
#####################################################################################################################


  def simulate_north(self,t,swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump):
	###Daily Operations###
	##Step forward environmental parameters (snow & flow)
    ##Set Delta operating rules
    ##Water Balance on each reservoir
    ##Decisions - release water for delta export, flood control
    cdef Reservoir reservoir_obj

    swp_release = 0#turn off any pumping over the E/I ratio 'tax'
    cvp_release = 0

    d = self.day_year[t]
    da = self.day_month[t]
    dowy = self.dowy[t]
    m = self.month[t]
    y = self.year[t]
    wateryear = self.water_year[t]
    year_index = y - self.starting_year

    ##WATER YEAR TYPE CLASSIFICATION (for operating rules)
    ##WYT uses flow forecasts - gets set every day, may want to decrease frequency (i.e. every month, season)
    NMI = self.calc_wytypes(t,dowy)#NMI (new melones index) - used as input for vernalis control rules
	  
	##REAL-WORLD RULE ADJUSTMENTS
	##Updates to reflect SJRR & Yuba Accalfews_srcs occuring during historical time period (1996-2016)
    if self.model_mode == 'validation':
      self.update_regulations_north(t,dowy, year_index + self.starting_year)
	  
	####NON-PROJECT USES
    ##Find out if reservoir releases need to be made for in-stream uses
    for reservoir_obj in self.reservoir_list:
      reservoir_obj.rights_call(reservoir_obj.downstream[t])
    ##any additional losses before the delta inflow (.downstream member only accounts to downstream trib gauge)
	##must be made up by releases from Shasta and New Melones, respectively
    #self.newmelones.rights_call(self.delta.gains_sj[t-1],1)

    ##FIND MINIMUM ENVIRONMENTAL RELEASES
    #San Joaquin Tributaries
    for reservoir_obj in [self.newmelones, self.donpedro, self.exchequer]:
      reservoir_obj.release_environmental(t, d, m, dowy, self.first_d_of_month[year_index], self.delta.forecastSJWYT)
	#Sacramento Tributaries
    self.oroville.set_oct_nov_rule(t, m)
    for reservoir_obj in [self.shasta, self.oroville, self.yuba, self.folsom]:
      reservoir_obj.release_environmental(t, d, m, dowy, self.first_d_of_month[year_index], self.delta.forecastSCWYT)
    ##MINIMUM FLOW AT VERNALIS GAUGE(SAN JOAQUIN DELTA INFLOW)
    #from self.reservoir.release_environmental() function:
	#self.reservoir.gains_to_delta
    #self.reservoir.envmin
    self.delta.vernalis_gains = self.newmelones.gains_to_delta + self.donpedro.gains_to_delta + self.exchequer.gains_to_delta + self.delta.gains_sj[t]
    self.delta.vernalis_gains += self.newmelones.envmin + self.donpedro.envmin + self.exchequer.envmin
    #find additional releases for vernalis control using self.delta.vernalis_gains
    self.exchequer.din, self.donpedro.din, self.newmelones.din  = self.delta.calc_vernalis_rule(t,d,y,m,dowy,NMI)
    self.delta.vernalis_gains += self.exchequer.din + self.donpedro.din + self.newmelones.din
	
	##MINIMUM FLOW AT RIO VIST GAUGE (SACRAMENTO DELTA INFLOW)
    for reservoir_obj in [self.shasta, self.oroville, self.yuba, self.folsom]:
      reservoir_obj.find_available_storage(t, m, da, dowy)  
    #additional releases to meet rio vista minimums shared by Sacramento Reservoirs
    cvp_stored_release = self.shasta.envmin + self.folsom.envmin
    swp_stored_release = self.oroville.envmin + self.yuba.envmin
    #unstored flow at rio vista comes from tributary gains, environmental releases and sacramento river gains
    self.delta.rio_gains = self.delta.gains_sac[t]
    for reservoir_obj in [self.shasta, self.oroville, self.yuba, self.folsom]:
      self.delta.rio_gains += reservoir_obj.gains_to_delta + reservoir_obj.envmin
    #share rio vista requirements among Sacramento Reservoirs based on self.resevoir.availale_storage
    self.shasta.din, self.oroville.din = self.delta.calc_rio_vista_rule(t, m, cvp_stored_release, swp_stored_release)

    ##MINIMUM DELTA OUTFLOW REQUIREMENTS
    #flows to delta come from vernalis, rio vista, and the 'eastside streams' (delta gains)
    self.delta.total_inflow = self.delta.eastside_streams[t] + self.delta.rio_gains + self.delta.vernalis_gains
    cvp_stored_release += self.shasta.din
    swp_stored_release += self.oroville.din
	##additional releases for delta outflow split between cvp/swp reservoirs
    self.shasta.dout, self.oroville.dout = self.delta.calc_outflow_release(t,m,dowy, cvp_stored_release, swp_stored_release)
  
	#TOTAL AVAILABLE PROJECT STORAGE
	#based on snowpack based forecast (pre-processed) + current storage
    cvp_available_storage = max(self.folsom.available_storage[t],0.0) + max(self.shasta.available_storage[t],0.0)
    swp_available_storage = max(self.oroville.available_storage[t],0.0) + max(self.yuba.available_storage[t],0.0)
    cvp_flood_storage = 0.0
    swp_flood_storage = 0.0
    #some 'saved' storage in oroville can be used to make non-taxed releases
    swp_extra = self.oroville.use_saved_storage(t, m, dowy, self.delta.forecastSCWYT)
    #project if flood pool will be exceeded in the future & find min release rate to avoid reaching the flood pool
	#monthly flow projections from self.reservoir.create_flow_shapes (i.e. flood available water)
    for reservoir_obj in [self.shasta, self.folsom, self.oroville, self.yuba]:
      reservoir_obj.find_flow_pumping(t, m, dowy, year_index, self.days_in_month, self.dowy_eom, self.delta.forecastSCWYT, 'env')
      reservoir_obj.days_til_full[t] = min(reservoir_obj.numdays_fillup['env'], reservoir_obj.numdays_fillup['lookahead'])
	  	  	
	###DETERMINE RELEASES REQUIRED FOR DESIRED PUMPING
    ###Uses gains and environmental releases to determine additional releases required for
	###pumping (if desired), given inflow/export requirements, pump constraints, and CVP/SWP sharing of unstored flows
	#at-the-pump limits (from BiOps)
    cvp_max, swp_max = self.delta.find_max_pumping(d, dowy, t, self.delta.forecastSCWYT)
    #OMR rule limits
    cvp_max, swp_max = self.delta.meet_OMR_requirement(t, m, y, dowy,cvp_max, swp_max)
	
    proj_surplus, max_pumping = self.proj_gains(t, dowy, m, year_index)
    flood_release = {}
    flood_volume = {}
	##Releases in anticipation of flood pool encroachment (not required by flood rules)
    flood_release['swp'] = self.oroville.min_daily_uncontrolled
    flood_release['cvp'] = self.shasta.min_daily_uncontrolled
    flood_volume['swp'] = self.oroville.uncontrolled_available
    flood_volume['cvp'] = self.shasta.uncontrolled_available
    swp_over_dead_pool = self.oroville.find_emergency_supply(t, m, dowy)
    cvp_over_dead_pool = 0.0
	##Distribute 'available storage' seasonally to maximize pumping under E/I ratio requirements (i.e., pump when E/I ratio is highest)
    cvp_max_final, swp_max_final = self.delta.find_release(t, m, y, year_index, dowy, self.days_in_month, self.dowy_eom, cvp_max, swp_max, cvp_available_storage, swp_available_storage, cvp_release, swp_release, proj_surplus, max_pumping)
    
    #if pumping is turned 'off' (b/c SL conditions), calculate how much forgone pumping to take away from SL carryover storage (southern model input)
    cvp_forgone = max(cvp_max - cvp_pump, 0.0)
    swp_forgone = max(swp_max - swp_pump, 0.0)
    #swp_forgone, swp_max_final = self.delta.hypothetical_pumping(t, m, swp_max, swp_max_final, swp_release2, 0.45)
    #find additional releases to pump at the desired levels
    cvp_max = min(cvp_max, cvp_pump)#don't release 'tax free' pumping in excess of storage capacity at SL
    swp_max = min(swp_max, swp_pump)#don't release 'tax free' pumping in excess of storage capacity at SL
    cvp_max_final = min(cvp_max_final, cvp_pump)
    swp_max_final = min(swp_max_final, swp_pump)
    #calculates releases to pump at desired levels (either cvp/swp_max or non-taxed levels, based on min outflow & i/e rules)
    swp_reduced, cvp_reduced = self.delta.calc_flow_bounds(t, m, y, year_index, d, dowy, self.dowy_eom, cvp_max_final, swp_max_final, cvp_max, swp_max, cvp_release2, swp_release2, cvp_available_storage, swp_available_storage, flood_release['cvp'], flood_release['swp'], swp_over_dead_pool, cvp_over_dead_pool, flood_volume['swp'], flood_volume['cvp'], min(self.oroville.numdays_fillup['env'],self.oroville.numdays_fillup['lookahead']), min(self.shasta.numdays_fillup['env'],self.shasta.numdays_fillup['lookahead']) )
    cvp_forgone = max(cvp_forgone, cvp_reduced)
    swp_forgone = max(cvp_forgone, cvp_reduced)

    #distribute releases for export between Sacramento River Reservoirs
    self.shasta.sodd, self.folsom.sodd = self.delta.distribute_export_releases(t, cvp_max, self.delta.sodd_cvp[t], self.shasta.flood_storage[t], self.folsom.flood_storage[t], self.shasta.available_storage[t], self.folsom.available_storage[t])
    self.oroville.sodd, self.yuba.sodd = self.delta.distribute_export_releases(t, swp_max, self.delta.sodd_swp[t], self.oroville.flood_storage[t], self.yuba.flood_storage[t], self.oroville.available_storage[t], self.yuba.available_storage[t])
    if self.shasta.sodd > self.shasta.S[t] - self.shasta.dead_pool:
      self.shasta.sodd = 0.0
    if self.oroville.sodd > self.oroville.S[t] - self.oroville.dead_pool:	  
      self.oroville.sodd = 0.0
	  
    ##Releases for export from reservoirs with flood control encroachment	  
    if self.shasta.sodd < self.shasta.min_daily_uncontrolled and self.folsom.sodd > self.folsom.min_daily_uncontrolled:
      release_switch = min(self.folsom.sodd - self.folsom.min_daily_uncontrolled, self.shasta.min_daily_uncontrolled - self.shasta.sodd)
      self.shasta.sodd += release_switch
      self.folsom.sodd -= release_switch
    elif self.shasta.sodd > self.shasta.min_daily_uncontrolled and self.folsom.sodd < self.folsom.min_daily_uncontrolled:
      release_switch = min(self.shasta.sodd - self.shasta.min_daily_uncontrolled, self.folsom.min_daily_uncontrolled - self.folsom.sodd)
      self.shasta.sodd -= release_switch
      self.folsom.sodd += release_switch

    if self.oroville.sodd < self.oroville.min_daily_uncontrolled and self.yuba.sodd > self.yuba.min_daily_uncontrolled:
      release_switch = min(self.yuba.sodd - self.yuba.min_daily_uncontrolled, self.oroville.min_daily_uncontrolled - self.oroville.sodd)
      self.oroville.sodd += release_switch
      self.yuba.sodd -= release_switch
    elif self.oroville.sodd > self.oroville.min_daily_uncontrolled and self.yuba.sodd < self.yuba.min_daily_uncontrolled:
      release_switch = min(self.oroville.sodd - self.oroville.min_daily_uncontrolled, self.yuba.min_daily_uncontrolled - self.yuba.sodd)
      self.yuba.sodd += release_switch
      self.oroville.sodd -= release_switch


	##SAN JOAQUIN RESERVOIR OPERATIONS
	##lower SJ basins - no 'release for exports' but used to meet delta targets @ vernalis
    ##Water Balance
    for reservoir_obj in [self.newmelones, self.donpedro, self.exchequer]:	
      reservoir_obj.step(t)
	  #forced spills also go to delta
      self.delta.total_inflow += reservoir_obj.force_spill


    #SACRAMENTO RESERVOIR OPERATIONS
	##Water balance at each Northern Reservoir
    self.shasta.rights_call(self.delta.ccc[t]*-1.0,1)
    self.oroville.rights_call(self.delta.barkerslough[t]*-1.0,1)
    for reservoir_obj in [self.shasta, self.oroville, self.yuba, self.folsom]:
      reservoir_obj.step(t)
	  #forced spills also go to delta
      self.delta.total_inflow += reservoir_obj.force_spill

	  
    ###DELTA OPERATIONS
	##Given delta inflows (from gains and reservoir releases), find pumping
    #cvp_stored_flow = self.shasta.R_to_delta[t] + self.folsom.R_to_delta[t]
    #swp_stored_flow = self.oroville.R_to_delta[t] + self.yuba.R_to_delta[t]
    cvp_stored_flow = self.shasta.sodd + self.folsom.sodd
    swp_stored_flow = self.oroville.sodd + self.yuba.sodd

    ##route all water through delta rules to determine pumping
    self.delta.step(t, d, da, m, y, wateryear, dowy, cvp_stored_flow, swp_stored_flow, swp_pump, cvp_pump, swp_available_storage, cvp_available_storage)

		    
    return self.delta.HRO_pump[t], self.delta.TRP_pump[t], self.delta.swp_allocation[t], self.delta.cvp_allocation[t], proj_surplus, max_pumping, swp_forgone, cvp_forgone, swp_flood_storage, cvp_flood_storage, swp_available_storage, cvp_available_storage, flood_release, flood_volume
			


  def simulate_south(self, int t, double hro_pump, double trp_pump, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgone, cvp_forgone, swp_AF, cvp_AF, swp_AS, cvp_AS, wyt, wytSC, max_tax_free, flood_release, flood_volume):
    cdef Canal canal_obj
    cdef Reservoir reservoir_obj
    cdef Contract contract_obj, contract_obj2
    cdef District district_obj, leiu_obj
    cdef Private private_obj
    cdef Waterbank waterbank_private
    cdef dict total_canal_demand
    cdef int d, da, dowy, m, y, wateryear, year_index, m1, use_contract

    ####Maintain the same date/time accounting as the northern part of the model
    d = self.day_year[t]
    da = self.day_month[t]
    dowy = self.dowy[t]
    m = self.month[t]
    y = self.year[t]
    wateryear = self.water_year[t]
    year_index = y - self.starting_year

    if m == 12:
      m1 = 1
    else:
      m1 = m + 1

    #####Pumping and project allocations (projections of future pumping) are passed 
	#####Into the southern model from the delta calcs in the northern model
    self.trp_pumping[t] = trp_pump
    self.hro_pumping[t] = hro_pump
    self.annual_SWP[wateryear] += hro_pump
    self.annual_CVP[wateryear] += trp_pump
    self.cvp_allocation[t] = cvp_alloc
    self.swp_allocation[t] = swp_alloc
	
	####Various infrastructure & regulatory changes that 
	####occurred during the duration of the 1996-2016 calibration period
    if self.model_mode == 'validation':
      self.update_regulations_south(t,dowy,m,year_index + self.starting_year, wateryear)
    else:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)
	  
    ####Calculate water balance/flow requirements at each 
	####local reservoir, in the same fashion as they are calculated for the 
	####Northern Reservoir
    watershed_reservoir_list = [self.millerton, self.success, self.kaweah, self.isabella, self.pineflat]
    for reservoir_obj in watershed_reservoir_list:
      reservoir_obj.rights_call(reservoir_obj.downstream[t])
      reservoir_obj.release_environmental(t, d, m, dowy, self.first_d_of_month[year_index], wyt)

	###Flow projections for the local reservoirs
	###Note: no flow projection for the San Luis Reservoir,
	###because it has no watershed affects.  Projections of pumping
	###are calculated in the northern function, and passed here as 
	###'projected allocations'
    for reservoir_obj in watershed_reservoir_list:
      reservoir_obj.find_available_storage(t, m, da, dowy)
	  
    ##Water Balance step at each reservoir
    for reservoir_obj in watershed_reservoir_list:
      reservoir_obj.step(t)
    
    ##Water balance/capacity sharing at San Luis Reservoir - capacity
	##Sharing means that both the state/federal portions can exceed 50% of the
	##total storage in San Luis, but any extra storage must be evacuated if pumping
	##from the other project begins to encroach on this space (i.e. temporary storage in the
	##other projects capacity)
    if t < (self.T - 1):
      extra_s, extra_f = self.step_san_luis(t, m, da)
    else:
      extra_s = 0.0
      extra_f = 0.0
  	
	###If pumping would occur from the northern model, but cannot because San Luis
	###Reservoir is full (and unable to be emptied), the projects 'take back' any 
	###carryover water and pretend that it was pumped, adding the carryover to the projections for 
	###this year's allocation.  This has the effect of taking water belonging to an individual contractor
	###(i.e. Southern California) and dividing it among all contractors
    self.appropriate_carryover(swp_forgone, "SLS", wateryear)
    self.appropriate_carryover(cvp_forgone, "SLF", wateryear)
    self.sanluisstate.flood_spill[t] += swp_forgone
    self.sanluisfederal.flood_spill[t] += cvp_forgone
	
	##Find ID demands
	###Daily demands are calculated from monthly demands based on 
	###crop acreage.  Right now the acreage is dependent on water year type,
	###so demand for each water year type can be calculated before the timestep loop.
	###When crop allocation functions are added, this demand must be calculated at least once
	###per year (as acreages update).  Daily demands are just monthly demands divided by the number
	###of days in a month
    if m == 3 and da == 2:
      for district_obj in self.district_list:
        if district_obj.has_pmp:
          total_water_base = 0.0
          land_constraint = 0.0
          for crop in district_obj.irrdemand.crop_list:
            land_constraint += district_obj.irrdemand.baseline_inputs['LAND'][crop]
          water_constraint_by_source = {}
          water_available = 0.0
          for source in district_obj.irrdemand.water_source_list:
            if source != 'GW':
              contracts_from_source = self.source_codes[source]
              water_constraint_by_source[source] = 0.0
              for source_contracts in contracts_from_source:
                water_available += (district_obj.deliveries[source_contracts][wateryear] + district_obj.projected_supply[source_contracts])*1000.0
                water_constraint_by_source[source] += (district_obj.deliveries[source_contracts][wateryear] + district_obj.projected_supply[source_contracts])*1000.0
          water_constraint_by_source['GW'] = max(district_obj.total_water_base - water_available, 0.0)
          i = 0
          x0 = np.zeros(len(district_obj.acreage_by_pmp_crop_type))
          for i in range(0, len(district_obj.acreage_by_pmp_crop_type)):
            x0[i] = district_obj.acreage_by_pmp_crop_type[i]
          district_obj.set_pmp_acreage(water_constraint_by_source, land_constraint, x0)

    if dowy == 0:
      for private_obj in self.private_list:
        if wateryear > 0:
          private_obj.permanent_crop_growth(wateryear, self.days_in_month, self.non_leap_year)
    for district_obj in self.district_list:
      district_obj.calc_demand(wateryear, year_index, da, m, self.days_in_month, m1, wyt)
      if district_obj.has_private:
        district_obj.private_demand = {}
        district_obj.private_delivery = {}
    for private_obj in self.private_list:
      private_obj.calc_demand(wateryear, year_index, da, m, self.days_in_month, self.non_leap_year, m1, wyt)
        
    ###For demands that occur on a branch of the California Aqueduct
	###(i.e. pumped into some kind of regional urban storage/distribution 
	###systems, daily demand are just the observed pumping (i.e. no model of 
	###the southern California/South Bay/Central Coast urban demand).  To run the
	###model in projection mode, we need statistical series of pumping at each of the Cal Aqueduct
	###branches.  Note:  for Bakersfield and Fresno in the local water systems, demands are deterministic
	###seasonal estimates.  Adding in pop. growth, etc. would be trivial, but is not included
    if t > 0:
      allocation_change = self.swp_allocation[t] - self.swp_allocation[t-1]
    else:
      allocation_change = 0.0
    for district_obj in self.urban_list:
      district_obj.get_urban_demand(t, m, da, dowy, wateryear, year_index, self.dowy_eom, self.forecastSRI[t], self.swp_allocation[t], allocation_change, self.model_mode)
    for private_obj in self.city_list:
      private_obj.get_urban_demand(t, m, da, wateryear, year_index, self.dowy_eom, self.forecastSRI[t], dowy, self.swp_allocation[t], allocation_change, self.model_mode)
    #else:
      #self.project_urban_pumping(da, dowy, m, wateryear, year_index, self.swp_allocation[t], self.cvp_allocation[t], self.forecastSRI[t])

    if m == 10 and da == 1:      
	  ###Pre flood demands - used to approximate the limit 
      ###for carryover storage (don't want to carryover more water than you can
      ###use from Oct-Jan).  Values for aqueduct branches are estimated to 
      ###avoid 'perfect foresight'
      for district_obj in self.district_list:
        district_obj.find_baseline_demands(wateryear, self.non_leap_year, self.days_in_month)
      for private_obj in self.private_list:
        private_obj.find_baseline_demands(self.non_leap_year, self.days_in_month)
	  
      for district_obj in self.urban_list:
        district_obj.find_pre_flood_demand(year_index, self.days_in_month, wyt)
      self.socal.pre_flood_demand = 500.0
      self.centralcoast.pre_flood_demand = 25.0
      self.southbay.pre_flood_demand = 15.0
	  
      ###Take the monthly demands for each irrigation district and
      ###'assign' them to a reservoir - this is used to estimate 
      ###fillup times so that districts know when to request recharge water
      #generates res.monthlydemand from aggregated district.monthlydemand
    if da == 1:
      self.agg_contract_demands(year_index, m, wyt)
	  
    ##Once a month, find the recharge capacity for each irrigation district
    ###This capacity is projected forward for a year to project how capacity would decline
    ###under continuous use - recalculated every month to update for actual use
    #generates self.district.max_leiu_recharge & self.district.max_direct_recharge
    if da == 1:
      for district_obj in self.district_list:
        district_obj.reset_recharge_recovery()
      for private_obj in self.private_list:
        private_obj.reset_recharge_recovery()
      for private_obj in self.city_list:
        private_obj.reset_recharge_recovery()
      ##searches through all waterbanks to find recharge capacity,
	  ##applies that capacity to districts by ownership shares
      self.find_recharge_bank(m,wyt)
      ##searches through all leiu bankign districts to find recharge capacity,
	  ##applies that capacity to districts by ownership shares
      self.find_recharge_leiu(m,wyt)
      ##searches through all districts to find native recharge capacity
      self.find_recharge_indistrict(m,wyt)
      self.find_leiu_exchange(wateryear, dowy)

	#Find the number of days before each reservoir is expected to fill-up	  
    ##Get Article 21 water from San Luis
	#for san luis - need to know if we can use the xvc from california aquduct - check for turnout to xvc from kern river and fkc
    ###find flood releases for the SWP at san luis (self.sanluisstate.min_daily_uncontrolled) - also find release toggles (for northern reservoir pumping coordination w/ san luis) and numdays_fillup for SWP district recharge decisions
    expected_pumping = self.estimate_project_pumping(t, proj_surplus, max_pumping, swp_AS, cvp_AS, self.max_tax_free, flood_release, wytSC)
    swp_release, swp_release2, self.sanluisstate.min_daily_uncontrolled, self.sanluisstate.numdays_fillup['demand'], fill_up_cross_swp = self.find_pumping_release(m, da, year_index, self.sanluisstate.S[t], 6680.0*cfs_tafd, self.sanluisstate.monthly_demand, self.sanluisstate.monthly_demand_must_fill, self.swpdelta.allocation[t-1]/self.swpdelta.total, expected_pumping['swp'], swp_AF, swp_AS, flood_volume['swp'], self.swpdelta.projected_carryover, self.swpdelta.running_carryover, self.max_tax_free, wyt, t, 'swp')
	  
    ###find flood releases for the CVP at san luis (self.sanluisfederal.min_daily_uncontrolled) - also find release toggles (for northern reservoir pumping coordination w/ san luis) and numdays_fillup for SWP district recharge decisions
    cvp_release, cvp_release2, self.sanluisfederal.min_daily_uncontrolled, self.sanluisfederal.numdays_fillup['demand'], fill_up_cross_cvp = self.find_pumping_release(m, da, year_index, self.sanluisfederal.S[t], 4430.0*cfs_tafd, self.sanluisfederal.monthly_demand, self.sanluisfederal.monthly_demand_must_fill, (self.cvpdelta.allocation[t-1] + self.cvpexchange.allocation[t-1])/(self.cvpexchange.total+self.cvpdelta.total), expected_pumping['cvp'], cvp_AF, cvp_AS, flood_volume['cvp'], self.cvpdelta.projected_carryover, self.cvpdelta.running_carryover + self.cvpexchange.running_carryover + self.crossvalley.running_carryover, self.max_tax_free, wyt, t, 'cvp')
    
    self.sanluisfederal.days_til_full[t] = min(self.sanluisfederal.numdays_fillup['demand'],fill_up_cross_cvp)
    self.sanluisstate.days_til_full[t] = min(self.sanluisstate.numdays_fillup['demand'],fill_up_cross_swp)

    ###June 1st, determine who is buying/selling into 'turnback pools' for the SWP.
    ###Note: look into other contract types to determine if this happens in CVP, Friant, local source contracts too
    if m == 6 and da == 1:
      for contract_obj in self.contract_list:
        seller_total = 0.0
        buyer_total = 0.0
        for district_obj in self.district_list:
          seller_turnback, buyer_turnback = district_obj.set_turnback_pool(contract_obj.name, year_index, self.days_in_month)
          seller_total += seller_turnback
          buyer_total += buyer_turnback
        for private_obj in self.city_list:
          total_contract = {}
          for district_key in private_obj.district_list:
            # district_obj = self.district_keys[district_key]
            total_contract[district_key] = self.district_keys[district_key].project_contract['tableA']
          additional_carryover = 0.0
          seller_turnback, buyer_turnback = private_obj.set_turnback_pool(contract_obj.name, year_index, self.days_in_month, additional_carryover)
          for district_key in private_obj.district_list:
            seller_total += seller_turnback[district_key]
            buyer_total += buyer_turnback[district_key]
        for district_obj in self.district_list:
          district_obj.make_turnback_purchases(seller_total, buyer_total, contract_obj.name)
        for private_obj in self.city_list:
          private_obj.make_turnback_purchases(seller_total, buyer_total, contract_obj.name)
 

	
    ####This function finds the expected # of days that a reservoir will fill
	####districts use this numdays_fillup attribute to determine when to recharge
	####carryover water
    for reservoir_obj in [self.success, self.kaweah, self.isabella, self.pineflat, self.millerton]:
      reservoir_obj.find_flow_pumping(t, m, dowy, year_index, self.days_in_month, self.dowy_eom, wyt, 'demand')
      reservoir_obj.days_til_full[t] = min(reservoir_obj.numdays_fillup['demand'], reservoir_obj.numdays_fillup['lookahead'])
	#Update Contract Allocations
    for contract_obj in self.contract_list:
      #for a specific contract, look up the reservoir it is stored in
      reservoir_obj = self.contract_reservoir[contract_obj.key]
      #then find all the contracts associated with that reservoir
      this_reservoir_all_contract = self.reservoir_contract[reservoir_obj.key]
      #need to find the total deliveries already made from the reservoir,
	  #total carryover storage at the reservoir, and the total priority/secondary allocations
	  #at that reservoir
      priority_deliveries = 0.0
      secondary_deliveries = 0.0
      total_res_carryover = 0.0
      priority_contract = 0.0
      secondary_contract = 0.0
      extra_allocation = 0.0
      for contract_obj2 in this_reservoir_all_contract:
        total_res_carryover += contract_obj2.tot_carryover
        extra_allocation += contract_obj2.tot_new_alloc
        if contract_obj2.allocation_priority == 1:
          priority_contract += contract_obj2.total*contract_obj2.reduction[wyt]
          priority_deliveries += contract_obj2.annual_deliveries[wateryear]
        else:
          secondary_contract += contract_obj2.total*contract_obj2.reduction[wyt]
          secondary_deliveries += contract_obj2.annual_deliveries[wateryear]
      #san luis doesn't have available_storage forecasts, so input from northern model is used
      #for state & federal portions
      if reservoir_obj.key == "SLS":
        total_allocation = self.swp_allocation[t] - self.pumping_turnback['SLS'] + extra_allocation - self.allocation_losses['SLS']
        reservoir_obj.reclaimed_carryover[t] = extra_allocation - self.pumping_turnback['SLS']
        reservoir_obj.contract_flooded[t] = self.allocation_losses['SLS'] * 1.0
        tot_ind_deliveries = 0.0
        tot_ind_carryover = 0.0
        tot_ind_turnback = 0.0
        tot_ind_paper = 0.0
	
        for district_obj in self.district_list:
          tot_ind_carryover +=  district_obj.carryover[contract_obj.name]
          tot_ind_deliveries +=  district_obj.deliveries[contract_obj.name][wateryear]
          tot_ind_turnback +=  district_obj.turnback_pool[contract_obj.name]
          tot_ind_paper +=  district_obj.paper_balance[contract_obj.name]
        for private_obj in self.private_list:
          for district_key in private_obj.district_list:
            tot_ind_carryover +=  private_obj.carryover[district_key][contract_obj.name]
            tot_ind_deliveries +=  private_obj.deliveries[district_key][contract_obj.name][wateryear]
            tot_ind_turnback +=  private_obj.turnback_pool[district_key][contract_obj.name]
          tot_ind_paper +=  private_obj.paper_balance[district_key][contract_obj.name]
        for private_obj in self.city_list:
          for district_key in private_obj.district_list:
            tot_ind_carryover +=  private_obj.carryover[district_key][contract_obj.name]
            tot_ind_deliveries +=  private_obj.deliveries[district_key][contract_obj.name][wateryear]
            tot_ind_turnback +=  private_obj.turnback_pool[district_key][contract_obj.name]
          tot_ind_paper +=  private_obj.paper_balance[district_key][contract_obj.name]


      elif reservoir_obj.key == "SLF":
        total_allocation = self.cvp_allocation[t] - self.pumping_turnback['SLF'] + extra_allocation - self.allocation_losses['SLF']
        reservoir_obj.reclaimed_carryover[t] = extra_allocation - self.pumping_turnback['SLF']
        reservoir_obj.contract_flooded[t] = self.allocation_losses['SLF'] * 1.0
        
      elif reservoir_obj.key == 'MIL':
        if m > 9 or m < 3:
          total_allocation = 0.0
        else:
          if contract_obj.allocation_priority == 1:
            total_allocation = reservoir_obj.available_storage[t] + contract_obj.annual_deliveries[wateryear] - max(total_res_carryover, 0.0)
          else:
            total_allocation = reservoir_obj.available_storage[t] + priority_deliveries + contract_obj.annual_deliveries[wateryear] - max(total_res_carryover, 0.0)
		
      else:
        #otherwise, total allocation at the reservoir is equal to available storage + deliveries - the total carryover storage
        if contract_obj.allocation_priority == 1:
          total_allocation = reservoir_obj.available_storage[t] + contract_obj.annual_deliveries[wateryear] - max(total_res_carryover, 0.0)
        else:
          total_allocation = reservoir_obj.available_storage[t] + priority_deliveries + contract_obj.annual_deliveries[wateryear] - max(total_res_carryover, 0.0)
      		
      contract_obj.calc_allocation(t, dowy, total_allocation, priority_contract, secondary_contract, wyt)

    ##Find contract 'storage pools' - how much water is available right now	
    ##san luis federal storage is divided between 3 water contracts - cvpdelta, exchange, and crossvalley
    ##millerton storage is divided between 2 water contracts - friant1 and friant2
    for contract_obj in self.contract_list:
      #for a specific contract, look up the reservoir it is stored in
      reservoir_obj = self.contract_reservoir[contract_obj.key]
      #then find all the contracts associated with that reservoir
      this_reservoir_all_contract = self.reservoir_contract[reservoir_obj.key]
      tot_res_deliveries = 0.0
      priority_storage = 0.0
      tot_res_carryover = 0.0
      for contract_obj2 in this_reservoir_all_contract:
        #if some contracts at a reservoir have 'priority' over storage space
        #(i.e., cvpdelta and exchange contracts have priority over the federal
        #san luis storage), calculate the total allocation volume that has priority
        #in a reservoir
        tot_res_deliveries += contract_obj2.annual_deliveries[wateryear]
        tot_res_carryover += contract_obj2.tot_carryover
        if contract_obj2.storage_priority == 1:
          priority_storage += contract_obj2.allocation[t]
      ##contract storage pools are the existing storage plus all the deliveries
      ##that have been made so far in that water year - so 'storage pool' is all
      ##the contract water that has already come into the reservoir, even water
      ##that has already been delivered	  
      total_water = reservoir_obj.S[t] - reservoir_obj.dead_pool + tot_res_deliveries - tot_res_carryover
      #find the storage pool for each contract
      contract_obj.find_storage_pool(t, wateryear, total_water, reservoir_obj.S[t], priority_storage)

	  ##Update District Contracts
    #self.assign_uncontrolled(t, wateryear)
    for contract_obj in self.contract_list:
      contract_obj.projected_carryover = 0.0
      contract_obj.running_carryover = 0.0
    #for each contract in each district, what is the district's share of (i) currently available (surface water) storage and (ii) expected remaining allocation
    for district_obj in self.district_list:
      for contract_obj in self.contract_list:
        next_year_carryover, this_year_carryover = district_obj.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type)
        contract_obj.projected_carryover += next_year_carryover
        contract_obj.running_carryover += this_year_carryover

    for private_obj in self.private_list:
      for contract_obj in self.contract_list:
        for district_key in private_obj.district_list:
          # district_obj = self.district_keys[district_key]
          next_year_carryover, this_year_carryover = private_obj.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type, district_key, self.district_keys[district_key].project_contract, self.district_keys[district_key].rights)
          contract_obj.running_carryover += this_year_carryover
        #next_year_carryover = x.apply_paper_balance(y.name, wyt, wateryear)
        #y.projected_carryover += next_year_carryover

    for private_obj in self.city_list:
      for contract_obj in self.contract_list:
        for district_key in private_obj.district_list:
          # district_obj = self.district_keys[district_key]
          next_year_carryover, this_year_carryover = private_obj.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type, district_key, self.district_keys[district_key].project_contract, self.district_keys[district_key].rights)
          contract_obj.running_carryover += this_year_carryover
        #next_year_carryover = x.apply_paper_balance_urban(y.name, wyt, wateryear)
        #y.projected_carryover += next_year_carryover		
		
      ##summation of all projected contracts for each water district (total surface water expected)
    counter = 0
    #find the 'in leiu' recovery capacity at each in-leiu recharge district using this day's irrigation demand
    #recovery is based on the surface water allocations for the in-leiu bank (i.e., the surface water that they give their banking partners
    #when the partners want to recover banked water
    self.update_leiu_capacity()
	
    for district_obj in self.district_list:
      #district can request recovery of their banked water
      if district_obj.key == 'SOB':
        target_eoy = 50.0
      else:
        target_eoy = 0.0
      district_obj.open_recovery(t, dowy, wateryear, target_eoy)
  
	  ##Recover Banked Water
    use_tolerance = 0
    for private_obj in self.private_list:
      private_obj.open_recovery(t, dowy, wateryear, self.number_years, wyt, use_tolerance, 0.0)
  
    use_tolerance = 0
    for private_obj in self.city_list:
      # for xx in private_obj.district_list:
        # district_obj = self.district_keys[xx]
        # total_contract = self.district_keys[xx].project_contract['tableA']
      # if dowy > 273:
      #   #additional_carryover = private_obj.get_urban_recovery_target(expected_pumping, total_contract, wateryear, dowy, year_index, wyt, 90, t, xx)
      #   additional_carryover = 0.0
      # else:
      #   additional_carryover = 0.0
      additional_carryover = 0.0
      private_obj.open_recovery(t, dowy, wateryear, self.number_years, wyt, use_tolerance, additional_carryover)
  
    flow_type = "recovery"
    #initialize the recover variables at the bank
    for waterbank_obj in self.waterbank_list:
      for participant_key in waterbank_obj.participant_list:
        waterbank_obj.recovery_use[participant_key] = 0.0#how much of the recovery capacity was used by the account holder
    #same but for 'in leiu' banks
    for leiu_obj in self.leiu_list:
      leiu_obj.tot_leiu_recovery_use = 0.0
      for participant_key in leiu_obj.participant_list:
        leiu_obj.recovery_use[participant_key] = 0.0
        leiu_obj.bank_deliveries[participant_key] = 0.0
    
	    #recover banked groundwater
      #only looking at GW exchanges for a few contracts
    if self.metropolitan.use_recovery > 0.0:
      exchanger_list = [self.kerntulare, self.pixley, self.lowertule]
      exchange_max = min(self.arvin.inleiubanked['MET'], self.metropolitan.dailydemand_start['SOC']*self.metropolitan.use_recovery)
      exchange_request = 0.0
      for district_obj in exchanger_list:
        exchange_request += max(district_obj.projected_supply['cvc'], 0.0)
      if exchange_request > 0.0:
        delivered_exchange = min(exchange_max, exchange_request)
        self.arvin.inleiubanked['MET'] -= delivered_exchange
        self.metropolitan.paper_balance['SOC']['cvc'] += delivered_exchange
      
        for district_obj in exchanger_list:
          ind_exchange = delivered_exchange * max(district_obj.projected_supply['cvc'], 0.0)/exchange_request
          self.arvin.inleiubanked[district_obj.key] += ind_exchange
          district_obj.paper_balance['cvc'] -= ind_exchange
    
    self.canal_contract['caa'] = [self.swpdelta]#only want to 'paper' exchange swp contracts
    for canal_obj in [self.calaqueduct, self.fkc, self.kernriverchannel]:
      for reservoir_obj in self.canal_reservoir[canal_obj.name]:
        if reservoir_obj.min_daily_uncontrolled < reservoir_obj.flood_flow_min or reservoir_obj.fcr > 0.0:
          for contract_obj in self.canal_contract[canal_obj.name]:
            exchange_contract = contract_obj.name
            delivery_key = exchange_contract + "_banked"
            self.set_canal_direction(flow_type)		
            canal_size = self.canal_district_len[canal_obj.name]
            total_canal_demand = self.search_canal_demand(dowy,canal_obj, "none", canal_obj.name, 'normal', flow_type, wateryear, 'recovery', {})
        self.set_canal_direction(flow_type)
    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]#reset california aqueduct contracts to be all san luis contracts
    
    #if self.xvc.locked == 1 and self.calaqueduct.flow_directions['recharge']['xvc'] == 'reverse':
    total_current_balance = max(self.buenavista.current_balance['kern'], 0.0)
    total_projected_supply = max(self.buenavista.projected_supply['kern'], 0.0)
      #conservative_estimate = max(min((dowy- 211.0)/(273.0 - 211.0), 1.0), 0.0)
    conservative_estimate = 1.0
    available_exchange_kern = max(min(conservative_estimate*total_projected_supply,total_current_balance), 0.0)
    requester_list = [self.cawelo, self.ID4, self.rosedale]
    total_request = 0.0
    for district_obj in requester_list:
      total_request += max(min(district_obj.dailydemand_start[0] + district_obj.recharge_carryover['tableA'], district_obj.dailydemand[0] + district_obj.recharge_carryover['tableA'], district_obj.current_balance['tableA'], district_obj.projected_supply['tableA']),0.0)
    if available_exchange_kern > 0.0:
      request_fraction = min(available_exchange_kern/total_request, 1.0)
    else:
      request_fraction = 0.0
    for district_obj in requester_list:
      exchanged_value = request_fraction * max(min(district_obj.dailydemand_start[0] + district_obj.recharge_carryover['tableA'], district_obj.dailydemand[0] + district_obj.recharge_carryover['tableA'], district_obj.current_balance['tableA'], district_obj.projected_supply['tableA']),0.0)
      district_obj.paper_balance['kern'] += exchanged_value
      district_obj.paper_balance['tableA'] -= exchanged_value
      self.buenavista.paper_balance['kern'] -= exchanged_value
      self.buenavista.paper_balance['tableA'] += exchanged_value
      for contract_obj in [self.kernriver, self.swpdelta]:
        next_year_carryover, this_year_carryover = district_obj.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type)
        next_year_carryover, this_year_carryover = self.buenavista.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type)

    flow_type = "recharge"
    for canal_obj in self.reservoir_canal[self.millerton.key]:
      self.set_canal_direction(flow_type)

      canal_size = self.canal_district_len[canal_obj.name]
      total_canal_demand = self.search_canal_demand(dowy, canal_obj, self.millerton.key, canal_obj.name, 'normal', flow_type, wateryear,'delivery', {})
      available_flow = 0.0
      for zz in total_canal_demand:
        available_flow += total_canal_demand[zz]
      excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, canal_obj, self.millerton.key, canal_obj.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'delivery')

      #total_canal_demand = self.find_contract_demand(t, dowy, wateryear, z, a.key, z.name, 'normal',flow_type)
      #excess_water, unmet_demand = self.deliver_contracts(t, dowy, z, a.key, z.name, total_canal_demand, canal_size, wateryear, 'normal',flow_type)
      self.set_canal_direction(flow_type)
	
    ##Flood Deliveries - 4 flood sources - Millerton, Isabella, Success, and Kaweah
    ##What is the priority for reservoirs getting to use the canals to route flood releases?
	  ##Note: most of the contracts have provisions that flood flows 'cannot displace' scheduled 
    ##deliveries (i.e. you can't use flood releases to fill demand that would be met by your contract
	  ##schedule), so might want to put this AFTER regular delivery routing
    flood_order_list = [self.pineflat, self.success, self.kaweah, self.isabella]
    #toggle to enable flood releases to go to districts/banks that don't have a contract w/the reservoir
    #only san luis restricts flood releases to contractors only (b/c otherwise they just dont pump)
    overflow_deliveries = 1
    flow_type = "recharge"
    self.set_canal_direction(flow_type)	
    for reservoir_obj in flood_order_list:
      #if flow is already on a bi-directional canal, it becomes closed to canals going the other direction
	    #checks the calaqueduct turnout to xvc is used, if not, xvc is open to fkc and kern river
      self.set_canal_direction(flow_type)
      #release flood flows to canals
      self.flood_operations(t, m, dowy, wateryear, reservoir_obj, flow_type, overflow_deliveries, wyt)
      #for canal in self.reservoir_canal[reservoir_obj.key]: 
        #for cnt in self.canal_contract[canal.name]:
          #for socal_cont in [self.metropolitan, self.castaic, self.coachella]:
            #if cnt.name + '_flood' in socal_cont.deliveries['SOC']:
              #if socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear] > 0.0:
                #socal_cont.deliveries['SOC']['tableA'][wateryear] += socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear]
                #self.pumping_turnback['SLS'] -= socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear]
                #socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear] = 0.0
          #for socal_cont in [self.socal,]:
            #if cnt.name + '_flood' in socal_cont.deliveries:
              #if socal_cont.deliveries[cnt.name + '_flood'][wateryear] > 0.0:
                #socal_cont.deliveries['tableA'][wateryear] += socal_cont.deliveries[cnt.name + '_flood'][wateryear]
                #self.pumping_turnback['SLS'] -= socal_cont.deliveries[cnt.name + '_flood'][wateryear]
                #socal_cont.deliveries[cnt.name + '_flood'][wateryear] = 0.0
	  
    self.set_canal_direction(flow_type)	
		
	  ##Direct deliveries from surface water sources
    flow_type = "recharge"
    for reservoir_obj in [self.pineflat, self.success, self.kaweah, self.isabella]:
      for canal_obj in self.reservoir_canal[reservoir_obj.key]:
        self.set_canal_direction(flow_type)

        canal_size = self.canal_district_len[canal_obj.name]
        total_canal_demand = self.search_canal_demand(dowy, canal_obj, reservoir_obj.key, canal_obj.name, 'normal', flow_type, wateryear,'delivery', {})
        available_flow = 0.0
        for zz in total_canal_demand:
          available_flow += total_canal_demand[zz]
        excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, canal_obj, reservoir_obj.key, canal_obj.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'delivery')

        #total_canal_demand = self.find_contract_demand(t, dowy, wateryear, z, reservoir_obj.key, z.name, 'normal',flow_type)
        #excess_water, unmet_demand = self.deliver_contracts(t, dowy, z, reservoir_obj.key, z.name, total_canal_demand, canal_size, wateryear, 'normal',flow_type)
		
    self.set_canal_direction(flow_type)
    for district_obj in self.district_list:
      district_obj.demand_days = {}
      district_obj.demand_days['current'] = {}
      district_obj.demand_days['lookahead'] = {}
      for contract_obj in self.contract_list:
        district_obj.demand_days['current'][contract_obj.name] = 0.0	
        district_obj.demand_days['lookahead'][contract_obj.name] = 0.0	
		
    for private_obj in self.city_list:
      private_obj.demand_days = {}
      private_obj.demand_days['current'] = {}
      private_obj.demand_days['lookahead'] = {}
      for contract_obj in self.contract_list:
        private_obj.demand_days['current'][contract_obj.name] = 0.0
        private_obj.demand_days['lookahead'][contract_obj.name] = 0.0

    for private_obj in self.private_list:
      private_obj.demand_days = {}      
      private_obj.demand_days['current'] = {}
      private_obj.demand_days['lookahead'] = {}
      for contract_obj in self.contract_list:
        private_obj.demand_days['current'][contract_obj.name] = 0.0
        private_obj.demand_days['lookahead'][contract_obj.name] = 0.0

    for contract_obj in self.contract_list:
      reservoir_obj = self.contract_reservoir[contract_obj.key]
      numdays_fillup = reservoir_obj.numdays_fillup['demand']
      if int(numdays_fillup) + dowy > 364:
        demand_days = dowy + int(numdays_fillup) - 364
        for district_obj in self.urban_list:
          if contract_obj.type == 'contract':
            total_contract = district_obj.project_contract[contract_obj.name]
          else:
            total_contract = 0.0
          district_obj.demand_days['lookahead'][contract_obj.name] = district_obj.get_urban_recovery_target(t, dowy, wateryear, wyt, expected_pumping, total_contract, demand_days, 0)

          #district_obj.demand_days['lookahead'][contract_obj.name] = np.sum(x.pumping[0][(t-dowy):(t+demand_days-dowy)])/1000.0
          district_obj.demand_days['current'][contract_obj.name] = district_obj.get_urban_recovery_target(t, 0, wateryear, wyt, expected_pumping, total_contract, demand_days, m-1)

        for private_obj in self.city_list:
          for district_key in private_obj.district_list:
            # district_obj = self.district_keys[district_key]
            if contract_obj.type == 'contract':
              total_contract = self.district_keys[district_key].project_contract[contract_obj.name]
            else:
              total_contract = 0.0
            private_obj.demand_days['lookahead'][contract_obj.name] += private_obj.get_urban_recovery_target(t, dowy, wateryear, wyt, expected_pumping, total_contract, demand_days, district_key, 0)
            private_obj.demand_days['current'][contract_obj.name] += private_obj.get_urban_recovery_target(t, 0, wateryear, wyt, expected_pumping, total_contract, demand_days, district_key, m-1)

      else:
        demand_days = int(numdays_fillup)
        if contract_obj.name == 'tableA':
          lookahead_days = dowy + int(fill_up_cross_swp) - 364
        elif contract_obj.name == 'cvpdelta' or contract_obj.name == 'exchange':
          lookahead_days = dowy + int(fill_up_cross_cvp) - 364
        else:
          lookahead_days = 0
        for district_obj in self.urban_list:
          if contract_obj.type == 'contract':
            total_contract = district_obj.project_contract[contract_obj.name]
          else:
            total_contract = 0.0

          district_obj.demand_days['current'][contract_obj.name] = district_obj.get_urban_recovery_target(t, 0, wateryear, wyt, expected_pumping, total_contract, demand_days, m-1)
          district_obj.demand_days['lookahead'][contract_obj.name]= district_obj.get_urban_recovery_target(t, dowy, wateryear, wyt, expected_pumping, total_contract, lookahead_days, 0)
        for private_obj in self.city_list:
          for district_key in private_obj.district_list:
            # district_obj = self.district_keys[district_key]
            if contract_obj.type == 'contract':
              total_contract = self.district_keys[district_key].project_contract[contract_obj.name]
            else:
              total_contract = 0.0
            private_obj.demand_days['current'][contract_obj.name] += private_obj.get_urban_recovery_target(t, 0, wateryear, wyt, expected_pumping, total_contract, demand_days, district_key, m-1)
            private_obj.demand_days['lookahead'][contract_obj.name] += private_obj.get_urban_recovery_target(t, dowy, wateryear, wyt, expected_pumping, total_contract, lookahead_days, district_key, 0)

   
    #Find district banking needs
    for district_obj in self.district_list:
      for contract_key in district_obj.contract_list:
        # contract_object = self.contract_keys[contract_key]
        reservoir = self.contract_reservoir[self.contract_keys[contract_key].key]
        if contract_key == 'tableA':
          lookahead_days = fill_up_cross_swp
          carryover_days = min(reservoir.numdays_fillup['demand'], 999.9)
        elif contract_key == 'cvpdelta' or contract_key == 'exchange' or contract_key == 'cvc':
          lookahead_days = fill_up_cross_cvp
          carryover_days = min(reservoir.numdays_fillup['demand'], 999.9)
        elif contract_key == 'kings':
          lookahead_days = min(reservoir.numdays_fillup['lookahead'], max(365.0 - dowy, 0.0))
          carryover_days = min(reservoir.numdays_fillup['demand'], 999.9)
        else:
          lookahead_days = reservoir.numdays_fillup['lookahead']
          carryover_days = min(reservoir.numdays_fillup['demand'], 999.9)
        additional_carryover = 0.0

        district_obj.open_recharge(t,m-1,da,wateryear,year_index,self.days_in_month, carryover_days, lookahead_days, self.contract_keys[contract_key].tot_carryover - self.contract_keys[contract_key].annual_deliveries[wateryear], contract_key, wyt, self.contract_turnouts[contract_key], 0.0, self.contract_keys[contract_key].allocation_priority)
		
    for private_obj in self.private_list:
      for contract_key in private_obj.contract_list:
        # contract_object = self.contract_keys[contract_key]
        reservoir_obj = self.contract_reservoir[self.contract_keys[contract_key].key]
        if contract_key == 'tableA':
          lookahead_days = fill_up_cross_swp
        elif contract_key == 'cvpdelta' or contract_key == 'exchange' or contract_key == 'cvc':
          lookahead_days = fill_up_cross_cvp
        else:
          lookahead_days = reservoir_obj.numdays_fillup['demand']

        additional_carryover = 0.0
          #additional_carryover += private_obj.contract_carryover_list[xx][y]
        private_obj.open_recharge(t,m-1,da,wateryear,year_index,self.days_in_month, reservoir_obj.numdays_fillup['demand'], lookahead_days, contract_key, wyt, self.contract_turnouts[contract_key], additional_carryover, self.contract_keys[contract_key].allocation_priority)
    
    for private_obj in self.city_list:
      for contract_key in private_obj.contract_list:
        # contract_object = self.contract_keys[contract_key]
        reservoir_obj = self.contract_reservoir[self.contract_keys[contract_key].key]
        if contract_key == 'tableA':
          lookahead_days = fill_up_cross_swp
        elif contract_key == 'cvpdelta' or contract_key == 'exchange' or contract_key == 'cvc':
          lookahead_days = fill_up_cross_cvp
        else:
          lookahead_days = reservoir_obj.numdays_fillup['demand']
		  
        additional_carryover = 0.0
        for district_key in private_obj.district_list:
          if t + lookahead_days < self.T:
            additional_carryover += np.sum(private_obj.pumping[district_key][(t+365-dowy): int(t+lookahead_days) ])/1000.0
          else:
            if lookahead_days > 365:
              additional_carryover= 999.9
            else:
              additional_carryover += np.sum(private_obj.pumping[district_key][(t-dowy): int(t + lookahead_days - 365) ])/1000.0
        private_obj.open_recharge(t, m-1, da, wateryear, year_index, self.days_in_month, reservoir_obj.numdays_fillup['demand'], lookahead_days, contract_key, wyt, self.contract_turnouts[contract_key], 0.0, self.contract_keys[contract_key].allocation_priority)
		
	  ##Deliveries for banking
    flow_type = "recharge"
    for reservoir_obj in [self.isabella, self.pineflat, self.success, self.kaweah]:
      for canal_obj in self.reservoir_canal[reservoir_obj.key]:
        self.set_canal_direction(flow_type)

        canal_size = self.canal_district_len[canal_obj.name]
        total_canal_demand = self.search_canal_demand(dowy, canal_obj, reservoir_obj.key, canal_obj.name, 'normal',flow_type,wateryear,'banking', {})
        available_flow = 0.0
        for zz in total_canal_demand:
          available_flow += total_canal_demand[zz]
        excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, canal_obj, reservoir_obj.key, canal_obj.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'banking')
		
    self.set_canal_direction(flow_type)
	
	
    #toggle to enable flood releases to go to districts/banks that don't have a contract w/the reservoir
    #only san luis restricts flood releases to contractors only (b/c otherwise they just dont pump)
    overflow_deliveries = 1
    flow_type = "recharge"
    self.set_canal_direction(flow_type)	
    #if flow is already on a bi-directional canal, it becomes closed to canals going the other direction
    #checks the calaqueduct turnout to xvc is used, if not, xvc is open to fkc and kern river
    self.set_canal_direction(flow_type)
    #release flood flows to canals
    self.flood_operations(t, m, dowy, wateryear, self.millerton, flow_type, overflow_deliveries, wyt)  
    self.set_canal_direction(flow_type)
    #for canal in self.reservoir_canal[self.millerton.key]:
      #for cnt in self.canal_contract[canal.name]:
        #for socal_cont in [self.metropolitan, self.castaic, self.coachella]:
          #if cnt.name + '_flood' in socal_cont.deliveries['SOC']:
            #if socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear] > 0.0:
              #socal_cont.deliveries['SOC']['tableA'][wateryear] += socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear]
              #self.pumping_turnback['SLS'] -= socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear]
              #socal_cont.deliveries['SOC'][cnt.name + '_flood'][wateryear] = 0.0
        #for socal_cont in [self.socal,]:
          #if cnt.name + '_flood' in socal_cont.deliveries:
            #if socal_cont.deliveries[cnt.name + '_flood'][wateryear] > 0.0:
              #socal_cont.deliveries['tableA'][wateryear] += socal_cont.deliveries[cnt.name + '_flood'][wateryear]
              #self.pumping_turnback['SLS'] -= socal_cont.deliveries[cnt.name + '_flood'][wateryear]
              #socal_cont.deliveries[cnt.name + '_flood'][wateryear] = 0.0

	
    flow_type = "recharge"
    for canal_obj in self.reservoir_canal[self.sanluis.key]:
      self.set_canal_direction(flow_type)

      canal_size = self.canal_district_len[canal_obj.name]
      total_canal_demand = self.search_canal_demand(dowy, canal_obj, self.sanluis.key, canal_obj.name, 'normal', flow_type, wateryear,'delivery', {})
      available_flow = 0.0
      for zz in total_canal_demand:
        available_flow += total_canal_demand[zz]
      excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, canal_obj, self.sanluis.key, canal_obj.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'delivery')

      #total_canal_demand = self.find_contract_demand(t, dowy, wateryear, z, a.key, z.name, 'normal',flow_type)
      #excess_water, unmet_demand = self.deliver_contracts(t, dowy, z, a.key, z.name, total_canal_demand, canal_size, wateryear, 'normal',flow_type)
      self.set_canal_direction(flow_type)
	
    #Flood releases	
    #article21 releases from san luis - state
    self.canal_contract['caa'] = [self.swpdelta]#for swp flood releases, only swp contracts are considered
    flow_type = "recharge"
    overflow_deliveries = 0#no flood deliveries to non-contractors in swp or cvp
    self.set_canal_direction(flow_type)   
    self.flood_operations(t, m, dowy, wateryear, self.sanluisstate, flow_type, overflow_deliveries, wyt)	  

    #flood releases from san luis - federal
    self.canal_contract['caa'] = [self.cvpdelta, self.cvpexchange, self.crossvalley]
    self.set_canal_direction(flow_type)
    self.flood_operations(t, m, dowy, wateryear, self.sanluisfederal, flow_type, overflow_deliveries, wyt)	  
    self.set_canal_direction(flow_type)
    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]#reset california aqueduct contracts to be all san luis contracts	

    #if self.sanluisstate.min_daily_uncontrolled > 0.0:
      #if self.metropolitan.annualdemand['SOC'] > self.metropolitan.projected_supply['SOC']['tableA']:
        #this_day_contract_deliveries = max(min(self.metropolitan.dailydemand_start['SOC'] - self.metropolitan.dailydemand['SOC'], self.metropolitan.deliveries['SOC']['tableA'][wateryear], self.metropolitan.annualdemand['SOC'] - self.metropolitan.projected_supply['SOC']['tableA']), 0.0)
        #self.metropolitan.deliveries['SOC']['tableA_flood'][wateryear] += this_day_contract_deliveries	
        #self.metropolitan.deliveries['SOC']['tableA'][wateryear] -= this_day_contract_deliveries
		
	  ##Deliveries for banking
    flow_type = "recharge"
    for reservoir_obj in [self.sanluis, self.millerton]:
      for canal_obj in self.reservoir_canal[reservoir_obj.key]:
        self.set_canal_direction(flow_type)

        canal_size = self.canal_district_len[canal_obj.name]
        total_canal_demand = self.search_canal_demand(dowy, canal_obj, reservoir_obj.key, canal_obj.name, 'normal',flow_type,wateryear,'banking', {})
        available_flow = 0.0
        for zz in total_canal_demand:
          available_flow += total_canal_demand[zz]
        excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, canal_obj, reservoir_obj.key, canal_obj.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'banking')
		
    self.set_canal_direction(flow_type)
	
    #swp/cvp_pump - find maximum pumping levels based on space in san luis(inputs for the northern model)
  	#swp/cvp_release -  toggle for 'max pumping' releases, based on space in san luis (inputs for the northern model)
	  #take direct recharge deliveries and 'absorb' them into the groundwater, clearing way for more space in the recharge basins
    for waterbank_obj in self.waterbank_list:#at water banks
      waterbank_obj.sum_storage()
      waterbank_obj.absorb_storage()
    for leiu_obj in self.leiu_list:#at in-leiu district banks (some also have direct recharge capacity, in addition to in-leiu)
      leiu_obj.absorb_storage()
    for district_obj in self.district_list:#at in-district recharge facilities
      if district_obj.current_recharge_storage > 0.0:
        district_obj.absorb_storage()
		
    # kill_permanent = 0
    # if kill_permanent == 1:
    #   for private_obj in self.private_list:
    #     for district_key in private_obj.district_list:
    #       private_obj.find_unmet_et(district_key, wateryear, dowy)


    requester_list = [self.cawelo, self.ID4, self.rosedale]
    for district_obj in requester_list:
      for contract_obj in [self.kernriver, self.swpdelta]:
        next_year_carryover, this_year_carryover = district_obj.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type)
      self.buenavista.paper_balance['tableA'] -= district_obj.projected_supply['kern']
      self.buenavista.paper_balance['kern'] += district_obj.projected_supply['kern']
      district_obj.paper_balance['tableA'] += district_obj.projected_supply['kern']
      district_obj.paper_balance['kern']  -= district_obj.projected_supply['kern']
      for contract_obj in [self.kernriver, self.swpdelta]:
        next_year_carryover, this_year_carryover = district_obj.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type)

    for contract_obj in [self.kernriver, self.swpdelta]:
      next_year_carryover, this_year_carryover = self.buenavista.update_balance(t, wateryear, contract_obj.storage_pool[t], contract_obj.allocation[t], contract_obj.available_water[t], contract_obj.name, contract_obj.tot_carryover, contract_obj.type)
      
		
    #reservoir class water balance do not include releases for irrigation/recharge deliveries
	  #update storage based on total contract deliveries each day
    for contract_obj in self.contract_list:
      reservoir = self.contract_reservoir[contract_obj.key]
      if t < (self.T - 1):
        reservoir.S[t+1] -= contract_obj.daily_deliveries
      contract_obj.daily_deliveries = 0.0
    if t < (self.T -1):
      swp_pump, cvp_pump, = self.find_san_luis_space(t, 6680.0*cfs_tafd, 4430.0*cfs_tafd)
    else:
      swp_pump = 0.0
      cvp_pump = 0.0
	  
	  ####ASSUMPTION THAT ANY DEMAND NOT MET BY SURFACE WATER IS MET THROUGH PUMPING
	  ####doesn't do anything in the model (no GW connection), but can change this assumption/link to other models
    for district_obj in self.district_list:
      district_obj.annual_private_pumping = district_obj.dailydemand[0]
    for private_obj in self.private_list:
      for district_key in private_obj.district_list:
        private_obj.annual_private_pumping[district_key] = private_obj.dailydemand[district_key] 
    for private_obj in self.city_list:
      for district_key in private_obj.district_list:
        private_obj.annual_private_pumping[district_key] = private_obj.dailydemand[district_key] 
	  ####FOR RESULTS-OUTPUT (not output to northern model, but output for plots)
    for district_obj in self.district_list:
      district_obj.accounting_full(t, wateryear)
      for contract_obj in self.contract_list:
        #from individual contracts - paper balance, carryover storage, allocations, and deliveries (irrigation) - records daily values
        contract_obj.accounting(t, da, m, wateryear, district_obj.deliveries[contract_obj.name][wateryear], district_obj.carryover[contract_obj.name], district_obj.turnback_pool[contract_obj.name], district_obj.deliveries[contract_obj.name + '_flood'][wateryear] + district_obj.deliveries[contract_obj.name + '_flood_irrigation'][wateryear])
    for private_obj in self.private_list:
      private_obj.accounting_full(t, wateryear)
      for contract_obj in self.contract_list:
        for district_key in private_obj.district_list:
          contract_obj.accounting(t, da, m, wateryear, private_obj.deliveries[district_key][contract_obj.name][wateryear], private_obj.carryover[district_key][contract_obj.name], private_obj.turnback_pool[district_key][contract_obj.name], private_obj.deliveries[district_key][contract_obj.name + '_flood'][wateryear] + private_obj.deliveries[district_key][contract_obj.name + '_flood_irrigation'][wateryear])
    for private_obj in self.city_list:
      private_obj.accounting_full(t, wateryear)
      for contract_obj in self.contract_list:
        for district_key in private_obj.district_list:
          contract_obj.accounting(t, da, m, wateryear, private_obj.deliveries[district_key][contract_obj.name][wateryear], private_obj.carryover[district_key][contract_obj.name], private_obj.turnback_pool[district_key][contract_obj.name], private_obj.deliveries[district_key][contract_obj.name + '_flood'][wateryear] + private_obj.deliveries[district_key][contract_obj.name + '_flood_irrigation'][wateryear])    
    
    #update individual accounts in groundwater banks
    for waterbank_obj in self.waterbank_list:
      waterbank_obj.accounting(t, m, da, wateryear)
    for waterbank_obj in self.leiu_list:
      waterbank_obj.accounting_leiubank(t, m, da, wateryear)

    ##Reset contracts for the next water year, distribute unused contract water into carryover flows/ next year's contract allocation
    tot_paper = 0.0
    tot_turnback = 0.0
    if m == 9 and da == 30:
      for contract_obj in self.contract_list:
        lastYearCarryover = contract_obj.tot_carryover
        contract_obj.tot_carryover = 0.0
        contract_obj.tot_new_alloc = 0.0
        for district_obj in self.district_list:
          use_contract = 0
          for contract_key in district_obj.contract_list:
            if contract_key == contract_obj.name:
              use_contract = 1
          if use_contract == 1:
            new_alloc, carryover = district_obj.calc_carryover(contract_obj.storage_pool[t], wateryear, contract_obj.type, contract_obj.name)
            contract_obj.tot_new_alloc += new_alloc
            contract_obj.tot_carryover += carryover
              

        for private_obj in self.private_list:
          #total_carryover = 0.0
          #total_paper_balance = 0.0
          #total_carryover_limit = 0.0
          use_contract = 0
          for contract_key in private_obj.contract_list:
            if contract_key == contract_obj.name:
              use_contract = 1
          if use_contract == 1:	
            for district_key in private_obj.district_list:
              # district_obj = self.district_keys[district_key]
              new_alloc, carryover = private_obj.calc_carryover(contract_obj.storage_pool[t], wateryear, contract_obj.type, contract_obj.name, district_key, self.district_keys[district_key].project_contract, self.district_keys[district_key].rights)

              contract_obj.tot_carryover += carryover
              contract_obj.tot_new_alloc += new_alloc
              #total_carryover += private_obj.carryover[district_key][contract_obj.name]
              #total_paper_balance += private_obj.paper_balance[district_key][contract_obj.name]
              #total_carryover_limit += private_obj.contract_carryover_list[district_key][contract_obj.name]
            #if total_carryover + total_paper_balance > total_carryover_limit:
              #for district_key in private_obj.district_list:
                #private_obj.carryover[district_key][contract_obj.name] = private_obj.contract_carryover_list[district_key][contract_obj.name]
                #contract_obj.tot_carryover += private_obj.carryover[district_key][contract_obj.name]
              #contract_obj.tot_new_alloc += (total_carryover + total_paper_balance - total_carryover_limit)
            #else:
              #carryover_frac = (total_carryover + total_paper_balance)/total_carryover_limit
              #for district_key in private_obj.district_list:
                #private_obj.carryover[district_key][contract_obj.name] = carryover_frac*private_obj.contract_carryover_list[district_key][contract_obj.name]
                #contract_obj.tot_carryover += private_obj.carryover[district_key][contract_obj.name]
          #for district_key in private_obj.district_list:	
            #private_obj.paper_balance[district_key][contract_obj.name] = 0.0
        for private_obj in self.city_list:
          #total_carryover = 0.0
          #total_paper_balance = 0.0
          #total_carryover_limit = 0.0
          use_contract = 0
          for contract_key in private_obj.contract_list:
            if contract_key == contract_obj.name:
              use_contract = 1
          if use_contract == 1:	  
            for district_key in private_obj.district_list:
              # district_obj = self.district_keys[district_key]
              new_alloc, carryover = private_obj.calc_carryover(contract_obj.storage_pool[t], wateryear, contract_obj.type, contract_obj.name, district_key, self.district_keys[district_key].project_contract, self.district_keys[district_key].rights)
              contract_obj.tot_carryover += carryover
              contract_obj.tot_new_alloc += new_alloc
              #total_carryover += private_obj.carryover[district_key][contract_obj.name]
              #total_paper_balance += private_obj.paper_balance[district_key][contract_obj.name]
              #total_carryover_limit += private_obj.contract_carryover_list[district_key][contract_obj.name]
            #if total_carryover + total_paper_balance > total_carryover_limit:
              #for district_key in private_obj.district_list:
                #private_obj.carryover[district_key][contract_obj.name] = private_obj.contract_carryover_list[district_key][contract_obj.name]
                #contract_obj.tot_carryover += private_obj.carryover[district_key][contract_obj.name]
              #contract_obj.tot_new_alloc += (total_carryover + total_paper_balance - total_carryover_limit)
            #else:
              #if total_carryover_limit > 0.0:
                #carryover_frac = (total_carryover + total_paper_balance)/total_carryover_limit
              #else:
                #carryover_frac = 0.0
              #for district_key in private_obj.district_list:
                #private_obj.carryover[district_key][contract_obj.name] = carryover_frac*private_obj.contract_carryover_list[district_key][contract_obj.name]

                #contract_obj.tot_carryover += private_obj.carryover[district_key][contract_obj.name]
          #for district_key in private_obj.district_list:	
            #private_obj.paper_balance[district_key][contract_obj.name] = 0.0

        if contract_obj.name == 'tableA' and use_contract == 1:
          current_carryover_storage = self.sanluisstate.S[t] - contract_obj.tot_new_alloc - 40.0
          fudge_factor = current_carryover_storage/contract_obj.tot_carryover
          contract_obj.tot_carryover = self.sanluisstate.S[t] - contract_obj.tot_new_alloc - 40.0
          sum_carryover = 0.0
          for district_obj in self.district_list:
            district_obj.carryover[contract_obj.name] = district_obj.carryover[contract_obj.name]*fudge_factor
            sum_carryover+= district_obj.carryover[contract_obj.name]
          for private_obj in self.private_list:
            for district_key in private_obj.district_list:
              private_obj.carryover[district_key][contract_obj.name] = private_obj.carryover[district_key][contract_obj.name]*fudge_factor
              sum_carryover+= private_obj.carryover[district_key][contract_obj.name]
          for private_obj in self.city_list:
            for district_key in private_obj.district_list:
              private_obj.carryover[district_key][contract_obj.name] = private_obj.carryover[district_key][contract_obj.name]*fudge_factor
              sum_carryover+= private_obj.carryover[district_key][contract_obj.name]

        contract_obj.running_carryover = contract_obj.tot_carryover


      #reset counter for delta contract adjustment for foregone pumping and uncontrolled releases
      for key in self.pumping_turnback:
        self.pumping_turnback[key] = 0.0
      for key in self.allocation_losses:
        self.allocation_losses[key] = 0.0
		
    ##Clear Canal Flows
    ##every day, we zero out the flows on each canal (i.e. no canal storage, no 'routing' of water on the canals)
	  ###any flow released from a reservoir is assumed to arrive at its destimation immediately
    #Reset canals and record turnouts & flows at each node
    for canal_obj in self.canal_list:
      counter = 0
      for canal_loc in range(0, self.canal_district_len[canal_obj.name]):
        loc_id = self.canal_district[canal_obj.name][canal_loc]
        canal_obj.accounting(t, loc_id.key, counter)
        counter += 1
      canal_obj.num_sites = self.canal_district_len[canal_obj.name]
      canal_obj.turnout_use = [0.0 for _ in range(canal_obj.num_sites)]
      canal_obj.flow = [0.0 for _ in range(canal_obj.num_sites+1)]
      canal_obj.locked = 0


    return swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump
		
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################



#####################################################################################################################
#############################  Federal/State San Luis Storage Sharing   #############################################
#####################################################################################################################		  
  def step_san_luis(self, t, m, da):
  #This function allows the state/federal projects to take advantage of any unused space the other may have so that storage
  #volumes can temporarily go above each project's 50% share of the storage cpacity at san luis
    self.sanluisfederal.S[t+1] = self.sanluisfederal.S[t] + self.trp_pumping[t]
    self.sanluisstate.S[t+1] = self.sanluisstate.S[t] + self.hro_pumping[t]
    if m == 10 and da == 1:
      self.ytd_pump_trp[t] = self.trp_pumping[t]
      self.ytd_pump_hro[t] = self.hro_pumping[t]
    else:
      self.ytd_pump_trp[t] = self.trp_pumping[t] + self.ytd_pump_trp[t-1]
      self.ytd_pump_hro[t] = self.hro_pumping[t] + self.ytd_pump_hro[t-1]

    if self.sanluisstate.S[t+1] > 1021.0:
      extra_storage_s = self.sanluisstate.S[t+1] - 1021.0
      extra_space_s = 0.0
    else:
      #extra_space_s = 0.0
      extra_space_s = 1021.0 - self.sanluisstate.S[t+1]
      extra_storage_s = 0.0
    if self.sanluisfederal.S[t+1] > 1021.0:
      extra_storage_f = self.sanluisfederal.S[t+1] - 1021.0
      extra_space_f = 0.0
    else:
      #extra_space_f = 0.0
      extra_space_f = 1021.0 - self.sanluisfederal.S[t+1]
      extra_storage_f = 0.0
    if extra_storage_s > 0.0:
      self.sanluisstate.fcr = max(extra_storage_s - extra_space_f,0.0)
    else:
      self.sanluisstate.fcr = 0.0
    if extra_storage_f > 0.0:
      self.sanluisfederal.fcr = max(extra_storage_f - extra_space_s,0.0)
    else:
      self.sanluisfederal.fcr = 0.0
    self.sanluisstate.S[t+1] -= self.sanluisstate.fcr
    self.sanluisfederal.S[t+1] -= self.sanluisfederal.fcr	  
    return max(min(extra_storage_s, extra_space_f), 0.0), max(min(extra_storage_f, extra_space_s),0.0)
	
  def find_san_luis_space(self, t, swp_pump_max, cvp_pump_max):
  #if there is no additional storage in san luis, send toggle variable to the northern model to turn 'off'
	#pumping at teh delta (so no wasted pumping if there is no room in san luis)
    if self.sanluisstate.S[t+1] + swp_pump_max > 1020.0:
      swp_pump = 1021.0 - self.sanluisstate.S[t+1]
    else:
      swp_pump = 999.0
    if self.sanluisfederal.S[t+1] + cvp_pump_max >	1020.0:
      cvp_pump = 1021.0 - self.sanluisfederal.S[t+1]
    else:
      cvp_pump = 999.0
	  
    return swp_pump, cvp_pump
	
  def estimate_project_pumping(self, t, proj_surplus, max_pumping, swp_AS, cvp_AS, max_tax_free, flood_release, wyt):
    dowy = self.dowy[t]
    year_index = self.year[t] - self.starting_year

    # month_evaluate = m - 1
    tax_free_frac = {}
    excess_storage = {}
    available_storage = {}
    max_pump = {}
    expected_pumping = {}
    available_storage['swp'] = swp_AS
    available_storage['cvp'] = cvp_AS
    max_pump['swp'] = 6680.0*cfs_tafd
    max_pump['cvp'] = 4300.0*cfs_tafd
    expected_pumping['swp'] = {}
    expected_pumping['swp']['taxed']= np.zeros(12)
    expected_pumping['swp']['untaxed']= np.zeros(12)
    expected_pumping['swp']['gains']= np.zeros(12)
    expected_pumping['cvp'] = {}
    expected_pumping['cvp']['taxed']= np.zeros(12)
    expected_pumping['cvp']['untaxed']= np.zeros(12)
    expected_pumping['cvp']['gains']= np.zeros(12)

    for key in ['swp', 'cvp']:
      tax_free_frac[key] = min(max(available_storage[key]/max_tax_free[wyt][key][dowy], 0.0), 1.0)
      excess_storage[key] = max(available_storage[key] - max_tax_free[wyt][key][dowy], 0.0)
      # if dowy < 123:
      #   total_taxed = (123 + 92 - dowy)*max_pump[key] - (max_tax_free[wyt][key][dowy] - max_tax_free[wyt][key][122]) - max_tax_free[wyt][key][274]
      # elif dowy < 274:
      #   total_taxed = (273 + 92 - dowy)*max_pump[key] - max_tax_free[wyt][key][dowy]
      # else:
      #   total_taxed = (365 - dowy)*max_pump[key] - max_tax_free[wyt][key][dowy]

      #if month_evaluate > 8:
      for monthloop in range(0, 12):
        # if month already happened this year, we are looping to next year
        if self.dowy_eom[year_index][monthloop] < dowy:
          daysmonth = self.days_in_month[year_index + 1][monthloop]
          dowyeom = self.dowy_eom[year_index + 1][monthloop]
          running_days = 365 - dowy + dowyeom

        else:
          daysmonth = self.days_in_month[year_index][monthloop]
          dowyeom = self.dowy_eom[year_index][monthloop]
          running_days = dowyeom - dowy

        # max_tax_free starts with total max_tax_free for water year at index 0, then amount left after day 0 in index 1, etc. So total_tax_free for October is index 0 minus index[31], November is [31]-[61],...
        start_m = dowyeom - daysmonth + 1
        end_m = dowyeom + 1
        total_tax_free = max_tax_free[wyt][key][start_m] - max_tax_free[wyt][key][end_m]

          #if excess_storage[key] > total_taxed and dowy < self.dowy_eom[monthloop]:
        if monthloop == 3 or monthloop == 4:
          max_pump['swp'] = 750.0*cfs_tafd
          max_pump['cvp'] = 750.0*cfs_tafd
        else:
          max_pump['swp'] = 6680.0*cfs_tafd
          max_pump['cvp'] = 4300.0*cfs_tafd

        # account for omr rules
        if t > self.omr_rule_start - running_days:
          max_pump['swp'] = min(max_pump['swp'], max_pumping['swp'][monthloop]/daysmonth)
          max_pump['cvp'] = min(max_pump['cvp'], max_pumping['cvp'][monthloop]/daysmonth)


        expected_pumping[key]['taxed'][monthloop] = max_pump[key]*daysmonth
        expected_pumping[key]['untaxed'][monthloop] = min(max(proj_surplus[key][monthloop] + flood_release[key]*daysmonth,total_tax_free), max_pump[key]*daysmonth)
        expected_pumping[key]['gains'][monthloop] = min(proj_surplus[key][monthloop] + flood_release[key]*daysmonth, max_pump[key]*daysmonth)

    return expected_pumping


	
  def find_pumping_release(self, m, da, year_index, start_storage, pump_max, month_demand, month_demand_must_fill, allocation, expected_pumping, flood_supply, available_storage, flood_storage, projected_carryover, current_carryover, max_tax_free, wyt, t, key):
  ##this function is used by the swpdelta & cvpdelta contracts to manage san luis reservoir storage
	##and coordinate pumping at the delta
  ##state and federal storage portions managed seperately

    month_evaluate = m - 1
    # first_month_frac = max(self.days_in_month[year_index][month_evaluate] - da, 0.0)/self.days_in_month[year_index][month_evaluate]
	
	
	  ###Initial storage projections - current month
	  ##calculate expected deliveries during this month from san luis
    #expected_demands = (month_demand[wyt][month_evaluate]*allocation + month_demand_must_fill[wyt][month_evaluate])/self.days_in_month[year_index][month_evaluate]
    expected_demands = (month_demand[wyt][month_evaluate] + month_demand_must_fill[wyt][month_evaluate])/self.days_in_month[year_index][month_evaluate]
    expected_inflow = expected_pumping['gains'][month_evaluate]/self.days_in_month[year_index][month_evaluate]
    expected_untaxed = (expected_pumping['untaxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])*(1.0 - da/self.days_in_month[year_index][month_evaluate])
    expected_taxed = (expected_pumping['taxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])*(1.0 - da/self.days_in_month[year_index][month_evaluate])

	  #how much 'unstored' pumping can we expect into San Luis?
    #self.month_averages comes from self.predict_delta_gains
	  #proj_surplus & proj_surplus2 are generated in the northern model, from 8RI regression in self.predict_delta_gains
    if month_evaluate == 3 or month_evaluate == 4:
      expected_inflow = 0.75
    #expected monthly change in san luis storage
    net_monthly = (expected_inflow - expected_demands)*max(self.days_in_month[year_index][month_evaluate] - da, 0.0)
    ##Enter into a loop for projecting storage & pumping forward one month at a time
  	##start with current estimates
    next_month_storage = start_storage#running storage levels
    this_month_days = max(self.days_in_month[year_index][month_evaluate] - da, 0.0)#running days in a month
    article21 = 0.0#initialize article 21 release estimates
    numdays_fillup = 999.9#initialize numdays_fillup variable
    numdays_fillup_next_year = 999.9
    total_days_remaining = 0.0#used for estimates of how long san luis will take to fill up (for districts to make carryover decisions)

    pumping_toggle = 1#toggle for releasing water to maximum pumping levels
    tax_free_toggle = 1#toggle for releasing water to 'tax free' pumping levels
    pumping_toggle_override = 0#toggle for releasing water to maximum pumping levels
    tax_free_toggle_override = 0#toggle for releasing water to 'tax free' pumping levels
    exceed_toggle_override = 0
    ##loop through all months until april (april/may have very limited pumping, should not plan for any pumping to occur then)
	  ##this loop helps to project storage in san luis up to a year out > so we know in advance if we need to pump or will be filling the reservoir
	  ##note: this loop will go through one water year and into the next one
    cross_counter_y = 0
    cross_counter_wy = 0
    end_counter = 0
    extra_demand = 0.0
    carryover_adjust = current_carryover
    while end_counter == 0:
    #while month_evaluate == m - 1:
      #estimate storage at the end of this month by adding monthly change to the running storage tally
      next_month_storage += net_monthly

      if net_monthly > 0.0:
        partial_month_remaining = max(1 - max(next_month_storage - 1020.0, 0.0)/net_monthly, 0.0)*self.days_in_month[year_index+cross_counter_y][month_evaluate]
      else:
        next_month_storage = min(1020.0 + net_monthly, next_month_storage)
        partial_month_remaining = 0.0
      if next_month_storage > 1020.0:
        exceed_toggle_override = 1
	    ##can we reach the storage targets only using 'tax free' pumping?
      ##how much water can we expect to pump w/o additional E/I tax through the end of the month?
      #if dowy <= self.dowy_eom[month_evaluate]:#running water year is the same as the beginning of the loop
        #how much 'tax free' pumping through the end of this month? - total tax free remaining at the current simulation day, minus total tax free remaining at the end of the looped month
        #running_tax_free_pumping = self.max_tax_free[wyt][key][dowy] - self.max_tax_free[wyt][key][self.dowy_eom[month_evaluate]]
      #else:#looped into the next water year, so we have to calculate the tax free pumping remaining through the end of the current year, then add in the tax free remaining through the looped month in the next year
        #running_tax_free_pumping = self.max_tax_free[wyt][key][dowy] + self.max_tax_free[wyt][key][0] - self.max_tax_free[wyt][key][self.dowy_eom[month_evaluate]]
      #running_tax_free_pumping will be added to the net_month storage variable, so we don't want to double-count 'unstored pumping'
      #if running_tax_free_pumping > available_pumping:
        #running_tax_free_pumping = available_pumping
	    ##note - beginning month = m; looped month = month_evaluate
      if start_storage > 1000.0:
        #if san luis storage is currently greater than capacity, no pumping, article21 releases triggered
        pumping_toggle = min(0, pumping_toggle)
        tax_free_toggle = min(0, tax_free_toggle)
        article21 = max(next_month_storage - 1000.0, start_storage - 1000.0, article21)
        numdays_fillup = 0.0#if this condition is hit, no more days needed to fill reservoir (already full)
      if next_month_storage < 1020.0:
        article21 = max(0.0, article21)
        #if expected storage is less than 0 in any month, pump at max, no article 21
        if (next_month_storage + expected_untaxed) > 1020.0:
          if net_monthly+(expected_pumping['untaxed'][month_evaluate] - expected_pumping['gains'][month_evaluate]) > 0.0:
            partial_month_remaining = max(1 - max(next_month_storage + expected_untaxed - 1020.0, 0.0)/(net_monthly+(expected_pumping['untaxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])), 0.0)*self.days_in_month[year_index+cross_counter_y][month_evaluate]

          numdays_fillup = min(numdays_fillup,total_days_remaining + partial_month_remaining)
          if cross_counter_wy == 1:
            numdays_fillup_next_year = min(numdays_fillup_next_year, total_days_remaining + partial_month_remaining)
        else:
          numdays_fillup = min(numdays_fillup, 999.9)#reservoir does not fill up in this condition (if it was full in prior loop months, retains its value)
        if next_month_storage + expected_untaxed > 1020.0:
          pumping_toggle = min(0, pumping_toggle)
          tax_free_toggle = min(0, tax_free_toggle)
        elif next_month_storage + expected_taxed > 1020.0:
          pumping_toggle = min(0, pumping_toggle)
          tax_free_toggle = min(0, tax_free_toggle)
        else:
          pumping_toggle = min(1, pumping_toggle)
          tax_free_toggle = min(1, tax_free_toggle)
      else:
        article21 = max(0.0, article21)
        pumping_toggle = min(0, pumping_toggle)
        tax_free_toggle = min(0, tax_free_toggle)
        #article21 flows are the expected extra flows divided by the number of days until the end of the month
        numdays_fillup = min(numdays_fillup,total_days_remaining+partial_month_remaining)
        if cross_counter_wy == 1:
          numdays_fillup_next_year = min(numdays_fillup_next_year, total_days_remaining + partial_month_remaining)
		
	    ##note - beginning month = m; looped month = month_evaluate
		   		   
      ##After we calculate what the pumping for SL based off projections from this month, we step the month
      ##forward and project new storage & pumping for the next month, and re-evaluate all releases.  From Oct-Mar, if
      ##any month triggers the pumping to stop, the pumping stops.  From June-Sept, if any month triggers the pumping, the
	    ##pumping occurs
      month_evaluate += 1
      if month_evaluate > 11:
        month_evaluate = 0
        cross_counter_y = 1
        carryover_adjust = projected_carryover
      if month_evaluate == m-1:
        end_counter = 1
     		
      if next_month_storage < 0.0 and cross_counter_y == 0:
        tax_free_toggle_override = 1
      if m == 7 or m == 8 or m == 9:
        tax_free_toggle_override = 1
      if month_evaluate == 9:
        expected_untaxed = max(expected_untaxed + min(next_month_storage, 0.0), 0.0)
        available_storage += min(next_month_storage, 0.0)
        if m < 4 or m > 9 or key == 'cvp':
          next_month_storage = max(next_month_storage, 0.0)
        else:
          next_month_storage = max(next_month_storage, 0.0)
        carryover_adjust = projected_carryover
        cross_counter_wy = 1

      expected_demands = (month_demand[wyt][month_evaluate] + month_demand_must_fill[wyt][month_evaluate])/self.days_in_month[year_index+cross_counter_y][month_evaluate]
      expected_inflow = expected_pumping['gains'][month_evaluate]/self.days_in_month[year_index+cross_counter_y][month_evaluate]
      expected_untaxed += (expected_pumping['untaxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])
      expected_taxed += (expected_pumping['taxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])
	    #how much 'unstored' pumping can we expect into San Luis?
      #self.month_averages comes from self.predict_delta_gains
	    #proj_surplus & proj_surplus2 are generated in the northern model, from 8RI regression in self.predict_delta_gains
      if month_evaluate == 3 or month_evaluate == 4:
        expected_inflow = 0.75
      #expected monthly change in san luis storage
      net_monthly = (expected_inflow - expected_demands)*self.days_in_month[year_index+cross_counter_y][month_evaluate]
      total_days_remaining += this_month_days
      this_month_days = self.days_in_month[year_index+cross_counter_y][month_evaluate]

    return max(pumping_toggle, pumping_toggle_override), max(tax_free_toggle, tax_free_toggle_override), article21, numdays_fillup, numdays_fillup_next_year
      
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
#############################  State Variables that use data from more than one obejct class#########################
#####################################################################################################################	  
  def project_urban_pumping(self, da, dowy, m, wateryear, year_index, total_delta_pumping, projected_allocation_cvp, sri):
    cdef District district_obj
    cdef Private private_obj

    urban_list = [self.socal, self.centralcoast, self.southbay]
    projected_allocation = {}
    projected_allocation['swp'] = total_delta_pumping
    projected_allocation['cvp'] = projected_allocation_cvp
    if dowy == 0:
      for x in range(0, len(self.socal.hist_demand_dict['annual_sorted'][dowy])):
        if total_delta_pumping < self.socal.hist_demand_dict['annual_sorted'][dowy][x]:
          break
      self.k_close_wateryear = np.random.randint(0, len(self.socal.hist_demand_dict['sorted_index'][dowy]))

    for district_obj in urban_list:
      #sri_estimate = (total_delta_pumping*district_obj.delivery_percent_coefficient[0][dowy][0] + district_obj.delivery_percent_coefficient[0][dowy][1] - district_obj.regression_errors[0][dowy][self.k_close_wateryear])*total_delta_pumping
      sri_estimate = (total_delta_pumping*district_obj.delivery_percent_coefficient[0][dowy][0] + district_obj.delivery_percent_coefficient[0][dowy][1])*total_delta_pumping
      district_obj.annualdemand[0] = max(sri_estimate - x.ytd_pumping[0][wateryear], 0.0)
    for private_obj in self.city_list:
      for district_key in private_obj.district_list:
        #sri_estimate = (total_delta_pumping*x.delivery_percent_coefficient[district_key][dowy][0] + private_obj.delivery_percent_coefficient[district_key][dowy][1] - private_obj.regression_errors[district_key][dowy][self.k_close_wateryear])*total_delta_pumping
        sri_estimate = (total_delta_pumping*private_obj.delivery_percent_coefficient[district_key][dowy][0] + private_obj.delivery_percent_coefficient[district_key][dowy][1])*total_delta_pumping
        private_obj.annualdemand[district_key] = max(sri_estimate - private_obj.ytd_pumping[district_key][wateryear], 1.0)

    if da == 1:
    
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        for district_obj in urban_list:
          district_obj.monthlydemand[wyt] = np.zeros(12)
      for private_obj in self.city_list:
        private_obj.monthlydemand = {}
        for district_key in private_obj.district_list:
          private_obj.monthlydemand[district_key] = {}
          for wyt in ['W', 'AN', 'BN', 'D', 'C']:
            private_obj.monthlydemand[district_key][wyt] = np.zeros(12)


      start_of_month = 0
      ###Divide aqueduct branch pumping into 'monthly demands'
      for monthloop in range(0,12):
        monthcounter = monthloop + 9
        if monthcounter > 11:
          monthcounter -= 12
        if monthcounter < m-1:
          cross_counter_y = 1
        else:
          cross_counter_y = 0
        start_next_month = self.dowy_eom[year_index+cross_counter_y][monthcounter] + 1
        for wyt in ['W', 'AN', 'BN', 'D', 'C']:
          for district_obj in urban_list:
            #sri_estimate = (total_delta_pumping*district_obj.delivery_percent_coefficient[0][dowy][0] + district_obj.delivery_percent_coefficient[0][dowy][1] - district_obj.regression_errors[0][dowy][self.k_close_wateryear])*total_delta_pumping
            sri_estimate = (total_delta_pumping*district_obj.delivery_percent_coefficient[0][dowy][0] + district_obj.delivery_percent_coefficient[0][dowy][1])*total_delta_pumping
            #if monthcounter >= 9:
              #if wateryear > 0:
                #district_obj.monthlydemand[wyt][monthcounter] += np.mean(district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][start_of_month:start_next_month])*max(district_obj.ytd_pumping[0][wateryear-1], 0.0)
              #else:
                #district_obj.monthlydemand[wyt][monthcounter] += np.mean(district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][start_of_month:start_next_month])*max(district_obj.initial_pumping, 0.0)
            #else:
            district_obj.monthlydemand[wyt][monthcounter] += np.mean(district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][start_of_month:start_next_month])*max(sri_estimate - district_obj.ytd_pumping[0][wateryear], 0.0)
          
          for private_obj in self.city_list:
            for district_keys in private_obj.district_list:
                # district_obj = self.district_keys[private_obj]
                #sri_estimate = (total_delta_pumping*private_obj.delivery_percent_coefficient[private_obj][dowy][0] + private_obj.delivery_percent_coefficient[private_obj][dowy][1] - private_obj.regression_errors[private_obj][dowy][self.k_close_wateryear])*total_delta_pumping
                sri_estimate = (total_delta_pumping*private_obj.delivery_percent_coefficient[private_obj][dowy][0] + private_obj.delivery_percent_coefficient[private_obj][dowy][1])*total_delta_pumping
              #if monthcounter >= 9:
                #if wateryear > 0:
                  #private_obj.monthlydemand[private_obj][wyt][monthcounter] += np.mean(self.district_keys[private_obj].hist_demand_dict['daily_fractions'][self.k_close_wateryear][start_of_month:start_next_month])*max(private_obj.ytd_pumping[private_obj][wateryear-1], 0.0)
                #else:
                  #private_obj.monthlydemand[private_obj][wyt][monthcounter] += np.mean(self.district_keys[private_obj].hist_demand_dict['daily_fractions'][self.k_close_wateryear][start_of_month:start_next_month])max(private_obj.initial_pumping[private_obj], 0.0)
              #else:
                private_obj.monthlydemand[private_obj][wyt][monthcounter] += np.mean(self.district_keys[private_obj].hist_demand_dict['daily_fractions'][self.k_close_wateryear][start_of_month:start_next_month])*max(sri_estimate - private_obj.ytd_pumping[private_obj][wateryear], 0.0)

        start_of_month = start_next_month

    for district_obj in urban_list:
      district_obj.dailydemand[0] = 0.0

      #sri_estimate = (total_delta_pumping*district_obj.delivery_percent_coefficient[0][dowy][0] + district_obj.delivery_percent_coefficient[0][dowy][1] - district_obj.regression_errors[0][dowy][self.k_close_wateryear])*total_delta_pumping
      sri_estimate = (total_delta_pumping*district_obj.delivery_percent_coefficient[0][dowy][0] + district_obj.delivery_percent_coefficient[0][dowy][1])*total_delta_pumping
      #if monthcounter >= 9:
        #if wateryear > 0:
          #district_obj.dailydemand[0] += max(district_obj.ytd_pumping[0][wateryear-1], 0.0)*district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
          #district_obj.dailydemand_start[0] += max(district_obj.ytd_pumping[0][wateryear-1], 0.0)*district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
        #else:
          #district_obj.dailydemand[0] += max(district_obj.initial_pumping, 0.0)*district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
          #district_obj.dailydemand_start[0] += max(district_obj.initial_pumping, 0.0)*district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
      #else:
      district_obj.dailydemand[0] += max(sri_estimate - district_obj.ytd_pumping[0][wateryear], 0.0)*district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
      district_obj.dailydemand_start[0] += max(sri_estimate - district_obj.ytd_pumping[0][wateryear], 0.0)*district_obj.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]

      district_obj.ytd_pumping[0][wateryear] += district_obj.dailydemand[0]

    for private_obj in self.city_list:
      for district_keys in private_obj.district_list:
        private_obj.dailydemand[district_keys] = 0.0
        # district_obj = self.district_keys[district_keys]
        #sri_estimate = (total_delta_pumping*private_obj.delivery_percent_coefficient[district_keys][dowy][0] + private_obj.delivery_percent_coefficient[district_keys][dowy][1] - private_obj.regression_errors[district_keys][dowy][self.k_close_wateryear])*total_delta_pumping
        sri_estimate = (total_delta_pumping*private_obj.delivery_percent_coefficient[district_keys][dowy][0] + private_obj.delivery_percent_coefficient[district_keys][dowy][1])*total_delta_pumping
        private_obj.dailydemand[district_keys] += max(sri_estimate- private_obj.ytd_pumping[district_keys][wateryear], 0.0)*self.district_keys[district_keys].hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
        private_obj.dailydemand_start[district_keys] += max(sri_estimate -private_obj.ytd_pumping[district_keys][wateryear], 0.0)*self.district_keys[district_keys].hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
        private_obj.ytd_pumping[district_keys][wateryear] += private_obj.dailydemand[district_keys]
    

  def agg_contract_demands(self, year_index, m, wyt_real):
  #this function sums district demands by reservoir (i.e. - for each reservoir, the sum of the demand of all districts
  #with a contract that is held at that reservoir
    cdef Reservoir reservoir_obj
    cdef District district_obj
    cdef Private private_obj

    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      for reservoir_obj in self.reservoir_list:
        reservoir_obj.monthly_demand[wyt] = np.zeros(12)
        reservoir_obj.monthly_demand_full[wyt] = np.zeros(12)
        reservoir_obj.monthly_demand_must_fill[wyt] = np.zeros(12)
        for district_obj in self.district_list: 
          total_alloc = 0.0
          for i in range(len(self.reservoir_contract[reservoir_obj.key])):
            if reservoir_obj.key == "MIL":
              if district_obj.annualdemand[0] > 0.0:
                total_frac = min(max(district_obj.project_contract['friant1']*self.friant1.total,0.0)/district_obj.annualdemand[0], 1.0)
              else:
                total_frac = 0.0
            elif reservoir_obj.key == 'PFT':
              if district_obj.annualdemand[0] > 0.0:
                total_frac = min(max(district_obj.projected_supply['kings']/district_obj.annualdemand[0],0.0), 1.0)
              else:
                total_frac = 0.0	
            elif reservoir_obj.key == 'KWH':
              if district_obj.annualdemand[0] > 0.0:
                total_frac = min(max(district_obj.projected_supply['kaweah']/district_obj.annualdemand[0],0.0), 1.0)
              else:
                total_frac = 0.0			  
            else:
              total_frac = 1.0
          if district_obj.reservoir_contract[reservoir_obj.key] == 1:
            for monthcounter in range(0,12):
              if monthcounter >= m-1:
                daysmonth = self.days_in_month[year_index][monthcounter]
              else:
                daysmonth = self.days_in_month[year_index+1][monthcounter]
              if district_obj.must_fill == 1:
                reservoir_obj.monthly_demand_must_fill[wyt][monthcounter] += district_obj.monthlydemand[wyt][monthcounter]*daysmonth
              else:
                reservoir_obj.monthly_demand[wyt][monthcounter] += district_obj.monthlydemand[wyt][monthcounter]*daysmonth*total_frac
                reservoir_obj.monthly_demand_full[wyt][monthcounter] += district_obj.monthlydemand[wyt][monthcounter]*daysmonth

        for private_obj in self.private_list:
          total_alloc = 0.0
          total_frac = {}
          for district_key in private_obj.district_list:
            for contract_key in (_.name for _ in self.reservoir_contract[reservoir_obj.key]):
              total_alloc += private_obj.projected_supply[district_key][contract_key]
            if private_obj.annualdemand[district_key] > 0.0:
              total_frac[district_key] = min(total_alloc/private_obj.annualdemand[district_key], 1.0)
            else:
              total_frac[district_key] = 0.0
          if private_obj.reservoir_contract[reservoir_obj.key] == 1:
            for monthcounter in range(0,12):
              if monthcounter >= m-1:
                daysmonth = self.days_in_month[year_index][monthcounter]
              else:
                daysmonth = self.days_in_month[year_index+1][monthcounter]
              for district_key in private_obj.district_list:
                reservoir_obj.monthly_demand[wyt][monthcounter] += private_obj.monthlydemand[district_key][wyt][monthcounter]*daysmonth
                reservoir_obj.monthly_demand_full[wyt][monthcounter] += private_obj.monthlydemand[district_key][wyt][monthcounter]*daysmonth
				
        for private_obj in self.city_list:
          total_alloc = 0.0
          total_frac = {}
          for district_key in private_obj.district_list:
            for contract_key in (_.name for _ in self.reservoir_contract[reservoir_obj.key]):
              total_alloc += private_obj.projected_supply[district_key][contract_key]
            if private_obj.annualdemand[district_key] > 0.0:
              total_frac[district_key] = min(total_alloc/private_obj.annualdemand[district_key], 1.0)
            else:
              total_frac[district_key] = 0.0
          if private_obj.reservoir_contract[reservoir_obj.key] == 1:
            for monthcounter in range(0,12):
              if monthcounter >=m-1:
                daysmonth = self.days_in_month[year_index][monthcounter]
              else:
                daysmonth = self.days_in_month[year_index+1][monthcounter]
              for district in private_obj.district_list:
                reservoir_obj.monthly_demand[wyt][monthcounter] += private_obj.monthlydemand[district][wyt][monthcounter]*daysmonth
                reservoir_obj.monthly_demand_full[wyt][monthcounter] += private_obj.monthlydemand[district][wyt][monthcounter]*daysmonth
				
        for monthcounter in range(0,12):
          if monthcounter >= m-1:
            daysmonth = self.days_in_month[year_index][monthcounter]
          else:
            daysmonth = self.days_in_month[year_index + 1][monthcounter]
          if reservoir_obj.monthly_demand[wyt][monthcounter] > reservoir_obj.total_capacity*cfs_tafd*daysmonth:
            reservoir_obj.monthly_demand[wyt][monthcounter] = reservoir_obj.total_capacity*cfs_tafd*daysmonth
          if reservoir_obj.monthly_demand_full[wyt][monthcounter] > reservoir_obj.total_capacity*cfs_tafd*daysmonth:
            reservoir_obj.monthly_demand_full[wyt][monthcounter] = reservoir_obj.total_capacity*cfs_tafd*daysmonth
              			  

  def appropriate_carryover(self, forgone, key, wateryear):
  #if pumping is turned 'off' because of san luis storage conditions,
	#any carryover water (up to the total potential pumping) is taken from the individual
	#district that owned it and redistributed to all districts as this year's allocation
    cdef Contract contract_obj
    cdef District district_obj
    cdef Private private_obj

    remaining_carryover = {}
    remaining_balance = {}
    for contract_obj in self.reservoir_contract[key]:
      remaining_carryover[contract_obj.name] = 0.0
      remaining_balance[contract_obj.name] = 0.0
    for district_obj in self.district_list:
      #find total amount of carryover that has not yet been delivered, by contract
      for contract_key in remaining_carryover:
        remaining_carryover[contract_key] += max(district_obj.carryover[contract_key] - district_obj.deliveries[contract_key][wateryear], 0.0)
    for private_obj in self.private_list:
      for contract_key in remaining_carryover:
        for district_key in private_obj.district_list:
          remaining_carryover[contract_key] += max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)
    for private_obj in self.city_list:
      for contract_key in remaining_carryover:
        for district_key in private_obj.district_list:
          remaining_carryover[contract_key] += max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)
	
    total_remaining = 0.0
    for contract_key in remaining_carryover:
      #total the carryover for each contract at that reservoir
      total_remaining += remaining_carryover[contract_key]
    if total_remaining > 0.0:
      #what % of carryover needs to be taken
      carryover_fraction = min(forgone/total_remaining, 1.0)
      for contract_key in remaining_carryover:
        current_contract = self.contract_keys[contract_key]
        #carryover contracts canceled
        current_contract.tot_carryover -= remaining_carryover[contract_key]*carryover_fraction
        #'new allocation' credited to the contract
        self.pumping_turnback[key] -= remaining_carryover[contract_key]*carryover_fraction
        for district_obj in self.district_list:
          district_obj.carryover[contract_key] -= max(district_obj.carryover[contract_key] - district_obj.deliveries[contract_key][wateryear], 0.0)*carryover_fraction
        for private_obj in self.private_list:
          for district_key in private_obj.district_list:
            private_obj.carryover[district_key][contract_key] -= max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)*carryover_fraction
        for private_obj in self.city_list:
          for district_key in private_obj.district_list:
            private_obj.carryover[district_key][contract_key] -= max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)*carryover_fraction
		  

  def update_carryover(self, spill, key, wateryear):
  #This function is meant to take a flood release and subtract it either from
  #existing carryover or projected contract deliveries
    cdef Canal canal_obj
    cdef Contract contract_obj
    cdef District district_obj
    cdef Private private_obj

    remaining_carryover = {}
    carryover_fraction = 0.0
    #loop through the canals associated with the reservoir, 'key'
    for canal_obj in self.reservoir_canal[key]:
      #what contracts are deliveried on that canal
      for contract_obj in self.canal_contract[canal_obj.name]:
        #initialize remaining carryover variable
		    #this also makes a list of all contracts w/carryover (for looping later)
        remaining_carryover[contract_obj.name] = 0.0
		
    #find total carryover (district carryover balances that have not yet been delivered)
    for district_obj in self.district_list:
      for contract_key in remaining_carryover:
        remaining_carryover[contract_key] += max(district_obj.carryover[contract_key] - district_obj.deliveries[contract_key][wateryear], 0.0)
    for private_obj in self.private_list:
      for contract_key in remaining_carryover:
        for district_key in private_obj.district_list:
          remaining_carryover[contract_key] += max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)
    for private_obj in self.city_list:
      for contract_key in remaining_carryover:
        for district_key in private_obj.district_list:
          remaining_carryover[contract_key] += max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)
	
    #sum carryover in all contracts on that reservoir
    total_remaining = 0.0
    for contract_key in remaining_carryover:#loop over all contracts w/carryover balances
      total_remaining += remaining_carryover[contract_key]
	  
    #if there is carryover - what % needs to be taken to make up for spillage
    if total_remaining > 0.0:
      carryover_fraction = min(spill/total_remaining, 1.0)
	  
      #if there is more spill than remaining carryover, need to add to the contract adjustment (this amount is subtracted from total contract allocation)
      self.allocation_losses[key] += max(spill - total_remaining*carryover_fraction, 0.0)
      self.allocation_losses[key] += max(spill - total_remaining*carryover_fraction, 0.0)
	  
      for contract_key in remaining_carryover:#loop over all contracts w/carryover balances
        #reduce overall contract carryover balance
        current_contract = self.contract_keys[contract_key]
        current_contract.tot_carryover -= remaining_carryover[contract_key]*carryover_fraction
        #reduce individual contract carryover balance (only on undelivered carryover
        for district_obj in self.district_list:
          district_obj.carryover[contract_key] -= max(district_obj.carryover[contract_key] - district_obj.deliveries[contract_key][wateryear], 0.0)*carryover_fraction
        for private_obj in self.private_list:
          for district_key in private_obj.district_list:
            private_obj.carryover[district_key][contract_key] -= max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)*carryover_fraction
        for private_obj in self.city_list:
          for district_key in private_obj.district_list:
            private_obj.carryover[district_key][contract_key] -= max(private_obj.carryover[district_key][contract_key] - private_obj.deliveries[district_key][contract_key][wateryear], 0.0)*carryover_fraction
			
    else:
      #if no carryover, just add the spill to the contract adjustment (this amount is subtracted from total contract allocation)
      self.allocation_losses[key] += max(spill, 0.0)    		


  def find_recharge_bank(self,m,wyt):  
  ###this function projects the total GW recharge
  ###capacity in each waterbank out 12 months, and then allocates
  ###that capacity to individual districts based on their
  ###ownership stake in teh waterbank
    cdef Waterbank waterbank_obj
    cdef District district_obj
    cdef Private private_obj
    cdef Reservoir reservoir_obj

    for waterbank_obj in self.waterbank_list:
      ##direct recharge capacity is directly related to
      ##how long the banks have been used continuously
      #this month use tracks if the bank has been used in the past month
      if waterbank_obj.thismonthuse == 1:
        waterbank_obj.monthusecounter += 1
        waterbank_obj.monthemptycounter = 0
        if waterbank_obj.monthusecounter > 11:
          waterbank_obj.monthusecounter = 11
        #this function describes how recharge rate declines over time
        waterbank_obj.recharge_rate *= waterbank_obj.recharge_decline[waterbank_obj.monthusecounter]
      else:
      #in order for recharge rate to 'bounce back', needs 3 months of 
      #continuous non-use
        waterbank_obj.monthemptycounter += 1
        if waterbank_obj.monthemptycounter == 3:
          waterbank_obj.monthusecounter = 0
          waterbank_obj.recharge_rate = waterbank_obj.initial_recharge*cfs_tafd
      waterbank_obj.thismonthuse = 0
      #if m == 10:
        #waterbank_obj.recharge_rate = waterbank_obj.initial_recharge*cfs_tafd
	    ###distribute this recharge capacity among districts (based on ownership share)
      for participant_key in waterbank_obj.participant_list:
        num_districts = self.district_keys_len[participant_key]
        if self.district_keys[participant_key].is_District == 1:
          district_obj = self.district_keys[participant_key]
          participant_obj = district_obj
        elif self.district_keys[participant_key].is_Private == 1:
          private_obj = self.district_keys[participant_key]
          participant_obj = private_obj

        participant_obj.total_banked_storage += waterbank_obj.banked[participant_key]
        participant_obj.max_direct_recharge[0] += waterbank_obj.ownership[participant_key]*waterbank_obj.recharge_rate/num_districts
        for reservoir_obj in self.reservoir_list:
          if participant_obj.reservoir_contract[reservoir_obj.key] == 1:
            reservoir_obj.max_direct_recharge[0] += waterbank_obj.ownership[participant_key]*waterbank_obj.recharge_rate/num_districts
        ##each month of consecutive use results in the recharge capacity of the bank declining
        ##we want to know what is the recharge capacity available in the future, considering 
        ##continuous use from this point on
        decline_coef = 1.0
        for m_counter in range(1,12):
          decline_counter = waterbank_obj.monthusecounter + m_counter
          if decline_counter > 11:
            decline_counter = 11
          decline_coef *= waterbank_obj.recharge_decline[decline_counter]
          participant_obj.max_direct_recharge[m_counter] += waterbank_obj.ownership[participant_key]*waterbank_obj.recharge_rate*decline_coef/num_districts
          for reservoir_obj in self.reservoir_list:
            if participant_obj.reservoir_contract[reservoir_obj.key] == 1:
              reservoir_obj.max_direct_recharge[m_counter] += waterbank_obj.ownership[participant_key]*waterbank_obj.recharge_rate*decline_coef/num_districts
        

  def find_leiu_exchange(self, wateryear, dowy):
    cdef District district_obj, leiu_obj
    cdef Contract contract_obj

    for leiu_obj in self.leiu_list:
      for participant_key in leiu_obj.participant_list:
        if self.district_keys[participant_key].is_District == 1:
          district_obj = self.district_keys[participant_key]
          participant_obj = district_obj
        elif self.district_keys[participant_key].is_Private == 1:
          private_obj = self.district_keys[participant_key]
          participant_obj = private_obj

        for contract_key in leiu_obj.contract_list:
          for contract_key2 in participant_obj.contract_list:
            if contract_key2 == contract_key:
              if dowy < 180:
                contract_obj = self.contract_keys[contract_key]
                if contract_obj.type == 'right':
                  participant_obj.max_leiu_exchange += max(leiu_obj.rights[contract_key]['capacity'] * contract_obj.total * leiu_obj.leiu_ownership[participant_key], 0.0)
                else:
                  participant_obj.max_leiu_exchange += max(leiu_obj.project_contract[contract_key] * contract_obj.total * leiu_obj.leiu_ownership[participant_key], 0.0)
              else:
                participant_obj.max_leiu_exchange += max(leiu_obj.projected_supply[contract_key] * leiu_obj.leiu_ownership[participant_key], 0.0)
			  

  def find_recharge_leiu(self,m,wyt):
  ###this function projects the total GW recharge
  ###capacity in each in-leiu banking district out 12 months, and then allocates
  ###that capacity to individual districts based on their
  ###ownership stake in teh waterbank
    cdef District district_obj, leiu_obj
    cdef Private private_obj
    cdef Reservoir reservoir_obj

    #in-leiu banks combine both direct and in-leiu recharge
    #capacity, so both must be forecasting moving forward (12 months)	
    for leiu_obj in self.leiu_list:
      if leiu_obj.thismonthuse == 1:
        leiu_obj.monthusecounter += 1
        leiu_obj.monthemptycounter = 0
        if leiu_obj.monthusecounter > 11:
          leiu_obj.monthusecounter = 11
        leiu_obj.recharge_rate *= leiu_obj.recharge_decline[leiu_obj.monthusecounter]
      else:
        leiu_obj.monthemptycounter += 1
        leiu_obj.recharge_rate += max(leiu_obj.in_district_direct_recharge*cfs_tafd - leiu_obj.recharge_rate, 0.0)*0.5
        if leiu_obj.monthemptycounter == 3:
          leiu_obj.monthusecounter = 0
          leiu_obj.recharge_rate = leiu_obj.in_district_direct_recharge*cfs_tafd
      leiu_obj.thismonthuse = 0
      if m == 10:
        leiu_obj.recharge_rate = leiu_obj.in_district_direct_recharge*cfs_tafd
	  
      ##find district share of recharge capacity
      bank_total_supply = 0.0
      for contract_key in leiu_obj.contract_list:
        bank_total_supply += leiu_obj.projected_supply[contract_key]
      if leiu_obj.key == "SMI":
        for participant_key in leiu_obj.participant_list:
          num_districts = self.district_keys_len[participant_key]
          if self.district_keys[participant_key].is_District == 1:
            district_obj = self.district_keys[participant_key]
            participant_obj = district_obj
          elif self.district_keys[participant_key].is_Private == 1:
            private_obj = self.district_keys[participant_key]
            participant_obj = private_obj
          
          #current direct recharge
          participant_obj.max_direct_recharge[0] += leiu_obj.leiu_ownership[participant_key]*leiu_obj.recharge_rate/num_districts
          #current in leiu recharge (based on irrigation demands of the in-leiu bank)
          if leiu_obj.inleiubanked[participant_key] < leiu_obj.inleiucap[participant_key]:
            participant_obj.max_leiu_recharge[0] += leiu_obj.leiu_ownership[participant_key]*leiu_obj.monthlydemand[wyt][m-1]*(1.0 - min(bank_total_supply/leiu_obj.annualdemand[0], 1.0))/num_districts

          for reservoir_obj in self.reservoir_list:
            if participant_obj.reservoir_contract[reservoir_obj.key] == 1:
              if leiu_obj.inleiubanked[participant_key] < leiu_obj.inleiucap[participant_key]:
                reservoir_obj.max_direct_recharge[0] += leiu_obj.leiu_ownership[participant_key]*leiu_obj.recharge_rate/num_districts
      
          ##each month of consecutive use results in the recharge capacity of the bank declining
          ##we want to know what is the recharge capacity available in the future, considering 
          ##continuous use from this point on
          decline_coef = 1.0
          for m_counter in range(1,12):
            decline_counter = leiu_obj.monthusecounter + m_counter
            future_month = m - 1 + m_counter
            if future_month > 11:
              future_month -= 12
            if decline_counter > 12:
              decline_counter = 12
            decline_coef *= leiu_obj.recharge_decline[decline_counter]
            #future (12 months) direct recharge
            participant_obj.max_direct_recharge[m_counter] += leiu_obj.leiu_ownership[participant_key]*leiu_obj.recharge_rate*decline_coef/num_districts
            #future (12 months) in leiu recharge
            if leiu_obj.inleiubanked[participant_key] < leiu_obj.inleiucap[participant_key]:
              participant_obj.max_leiu_recharge[m_counter] += leiu_obj.leiu_ownership[participant_key]*leiu_obj.monthlydemand[wyt][future_month]*(1.0 - min(bank_total_supply/leiu_obj.annualdemand[0], 1.0))/num_districts
            for reservoir_obj in self.reservoir_list:
              if participant_obj.reservoir_contract[reservoir_obj.key] == 1:
                if leiu_obj.inleiubanked[participant_key] < leiu_obj.inleiucap[participant_key]:
                  reservoir_obj.max_direct_recharge[m_counter] += leiu_obj.leiu_ownership[participant_key]*leiu_obj.recharge_rate*decline_coef/num_districts


  def find_recharge_indistrict(self,m,wyt):
  ###this function projects the total GW recharge
  ###capacity within the boundaries of each district,
  ###then adds that recharge to the expected recharge from
  ###banking opportunities
    cdef District district_obj
    cdef Reservoir reservoir_obj

    for district_obj in self.district_list:
      if district_obj.in_district_storage > 0.0 and not district_obj.in_leiu_banking:
        if district_obj.thismonthuse == 1:
          district_obj.monthusecounter += 1
          district_obj.monthemptycounter = 0
          if district_obj.monthusecounter > 11:
            district_obj.monthusecounter = 11
          district_obj.recharge_rate *= district_obj.recharge_decline[district_obj.monthusecounter]
        else:
          district_obj.monthemptycounter += 1
          district_obj.recharge_rate += max(district_obj.in_district_direct_recharge*cfs_tafd - district_obj.recharge_rate, 0.0)*0.5
          if district_obj.monthemptycounter == 3:
            district_obj.monthusecounter = 0
            district_obj.recharge_rate = district_obj.in_district_direct_recharge*cfs_tafd
        district_obj.thismonthuse = 0
        if m == 10:
          district_obj.recharge_rate = district_obj.in_district_direct_recharge*cfs_tafd
      if district_obj.recharge_rate > 0.0:
        district_obj.max_direct_recharge[0] += district_obj.recharge_rate
        for reservoir_obj in self.reservoir_list:
          if district_obj.reservoir_contract[reservoir_obj.key] == 1:
            reservoir_obj.max_direct_recharge[0] += district_obj.recharge_rate

        decline_coef = 1.0
        for m_counter in range(1,12):
          decline_counter = district_obj.monthusecounter + m_counter
          if decline_counter > 12:
            decline_counter = 12
          decline_coef *= district_obj.recharge_decline[decline_counter]
          district_obj.max_direct_recharge[m_counter] += district_obj.recharge_rate*decline_coef
          for reservoir_obj in self.reservoir_list:
            if district_obj.reservoir_contract[reservoir_obj.key] == 1:
              reservoir_obj.max_direct_recharge[0] += district_obj.recharge_rate*decline_coef


  def update_leiu_capacity(self):
    cdef District district_obj, leiu_obj
    cdef Private private_obj

    #initialize individual banking partner's recovery capacity
    for leiu_obj in self.leiu_list:
      for participant_key in leiu_obj.participant_list:
        if participant_key != leiu_obj.key:
          self.district_keys[participant_key].extra_leiu_recovery = 0.0
    #find individual banking partner's (district') recovery capacity based on their total 
	  #supply in reservoirs accessable by their partners
    for leiu_obj in self.leiu_list:
      for participant_key in leiu_obj.participant_list:
          if self.district_keys[participant_key].is_District == 1:
            district_obj = self.district_keys[participant_key]
            participant_obj = district_obj
          elif self.district_keys[participant_key].is_Private == 1:
            private_obj = self.district_keys[participant_key]
            participant_obj = private_obj
          for contract_key in participant_obj.contract_list:#if the banking partner has a contract at that reservoir, they can trade water there
            for contract_key2 in leiu_obj.contract_list:
              if contract_key == contract_key2:
                participant_obj.extra_leiu_recovery += leiu_obj.projected_supply[contract_key2]*leiu_obj.leiu_trade_cap*leiu_obj.leiu_ownership[participant_key]
           						
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


#####################################################################################################################
#############################     Flood operations       ############################################################
#####################################################################################################################

	
  cdef void flood_operations(self, int t, int m, int dowy, int wateryear, Reservoir reservoir, str flow_type, int overflow_toggle, str wyt):
    ###available flood taken from reservoir step
	  ###min-daily-uncontrolled is based on reservoir forecasts & available recharge space
    #releases from the flood pool, or in anticipation of the flood releases
    #'anticipation' releases are only made if they are at least as large as the
	  #total recharge capacity at the reservoir
    cdef Canal canal_obj
    cdef double existing_flow, flood_available, flood_available_overflow, total_flood_deliveries, total_excess_flow, non_overflow_demand, \
              priority_flows, flood_deliveries, priority_flows_tot, excess_flows, total_spill
    cdef int canal_counter, canal_counter2, xxx, canal_size
    cdef str begin_key, delivery_key, demand_type
    cdef list canal_cap, type_list
    cdef dict tot_canal_demand, flood_demand, unmet_demands

    if reservoir.key == "SLS" or reservoir.key == "SLF":
      begin_key = "SNL"
    else:
      begin_key = reservoir.key
	  
    existing_flow = 0.0
    if max(reservoir.flood_flow_min, 2.0) > reservoir.min_daily_uncontrolled:
      #if reservoir.min_daily_uncontrolled < 3.0:
      flood_available = reservoir.fcr
      flood_available_overflow = 0.0
    else:
      for canal_obj in self.reservoir_canal[reservoir.key]:
        existing_flow += canal_obj.flow[1]
      flood_available = max(reservoir.fcr, reservoir.min_daily_uncontrolled + max((reservoir.monthly_demand[wyt][m-1] + reservoir.monthly_demand_must_fill[wyt][m-1])/31.0 - existing_flow, 0.0))    #if reservoir.fcr < reservoir.flood_flow_min:
      if reservoir.min_daily_overflow > 0.0:
        flood_available_overflow = reservoir.min_daily_overflow + max((reservoir.monthly_demand_full[wyt][m-1] + reservoir.monthly_demand_must_fill[wyt][m-1])/31.0 - existing_flow, 0.0)    #if reservoir.fcr < reservoir.flood_flow_min:
      else:
        flood_available_overflow = 0.0


    if flood_available > 0.0:
      delivery_key = reservoir.key + "_flood"		
	    #3 priority levels for flood flows
      #contractor - 1st priority, has contract at the reservoir being spilled
      #turnout - 2nd priority, has a turnout on a 'priority' canal for the reservoir being spilled
      #excess - 3rd priority, turnout on a non-priority canal for th ereservoir being spilled
      flood_demand = {}
      for demand_type in ['contractor', 'alternate', 'turnout', 'excess']:
        flood_demand[demand_type] = np.zeros(len(self.reservoir_canal[reservoir.key]))
        flood_demand['tot_' + demand_type] = 0.0
        	  
      ##Search for districts to take water
      ##Note: Millerton deliveries water to two seperate canals - their demands calculated seperately and split proportionally
      canal_counter = 0
      for canal_obj in self.reservoir_canal[reservoir.key]:
        #total flood deliveries on each canal to each priority type
        tot_canal_demand = self.search_canal_demand(dowy, canal_obj, begin_key, canal_obj.name, 'normal',flow_type,wateryear,'flood', {})
        for demand_type in tot_canal_demand:
          #sum priority deliveries over all canals
          flood_demand[demand_type][canal_counter] = tot_canal_demand[demand_type]
          flood_demand['tot_' + demand_type] += flood_demand[demand_type][canal_counter]
        canal_counter += 1
      canal_counter = 0
      total_flood_deliveries = 0.0
      total_excess_flow = 0.0
      canal_cap = [0.0 for _ in range(len(self.reservoir_canal[reservoir.key]))]
      canal_counter = 0
      non_overflow_demand = 0.0
      for canal_obj in self.reservoir_canal[reservoir.key]:
        canal_cap[canal_counter] = canal_obj.capacity['normal'][1]*cfs_tafd - canal_obj.flow[1]
        non_overflow_demand += min(flood_demand['contractor'][canal_counter] + flood_demand['alternate'][canal_counter], canal_cap[canal_counter])
        canal_counter += 1
      if overflow_toggle == 1:
        flood_available = max(min(flood_available, non_overflow_demand), min(flood_available_overflow, flood_available))

      canal_counter = 0
      for canal_obj in self.reservoir_canal[reservoir.key]:
        #first, determine the % of total demand at each priority level that can be fufilled
        #second, sum up the total deliveries to each canal from the reservoir
        priority_flows = 0.0
        flood_deliveries = 0.0
        priority_flows_tot = 0.0
        if overflow_toggle == 1:
          type_list = ['contractor', 'alternate', 'turnout', 'excess']
        else:
          type_list = ['contractor', 'alternate']
        for demand_type in type_list:
          if flood_demand['tot_' + demand_type] > 0.0:
            if (flood_demand[demand_type][canal_counter] + priority_flows) > canal_cap[canal_counter] and ((flood_available-priority_flows_tot)*(flood_demand[demand_type][canal_counter]/flood_demand['tot_' + demand_type])+priority_flows) > canal_cap[canal_counter]:
              if flood_demand[demand_type][canal_counter] > 0.0:
                flood_demand[demand_type + '_frac'] = min(max(canal_cap[canal_counter]-priority_flows, 0.0)/flood_demand[demand_type][canal_counter], 1.0)# the percent of demand that can be fufilled, adjusting for priority priority deliveries
              else:           
                flood_demand[demand_type + '_frac'] = 0.0# the percent of demand that can be fufilled, adjusting for priority priority deliveries
			  
              flood_deliveries += flood_demand[demand_type + '_frac']*flood_demand[demand_type][canal_counter]
              priority_flows += min(flood_demand[demand_type][canal_counter], canal_cap[canal_counter])
              canal_counter2 = 0
              for xxx in range(0,len(self.reservoir_canal[reservoir.key])):
                priority_flows_tot += min(flood_demand[demand_type][canal_counter2], canal_cap[canal_counter2])
                canal_counter2 += 1
            else:
              flood_demand[demand_type + '_frac'] = min(max(flood_available - priority_flows_tot, 0.0)/flood_demand['tot_' + demand_type], 1.0)# the percent of demand that can be fufilled, adjusting for priority priority deliveries
              priority_flows += min(flood_demand[demand_type][canal_counter], canal_cap[canal_counter])
              flood_deliveries += flood_demand[demand_type + '_frac'] * flood_demand[demand_type][canal_counter]  

              canal_counter2 = 0
              for xxx in range(0,len(self.reservoir_canal[reservoir.key])):
                priority_flows_tot += min(flood_demand[demand_type][canal_counter2], canal_cap[canal_counter2])
                canal_counter2 += 1
          else:
            flood_demand[demand_type + '_frac'] = 0.0
            priority_flows += min(flood_demand[demand_type][canal_counter], canal_cap[canal_counter])
            flood_deliveries += flood_demand[demand_type + '_frac'] * flood_demand[demand_type][canal_counter]
            canal_counter2 = 0
            for xxx in range(0,len(self.reservoir_canal[reservoir.key])):
              priority_flows_tot += min(flood_demand[demand_type][canal_counter2], canal_cap[canal_counter2])
              canal_counter2 += 1
    
        canal_size = self.canal_district_len[canal_obj.name]
        if flood_deliveries > 0.0:
          excess_flows, unmet_demands = self.distribute_canal_deliveries(dowy, canal_obj, begin_key, canal_obj.name, flood_deliveries, canal_size, wateryear, 'normal', flow_type, 'flood')
          
        else:
          excess_flows = 0.0
        canal_counter += 1
        total_flood_deliveries += flood_deliveries
        total_excess_flow += excess_flows
      #if all deliveries cannot be taken, then only need to 'spill' from the 
      #reservoir what was actually delivered (unless over the flood pool - then spill into channel (not tracked)
      total_spill = max(total_flood_deliveries - total_excess_flow, reservoir.fcr)
      reservoir.flood_spill[t] += total_spill - total_flood_deliveries + total_excess_flow
      reservoir.flood_deliveries[t] = total_flood_deliveries - total_excess_flow

      #if water is spilled, it has to be taken from existing carryover or from estimates
      #of that year's contract (b/c flood releases do not count as contract deliveries, but that
      #water is still used to estimate water availability for contract allocations)
      self.update_carryover(total_spill,reservoir.key,wateryear)
      #update storage (reservoir.fcr: flood control releases, already accounted for in reservoir water balance)
      if t < (self.T -1):
        reservoir.S[t+1] -= (total_spill - reservoir.fcr)

#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


#####################################################################################################################
######  Canal loop with capacity constraints - find demand & deliver flood/contract/recharge/recovery water #########
#####################################################################################################################

  def set_canal_direction(self, flow_type):
    ##This function determines the flow direction on the cross valley canal based on the use of the turnouts w/ the 
	##California Aqueduct, Friant-Kern Canal, and/or Kern River. 
    adjust_both_types = 1
    adjust_one_type = 0
    if flow_type == "recharge":
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[18], "normal", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.fkc.find_bi_directional(self.calaqueduct.turnout_use[15], "normal", "reverse", flow_type, 'xvc', adjust_both_types,  self.xvc.locked)
      if self.calaqueduct.turnout_use[18] > 0.0:
        self.xvc.locked = 1
      #if self.kwbcanal.capacity["reverse"][2] > 0.0:
        #self.calaqueduct.find_bi_directional(self.fkc.turnout_use[22], "normal", "normal", flow_type, 'xvc')
        #self.fkc.find_bi_directional(self.fkc.turnout_use[22], "normal", "normal", flow_type, 'xvc')
      #else:
      #self.calaqueduct.find_bi_directional(self.fkc.turnout_use[22], "reverse", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.fkc.find_bi_directional(self.fkc.turnout_use[22], "reverse", "reverse", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #if self.fkc.turnout_use[22] > 0.0:
        #self.xvc.locked = 1

      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[19], "normal", "normal", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      self.kerncanal.find_bi_directional(self.calaqueduct.turnout_use[19], "closed", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      if self.calaqueduct.turnout_use[19] > 0.0:
        self.kwbcanal.locked = 1

      #self.calaqueduct.find_bi_directional(self.kerncanal.turnout_use[5], "reverse", "normal", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      #self.kerncanal.find_bi_directional(self.kerncanal.turnout_use[5], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      #if self.kerncanal.turnout_use[5] > 0.0:
        #self.kwbcanal.locked = 1

    elif flow_type == "recovery":
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[18], "reverse", "reverse", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.fkc.find_bi_directional(self.calaqueduct.turnout_use[15], "reverse", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      self.kernriverchannel.find_bi_directional(self.calaqueduct.turnout_use[18], "reverse", "reverse", flow_type, 'xvc', adjust_one_type, self.xvc.locked)
      if self.calaqueduct.turnout_use[18] > 0.0:
        self.xvc.locked = 1

      #self.calaqueduct.find_bi_directional(self.fkc.turnout_use[22], "normal", "reverse", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.fkc.find_bi_directional(self.fkc.turnout_use[22], "normal", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.kernriverchannel.find_bi_directional(self.fkc.turnout_use[22], "normal", "reverse", flow_type, 'xvc', adjust_one_type, self.xvc.locked)
      #if self.fkc.turnout_use[22] > 0.0:
        #self.xvc.locked = 1
	  
      self.calaqueduct.find_bi_directional(self.kernriverchannel.turnout_use[4], "reverse", "reverse", flow_type, adjust_both_types, 'xvc', self.xvc.locked)
      #self.fkc.find_bi_directional(self.kernriverchannel.turnout_use[4], "reverse", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      self.kernriverchannel.find_bi_directional(self.kernriverchannel.turnout_use[4], "reverse", "normal", flow_type, 'xvc', adjust_one_type, self.xvc.locked)
      if self.kernriverchannel.turnout_use[4] > 0.0:
        self.xvc.locked = 1
	  
	  
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[19], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      self.kerncanal.find_bi_directional(self.calaqueduct.turnout_use[19], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      if self.calaqueduct.turnout_use[19] > 0.0:
        self.kwbcanal.locked = 1

      #self.calaqueduct.find_bi_directional(self.kerncanal.turnout_use[4], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      #self.kerncanal.find_bi_directional(self.kerncanal.turnout_use[4], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      #if self.kerncanal.turnout_use[5] > 0.0:
        #self.kwbcanal.locked = 1

	  
  def set_canal_range(self, flow_dir, flow_type, Canal canal, prev_canal, canal_size):
    #this function searches through the self.canal_district dictionary to find the 
    #node index range for any canal, given the flow direction on the canal and the 
    #previous or connecting canal (i.e., where the water is coming from).  If this is
    #the first canal in a search series (and the water is coming from a reservoir), this
    #function will identify that reservoir as the starting point and find the node index range
    #for a canal starting at the reservoir
    #EXAMPLE - if flow is coming from the friant-kern canal, and flowing in 'reverse' direction
    #onto the cross valley canal, this function will identify the 'starting point' on the XVC
    #as node #9 (index starts at zero) and the 'range' of flow as nodes #8-#0 (at which point the 
    #search will continue onto the california aqueduct

    total_canal = self.canal_district_len[canal.name]
    #recharge flows move down the canals starting from the reservoirs
    if flow_type == "recharge":
      for starting_point in range(len(self.canal_district[canal.name])):
        if self.canal_district[canal.name][starting_point].key == prev_canal:
          break
      if flow_dir == "normal":
        starting_point += 1
        canal_range = range(starting_point,canal_size)
      elif flow_dir == "reverse":
        starting_point -= 1
        canal_range = range(starting_point,total_canal - canal_size,-1)
      else:
        return (range(0, 0), 0.0)
		
    elif flow_type == "recovery":
      if flow_dir == "normal":
        if self.canal_district[canal.name][0].is_Reservoir:
          starting_point = 1
        else:
          starting_point = 0
        if prev_canal == "none":
          canal_range = range(starting_point, canal_size)        
        else:
          for ending_point in range(len(self.canal_district[canal.name])):
            if self.canal_district[canal.name][ending_point].key == prev_canal:
              break
          if ending_point == 0:
            if canal.recovery_feeder:
              canal_range = (0, 0)
            else:
              canal_range = range(starting_point, self.canal_district_len[canal.name])
          else:
            #ending_point -= 1			  
            canal_range = range(starting_point, ending_point)
      elif flow_dir == "reverse":
        starting_point = self.canal_district_len[canal.name] - 1
        if prev_canal == "none":
          canal_range = range(starting_point, -1, -1)
        else:
          for ending_point in range(len(self.canal_district[canal.name])):
            if self.canal_district[canal.name][ending_point].key == prev_canal:
              break
          if ending_point == (self.canal_district_len[canal.name] - 1):
            if canal.recovery_feeder:
              canal_range = (0,0)
            else:
              canal_range = range(starting_point, 0, -1)
          else:
            #ending_point += 1
            canal_range = range(starting_point, ending_point, -1)
      else:
        return(range(0, 0), 0.0)
    return canal_range, starting_point
	

  cdef tuple distribute_canal_deliveries(self, int dowy, Canal canal, str prev_canal, str contract_canal, double available_flow, int canal_size, int wateryear, str flow_dir, str flow_type, str search_type):
    cdef District district_obj, district_obj2
    cdef Private private_obj
    cdef Waterbank waterbank_obj
    cdef Canal canal_obj
    cdef double private_demand_constraint, demand_constraint, excess_flow, unmet_demand, total_demand, turnback_flow, excess_flow_int, available_capacity_int, \
              location_delivery, current_storage, deliveries, priority_bank_space, actual_deliveries, direct_deliveries, recharge_deliveries, undelivered, \
              private_delivery_constraint, delivery_to_private, turnout_available, new_excess_flow, remaining_excess_flow
    cdef int toggle_partial_delivery, toggle_district_recharge, starting_point, canal_loc, num_members, new_canal_size, turnback_end, toggle_demand_count, \
              canal_loc_int
    cdef str list_member, zz, district_key, participant_key, district2_key, contract_key
    cdef list type_list, priority_list, contract_list
    cdef dict empty_demands, type_deliveries, type_demands, type_fractions, canal_fractions, priorities, priority_turnout_adjusted, delivery_by_contract, \
              private_deliveries, canal_demands, unmet_canal_demands, unmet_demands

    if search_type == 'delivery':
      #for regular deliveries, we need to distinguish between demands from each contract
      #because the distribute_canal_deliveries and search_canal_demands functions are called
      #one reservoir at a time, there are only multiple 'types' of demand when there are more
      #than one type of contract at a reservoir
      #NOTE: as it is currently written, this implies some sort of contract 'priority' structure
      #when there are more than one type of contract at a reservoir.  Not sure if this is a valid assumption
      #or if it makes a big deal - b/c this is only for direct irrigation deliveries, and not flood/recharge water,
      #it might not be a big deal
      type_list = [contract_canal]
      # print(contract_canal, type_list)
      toggle_partial_delivery = 1
      toggle_district_recharge = 0
    elif search_type == 'flood':
      #for flood flows, need to distinguish between districts with a contract
      #to the water being spilled (1st priority), districts with a turnout on
      #a 'favored' canal (i.e, one that won't disrupt flows from other sources,
      #2nd priority), and districts with turnouts on other canals that can still
      #be technically reached from this source (3rd priority)
      type_list = ['contractor', 'alternate', 'turnout', 'excess']
      toggle_partial_delivery = 0
      toggle_district_recharge = 1
    elif search_type == 'banking':
      #banking flows need to distinguish between priority space in recharge facilities (i.e., the percentage of the facility
      #'owned' by a particular district, and secondary space, which can be used by individual districts if they are not in use
      # by the 'owner'
      type_list = ['priority', 'secondary']
      toggle_partial_delivery = 0
      toggle_district_recharge = 1
	  
    #find the range of nodes to 'search' on this canal
    if flow_dir == "closed":
      empty_demands = {}
      for list_member in type_list:
        empty_demands[list_member] = 0.0
      return available_flow, empty_demands
    else:
      canal_range, starting_point = self.set_canal_range(flow_dir, flow_type, canal, prev_canal, canal_size)

    #initialize/clear dictionaries to store demand/delivery variables needed to take
	  #the total 'available flow' and distribute it among the canal nodes
    type_deliveries = {}
    type_demands = {}
    type_fractions = {}
    for zz in type_list:
      type_deliveries[zz] = 0.0
      type_demands[zz] = 0.0
      type_fractions[zz] = 0.0

    #make sure that the available flow is less than the initial capacity of the canal
    excess_flow = 0.0
    unmet_demand = 0.0
    total_demand = 0.0
    turnback_flow = 0.0
    for canal_loc in canal_range:
      for zz in type_list:
        type_demands[zz] += canal.demand[zz][canal_loc]
        total_demand += canal.demand[zz][canal_loc]

    #if the available flow is greater than the total demand on the canal, the difference 
    #is returned by the function as 'excess flow'
    if available_flow > total_demand:
      excess_flow += available_flow - total_demand
      available_flow = total_demand
	  
    available_flow, excess_flow_int = canal.check_flow_capacity(available_flow, starting_point, flow_dir)
    excess_flow += excess_flow_int
 
    available_capacity_int = max(available_flow, 0.0)
    for zz in type_list:
      if type_demands[zz] > 0.0:
        type_fractions[zz] = max(min(available_capacity_int/type_demands[zz], 1.0), 0.0)
      else:
        type_fractions[zz] = 0.0
      available_capacity_int -= type_demands[zz]*type_fractions[zz]

    #canal priority
    priority_list = self.canal_priority[canal.name]
    #contracts on this canal
    contract_list = self.canal_contract[contract_canal]
    for district_obj in self.district_list:
      district_obj.private_demand = {}
      district_obj.private_delivery = {}
    for district_obj in self.urban_list:
      district_obj.private_demand = {}
      district_obj.private_delivery = {}
    for private_obj in self.private_list:
      for district_key in private_obj.district_list:
        private_demand_constraint = private_obj.find_node_demand(contract_list, search_type, district_key)
        self.district_keys[district_key].private_demand[private_obj.key] = private_demand_constraint
        self.district_keys[district_key].private_delivery[private_obj.key] = private_obj.set_request_to_district(private_demand_constraint,search_type,contract_list,0.0,dowy,district_key)
    for private_obj in self.city_list:
      for district_key in private_obj.district_list:
        private_demand_constraint = private_obj.find_node_demand(contract_list, search_type, district_key)
        self.district_keys[district_key].private_demand[private_obj.key] = private_demand_constraint
        self.district_keys[district_key].private_delivery[private_obj.key] = private_obj.set_request_to_district(private_demand_constraint,search_type,contract_list,0.0,dowy,district_key)


    #initial capacity check on flow available for delivery (i.e., canal capacity at starting node)
    #MAIN DISTRIBUTION LOOP - within the canal range identified above, distribute the available flow to each node based on the canal capacity and the different demand magnitudes and priorities at each node
    for canal_loc in canal_range:
      #first, find the fraction of each priority that can be diverted at this node, based on total canal demands and canal conveyance capacity
      # available_capacity_int = available_flow
      #for zz in type_list:
        #type_demands[zz] = 0.0
        #for type_loc in canal_range:
          #type_demands[zz] += canal.demand[zz][type_loc]

      #for zz in type_list:
        #find the fraction of each priority type that can be filled, based on canal capacity and downstream demands
        #if type_demands[zz] > 0.0:
          #type_fractions[zz] = max(min(available_capacity_int/type_demands[zz], 1.0), 0.0)
        #else:
          #type_fractions[zz] = 0.0
        #available_capacity_int -= type_demands[zz]*type_fractions[zz]
        #type_demands[zz] -= canal.demand[zz][canal_loc]

      # #find type of the object at the current node
      if self.canal_district[canal.name][canal_loc].is_Waterbank == 1:
        #find the object at the current node
        waterbank_obj = self.canal_district[canal.name][canal_loc]
        location_delivery = 0.0

        #for waterbanks, we calculate the demands of each waterbank partner individually
        for participant_key in waterbank_obj.participant_list:
          num_members = self.district_keys_len[participant_key]
          if self.district_keys[participant_key].is_District == 1:
            district_obj2 = self.district_keys[participant_key]
            participant_obj = district_obj2
          elif self.district_keys[participant_key].is_Private == 1:
            private_obj = self.district_keys[participant_key]
            participant_obj = private_obj

          #find waterbank partner demand (i.e., recharge capacity of their ownership share)
          demand_constraint = waterbank_obj.find_node_demand(contract_list, participant_key, num_members, search_type)
          #find how much water is allocated to each priority demand based on the total space and turnout at this node
          current_storage = sum((waterbank_obj.storage[_] for _ in waterbank_obj.participant_list))
          canal_fractions = canal.find_priority_fractions(waterbank_obj.tot_storage - current_storage, type_fractions, type_list, canal_loc, flow_dir)
          #does this partner want to bank water?
          #find if banking partner wants to bank water
          deliveries =  participant_obj.set_request_constraints(demand_constraint, search_type, contract_list, waterbank_obj.banked[participant_key], waterbank_obj.bank_cap[participant_key], dowy, wateryear)
            #flood deliveries to bank
            #deliveries = waterbank_obj.set_request_constraints(demand_constraint, search_type, contract_list)
          #what priority does their banked water have (can be both)
          priority_bank_space = waterbank_obj.find_priority_space(num_members, participant_key, search_type)
          priorities = waterbank_obj.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal, canal.name, participant_obj.contract_list)
          #need to adjust the water request to account for the banking partner share of the turnout
          priority_turnout_adjusted = {}
          for zz in type_list:
            priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][canal_loc]
          #deliver water to the waterbank
          actual_deliveries = waterbank_obj.set_deliveries(priority_turnout_adjusted,canal_fractions,type_list,participant_key)
          #keep track of total demands at this node
          location_delivery += actual_deliveries
          #adjust accounts for overall contracts and invididual districts
          delivery_by_contract = participant_obj.adjust_accounts(0.0, actual_deliveries,contract_list, search_type, wateryear, waterbank_obj.key)

          for contract_key in delivery_by_contract:
            #update the accounting for deliveries made by each contract (overall contract accounting - not ind. district)
            # contract_object = self.contract_keys[contract_keyy]
            self.contract_keys[contract_key].adjust_accounts(delivery_by_contract[contract_key], search_type, wateryear)
    
        #find new banking demands
        self.find_node_demand_bank(waterbank_obj, canal, canal_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        current_storage = sum((waterbank_obj.storage[_] for _ in waterbank_obj.participant_list))
        # current_storage = 0.0
        # for participant_key in waterbank_obj.participant_list:
        #   current_storage += waterbank_obj.storage[participant_key]

        canal.find_turnout_adjustment(waterbank_obj.tot_storage - current_storage, flow_dir, canal_loc, type_list)


      # #find type of the object at the current node
      elif self.canal_district[canal.name][canal_loc].is_District == 1:
        #find the object at the current node
        district_obj = self.canal_district[canal.name][canal_loc]
        location_delivery = 0.0
      
        #find demand at the node
        #partial delivery is used if the district recieves less than full daily demand due to projected contract allocations being lower than expected remaining annual demand
        #find district demand at the node
        if search_type == "recovery":
          demand_constraint = district_obj.find_node_output()
        else:
          demand_constraint = district_obj.find_node_demand(contract_list, search_type, toggle_partial_delivery, toggle_district_recharge)
        #update the fractions based on turnout capacity/use capacity at the current node

        canal_fractions = canal.find_priority_fractions(demand_constraint, type_fractions, type_list, canal_loc, flow_dir)
        #if a district is an in-leiu bank, partners can send water to this district for banking recharge
        if (district_obj.in_leiu_banking and search_type == "banking") or (district_obj.in_leiu_banking and search_type == "recovery"):
          for participant_key in district_obj.participant_list:
            num_members = self.district_keys_len[participant_key]
            if self.district_keys[participant_key].is_District == 1:
              district_obj2 = self.district_keys[participant_key]
              participant_obj = district_obj2
            elif self.district_keys[participant_key].is_Private == 1:
              private_obj = self.district_keys[participant_key]
              participant_obj = private_obj
              
            #find if the banking partner wants to bank
            deliveries = participant_obj.set_request_constraints(demand_constraint, search_type, contract_list, district_obj.inleiubanked[participant_key], district_obj.inleiucap[participant_key], dowy, wateryear)
            #determine the priorities of the banking
            priority_bank_space = district_obj.find_leiu_priority_space(demand_constraint, num_members, participant_key, toggle_district_recharge, search_type)
            priorities = participant_obj.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal)

            #need to adjust the water request to account for the banking partner share of the turnout
            priority_turnout_adjusted = {}
            for zz in type_list:
              priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][canal_loc]
            #make deliveries, adjust demands & recharge availability
            direct_deliveries, recharge_deliveries, undelivered = district_obj.set_deliveries(priority_turnout_adjusted,canal_fractions,type_list,search_type, toggle_district_recharge,participant_key,wateryear)
            actual_deliveries = direct_deliveries + recharge_deliveries
            location_delivery += actual_deliveries
            #adjust accounts for overall contracts and invididual districts
            delivery_by_contract = participant_obj.adjust_accounts(direct_deliveries, recharge_deliveries,contract_list, search_type, wateryear, district_obj.key)
            district_obj.adjust_bank_accounts(participant_key, direct_deliveries, recharge_deliveries, wateryear)
            for contract_key in delivery_by_contract:
              self.contract_keys[contract_key].adjust_accounts(delivery_by_contract[contract_key], search_type, wateryear)
        else:
          #find if district wants to purchase this type of flow
          deliveries =  district_obj.set_request_constraints(demand_constraint, search_type, contract_list, 0.0, 999.0, dowy, wateryear)
          #find what priority district has for flow purchases
          priorities = district_obj.set_demand_priority(priority_list, contract_list, demand_constraint, deliveries, demand_constraint, search_type, contract_canal)
          priority_turnout_adjusted = {}
          #need to adjust the water request to account for the banking partner share of the turnout
          for zz in type_list:
            priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][canal_loc]
          #make deliveries, adjust demands & recharge availability
          direct_deliveries, recharge_deliveries, undelivered = district_obj.set_deliveries(priority_turnout_adjusted,canal_fractions,type_list,search_type,toggle_district_recharge,'none',wateryear)
          # actual_deliveries = direct_deliveries + recharge_deliveries
          #adjust accounts for overall contracts and invididual districts
          if district_obj.has_private:
            for private_obj in self.private_list:
              for district2_key in private_obj.district_list:
                if district2_key == district_obj.key:
                  private_demand_constraint = private_obj.find_node_demand(contract_list, search_type, district2_key)
                  private_delivery_constraint = private_obj.set_request_to_district(private_demand_constraint,search_type,contract_list,0.0,dowy,district2_key)
                  delivery_to_private = min(private_demand_constraint, private_delivery_constraint,undelivered)
                  undelivered -= delivery_to_private
                  private_deliveries = private_obj.adjust_account_district(delivery_to_private,contract_list,search_type,wateryear, district2_key, district_obj.key)

                  for contract_key in private_deliveries:
                    self.contract_keys[contract_key].adjust_accounts(private_deliveries[contract_key], search_type, wateryear)
                    location_delivery += private_deliveries[contract_key]
					
            for private_obj in self.city_list:
              for district2_key in private_obj.district_list:
                if district2_key == district_obj.key:
                  private_demand_constraint = private_obj.find_node_demand(contract_list, search_type, district2_key)
                  private_delivery_constraint = private_obj.set_request_to_district(private_demand_constraint,search_type,contract_list,0.0,dowy,district2_key)
                  delivery_to_private = min(private_demand_constraint, private_delivery_constraint,undelivered)
                  undelivered -= delivery_to_private
                  city_deliveries = private_obj.adjust_account_district(delivery_to_private,contract_list,search_type,wateryear, district2_key, district_obj.key)

                  for contract_key in city_deliveries:
                    self.contract_keys[contract_key].adjust_accounts(city_deliveries[contract_key], search_type, wateryear)
                    location_delivery += city_deliveries[contract_key]
					
          delivery_by_contract = district_obj.adjust_accounts(direct_deliveries, recharge_deliveries,contract_list, search_type, wateryear, district_obj.key)
          for contract_key in delivery_by_contract:
            self.contract_keys[contract_key].adjust_accounts(delivery_by_contract[contract_key], search_type, wateryear)
            location_delivery += delivery_by_contract[contract_key]
          #record flow and turnout on each canal, check for capacity turnback at the next node				
        #find new district demand at the node
        demand_constraint = district_obj.find_node_demand(contract_list, search_type, toggle_partial_delivery, toggle_district_recharge)
        self.find_node_demand_district(district_obj, canal, canal_loc, demand_constraint, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list, toggle_district_recharge)
        canal.find_turnout_adjustment(demand_constraint, flow_dir, canal_loc, type_list)


      elif self.canal_district[canal.name][canal_loc].is_Canal == 1:
        #find the object at the current node
        canal_obj = self.canal_district[canal.name][canal_loc]
        location_delivery = 0.0

        #if object is a canal, determine if water can flow from current canal into this canal (and orient the direction of flow)
        new_flow_dir = canal.flow_directions[flow_type][canal_obj.name]
        new_canal_size = self.canal_district_len[canal_obj.name]
        #how much flow can go into this new canal
        turnout_available = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]
        #initial demand for flow on the canal
        # location_delivery = 0.0
        # priorities = {}
        # priority_turnout_adjusted = {}
        for zz in type_list:
          location_delivery += canal.demand[zz][canal_loc]*type_fractions[zz]
          # priorities[zz] = 0.0
          # priority_turnout_adjusted[zz] = 0.0

        #if there is space & demand, 'jump' into new canal - outputs serve as turnouts from the current canal
        location_delivery = min(location_delivery, turnout_available)
        if turnout_available > 0.001 and location_delivery > 0.001:
          new_excess_flow, canal_demands = self.distribute_canal_deliveries(dowy, canal_obj, canal.key, contract_canal, location_delivery, new_canal_size, wateryear, new_flow_dir, flow_type, search_type)
          #update canal demands
          for zz in type_list:
            canal.demand[zz][canal_loc] = canal_demands[zz]
          if new_excess_flow > 0.0:
            for zz in type_list:
              canal.demand[zz][canal_loc] = 0.0
          #record deliveries
          location_delivery -= new_excess_flow
          canal_fractions = {}
          for zz in type_list:
            canal_fractions[zz] = 0.0
        else:
          # new_excess_flow = 0.0
          location_delivery = 0.0
          # canal_fractions = {}
          # for zz in type_list:
            # canal_fractions[zz] = 0.0

        canal.find_turnout_adjustment(turnout_available, flow_dir, canal_loc, type_list)


      #record flow and turnout on each canal, check for capacity turnback at the next node
      available_flow, turnback_flow, turnback_end, remaining_excess_flow = canal.update_canal_use(available_flow, location_delivery, flow_dir, canal_loc, starting_point, canal_size, type_list)
      excess_flow += remaining_excess_flow
      #if there is more demand/available water than canal capacity at the next canal node, the 'extra' water (that was expected to be delivered down-canal in earlier calculations) can be distributed among upstream nodes if there is remaining demand
      # for zz in type_list:
      #   type_demands[zz] -= canal.demand[zz][canal_loc]   
      toggle_demand_count = 0
      for zz in type_list:
        type_demands[zz] = 0.0
      for canal_loc_int in canal_range:
        if toggle_demand_count == 1:
          for zz in type_list:
            type_demands[zz] += canal.demand[zz][canal_loc_int]
        if canal_loc_int == canal_loc:
          toggle_demand_count = 1  

      if turnback_flow > 0.001:
        remaining_excess_flow, unmet_canal_demands = self.distribute_canal_deliveries(dowy, canal, prev_canal, contract_canal, turnback_flow, turnback_end, wateryear, flow_dir, flow_type, search_type)
        excess_flow += remaining_excess_flow
        available_capacity_int = max(available_flow, 0.0)
        for zz in type_list:
          if type_demands[zz] > 0.0:
            type_fractions[zz] = max(min(available_capacity_int/type_demands[zz], 1.0), 0.0)
          else:
            type_fractions[zz] = 0.0
          available_capacity_int -= type_demands[zz]*type_fractions[zz]

	  #sum remaining demand after all deliveries have been madw
    unmet_demands = {}
    for zz in type_list:
      unmet_demands[zz] = sum((canal.demand[zz][_] for _ in canal_range))
    		
    return excess_flow, unmet_demands


  cdef dict search_canal_demand(self, int dowy, Canal canal, str prev_canal, str contract_canal, str flow_dir, str flow_type, int wateryear, str search_type, dict existing_deliveries):
    ## Cython type declarations for whole function
    cdef list type_list, priority_list, contract_list, demand_constraint_by_contracts
    cdef dict empty_demands, type_deliveries, available_to_canal, canal_demands, priorities, paper_fractions
    cdef int toggle_partial_delivery, toggle_district_recharge, canal_size, starting_point, num_members, canal_loc
    cdef double private_demand_constraint, demand_constraint, current_recovery, current_storage, total_demand, priority_bank_space, paper_amount, direct_amount, \
                total_district_demand, total_available, existing_canal_space, total_exchange, paper_recovery, private_deliveries, direct_recovery, max_flow, \
                committed, location_delivery, total_paper, deliveries
    cdef str new_flow_dir, list_member, district_key, participant_key, zz, delivery_type, private_key
    cdef District district_obj, district_obj2
    cdef Private private_obj
    cdef Waterbank waterbank_obj
    cdef Canal canal_obj
    cdef Contract contract_obj

    if search_type == 'flood':
      #for flood flows, need to distinguish between districts with a contract
	  #to the water being spilled (1st priority), districts with a turnout on
	  #a 'favored' canal (i.e, one that won't disrupt flows from other sources,
	  #2nd priority), and districts with turnouts on other canals that can still
	  #be technically reached from this source (3rd priority)
      type_list = ['contractor', 'alternate', 'turnout', 'excess']
      toggle_partial_delivery = 0
      toggle_district_recharge = 1
    if search_type == 'delivery':
      type_list = [contract_canal]
      toggle_partial_delivery = 1
      toggle_district_recharge = 0
    if search_type == 'banking':
      type_list = ['priority', 'secondary']
      toggle_partial_delivery = 0
      toggle_district_recharge = 1
    if search_type == 'recovery':
      #if we are trying to distribute recovery water, we need to know how much 'initial' space is owned by each district in the recovery capacity at a waterbank/leiubank and then how much supplemental space, which can be used by individual districts if the capacity is not being used (same as for banking above, just w/ different names)
      type_list = ['initial', 'supplemental']
      toggle_partial_delivery = 1
      toggle_district_recharge = 0
	  
    #find the range of nodes to 'search' on this canal
    canal_size = self.canal_district_len[canal.name]
    if flow_dir == "closed":
      empty_demands = {}
      for list_member in type_list:
        empty_demands[list_member] = 0.0
      return empty_demands
    else:
      canal_range, starting_point = self.set_canal_range(flow_dir, flow_type, canal, prev_canal, canal_size)

    #initialize/clear dictionaries to store different types of demand on the canal
	#different flow 'modes' require different types of demand to be distinguished

    type_deliveries = {}
    for list_member in type_list:
      canal.demand[list_member] = np.zeros(canal_size)
      canal.turnout_frac[list_member] = np.zeros(canal_size)
      if existing_deliveries == {}:
        type_deliveries[list_member] = 0.0
      else:
        type_deliveries[list_member] = existing_deliveries[list_member]
      canal.recovery_flow_frac[list_member] = np.ones(canal_size)
	
    #canal priority
    priority_list = self.canal_priority[canal.name]
    #contracts on this canal
    contract_list = self.canal_contract[contract_canal]

    #MAIN SEARCH LOOP - within the canal range identified above, search through
    #the objects in self.canal_district to determine the total demand on the canal
    #(divided by demand 'type')

    for district_obj in self.district_list:
      district_obj.private_demand = {}
      district_obj.private_delivery = {}
    for private_obj in self.private_list:
      for district_key in private_obj.district_list:
        # district_obj = self.district_keys[district_key]
        private_demand_constraint = private_obj.find_node_demand(contract_list,search_type, district_key)
        self.district_keys[district_key].private_demand[private_obj.key] = private_demand_constraint
        self.district_keys[district_key].private_delivery[private_obj.key] = private_obj.set_request_to_district(private_demand_constraint,search_type,contract_list,0.0,dowy,district_key)
    for private_obj in self.city_list:
      for district_key in private_obj.district_list:
        # district_obj = self.district_keys[district_key]
        private_demand_constraint = private_obj.find_node_demand(contract_list,search_type, district_key)
        self.district_keys[district_key].private_demand[private_obj.key] = private_demand_constraint
        self.district_keys[district_key].private_delivery[private_obj.key] = private_obj.set_request_to_district(private_demand_constraint,search_type,contract_list,0.0,dowy,district_key)
	  
    for canal_loc in canal_range:
      if self.canal_district[canal.name][canal_loc].is_District == 1:
        district_obj = self.canal_district[canal.name][canal_loc]
        demand_constraint = 0.0

        #find demand at the node
        #partial delivery is used if the district recieves less than full daily demand due to projected contract allocations being lower than expected remaining annual demand
        #find district demand at the node
        if search_type == "recovery":
          demand_constraint = district_obj.find_node_output()
        else:
          demand_constraint = district_obj.find_node_demand(contract_list, search_type, toggle_partial_delivery, toggle_district_recharge)
        self.find_node_demand_district(district_obj, canal, canal_loc, demand_constraint, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list, toggle_district_recharge)
        canal.find_turnout_adjustment(demand_constraint, flow_dir, canal_loc, type_list)

      elif self.canal_district[canal.name][canal_loc].is_Waterbank == 1:
        waterbank_obj = self.canal_district[canal.name][canal_loc]
        demand_constraint = 0.0        
        self.find_node_demand_bank(waterbank_obj, canal, canal_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        #once all member demands/requests/priorities have been established, we can determine how much of each type of demand can be sent to the bank (b/c of turnout space)
        if search_type == 'recovery':
          current_recovery = 0.0
          for participant_key in waterbank_obj.participant_list:
            current_recovery += waterbank_obj.recovery_use[participant_key]
          demand_constraint = waterbank_obj.recovery - current_recovery
        else:
          current_storage = 0.0
          for participant_key in waterbank_obj.participant_list:
            current_storage += waterbank_obj.storage[participant_key]
          demand_constraint = waterbank_obj.tot_storage - current_storage
          self.find_node_demand_bank(waterbank_obj, canal, canal_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        canal.find_turnout_adjustment(demand_constraint, flow_dir, canal_loc, type_list)		

      elif self.canal_district[canal.name][canal_loc].is_Canal == 1:
        canal_obj = self.canal_district[canal.name][canal_loc]
        demand_constraint = 0.0        #find if the new canal can be accessed from the current canal
        if canal.turnout[flow_dir][canal_loc] > 0.0:
          #if it can, which way does the water flow onto the new canal
          new_flow_dir = canal.flow_directions[flow_type][canal_obj.name]
          #calculate the demands for this whole canal by recursively calling this function again, but with the new canal input parameters
          available_to_canal = {}
          if canal_obj.recovery_feeder:
            for zz in type_deliveries:
              available_to_canal[zz] = 0.0
          elif search_type == 'recovery':
            for zz in type_deliveries:
              available_to_canal[zz] = type_deliveries[zz]
          else:
            for zz in type_deliveries:
              available_to_canal[zz] = 0.0

          canal_demands = self.search_canal_demand(dowy, canal_obj, canal.key, contract_canal, new_flow_dir,flow_type,wateryear,search_type, available_to_canal)
		  #check to see all demands can be met using the turnout space
          total_demand = 0.0
          for zz in type_list:
            canal.demand[zz][canal_loc] = canal_demands[zz]
            total_demand += canal_demands[zz]
          canal.find_turnout_adjustment(total_demand, flow_dir, canal_loc, type_list)
        else:
          for zz in type_list:
            canal.demand[zz][canal_loc] = 0.0	

      #sum demand at all canal nodes
      for zz in type_list:
        type_deliveries[zz] += canal.demand[zz][canal_loc]
      if search_type == "recovery":
        if self.canal_district[canal.name][canal_loc].is_District == 1:
          if district_obj.in_leiu_banking:
            for participant_key in district_obj.participant_list:
              if participant_key != district_obj.key:
                num_members = self.district_keys_len[participant_key]      
                if self.district_keys[participant_key].is_District == 1:
                  district_obj2 = self.district_keys[participant_key]
                  participant_obj = district_obj2
                elif self.district_keys[participant_key].is_Private == 1:
                  private_obj = self.district_keys[participant_key]
                  participant_obj = private_obj

                #find waterbank partner demand (i.e., recovery capacity of their ownership share)                 
                demand_constraint, demand_constraint_by_contracts = district_obj.find_leiu_output(contract_list, district_obj.leiu_ownership[participant_key], participant_key, wateryear)
                #does this partner want recovery water?
                deliveries = participant_obj.set_request_constraints(demand_constraint, search_type, contract_list, district_obj.inleiubanked[participant_key], district_obj.inleiucap[participant_key], dowy, wateryear)
                #what is their priority over the water/canal space?
                priority_bank_space = district_obj.find_leiu_priority_space(demand_constraint, num_members, participant_key, 0, search_type)
      
                priorities = district_obj.set_demand_priority("N/A", "N/A", priority_bank_space, deliveries, demand_constraint, search_type, "N/A")
                #need to adjust the water request to account for the banking partner share of the turnout
                for zz in type_list:
                #paper trade recovery is equal to 
                  paper_amount = priorities[zz]
                  # direct_amount = 0.0
                  # contract_frac_list = np.zeros(len(district_obj.contract_list))
                  participant_obj.get_paper_exchange(paper_amount, district_obj.contract_list, demand_constraint_by_contracts, wateryear)
                  district_obj.adjust_exchange(paper_amount, participant_key, wateryear)
                  district_obj.give_paper_exchange(paper_amount, district_obj.contract_list, demand_constraint_by_contracts, wateryear, district_obj.key)

          #for non-bank district nodes, they can accept recovery water.  we want to find how much water they can accept (based on their ability to make paper trades using the contracts in contract_list, then determine how much of the recovery water up-canal, can be delivered here as a 'paper' trade, and then how much additional water can be delivered here 'directly' (i.e., the pumping out of the water bank is going to the district that owns capacity in the water bank, so no paper trades needed - this is useful if there is no surface water storage, but a district still wants water from its water bank (and can get that water directly, from the run of the canal)
          total_district_demand = district_obj.find_node_demand(contract_list, search_type, toggle_partial_delivery, toggle_district_recharge)
          total_available = 0.0
          existing_canal_space = canal.capacity[flow_dir][canal_loc]*cfs_tafd - canal.flow[canal_loc]
          for delivery_type in type_deliveries:
            total_available += type_deliveries[delivery_type]
          total_exchange = 0.0
          for contract_obj in contract_list:
            total_exchange += district_obj.projected_supply[contract_obj.name]
          if district_obj.has_private:
            for private_obj in self.city_list:
              for district_key in private_obj.district_list:
                if district_key == district_obj.key:
                  for contract_obj in contract_list:
                    total_exchange += private_obj.projected_supply[district_obj.key][contract_obj.name]
          paper_recovery = min(total_district_demand, total_available, total_exchange)
          private_deliveries = 0.0
          if district_obj.has_private:
            for private_key in district_obj.private_demand:
              private_deliveries += min(district_obj.private_demand[private_key], district_obj.private_delivery[private_key])
          direct_recovery = max(min(total_available - paper_recovery, district_obj.dailydemand[0]*district_obj.seepage*district_obj.surface_water_sa + private_deliveries - paper_recovery), 0.0)
          #find capacity constraints between this location and the up-canal waterbanks
          if flow_dir == "normal":
            lookback_range = range(starting_point, canal_loc)
          elif flow_dir == "reverse":
            lookback_range = range(starting_point, canal_loc, -1)
          max_flow = canal.capacity[flow_dir][starting_point]*cfs_tafd - canal.flow[starting_point]
          for lookback_loc in lookback_range:
            max_flow = min(canal.capacity[flow_dir][lookback_loc]*cfs_tafd - canal.flow[lookback_loc], max_flow)
          direct_recovery = min(max(max_flow - paper_recovery, 0.0), direct_recovery)
          paper_recovery = min(paper_recovery, max_flow)
          #find the % of total 'recovery demand' at each water bank that can be fufilled at this district demand node
          paper_fractions = {}
          committed = 0.0
          for zz in type_list:
            if type_deliveries[zz] > 0.0:
              paper_fractions[zz] = min((paper_recovery - committed)/type_deliveries[zz], 1.0)
              committed += min(paper_recovery - committed, type_deliveries[zz])
            else:
              paper_fractions[zz] = 0.0
              committed += min(paper_recovery - committed, type_deliveries[zz])
          location_delivery = 0.0
          if committed > 0.0:
            if flow_dir == "normal":
              lookback_range = range(starting_point, canal_loc + 1)
            elif flow_dir == "reverse":
                lookback_range = range(starting_point, canal_loc - 1, -1)
              #search for waterbanks
            location_delivery, total_paper = self.delivery_recovery(contract_list, canal, lookback_range, starting_point, paper_fractions, direct_recovery, flow_dir, type_list, priority_list, contract_canal, district_obj.key, dowy, wateryear)
            paper_delivery = district_obj.give_paper_trade(total_paper, contract_list, wateryear, district_obj.key)
            location_delivery -= paper_delivery
            total_paper -= paper_delivery
            if district_obj.has_private:
              for private_obj in self.city_list:
                for district_key in private_obj.district_list:
                  if district_key == district_obj.key:
                    paper_delivery = private_obj.give_paper_trade(total_paper, contract_list, wateryear, district_obj.key)
                    location_delivery -= paper_delivery
                    total_paper -= paper_delivery
					  
            location_delivery -= district_obj.record_direct_delivery(location_delivery, wateryear)

            if district_obj.has_private:
              for private_obj in self.city_list:
                for district_key in private_obj.district_list:
                  if district_key == district_obj.key:
                    location_delivery -= private_obj.record_direct_delivery(location_delivery, wateryear, district_obj.key)
		  
	#once all canal nodes have been searched, we can check to make sure the demands aren't bigger than the canal capacity, then adjust our demands	
    #type_deliveries = canal.capacity_adjust_demand(starting_point, canal_range, flow_dir, type_list)
    if search_type == 'recovery':
      if canal.recovery_feeder:
        return type_deliveries
      else:
        for zz in type_deliveries:
          type_deliveries[zz] = 0.0
        return type_deliveries	  
    else:
      return type_deliveries
	


  cdef (double, double) delivery_recovery(self, list contract_list, Canal canal, lookback_range, int starting_point, dict paper_fractions, double direct_recovery, str flow_dir, list type_list, list priority_list, str contract_canal, str delivery_loc_name, int dowy, int wateryear):
    cdef District district_obj, district_obj2
    cdef Private private_obj
    cdef Waterbank waterbank_obj
    cdef Canal canal_obj
    cdef double location_pumpout, paper_amount, demand_constraint, sum_deliveries, existing_canal_space, new_flow, available_flow, total_paper, max_current_release, \
              deliveries, priority_bank_space, direct_amount, actual_delivery, current_recovery
    cdef int lookback_loc, canal_backtrack, toggle_district_recharge, num_members, counter_toggle, new_canal_size, new_starting_point
    cdef str zz, search_type, participant_key, district_key, new_flow_dir, new_prev_canal
    cdef dict running_type_deliveries, priorities, priority_turnout_adjusted
    
    running_type_deliveries = {}
    for zz in type_list:
      running_type_deliveries[zz] = 0.0
    
    sum_deliveries = 0.0
    for lookback_loc in lookback_range:
      for zz in type_list:
        running_type_deliveries[zz] += canal.demand[zz][lookback_loc]
        sum_deliveries += canal.demand[zz][lookback_loc]
      existing_canal_space = canal.capacity[flow_dir][lookback_loc]*cfs_tafd - canal.flow[lookback_loc]
      if sum_deliveries > existing_canal_space:
        if flow_dir == "normal":
          backtrack_range = range(starting_point, lookback_loc + 1)
        elif flow_dir == "reverse":
          backtrack_range = range(starting_point, lookback_loc - 1, -1)
        for zz in type_list:
          for canal_backtrack in backtrack_range:
            canal.recovery_flow_frac[zz][canal_backtrack] = min(max(min(existing_canal_space/running_type_deliveries[zz], 1.0), 0.0), canal.recovery_flow_frac[zz][canal_backtrack])
          new_flow = min(running_type_deliveries[zz], existing_canal_space)
          existing_canal_space -= new_flow

    #Loop back through the canal looking for waterbank sources to make paper trades with
    available_flow = 0.0
    total_paper = 0.0
    toggle_district_recharge = 0
    for lookback_loc in lookback_range:
      location_pumpout = 0.0

      if self.canal_district[canal.name][lookback_loc].is_District == 1:
        district_obj = self.canal_district[canal.name][lookback_loc]
        recovery_source = district_obj
      elif self.canal_district[canal.name][lookback_loc].is_Waterbank == 1:
        waterbank_obj = self.canal_district[canal.name][lookback_loc]
        recovery_source = waterbank_obj
      elif self.canal_district[canal.name][lookback_loc].is_Canal == 1:
        canal_obj = self.canal_district[canal.name][lookback_loc]
        recovery_source = canal_obj

      search_type = "recovery"
      max_current_release = 0.0
      for zz in type_list:
        max_current_release = canal.demand[zz][lookback_loc]*canal.recovery_flow_frac[zz][lookback_loc]
      if recovery_source.is_District == 1:
        if recovery_source.in_leiu_banking:
          for participant_key in recovery_source.participant_list:
            num_members = self.district_keys_len[participant_key]
            if participant_key != recovery_source.key:
              if self.district_keys[participant_key].is_District == 1:
                district_obj2 = self.district_keys[participant_key]
                participant_obj = district_obj2
              elif self.district_keys[participant_key].is_Private == 1:
                private_obj = self.district_keys[participant_key]
                participant_obj = private_obj

              #find waterbank partner demand (i.e., recovery capacity of their ownership share)
              demand_constraint = recovery_source.find_node_output()
              #does this partner want recovery water?
              deliveries = participant_obj.set_request_constraints(demand_constraint, search_type, contract_list, recovery_source.inleiubanked[participant_key], recovery_source.inleiucap[participant_key], dowy, wateryear)
              #what is their priority over the water/canal space?
              priority_bank_space = recovery_source.find_leiu_priority_space(demand_constraint, num_members, participant_key, 0, search_type)
      
              priorities = recovery_source.set_demand_priority("N/A", "N/A", priority_bank_space, deliveries, demand_constraint, search_type, "N/A")
              priority_turnout_adjusted = {}
              #need to adjust the water request to account for the banking partner share of the turnout
              for zz in type_list:
                priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][lookback_loc]
              for zz in type_list:
                #paper trade recovery is equal to 
                paper_amount = priority_turnout_adjusted[zz]*min(paper_fractions[zz], canal.recovery_flow_frac[zz][lookback_loc])
                direct_amount = min(direct_recovery, priority_turnout_adjusted[zz]*canal.recovery_flow_frac[zz][lookback_loc] - paper_amount)
                recovery_source.adjust_recovery(paper_amount, participant_key, wateryear)
                location_pumpout += paper_amount
                actual_delivery = 0.0
                if delivery_loc_name == participant_obj.key:
                  demand_constraint = recovery_source.find_node_output()
                  max_direct_recovery = min(demand_constraint, direct_amount, recovery_source.inleiubanked[participant_key]/num_members)
                  actual_delivery = participant_obj.direct_delivery_bank(max_direct_recovery, wateryear)
                  direct_recovery -= actual_delivery
                  recovery_source.adjust_recovery(actual_delivery, participant_key, wateryear)
                  location_pumpout += actual_delivery
                elif participant_obj.is_Private == 1:
                  counter_toggle = 0
                  for district_key in participant_obj.district_list:
                    if delivery_loc_name == district_key:
                      demand_constraint = recovery_source.find_node_output()
                      max_direct_recovery = min(demand_constraint, direct_amount, recovery_source.inleiubanked[participant_key]/num_members)
                      actual_delivery = participant_obj.direct_delivery_bank(max_direct_recovery, wateryear, district_key)
                      direct_recovery -= actual_delivery
                      recovery_source.adjust_recovery(actual_delivery, participant_key, wateryear)
                      location_pumpout += actual_delivery
                      counter_toggle = 1
                    if counter_toggle == 0:
                      participant_obj.get_paper_trade(paper_amount, contract_list, wateryear)
                      total_paper += paper_amount
                else:
                  participant_obj.get_paper_trade(paper_amount, contract_list, wateryear)
                  total_paper += paper_amount


          #recalculate the 'recovery demand' at each waterbank		  
          demand_constraint = recovery_source.find_node_output()
          self.find_node_demand_district(recovery_source, canal, lookback_loc, demand_constraint, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list, toggle_district_recharge)
          canal.find_turnout_adjustment(demand_constraint, flow_dir, lookback_loc, type_list)
		
      elif recovery_source.is_Waterbank == 1:
        for participant_key in recovery_source.participant_list:
          num_members = self.district_keys_len[participant_key]
          if self.district_keys[participant_key].is_District == 1:
            district_obj = self.district_keys[participant_key]
            participant_obj = district_obj
          elif self.district_keys[participant_key].is_Private == 1:
            private_obj = self.district_keys[participant_key]
            participant_obj = private_obj

          #find waterbank partner demand (i.e., recovery capacity of their ownership share)
          demand_constraint = recovery_source.find_node_demand(contract_list, participant_key, num_members, search_type) 
          #does this partner want recovery water?
          deliveries =  participant_obj.set_request_constraints(demand_constraint, search_type, contract_list, recovery_source.banked[participant_key], recovery_source.bank_cap[participant_key], dowy, wateryear)
          #what is their priority over the water/canal space?
          priority_bank_space = recovery_source.find_priority_space(num_members, participant_key, search_type)
          priorities = recovery_source.set_demand_priority("NA", "N/A", priority_bank_space, deliveries, demand_constraint, search_type, "N/A", "N/A",participant_obj.contract_list)
          priority_turnout_adjusted = {}


          #need to adjust the water request to account for the banking partner share of the turnout
          for zz in type_list:
            priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][lookback_loc]
          #finds how much water can be delivered through paper trades (exchange of GW recovery for stored SW)
    #and how much water can be delivered directly
    #canal.recovery_flow_frac is the adjustment needed if the bank runs into canal capacity constraints
          for zz in type_list:
            paper_amount = priority_turnout_adjusted[zz]*min(paper_fractions[zz], canal.recovery_flow_frac[zz][lookback_loc])
            direct_amount = min(direct_recovery, priority_turnout_adjusted[zz]*canal.recovery_flow_frac[zz][lookback_loc] - paper_amount)
            recovery_source.adjust_recovery(paper_amount, participant_key, wateryear)#adjust accounts
            location_pumpout += paper_amount
      #if the GW is being delivered to the WB owner, more water can be delivered (not constrained by 
      #another district's willingness to trade SW storage)
            if delivery_loc_name == participant_obj.key:
              demand_constraint = recovery_source.find_node_demand(contract_list, participant_key, num_members, search_type)
              max_direct_recovery = min(demand_constraint, direct_amount, recovery_source.banked[participant_key]/num_members)
              actual_delivery = participant_obj.direct_delivery_bank(max_direct_recovery, wateryear)
              direct_recovery -= actual_delivery
              recovery_source.adjust_recovery(actual_delivery, participant_key, wateryear)
              location_pumpout += actual_delivery
            elif participant_obj.is_Private == 1:
              counter_toggle = 0
              for district_key in participant_obj.district_list:
                if delivery_loc_name == district_key:
                  demand_constraint = recovery_source.find_node_demand(contract_list, participant_key, num_members, search_type)
                  max_direct_recovery = min(demand_constraint, direct_amount, recovery_source.banked[participant_key]/num_members)
                  actual_delivery = participant_obj.direct_delivery_bank(max_direct_recovery, wateryear, district_key)
                  direct_recovery -= actual_delivery
                  recovery_source.adjust_recovery(actual_delivery, participant_key, wateryear)
                  location_pumpout += actual_delivery
                  counter_toggle = 1
              if counter_toggle == 0:
                participant_obj.get_paper_trade(paper_amount, contract_list, wateryear)#exchange GW for SW 
                total_paper += paper_amount
            else:
              participant_obj.get_paper_trade(paper_amount, contract_list, wateryear)#exchange GW for SW 
              total_paper += paper_amount
    
        #recalculate the 'recovery demand' at each waterbank			
        self.find_node_demand_bank(recovery_source, canal, lookback_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        current_recovery = 0.0
        for participant_key in recovery_source.participant_list:
          current_recovery += recovery_source.recovery_use[participant_key]
        demand_constraint = recovery_source.recovery - current_recovery
        canal.find_turnout_adjustment(demand_constraint, flow_dir, lookback_loc, type_list)
				
      elif recovery_source.is_Canal == 1:
        new_flow_dir = canal.flow_directions['recovery'][recovery_source.name]
        new_canal_size = self.canal_district_len[recovery_source.name]
        new_prev_canal = canal.key
        new_lookback_range, new_starting_point = self.set_canal_range(new_flow_dir, 'recovery', recovery_source, new_prev_canal, new_canal_size)
        location_pumpout, paper_amount = self.delivery_recovery(contract_list, recovery_source, new_lookback_range, new_starting_point, paper_fractions, direct_recovery, new_flow_dir, type_list, priority_list, contract_canal, delivery_loc_name, dowy, wateryear)
        total_paper += paper_amount

      available_flow += location_pumpout
      canal.turnout_use[lookback_loc] += location_pumpout
      canal.flow[lookback_loc] += available_flow
   
    return available_flow, total_paper
	


  cdef void find_node_demand_district(self, District district_node, Canal canal, int canal_loc, double demand_constraint, list contract_list, list priority_list, str contract_canal, int dowy, int wateryear, str search_type, list type_list, int toggle_district_recharge):
    cdef District district_obj
    cdef Private private_obj
    cdef double priority_bank_space, deliveries
    cdef int num_members
    cdef str zz, participant_key
    cdef list 
    cdef dict priorities

    #this function classifies the demand at a district node - 2 parts (i) find how much water district(s) want to apply and (ii) give each water request a priority
    for zz in type_list:
      canal.demand[zz][canal_loc] = 0.0
    #if a district is an in-leiu bank, partners can send water to this district for banking recharge
    if (district_node.in_leiu_banking and search_type == "banking") or (district_node.in_leiu_banking and search_type == "recovery"):
      for participant_key in district_node.participant_list:
        num_members = self.district_keys_len[participant_key]
        if self.district_keys[participant_key].is_District == 1:
          district_obj = self.district_keys[participant_key]
          participant_obj = district_obj
        elif self.district_keys[participant_key].is_Private == 1:
          private_obj = self.district_keys[participant_key]
          participant_obj = private_obj
        #find if the banking partner wants to bank
        deliveries = participant_obj.set_request_constraints(demand_constraint, search_type, contract_list, district_node.inleiubanked[participant_key], district_node.inleiucap[participant_key], dowy, wateryear)
        #determine the priorities of the banking
        priority_bank_space = district_node.find_leiu_priority_space(demand_constraint, num_members, participant_key, toggle_district_recharge, search_type)
        priorities = participant_obj.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal)

        for zz in type_list:
          canal.demand[zz][canal_loc] += priorities[zz]
        #can't purchase more than the turnout capacity

    else:
      deliveries =  district_node.set_request_constraints(demand_constraint, search_type, contract_list, 0.0, 999.0, dowy, wateryear)
      #find what priority district has for flow purchases
      priorities = district_node.set_demand_priority(priority_list, contract_list, demand_constraint, deliveries, demand_constraint, search_type, contract_canal)

      for zz in type_list:
        canal.demand[zz][canal_loc] += priorities[zz]



  cdef void find_node_demand_bank(self, Waterbank bank_node, Canal canal, int canal_loc, list contract_list, list priority_list, str contract_canal, int dowy, int wateryear, str search_type, list type_list):
    cdef str zz, participant_key
    cdef int num_members
    cdef double demand_constraint, priority_bank_space, deliveries
    cdef dict priorities
    cdef District district_obj
    cdef Private private_obj

    #this function finds the total demand at a waterbank node - 3 parts (i) find total water that can be taken (ii) find how much water district(s) want to apply (iii) give each water request a priority  
    #for waterbanks, we calculate the demands of each waterbank partner individually
    for zz in type_list:
      canal.demand[zz][canal_loc] = 0.0

    for participant_key in bank_node.participant_list:
      num_members = self.district_keys_len[participant_key]
      if self.district_keys[participant_key].is_District == 1:
        district_obj = self.district_keys[participant_key]
        participant_obj = district_obj
      elif self.district_keys[participant_key].is_Private == 1:
        private_obj = self.district_keys[participant_key]
        participant_obj = private_obj

      #find waterbank partner demand (i.e., recharge capacity of their ownership share)
      demand_constraint = bank_node.find_node_demand(contract_list, participant_key, num_members, search_type) 
      #does this partner want to bank water?
      deliveries =  participant_obj.set_request_constraints(demand_constraint, search_type, contract_list, bank_node.banked[participant_key], bank_node.bank_cap[participant_key], dowy, wateryear)
        #deliveries = bank_node.set_request_constraints(demand_constraint, search_type, contract_list)
      #what is their priority over the water/canal space?
      priority_bank_space = bank_node.find_priority_space(num_members, participant_key, search_type)
      priorities = bank_node.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal, canal.name, participant_obj.contract_list)
      #take the individual priorities of waterbank members and add them to the total canal node demands

      for zz in type_list:
        canal.demand[zz][canal_loc] += priorities[zz]
  
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################



#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


#####################################################################################################################
###############################  Miscellaneous Functions Within Simulation ###############################
#####################################################################################################################
  def set_regulations_current_south(self, scenario):
    cdef District district_obj
    cdef Waterbank waterbank_obj

    self.semitropic.leiu_recovery = 0.7945
    self.isabella.capacity = 361.25
    self.isabella.tocs_rule['storage'] = [[302.6,170,170,245,245,361.25,361.25,302.6],  [302.6,170,170,245,245,361.25,361.25,302.6]]
    self.poso.initial_recharge = 420.0
    self.poso.recovery = 0.6942
    self.poso.tot_storage = 2.1
    self.irvineranch.initial_recharge = 300.0
    self.irvineranch.recovery = 0.0479
    self.irvineranch.tot_storage = 0.594
    self.losthills.project_contract['tableA'] = 0.0293663708
    self.wheeler.project_contract['tableA'] =  0.04858926015
    self.belridge.project_contract['tableA'] = 0.02995607
    self.southbay.project_contract['tableA'] = 0.0548863
    self.westkern.project_contract['tableA'] = 0.00776587
    self.berrenda.project_contract['tableA'] =  0.02282922
    self.socal.project_contract['tableA'] = 0.648310
    for xnum in range(0, self.number_years):
      self.metropolitan.private_fraction['SOC'][xnum] = 1911.0/(4056.0 * 0.648310)
      self.metropolitan.pump_out_fraction['SOC'] = 1911.0/(4056.0 * 0.648310)
    self.socal.private_fraction =  [(1911.0 + (0.03629 + 0.05274) * 4056.0 * 0.648310) / (4056.0 * 0.648310)]

    self.kwbcanal.capacity["normal"] = [800.0, 800.0, 0.0, 0.0]
    self.kwbcanal.capacity["reverse"] = [0.0, 440.0, 800.0, 800.0]
    self.kwbcanal.capacity["closed"] = [0.0, 0.0, 0.0, 0.0]
    self.kwbcanal.turnout["normal"] = [800.0, 800.0, 0.0]
    self.kwbcanal.turnout["reverse"] = [0.0, 440.0, 800.0]
    self.kwbcanal.turnout["closed"] = [0.0, 0.0, 0.0]
    self.kwbcanal.flow_directions["recharge"]["caa"] = 'closed'
    self.kwbcanal.flow_directions["recharge"]["knc"] = 'closed'
    self.kwbcanal.flow_directions["recovery"]["caa"] = 'normal'
    self.kwbcanal.flow_directions["recovery"]["knc"] = 'normal'
    self.fkc.flow_directions["recharge"]["xvc"] = 'normal'
    self.kwb.initial_recharge = 1212.12
    self.kwb.recovery = 0.7863
    self.kwb.tot_storage = 2.4
    tot_contract = 0.0

    if self.use_sensitivity:
      for district_obj in self.district_list:
        district_obj.set_sensitivity_factors(self.sensitivity_factors['et_multiplier']['realization'], self.sensitivity_factors['acreage_multiplier']['realization'], self.sensitivity_factors['irrigation_efficiency']['realization'], self.sensitivity_factors['recharge_decline']['realization'])
      for waterbank_obj in self.waterbank_list:
        for x in range(0, len(waterbank_obj.recharge_decline)):
          waterbank_obj.recharge_decline[x] = 1.0 - self.sensitivity_factors['recharge_decline']['realization']*(1.0 - waterbank_obj.recharge_decline[x])		

	
  def set_regulations_historical_north(self):
    if self.starting_year >= 2005:
      self.yuba.env_min_flow = self.yuba.env_min_flow_ya
      self.yuba.temp_releases = self.yuba.temp_releases_ya
    if self.starting_year >= 2008:
      for x in range(318, 334):
        self.delta.x2constraint['W'][x] = 77.0 - 3.0*(x-318)/16
        self.delta.x2constraint['AN'][x] = 81.0
      for x in range(334,366):
        self.delta.x2constraint['W'][x] = 74.0
        self.delta.x2constraint['AN'][x] = 81.0
      for x in range(0, 30):
        self.delta.x2constraint['W'][x] = 74.0
        self.delta.x2constraint['AN'][x] = 81.0

  def set_regulations_current_north(self):
    self.yuba.env_min_flow = self.yuba.env_min_flow_ya
    self.yuba.temp_releases = self.yuba.temp_releases_ya
    for x in range(318, 334):
      self.delta.x2constraint['W'][x] = 77.0 - 3.0*(x-318)/16
      self.delta.x2constraint['AN'][x] = 81.0
    for x in range(334,366):
      self.delta.x2constraint['W'][x] = 74.0
      self.delta.x2constraint['AN'][x] = 81.0
    for x in range(0, 30):
      self.delta.x2constraint['W'][x] = 74.0
      self.delta.x2constraint['AN'][x] = 81.0
	  

  def set_regulations_historical_south(self, scenario):
    cdef District district_obj
    cdef Private private_obj
    cdef Contract contract_obj

    if self.starting_year >= 2005:
      self.semitropic.leiu_recovery = 0.7945
    if self.starting_year >= 2009:
      expected_outflow_releases = {}
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        expected_outflow_releases[wyt] = np.zeros(366)
        self.millerton.carryover_target[wyt] = 250.0
      self.millerton.calc_expected_min_release(self, expected_outflow_releases, np.zeros(12), 1)
      self.millerton.max_carryover_target = 250.0

    if self.starting_year >= 2004:
      self.kaweah.capacity = 180.0
      self.kaweah.tocs_rule['storage'] = [[180,63,63,180,180], [180,63,63,180,180]]
    if self.starting_year >= 2005:
      self.isabella.capacity = 400.0
      self.isabella.tocs_rule['storage'] = [[302.6,245,245,245,245,400,400,302.6],  [302.6,245,245,245,245,400,400,302.6]]
      self.kernriver.carryover = 170.0
    if self.starting_year >= 2006:
      self.isabella.capacity = 361.25
      self.isabella.tocs_rule['storage'] = [[302.6,170,170,245,245,361.25,361.25,302.6],  [302.6,170,170,245,245,361.25,361.25,302.6]]
      self.kernriver.carryover = 170.0
      for district_obj in self.district_list:
        district_obj.carryover_rights = {}
        for contract_obj in self.contract_list:
          if contract_obj.type == 'right':
            district_obj.carryover_rights[contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']
          else:
            district_obj.carryover_rights[contract_obj.name] = 0.0
      for private_obj in self.private_list:
        private_obj.carryover_rights = {}
        for district_key in private_obj.district_list:
          district_obj = self.district_keys[district_key]
          private_obj.carryover_rights[district_key] = {}
          for contract_obj in self.contract_list:
            if contract_obj.type == 'right':
              private_obj.carryover_rights[district_key][contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*private_obj.private_fraction[district_key][0]
            else:
              private_obj.carryover_rights[district_key][contract_obj.name] = 0.0
      for private_obj in self.city_list:
        private_obj.carryover_rights = {}
        for district_key in private_obj.district_list:
          district_obj = self.district_keys[district_key]
          private_obj.carryover_rights[district_key] = {}
          for contract_obj in self.contract_list:
            if contract_obj.type == 'right':
              private_obj.carryover_rights[district_key][contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*private_obj.private_fraction[district_key][0]
            else:
              private_obj.carryover_rights[district_key][contract_obj.name] = 0.0
    if self.starting_year >= 2009:
      self.poso.initial_recharge = 420.0
      self.poso.recovery = 0.6942
      self.poso.tot_storage = 2.1
      self.fkc.capacity["normal"] = self.fkc.capacity["normal_wy2010"]
    if self.starting_year >= 2010:
      self.irvineranch.initial_recharge = 300.0
      self.irvineranch.recovery = 0.0479
      self.irvineranch.tot_storage = 0.594
    if self.starting_year >= 1998:
      self.berrenda.project_contract['tableA'] =  0.032076
      self.socal.project_contract['tableA'] = 0.63338264299
      for xnum in range(0, self.number_years):
        self.metropolitan.private_fraction['SOC'][xnum] = 1911.0/(4056.0 * 0.63338264299)
      self.socal.private_fraction =  [(1911.0 + (0.03629 + 0.05274) * 4056.0) / (4056.0 * 0.63338264299)]
    if self.starting_year >= 1999:
      self.belridge.project_contract['tableA'] = 0.03636
    if self.starting_year >= 2000:
      self.southbay.project_contract['tableA'] = 0.05177514792
      self.belridge.project_contract['tableA'] = 0.03538
      self.berrenda.project_contract['tableA'] =  0.03035
      self.losthills.project_contract['tableA'] = 0.0293663708
      self.wheeler.project_contract['tableA'] =  0.04858926015
      self.socal.project_contract['tableA'] = 0.64423076923
      for xnum in range(0, self.number_years):
        self.metropolitan.private_fraction['SOC'][xnum] = 1911.0/(4056.0 * 0.64423076923)
      self.socal.private_fraction =  [(1911.0 + (0.03629 + 0.05274) * 4056.0) / (4056.0 * 0.64423076923)]

    if self.starting_year >= 2001:
      self.southbay.project_contract['tableA'] = 0.05424063116
      self.belridge.project_contract['tableA'] = 0.0305
      self.berrenda.project_contract['tableA'] =  0.02837
    if self.starting_year >= 2004:
      self.belridge.project_contract['tableA'] = 0.02995607
      self.berrenda.project_contract['tableA'] =  0.02677
      self.southbay.project_contract['tableA'] = 0.0548863
      self.westkern.project_contract['tableA'] = 0.00776587
    if self.starting_year >= 2010:
      self.berrenda.project_contract['tableA'] =  0.02282922
      self.socal.project_contract['tableA'] = 0.648310
      for xnum in range(0, self.number_years):
        self.metropolitan.private_fraction['SOC'][xnum] = 1911.0/(4056.0 * 0.648310)
      self.socal.private_fraction =  [(1911.0 + (0.03629 + 0.05274) * 4056.0) / (4056.0 * 0.648310)]

    if self.starting_year >= 2002:
      self.kwbcanal.capacity["normal"] = [800.0, 800.0, 0.0, 0.0]
      self.kwbcanal.capacity["reverse"] = [0.0, 440.0, 800.0, 800.0]
      self.kwbcanal.capacity["closed"] = [0.0, 0.0, 0.0, 0.0]
      self.kwbcanal.turnout["normal"] = [800.0, 800.0, 0.0]
      self.kwbcanal.turnout["reverse"] = [0.0, 440.0, 800.0]
      self.kwbcanal.turnout["closed"] = [0.0, 0.0, 0.0]
      self.kwbcanal.flow_directions["recharge"]["caa"] = 'closed'
      self.kwbcanal.flow_directions["recharge"]["knc"] = 'closed'
      self.kwbcanal.flow_directions["recovery"]["caa"] = 'normal'
      self.kwbcanal.flow_directions["recovery"]["knc"] = 'normal'
      #self.fkc.flow_directions["recharge"]["xvc"] = 'normal'

      self.kwb.initial_recharge = 1212.12
      self.kwb.recovery = 0.7863
      self.kwb.tot_storage = 2.4
      if (scenario == 'baseline'):
        do_nothing = 0
      elif (scenario['FKC'] == 'baseline'):
        self.fkc.capacity["normal"] = self.fkc.capacity["normal_wy2010"]

      self.kerndelta.in_district_direct_recharge = 165.0
      self.kerndelta.in_district_storage = 0.326
      self.buenavista.in_district_direct_recharge = 333.3
      self.buenavista.in_district_storage = 0.66
      self.rosedale.in_district_direct_recharge = 606.1
      self.rosedale.in_district_storage = 1.2
	  
    self.swpdelta.total = 4056.0
    if self.starting_year == 1996:
      self.swpdelta.max_allocation = 2977.0
    elif self.starting_year == 1997:
      self.swpdelta.max_allocation = 3191.0
    elif self.starting_year == 1998:
      self.swpdelta.max_allocation = 3214.0
    elif self.starting_year == 1999:
      self.swpdelta.max_allocation = 3617.0
    else:
      self.swpdelta.max_allocation = 4056.0
	  
    request_empty = self.swpdelta.total - self.swpdelta.max_allocation
    for district_obj in self.district_list:
      contractor_toggle = 0
      for contract in district_obj.contract_list:
        if contract == 'tableA':
          contractor_toggle = 1
          break
      if contractor_toggle == 1:	  
        if district_obj.key == "SOC":
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total - request_empty
        elif district_obj.key == "SOB":
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total 
        elif district_obj.key == "CCA":
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total
        else:
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total
    self.swpdelta.total = self.swpdelta.max_allocation
    for district_obj in self.district_list:
      contractor_toggle = 0
      for contract in district_obj.contract_list:
        if contract == 'tableA':
          contractor_toggle = 1
          break
      if contractor_toggle == 1:	  
        district_obj.project_contract['tableA'] = district_obj.table_a_request/self.swpdelta.total


	
  def update_regulations_south(self,t,dowy,m,y, wateryear):
    ##San Joaquin River Restoration Project, started in October of 2009 (WY 2009)
    cdef District district_obj
    cdef Private private_obj
    cdef Contract contract_obj

	##Additional Releases from Millerton Lake depending on WYT
    if y >= 2006:
      self.semitropic.leiu_recovery = 0.7945
    if y == 2009 and dowy == 1:
      expected_outflow_releases = {}
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        expected_outflow_releases[wyt] = np.zeros(366)
      self.millerton.calc_expected_min_release(self, expected_outflow_releases, np.zeros(12), 1)

    if y == 2009 and m >= 10:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)
      for sjrrwyt in ['W', 'AN', 'BN', 'D', 'C']:
        self.millerton.carryover_target[sjrrwyt] = 250.0
      self.millerton.max_carryover_target = 250.0
    elif y > 2009:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)
    if t == 3089:
      self.kaweah.capacity = 180.0
      self.kaweah.tocs_rule['storage'] = [[180,63,63,180,180], [180,63,63,180,180]]
    if t == 3451:
      self.isabella.capacity = 400.0
      self.isabella.tocs_rule['storage'] = [[302.6,245,245,245,245,400,400,302.6],  [302.6,245,245,245,245,400,400,302.6]]
      self.kernriver.carryover = 170.0
    if t == 3816:
      self.isabella.capacity = 361.25
      self.isabella.tocs_rule['storage'] = [[302.6,170,170,245,245,361.25,361.25,302.6],  [302.6,170,170,245,245,361.25,361.25,302.6]]
      self.kernriver.carryover = 170.0
    if t == 2985:
      self.success.tocs_rule['storage'] = [[36.8,6.5,6.5,41.0,41.0,36.8] , [36.8,6.5,6.5,41.0,41.0,36.8]]
    if t == 3350:
      self.success.tocs_rule['storage'] = [[36.8,6.5,6.5,65.0,65.0,36.8] , [36.8,6.5,6.5,65.0,65.0,36.8]]
    if t == 3715:
      self.success.tocs_rule['storage'] = [[29.2,6.5,6.5,29.2,29.2,29.2] , [29.2,6.5,6.5,29.2,29.2,29.2]]
    if t == 4445:
      self.success.tocs_rule['storage'] = [[36.8,6.5,6.5,41.0,41.0,36.8] , [36.8,6.5,6.5,41.0,41.0,36.8]]
    if t == 5540:
      self.success.tocs_rule['storage'] = [[36.8,6.5,6.5,65.0,65.0,36.8] , [36.8,6.5,6.5,65.0,65.0,36.8]]
    if t == 6270:
      self.success.tocs_rule['storage'] = [[36.8,6.5,6.5,65.0,65.0,36.8] , [36.8,6.5,6.5,82.3,82.3,36.8]]

      for district_obj in self.district_list:
        district_obj.carryover_rights = {}
        for contract_obj in self.contract_list:
          if contract_obj.type == 'right':
            district_obj.carryover_rights[contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']
          else:
            district_obj.carryover_rights[contract_obj.name] = 0.0
      for private_obj in self.private_list:
        private_obj.carryover_rights = {}
        for district_key in private_obj.district_list:
          district_obj = self.district_keys[district_key]
          private_obj.carryover_rights[district_key] = {}
          for contract_obj in self.contract_list:
            if contract_obj.type == 'right':
              private_obj.carryover_rights[district_key][contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*private_obj.private_fraction[district_key][wateryear]
            else:
              private_obj.carryover_rights[district_key][contract_obj.name] = 0.0
      for private_obj in self.city_list:
        private_obj.carryover_rights = {}
        for district_key in private_obj.district_list:
          district_obj = self.district_keys[district_key]
          private_obj.carryover_rights[district_key] = {}
          for contract_obj in self.contract_list:
            if contract_obj.type == 'right':
              private_obj.carryover_rights[district_key][contract_obj.name] = contract_obj.carryover*district_obj.rights[contract_obj.name]['carryover']*private_obj.private_fraction[district_key][wateryear]
            else:
              private_obj.carryover_rights[district_key][contract_obj.name] = 0.0
		  

    if y == 2009 and dowy == 1:
      self.poso.initial_recharge = 420.0
      self.poso.recovery = 0.6942
      self.poso.tot_storage = 2.1
      self.find_all_triggers()
      self.fkc.capacity["normal"] = self.fkc.capacity["normal_wy2010"]


    if y == 2010 and dowy == 1:
      self.irvineranch.initial_recharge = 300.0
      self.irvineranch.recovery = 0.0479
      self.irvineranch.tot_storage = 0.594

    if y == 1998 and dowy == 1:
      self.berrenda.project_contract['tableA'] =  0.032076
      self.socal.project_contract['tableA'] = 0.63338264299
    if y == 1999 and dowy == 1:
      self.belridge.project_contract['tableA'] = 0.03636
    if y == 2000 and dowy == 1:
      self.southbay.project_contract['tableA'] = 0.05177514792
      self.belridge.project_contract['tableA'] = 0.03538
      self.berrenda.project_contract['tableA'] =  0.03035
      self.losthills.project_contract['tableA'] = 0.0293663708
      self.wheeler.project_contract['tableA'] =  0.04858926015
      self.socal.project_contract['tableA'] = 0.64423076923
    if y == 2001 and dowy == 1:
      self.southbay.project_contract['tableA'] = 0.05424063116
      self.belridge.project_contract['tableA'] = 0.0305
      self.berrenda.project_contract['tableA'] =  0.02837
    if y == 2004 and dowy == 1:
      self.belridge.project_contract['tableA'] = 0.02995607
      self.berrenda.project_contract['tableA'] =  0.02677
      self.southbay.project_contract['tableA'] = 0.0548863
      self.westkern.project_contract['tableA'] = 0.00776587
    if y == 2010 and dowy == 1:
      self.berrenda.project_contract['tableA'] =  0.02282922
      self.socal.project_contract['tableA'] = 0.648310
	  
    if y == 2002 and dowy == 1:
      self.kwbcanal.capacity["normal"] = [800.0, 800.0, 0.0, 0.0]
      self.kwbcanal.capacity["reverse"] = [0.0, 440.0, 800.0, 800.0]
      self.kwbcanal.capacity["closed"] = [0.0, 0.0, 0.0, 0.0]
      self.kwbcanal.turnout["normal"] = [800.0, 800.0, 0.0]
      self.kwbcanal.turnout["reverse"] = [0.0, 440.0, 800.0]
      self.kwbcanal.turnout["closed"] = [0.0, 0.0, 0.0]
      self.kwbcanal.flow_directions["recharge"]["caa"] = 'closed'
      self.kwbcanal.flow_directions["recharge"]["knc"] = 'closed'
      self.kwbcanal.flow_directions["recovery"]["caa"] = 'normal'
      self.kwbcanal.flow_directions["recovery"]["knc"] = 'normal'
      #self.fkc.flow_directions["recharge"]["xvc"] = 'normal'

      self.kwb.initial_recharge = 1212.12
      self.kwb.recovery = 0.7863
      self.kwb.tot_storage = 2.4
      self.init_tot_recovery()
      self.kerndelta.in_district_direct_recharge = 165.0
      self.kerndelta.in_district_storage = 0.326
      self.buenavista.in_district_direct_recharge = 333.3
      self.buenavista.in_district_storage = 0.66
      self.rosedale.in_district_direct_recharge = 606.1
      self.rosedale.in_district_storage = 1.2

	  
      self.find_all_triggers()
	  
      ####Calculates the requests for SWP allocations in WY 1997-2000
      ###when less than full allocation was requested by MWD.  This is unlikely to 
      ###occur in the future
    self.swpdelta.total = 4056.0
    if y == 1996:
      self.swpdelta.max_allocation = 2977.0
    elif y == 1997:
      self.swpdelta.max_allocation = 3191.0
    elif y == 1998:
      self.swpdelta.max_allocation = 3214.0
    elif y == 1999:
      self.swpdelta.max_allocation = 3617.0
    else:
      self.swpdelta.max_allocation = 4056.0
	  
    request_empty = self.swpdelta.total - self.swpdelta.max_allocation
    for district_obj in self.district_list:
      contractor_toggle = 0
      for contract_key in district_obj.contract_list:
        if contract_key == 'tableA':
          contractor_toggle = 1
      if contractor_toggle == 1:	  
        if district_obj.key == "SOC":
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total - request_empty
        elif district_obj.key == "SOB":
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total 
        elif district_obj.key == "CCA":
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total
        else:
          district_obj.table_a_request = district_obj.initial_table_a*self.swpdelta.total
    self.swpdelta.total = self.swpdelta.max_allocation
    for district_obj in self.district_list:
      contractor_toggle = 0
      for contract_key in district_obj.contract_list:
        if contract_key == 'tableA':
          contractor_toggle = 1
      if contractor_toggle == 1:	  
        district_obj.project_contract['tableA'] = district_obj.table_a_request/self.swpdelta.total
    

  def update_regulations_north(self,t,dowy,y):

	##Yuba River Accalfews_src, started in Jan of 2006 (repaces minimum flow requirements)
    if y >= 2006:
      self.yuba.env_min_flow = self.yuba.env_min_flow_ya
      self.yuba.temp_releases = self.yuba.temp_releases_ya
	  
    if y == 2008 and dowy == 1:
      for x in range(318, 334):
        self.delta.x2constraint['W'][x] = 77.0 - 3.0*(x-318)/16
        self.delta.x2constraint['AN'][x] = 81.0

      for x in range(334,366):
        self.delta.x2constraint['W'][x] = 74.0
        self.delta.x2constraint['AN'][x] = 81.0
      for x in range(0, 30):
        self.delta.x2constraint['W'][x] = 74.0
        self.delta.x2constraint['AN'][x] = 81.0
		
    #tucp orders during the drought can be found here:
	#https://www.waterboards.ca.gov/waterrights/water_issues/programs/drought/tucp/index.html
    if y == 2014 and dowy == 123:
      self.delta.min_outflow['C'][1] = 3000
      self.delta.min_outflow['C'][2] = 3000
      self.delta.min_outflow['C'][3] = 3000
      self.delta.min_outflow['C'][4] = 3000
      self.delta.min_outflow['C'][5] = 3000
      self.delta.min_outflow['C'][6] = 3000
	  
      self.delta.rio_vista_min['C'][8] = 2000
      self.delta.rio_vista_min['C'][9] = 2000
      self.delta.rio_vista_min['C'][10] = 2000
    elif y == 2014 and dowy == 228:
      self.delta.san_joaquin_min_flow['C'][2] = 500
    if y == 2014 and dowy == 1:
      self.delta.san_joaquin_min_flow['C'][2] = 500
      self.delta.rio_vista_min['C'][8] = 2500
      self.delta.rio_vista_min['C'][9] = 2500
      self.delta.rio_vista_min['C'][10] = 2500
      self.delta.new_vamp_rule['C'] = 710.0
    elif y == 2015 and dowy == 228:
      self.delta.san_joaquin_min_flow['C'][2] = 300
    elif y == 2015 and dowy == 242:
      self.delta.san_joaquin_min_flow['C'][2] = 200
	  
      #expected_outflow_req, expected_depletion = self.delta.calc_expected_delta_outflow(self.shasta.downstream,self.oroville.downstream,self.yuba.downstream,self.folsom.downstream, self.shasta.temp_releases, self.oroville.temp_releases, self.yuba.temp_releases, self.folsom.temp_releases)
      #expected_outflow_req = self.delta.min_outflow
      #expected_outflow_req['EC'] = expected_outflow_req['C']
      #inflow_list = [self.shasta, self.folsom, self.yuba, self.oroville]
      #for x in inflow_list:
        #x.calc_expected_min_release(self, expected_outflow_req, expected_depletion, 0)

    if y == 2015 and dowy == 1:
      self.delta.min_outflow['C'][1] = 7100
      self.delta.min_outflow['C'][2] = 7100
      self.delta.min_outflow['C'][3] = 7100
      self.delta.min_outflow['C'][4] = 7100
      self.delta.min_outflow['C'][5] = 7100
      self.delta.min_outflow['C'][6] = 4000
      self.delta.san_joaquin_min_flow['C'][2] = 1140
      self.delta.rio_vista_min['C'][8] = 3000
      self.delta.rio_vista_min['C'][9] = 3000
      self.delta.rio_vista_min['C'][10] = 3500
      self.delta.new_vamp_rule['C'] = 1500.0

      #expected_outflow_req, expected_depletion = self.delta.calc_expected_delta_outflow(self.shasta.downstream,self.oroville.downstream,self.yuba.downstream,self.folsom.downstream, self.shasta.temp_releases, self.oroville.temp_releases, self.yuba.temp_releases, self.folsom.temp_releases)
      #expected_outflow_req = self.delta.min_outflow
      #expected_outflow_req['EC'] = expected_outflow_req['C']
      #inflow_list = [self.shasta, self.folsom, self.yuba, self.oroville]
      #for x in inflow_list:
        #x.calc_expected_min_release(self, expected_outflow_req, expected_depletion, 0)

	  
  def proj_gains(self,t, dowy, m, year_index):
    cdef Reservoir reservoir_obj
    tot_sac_fnf = 0.0
    tot_sj_fnf = 0.0
    proj_surplus = np.zeros(12)
    proj_omr = np.zeros(12)
    for reservoir_obj in [self.shasta, self.oroville, self.yuba, self.folsom]:
      if t < 30:
        tot_sac_fnf += np.sum(reservoir_obj.fnf[0:t])*30.0/(t+1)
      else:
        tot_sac_fnf += np.sum(reservoir_obj.fnf[(t-30):t])
    for reservoir_obj in [self.newmelones, self.donpedro, self.exchequer, self.millerton]:
      if t < 30:
        tot_sj_fnf += np.sum(reservoir_obj.fnf[0:t])*30.0/(t+1)
      else:
        tot_sj_fnf += np.sum(reservoir_obj.fnf[(t-30):t])

    for x in range(0, 12):
      if x >= m:
        daysmonth = self.days_in_month[year_index][x]
      else:
        daysmonth = self.days_in_month[year_index + 1][x]
      proj_surplus[x] = max(self.delta_gains_regression['slope'][dowy][x]*min(tot_sac_fnf,4.0) + self.delta_gains_regression['intercept'][dowy][x], 0.0)
      proj_omr[x] = (self.delta.omr_regression['slope'][dowy][x]*tot_sj_fnf + self.delta.omr_regression['intercept'][dowy][x] + 5000.0*cfs_tafd*daysmonth)/0.94
    expected_pumping = {}
    expected_pumping['cvp'] = np.zeros(12)
    expected_pumping['swp'] = np.zeros(12)
    max_pumping = {}
    max_pumping['cvp'] = np.zeros(12)
    max_pumping['swp'] = np.zeros(12)


    for monthloop in range(0,12):
      if monthloop >= m:
        daysmonth = self.days_in_month[year_index][monthloop]
      else:
        daysmonth = self.days_in_month[year_index + 1][monthloop]
      if proj_surplus[monthloop]*0.55 > self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*daysmonth:
        expected_pumping['cvp'][monthloop] = self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*daysmonth
        expected_pumping['swp'][monthloop] = min(self.delta.pump_max['swp']['intake_limit'][0]*cfs_tafd*daysmonth, proj_surplus[monthloop] - self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*daysmonth)
      else:
        expected_pumping['cvp'][monthloop] = proj_surplus[monthloop]*0.55
        expected_pumping['swp'][monthloop] = proj_surplus[monthloop]*0.45
 		
      if monthloop < 6 and year_index + self.starting_year > self.delta.omr_rule_start:
        if proj_omr[monthloop]*0.5 > self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*daysmonth:
          max_pumping['cvp'][monthloop] = self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*daysmonth
          max_pumping['swp'][monthloop] = min(self.delta.pump_max['swp']['intake_limit'][0]*cfs_tafd*daysmonth, proj_omr[monthloop] - self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*daysmonth)
        else:
          max_pumping['cvp'][monthloop] = proj_omr[monthloop]*0.5
          max_pumping['swp'][monthloop] = proj_omr[monthloop]*0.5
		  
      else:
        max_pumping['cvp'][monthloop] = self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*daysmonth
        max_pumping['swp'][monthloop] = self.delta.pump_max['swp']['intake_limit'][0]*cfs_tafd*daysmonth

    return expected_pumping, max_pumping

		
  def find_wyt(self,index):
    if index <= 2.1:
      wyt = "C"
      self.isabella.forecastWYT = "C"
      self.success.forecastWYT = "C"
      self.kaweah.forecastWYT = "C"
      self.millerton.forecastWYT = "C"
    elif index <= 2.5:
      wyt = "D"
      self.isabella.forecastWYT = "D"
      self.success.forecastWYT = "D"
      self.kaweah.forecastWYT = "D"
      self.millerton.forecastWYT = "D"
    elif index <= 3.1:
      wyt = "BN"
      self.isabella.forecastWYT = "BN"
      self.success.forecastWYT = "BN"
      self.kaweah.forecastWYT = "BN"
      self.millerton.forecastWYT = "BN"
    elif index <= 3.8:
      wyt = "AN"
      self.isabella.forecastWYT = "AN"
      self.success.forecastWYT = "AN"
      self.kaweah.forecastWYT = "AN"
      self.millerton.forecastWYT = "AN"
    else:
      wyt = "W"
      self.isabella.forecastWYT = "W"
      self.success.forecastWYT = "W"
      self.kaweah.forecastWYT = "W"
      self.millerton.forecastWYT = "W"
    return wyt

  def calc_wytypes(self,t,dowy):
  
####NOTE:  Full natural flow data is in MAF, inflow data is in TAF  
##Index for Shasta Min Flows
############################
    if self.delta.forecastSRI[t] <= 5.4:
      self.shasta.forecastWYT = "C"
      self.delta.forecastSCWYT = "C"
    elif self.delta.forecastSRI[t] <= 6.6:
      self.shasta.forecastWYT = "D"
      self.delta.forecastSCWYT = "D" 
    elif self.delta.forecastSRI[t] <= 7.8:
      self.shasta.forecastWYT = "BN"
      self.delta.forecastSCWYT = "BN"
    elif self.delta.forecastSRI[t] <= 9.2:
      self.shasta.forecastWYT = "AN"
      self.delta.forecastSCWYT = "AN" 
    else:
      self.shasta.forecastWYT = "W"
      self.delta.forecastSCWYT = "W"

##Index for Oroville Min Flows
############################	  
    if self.oroville.snowflood_fnf[t] < 0.55*1.942:
      self.oroville.forecastWYT = "D"
    else:
      self.oroville.forecastWYT = "W"
    
    if self.delta.forecastSRI[t] <= 5.4:
      self.oroville.forecastWYT = "C"
  
##Index for Yuba Min Flows
############################	
    eos_date = t - dowy
    if eos_date < 0:
      eos_date = 0
	  
    yubaIndex = (self.yuba.rainflood_fnf[t] + self.yuba.snowflood_fnf[t])*1000 + self.yuba.S[eos_date] - 234.0
    if yubaIndex >= 1400:
      self.yuba.forecastWYT = "W" 
    elif yubaIndex >= 1040:
      self.yuba.forecastWYT = "AN"
    elif yubaIndex >= 920:
      self.yuba.forecastWYT = "BN"
    elif yubaIndex >= 820:
      self.yuba.forecastWYT = "D"
    elif yubaIndex >= 693:
      self.yuba.forecastWYT = "C"
    else:
      self.yuba.forecastWYT = "EC"
  
##Index for Folsom Min Flows
############################
##Folsom has the most ridiculous operating rules, and combines a bunch of different 'indicies' throughout the year to determine min flows	
    if dowy < 91:
      folsomIndex = self.folsom.S[eos_date] + (361.701 - self.folsom.fci[eos_date])
      if folsomIndex >= 848:
        self.folsom.forecastWYT = "W"
      elif folsomIndex >= 746:
        self.folsom.forecastWYT = "AN" 
      elif folsomIndex >= 600:
        self.folsom.forecastWYT = "BN" 
      elif folsomIndex >= 300:
        self.folsom.forecastWYT = "D"
      else:
        self.folsom.forecastWYT = "C"
    elif dowy < 150:
      folsomIndex = self.folsom.S[eos_date] + (361.701 - self.folsom.fci[eos_date])
      if self.delta.forecastSRI[t] <= 5.4 and folsomIndex < 600:
        self.folsom.forecastWYT = "C"
      elif self.delta.forecastSRI[t] <= 5.4 and folsomIndex < 746:
        self.folsom.forecastWYT = "D"
      elif self.delta.forecastSRI[t] <= 5.4 and folsomIndex < 848:
        self.folsom.forecastWYT = "AN"
      elif self.delta.forecastSRI[t] < 7.8 and folsomIndex < 600:
        self.folsom.forecastWYT = "D"
      elif self.delta.forecastSRI[t] < 7.8 and folsomIndex < 746:
        self.folsom.forecastWYT = "BN"
      else:
        self.folsom.forecastWYT = "W"
    else:
      folsomIndex = (self.folsom.snowflood_fnf[t] - sum(self.folsom.fnf[(t-dowy+181):(t-dowy+211)]) + sum(self.folsom.fnf[(t-dowy+304):(t-dowy+364)]))*1000
      if folsomIndex < 250:
        self.folsom.forecastWYT = "C"
      elif folsomIndex < 375:
        self.folsom.forecastWYT = "D"
      elif folsomIndex < 460:
        self.folsom.forecastWYT = "BN"
      elif folsomIndex < 550:
        self.folsom.forecastWYT = "AN"
      else:
        self.folsom.forecastWYT = "W"
  
##Index for New Melones Min Flows
############################
    if dowy <= 150:
      eof_storage = t - dowy - 215
      if eof_storage < 0:
        eof_storage == 0
      newmelonesIndex = self.newmelones.S[eof_storage] + sum(self.newmelones.fnf[(eof_storage+1):(t-dowy)])*1000
    else:
      eof_storage = t - dowy + 149
      newmelonesIndex = self.newmelones.S[eof_storage] + (sum(self.newmelones.fnf[(eof_storage+1):(t-dowy+181)]) + self.newmelones.snowflood_fnf[t] + sum(self.newmelones.fnf[(t-dowy+304):(t-dowy+365)]))*1000
	
    if newmelonesIndex < 1400:
      self.newmelones.forecastWYT = "C"
    elif newmelonesIndex < 2000:
      self.newmelones.forecastWYT = "D"
    elif newmelonesIndex < 2500:
      self.newmelones.forecastWYT = "BN"
    elif newmelonesIndex < 3000:
      self.newmelones.forecastWYT = "AN"
    else:
      self.newmelones.forecastWYT = "W"
  
##Index for Don Pedro Min Flows
############################
    if self.delta.forecastSJI[t] <= 2.1:
      self.donpedro.forecastWYT = "C"
      self.delta.forecastSJWYT = "C"
    elif self.delta.forecastSJI[t] <= 2.5:
      self.donpedro.forecastWYT = "D"
      self.delta.forecastSJWYT = "D"
    elif self.delta.forecastSJI[t] <= 3.1:
      self.donpedro.forecastWYT = "BN"
      self.delta.forecastSJWYT = "BN"
    elif self.delta.forecastSJI[t] <= 3.8:
      self.donpedro.forecastWYT = "AN"
      self.delta.forecastSJWYT = "AN"
    else:
      self.donpedro.forecastWYT = "W"
      self.delta.forecastSJWYT = "W"
    
  
##Index for Exchequer Min Flows
############################	  
    if self.exchequer.snowflood_fnf[t] < .45:
      self.exchequer.forecastWYT = "D"
    else:
      self.exchequer.forecastWYT = "AN"
  	
    return newmelonesIndex


