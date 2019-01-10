import numpy as np
import pandas as pd
import collections as cl
import sys
import calendar
import matplotlib.pyplot as plt
from .reservoir import Reservoir
from .delta import Delta
from .district import District
from .contract import Contract
from .canal import Canal
from .waterbank import Waterbank
from .util import *


class Model():

  def __init__(self, datafile, sd):
    ##Set model dataset & index length
    self.df = pd.read_csv(datafile, index_col=0, parse_dates=True)
    self.index = self.df.index
    self.T = len(self.df)
    self.starting_year = int(self.index.year[0])
    self.ending_year = int(self.index.year[self.T-1])
    self.current_day_year = self.index.dayofyear
    self.current_year = self.index.year
    self.current_month = self.index.month
    self.current_day_month = self.index.day

	
#####################################################################################################################
#############################     Object Creation     ###############################################################
#####################################################################################################################
  def northern_initialization_routine(self, model_mode):
######################################################################################
######################################################################################
#preprocessing for the northern system
######################################################################################
#initialize reservoirs 
#generates - regression coefficients & standard deviations for flow predictions (fnf & inf)
#(at each reservoir)
#self.res.rainflood_fnf; self.res.snowflood_fnf
#self.res.rainflood_inf; self.res.snowflood_inf; self.res.baseline_inf
#self.res.rainfnf_stds; self.res.snowfnf_stds
#self.res.raininf_stds; self.res.snowinf_stds; self.res.baseinf_stds
#self.res.flow_shape - monthly fractions of total period flow
    self.initialize_northern_res(model_mode)
    expected_release_datafile = 'cord/data/cord-data.csv'
    print('Initialize Northern Reservoirs')
#initialize delta rules, calcluate expected environmental releases at each reservoir
#generates - cumulative environmental/delta releases remaining (at each reservoir)
#self.res.cum_min_release; self.res.aug_sept_min_release; self.res.oct_nov_min_release
    self.initialize_delta_ops(model_mode, expected_release_datafile)
    print('Initialize Delta Ops')

######
#calculate projection-based flow year indicies using flow & snow inputs
##note: these values are pre-processed, but represent no 'foresight' WYT & WYI index use
#snow-based projections to forecast flow, calculate running WY index & WYT
#generates:
#self.delta.forecastSJI (self.T x 1) - forecasts for san joaquin river index
#self.delta.forecastSRI (self.T x 1) - forecasts for sacramento river index
    self.find_running_WYI()
    print('Find Water Year Indicies')

######
#calculate expected 'unstored' pumping at the delta (for predictions into San Luis)
#this generates:
#self.delta_gains_regression (365x2) - linear coeffecicients for predicting total unstored pumping, oct-mar, based on ytd full natural flow
#self.delta_gains_regression2 (365x2) - linear coeffecicients for predicting total unstored pumping, apr-jul, based on ytd full natural flow
#self.month_averages (12x1) - expected fraction of unstored pumping to come in each month (fraction is for total period flow, so 0.25 in feb is 25% of total oct-mar unstored flow)
    self.predict_delta_gains(expected_release_datafile)
    print('Find Delta Gains')
    if model_mode != 'validation':
      self.set_regulations_current_north()
    return self.delta.omr_rule_start, self.delta.max_tax_free
######################################################################################
  def southern_initialization_routine(self, model_mode):
######################################################################################
#preprocessing for the southern system
######################################################################################
#initialize the southern reservoirs -
#generates - same values as initialize_northern_res(), but for southern reservoirs
    self.initialize_southern_res(model_mode)
    print('Initialize Southern Reservoirs')
#initialize water districts for southern model 
#generates - water district parameters (see cord-combined/cord/districts/readme.txt)
#self.district_list - list of district objects
#self.district_keys - dictionary pairing district keys w/district class objects
    self.initialize_water_districts()
    print('Initialize Water Districts')
#initialize water contracts for southern model
#generates - water contract parameters (see cord-combined/cord/contracts/readme.txt)
#self.contract_list - list of contract objects
#self.contract_keys - dictionary pairing contract keys w/contract class objects
#self.res.contract_carryover_list - record of carryover space afforded to each contract (for all district)
    self.initialize_sw_contracts()
    print('Initialize Contracts')
#initialize water banks for southern model
#generates - water bank parameters (see cord-combined/cord/banks/readme.txt)
#self.waterbank_list - list of waterbank objects
#self.leiu_list - list of district objects that also operate as 'in leiu' or 'direct recharge' waterbanks
    self.initialize_water_banks()
    print('Initialize Water Banks')
#initialize canals/waterways for southern model
#generates - canal parameters (see cord-combined/cord/canals/readme.txt)
#self.canal_list - list of canal objects
    self.initialize_canals()
    print('Initialize Canals')
    if model_mode != 'validation':
      self.set_regulations_current_south()

#create dictionaries that structure the relationships between
#reservoirs, canals, districts, waterbanks, and contracts
#generates:
#self.canal_district - dict keys are canals, object lists place reservoirs, waterbanks, districts & other canals in order on a given canal
#self.canal_priority - dict keys are canals, object lists are the 'main' canals that have 'priority' on the other canals (through turnouts)
#self.reservoir_contract - dict keys are reservoirs, object lists are contracts stored in that reservoir
#self.contract_reservoir - dict keys are contracts, objects (single) are reservoirs where that contract is stored (inverse of reservoir_contract)
#self.canal_contract - dict keys are canals, object lists are contracts that have priority on those canals (primarily for flood flows)
#self.reservoir_canal - dict keys are reservoirs, object lists are canal(s) that connect to the reservoir (note - only millerton has more than one canal)
#Also initializes some canal properties
#self.canal.demand - dictionary for the different types of demand that can be created at each canal node (note - these values are updated within model steps)
#self.canal.flow - vector recording flow to a node on a canal (note - these values are updated within model steps)
#self.canal.turnout_use - vector recording diversions to a node on a canal (note - these values are updated within model steps)
    self.create_object_associations()
    print('Create Object Associations')
###Applies initial carryover balances to districts
##based on initial reservoir storage conditions
##PLEASE NOTE CARRYOVER STORAGE IN SAN LUIS IS HARD-CODED
    self.find_initial_carryover()
    print('Initialize Carryover Storage')
##initial recovery capacities for districts, based on
##ownership stakes in waterbanks (direct + inleui)
    self.init_tot_recovery()
    print('Initialize Recovery Capacity')
##initial recharge capacities (projected out 12 months) for districts,
##based on ownership stakes in waterbanks (direct + inleui + indistrict)
    urban_datafile = 'cord/data/cord-data-urban.csv'
    urban_datafile_cvp = 'cord/data/pump-data-cvp.csv'
    self.project_urban(urban_datafile, urban_datafile_cvp, model_mode)

#calculate how much recharge capacity is reachable from each reservoir 
#that is owned by surface water contracts held at that reservoir - used to determine
#how much flood water can be released and 'taken' by a contractor
    self.find_all_triggers()
    print('Find Triggers')	
  
  
  
  def initialize_northern_res(self, model_mode):
    #########################################################################################
	#reservoir initialization for the northern delta system
    #########################################################################################
    #4 Sacramento River Reservoirs (CVP & SWP)
    self.shasta = Reservoir(self.df, 'SHA', model_mode)
    self.folsom = Reservoir(self.df, 'FOL', model_mode)
    self.oroville = Reservoir(self.df, 'ORO', model_mode)
    self.yuba = Reservoir(self.df,'YRS', model_mode)
	
    #3 San Joaquin River Reservoirs (to meet Vernalis flow targets)
    self.newmelones = Reservoir(self.df,'NML', model_mode)
    self.donpedro = Reservoir(self.df,'DNP', model_mode)
    self.exchequer = Reservoir(self.df,'EXC', model_mode)
	
    #Millerton Reservoir (flows used to calculate San Joaquin River index, not in northern simulation)
    self.millerton = Reservoir(self.df,'MIL', model_mode)
    reservoir_list = [self.shasta, self.oroville, self.folsom, self.yuba, self.newmelones, self.donpedro, self.exchequer, self.millerton]
    ##Regression flow & standard deviations read from file
	#### Find regression information for all 8 reservoirs
    if model_mode == 'forecast':
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      df_res_process = pd.DataFrame()
      df_res_annual = pd.DataFrame()
      for x in reservoir_list:
        x.find_release_func()
      ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      expected_flow_shape_datafile = 'cord/data/cord-data.csv' 
      for x in reservoir_list:
        x.create_flow_shapes(expected_flow_shape_datafile)
    elif model_mode == 'validation':
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      #df_res_process = pd.DataFrame()
      #df_res_annual = pd.DataFrame()
      #for x in reservoir_list:
        #x.find_release_func()
        #df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        #df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        #df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        #df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        #df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)

        #df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        #df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        #df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        #df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        #df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)

      #df_res_process.to_csv('cord/data/no_res_preprocess_daily.csv')
      #df_res_annual.to_csv('cord/data/no_res_presprocess_annual.csv')
      flow_estimates = pd.read_csv('cord/data/no_res_preprocess_daily.csv', index_col=0, parse_dates=True)
      std_estimates = pd.read_csv('cord/data/no_res_presprocess_annual.csv')
      for x in reservoir_list:
        x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]##FNF, OCT-MAR, LINEAR COEF
        x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]##FNF, APR-JUL, LINEAR COEF
        x.rainflood_inf = flow_estimates['%s_raininf' % x.key]##INF, OCT-MAR, LINEAR COEF
        x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]##INF, APR-JUL, LINEAR COEF
        x.baseline_inf = flow_estimates['%s_baseinf' % x.key]##INF, AUG-SEPT, LINEAR COEF
        x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]##FNF, OCT-MAR, STD
        x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]##FNF, APR-JUL, STD
        x.raininf_stds = std_estimates['%s_raininfstd' % x.key]##INF, OCT-MAR, STD
        x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]##INF, APR-JUL, STD
        x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]##INF, AUG-SEPT, STD
      ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      #df_flow_shape_no = pd.DataFrame()
      expected_flow_shape_datafile = 'cord/data/cord-data.csv' 
      for x in reservoir_list:
        x.create_flow_shapes(expected_flow_shape_datafile)
    else:
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      #df_res_process = pd.DataFrame()
      #df_res_annual = pd.DataFrame()
      #for x in reservoir_list:
        #x.find_release_func()
        #df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        #df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        #df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        #df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        #df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)

        #df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        #df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        #df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        #df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        #df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
      #df_res_process.to_csv('cord/data/no_res_preprocess_simulation_daily.csv')
      #df_res_annual.to_csv('cord/data/no_res_presprocess_simulation_annual.csv')
      flow_estimates = pd.read_csv('cord/data/no_res_preprocess_simulation_daily.csv')
      std_estimates = pd.read_csv('cord/data/no_res_presprocess_simulation_annual.csv')
      for x in reservoir_list:
        x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]##FNF, OCT-MAR, LINEAR COEF
        x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]##FNF, APR-JUL, LINEAR COEF
        x.rainflood_inf = flow_estimates['%s_raininf' % x.key]##INF, OCT-MAR, LINEAR COEF
        x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]##INF, APR-JUL, LINEAR COEF
        x.baseline_inf = flow_estimates['%s_baseinf' % x.key]##INF, AUG-SEPT, LINEAR COEF
        x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]##FNF, OCT-MAR, STD
        x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]##FNF, APR-JUL, STD
        x.raininf_stds = std_estimates['%s_raininfstd' % x.key]##INF, OCT-MAR, STD
        x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]##INF, APR-JUL, STD
        x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]##INF, AUG-SEPT, STD
	  
	  ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      #df_flow_shape_no = pd.DataFrame()
      expected_flow_shape_datafile = 'cord/data/cord-data.csv' 
      for x in reservoir_list:
        x.create_flow_shapes(expected_flow_shape_datafile)
        #df_flow_shape_no['%s_slope' % x.key] = pd.Series(x.flow_shape['slope'])
        #df_flow_shape_no['%s_intercept' % x.key] = pd.Series(x.flow_shape['intercept'])
      ##save flow shapes for the northern model
      #df_flow_shape_no.to_csv('cord/data/flow_shape_no_simulation.csv')
      flow_shape_files = pd.read_csv('cord/data/flow_shape_no_simulation.csv')
      for x in reservoir_list:
        x.flow_shape = {}
        x.flow_shape['slope'] = flow_shape_files['%s_slope' % x.key]
        x.flow_shape['intercept'] = flow_shape_files['%s_intercept' % x.key]
    #########################################################################################

  def initialize_delta_ops(self, model_mode, datafile):
	#########################################################################################
    ##initialization of the delta rules
    #########################################################################################
    self.delta = Delta(self.df, 'DEL', model_mode)
	###Find expected reservoir releases to meet delta requirements - used in flow forecasting
    ###these use the flow 'gains' on each tributary stretch to find the expected extra releases required to meet env & delta mins
    df_short = pd.read_csv(datafile, index_col=0, parse_dates=True)
    index_short = df_short.index
    T_short = len(df_short)
    gains_sac_short = df_short.SAC_gains * cfs_tafd
    gains_sj_short = df_short.SJ_gains * cfs_tafd
    depletions_short = df_short.delta_depletions * cfs_tafd
    eastside_streams_short = df_short.EAST_gains * cfs_tafd
    inflow_list = [self.shasta, self.folsom, self.yuba, self.oroville, self.newmelones, self.donpedro, self.exchequer]
    for x in inflow_list:
      x.downstream_short = df_short['%s_gains'% x.key].values * cfs_tafd
 
    ##in addition to output variables, this generates:
	#self.max_tax_free (5x2x365) - using delta outflow min, calculate how much pumping can occur without paying any additional I/E 'tax' (b/c some inflow is already used for delta outflow requirements)
    expected_outflow_req, expected_depletion = self.delta.calc_expected_delta_outflow(self.shasta.downstream_short,self.oroville.downstream_short,self.yuba.downstream_short,self.folsom.downstream_short, self.shasta.temp_releases, self.oroville.temp_releases, self.yuba.temp_releases, self.folsom.temp_releases, gains_sac_short, gains_sj_short, depletions_short, eastside_streams_short, T_short, index_short)
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
    for x in inflow_list:
      x.calc_expected_min_release(expected_outflow_req, expected_depletion, 0, T_short, index_short)
	  
    expected_flow_shape_datafile = 'cord/data/cord-data.csv' 
    self.delta.create_flow_shapes_omr(expected_flow_shape_datafile)

  def initialize_southern_res(self, model_mode):
    ############################################################################
    ###Reservoir Initialization
	############################################################################
    self.millerton = Reservoir(self.df,'MIL', model_mode)
    self.pineflat = Reservoir(self.df,'PFT', model_mode)
    self.kaweah = Reservoir(self.df,'KWH', model_mode)
    self.success = Reservoir(self.df,'SUC', model_mode)
    self.isabella = Reservoir(self.df,'ISB', model_mode)
    ###San Luis is initialized as a Reservoir, but
    ###has none of the watershed data that goes along with the other reservoirs
    self.sanluis = Reservoir(self.df,'SNL', model_mode)
    self.sanluisstate = Reservoir(self.df, 'SLS', model_mode)
    self.sanluisfederal = Reservoir(self.df, 'SLF', model_mode)
    self.reservoir_list = [self.sanluisstate, self.sanluisfederal, self.millerton, self.isabella, self.success, self.kaweah]
    if model_mode == 'forecast':
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      for x in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
        x.find_release_func()
      expected_flow_shape_datafile = 'cord/data/cord-data.csv' 
      for x in [self.millerton, self.isabella, self.success, self.kaweah]:
        x.create_flow_shapes(expected_flow_shape_datafile)
    elif model_mode == 'validation':
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      #df_res_process = pd.DataFrame()
      #df_res_annual = pd.DataFrame()
      #for x in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
        #x.find_release_func()
        #df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        #df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        #df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        #df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        #df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)

        #df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        #df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        #df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        #df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        #df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
      #df_res_process.to_csv('cord/data/res_preprocess_daily.csv')
      #df_res_annual.to_csv('cord/data/res_presprocess_annual.csv')
	  
      ##Regression flow & standard deviations read from file (see end of function for code to generate files)	  
      flow_estimates = pd.read_csv('cord/data/res_preprocess_daily.csv', index_col=0, parse_dates=True)
      std_estimates = pd.read_csv('cord/data/res_presprocess_annual.csv')
	  #### Find regression information for all 8 reservoirs 
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      for x in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
        x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]#FNF, Oct-Mar, Linear coefficients
        x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]#FNF, Apr-Jul, Linear coefficients
        x.rainflood_inf = flow_estimates['%s_raininf' % x.key]#INF, Oct-Mar, Linear coefficients
        x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]#INF, Apr-Jul, Linear coefficients
        x.baseline_inf = flow_estimates['%s_baseinf' % x.key]#INF, Aug-Sept, Linear coefficients
        x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]#FNF, Oct-Mar, STD
        x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]#FNF, Apr-Jul, STD
        x.raininf_stds = std_estimates['%s_raininfstd' % x.key]#INF, Oct-Mar, STD
        x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]#INF, Apr-Jul, STD
        x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]#INF, Aug-Sept, STD
		
      ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      expected_flow_shape_datafile = 'cord/data/cord-data.csv' 
      for x in [self.millerton, self.isabella, self.success, self.kaweah]:
        x.create_flow_shapes(expected_flow_shape_datafile)
    else:
	  ### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
      reservoir_list = [self.millerton, self.isabella, self.pineflat, self.kaweah, self.success]
      #df_res_process = pd.DataFrame()
      #df_res_annual = pd.DataFrame()
      #for x in reservoir_list:
        #x.find_release_func()
        #df_res_process['%s_rainfnf' %x.key] = pd.Series(x.rainflood_fnf, index = self.index)
        #df_res_process['%s_snowfnf' %x.key] = pd.Series(x.snowflood_fnf, index = self.index)
        #df_res_process['%s_raininf' %x.key] = pd.Series(x.rainflood_inf, index = self.index)
        #df_res_process['%s_snowinf' %x.key] = pd.Series(x.snowflood_inf, index = self.index)
        #df_res_process['%s_baseinf' %x.key] = pd.Series(x.baseline_inf, index = self.index)

        #df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
        #df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
        #df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
        #df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
        #df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)
      #df_res_process.to_csv('cord/data/so_res_preprocess_simulation_daily.csv')
      #df_res_annual.to_csv('cord/data/so_res_presprocess_simulation_annual.csv')
      flow_estimates = pd.read_csv('cord/data/so_res_preprocess_simulation_daily.csv')
      std_estimates = pd.read_csv('cord/data/so_res_presprocess_simulation_annual.csv')
      for x in reservoir_list:
        x.rainflood_fnf = flow_estimates['%s_rainfnf' % x.key]##FNF, OCT-MAR, LINEAR COEF
        x.snowflood_fnf = flow_estimates['%s_snowfnf' % x.key]##FNF, APR-JUL, LINEAR COEF
        x.rainflood_inf = flow_estimates['%s_raininf' % x.key]##INF, OCT-MAR, LINEAR COEF
        x.snowflood_inf = flow_estimates['%s_snowinf' % x.key]##INF, APR-JUL, LINEAR COEF
        x.baseline_inf = flow_estimates['%s_baseinf' % x.key]##INF, AUG-SEPT, LINEAR COEF
        x.rainfnf_stds = std_estimates['%s_rainfnfstd' % x.key]##FNF, OCT-MAR, STD
        x.snowfnf_stds = std_estimates['%s_snowfnfstd' % x.key]##FNF, APR-JUL, STD
        x.raininf_stds = std_estimates['%s_raininfstd' % x.key]##INF, OCT-MAR, STD
        x.snowinf_stds = std_estimates['%s_snowinfstd' % x.key]##INF, APR-JUL, STD
        x.baseinf_stds = std_estimates['%s_baseinfstd' % x.key]##INF, AUG-SEPT, STD
	  
	  ###Flow shapes are regressions that determine % of remaining flow in a period (Oct-Mar; Apr-Jul; Aug-Sept)
	  ###that is expected to come, regressed against the total flow already observed in that period
	  ###regressions are done for each reservoir, and values are calculated for each month (i.e., 33% of remaining Apr-Jul flow comes in May)
      expected_flow_shape_datafile = 'cord/data/cord-data.csv' 
      for x in reservoir_list:
        x.create_flow_shapes(expected_flow_shape_datafile)
    #########################################################################################	  

    #Tulare Basin Reservoirs do not need to release to the delta, so they only use their own
    #environmental flow requirements when calculating expected environmental releases
	#arguements passed into the function here are equal to zero
    expected_outflow_releases = {}
    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      expected_outflow_releases[wyt] = np.zeros(366)
    df_short = pd.read_csv('cord/data/cord-data.csv', index_col=0, parse_dates=True)
    index_short = df_short.index
    T_short = len(df_short)
    inflow_list = [self.millerton, self.pineflat, self.kaweah, self.success, self.isabella]
    for x in inflow_list:
      x.downstream_short = df_short['%s_gains'% x.key].values * cfs_tafd

    for x in inflow_list:
      #generates:
      #x.cum_min_release (5 x 365) - daily values of remaining enviromental releases through the end of july, in each wyt
      #x.aug_sept_min_release (5 x 365) - daily values of remaining enviromental releases during the aug-sept period, in each wyt
      #x.oct_nov_min_release (5 x 365) - daily values of remaining enviromental releases during the oct-nov period, in each wyt
      if x.key == "MIL":
        x.calc_expected_min_release(expected_outflow_releases, np.zeros(12), 1, T_short, index_short)
      else:
        x.calc_expected_min_release(expected_outflow_releases, np.zeros(12), 0, T_short, index_short)
	  
    ##Code to calculate snow/flow regressions and save to file
	############################################################################
    #self.pineflat.find_release_func()
    #self.kaweah.find_release_func()
    #self.success.find_release_func()
    #self.isabella.find_release_func()
    #self.millerton.find_release_func()	
    #df_res_process = pd.DataFrame()
    #df_res_annual = pd.DataFrame()
    #for x in [self.pineflat, self.kaweah, self.success, self.isabella, self.millerton]:
      #df_res_process['%s_rainfnf' % x.key] = pd.Series(x.rainflood_fnf, index = self.index)
      #df_res_process['%s_snowfnf' % x.key] = pd.Series(x.snowflood_fnf, index = self.index)
      #df_res_process['%s_raininf' % x.key] = pd.Series(x.rainflood_inf, index = self.index)
      #df_res_process['%s_snowinf' % x.key] = pd.Series(x.snowflood_inf, index = self.index)
      #df_res_process['%s_baseinf' % x.key] = pd.Series(x.baseline_inf, index = self.index)
      #df_res_annual['%s_rainfnfstd' % x.key] = pd.Series(x.rainfnf_stds)
      #df_res_annual['%s_snowfnfstd' % x.key] = pd.Series(x.snowfnf_stds)
      #df_res_annual['%s_raininfstd' % x.key] = pd.Series(x.raininf_stds)
      #df_res_annual['%s_snowinfstd' % x.key] = pd.Series(x.snowinf_stds)
      #df_res_annual['%s_baseinfstd' % x.key] = pd.Series(x.baseinf_stds)

    #df_res_process.to_csv('cord/data/res_preprocess_daily.csv')
    #df_res_annual.to_csv('cord/data/res_presprocess_annual.csv')
	
  def initialize_water_districts(self):		  
    ############################################################################
    ###District Initialization
	############################################################################
	##Kern County Water Agency Member Units
    self.berrenda = District(self.df, 'BDM')
    self.belridge = District(self.df, 'BLR')
    self.buenavista = District(self.df, 'BVA')
    self.cawelo = District(self.df, 'CWO')
    self.henrymiller = District(self.df, 'HML')
    self.ID4 = District(self.df, 'ID4')
    self.kerndelta = District(self.df, 'KND')
    self.losthills = District(self.df, 'LHL')
    self.rosedale = District(self.df, 'RRB')
    self.semitropic = District(self.df, 'SMI')
    self.tehachapi = District(self.df, 'THC')
    self.tejon = District(self.df, 'TJC')
    self.westkern = District(self.df, 'WKN')
    self.wheeler = District(self.df, 'WRM')
    self.kcwa = District(self.df, 'KCWA')
	##Other Kern County
    self.bakersfield = District(self.df, 'COB')
    self.northkern = District(self.df, 'NKN')
    ##Friant Kern Contractors
    self.arvin = District(self.df, 'ARV')
    self.delano = District(self.df, 'DLE')
    self.exeter = District(self.df, 'EXE')
    self.kerntulare = District(self.df, 'KRT')
    self.lindmore = District(self.df, 'LND')
    self.lindsay = District(self.df, 'LDS')
    self.lowertule = District(self.df, 'LWT')
    self.porterville = District(self.df, 'PRT')
    self.saucelito = District(self.df, 'SAU')
    self.shaffer = District(self.df, 'SFW')
    self.sosanjoaquin = District(self.df, 'SSJ')
    self.teapot = District(self.df, 'TPD')
    self.terra = District(self.df, 'TBA')
    self.tulare = District(self.df, 'TUL')
    self.fresno = District(self.df, 'COF')
    self.fresnoid = District(self.df, 'FRS')
    ##Canal Boundaries
    self.socal = District(self.df, 'SOC')
    self.southbay = District(self.df, 'SOB')
    self.centralcoast = District(self.df, 'CCA')
    ##demands at canal boundaries are taken from observed pumping into canal brannch

    ##Other Agencies
    self.dudleyridge = District(self.df, 'DLR')
    self.tularelake = District(self.df, 'TLB')
    self.westlands = District(self.df, 'WSL')
    self.chowchilla = District(self.df, 'CWC')
    self.maderairr = District(self.df, 'MAD')
    self.othertule = District(self.df, 'OTL')
    self.otherkaweah = District(self.df, 'OKW')
    self.otherfriant = District(self.df, 'OFK')
    self.othercvp = District(self.df, 'OCD')
    self.otherexchange = District(self.df, 'OEX')
    self.othercrossvalley = District(self.df, 'OXV')
    self.otherswp = District(self.df, 'OSW')
	
	##List of all intialized districts for looping
    self.district_list = [self.berrenda, self.belridge, self.buenavista, self.cawelo, self.henrymiller, self.ID4, self.kerndelta, self.losthills, self.rosedale, self.semitropic, self.tehachapi, self.tejon, self.westkern, self.wheeler, self.kcwa, self.bakersfield, self.northkern, self.arvin, self.delano, self.exeter, self.kerntulare, self.lindmore, self.lindsay, self.lowertule, self.porterville, self.saucelito, self.shaffer, self.sosanjoaquin, self.teapot, self.terra, self.tulare, self.fresno, self.fresnoid, self.socal, self.southbay, self.centralcoast, self.dudleyridge, self.tularelake, self.westlands, self.chowchilla, self.maderairr, self.othertule, self.otherkaweah, self.otherfriant, self.othercvp, self.otherexchange, self.othercrossvalley, self.otherswp]
    #list of all california aqueduct branch urban users (their demands are generated from pumping data - different than other district objects)
    self.urban_list = [self.socal, self.centralcoast, self.southbay]
	
    ##District Keys - dictionary to be able to call the member from its key
    self.district_keys = {}
    for districts_included in self.district_list:
      self.district_keys[districts_included.key] = districts_included
    self.district_keys['PVT'] = [self.berrenda, self.belridge, self.losthills]###Private interests in the Kern Water Bank (Westside Mutual)
    
  def initialize_sw_contracts(self):
    ############################################################################
    ###Contract Initialization
	############################################################################
   	#Project Contracts/Water Rights
    self.friant1 = Contract(self.df, 'FR1')
    self.friant2 = Contract(self.df, 'FR2')
    self.swpdelta = Contract(self.df, 'SLS')
    self.cvpdelta = Contract(self.df, 'SLF')
    self.cvpexchange = Contract(self.df, 'ECH')
    self.crossvalley = Contract(self.df, 'CVC')
    self.kernriver = Contract(self.df, 'KRR')
    self.tuleriver = Contract(self.df, 'TRR')
    self.kaweahriver = Contract(self.df, 'WRR')
	
	##List of all intialized contracts for looping
    self.contract_list = [self.friant1, self.friant2, self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley, self.kernriver, self.tuleriver, self.kaweahriver]
	
    ##Contract Keys - dictionary to be able to call the member from its key	
    self.contract_keys = {}
    for contract_options in self.contract_list:
      self.contract_keys[contract_options.name] = contract_options
	  
    ##For each district on the district list, find the total carryover storage
    ##they have associated with each contract
    ##Dictionary is a part of the district class, and dictionary keys are the names of contract types
    for x in self.district_list:
      for y in x.contract_list:
        contract_object = self.contract_keys[y]
        if contract_object.type == "contract":
          x.contract_carryover_list[y] = contract_object.carryover*x.project_contract[y]
        elif contract_object.type == "right":
          x.contract_carryover_list[y] = contract_object.carryover*x.rights[y]['carryover']
        if y == "tableA":
          x.initial_table_a = x.project_contract[y]

  def initialize_water_banks(self):
    ############################################################################
    ###Water Bank Initialization
	############################################################################
		  
	##Water Banks
    self.stockdale = Waterbank(self.df, 'STOCK')
    self.kernriverbed = Waterbank(self.df, 'KRC')
    self.poso = Waterbank(self.df, 'POSO')
    self.rosedale21 = Waterbank(self.df, 'R21')
    self.pioneer = Waterbank(self.df, 'PIO')
    self.kwb = Waterbank(self.df, 'KWB')
    self.berrendawb = Waterbank(self.df, 'BRM')
    self.b2800 = Waterbank(self.df, 'B2800')
    self.aewb = Waterbank(self.df, 'AEMWD')
    self.wkwb = Waterbank(self.df, 'WKB')
    self.irvineranch = Waterbank(self.df, 'IVR')
    self.northkernwb = Waterbank(self.df, 'NKB')
	
    self.waterbank_list = [self.stockdale, self.kernriverbed, self.poso, self.rosedale21, self.pioneer, self.kwb, self.berrendawb, self.b2800, self.wkwb, self.irvineranch, self.northkernwb]
    self.leiu_list = [self.semitropic, self.arvin]##these are districts that operate water banks (some mix of in-leiu deliveries and direct recharge)
    
  def initialize_canals(self):
    ############################################################################
    ###Canal Initialization
	############################################################################
    #Waterways
    self.fkc = Canal(self.df, 'FKC')
    self.xvc = Canal(self.df, 'XVC')
    self.madera = Canal(self.df, 'MDC')
    self.calaqueduct = Canal(self.df, 'CAA')
    self.kwbcanal = Canal(self.df, 'KBC')
    self.aecanal = Canal(self.df, 'AEC')
    self.kerncanal = Canal(self.df, 'KNC')
    self.gooseslough = Canal(self.df, 'GSL')
    self.calloway = Canal(self.df, 'CWY')
    self.lerdo = Canal(self.df, 'LRD')
    self.beardsley = Canal(self.df, 'BLY')
    self.kernriverchannel = Canal(self.df, 'KNR')
    self.kaweahriverchannel = Canal(self.df, 'KWR')
    self.tuleriverchannel = Canal(self.df, 'TLR')
	
    self.canal_list = [self.fkc, self.madera, self.xvc, self.calaqueduct, self.kwbcanal, self.aecanal, self.kerncanal, self.gooseslough, self.calloway, self.lerdo, self.beardsley, self.kernriverchannel, self.kaweahriverchannel, self.tuleriverchannel]

    #initialize variables to store pumping from delta	
    self.trp_pumping = np.zeros(self.T)
    self.hro_pumping = np.zeros(self.T)
    self.cvp_allocation = np.zeros(self.T)
    self.swp_allocation = np.zeros(self.T)
    self.annual_SWP = np.zeros(self.ending_year - self.starting_year)
    self.annual_CVP = np.zeros(self.ending_year - self.starting_year)
    self.ytd_pump_trp = np.zeros(self.T)
    self.ytd_pump_hro = np.zeros(self.T)

	
  def create_object_associations(self):
    ##Canal Structure Dictionary
    #This is the dictionary that holds the structure of the canal system.  The dictionary is made up of lists, with the objects in the lists representing delivery nodes on the canal (canal is denoted by dictionary key)
	#Objects can be districts, waterbanks, or other canals.  Canal objects show an intersection with the canal represented by the dictionary 'key' that holds the list.  Dictionary keys are all canal keys.  If a canal is located on a list, the canal associated with that list's key will also be on the list associated with the canal of the first key (i.e., if self.fkc is on the list with the key 'self.canal_district['xvc'], then the object self.xvc will be on the list with the key self.canal_district['fkc'] - these intersections help to organize these lists into a structure that models the interconnected canal structure
	#The first object on each list is either a reservoir or another canal
    self.canal_district = {}
    self.canal_district['fkc'] = [self.millerton, self.otherfriant, self.othercrossvalley, self.otherkaweah, self.fresno, self.fresnoid, self.tulare, self.exeter, self.lindsay, self.lindmore, self.porterville, self.lowertule, self.othertule, self.teapot, self.saucelito, self.terra, self.delano, self.kerntulare, self.sosanjoaquin, self.shaffer, self.northkern, self.northkernwb, self.xvc, self.kernriverchannel, self.aecanal]
    self.canal_district['mdc'] = [self.millerton, self.maderairr, self.chowchilla]
    self.canal_district['caa'] = [self.sanluis, self.southbay, self.otherswp, self.othercvp, self.otherexchange, self.westlands, self.centralcoast, self.tularelake, self.dudleyridge, self.losthills, self.berrenda, self.belridge, self.semitropic, self.buenavista, self.wkwb, self.xvc, self.kwbcanal, self.kernriverchannel, self.henrymiller, self.wheeler, self.aecanal, self.tejon, self.tehachapi, self.socal]
    self.canal_district['xvc'] = [self.calaqueduct, self.buenavista, self.kwb, self.irvineranch, self.pioneer, self.b2800, self.berrendawb, self.gooseslough, self.kernriverchannel, self.fkc, self.aecanal, self.beardsley]
    self.canal_district['kbc'] = [self.calaqueduct, self.kwb, self.kerncanal]
    self.canal_district['aec'] = [self.fkc, self.xvc, self.kernriverchannel, self.kerndelta, self.arvin, self.calaqueduct]
    self.canal_district['knr'] = [self.isabella, self.calloway, self.kerndelta, self.lerdo, self.xvc, self.fkc, self.aecanal, self.kerncanal, self.gooseslough, self.bakersfield, self.berrendawb, self.b2800, self.pioneer, self.kwb, self.buenavista, self.calaqueduct]
    self.canal_district['knc'] = [self.kernriverchannel, self.kerndelta, self.pioneer, self.buenavista, self.kwbcanal]
    self.canal_district['gsl'] = [self.kernriverchannel, self.xvc, self.rosedale21]
    self.canal_district['cwy'] = [self.kernriverchannel, self.beardsley, self.cawelo, self.northkern, self.poso, self.northkernwb]
    self.canal_district['lrd'] = [self.kernriverchannel, self.cawelo, self.northkern, self.poso, self.northkernwb]
    self.canal_district['bly'] = [self.xvc, self.calloway]
    self.canal_district['kwr'] = [self.kaweah, self.otherkaweah, self.tularelake]
    self.canal_district['tlr'] = [self.success, self.othertule, self.lowertule, self.porterville]
	
    ###After the canal structure is defined, each of the nodes on the list
    ###has a demand initialized.  There are many different types of demands
    ###depending on the surface water availabilities
    for y in self.canal_list:
      y.num_sites = len(self.canal_district[y.name])
      y.turnout_use = np.zeros(y.num_sites)##how much water diverted at a node
      y.flow = np.zeros(y.num_sites+1)##how much water passing through a node (inc. diversions)
      y.demand = {}
      y.turnout_frac = {}
      y.recovery_flow_frac = {}
      y.daily_flow = {}
      y.daily_turnout = {}
      for canal_member in self.canal_district[y.name]:
        y.daily_flow[canal_member.key] = np.zeros(self.T)
        y.daily_turnout[canal_member.key] = np.zeros(self.T)

      for z in ['contractor', 'turnout', 'excess', 'priority', 'secondary']:
        y.demand[z] = np.zeros(y.num_sites)
        y.turnout_frac[z] = np.zeros(y.num_sites)
        y.recovery_flow_frac[z] = np.ones(y.num_sites)
      for z in [self.calaqueduct, self.fkc, self.madera, self.kernriverchannel, self.tuleriverchannel, self.kaweahriverchannel]:
        y.demand[z.name] = np.zeros(y.num_sites)##for irrigation deliveries
        y.turnout_frac[z] = np.zeros(y.num_sites)
        y.recovery_flow_frac[z] = np.ones(y.num_sites)

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

    ##Linkages between reservoirs, canals, and surface water contracts
    ##Reservoir-Contract Relationships (reservoirs are dictionary key, contracts are list objects)
    self.reservoir_contract = {}
    self.reservoir_contract['SLF'] = [self.crossvalley, self.cvpdelta, self.cvpexchange]
    self.reservoir_contract['SLS'] = [self.swpdelta]
    self.reservoir_contract['MIL'] = [self.friant2, self.friant1]
    self.reservoir_contract['ISB'] = [self.kernriver]
    self.reservoir_contract['SUC'] = [self.tuleriver]
    self.reservoir_contract['KWH'] = [self.kaweahriver]
	
	##Use reservoir/contract dictionary to develop
	##a list linking individual districts to reservoirs,
	##based on their individual contracts
    for x in self.district_list:
      x.reservoir_contract = {}
      for res in self.reservoir_list:
        use_reservoir = 0
        for y in self.reservoir_contract[res.key]:
          for yy in x.contract_list:
            if y.name == yy:
              use_reservoir = 1
              break
        if use_reservoir == 1:
          x.reservoir_contract[res.key] = 1
        else:
          x.reservoir_contract[res.key] = 0

	
    ##Contract-Reservoir Relationships (contracts are dictionary key, reservoirs are list objects)
    self.contract_reservoir = {}
    self.contract_reservoir['FR1'] = self.millerton
    self.contract_reservoir['FR2'] = self.millerton
    self.contract_reservoir['KRR'] = self.isabella
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

	
    ##Reservoir-Canal Relationships (reservoirs are dictionary key, canals are list objects)
    self.reservoir_canal = {}
    self.reservoir_canal['SLS'] = [self.calaqueduct]
    self.reservoir_canal['SLF'] = [self.calaqueduct]
    self.reservoir_canal['SNL'] = [self.calaqueduct]
    self.reservoir_canal['MIL'] = [self.fkc, self.madera]
    self.reservoir_canal['ISB'] = [self.kernriverchannel]
    self.reservoir_canal['SUC'] = [self.tuleriverchannel]
    self.reservoir_canal['KWH'] = [self.kaweahriverchannel]
	
    self.pumping_turnback = {}
    for z in ['SLS', 'SLF', 'MIL', 'ISB', 'SUC', 'KWH']:
      self.pumping_turnback[z] = 0.0
####################################################################################################################
#####################################################################################################################
	  
	  
#####################################################################################################################
#############################     Pre processing functions    #######################################################
#####################################################################################################################

  def find_running_WYI(self):
    ###Pre-processing function
	##Finds the 8 River, Sacramento, and San Joaquin indicies based on flow projections
    lastYearSRI = 10.26 # WY 1996
    lastYearSJI = 4.12 # WY 1996
    current_year = 0
    startMonth = int(self.index.month[0])
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
      d = self.current_day_year[t]
      y = self.current_year[t]
      m = self.current_month[t]
      da = self.current_day_month[t]
      dowy = water_day(d,calendar.isleap(y))
      index_exceedence_sac = 9
      index_exceedence_sj = 5
	  ##8 River Index
      for x in reservoir_list:
        self.delta.eri[m-startMonth + (y - startYear)*12] + x.fnf[t]*1000
	  ####################Sacramento Index#############################################################################################
	  ##Individual Rainflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
      if m >=10:
        self.delta.forecastSJI[t] = lastYearSJI
        self.delta.forecastSRI[t] = lastYearSRI
      else:
        res_rain_forecast = 0.0
        for x in sac_list:
          res_rain_forecast += x.rainflood_fnf[t] + x.rainfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL RAIN
        if m >= 4 and m < 10:
          sac_rain = rainflood_sac_obs
        else:
          sac_rain = max(rainflood_sac_obs, res_rain_forecast)
	    ##Individual Snowflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_snow_forecast = 0.0
        for x in sac_list:
          res_snow_forecast += x.snowflood_fnf[t] + x.snowfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL SNOW
        if m >= 8 and m < 10:
          sac_snow = snowflood_sac_obs
        else:
          sac_snow = max(snowflood_sac_obs, res_snow_forecast)
	  #######################################################################################################################################
	  #####################San Joaquin Index################################################################################################
        ##Individual Rainflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_rain_forecast = 0.0
        for x in sj_list:
          res_rain_forecast += x.rainflood_fnf[t] + x.rainfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SJ TOTAL RAIN
        if m >= 4 and m < 10:
          sj_rain = rainflood_sj_obs
        else:
          sj_rain = max(rainflood_sj_obs, res_rain_forecast)
	    ##Individual Snowflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_snow_forecast = 0.0
        for x in sj_list:
          res_snow_forecast += x.snowflood_fnf[t] + x.snowfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
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
    df_wyi = pd.DataFrame()
    df_wyi['SRI'] = pd.Series(self.delta.forecastSRI, index = self.index)
    df_wyi['SJI'] = pd.Series(self.delta.forecastSJI, index = self.index)
    df_wyi.to_csv('cord/data/water_year_index_simulation.csv')
		
  def predict_delta_gains(self, datafile):
    ##this function uses a regression to find expected 'unstored' flows coming to the
    ##delta, to better project flow into San Luis
    df_short = pd.read_csv(datafile, index_col=0, parse_dates=True)
    index_short = df_short.index
    T_short = len(df_short)
    gains_sac_short = df_short.SAC_gains * cfs_tafd
    gains_sj_short = df_short.SJ_gains * cfs_tafd
    eastside_streams_short = df_short.EAST_gains * cfs_tafd
    depletions_short = df_short.delta_depletions * cfs_tafd
	
    sac_list = [self.shasta, self.folsom, self.oroville, self.yuba]
    for reservoir in sac_list:
      reservoir.fnf_short = df_short['%s_fnf'% reservoir.key].values / 1000000.0
      reservoir.downstream_short = df_short['%s_gains'% reservoir.key].values * cfs_tafd

	##########################################################################################
    #Initialize gains matricies
	##Unstored flow will be regressed against total FNF expected in that year
    numYears_short = index_short.year[T_short-1]-index_short.year[0]
    self.running_fnf = np.zeros((365,numYears_short))
    ##Total gains in each month
    monthly_gains = np.zeros((12,numYears_short))
    startYear = int(index_short.year[0])
    ##########################################################################################
    ##########################################################################################
    #Read flow from historical record
	##########################################################################################
    prev_gains = 0.0
    prev_fnf = 0.0
    for t in range(0,T_short):
      ##Get date information
      d = int(index_short.dayofyear[t])
      y = int(index_short.year[t])
      dowy = water_day(d,calendar.isleap(y))
      m = int(index_short.month[t])
      da = int(index_short.day[t])
      if m >= 10:
        wateryear = y - startYear
      else:
        wateryear = y - startYear - 1
		
      #Calculate the total daily unstored gains to the delta
      this_day_fnf = 0.0
      fnf_off = 0.0
      this_day_gains = 0.0
      for x in sac_list:
        this_day_fnf += x.fnf_short[t]
        min_release = x.env_min_flow[self.delta.forecastSCWYT][m-1]*cfs_tafd
        gauge_min = x.temp_releases[self.delta.forecastSCWYT][m-1]*cfs_tafd
        this_day_gains += max(max(x.downstream_short[t] + min_release, 0.0), gauge_min)
        if t >= 30:
          fnf_off += x.fnf_short[t-30]

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
    dowy_eom = [123, 150, 181, 211, 242, 272, 303, 333, 364, 30, 60, 91] 
    self.delta_gains_regression = {}
    self.delta_gains_regression['slope'] = np.zeros((365,12))
    self.delta_gains_regression['intercept'] = np.zeros((365,12))
    for x in range(0,365): 
      #fig = plt.figure()
      #coef_save = np.zeros((12,2))
      #regress for gains in oct-mar period and april-jul period
      for mm in range(0,12):
        if x <= dowy_eom[mm]:
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
        #print(x, end = " ")
        #print(mm, end = " ")
        #print(r, end = " ")
        #print(coef[0], end = " ")
        #print(coef[1])
      #for mm in range(0,12):
        #ax1 = fig.add_subplot(4,3,mm+1)
        #if x <= dowy_eom[mm]:
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

	#The value self.reservoir.flood_flow_min is used to determine when uncontrolled releases
	#are initiated at the reservoir
    for a in [self.isabella, self.millerton, self.kaweah, self.success]:
    #for each reservoir, clear the demands of each object
      for x in self.district_list:
        x.current_requested = 0.0
      for x in self.waterbank_list:
        x.current_requested = 0.0
      for z in self.reservoir_canal[a.key]:
        #find all demands that can be reached from the reservoir
        a.flood_flow_min = self.find_flood_trigger(z, a.key, z.name, 'normal','recharge')
    
	#also calculate for san luis - but split federal and state portions (uncontrolled releases are made seperately)
    #only want the demands that are associated w/ nodes that have a contract
    self.canal_contract['caa'] = [self.swpdelta]
    for x in self.district_list:
      x.current_requested = 0.0
    for x in self.waterbank_list:
      x.current_requested = 0.0
    self.sanluisstate.flood_flow_min = self.find_flood_trigger(self.calaqueduct, self.sanluis.key, self.calaqueduct.name, 'normal', 'recharge')
    #same thing for the federal portion
    self.canal_contract['caa'] = [self.cvpdelta, self.cvpexchange, self.crossvalley]
    for x in self.district_list:
      x.current_requested = 0.0
    for x in self.waterbank_list:
      x.current_requested = 0.0
    self.sanluisfederal.flood_flow_min = self.find_flood_trigger(self.calaqueduct, self.sanluis.key, self.calaqueduct.name, 'normal', 'recharge')
    #return the contract association on the california aqeuduct to all CVP & SWP delta contracts
    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]

  def find_flood_trigger(self, canal, prev_canal, contract_canal, flow_dir,flow_type):
    #########################################################################################
    #this function loops through the canal nodes looking for recharge storage attached
	#to particular contracts.
    #########################################################################################

	#finds where on the canal to begin (if coming from another canal), and 
	#where to end (either the end or beginning of canal, depending on flow direction)
    for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
      if new_canal.key == prev_canal:#find canal intersections
        break
    if flow_dir == "normal":
      canal_size = len(self.canal_district[canal.name])
      canal_range = range((starting_point+1),canal_size)
    elif flow_dir == "reverse":
      canal_range = range((starting_point-1),0,-1)
    else:
      return (0.0)

    tot_contractor_demand = 0.0#initialize total demand on the canal
    for canal_loc in canal_range:#loop through the flow range on the canal (determined above)
      x = self.canal_district[canal.name][canal_loc]
      if isinstance(x, District):
        new_loc_demand = 0.0
        contractor_toggle = 0
		#find if the node has a particular contract
        for y in self.canal_contract[contract_canal]:
          for yx in x.contract_list:
            if y.name == yx:
              contractor_toggle = 1
        #calculate teh maximium recharge storage
        if contractor_toggle == 1:
          new_loc_demand = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd, max(x.in_district_storage - x.current_requested, 0.0))
          tot_contractor_demand += new_loc_demand
          x.current_requested += new_loc_demand
		
      elif isinstance(x, Waterbank):
        new_loc_demand = 0.0
        #at a waterbank, find if the bank member has a contract
        for xx in x.participant_list:
          contractor_toggle = 0
          for wb_member in self.get_iterable(self.district_keys[xx]):
            for y in self.canal_contract[contract_canal]:
              for yx in wb_member.contract_list:
                if y.name == yx:
                  contractor_toggle = 1
          if contractor_toggle == 1:
            new_loc_demand += max(x.tot_storage*x.ownership[xx],0.0)#only account for member-owned storage
        new_loc_demand -= x.current_requested
        #make sure storage doesn't exceed the turnout capacity
        if new_loc_demand > canal.turnout[flow_dir][canal_loc]*cfs_tafd:
          new_loc_demand = canal.turnout[flow_dir][canal_loc]*cfs_tafd	  
        x.current_requested += new_loc_demand
        tot_contractor_demand += new_loc_demand

      #if a node is a canal node, jump to that canal (function calls itself, but for another canal) 
      elif isinstance(x, Canal):
        new_loc_demand = 0.0	  
        if canal.turnout[flow_dir][canal_loc] > 0.0:
          new_flow_dir = canal.flow_directions[flow_type][x.name]
          new_loc_demand = self.find_flood_trigger(x, canal.key, contract_canal, new_flow_dir,flow_type)
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

    tot_state = self.sanluisstate.S[0]
    tot_federal = self.sanluisfederal.S[0]
    total_alloc_state = self.swpdelta.total
    total_alloc_federal = self.cvpdelta.total + self.cvpexchange.total
    for y in self.contract_list:
      reservoir = self.contract_reservoir[y.key]
      #then find all the contracts associated with that reservoir
      this_reservoir_all_contract = self.reservoir_contract[reservoir.key]
      #need to find the total deliveries already made from the reservoir,
	  #total carryover storage at the reservoir, and the total priority/secondary allocations
	  #at that reservoir
      priority_allocation = 0.0
      secondary_allocation = 0.0
      for yy in self.get_iterable(this_reservoir_all_contract):
        if yy.allocation_priority == 1:
          priority_allocation += yy.total
        else:
          secondary_allocation += yy.total

      if y.allocation_priority == 1:
        if priority_allocation > 0.0:
          y.tot_new_alloc = (reservoir.S[0] - reservoir.dead_pool)*max(y.total/priority_allocation, 1.0)
        else:
          y.tot_new_alloc = 0.0
      else:
        if secondary_allocation > 0.0:
          y.tot_new_alloc = max(reservoir.S[0] - reservoir.dead_pool - priority_allocation, 0.0)*y.total/secondary_allocation
        else:
          y.tot_new_alloc = 0.0

      for x in self.district_list:
        x.carryover[y.name] = 0.0
	
  def init_tot_recovery(self):
    #########################################################################################
    ###this function finds the total GW recovery
    ###capacity available to all district objects
    #########################################################################################

    for x in self.district_list:
      x.max_recovery = 0.0
    #each waterbank has a list of district participants -
	#they get credit for their ownership share of the total recovery capacity
    for w in self.waterbank_list:
      for member in w.participant_list:
        num_districts = len(self.get_iterable(self.district_keys[member]))
        for irr_district in self.get_iterable(self.district_keys[member]):
          irr_district.max_recovery += w.ownership[member]*w.recovery/num_districts
    #same for 'in leiu' banks (districts)
    for w in self.leiu_list:
      for member in w.participant_list:
        num_districts = len(self.get_iterable(self.district_keys[member]))
        for irr_district in self.get_iterable(self.district_keys[member]):
          irr_district.max_recovery += w.leiu_ownership[member]*w.leiu_recovery/num_districts
      
  def project_urban(self, datafile, datafile_cvp, model_mode):
    #########################################################################################
    ###initializes variables needed for district objects that are pumping plants on branches
	###of the california aqueduct (southern california, central coast, and the south bay)
    #########################################################################################

    ##This function finds linear regression coefficients between urban CA AQ branch pumpning and delta pumping
	##to predict water use in southbay, centralcoast, and socal district objects
	##NOTE!!! More detailed MWD/Southern Cal demand data would improve the model
    df_urban = pd.read_csv(datafile, index_col=0, parse_dates=True)
    df_urban_monthly_cvp = pd.read_csv(datafile_cvp, index_col=0, parse_dates=True)
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    index_urban = df_urban.index
    urban_historical_T = len(df_urban)
    numYears_urban = index_urban.year[urban_historical_T - 1] - index_urban.year[0]
    urban_list = [self.socal, self.centralcoast, self.southbay]
    self.observed_hro = df_urban['HRO_pump'].values*cfs_tafd
    self.observed_trp = df_urban['TRP_pump'].values*cfs_tafd
    regression_annual_hro = np.zeros(numYears_urban)
    regression_annual_trp = np.zeros(numYears_urban)

    for x in urban_list:
      x.hist_pumping = df_urban[x.key+ '_pump'].values
      x.regression_annual = np.zeros(numYears_urban)
    self.southbay.regression_pacheco = np.zeros(numYears_urban)
    self.southbay.hist_pumping_pacheco = np.zeros(urban_historical_T)
    startYear = index_urban.year[0]
    for t in range(1,(urban_historical_T)):
      m = int(index_urban.month[t-1])
      y = int(index_urban.year[t-1])
      if m >= 10:
        wateryear = y - startYear
      else:
        wateryear = y - startYear - 1
	  
	  ##Find annual pumping at each branch (and @ delta)
      regression_annual_hro[wateryear] += self.observed_hro[t-1]
      regression_annual_trp[wateryear] += self.observed_trp[t-1]
      for x in urban_list:
        x.regression_annual[wateryear] += x.hist_pumping[t-1]/1000.0
		
      self.southbay.regression_pacheco[wateryear] += df_urban_monthly_cvp['PCH_pump'][m-1 + wateryear*12]/days_in_month[m-1]
      self.southbay.hist_pumping_pacheco[t-1] = df_urban_monthly_cvp['PCH_pump'][m-1 + wateryear*12]/days_in_month[m-1]

		
    for x in urban_list:
      x.urb_coef = {}
    ##regression between pumping at delta and pumping on branches
	##note - only use water years 2000 - 2016 (1997-1999 saw low pumping that is unlikely to be recreated in the future)
      x.urb_coef['swp'] = np.polyfit(regression_annual_hro[3:(numYears_urban-1)],x.regression_annual[3:(numYears_urban-1)],1)
      x.regression = np.zeros(len(x.regression_annual))
		
      for reg_year in range(0,len(x.regression)):
        x.regression[reg_year] = x.urb_coef['swp'][0]*regression_annual_hro[reg_year] + x.urb_coef['swp'][1]

    self.southbay.urb_coef['cvp'] = np.polyfit(regression_annual_trp, self.southbay.regression_pacheco,1)
    self.southbay.regression_cvp = np.zeros(len(self.southbay.regression_pacheco))
    for reg_year in range(0,len(self.southbay.regression_cvp)):
      self.southbay.regression_cvp[reg_year] = self.southbay.urb_coef['cvp'][0]*regression_annual_trp[reg_year] + self.southbay.urb_coef['cvp'][1]
    self.socal.urb_coef['cvp'] = np.zeros(2)
    self.centralcoast.urb_coef['cvp'] = np.zeros(2)

	  
    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1, axisbg = "1.0")
    #ax2 = fig.add_subplot(2,2,2, axisbg = "1.0")
    #ax3 = fig.add_subplot(2,2,3, axisbg = "1.0")
    ax1.scatter(regression_annual_trp,self.southbay.regression_pacheco, alpha = 0.8, c = 'red', edgecolors = 'black', s = 30)
    ax1.scatter(regression_annual_trp,self.southbay.regression_cvp, alpha = 0.8, c = 'blue', edgecolors = 'black', s = 30)
    #ax2.scatter(regression_annual_hro,self.centralcoast.regression_annual, alpha = 0.8, c = 'red', edgecolors = 'black', s = 30)
    #ax2.scatter(regression_annual_hro,self.centralcoast.regression, alpha = 0.8, c = 'blue', edgecolors = 'black', s = 30)
    #ax3.scatter(regression_annual_hro,self.southbay.regression_annual, alpha = 0.8, c = 'red', edgecolors = 'black', s = 30)
    #ax3.scatter(regression_annual_hro,self.southbay.regression, alpha = 0.8, c = 'blue', edgecolors = 'black', s = 30)
    #plt.show()
	
    if model_mode == 'validation':
      for x in urban_list:
        x.pumping = df_urban[x.key + '_pump'].values
        x.annual_pumping = x.regression_annual
      for xx in range(0, len(self.southbay.pumping)):
        self.southbay.pumping[xx] += self.southbay.hist_pumping_pacheco[xx]*1000.0
      for xx in range(0, len(self.southbay.annual_pumping)):
        self.southbay.annual_pumping[xx] += self.southbay.regression_pacheco[xx]

    else:
      for x in urban_list:
        x.hist_demand_dict = {}
        x.hist_demand_dict['swp'] = {}
        x.hist_demand_dict['cvp'] = {}
		
	  ##Finds regressions to predict urban CA AQ branch pumping based on SWP allocations
        x.annual_pumping = np.zeros((self.ending_year-self.starting_year))
        x.pumping = np.zeros(self.T)
        x.hist_demand_dict['swp']['annual_sorted'] = np.sort(regression_annual_hro)
        x.hist_demand_dict['swp']['sorted_index'] = np.argsort(regression_annual_hro)
        x.hist_demand_dict['swp']['daily_fractions'] = np.zeros((len(x.regression_annual),366))
        x.hist_demand_dict['cvp']['annual_sorted'] = np.sort(regression_annual_trp)
        x.hist_demand_dict['cvp']['sorted_index'] = np.argsort(regression_annual_trp)
        x.hist_demand_dict['cvp']['daily_fractions'] = np.zeros((len(self.southbay.regression_pacheco),366))        

      for t in range(1,(urban_historical_T)):
        m = int(index_urban.month[t-1])
        y = int(index_urban.year[t-1])
        d = int(index_urban.dayofyear[t-1])
        dowy = water_day(d, calendar.isleap(y))
        if m >= 10:
          wateryear = y - startYear
        else:
          wateryear = y - startYear - 1  
        for x in urban_list:
          x.hist_demand_dict['swp']['daily_fractions'][wateryear][dowy] = x.hist_pumping[t-1]/(x.regression_annual[wateryear]*1000.0)
          if x.key == "SOB":
            x.hist_demand_dict['cvp']['daily_fractions'][wateryear][dowy] = x.hist_pumping_pacheco[t-1]/(x.regression_pacheco[wateryear])
    for x in urban_list:
      x.ytd_pumping = np.zeros((self.ending_year-self.starting_year))
	  
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


  def simulate_north(self,t,swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump, model_mode):   
	###Daily Operations###
	##Step forward environmental parameters (snow & flow)
    ##Set Delta operating rules
    ##Water Balance on each reservoir
    ##Decisions - release water for delta export, flood control
    d = self.current_day_year[t]
    y = self.current_year[t]
    m = self.current_month[t]
    dowy = water_day(d,calendar.isleap(y))
	  
    ##WATER YEAR TYPE CLASSIFICATION (for operating rules)
    ##WYT uses flow forecasts - gets set every day, may want to decrease frequency (i.e. every month, season)
    NMI = self.calc_wytypes(t,dowy)#NMI (new melones index) - used as input for vernalis control rules
	  
	##REAL-WORLD RULE ADJUSTMENTS
	##Updates to reflect SJRR & Yuba Accords occuring during historical time period (1996-2016)
    if model_mode == 'validation':
      self.update_regulations_north(t,dowy)
	  
	####NON-PROJECT USES
    ##Find out if reservoir releases need to be made for in-stream uses
    self.reservoir_list = [self.shasta, self.oroville, self.yuba, self.folsom, self.newmelones, self.donpedro, self.exchequer]
    for x in self.reservoir_list:	
      x.rights_call(x.downstream[t])
    ##any additional losses before the delta inflow (.downstream member only accounts to downstream trib gauge)
	##must be made up by releases from Shasta and New Melones, respectively
    #self.newmelones.rights_call(self.delta.gains_sj[t-1],1)

    ##FIND MINIMUM ENVIRONMENTAL RELEASES
    #San Joaquin Tributaries
    for x in [self.newmelones, self.donpedro, self.exchequer]:
      x.release_environmental(t,self.delta.forecastSJWYT)
	#Sacramento Tributaries
    self.oroville.set_oct_nov_rule(t, m)
    for x in [self.shasta, self.oroville, self.yuba, self.folsom]:
      x.release_environmental(t,self.delta.forecastSCWYT)
    ##MINIMUM FLOW AT VERNALIS GAUGE(SAN JOAQUIN DELTA INFLOW)
    #from self.reservoir.release_environmental() function:
	#self.reservoir.gains_to_delta
    #self.reservoir.envmin
    self.delta.vernalis_gains = self.newmelones.gains_to_delta + self.donpedro.gains_to_delta + self.exchequer.gains_to_delta + self.delta.gains_sj[t]
    self.delta.vernalis_gains += self.newmelones.envmin + self.donpedro.envmin + self.exchequer.envmin
    #find additional releases for vernalis control using self.delta.vernalis_gains
    self.exchequer.din, self.donpedro.din, self.newmelones.din  = self.delta.calc_vernalis_rule(t, NMI)
    self.delta.vernalis_gains += self.exchequer.din + self.donpedro.din + self.newmelones.din
	
	##MINIMUM FLOW AT RIO VIST GAUGE (SACRAMENTO DELTA INFLOW)
    for x in [self.shasta, self.oroville, self.yuba, self.folsom]:
      x.find_available_storage(t)  
    #additional releases to meet rio vista minimums shared by Sacramento Reservoirs
    cvp_stored_release = self.shasta.envmin + self.folsom.envmin
    swp_stored_release = self.oroville.envmin + self.yuba.envmin
    #unstored flow at rio vista comes from tributary gains, environmental releases and sacramento river gains
    self.delta.rio_gains = self.delta.gains_sac[t]
    for x in [self.shasta, self.oroville, self.yuba, self.folsom]:
      self.delta.rio_gains += x.gains_to_delta + x.envmin
    #share rio vista requirements among Sacramento Reservoirs based on self.resevoir.availale_storage
    self.shasta.din, self.oroville.din = self.delta.calc_rio_vista_rule(t, cvp_stored_release, swp_stored_release)

    ##MINIMUM DELTA OUTFLOW REQUIREMENTS
    #flows to delta come from vernalis, rio vista, and the 'eastside streams' (delta gains)
    self.delta.total_inflow = self.delta.eastside_streams[t] + self.delta.rio_gains + self.delta.vernalis_gains
    cvp_stored_release += self.shasta.din
    swp_stored_release += self.oroville.din
	##additional releases for delta outflow split between cvp/swp reservoirs
    self.shasta.dout, self.oroville.dout = self.delta.calc_outflow_release(t, cvp_stored_release, swp_stored_release)
  
	#TOTAL AVAILABLE PROJECT STORAGE
	#based on snowpack based forecast (pre-processed) + current storage
    cvp_available_storage = max(self.folsom.available_storage[t],0.0) + max(self.shasta.available_storage[t],0.0)
    swp_available_storage = max(self.oroville.available_storage[t],0.0) + max(self.yuba.available_storage[t],0.0)
    cvp_flood_storage = 0.0
    swp_flood_storage = 0.0
    #some 'saved' storage in oroville can be used to make non-taxed releases
    swp_extra = self.oroville.use_saved_storage(t, m, self.delta.forecastSCWYT, dowy)
    #project if flood pool will be exceeded in the future & find min release rate to avoid reaching the flood pool
	#monthly flow projections from self.reservoir.create_flow_shapes (i.e. flood available water)
    for x in [self.shasta, self.folsom, self.oroville, self.yuba]:
      x.find_flow_pumping(t, m, dowy, self.delta.forecastSCWYT, 'env')
	  	  	
	###DETERMINE RELEASES REQUIRED FOR DESIRED PUMPING
    ###Uses gains and environmental releases to determine additional releases required for
	###pumping (if desired), given inflow/export requirements, pump constraints, and CVP/SWP sharing of unstored flows
	#at-the-pump limits (from BiOps)
    cvp_max, swp_max = self.delta.find_max_pumping(d, dowy, t, self.delta.forecastSCWYT)
    #OMR rule limits
    cvp_max, swp_max = self.delta.meet_OMR_requirement(cvp_max, swp_max, t, model_mode)
	
    proj_surplus, max_pumping = self.proj_gains(t)
    flood_release = {}
    flood_volume = {}
    flood_release['swp'] = self.oroville.min_daily_uncontrolled
    flood_release['cvp'] = self.shasta.min_daily_uncontrolled
    flood_volume['swp'] = self.oroville.uncontrolled_available
    flood_volume['cvp'] = self.shasta.uncontrolled_available
    swp_over_dead_pool = self.oroville.find_emergency_supply(t, m, dowy)
    cvp_over_dead_pool = 0.0
	##Distribute 'available storage' seasonally to maximize pumping under E/I ratio requirements (i.e., pump when E/I ratio is highest)
    cvp_max_final, swp_max_final = self.delta.find_release(t, m, dowy, cvp_max, swp_max, cvp_available_storage, swp_available_storage, cvp_release, swp_release, proj_surplus, max_pumping)
    
    #if pumping is turned 'off' (b/c SL conditions), calculate how much forgone pumping to take away from SL carryover storage (southern model input)
    cvp_forgone = max(cvp_max - cvp_pump, 0.0)
    swp_forgone = max(swp_max - swp_pump, 0.0)
    #swp_forgone, swp_max_final = self.delta.hypothetical_pumping(swp_max, swp_max_final, swp_release2, 0.45, t)
    #find additional releases to pump at the desired levels
    cvp_max = min(cvp_max, cvp_pump)#don't release 'tax free' pumping in excess of storage capacity at SL
    swp_max = min(swp_max, swp_pump)#don't release 'tax free' pumping in excess of storage capacity at SL
    cvp_max_final = min(cvp_max_final, cvp_pump)
    swp_max_final = min(swp_max_final, swp_pump)
    #calculates releases to pump at desired levels (either cvp/swp_max or non-taxed levels, based on min outflow & i/e rules)
    self.delta.calc_flow_bounds(t, cvp_max_final, swp_max_final, cvp_max, swp_max, cvp_release2, swp_release2, cvp_available_storage, swp_available_storage, flood_release['cvp'], flood_release['swp'], swp_over_dead_pool, cvp_over_dead_pool, flood_volume['swp'], flood_volume['cvp'], model_mode)

    #distribute releases for export between Sacramento River Reservoirs
    self.shasta.sodd, self.folsom.sodd = self.delta.distribute_export_releases(t, cvp_max, self.delta.sodd_cvp[t], self.shasta.flood_storage[t], self.folsom.flood_storage[t], self.shasta.available_storage[t], self.folsom.available_storage[t])
    self.oroville.sodd, self.yuba.sodd = self.delta.distribute_export_releases(t, swp_max, self.delta.sodd_swp[t], self.oroville.flood_storage[t], self.yuba.flood_storage[t], self.oroville.available_storage[t], self.yuba.available_storage[t])
    if self.shasta.sodd > self.shasta.S[t] - self.shasta.dead_pool:
      self.shasta.sodd = 0.0
    if self.oroville.sodd > self.oroville.S[t] - self.oroville.dead_pool:	  
      self.oroville.sodd = 0.0
	  
    if self.shasta.sodd < self.shasta.min_daily_uncontrolled:
      release_switch = min(self.folsom.sodd, self.shasta.min_daily_uncontrolled - self.shasta.sodd)
      self.shasta.sodd += release_switch
      self.folsom.sodd -= release_switch
    if self.oroville.sodd < self.oroville.min_daily_uncontrolled:
      release_switch = min(self.yuba.sodd, self.oroville.min_daily_uncontrolled - self.oroville.sodd)
      self.oroville.sodd += release_switch
      self.yuba.sodd -= release_switch

	##SAN JOAQUIN RESERVOIR OPERATIONS
	##lower SJ basins - no 'release for exports' but used to meet delta targets @ vernalis
    ##Water Balance
    for x in [self.newmelones, self.donpedro, self.exchequer]:	
      x.step(t)

    #SACRAMENTO RESERVOIR OPERATIONS
	##Water balance at each Northern Reservoir
    self.shasta.rights_call(self.delta.ccc[t]*-1.0,1)
    self.oroville.rights_call(self.delta.barkerslough[t]*-1.0,1)
    for x in [self.shasta, self.oroville, self.yuba, self.folsom]:
      x.step(t)
	  
    ###DELTA OPERATIONS
	##Given delta inflows (from gains and reservoir releases), find pumping
    #cvp_stored_flow = self.shasta.R_to_delta[t] + self.folsom.R_to_delta[t]
    #swp_stored_flow = self.oroville.R_to_delta[t] + self.yuba.R_to_delta[t]
    cvp_stored_flow = self.shasta.sodd + self.folsom.sodd
    swp_stored_flow = self.oroville.sodd + self.yuba.sodd

    ##route all water through delta rules to determine pumping
    self.delta.step(t, cvp_stored_flow, swp_stored_flow, swp_pump, cvp_pump, swp_available_storage, cvp_available_storage, model_mode)
	
		    
    return self.delta.HRO_pump[t], self.delta.TRP_pump[t], self.delta.swp_allocation[t], self.delta.cvp_allocation[t], proj_surplus, max_pumping, swp_forgone, cvp_forgone, swp_flood_storage, cvp_flood_storage, swp_available_storage, cvp_available_storage, flood_release, flood_volume
			
  def simulate_south(self, t, hro_pump, trp_pump, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgone, cvp_forgone, swp_AF, cvp_AF, swp_AS, cvp_AS, wyt, max_tax_free, flood_release, flood_volume, model_mode):
    ####Maintain the same date/time accounting as the northern part of the model
    startYear = self.starting_year
    d = self.current_day_year[t]
    current_year = self.current_year[t]
    m = self.current_month[t]
    da = self.current_day_month[t]

    dowy = water_day(d,calendar.isleap(current_year))
    dowy_md = [122, 150, 181, 211, 242, 272, 303, 334, 365, 30, 60, 91]
    if m >= 10:
      wateryear = current_year - startYear
    else:
      wateryear = current_year - startYear - 1  
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
    if model_mode == 'validation':
      self.update_regulations_south(t,dowy,m,current_year)
    else:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)

	  
    ####Calculate water balance/flow requirements at each 
	####local reservoir, in the same fashion as they are calculated for the 
	####Northern Reservoir
    watershed_reservoir_list = [self.millerton, self.success, self.kaweah, self.isabella]
    for x in watershed_reservoir_list:
      x.rights_call(x.downstream[t])
      x.release_environmental(t,wyt)

	###Flow projections for the local reservoirs
	###Note: no flow projection for the San Luis Reservoir,
	###because it has no watershed affects.  Projections of pumping
	###are calculated in the northern function, and passed here as 
	###'projected allocations'
    for x in watershed_reservoir_list:
      x.find_available_storage(t)
	  
    ##Water Balance step at each reservoir
    for x in watershed_reservoir_list:
      x.step(t)
    
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
	
	##Find ID demands
	###Daily demands are calculated from monthly demands based on 
	###crop acreage.  Right now the acreage is dependent on water year type,
	###so demand for each water year type can be calculated before the timestep loop.
	###When crop allocation functions are added, this demand must be calculated at least once
	###per year (as acreages update).  Daily demands are just monthly demands divided by the number
	###of days in a month
    for x in self.district_list:
      x.calc_demand(wateryear, da, m, m1, wyt)
    ###For demands that occur on a branch of the California Aqueduct
	###(i.e. pumped into some kind of regional urban storage/distribution 
	###systems, daily demand are just the observed pumping (i.e. no model of 
	###the southern California/South Bay/Central Coast urban demand).  To run the
	###model in projection mode, we need statistical series of pumping at each of the Cal Aqueduct
	###branches.  Note:  for Bakersfield and Fresno in the local water systems, demands are deterministic
	###seasonal estimates.  Adding in pop. growth, etc. would be trivial, but is not included
    if model_mode == 'validation':
      for x in self.urban_list:
        x.get_urban_demand(t, m, da, wateryear)
    else:
      self.project_urban_pumping(d, da, dowy, wateryear, self.swp_allocation[t], self.cvp_allocation[t])
	  
    if m == 10 and da == 1:      
	  ###Pre flood demands - used to approximate the limit 
      ###for carryover storage (don't want to carryover more water than you can
      ###use from Oct-Jan).  Values for aqueduct branches are estimated to 
      ###avoid 'perfect foresight'	  
      for x in self.district_list:
        x.find_pre_flood_demand(wyt)
      self.socal.pre_flood_demand = 500.0
      self.centralcoast.pre_flood_demand = 25.0
      self.southbay.pre_flood_demand = 15.0
	  
      ###Take the monthly demands for each irrigation district and
      ###'assign' them to a reservoir - this is used to estimate 
      ###fillup times so that districts know when to request recharge water
      #generates res.monthlydemand from aggregated district.monthlydemand
    if da == 1:
      self.agg_contract_demands()
	  
    ##Once a month, find the recharge capacity for each irrigation district
    ###This capacity is projected forward for a year to project how capacity would decline
    ###under continuous use - recalculated every month to update for actual use
    #generates self.district.max_leiu_recharge & self.district.max_direct_recharge
    if da == 1:
      for x in self.district_list:
        x.reset_recharge_recovery()
      ##searches through all waterbanks to find recharge capacity,
	  ##applies that capacity to districts by ownership shares
      self.find_recharge_bank(m,wyt)
      ##searches through all leiu bankign districts to find recharge capacity,
	  ##applies that capacity to districts by ownership shares
      self.find_recharge_leiu(m,wyt)
      ##searches through all districts to find native recharge capacity
      self.find_recharge_indistrict(m,wyt)
	  
    ###June 1st, determine who is buying/selling into 'turnback pools' for the SWP.
    ###Note: look into other contract types to determine if this happens in CVP, Friant, local source contracts too
    if m == 6 and da == 1:
      for y in self.contract_list:
        seller_total = 0.0
        buyer_total = 0.0
        for x in self.district_list:
          seller_turnback, buyer_turnback = x.set_turnback_pool(y.name)
          seller_total += seller_turnback
          buyer_total += buyer_turnback
        for x in self.district_list:
          x.make_turnback_purchases(seller_total, buyer_total, y.name)

	#Find the number of days before each reservoir is expected to fill-up	  
    ##Get Article 21 water from San Luis
	#for san luis - need to know if we can use the xvc from california aquduct - check for turnout to xvc from kern river and fkc
    ###find flood releases for the SWP at san luis (self.sanluisstate.min_daily_uncontrolled) - also find release toggles (for northern reservoir pumping coordination w/ san luis) and numdays_fillup for SWP district recharge decisions
    expected_pumping = self.estimate_project_pumping(t, proj_surplus, max_pumping, swp_AS, cvp_AS, self.max_tax_free, flood_release, wyt)
    swp_release, swp_release2, self.sanluisstate.min_daily_uncontrolled, self.sanluisstate.numdays_fillup['demand'] = self.find_pumping_release(self.sanluisstate.S[t], 6680.0*cfs_tafd, self.sanluisstate.monthly_demand, self.sanluisstate.monthly_demand_must_fill, self.swpdelta.allocation[t-1]/self.swpdelta.total, expected_pumping['swp'], swp_AF, max(swp_AS, flood_volume['swp']), self.swpdelta.projected_carryover, self.swpdelta.running_carryover, self.max_tax_free, wyt, t, 'swp')
	  
    ###find flood releases for the CVP at san luis (self.sanluisfederal.min_daily_uncontrolled) - also find release toggles (for northern reservoir pumping coordination w/ san luis) and numdays_fillup for SWP district recharge decisions
    cvp_release, cvp_release2, self.sanluisfederal.min_daily_uncontrolled, self.sanluisfederal.numdays_fillup['demand'] = self.find_pumping_release(self.sanluisfederal.S[t], 4430.0*cfs_tafd, self.sanluisfederal.monthly_demand, self.sanluisfederal.monthly_demand_must_fill, (self.cvpdelta.allocation[t-1] + self.cvpexchange.allocation[t-1])/(self.cvpexchange.total+self.cvpdelta.total), expected_pumping['cvp'], cvp_AF, max(cvp_AS, flood_volume['cvp']), self.cvpdelta.projected_carryover, self.cvpdelta.running_carryover + self.cvpexchange.running_carryover + self.crossvalley.running_carryover, self.max_tax_free, wyt, t, 'cvp')
	  
    ####This function finds the expected # of days that a reservoir will fill
	####districts use this numdays_fillup attribute to determine when to recharge
	####carryover water
    for reservoir in [self.millerton, self.isabella, self.kaweah, self.success]:
      reservoir.find_flow_pumping(t, m, dowy, wyt, 'demand')
    
    ##Flood Deliveries - 4 flood sources - Millerton, Isabella, Success, and Kaweah
    ##What is the priority for reservoirs getting to use the canals to route flood releases?
	##Note: most of the contracts have provisions that flood flows 'cannot displace' scheduled 
    ##deliveries (i.e. you can't use flood releases to fill demand that would be met by your contract
	##schedule), so might want to put this AFTER regular delivery routing
    flood_order_list = [self.success, self.kaweah, self.isabella, self.millerton]
    #toggle to enable flood releases to go to districts/banks that don't have a contract w/the reservoir
    #only san luis restricts flood releases to contractors only (b/c otherwise they just dont pump)
    overflow_deliveries = 1
    flow_type = "recharge"
    self.set_canal_direction(flow_type)	
    for a in flood_order_list:
      #if flow is already on a bi-directional canal, it becomes closed to canals going the other direction
	  #checks the calaqueduct turnout to xvc is used, if not, xvc is open to fkc and kern river
      self.set_canal_direction(flow_type)
      #release flood flows to canals
      self.flood_operations(t, m, dowy, wateryear, a, flow_type, overflow_deliveries, wyt)
	  
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

	  
	#Update Contract Allocations
    for y in self.contract_list:
      #for a specific contract, look up the reservoir it is stored in
      reservoir = self.contract_reservoir[y.key]
      #then find all the contracts associated with that reservoir
      this_reservoir_all_contract = self.reservoir_contract[reservoir.key]
      #need to find the total deliveries already made from the reservoir,
	  #total carryover storage at the reservoir, and the total priority/secondary allocations
	  #at that reservoir
      total_res_deliveries = 0.0
      total_res_carryover = 0.0
      priority_contract = 0.0
      secondary_contract = 0.0
      extra_allocation = 0.0
      for yy in self.get_iterable(this_reservoir_all_contract):
        total_res_deliveries += yy.annual_deliveries[wateryear]
        total_res_carryover += yy.tot_carryover
        extra_allocation += yy.tot_new_alloc
        if yy.allocation_priority == 1:
          priority_contract += yy.total*yy.reduction[wyt]
        else:
          secondary_contract += yy.total*yy.reduction[wyt]
      #san luis doesn't have available_storage forecasts, so input from northern model is used
	  #for state & federal portions
      if reservoir.key == "SLS":
        total_allocation = self.swp_allocation[t] - self.pumping_turnback['SLS'] + extra_allocation
      elif reservoir.key == "SLF":
        total_allocation = self.cvp_allocation[t] - self.pumping_turnback['SLF'] + extra_allocation
      else:
        #otherwise, total allocation at the reservoir is equal to available storage + deliveries - the total carryover storage
        total_allocation = reservoir.available_storage[t] + total_res_deliveries - total_res_carryover
		
      y.calc_allocation(t, dowy, total_allocation, priority_contract, secondary_contract, wyt)
    ##Find contract 'storage pools' - how much water is available right now	
	##san luis federal storage is divided between 3 water contracts - cvpdelta, exchange, and crossvalley
	##millerton storage is divided between 2 water contracts - friant1 and friant2
    for y in self.contract_list:
      #for a specific contract, look up the reservoir it is stored in
      reservoir = self.contract_reservoir[y.key]
      #then find all the contracts associated with that reservoir
      this_reservoir_all_contract = self.reservoir_contract[reservoir.key]
      tot_res_deliveries = 0.0
      priority_storage = 0.0
      tot_res_carryover = 0.0
      for yy in self.get_iterable(this_reservoir_all_contract):
        #if some contracts at a reservoir have 'priority' over storage space
		#(i.e., cvpdelta and exchange contracts have priority over the federal
		#san luis storage), calculate the total allocation volume that has priority
		#in a reservoir
        tot_res_deliveries += yy.annual_deliveries[wateryear]
        tot_res_carryover += yy.tot_carryover
        if yy.storage_priority == 1:
          priority_storage += yy.allocation[t]
      ##contract storage pools are the existing storage plus all the deliveries
      ##that have been made so far in that water year - so 'storage pool' is all
      ##the contract water that has already come into the reservoir, even water
      ##that has already been delivered	  
      total_water = reservoir.S[t] - reservoir.dead_pool + tot_res_deliveries - tot_res_carryover
      #find the storage pool for each contract
      y.find_storage_pool(t, wateryear, total_water, reservoir.S[t], priority_storage)

	##Update District Contracts
    #self.assign_uncontrolled(t, wateryear)
    for y in self.contract_list:
      y.projected_carryover = 0.0
      y.running_carryover = 0.0
    #for each contract in each district, what is the district's share of (i) currently available (surface water) storage and (ii) expected remaining allocation
    for x in self.district_list:
      for y in self.contract_list:
        next_year_carryover, this_year_carryover = x.update_balance(t, wateryear, y.storage_pool[t], y.allocation[t], y.available_water[t], y.name, y.tot_carryover, y.type)
        y.projected_carryover += next_year_carryover
        y.running_carryover += this_year_carryover
      ##summation of all projected contracts for each water district (total surface water expected)
    counter = 0
	#find the 'in leiu' recovery capacity at each in-leiu recharge district using this day's irrigation demand
	#recovery is based on the surface water allocations for the in-leiu bank (i.e., the surface water that they give their banking partners
	#when the partners want to recover banked water
    self.update_leiu_capacity()
	
    for x in self.district_list:
      #district can request recovery of their banked water
      x.open_recovery(dowy, wateryear)
	  ##Recover Banked Water
    flow_type = "recovery"
    #initialize the recover variables at the bank
    for w in self.waterbank_list:
      for xx in w.participant_list:
        w.recovery_use[xx] = 0.0#how much of the recovery capacity was used by the account holder
    #same but for 'in leiu' banks
    for w in self.get_iterable(self.leiu_list):
      w.tot_leiu_recovery_use = 0.0
      for xx in w.participant_list:
        w.recovery_use[xx] = 0.0
        w.bank_deliveries[xx] = 0.0
    
    if self.sanluisstate.min_daily_uncontrolled < self.sanluisstate.flood_flow_min:
	  #recover banked groundwater
      #only looking at GW exchanges for a few contracts
      self.canal_contract['caa'] = [self.swpdelta]#only want to 'paper' exchange swp contracts
      self.canal_contract['fkc'] = [self.friant1, self.friant2]#reset california aqueduct contracts to be all san luis contracts
      for z in [self.calaqueduct, self.fkc, self.kernriverchannel]:
        for y in self.canal_contract[z.name]:
          exchange_contract = y.name
          delivery_key = exchange_contract + "_banked"
          self.set_canal_direction(flow_type)		
          canal_size = len(self.canal_district[z.name])
          total_canal_demand = self.search_canal_demand(dowy,z, "none", z.name, 'normal', flow_type, wateryear, 'recovery')
      self.set_canal_direction(flow_type)		
		
    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]#reset california aqueduct contracts to be all san luis contracts
    self.canal_contract['fkc'] = [self.friant1, self.friant2]#reset california aqueduct contracts to be all san luis contracts
		
	##Direct deliveries from surface water sources
    flow_type = "recharge"
    for a in [self.sanluis, self.isabella, self.millerton, self.success, self.kaweah]:
      for z in self.reservoir_canal[a.key]:
        self.set_canal_direction(flow_type)

        canal_size = len(self.canal_district[z.name])
        total_canal_demand = self.search_canal_demand(dowy, z, a.key, z.name, 'normal', flow_type, wateryear,'delivery')
        available_flow = 0.0
        for zz in total_canal_demand:
          available_flow += total_canal_demand[zz]
        excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, z, a.key, z.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'delivery')

        #total_canal_demand = self.find_contract_demand(t, dowy, wateryear, z, a.key, z.name, 'normal',flow_type)
        #excess_water, unmet_demand = self.deliver_contracts(t, dowy, z, a.key, z.name, total_canal_demand, canal_size, wateryear, 'normal',flow_type)
		
    self.set_canal_direction(flow_type)
    
    #Find district banking needs
    for x in self.district_list:
      for y in x.contract_list:
        contract_object = self.contract_keys[y]
        reservoir = self.contract_reservoir[contract_object.key]
        x.open_recharge(m-1, da, wateryear, reservoir.numdays_fillup['demand'], contract_object.tot_carryover - contract_object.annual_deliveries[wateryear], y, wyt, self.contract_turnouts[y])

	##Deliveries for banking
    flow_type = "recharge"
    for a in [self.sanluis, self.isabella, self.millerton, self.success, self.kaweah]:
      for z in self.reservoir_canal[a.key]:
        self.set_canal_direction(flow_type)

        canal_size = len(self.canal_district[z.name])
        total_canal_demand = self.search_canal_demand(dowy, z, a.key, z.name, 'normal',flow_type,wateryear,'banking')
        available_flow = 0.0
        for zz in total_canal_demand:
          available_flow += total_canal_demand[zz]

        excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, z, a.key, z.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'banking')
		
    self.set_canal_direction(flow_type)
		
	
    #swp/cvp_pump - find maximum pumping levels based on space in san luis(inputs for the northern model)
	#swp/cvp_release -  toggle for 'max pumping' releases, based on space in san luis (inputs for the northern model)
    if t < (self.T -1):
      swp_pump, cvp_pump, = self.find_san_luis_space(t, 6680.0*cfs_tafd, 4430.0*cfs_tafd)
    else:
      swp_pump = 0.0
      cvp_pump = 0.0
	#take direct recharge deliveries and 'absorb' them into the groundwater, clearing way for more space in the recharge basins
    for k in self.waterbank_list:#at water banks
      k.sum_storage()
      k.absorb_storage()
    for k in self.leiu_list:#at in-leiu district banks (some also have direct recharge capacity, in addition to in-leiu)
      k.absorb_storage()
    for x in self.district_list:#at in-district recharge facilities
      if x.current_recharge_storage > 0.0:
        x.absorb_storage()
		
    #reservoir class water balance do not include releases for irrigation/recharge deliveries
	#update storage based on total contract deliveries each day
    for y in self.contract_list:
      reservoir = self.contract_reservoir[y.key]
      if t < (self.T - 1):
        reservoir.S[t+1] -= y.daily_deliveries
      y.daily_deliveries = 0.0
	  
	  ####ASSUMPTION THAT ANY DEMAND NOT MET BY SURFACE WATER IS MET THROUGH PUMPING
	  ####doesn't do anything in the model (no GW connection), but can change this assumption/link to other models
    for x in self.district_list:
      if m == 10 and da == 1:
        x.annual_private_pumping = x.dailydemand
      else:
        x.annual_private_pumping += x.dailydemand

	####FOR RESULTS-OUTPUT (not output to northern model, but output for plots)
    for x in self.district_list:
      for y in self.contract_list:
        #from individual contracts - paper balance, carryover storage, allocations, and deliveries (irrigation) - records daily values
        x.accounting(t, da, m, wateryear,y.name)
        y.accounting(t, da, m, wateryear, x.deliveries[y.name][wateryear], x.carryover[y.name], x.turnback_pool[y.name], x.deliveries[y.name + '_flood'][wateryear])
      x.accounting_banking_activity(t, da, m, wateryear)
	  
    #update individual accounts in groundwater banks
    for w in self.waterbank_list:
      w.accounting(t, m, da, wateryear)
    for w in self.leiu_list:
      w.accounting_leiubank(t, m, da, wateryear)

    ##Reset contracts for the next water year, distribute unused contract water into carryover flows/ next year's contract allocation
    if m == 9 and da == 30:
      for z in self.pumping_turnback:
        self.pumping_turnback[z] = 0.0

      for y in self.contract_list:
        lastYearCarryover = y.tot_carryover
        y.tot_carryover = 0.0
        y.tot_new_alloc = 0.0
        for x in self.district_list:
          use_contract = 0
          for yy in x.contract_list:
            if yy == y.name:
              use_contract = 1
          if use_contract == 1:				
            new_alloc, carryover = x.calc_carryover(y.storage_pool[t], wateryear, y.type, y.name)
            y.tot_new_alloc += new_alloc
            y.tot_carryover += carryover
        y.running_carryover = y.tot_carryover
	  
    #reset counter for delta contract adjustment for foregone pumping and uncontrolled releases
    if m == 9 and da == 30:
      for z in self.pumping_turnback:
        self.pumping_turnback[z] = 0.0
		
    ##Clear Canal Flows
    ##every day, we zero out the flows on each canal (i.e. no canal storage, no 'routing' of water on the canals)
	###any flow released from a reservoir is assumed to arrive at its destimation immediately
    #Reset canals and record turnouts & flows at each node
    for z in self.canal_list:
      counter = 0
      for canal_loc in range(0, len(self.canal_district[z.name])):
        loc_id = self.canal_district[z.name][canal_loc]
        z.accounting(t, loc_id.key, counter)
        counter += 1
      z.num_sites = len(self.canal_district[z.name])
      z.turnout_use = np.zeros(z.num_sites)
      z.flow = np.zeros(z.num_sites+1)
      z.locked = 0

		                	  
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
    d = self.current_day_year[t]
    y = self.current_year[t]
    m = self.current_month[t]
    da = self.current_day_month[t]
    dowy = water_day(d,calendar.isleap(y))
   
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    dowy_eom = [123, 150, 181, 211, 242, 272, 303, 333, 364, 30, 60, 91] 
    month_evaluate = m - 1
    		      
    month_evaluate = m - 1
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
      if dowy < 123:
        total_taxed = (123 + 92 - dowy)*max_pump[key] - (max_tax_free[wyt][key][dowy] - max_tax_free[wyt][key][122]) - max_tax_free[wyt][key][274]
      elif dowy < 274:
        total_taxed = (273 + 92 - dowy)*max_pump[key] - max_tax_free[wyt][key][dowy]
      else:
        total_taxed = (365 - dowy)*max_pump[key] - max_tax_free[wyt][key][dowy]
    
      #if month_evaluate > 8:
      for monthloop in range(0, 12):
        start_m = dowy_eom[monthloop] - days_in_month[monthloop] + 1
        end_m = dowy_eom[monthloop]
        total_tax_free = max_tax_free[wyt][key][start_m] - max_tax_free[wyt][key][end_m]

          #if excess_storage[key] > total_taxed and dowy < dowy_eom[monthloop]:          
        if monthloop == 3 or monthloop == 4:
          max_pump['swp'] = 750.0*cfs_tafd
          max_pump['cvp'] = 750.0*cfs_tafd
        else:
          max_pump['swp'] = 6680.0*cfs_tafd
          max_pump['cvp'] = 4300.0*cfs_tafd
        if dowy_eom[monthloop] < dowy:
          running_days = 365 - dowy + dowy_eom[monthloop]
        else:
          running_days = dowy_eom[monthloop] - dowy
        if t > self.omr_rule_start - running_days:
          max_pump['swp'] = min(max_pump['swp'], max_pumping['swp'][monthloop]/days_in_month[monthloop])
          max_pump['cvp'] = min(max_pump['cvp'], max_pumping['cvp'][monthloop]/days_in_month[monthloop])


        expected_pumping[key]['taxed'][monthloop] = max_pump[key]*days_in_month[monthloop]
        expected_pumping[key]['untaxed'][monthloop] = min(max(proj_surplus[key][monthloop],total_tax_free), max_pump[key]*days_in_month[monthloop])
        expected_pumping[key]['gains'][monthloop] = min(proj_surplus[key][monthloop], max_pump[key]*days_in_month[monthloop])
     	  		  
    return expected_pumping
	
  def find_pumping_release(self, start_storage, pump_max, month_demand, month_demand_must_fill, allocation, expected_pumping, flood_supply, available_storage, projected_carryover, current_carryover, max_tax_free, wyt, t, key):
   ##this function is used by the swpdelta & cvpdelta contracts to manage san luis reservoir storage
	##and coordinate pumping at the delta
    ##state and federal storage portions managed seperately
    d = self.current_day_year[t]
    y = self.current_year[t]
    m = self.current_month[t]
    da = self.current_day_month[t]
    dowy = water_day(d,calendar.isleap(y))
   
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    dowy_eom = [123, 150, 181, 211, 242, 272, 303, 333, 364, 30, 60, 91] 
    month_evaluate = m - 1
    first_month_frac = max(days_in_month[month_evaluate] - da, 0.0)/days_in_month[month_evaluate]
	
	
	###Initial storage projections - current month
	##calculate expected deliveries during this month from san luis
    #expected_demands = (month_demand[wyt][month_evaluate]*allocation + month_demand_must_fill[wyt][month_evaluate])/days_in_month[month_evaluate]
    expected_demands = (month_demand[wyt][month_evaluate] + month_demand_must_fill[wyt][month_evaluate])/days_in_month[month_evaluate]
    expected_inflow = expected_pumping['gains'][month_evaluate]/days_in_month[month_evaluate]
    expected_untaxed = (expected_pumping['untaxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])
    expected_taxed = (expected_pumping['taxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])

	#how much 'unstored' pumping can we expect into San Luis?
    #self.month_averages comes from self.predict_delta_gains
	#proj_surplus & proj_surplus2 are generated in the northern model, from 8RI regression in self.predict_delta_gains
    if month_evaluate == 3 or month_evaluate == 4:
      expected_inflow = 0.75
    #expected monthly change in san luis storage
    net_monthly = (expected_inflow - expected_demands)*max(days_in_month[month_evaluate] - da, 0.0)
    ##Enter into a loop for projecting storage & pumping forward one month at a time
	##start with current estimates
    next_month_storage = start_storage#running storage levels
    this_month_days = max(days_in_month[month_evaluate] - da, 0.0)#running days in a month
    article21 = 0.0#initialize article 21 release estimates
    numdays_fillup = 999.9#initialize numdays_fillup variable
    numdays_fillup_override = 0.0
    total_days_remaining = 0.0#used for estimates of how long san luis will take to fill up (for districts to make carryover decisions)

    pumping_toggle = 1#toggle for releasing water to maximum pumping levels
    tax_free_toggle = 1#toggle for releasing water to 'tax free' pumping levels
    pumping_toggle_override = 0#toggle for releasing water to maximum pumping levels
    tax_free_toggle_override = 0#toggle for releasing water to 'tax free' pumping levels
	  
    ##loop through all months until april (april/may have very limited pumping, should not plan for any pumping to occur then)
	##this loop helps to project storage in san luis up to a year out > so we know in advance if we need to pump or will be filling the reservoir
	##note: this loop will go through one water year and into the next one
    while month_evaluate >= 5 or month_evaluate < 3:
    #while month_evaluate == m - 1:
      #estimate storage at the end of this month by adding monthly change to the running storage tally
      next_month_storage += net_monthly
      if net_monthly > 0.0:
        partial_month_remaining = max(1 - max(next_month_storage - 1020.0, 0.0)/net_monthly, 0.0)*days_in_month[month_evaluate]
      else:
        next_month_storage = min(1020.0 + net_monthly, next_month_storage)
        partial_month_remaining = 0.0
     
	  ##can we reach the storage targets only using 'tax free' pumping?
      ##how much water can we expect to pump w/o additional E/I tax through the end of the month?
      #if dowy <= dowy_eom[month_evaluate]:#running water year is the same as the beginning of the loop
        #how much 'tax free' pumping through the end of this month? - total tax free remaining at the current simulation day, minus total tax free remaining at the end of the looped month
        #running_tax_free_pumping = self.max_tax_free[wyt][key][dowy] - self.max_tax_free[wyt][key][dowy_eom[month_evaluate]]
      #else:#looped into the next water year, so we have to calculate the tax free pumping remaining through the end of the current year, then add in the tax free remaining through the looped month in the next year
        #running_tax_free_pumping = self.max_tax_free[wyt][key][dowy] + self.max_tax_free[wyt][key][0] - self.max_tax_free[wyt][key][dowy_eom[month_evaluate]]
      #running_tax_free_pumping will be added to the net_month storage variable, so we don't want to double-count 'unstored pumping'
      #if running_tax_free_pumping > available_pumping:
        #running_tax_free_pumping = available_pumping
	  ##note - beginning month = m; looped month = month_evaluate
      if start_storage > 1000.0:
        #if san luis storage is currently greater than capacity, no pumping, article21 releases triggered
        pumping_toggle = min(0, pumping_toggle)
        tax_free_toggle = min(0, tax_free_toggle)
        article21 = max(next_month_storage - 1000.0, article21)
        numdays_fillup = 0.0#if this condition is hit, no more days needed to fill reservoir (already full)
      if next_month_storage < 1020.0:
        article21 = max(0.0, article21)
        #if expected storage is less than 0 in any month, pump at max, no article 21
        if next_month_storage + min(expected_untaxed, available_storage) > 1020.0:
          numdays_fillup = min(numdays_fillup,total_days_remaining+partial_month_remaining)
        else:
          numdays_fillup = min(numdays_fillup, 999.9)#reservoir does not fill up in this condition (if it was full in prior loop months, retains its value)
        if next_month_storage + min(expected_untaxed, available_storage) > (1020.0 + current_carryover):
          pumping_toggle = min(0, pumping_toggle)
          tax_free_toggle = min(0, tax_free_toggle)
        elif next_month_storage + expected_taxed > (1020.0 + current_carryover):
          pumping_toggle = min(0, pumping_toggle)
          tax_free_toggle = min(1, tax_free_toggle)
        else:
          pumping_toggle = min(1, pumping_toggle)
          tax_free_toggle = min(1, tax_free_toggle)
      else:
        article21 = max(0.0, article21)
        pumping_toggle = min(0, pumping_toggle)
        tax_free_toggle = min(0, tax_free_toggle)
        #article21 flows are the expected extra flows divided by the number of days until the end of the month
        numdays_fillup = min(numdays_fillup,total_days_remaining+partial_month_remaining)   

      if (next_month_storage + expected_untaxed) < 0.0:
        tax_free_toggle_override = 1
        pumping_toggle_override = 1
      elif next_month_storage < 0.0:
        tax_free_toggle_override = 1
	  ##note - beginning month = m; looped month = month_evaluate

		   		   
      ##After we calculate what the pumping for SL based off projections from this month, we step the month
      ##forward and project new storage & pumping for the next month, and re-evaluate all releases.  From Oct-Mar, if
      ##any month triggers the pumping to stop, the pumping stops.  From June-Sept, if any month triggers the pumping, the
	  ##pumping occurs

      month_evaluate += 1
      if month_evaluate > 11:
        month_evaluate = 0
      expected_demands = (month_demand[wyt][month_evaluate] + month_demand_must_fill[wyt][month_evaluate])/days_in_month[month_evaluate]
      expected_inflow = expected_pumping['gains'][month_evaluate]/days_in_month[month_evaluate]
      expected_untaxed += (expected_pumping['untaxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])
      expected_taxed += (expected_pumping['taxed'][month_evaluate] - expected_pumping['gains'][month_evaluate])

	  #how much 'unstored' pumping can we expect into San Luis?
      #self.month_averages comes from self.predict_delta_gains
	  #proj_surplus & proj_surplus2 are generated in the northern model, from 8RI regression in self.predict_delta_gains
      if month_evaluate == 3 or month_evaluate == 4:
        expected_inflow = 0.75
      #expected monthly change in san luis storage
      net_monthly = (expected_inflow - expected_demands)*days_in_month[month_evaluate]
      total_days_remaining += this_month_days
      this_month_days = days_in_month[month_evaluate]

    return max(pumping_toggle, pumping_toggle_override), max(tax_free_toggle, tax_free_toggle_override), article21, numdays_fillup
      
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
#############################  State Variables that use data from more than one obejct class#########################
#####################################################################################################################	  
  def project_urban_pumping(self, d, da, dowy, wateryear, projected_allocation_swp, projected_allocation_cvp):
    urban_list = [self.socal, self.centralcoast, self.southbay]
    projected_allocation = {}
    projected_allocation['swp'] = projected_allocation_swp
    projected_allocation['cvp'] = projected_allocation_cvp

    if da == 1:
      self.k_close_wateryear = {}
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        for y in urban_list:
          y.monthlydemand[wyt] = np.zeros(12)
      dowy_md = [122, 150, 181, 211, 242, 272, 303, 334, 365, 30, 60, 91]
      for key in ['swp', 'cvp']:
        for x in range(0, len(self.socal.hist_demand_dict[key]['annual_sorted'])):
          if projected_allocation[key] < self.socal.hist_demand_dict[key]['annual_sorted'][x]:
            break
        self.k_close_wateryear[key] = self.socal.hist_demand_dict[key]['sorted_index'][x]
        last_month = 0
	    ###Divide aqueduct branch pumping into 'monthly demands'
        for monthloop in range(0,12):
          monthcounter = monthloop + 9
          if monthcounter > 11:
            monthcounter -= 12
          this_month = dowy_md[monthcounter]
          for wyt in ['W', 'AN', 'BN', 'D', 'C']:
            for y in urban_list:
              y.monthlydemand[wyt][monthcounter] += np.mean(y.hist_demand_dict[key]['daily_fractions'][self.k_close_wateryear[key]][last_month:this_month])*(projected_allocation[key]*y.urb_coef[key][0] + y.urb_coef[key][1])
          last_month = this_month + 1
          

    for y in urban_list:
      y.dailydemand = 0.0
      y.annualdemand = 0.0
      for key in ['swp', 'cvp']:
        y.dailydemand += (projected_allocation[key]*y.urb_coef[key][0] + y.urb_coef[key][1])*y.hist_demand_dict[key]['daily_fractions'][self.k_close_wateryear[key]][dowy]
        y.annualdemand += (projected_allocation[key]*y.urb_coef[key][0] + y.urb_coef[key][1])*sum(y.hist_demand_dict[key]['daily_fractions'][self.k_close_wateryear[key]][dowy:364])
      y.dailydemand_start = y.dailydemand
      y.ytd_pumping[wateryear] += y.dailydemand


  def agg_contract_demands(self):
  #this function sums district demands by reservoir (i.e. - for each reservoir, the sum of the demand of all districts
  #with a contract that is held at that reservoir
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      for res in self.reservoir_list:
        res.monthly_demand[wyt] = np.zeros(12)
        res.monthly_demand_must_fill[wyt] = np.zeros(12)
        for x in self.district_list:
          use_reservoir = 0
          total_contract = 0.0
          for y in x.contract_list:
            for yy in self.reservoir_contract[res.key]:
              if y == yy.name:
                use_reservoir = 1
                total_contract += x.projected_supply[y]
          if x.annualdemand > 0.0:
            demand_fraction = min(total_contract/x.annualdemand, 1.0)
          else:
            demand_fraction = 0.0
          if use_reservoir == 1:
            for monthcounter in range(0,12):
              if x.must_fill == 1:
                res.monthly_demand_must_fill[wyt][monthcounter] += x.monthlydemand[wyt][monthcounter]*days_in_month[monthcounter]
              else:
                res.monthly_demand[wyt][monthcounter] += x.monthlydemand[wyt][monthcounter]*days_in_month[monthcounter]*demand_fraction
        total_capacity = 0.0
        for canal_to_reservoir in self.reservoir_canal[res.key]:
          total_capacity += canal_to_reservoir.capacity['normal'][0]
        for monthcounter in range(0,12):
          if res.monthly_demand[wyt][monthcounter] > total_capacity*cfs_tafd*days_in_month[monthcounter]:
            res.monthly_demand[wyt][monthcounter]  = total_capacity*cfs_tafd*days_in_month[monthcounter]
              			  
  def appropriate_carryover(self, forgone, key, wateryear):
    #if pumping is turned 'off' because of san luis storage conditions,
	#any carryover water (up to the total potential pumping) is taken from the individual
	#district that owned it and redistributed to all districts as this year's allocation
    remaining_carryover = {}
    remaining_balance = {}
    for y in self.get_iterable(self.reservoir_contract[key]):
      remaining_carryover[y.name] = 0.0
      remaining_balance[y.name] = 0.0
    for x in self.district_list:
      #find total amount of carryover that has not yet been delivered, by contract
      for y in remaining_carryover:
        remaining_carryover[y] += max(x.carryover[y] - x.deliveries[y][wateryear], 0.0)
    total_remaining = 0.0
    for y in remaining_carryover:
      #total the carryover for each contract at that reservoir
      total_remaining += remaining_carryover[y]
    if total_remaining > 0.0:
      #what % of carryover needs to be taken
      carryover_fraction = min(forgone/total_remaining, 1.0)
      for y in remaining_carryover:
        current_contract = self.contract_keys[y]
        #carryover contracts canceled
        current_contract.tot_carryover -= remaining_carryover[y]*carryover_fraction
        #'new allocation' credited to the contract
        self.pumping_turnback[key] -= remaining_carryover[y]*carryover_fraction
        for x in self.district_list:
          x.carryover[y] -= max(x.carryover[y] - x.deliveries[y][wateryear], 0.0)*carryover_fraction
		  
  def update_carryover(self, spill, key, wateryear):
  #This function is meant to take a flood release and subtract it either from
  #existing carryover or projected contract deliveries
    remaining_carryover = {}
    carryover_fraction = 0.0
    #loop through the canals associated with the reservoir, 'key'
    for z in self.get_iterable(self.reservoir_canal[key]):
      #what contracts are deliveried on that canal
      for y in self.get_iterable(self.canal_contract[z.name]):
        #initialize remaining carryover variable
		#this also makes a list of all contracts w/carryover (for looping later)
        remaining_carryover[y.name] = 0.0
		
    #find total carryover (district carryover balances that have not yet been delivered)
    for x in self.district_list:
      for y in remaining_carryover:
        remaining_carryover[y] += max(x.carryover[y] - x.deliveries[y][wateryear], 0.0)
	
    #sum carryover in all contracts on that reservoir
    total_remaining = 0.0
    for y in remaining_carryover:#loop over all contracts w/carryover balances
      total_remaining += remaining_carryover[y]
	  
    #if there is carryover - what % needs to be taken to make up for spillage
    if total_remaining > 0.0:
      carryover_fraction = min(spill/total_remaining, 1.0)
	  
      #if there is more spill than remaining carryover, need to add to the contract adjustment (this amount is subtracted from total contract allocation)
      self.pumping_turnback[key] += max(spill - total_remaining*carryover_fraction, 0.0)
	  
      for y in remaining_carryover:#loop over all contracts w/carryover balances
        #reduce overall contract carryover balance
        current_contract = self.contract_keys[y]
        current_contract.tot_carryover -= remaining_carryover[y]*carryover_fraction
        #reduce individual contract carryover balance (only on undelivered carryover
        for x in self.district_list:
          x.carryover[y] -= max(x.carryover[y] - x.deliveries[y][wateryear], 0.0)*carryover_fraction
    else:
      #if no carryover, just add the spill to the contract adjustment (this amount is subtracted from total contract allocation)
      self.pumping_turnback[key] += max(spill, 0.0)
    		

  def find_recharge_bank(self,m,wyt):
  
  ###this function projects the total GW recharge
  ###capacity in each waterbank out 12 months, and then allocates
  ###that capacity to individual districts based on their
  ###ownership stake in teh waterbank
	
    for w in self.waterbank_list:
    ##direct recharge capacity is directly related to
    ##how long the banks have been used continuously
      #this month use tracks if the bank has been used in the past month
      if w.thismonthuse == 1:
        w.monthusecounter += 1
        w.monthemptycounter = 0
        if w.monthusecounter > 11:
          w.monthusecounter = 11
        #this function describes how recharge rate declines over time
        w.recharge_rate *= w.recharge_decline[w.monthusecounter]
      else:
      #in order for recharge rate to 'bounce back', needs 3 months of 
      #continuous non-use
        w.monthemptycounter += 1
        if w.monthemptycounter == 3:
          w.monthusecounter = 0
          w.recharge_rate = w.initial_recharge*cfs_tafd
      w.thismonthuse = 0
      
	  ###distribute this recharge capacity among districts (based on ownership share)
      for member in w.participant_list:
        num_districts = len(self.get_iterable(self.district_keys[member]))
        for irr_district in self.get_iterable(self.district_keys[member]):
          irr_district.max_direct_recharge[0] += w.ownership[member]*w.recharge_rate/num_districts
          for res in self.reservoir_list:
            if irr_district.reservoir_contract[res.key] == 1:
              res.max_direct_recharge[0] += w.ownership[member]*w.recharge_rate/num_districts
		  ##each month of consecutive use results in the recharge capacity of the bank declining
          ##we want to know what is the recharge capacity available in the future, considering 
          ##continuous use from this point on
          decline_coef = 1.0
          for m_counter in range(1,12):
            decline_counter = w.monthusecounter + m_counter
            if decline_counter > 11:
              decline_counter = 11
            decline_coef *= w.recharge_decline[decline_counter]
            irr_district.max_direct_recharge[m_counter] += w.ownership[member]*w.recharge_rate*decline_coef/num_districts
            for res in self.reservoir_list:
              if irr_district.reservoir_contract[res.key] == 1:
                res.max_direct_recharge[m_counter] += w.ownership[member]*w.recharge_rate*decline_coef/num_districts
				
  def find_recharge_leiu(self,m,wyt):
  
  ###this function projects the total GW recharge
  ###capacity in each in-leiu banking district out 12 months, and then allocates
  ###that capacity to individual districts based on their
  ###ownership stake in teh waterbank
	
    #in-leiu banks combine both direct and in-leiu recharge
    #capacity, so both must be forecasting moving forward (12 months)	
    for w in self.leiu_list:
      if w.thismonthuse == 1:
        w.monthusecounter += 1
        w.monthemptycounter = 0
        if w.monthusecounter > 11:
          w.monthusecounter = 11
        w.recharge_rate *= w.recharge_decline[w.monthusecounter]
      else:
        w.monthemptycounter += 1
        w.recharge_rate += max(w.in_district_direct_recharge*cfs_tafd - w.recharge_rate, 0.0)*0.5
        if w.monthemptycounter == 3:
          w.monthusecounter = 0
          w.recharge_rate = w.in_district_direct_recharge*cfs_tafd
      w.thismonthuse = 0
	  
      ##find district share of recharge capacity
      for member in w.participant_list:
        num_districts = len(self.get_iterable(self.district_keys[member]))
        for irr_district in self.get_iterable(self.district_keys[member]):
          #current direct recharge
          irr_district.max_direct_recharge[0] += w.leiu_ownership[member]*w.recharge_rate/num_districts
          #current in leiu recharge (based on irrigation demands of the in-leiu bank)
          irr_district.max_leiu_recharge[0] += w.leiu_ownership[member]*w.monthlydemand[wyt][m-1]/num_districts
          for res in self.reservoir_list:
            if irr_district.reservoir_contract[res.key] == 1:
              res.max_direct_recharge[0] += w.leiu_ownership[member]*w.recharge_rate/num_districts
			  
		  ##each month of consecutive use results in the recharge capacity of the bank declining
          ##we want to know what is the recharge capacity available in the future, considering 
          ##continuous use from this point on
          decline_coef = 1.0
          for m_counter in range(1,12):
            decline_counter = w.monthusecounter + m_counter
            future_month = m - 1 + m_counter
            if future_month > 11:
              future_month -= 12
            if decline_counter > 12:
              decline_counter = 12
            decline_coef *= w.recharge_decline[decline_counter]
            #future (12 months) direct recharge
            irr_district.max_direct_recharge[m_counter] += w.leiu_ownership[member]*w.recharge_rate*decline_coef/num_districts
            #future (12 months) in leiu recharge
            irr_district.max_leiu_recharge[m_counter] += w.leiu_ownership[member]*w.monthlydemand[wyt][future_month]/num_districts
            for res in self.reservoir_list:
              if irr_district.reservoir_contract[res.key] == 1:
                res.max_direct_recharge[m_counter] += w.leiu_ownership[member]*w.recharge_rate*decline_coef/num_districts

  def find_recharge_indistrict(self,m,wyt):
  
  ###this function projects the total GW recharge
  ###capacity within the boundaries of each district,
  ###then adds that recharge to the expected recharge from
  ###banking opportunities
  
    for x in self.district_list:
      if x.in_district_storage > 0.0 and not x.in_leiu_banking:
        if x.thismonthuse == 1:
          x.monthusecounter += 1
          x.monthemptycounter = 0
          if x.monthusecounter > 11:
            x.monthusecounter = 11
          x.recharge_rate *= x.recharge_decline[x.monthusecounter]
        else:
          x.monthemptycounter += 1
          x.recharge_rate += max(x.in_district_direct_recharge*cfs_tafd - x.recharge_rate, 0.0)*0.5
          if x.monthemptycounter == 3:
            x.monthusecounter = 0
            x.recharge_rate = x.in_district_direct_recharge*cfs_tafd
        x.thismonthuse = 0
      if x.recharge_rate > 0.0:
        x.max_direct_recharge[0] += x.recharge_rate
        for res in self.reservoir_list:
          if x.reservoir_contract[res.key] == 1:
            res.max_direct_recharge[0] += x.recharge_rate

        decline_coef = 1.0
        for m_counter in range(1,12):
          decline_counter = x.monthusecounter + m_counter
          if decline_counter > 12:
            decline_counter = 12
          decline_coef *= x.recharge_decline[decline_counter]
          x.max_direct_recharge[m_counter] += x.recharge_rate*decline_coef
          for res in self.reservoir_list:
            if x.reservoir_contract[res.key] == 1:
              res.max_direct_recharge[0] += x.recharge_rate*decline_coef

  def update_leiu_capacity(self):
    #initialize individual banking partner's recovery capacity
    for w in self.leiu_list:
      for member in w.participant_list:
        for irr_district in self.get_iterable(self.district_keys[member]):
          irr_district.extra_leiu_recovery = 0.0
    #find individual banking partner's (district') recovery capacity based on their total 
	#supply in reservoirs accessable by their partners
    for w in self.leiu_list:
      for member in w.participant_list:
        num_districts = len(self.get_iterable(self.district_keys[member]))
        for irr_district in self.get_iterable(self.district_keys[member]):
          for y in irr_district.contract_list:#if the banking partner has a contract at that reservoir, they can trade water there
            for yy in w.contract_list:
              if y == yy:
                irr_district.extra_leiu_recovery += w.projected_supply[yy]*w.leiu_trade_cap*w.leiu_ownership[member]
           						
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


#####################################################################################################################
#############################     Flood operations       ############################################################
#####################################################################################################################

	
  def flood_operations(self, t, m, dowy, wateryear, reservoir, flow_type, overflow_toggle, wyt):
    ###available flood taken from reservoir step
	###min-daily-uncontrolled is based on reservoir forecasts & available recharge space
    #releases from the flood pool, or in anticipation of the flood releases
    #'anticipation' releases are only made if they are at least as large as the
	#total recharge capacity at the reservoir
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    monthdays = days_in_month[m-1]
    if reservoir.key == "SLS" or reservoir.key == "SLF":
      begin_key = "SNL"
    else:
      begin_key = reservoir.key
    if reservoir.flood_flow_min > reservoir.min_daily_uncontrolled:
      flood_available = reservoir.fcr
    else:
      flood_available = max(reservoir.fcr, reservoir.min_daily_uncontrolled)
	  


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
      for z in self.reservoir_canal[reservoir.key]:
        #total flood deliveries on each canal to each priority type
        tot_canal_demand = self.search_canal_demand(dowy, z, begin_key, z.name, 'normal',flow_type,wateryear,'flood')
        for demand_type in tot_canal_demand:
          #sum priority deliveries over all canals
          flood_demand[demand_type][canal_counter] = tot_canal_demand[demand_type]
          flood_demand['tot_' + demand_type] += flood_demand[demand_type][canal_counter]
        canal_counter += 1
		  
      canal_counter = 0
      total_flood_deliveries = 0.0
      total_excess_flow = 0.0
	  
      for z in self.reservoir_canal[reservoir.key]:
        #first, determine the % of total demand at each priority level that can be fufilled
        #second, sum up the total deliveries to each canal from the reservoir
        priority_flows = 0.0
        flood_deliveries = 0.0
        if overflow_toggle == 1:
          type_list = ['contractor', 'alternate', 'turnout', 'excess']
        else:
          type_list = ['contractor', 'alternate']
        for demand_type in type_list:
          if flood_demand['tot_' + demand_type] > 0.0:
            flood_demand[demand_type + '_frac'] = min(max(flood_available - priority_flows, 0.0)/flood_demand['tot_' + demand_type], 1.0)# the percent of demand that can be fufilled, adjusting for priority priority deliveries
          else:
            flood_demand[demand_type + '_frac'] = 0.0
			
          priority_flows += flood_demand['tot_' + demand_type]
          flood_deliveries += flood_demand[demand_type + '_frac'] * flood_demand[demand_type][canal_counter]
    	
        canal_size = len(self.canal_district[z.name])
        if flood_deliveries > 0.0:
          excess_flows, unmet_demands = self.distribute_canal_deliveries(dowy, z, begin_key, z.name, flood_deliveries, canal_size, wateryear, 'normal', flow_type, 'flood')
        else:
          excess_flows = 0.0
			
        canal_counter += 1
        total_flood_deliveries += flood_deliveries
        total_excess_flow += excess_flows
      #if all deliveries cannot be taken, then only need to 'spill' from the 
      #reservoir what was actually delivered (unless over the flood pool - then spill into channel (not tracked)
      total_spill = max(total_flood_deliveries - total_excess_flow, reservoir.fcr)
		
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
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[15], "normal", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.fkc.find_bi_directional(self.calaqueduct.turnout_use[15], "normal", "reverse", flow_type, 'xvc', adjust_both_types,  self.xvc.locked)
      if self.calaqueduct.turnout_use[15] > 0.0:
        self.xvc.locked = 1
      #if self.kwbcanal.capacity["reverse"][2] > 0.0:
        #self.calaqueduct.find_bi_directional(self.fkc.turnout_use[22], "normal", "normal", flow_type, 'xvc')
        #self.fkc.find_bi_directional(self.fkc.turnout_use[22], "normal", "normal", flow_type, 'xvc')
      #else:
      #self.calaqueduct.find_bi_directional(self.fkc.turnout_use[22], "reverse", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.fkc.find_bi_directional(self.fkc.turnout_use[22], "reverse", "reverse", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #if self.fkc.turnout_use[22] > 0.0:
        #self.xvc.locked = 1

      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[16], "normal", "normal", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      self.kerncanal.find_bi_directional(self.calaqueduct.turnout_use[16], "closed", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      if self.calaqueduct.turnout_use[16] > 0.0:
        self.kwbcanal.locked = 1

      self.calaqueduct.find_bi_directional(self.kerncanal.turnout_use[4], "reverse", "normal", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      self.kerncanal.find_bi_directional(self.kerncanal.turnout_use[4], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      if self.kerncanal.turnout_use[4] > 0.0:
        self.kwbcanal.locked = 1

    elif flow_type == "recovery":
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[15], "reverse", "reverse", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      #self.fkc.find_bi_directional(self.calaqueduct.turnout_use[15], "reverse", "normal", flow_type, 'xvc', adjust_both_types, self.xvc.locked)
      self.kernriverchannel.find_bi_directional(self.calaqueduct.turnout_use[15], "reverse", "reverse", flow_type, 'xvc', adjust_one_type, self.xvc.locked)
      if self.calaqueduct.turnout_use[15] > 0.0:
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
	  
	  
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[16], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      self.kerncanal.find_bi_directional(self.calaqueduct.turnout_use[16], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      if self.calaqueduct.turnout_use[16] > 0.0:
        self.kwbcanal.locked = 1

      self.calaqueduct.find_bi_directional(self.kerncanal.turnout_use[4], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      self.kerncanal.find_bi_directional(self.kerncanal.turnout_use[4], "reverse", "reverse", flow_type, 'kbc', adjust_both_types, self.kwbcanal.locked)
      if self.kerncanal.turnout_use[4] > 0.0:
        self.kwbcanal.locked = 1

	  
  def set_canal_range(self, flow_dir, flow_type, canal, prev_canal, canal_size):
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
    total_canal = len(self.canal_district[canal.name])
    #recharge flows move down the canals starting from the reservoirs
    if flow_type == "recharge":
      for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
        if new_canal.key == prev_canal:
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
        starting_point = 1
        if prev_canal == "none":
          canal_range = range(starting_point, canal_size)        
        else:
          for ending_point, new_canal in enumerate(self.canal_district[canal.name]):
            if new_canal.key == prev_canal:
              break
          if ending_point == 0:
            if canal.recovery_feeder:
              canal_range = (0, 0)
            else:
              canal_range = range(starting_point,len(self.canal_district[canal.name]))
          else:
            #ending_point -= 1			  
            canal_range = range(starting_point, ending_point)
      elif flow_dir == "reverse":
        starting_point = len(self.canal_district[canal.name]) - 1
        if prev_canal == "none":
          canal_range = range(starting_point, -1, -1)
        else:
          for ending_point, new_canal in enumerate(self.canal_district[canal.name]):
            if new_canal.key == prev_canal:
              break
          if ending_point == (len(self.canal_district[canal.name])- 1):
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
	
  def distribute_canal_deliveries(self, dowy, canal, prev_canal, contract_canal, available_flow, canal_size, wateryear, flow_dir, flow_type, search_type):
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
      #for regular deliveries, we need to distinguish between demands from each contract
	  #because the distribute_canal_deliveries and search_canal_demands functions are called
	  #one reservoir at a time, there are only multiple 'types' of demand when there are more
	  #than one type of contract at a reservoir
	  #NOTE: as it is currently written, this implies some sort of contract 'priority' structure
	  #when there are more than one type of contract at a reservoir.  Not sure if this is a valid assumption
	  #or if it makes a big deal - b/c this is only for direct irrigation deliveries, and not flood/recharge water,
	  #it might not be a big deal
      type_list = (contract_canal,)
      toggle_partial_delivery = 1
      toggle_district_recharge = 0
    if search_type == 'banking':
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
    for canal_loc in canal_range:
      for zz in type_list:
        type_demands[zz] += canal.demand[zz][canal_loc]
        total_demand += canal.demand[zz][canal_loc]
    #if the available flow is greater than the total demand on the canal, the difference 
    #is returned by the function as 'excess flow'
    if available_flow > total_demand:
      excess_flow += available_flow - total_demand
      available_flow = total_demand

    #canal priority
    priority_list = self.get_iterable(self.canal_priority[canal.name])
    #contracts on this canal
    contract_list = self.canal_contract[contract_canal]
	
    #initial capacity check on flow available for delivery (i.e., canal capacity at starting node)
    available_flow, excess_flow_int = canal.check_flow_capacity(available_flow, starting_point, flow_dir)
    excess_flow += excess_flow_int
    #MAIN DISTRIBUTION LOOP - within the canal range identified above, distribute the available flow to each node based on the canal capacity and the different demand magnitudes and priorities at each node
    for canal_loc in canal_range:
      #first, find the fraction of each priority that can be diverted at this node, based on total canal demands and canal conveyance capacity
      available_capacity_int = available_flow
      for zz in type_list:
        #find the fraction of each priority type that can be filled, based on canal capacity and downstream demands
        if type_demands[zz] > 0.0:
          type_fractions[zz] = max(min(available_capacity_int/type_demands[zz], 1.0), 0.0)
        else:
          type_fractions[zz] = 0.0
        available_capacity_int -= type_demands[zz]*type_fractions[zz]
        type_demands[zz] -= canal.demand[zz][canal_loc]
      #find the object at the current node
      x = self.canal_district[canal.name][canal_loc]
      location_delivery = 0.0
      turnout_available = 0.0
      new_excess_flow = 0.0
      if isinstance(x,District):
        #find demand at the node
        #partial delivery is used if the district recieves less than full daily demand due to projected contract allocations being lower than expected remaining annual demand
        #find district demand at the node
        if search_type == "recovery":
          demand_constraint = x.find_node_output()
        else:
          demand_constraint = x.find_node_demand(contract_list, toggle_partial_delivery, toggle_district_recharge)
        #update the fractions based on turnout capacity/use capacity at the current node

        type_fractions = canal.find_priority_fractions(demand_constraint, type_fractions, type_list, canal_loc, flow_dir)
        #if a district is an in-leiu bank, partners can send water to this district for banking recharge
        if (x.in_leiu_banking and search_type == "banking") or (x.in_leiu_banking and search_type == "recovery"):
          for xx in x.participant_list:
            for wb_member in self.get_iterable(self.district_keys[xx]):
              num_members = len(self.get_iterable(self.district_keys[xx]))
              #find if the banking partner wants to bank

              deliveries = wb_member.set_request_constraints(demand_constraint, search_type, contract_list, x.inleiubanked[xx], dowy)
              #determine the priorities of the banking
              priority_bank_space = x.find_leiu_priority_space(demand_constraint, num_members, xx, toggle_district_recharge, search_type)
              priorities = wb_member.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal)
              #need to adjust the water request to account for the banking partner share of the turnout
              priority_turnout_adjusted = {}
              for zz in type_list:
                priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][canal_loc]
              #make deliveries, adjust demands & recharge availability
              actual_deliveries = x.set_deliveries(priority_turnout_adjusted,type_fractions,type_list,toggle_district_recharge,xx,wateryear)
              location_delivery += actual_deliveries
              #adjust accounts for overall contracts and invididual districts
              delivery_by_contract = wb_member.adjust_accounts(actual_deliveries,contract_list, search_type, wateryear)
              x.adjust_bank_accounts(xx, actual_deliveries, wateryear)
              for y in delivery_by_contract:
                contract_object = self.contract_keys[y]
                contract_object.adjust_accounts(delivery_by_contract[y], search_type, wateryear)
        else:
          #find if district wants to purchase this type of flow
          deliveries =  x.set_request_constraints(demand_constraint, search_type, contract_list, 0.0, dowy)
          #find what priority district has for flow purchases
          priorities = x.set_demand_priority(priority_list, contract_list, demand_constraint, deliveries, demand_constraint, search_type, contract_canal)
          priority_turnout_adjusted = {}
          #need to adjust the water request to account for the banking partner share of the turnout
          for zz in type_list:
            priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][canal_loc]
          #make deliveries, adjust demands & recharge availability
          actual_deliveries = x.set_deliveries(priority_turnout_adjusted,type_fractions,type_list,toggle_district_recharge,'none',wateryear)
          location_delivery += actual_deliveries          
          #adjust accounts for overall contracts and invididual districts
          delivery_by_contract = x.adjust_accounts(actual_deliveries,contract_list, search_type, wateryear)
          for y in delivery_by_contract:
            contract_object = self.contract_keys[y]
            contract_object.adjust_accounts(delivery_by_contract[y], search_type, wateryear)
          #record flow and turnout on each canal, check for capacity turnback at the next node				
        #find new district demand at the node
        demand_constraint = x.find_node_demand(contract_list, toggle_partial_delivery, toggle_district_recharge)
        self.find_node_demand_district(x, canal, canal_loc, demand_constraint, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list, toggle_district_recharge)
        canal.find_turnout_adjustment(demand_constraint, flow_dir, canal_loc, type_list)
		  

      elif isinstance(x, Waterbank):
        #for waterbanks, we calculate the demands of each waterbank partner individually
        for xx in x.participant_list:
          for wb_member in self.get_iterable(self.district_keys[xx]):
            num_members = len(self.get_iterable(self.district_keys[xx]))
            #find waterbank partner demand (i.e., recharge capacity of their ownership share)
            demand_constraint = x.find_node_demand(contract_list, xx, num_members, search_type)
            #find how much water is allocated to each priority demand based on the total space and turnout at this node
            current_storage = 0.0
            for yy in x.participant_list:
              current_storage += x.storage[yy]
            type_fractions = canal.find_priority_fractions(x.tot_storage - current_storage, type_fractions, type_list, canal_loc, flow_dir)
            #does this partner want to bank water?
            #find if banking partner wants to bank water
            deliveries =  wb_member.set_request_constraints(demand_constraint, search_type, contract_list, x.banked[xx], dowy)
              #flood deliveries to bank
              #deliveries = x.set_request_constraints(demand_constraint, search_type, contract_list)
            #what priority does their banked water have (can be both)
            priority_bank_space = x.find_priority_space(num_members, xx, search_type)
            priorities = x.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal, canal.name, wb_member.contract_list)
			#need to adjust the water request to account for the banking partner share of the turnout
            priority_turnout_adjusted = {}
            for zz in type_list:
              priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][canal_loc]
	        #deliver water to the waterbank
            actual_deliveries = x.set_deliveries(priority_turnout_adjusted,type_fractions,type_list,xx)
            #keep track of total demands at this node
            location_delivery += actual_deliveries
            #adjust accounts for overall contracts and invididual districts
            delivery_by_contract = wb_member.adjust_accounts(actual_deliveries,contract_list, search_type, wateryear)

            for y in delivery_by_contract:
              #update the accounting for deliveries made by each contract (overall contract accounting - not ind. district)
              contract_object = self.contract_keys[y]
              contract_object.adjust_accounts(delivery_by_contract[y], search_type, wateryear)
			
        #find new banking demands		
        self.find_node_demand_bank(x, canal, canal_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        current_storage = 0.0
        for xx in x.participant_list:
          current_storage += x.storage[xx]
        canal.find_turnout_adjustment(x.tot_storage - current_storage, flow_dir, canal_loc, type_list)
      elif isinstance(x, Canal):
        #if object is a canal, determine if water can flow from current canal into this canal (and orient the direction of flow)
        new_flow_dir = canal.flow_directions[flow_type][x.name]
        new_canal_size = len(self.canal_district[x.name])
        #how much flow can go into this new canal
        turnout_available = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]
        #initial demand for flow on the canal
        location_delivery = 0.0
        for zz in type_list:
          location_delivery += canal.demand[zz][canal_loc]*type_fractions[zz]
        #if there is space & demand, 'jump' into new canal - outputs serve as turnouts from the current canal
        location_delivery = min(location_delivery, turnout_available)
        if turnout_available > 0.001 and location_delivery > 0.001:
          new_excess_flow, canal_demands = self.distribute_canal_deliveries(dowy, x, canal.key, contract_canal, location_delivery, new_canal_size, wateryear, new_flow_dir, flow_type, search_type)
          #update canal demands
          for zz in type_list:
            canal.demand[zz][canal_loc] = canal_demands[zz]
          if new_excess_flow > 0.0:
            for zz in type_list:
              canal.demand[zz][canal_loc] = 0.0
          #record deliveries
          location_delivery -= new_excess_flow
        else:
          new_excess_flow = 0.0
          location_delivery = 0.0
        canal.find_turnout_adjustment(turnout_available, flow_dir, canal_loc, type_list)
	
      #record flow and turnout on each canal, check for capacity turnback at the next node				
      available_flow, turnback_flow, turnback_end = canal.update_canal_use(available_flow, location_delivery, flow_dir, canal_loc, starting_point, canal_size, type_list)


      #if there is more demand/available water than canal capacity at the next canal node, the 'extra' water (that was expected to be delivered down-canal in earlier calculations) can be distributed among upstream nodes if there is remaining demand
      if turnback_flow > 0.001:
        remaining_excess_flow, unmet_canal_demands = self.distribute_canal_deliveries(dowy, canal, prev_canal, contract_canal, turnback_flow, turnback_end, wateryear, flow_dir, flow_type, search_type)
        excess_flow += remaining_excess_flow

	#sum remaining demand after all deliveries have been madw
    unmet_demands = {}
    for zz in type_list:
      unmet_demands[zz] = 0.0
    for canal_loc in canal_range:
      for  zz in type_list:
        unmet_demands[zz] += canal.demand[zz][canal_loc]
		
    return excess_flow, unmet_demands
    	
  def search_canal_demand(self, dowy, canal, prev_canal, contract_canal, flow_dir,flow_type,wateryear,search_type):
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
      type_list = (contract_canal,)
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
    canal_size = len(self.canal_district[canal.name])
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
      type_deliveries[list_member] = 0.0
      canal.recovery_flow_frac[list_member] = np.ones(canal_size)
	
    #canal priority
    priority_list = self.get_iterable(self.canal_priority[canal.name])
    #contracts on this canal
    contract_list = self.canal_contract[contract_canal]

    #MAIN SEARCH LOOP - within the canal range identified above, search through
    #the objects in self.canal_district to determine the total demand on the canal
    #(divided by demand 'type')	
    for canal_loc in canal_range:
      x = self.canal_district[canal.name][canal_loc]
      if isinstance(x,District):
        #find demand at the node
        #partial delivery is used if the district recieves less than full daily demand due to projected contract allocations being lower than expected remaining annual demand
        #find district demand at the node
        if search_type == "recovery":
          demand_constraint = x.find_node_output()
        else:
          demand_constraint = x.find_node_demand(contract_list, toggle_partial_delivery, toggle_district_recharge)
        self.find_node_demand_district(x, canal, canal_loc, demand_constraint, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list, toggle_district_recharge)
        canal.find_turnout_adjustment(demand_constraint, flow_dir, canal_loc, type_list)

      elif isinstance(x, Waterbank):
        self.find_node_demand_bank(x, canal, canal_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        #once all member demands/requests/priorities have been established, we can determine how much of each type of demand can be sent to the bank (b/c of turnout space)
        if search_type == 'recovery':
          current_recovery = 0.0
          for xx in x.participant_list:
            current_recovery = x.recovery_use[xx]
          demand_constraint = x.recovery - current_recovery
        else:
          current_storage = 0.0
          for xx in x.participant_list:
            current_storage += x.storage[xx]
          demand_constraint = x.tot_storage - current_storage
        canal.find_turnout_adjustment(demand_constraint, flow_dir, canal_loc, type_list)
		
      elif isinstance(x, Canal):
        #find if the new canal can be accessed from the current canal
        if canal.turnout[flow_dir][canal_loc] > 0.0:
          #if it can, which way does the water flow onto the new canal
          new_flow_dir = canal.flow_directions[flow_type][x.name]
          #calculate the demands for this whole canal by recursively calling this function again, but with the new canal input parameters
          canal_demands = self.search_canal_demand(dowy, x, canal.key, contract_canal, new_flow_dir,flow_type,wateryear,search_type)
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
        if isinstance(x,District):
          if x.in_leiu_banking:
            for xx in x.participant_list:
              num_members = len(self.get_iterable(self.district_keys[xx]))
              for wb_member in self.get_iterable(self.district_keys[xx]):
                #find waterbank partner demand (i.e., recovery capacity of their ownership share)
                demand_constraint, demand_constraint_by_contracts = x.find_leiu_output(contract_list)
                #does this partner want recovery water?
                deliveries = wb_member.set_request_constraints(demand_constraint, search_type, contract_list, x.inleiubanked[xx], dowy)
                #what is their priority over the water/canal space?
                priority_bank_space = x.find_leiu_priority_space(demand_constraint, num_members, xx, 0, search_type)
			  
                priorities = x.set_demand_priority("N/A", "N/A", priority_bank_space, deliveries, demand_constraint, search_type, "N/A")
                #need to adjust the water request to account for the banking partner share of the turnout
                for zz in type_list:
                #paper trade recovery is equal to 
                  paper_amount = priorities[zz]
                  direct_amount = 0.0
                  contract_frac_list = np.zeros(len(x.contract_list))
				  
                  wb_member.get_paper_exchange(paper_amount, x.contract_list, demand_constraint_by_contracts, wateryear)
                  
                  x.adjust_exchange(paper_amount, xx, wateryear)
                  x.give_paper_exchange(paper_amount, x.contract_list, demand_constraint_by_contracts, wateryear)


          else:
            #for non-bank district nodes, they can accept recovery water.  we want to find how much water they can accept (based on their ability to make paper trades using the contracts in contract_list, then determine how much of the recovery water up-canal, can be delivered here as a 'paper' trade, and then how much additional water can be delivered here 'directly' (i.e., the pumping out of the water bank is going to the district that owns capacity in the water bank, so no paper trades needed - this is useful if there is no surface water storage, but a district still wants water from its water bank (and can get that water directly, from the run of the canal)
            total_district_demand = x.find_node_demand(contract_list, toggle_partial_delivery, toggle_district_recharge)
            total_available = 0.0
            existing_canal_space = canal.capacity[flow_dir][canal_loc]*cfs_tafd - canal.flow[canal_loc]
            for delivery_type in type_deliveries:
              total_available += type_deliveries[delivery_type]
            paper_recovery = min(total_district_demand, total_available)
            direct_recovery = max(min(total_available - paper_recovery, x.dailydemand*x.seepage*x.surface_water_sa - paper_recovery), 0.0)
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
              location_delivery = self.delivery_recovery(contract_list, canal, lookback_range, starting_point, paper_fractions, direct_recovery, flow_dir, type_list, priority_list, contract_canal, x.key, dowy, wateryear)
              x.give_paper_trade(location_delivery, contract_list, wateryear)
		  

	#once all canal nodes have been searched, we can check to make sure the demands aren't bigger than the canal capacity, then adjust our demands	
    #type_deliveries = canal.capacity_adjust_demand(starting_point, canal_range, flow_dir, type_list)
	
    return type_deliveries
	
  def delivery_recovery(self, contract_list, canal, lookback_range, starting_point, paper_fractions, direct_recovery, flow_dir, type_list, priority_list, contract_canal, delivery_loc_name, dowy, wateryear):
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
    toggle_district_recharge = 0
    for lookback_loc in lookback_range:
      location_pumpout = 0.0
      recovery_source = self.canal_district[canal.name][lookback_loc]
      search_type = "recovery"
      max_current_release = 0.0
      for zz in type_list:
        max_current_release = canal.demand[zz][lookback_loc]*canal.recovery_flow_frac[zz][lookback_loc]
      if isinstance(recovery_source, District):
        if recovery_source.in_leiu_banking:
          for xx in recovery_source.participant_list:
            num_members = len(self.get_iterable(self.district_keys[xx]))
            for wb_member in self.get_iterable(self.district_keys[xx]):
              #find waterbank partner demand (i.e., recovery capacity of their ownership share)
              demand_constraint = recovery_source.find_node_output()
              #does this partner want recovery water?
              deliveries = wb_member.set_request_constraints(demand_constraint, search_type, contract_list, recovery_source.inleiubanked[xx], dowy)
              #what is their priority over the water/canal space?
              priority_bank_space = recovery_source.find_leiu_priority_space(demand_constraint, num_members, xx, 0, search_type)
			  
              priorities = recovery_source.set_demand_priority("N/A", "N/A", priority_bank_space, deliveries, demand_constraint, search_type, "N/A")
              priority_turnout_adjusted = {}
              #need to adjust the water request to account for the banking partner share of the turnout
              for zz in type_list:
                priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][lookback_loc]
              for zz in type_list:
                #paper trade recovery is equal to 
                paper_amount = priority_turnout_adjusted[zz]*min(paper_fractions[zz], canal.recovery_flow_frac[zz][lookback_loc])
                direct_amount = min(direct_recovery, priority_turnout_adjusted[zz]*canal.recovery_flow_frac[zz][lookback_loc] - paper_amount)
                wb_member.get_paper_trade(paper_amount, contract_list, wateryear)
                recovery_source.adjust_recovery(paper_amount, xx, wateryear)
                location_pumpout += paper_amount
                if delivery_loc_name == wb_member.key:
                  demand_constraint = recovery_source.find_node_output()
                  max_direct_recovery = min(demand_constraint, direct_amount, recovery_source.inleiubanked[xx]/num_members)
                  actual_delivery = wb_member.direct_recovery_delivery(max_direct_recovery, wateryear)
                  recovery_source.adjust_recovery(actual_delivery, xx, wateryear)
                  location_pumpout += actual_delivery

          #recalculate the 'recovery demand' at each waterbank		  
          demand_constraint = recovery_source.find_node_output()
          self.find_node_demand_district(recovery_source, canal, lookback_loc, demand_constraint, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list, toggle_district_recharge)
          canal.find_turnout_adjustment(demand_constraint, flow_dir, lookback_loc, type_list)
		
      elif isinstance(recovery_source, Waterbank):
        for xx in recovery_source.participant_list:
          for wb_member in self.get_iterable(self.district_keys[xx]):
            num_members = len(self.get_iterable(self.district_keys[xx]))
            #find waterbank partner demand (i.e., recovery capacity of their ownership share)
            demand_constraint = recovery_source.find_node_demand(contract_list, xx, num_members, search_type) 
            #does this partner want recovery water?
            deliveries =  wb_member.set_request_constraints(demand_constraint, search_type, contract_list, recovery_source.banked[xx], dowy)
            #what is their priority over the water/canal space?
            priority_bank_space = recovery_source.find_priority_space(num_members, xx, search_type)
            priorities = recovery_source.set_demand_priority("NA", "N/A", priority_bank_space, deliveries, demand_constraint, search_type, "N/A", "N/A",wb_member.contract_list)
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
              wb_member.get_paper_trade(paper_amount, contract_list, wateryear)#exchange GW for SW 
              recovery_source.adjust_recovery(paper_amount, xx, wateryear)#adjust accounts
              location_pumpout += paper_amount
			  #if the GW is being delivered to the WB owner, more water can be delivered (not constrained by 
			  #another district's willingness to trade SW storage)
              if delivery_loc_name == wb_member.key:
                demand_constraint = recovery_source.find_node_demand(contract_list, xx, num_members, search_type)
                max_direct_recovery = min(demand_constraint, direct_amount, recovery_source.banked[xx]/num_members)
                actual_delivery = wb_member.direct_recovery_delivery(max_direct_recovery, wateryear)
                direct_recovery -= actual_delivery
                recovery_source.adjust_recovery(actual_delivery, xx, wateryear)
                location_pumpout += actual_delivery
			
        #recalculate the 'recovery demand' at each waterbank			
        self.find_node_demand_bank(recovery_source, canal, lookback_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        current_recovery = 0.0
        for xx in recovery_source.participant_list:
          current_recovery += recovery_source.recovery_use[xx]
        demand_constraint = recovery_source.recovery - current_recovery
        canal.find_turnout_adjustment(demand_constraint, flow_dir, lookback_loc, type_list)
				
      elif isinstance(recovery_source, Canal):
        new_flow_dir = canal.flow_directions['recovery'][recovery_source.name]
        new_canal_size = len(self.canal_district[recovery_source.name])
        new_prev_canal = canal.key
        new_lookback_range, new_starting_point = self.set_canal_range(new_flow_dir, 'recovery', recovery_source, new_prev_canal, new_canal_size)
        location_pumpout = self.delivery_recovery(contract_list, recovery_source, new_lookback_range, new_starting_point, paper_fractions, direct_recovery, new_flow_dir, type_list, priority_list, contract_canal, delivery_loc_name, dowy, wateryear)


      available_flow += location_pumpout
      canal.turnout_use[lookback_loc] += location_pumpout
      canal.flow[lookback_loc] += available_flow
   
    return available_flow
	
  def find_node_demand_district(self, district_node, canal, canal_loc, demand_constraint, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list, toggle_district_recharge):
  
    #this function classifies the demand at a district node - 2 parts (i) find how much water district(s) want to apply and (ii) give each water request a priority
    for zz in type_list:
      canal.demand[zz][canal_loc] = 0.0
    #if a district is an in-leiu bank, partners can send water to this district for banking recharge
    if (district_node.in_leiu_banking and search_type == "banking") or (district_node.in_leiu_banking and search_type == "recovery"):
      for xx in district_node.participant_list:
        for wb_member in self.get_iterable(self.district_keys[xx]):
          num_members = len(self.get_iterable(self.district_keys[xx]))
          #find if the banking partner wants to bank
          deliveries = wb_member.set_request_constraints(demand_constraint, search_type, contract_list, district_node.inleiubanked[xx], dowy)
          #determine the priorities of the banking
          priority_bank_space = district_node.find_leiu_priority_space(demand_constraint, num_members, xx, toggle_district_recharge, search_type)
          priorities = district_node.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal)
          for zz in type_list:
            canal.demand[zz][canal_loc] += priorities[zz]
			
          #can't purchase more than the turnout capacity

    else:
      #find if district wants to purchase this type of flow
      deliveries =  district_node.set_request_constraints(demand_constraint, search_type, contract_list, 0.0, dowy)
      #find what priority district has for flow purchases
      priorities = district_node.set_demand_priority(priority_list, contract_list, demand_constraint, deliveries, demand_constraint, search_type, contract_canal)
      for zz in type_list:
        canal.demand[zz][canal_loc] += priorities[zz]

  def find_node_demand_bank(self, bank_node, canal, canal_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list):
    #this function finds the total demand at a waterbank node - 3 parts (i) find total water that can be taken (ii) find how much water district(s) want to apply (iii) give each water request a priority  
    #for waterbanks, we calculate the demands of each waterbank partner individually
    for zz in type_list:
      canal.demand[zz][canal_loc] = 0.0

    for xx in bank_node.participant_list:
      for wb_member in self.get_iterable(self.district_keys[xx]):
        num_members = len(self.get_iterable(self.district_keys[xx]))
        #find waterbank partner demand (i.e., recharge capacity of their ownership share)
        demand_constraint = bank_node.find_node_demand(contract_list, xx, num_members, search_type) 
        #does this partner want to bank water?
        deliveries =  wb_member.set_request_constraints(demand_constraint, search_type, contract_list, bank_node.banked[xx], dowy)
          #deliveries = bank_node.set_request_constraints(demand_constraint, search_type, contract_list)
        #what is their priority over the water/canal space?
        priority_bank_space = bank_node.find_priority_space(num_members, xx, search_type)
        priorities = bank_node.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, demand_constraint, search_type, contract_canal, canal.name, wb_member.contract_list)
        #take the individual priorities of waterbank members and add them to the total canal node demands
        for zz in type_list:
          canal.demand[zz][canal_loc] += priorities[zz]
		
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


#####################################################################################################################
###############################  Record State Variables as DataFrames to print to CSV ###############################
#####################################################################################################################

  
  def results_as_df(self, time_step, list_type):
    if time_step == "daily":
      df = pd.DataFrame(index = self.df.index)
      for x in list_type:
        df = pd.concat([df, x.accounting_as_df(df.index)], axis = 1)
    else:
      df = pd.DataFrame()
      df = pd.Series(self.annual_SWP)
      df2 = pd.Series(self.annual_CVP)
      df = pd.concat([df, df2], axis = 1)
      for x in list_type:
        df = pd.concat([df, x.annual_results_as_df()], axis = 1)
    return df
     		
  def bank_as_df(self, time_step, list_type):
    if time_step == 'daily':
      df = pd.DataFrame(index = self.df.index)
      for x in list_type:
        df = pd.concat([df, x.bank_as_df(df.index)], axis = 1)	
    else:
      df = pd.DataFrame()
      for x in list_type:
        df = pd.concat([df, x.annual_bank_as_df()], axis = 1)
    return df



#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


#####################################################################################################################
###############################  Miscellaneous Functions Within Simulation ###############################
#####################################################################################################################
  def set_regulations_current_south(self):
    self.semitropic.leiu_recovery = 0.7945
    self.isabella.capacity = 361.25
    self.isabella.tocs_rule['storage'] = [[302.6,170,170,245,245,361.25,361.25,302.6],  [302.6,170,170,245,245,361.25,361.25,302.6]]
    self.poso.initial_recharge = 420.0
    self.poso.recovery = 0.6942
    self.poso.tot_storage = 2.1
    self.fkc.capacity["normal"] = [3797.0, 3797.0, 3797.0, 3797.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 2921.0, 2921.0, 2921.0, 2793.0, 2299.0, 2299.0, 2299.0, 1893.0, 1893.0, 1893.0, 1893.0, 1000.0, 0.0]
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

	
  def update_regulations_south(self,t,dowy,m,y):
    ##San Joaquin River Restoration Project, started in October of 2009 (WY 2009)
	##Additional Releases from Millerton Lake depending on WYT
    if y >= 2006:
      self.semitropic.leiu_recovery = 0.7945
    if y == 2009 and dowy == 1:
      df_short = pd.read_csv('cord/data/cord-data.csv', index_col=0, parse_dates=True)
      index_short = df_short.index
      T_short = len(df_short)
      expected_outflow_releases = {}
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        expected_outflow_releases[wyt] = np.zeros(366)
      self.millerton.calc_expected_min_release(expected_outflow_releases, np.zeros(12),1,T_short, index_short)

    if y == 2009 and m >= 10:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)
    elif y > 2009:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)
    if t == 3501:
      self.isabella.capacity = 361.25
      self.isabella.tocs_rule['storage'] = [[302.6,170,170,245,245,361.25,361.25,302.6],  [302.6,170,170,245,245,361.25,361.25,302.6]]
    if y == 2009 and dowy == 1:
      self.poso.initial_recharge = 420.0
      self.poso.recovery = 0.6942
      self.poso.tot_storage = 2.1
      self.find_all_triggers()
      self.fkc.capacity["normal"] = [3797.0, 3797.0, 3797.0, 3797.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 3427.0, 2921.0, 2921.0, 2921.0, 2793.0, 2299.0, 2299.0, 2299.0, 1893.0, 1893.0, 1893.0, 1893.0, 1000.0, 0.0]

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
    for x in self.district_list:
      contractor_toggle = 0
      for contract in x.contract_list:
        if contract == 'tableA':
          contractor_toggle = 1
      if contractor_toggle == 1:	  
        if x.key == "SOC":
          x.table_a_request = x.initial_table_a*self.swpdelta.total - request_empty
        elif x.key == "SOB":
          x.table_a_request = x.initial_table_a*self.swpdelta.total 
        elif x.key == "CCA":
          x.table_a_request = x.initial_table_a*self.swpdelta.total
        else:
          x.table_a_request = x.initial_table_a*self.swpdelta.total
    self.swpdelta.total = self.swpdelta.max_allocation
    for x in self.district_list:
      contractor_toggle = 0
      for contract in x.contract_list:
        if contract == 'tableA':
          contractor_toggle = 1
      if contractor_toggle == 1:	  
        x.project_contract['tableA'] = x.table_a_request/self.swpdelta.total
    
  def update_regulations_north(self,t,dowy):
    y = self.current_year[t]
    m = self.current_month[t]
    days_in_month = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]

	##Yuba River Accord, started in Jan of 2006 (repaces minimum flow requirements)
    if y >= 2006:
      self.yuba.env_min_flow = self.yuba.env_min_flow_ya
      self.yuba.temp_releases = self.yuba.temp_releases_ya
	  
    if y == 2008 and dowy == 1:
      #for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        #self.delta.max_tax_free[wyt]['cvp'] = np.zeros(366)
        #self.delta.max_tax_free[wyt]['swp'] = np.zeros(366)
      #for x in range(0,12):
        #if x < 6:
          #pump_max_cvp = 750.0*cfs_tafd
          #pump_max_swp = 750.0*cfs_tafd
        #else:
          #pump_max_cvp = 4300.0*cfs_tafd
          #pump_max_swp = 6680.0*cfs_tafd
		
      #calc pumping limit before inflow/export ratio is met
        #for wyt in ['W', 'AN', 'BN', 'D', 'C']:
          #outflow ratio 
          #tax_free_pumping = (self.delta.min_outflow[wyt][x]*cfs_tafd - self.delta.expected_depletion[x])*((1/(1-self.#delta.export_ratio[wyt][x]))-1)
          #if tax_free_pumping*0.55 > pump_max_cvp:
            #self.delta.max_tax_free[wyt]['cvp'][0] += pump_max_cvp*days_in_month[x]
            #self.delta.max_tax_free[wyt]['swp'][0] += min(tax_free_pumping - pump_max_cvp, pump_max_swp)*days_in_month[x]
          #else:
            #self.delta.max_tax_free[wyt]['cvp'][0] += tax_free_pumping*days_in_month[x]*0.55
            #self.delta.max_tax_free[wyt]['swp'][0] += tax_free_pumping*days_in_month[x]*0.45

      #for x in range(0,365):
        #if x > 92 and x < 274:
          #pump_max_cvp = 750.0*cfs_tafd
          #pump_max_swp = 750.0*cfs_tafd
        #else:
          #pump_max_cvp = 4300.0*cfs_tafd
          #pump_max_swp = 6680.0*cfs_tafd
        #m = int(self.index.month[x])
        #for wyt in ['W', 'AN', 'BN', 'D', 'C']:
          #tax_free_pumping = (self.delta.min_outflow[wyt][m-1]*cfs_tafd - self.delta.expected_depletion[m-1])*((1/(1-self.#delta.export_ratio[wyt][m-1]))-1)
          #if tax_free_pumping*0.55 > pump_max_cvp:
            #self.delta.max_tax_free[wyt]['cvp'][x+1] = self.delta.max_tax_free[wyt]['cvp'][x] - pump_max_cvp
            #self.delta.max_tax_free[wyt]['swp'][x+1] = self.delta.max_tax_free[wyt]['swp'][x] - min(tax_free_pumping - #pump_max_cvp, pump_max_swp)
          #else:
            #self.delta.max_tax_free[wyt]['cvp'][x+1] = self.delta.max_tax_free[wyt]['cvp'][x] - tax_free_pumping*0.55
            #self.delta.max_tax_free[wyt]['swp'][x+1] = self.delta.max_tax_free[wyt]['swp'][x] - tax_free_pumping*0.45

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
        #x.calc_expected_min_release(expected_outflow_req, expected_depletion, 0)

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
        #x.calc_expected_min_release(expected_outflow_req, expected_depletion, 0)

	  
  def get_iterable(self, x):
    if isinstance(x, cl.Iterable):
      return x
    else:
      return (x,)
	  	  
  def proj_gains(self,t):
    startYear = self.starting_year
    d = self.current_day_year[t]
    y = self.current_year[t]
    m = self.current_month[t]
    dowy = water_day(d,calendar.isleap(y))
    tot_sac_fnf = 0.0
    tot_sj_fnf = 0.0
    proj_surplus = np.zeros(12)
    proj_omr = np.zeros(12)
    if m >= 10:
      wateryear = y - startYear
    else:
      wateryear = y - startYear - 1
    for reservoir in [self.shasta, self.oroville, self.yuba, self.folsom]:
      if t < 30:
        tot_sac_fnf += np.sum(reservoir.fnf[0:t])*30.0/(t+1)
      else:
        tot_sac_fnf += np.sum(reservoir.fnf[(t-30):t])
    for reservoir in [self.newmelones, self.donpedro, self.exchequer, self.millerton]:
      if t < 30:
        tot_sj_fnf += np.sum(reservoir.fnf[0:t])*30.0/(t+1)
      else:
        tot_sj_fnf += np.sum(reservoir.fnf[(t-30):t])

    for x in range(0, 12):
      proj_surplus[x] = max(self.delta_gains_regression['slope'][dowy][x]*min(tot_sac_fnf,4.0) + self.delta_gains_regression['intercept'][dowy][x], 0.0)
      proj_omr[x] = (self.delta.omr_regression['slope'][dowy][x]*tot_sj_fnf + self.delta.omr_regression['intercept'][dowy][x] + 5000.0*cfs_tafd*days_in_month[x])/0.94
	  
    expected_pumping = {}
    expected_pumping['cvp'] = np.zeros(12)
    expected_pumping['swp'] = np.zeros(12)
    max_pumping = {}
    max_pumping['cvp'] = np.zeros(12)
    max_pumping['swp'] = np.zeros(12)


    for monthloop in range(0,12):
      if proj_surplus[monthloop]*0.55 > self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop]:
        expected_pumping['cvp'][monthloop] = self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop]
        expected_pumping['swp'][monthloop] = min(self.delta.pump_max['swp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop], proj_surplus[monthloop] - self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop])
      else:
        expected_pumping['cvp'][monthloop] = proj_surplus[monthloop]*0.55
        expected_pumping['swp'][monthloop] = proj_surplus[monthloop]*0.45
		
      if monthloop < 6:
        if proj_omr[monthloop]*0.5 > self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop]:
          max_pumping['cvp'][monthloop] = self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop]
          max_pumping['swp'][monthloop] = min(self.delta.pump_max['swp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop], proj_omr[monthloop] - self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop])
        else:
          max_pumping['cvp'][monthloop] = proj_omr[monthloop]*0.5
          max_pumping['swp'][monthloop] = proj_omr[monthloop]*0.5
		  
      else:
        max_pumping['cvp'][monthloop] = self.delta.pump_max['cvp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop]
        max_pumping['swp'][monthloop] = self.delta.pump_max['swp']['intake_limit'][0]*cfs_tafd*days_in_month[monthloop]

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

