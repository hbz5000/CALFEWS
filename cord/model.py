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

  def __init__(self, datafile, sd='10-01-1996'):
    ##Set model dataset & index length
    self.df = pd.read_csv(datafile, index_col=0, parse_dates=True)
    self.index = self.df.index
    self.T = len(self.df)
	
	
#####################################################################################################################
#############################     Object Creation     ###############################################################
#####################################################################################################################

  def initialize_northern_res(self):
    #########################################################################################
	#reservoir initialization for the northern delta system
    #########################################################################################
    #4 Sacramento River Reservoirs (CVP & SWP)
    self.shasta = Reservoir(self.df, 'SHA')
    self.folsom = Reservoir(self.df, 'FOL')
    self.oroville = Reservoir(self.df, 'ORO')
    self.yuba = Reservoir(self.df,'YRS')
	
    #3 San Joaquin River Reservoirs (to meet Vernalis flow targets)
    self.newmelones = Reservoir(self.df,'NML')
    self.donpedro = Reservoir(self.df,'DNP')
    self.exchequer = Reservoir(self.df,'EXC')
	
    #Millerton Reservoir (flows used to calculate San Joaquin River index, not in northern simulation)
    self.millerton = Reservoir(self.df,'MIL')
	
    ##Regression flow & standard deviations read from file (see end of function for code to generate files)
    flow_estimates = pd.read_csv('cord/data/no_res_preprocess_daily.csv', index_col=0, parse_dates=True)
    std_estimates = pd.read_csv('cord/data/no_res_presprocess_annual.csv')
	#### Find regression information for all 8 reservoirs 
	### 5 sets of daily linear coefficients & standard devations at each reservoir - (2x2) FNF/INFLOWS x OCT-MAR/APR-JUL + (1) INFLOWS AUG-SEPT
    for x in [self.shasta, self.oroville, self.folsom, self.yuba, self.newmelones, self.donpedro, self.exchequer, self.millerton]:
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
    inflow_list = [self.shasta, self.folsom, self.yuba, self.oroville, self.newmelones, self.donpedro, self.exchequer]
    #df_flow_shape_no = pd.DataFrame()
    #for x in inflow_list:
      #x.create_flow_shapes()
      #df_flow_shape_no['%s_slope' % x.key] = pd.Series(x.flow_shape['slope'])
      #df_flow_shape_no['%s_intercept' % x.key] = pd.Series(x.flow_shape['intercept'])
    ##save flow shapes for the northern model
    #df_flow_shape_no.to_csv('cord/data/flow_shape_no.csv')
    flow_shape_files = pd.read_csv('cord/data/flow_shape_no.csv')
    for x in inflow_list:
      x.flow_shape = {}
      x.flow_shape['slope'] = flow_shape_files['%s_slope' % x.key]
      x.flow_shape['intercept'] = flow_shape_files['%s_intercept' % x.key]

	#######################################################################################
    ###Code used to find regression between YTD snow and flow projections - replaced with read from file for speed
	#######################################################################################
    #self.shasta.find_release_func()
    #self.oroville.find_release_func()
    #self.folsom.find_release_func()
    #self.yuba.find_release_func()
    #self.newmelones.find_release_func()
    #self.donpedro.find_release_func()
    #self.exchequer.find_release_func()
    #self.millerton.find_release_func()
    #df_res_process = pd.DataFrame()
    #df_res_annual = pd.DataFrame()
    #for x in [self.shasta, self.oroville, self.folsom, self.yuba, self.newmelones, self.donpedro, self.exchequer, self.millerton]:
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
    #df_res_process.to_csv('cord/data/no_res_preprocess_daily.csv')
    #df_res_annual.to_csv('cord/data/no_res_presprocess_annual.csv')
    #########################################################################################

  def initialize_delta_ops(self):
	#########################################################################################
    ##initialization of the delta rules
    #########################################################################################
    self.delta = Delta(self.df, 'DEL')
	###Find expected reservoir releases to meet delta requirements - used in flow forecasting
    ###these use the flow 'gains' on each tributary stretch to find the expected extra releases required to meet env & delta mins
	
    ##in addition to output variables, this generates:
	#self.max_tax_free (5x2x365) - using delta outflow min, calculate how much pumping can occur without paying any additional I/E 'tax' (b/c some inflow is already used for delta outflow requirements)
    expected_outflow_req, expected_depletion = self.delta.calc_expected_delta_outflow(self.shasta.downstream,self.oroville.downstream,self.yuba.downstream,self.folsom.downstream, self.shasta.temp_releases, self.oroville.temp_releases, self.yuba.temp_releases, self.folsom.temp_releases)
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
    inflow_list = [self.shasta, self.folsom, self.yuba, self.oroville, self.newmelones, self.donpedro, self.exchequer]
    for x in inflow_list:
      x.calc_expected_min_release(expected_outflow_req, expected_depletion, 0)

  def initialize_southern_res(self):
    ############################################################################
    ###Reservoir Initialization
	############################################################################
    self.millerton = Reservoir(self.df,'MIL')
    self.pineflat = Reservoir(self.df,'PFT')
    self.kaweah = Reservoir(self.df,'KWH')
    self.success = Reservoir(self.df,'SUC')
    self.isabella = Reservoir(self.df,'ISB')
    ###San Luis is initialized as a Reservoir, but
    ###has none of the watershed data that goes along with the other reservoirs
    self.sanluis = Reservoir(self.df,'SNL')
    self.sanluisstate = Reservoir(self.df, 'SLS')
    self.sanluisfederal = Reservoir(self.df, 'SLF')
    self.reservoir_list = [self.sanluisstate, self.sanluisfederal, self.millerton, self.isabella, self.success, self.kaweah]

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
    #df_flow_shape_so = pd.DataFrame()
    #for x in [self.millerton, self.sanluisstate, self.sanluisfederal, self.isabella, self.success, self.kaweah]:
      #x.create_flow_shapes()
      #df_flow_shape_so['%s_slope' % x.key] = pd.Series(x.flow_shape['slope'])
      #df_flow_shape_so['%s_intercept' % x.key] = pd.Series(x.flow_shape['intercept'])
    #save southern flow shapes to file
    #df_flow_shape_so.to_csv('cord/data/flow_shape_so.csv')
    flow_shape_files = pd.read_csv('cord/data/flow_shape_so.csv')
    for x in [self.millerton, self.sanluisstate, self.sanluisfederal, self.isabella, self.success, self.kaweah]:
      x.flow_shape = {}
      x.flow_shape['slope'] = flow_shape_files['%s_slope' % x.key]
      x.flow_shape['intercept'] = flow_shape_files['%s_intercept' % x.key]


    #Tulare Basin Reservoirs do not need to release to the delta, so they only use their own
    #environmental flow requirements when calculating expected environmental releases
	#arguements passed into the function here are equal to zero
    expected_outflow_releases = {}
    for wyt in ['W', 'AN', 'BN', 'D', 'C']:
      expected_outflow_releases[wyt] = np.zeros(366)
    for x in [self.millerton, self.pineflat, self.kaweah, self.success, self.isabella]:
      #generates:
      #x.cum_min_release (5 x 365) - daily values of remaining enviromental releases through the end of july, in each wyt
      #x.aug_sept_min_release (5 x 365) - daily values of remaining enviromental releases during the aug-sept period, in each wyt
      #x.oct_nov_min_release (5 x 365) - daily values of remaining enviromental releases during the oct-nov period, in each wyt
      x.calc_expected_min_release(expected_outflow_releases, np.zeros(12), 0)
      if x.key == "MIL":
        x.calc_expected_min_release(expected_outflow_releases, np.zeros(12), 1)
	  
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
    self.southbay.pumping = self.df['SOB_pump'].values
    self.centralcoast.pumping = self.df['LAP_pump'].values
    self.socal.pumping = self.df['EDM_pump'].values
    self.observed_hro = self.df['HRO_pump'].values*cfs_tafd

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
    self.annual_SWP = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
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
    self.canal_district['aec'] = [self.fkc, self.xvc, self.kerndelta, self.arvin, self.calaqueduct]
    self.canal_district['knr'] = [self.isabella, self.calloway, self.kerndelta, self.lerdo, self.xvc, self.fkc, self.kerncanal, self.gooseslough, self.bakersfield, self.berrendawb, self.b2800, self.pioneer, self.buenavista, self.calaqueduct]
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
    startYear = int(self.index.year[0])
    rainflood_sac_obs = 0.0
    snowflood_sac_obs = 0.0
    rainflood_sj_obs = 0.0
    snowflood_sj_obs = 0.0
    index_exceedence = 2
    reservoir_list = [self.shasta, self.folsom, self.oroville, self.yuba, self.newmelones, self.donpedro, self.exchequer, self.millerton]
    sac_list = [self.shasta, self.folsom, self.oroville, self.yuba]
    sj_list = [self.newmelones, self.donpedro, self.exchequer, self.millerton]
    for t in range(1,self.T):
      d = int(self.index.dayofyear[t-1])
      m = int(self.index.month[t-1])
      y = int(self.index.year[t-1])
      da = int(self.index.day[t-1])
      dowy = water_day(d,calendar.isleap(y))
      index_exceedence_sac = 9
      index_exceedence_sj = 5
	  ##8 River Index
      for x in reservoir_list:
        self.delta.eri[m-startMonth + (y - startYear)*12] + x.fnf[t-1]*1000
	  ####################Sacramento Index#############################################################################################
	  ##Individual Rainflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
      if m >=10:
        self.delta.forecastSJI[t-1] = lastYearSJI
        self.delta.forecastSRI[t-1] = lastYearSRI
      else:
        res_rain_forecast = 0.0
        for x in sac_list:
          res_rain_forecast += x.rainflood_fnf[t] + x.rainfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL RAIN
        sac_rain = max(rainflood_sac_obs, res_rain_forecast)
	    ##Individual Snowflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_snow_forecast = 0.0
        for x in sac_list:
          res_snow_forecast += x.snowflood_fnf[t] + x.snowfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL SNOW
        sac_snow = max(snowflood_sac_obs, res_snow_forecast)
	  #######################################################################################################################################
	  #####################San Joaquin Index################################################################################################
        ##Individual Rainflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_rain_forecast = 0.0
        for x in sj_list:
          res_rain_forecast += x.rainflood_fnf[t] + x.rainfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SJ TOTAL RAIN
        sj_rain = max(rainflood_sj_obs, res_rain_forecast)
	    ##Individual Snowflood Forecast - either the 90% exceedence level prediction, or the observed WYTD fnf value
        res_snow_forecast = 0.0
        for x in sj_list:
          res_snow_forecast += x.snowflood_fnf[t] + x.snowfnf_stds[dowy]*z_table_transform[index_exceedence_sac]
	    ##SAC TOTAL SNOW
        sj_snow = max(snowflood_sj_obs, res_snow_forecast)

      ###INDEX FORECASTS########################################################################################################################
        self.delta.forecastSJI[t-1] = min(lastYearSJI,4.5)*0.2 + sj_rain*0.2 + sj_snow*0.6
        self.delta.forecastSRI[t-1] = min(lastYearSRI,10)*0.3 + sac_rain*0.3 + sac_snow*0.4

      ##REAL-TIME OBSERVATIONS
      if m >= 10 or m <= 3:
        rainflood_sac_obs += self.shasta.fnf[t] + self.oroville.fnf[t] + self.folsom.fnf[t] + self.yuba.fnf[t]
        rainflood_sj_obs += self.newmelones.fnf[t] + self.donpedro.fnf[t] + self.exchequer.fnf[t] + self.millerton.fnf[t]
      else:
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

		
  def predict_delta_gains(self):
    ##this function uses a regression to find expected 'unstored' flows coming to the
    ##delta, to better project flow into San Luis
	##########################################################################################
    #Initialize gains matricies
	##Unstored flow will be regressed against total FNF expected in that year
    self.total_fnf = np.zeros((365,(self.index.year[self.T-1]-self.index.year[0] + 1)))
	
	##Total gains, year-to-day, in every year of the historical record (Oct-Mar)
    self.ytd_gains = np.zeros((365,(self.index.year[self.T-1]-self.index.year[0] + 1)))
	##Total gains, year-to-day, in every year of the historical record (Apr-Jul)
    self.ytd_gains2 = np.zeros((365,(self.index.year[self.T-1]-self.index.year[0] + 1)))
	##Total gains, annually (Oct-Mar)
    total_gains = np.zeros((self.index.year[self.T-1]-self.index.year[0] + 1))
	##Total gains, annually (Apr-Jul)
    total_gains2 = np.zeros((self.index.year[self.T-1]-self.index.year[0] + 1))
    ##Total gains in each month
    monthly_gains = np.zeros((12,(self.index.year[self.T-1]-self.index.year[0] + 1)))
    startYear = int(self.index.year[0])
    ##Linear regression coefficient to project gains to delta (Oct-Mar)
    self.delta_gains_regression = np.zeros((365,2))
    ##Linear regression coefficient to project gains to delta (Oct-Mar)
    self.delta_gains_regression2 = np.zeros((365,2))
    ##########################################################################################
    ##########################################################################################
    #Read flow from historical record
	##########################################################################################
    for t in range(1,self.T):
      ##Get date information
      d = int(self.index.dayofyear[t-1])
      y = int(self.index.year[t-1])
      dowy = water_day(d,calendar.isleap(y))
      m = int(self.index.month[t-1])
      da = int(self.index.day[t-1])
      if m >= 10:
        wateryear = y - startYear
      else:
        wateryear = y - startYear - 1
		
      #Calculate the total daily unstored gains to the delta
      this_day_gains = 0.0
      for x in [self.shasta, self.folsom, self.oroville, self.yuba]:
        self.total_fnf[dowy][wateryear] += x.fnf[t]#total full natural flow
        this_day_gains += max(x.downstream[t], 0.0)#unstored tributary flows
      #gains from sac delta area, sj delta area, eastside stream delta area (note: trib gains from sj reservoirs are not used in this calc)
      this_day_gains += max(self.delta.eastside_streams[t], 0.0) + max(self.delta.gains_sac[t], 0.0) + max(self.delta.gains_sj[t], 0.0)
	  
      ##Calculate the max daily 'unstored pumping'
      #'unstored pumping' is the minimum of three constraints on the 'gains' flows
      volume_constraint = this_day_gains - self.delta.min_outflow[self.delta.forecastSCWYT][m-1]*cfs_tafd#extra gains after delta outflow requirements
      flow_ratio_constraint = this_day_gains*self.delta.export_ratio[self.delta.forecastSCWYT][m-1]#portion of gains that can be exported 
      state_pumping = np.interp(da, self.delta.pump_max['swp']['d'], self.delta.pump_max['swp']['intake_limit'])#max state pumping
      fed_pumping = np.interp(da, self.delta.pump_max['cvp']['d'], self.delta.pump_max['cvp']['intake_limit'])#max fed pumping
      pumping_constraint = (state_pumping + fed_pumping) * cfs_tafd#max pumping
      ##Monthly
      monthly_gains[m-1][wateryear] += max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
      if m == 10 and da == 1:
      ##Annually
        total_gains[wateryear] += max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
      ##Daily YTD
        self.ytd_gains[dowy][wateryear] = max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
      elif m >= 10 or m <= 3:
      ##Annually
        total_gains[wateryear] += max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
      ##Daily YTD
        self.ytd_gains[dowy][wateryear] = max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0) + self.ytd_gains[dowy-1][wateryear]
      elif m == 6 and da == 1:
      ##Annually
        total_gains2[wateryear] += max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
      ##Daily YTD
        self.ytd_gains2[dowy][wateryear] = max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
      elif m >= 6 and m <= 9:
      ##Annually
        total_gains2[wateryear] += max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0)
      ##Daily YTD
        self.ytd_gains2[dowy][wateryear] = max(min(volume_constraint,flow_ratio_constraint, pumping_constraint), 0.0) +  self.ytd_gains2[dowy-1][wateryear]
    ##########################################################################################
    ##########################################################################################
    #Perform linear regression - FNF used for running prediction of total 'unstored' flow to delta in oct-mar; apr-jul period
	##########################################################################################
    for x in range(1,365): 
      ##YTD flow in each year at dowy number X
      one_year_fnf = self.total_fnf[x-1]
	  
      #regress for gains in oct-mar period and april-jul period
      if sum(one_year_fnf) == 0.0:
        coef[0] = 0.0
        coef[1] = np.mean(total_gains)
        coef2[0] = 0.0
        coef2[1] = np.mean(total_gains2)
      else:
        coef = np.polyfit(one_year_fnf,total_gains,1)###regression of cumulative flow through a day of the rain-flood season with total flow in that rain-flood season
        coef2 = np.polyfit(one_year_fnf,total_gains2,1)###regression of cumulative flow through a day of the rain-flood season with total flow in that rain-flood season

      self.delta_gains_regression[x-1][0] = coef[0]
      self.delta_gains_regression[x-1][1] = coef[1]
      self.delta_gains_regression2[x-1][0] = coef2[0]
      self.delta_gains_regression2[x-1][1] = coef2[1]
    ##########################################################################################
    ##########################################################################################
    #Find the percent of the total gains (for each of oct-mar/apr-jul periods) that occurs in each month (expectation)
	##########################################################################################
    self.month_averages = np.zeros(12)
    for month_count in range(0,12):
      for year_count in range(0,(self.index.year[self.T-1]-self.index.year[0])):
        if month_count >= 9 or month_count <= 2:
          if total_gains[year_count] > 0.0:
            self.month_averages[month_count] += (monthly_gains[month_count][year_count]/total_gains[year_count])/(self.index.year[self.T-1]-self.index.year[0] + 1)
        else:
          if total_gains2[year_count] > 0.0:
            self.month_averages[month_count] += (monthly_gains[month_count][year_count]/total_gains2[year_count])/(self.index.year[self.T-1]-self.index.year[0] + 1)

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
      y.tot_carryover = 0.0

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

  def project_urban(self):
    #########################################################################################
    ###initializes variables needed for district objects that are pumping plants on branches
	###of the california aqueduct (southern california, central coast, and the south bay)
    #########################################################################################

    ##This function finds linear regression coefficients between urban CA AQ branch pumpning and delta pumping
	##to predict water use in southbay, centralcoast, and socal district objects
	##NOTE!!! We don't actually use the calculated linear regressions
	##regression coefficients - the correlation breaks down at higher pumping levels so we have a 'stopgap'
	##linear relationship that is hand-picked and hard-coded into the data.  Need a better model of urban demands
	##might be as simple as a linear relationship w/ a cap (most of the non-linear relationships here are from 
	##high allocation years w/socal -they just can't take their full allocation in wet years, when their local supplies are
	##also presumably full.  Also - they've made structural changes over the 1996-2016 period, so its unlikely that this
	##data represents a stationary relationship.  More detailed MWD/Southern Cal demand data would improve the model
    startYear = int(self.index.year[0])
	##Finds regressions to predict urban CA AQ branch pumping based on SWP allocations
    self.hro_annual = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    self.hro_modeled = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    self.southbay.annual_pumping = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    self.centralcoast.annual_pumping = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    self.socal.annual_pumping = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    self.southbay.ytd_pumping = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    self.centralcoast.ytd_pumping = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    self.socal.ytd_pumping = np.zeros((self.index.year[self.T-1]-self.index.year[0]))

    for t in range(1,(self.T)):
      m = int(self.index.month[t-1])
      y = int(self.index.year[t-1])
      if m >= 10:
        wateryear = y - startYear
      else:
        wateryear = y - startYear - 1  
	  
	  ##Find annual pumping at each branch (and @ delta)
      self.hro_annual[wateryear] += self.observed_hro[t-1]
      self.southbay.annual_pumping[wateryear] += self.southbay.pumping[t-1]/1000.0
      self.centralcoast.annual_pumping[wateryear] += self.centralcoast.pumping[t-1]/1000.0
      self.socal.annual_pumping[wateryear] += self.socal.pumping[t-1]/1000.0

    ##regression between pumping at delta and pumping on branches
    self.southbay.urb_coef = np.polyfit(self.hro_annual,self.southbay.annual_pumping,1)###regression of cumulative flow through a day of the rain-flood season with total flow in that rain-flood season
    self.centralcoast.urb_coef = np.polyfit(self.hro_annual, self.centralcoast.annual_pumping,1)###regression of cumulative flow through a day of the rain-flood season with total flow in that rain-flood season
    self.socal.urb_coef = np.polyfit(self.hro_annual, self.socal.annual_pumping,1)###regression of cumulative flow through a day of the rain-flood season with total flow in that rain-flood season
    self.socal.regression = np.zeros(len(self.socal.annual_pumping))
    self.centralcoast.regression = np.zeros(len(self.centralcoast.annual_pumping))
    self.southbay.regression = np.zeros(len(self.southbay.annual_pumping))
	
	###ACTUAL regression coefficients - picked to pass the 'eye test' 
    self.southbay.urb_coef[0] = 0.01
    self.centralcoast.urb_coef[0] = 0.0
    self.socal.urb_coef[0] = 0.5
    self.southbay.urb_coef[1] = 104.0
    self.centralcoast.urb_coef[1] = 110.0
    self.socal.urb_coef[1] = 200.0
	
    #for x in range(0,len(self.socal.regression)):
      #self.socal.regression[x] = self.socal.urb_coef[0]*self.hro_annual[x] + self.socal.urb_coef[1]
      #self.centralcoast.regression[x] = self.centralcoast.urb_coef[0]*self.hro_annual[x]  + self.centralcoast.urb_coef[1]
      #self.southbay.regression[x] = self.southbay.urb_coef[0]*self.hro_annual[x] + self.southbay.urb_coef[1]
    #fig = plt.figure()
    #ax1 = fig.add_subplot(2,2,1, axisbg = "1.0")
    #ax2 = fig.add_subplot(2,2,2, axisbg = "1.0")
    #ax3 = fig.add_subplot(2,2,3, axisbg = "1.0")
    #ax1.scatter(self.hro_annual,self.socal.annual_pumping, alpha = 0.8, c = 'red', edgecolors = 'black', s = 30)
    #ax1.scatter(self.hro_annual,self.socal.regression, alpha = 0.8, c = 'blue', edgecolors = 'black', s = 30)
    #ax2.scatter(self.hro_annual,self.centralcoast.annual_pumping, alpha = 0.8, c = 'red', edgecolors = 'black', s = 30)
    #ax2.scatter(self.hro_annual,self.centralcoast.regression, alpha = 0.8, c = 'blue', edgecolors = 'black', s = 30)
    #ax3.scatter(self.hro_annual,self.southbay.annual_pumping, alpha = 0.8, c = 'red', edgecolors = 'black', s = 30)
    #ax3.scatter(self.hro_annual,self.southbay.regression, alpha = 0.8, c = 'blue', edgecolors = 'black', s = 30)

    #plt.show()	
	
  #def results_as_df(self):
    #df = pd.DataFrame(index=self.df.index)
    #for x in [self.shasta, self.folsom, self.oroville, self.yuba, self.newmelones, self.donpedro, self.exchequer, self.delta]:
      #df = pd.concat([df, x.results_as_df(df.index)], axis=1)
    #return df
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
    d = self.index.dayofyear[t]
    m = int(self.index.month[t])
    y = int(self.index.year[t])
    dowy = water_day(d,calendar.isleap(y))
    print(y, end = " ")
    print(m, end = " ")
    print(dowy)
	  
    ##WATER YEAR TYPE CLASSIFICATION (for operating rules)
    ##WYT uses flow forecasts - gets set every day, may want to decrease frequency (i.e. every month, season)
    NMI = self.calc_wytypes(t,dowy)#NMI (new melones index) - used as input for vernalis control rules
	  
	##REAL-WORLD RULE ADJUSTMENTS
	##Updates to reflect SJRR & Yuba Accords occuring during historical time period (1996-2016)
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
    #share rio vista requirements among Sacramento Reservoirs based on self.resevoir.availale_storage
    self.shasta.release_frac, self.folsom.release_frac, self.oroville.release_frac, self.yuba.release_frac = self.delta.assign_releases(self.shasta.available_storage[t],self.folsom.available_storage[t], self.oroville.available_storage[t], self.yuba.available_storage[t],self.shasta.S[t]-self.shasta.dead_pool, 0.0,self.oroville.S[t]-self.oroville.dead_pool,0.0)	  
    #unstored flow at rio vista comes from tributary gains, environmental releases and sacramento river gains
    self.delta.rio_gains = self.delta.gains_sac[t]
    for x in [self.shasta, self.oroville, self.yuba, self.folsom]:
      self.delta.rio_gains += x.gains_to_delta + x.envmin
    #additional releases to meet rio vista minimums shared by Sacramento Reservoirs
    rio_release = self.delta.calc_rio_vista_rule(t)
    for x in [self.shasta, self.oroville, self.yuba, self.folsom]:
      x.din = x.release_frac*rio_release
    self.delta.rio_gains += rio_release

    ##MINIMUM DELTA OUTFLOW REQUIREMENTS
    #flows to delta come from vernalis, rio vista, and the 'eastside streams' (delta gains)
    self.delta.total_inflow = self.delta.eastside_streams[t] + self.delta.rio_gains + self.delta.vernalis_gains
    cvp_stored_release = self.shasta.envmin + self.folsom.envmin + self.shasta.din + self.folsom.din
    swp_stored_release = self.oroville.envmin + self.yuba.envmin + self.oroville.din + self.yuba.din
	##additional releases for delta outflow split between cvp/swp reservoirs
    self.shasta.dout, self.oroville.dout = self.delta.calc_outflow_release(t, cvp_stored_release, swp_stored_release)
    #for x in [self.shasta, self.oroville, self.yuba, self.folsom]:
      #x.dout = x.release_frac*(cvp_dout + swp_dout)
  
	#TOTAL AVAILABLE PROJECT STORAGE
	#based on snowpack based forecast (pre-processed) + current storage
    cvp_available_storage = max(self.folsom.available_storage[t],0.0) + max(self.shasta.available_storage[t],0.0)
    swp_available_storage = max(self.oroville.available_storage[t],0.0) + max(self.yuba.available_storage[t],0.0)
    #existing storage calculation to determine how much 'tax free' pumping to use
    if dowy > 90:
      self.delta.cvp_existing_storage = cvp_available_storage
      self.delta.swp_existing_storage = max(self.oroville.S[t] -1000.0 - self.oroville.aug_sept_min_release[self.oroville.forecastWYT][dowy] + self.oroville.baseline_forecast[t], 0.0)
    else:
      self.delta.cvp_existing_storage = cvp_available_storage
      self.delta.swp_existing_storage = max(self.oroville.S[t] - 1000.0 - self.oroville.oct_nov_min_release[self.oroville.forecastWYT][dowy], 0.0)

	
    #project if flood pool will be exceeded in the future & find min release rate to avoid reaching the flood pool
	#monthly flow projections from self.reservoir.create_flow_shapes (i.e. flood available water)
    for x in [self.shasta, self.folsom, self.oroville, self.yuba]:
      x.find_flow_pumping(t, m, dowy, self.delta.forecastSCWYT, 'env')
	  
    ##combining flood available water by project
    self.delta.available_flood_cvp = self.shasta.uncontrolled_available + self.folsom.uncontrolled_available
    self.delta.available_flood_swp = self.oroville.uncontrolled_available + self.yuba.uncontrolled_available
	
	###DETERMINE RELEASES REQUIRED FOR DESIRED PUMPING
    ###Uses gains and environmental releases to determine additional releases required for
	###pumping (if desired), given inflow/export requirements, pump constraints, and CVP/SWP sharing of unstored flows
	#at-the-pump limits (from BiOps)
    cvp_max, swp_max = self.delta.find_max_pumping(d, dowy, t, self.delta.forecastSCWYT)
    #OMR rule limits
    cvp_max, swp_max = self.delta.meet_OMR_requirement(cvp_max, swp_max, t)
	##Distribute 'available storage' seasonally to maximize pumping under E/I ratio requirements (i.e., pump when E/I ratio is highest)
    cvp_max_final, swp_max_final = self.delta.find_release(t, dowy, cvp_max, swp_max, cvp_available_storage, swp_available_storage)

    #if pumping is turned 'off' (b/c SL conditions), calculate how much forgone pumping to take away from SL carryover storage (southern model input)
    cvp_forgone, cvp_max_final = self.delta.hypothetical_pumping(cvp_max, cvp_max_final, cvp_release, 0.55, t)
    swp_forgone, swp_max_final = self.delta.hypothetical_pumping(swp_max, swp_max_final, swp_release, 0.45, t)
     
    #find additional releases to pump at the desired levels
    cvp_max = min(cvp_max, cvp_pump)#don't release 'tax free' pumping in excess of storage capacity at SL
    swp_max = min(swp_max, swp_pump)#don't release 'tax free' pumping in excess of storage capacity at SL
    self.delta.calc_flow_bounds(t, cvp_max_final, swp_max_final,cvp_max, swp_max, cvp_release2, swp_release2, cvp_available_storage,swp_available_storage)
	
    self.folsom.min_daily_uncontrolled = 0.0
    self.yuba.min_daily_uncontrolled = 0.0
    #distribute releases for export between Sacramento River Reservoirs
    self.shasta.sodd, self.folsom.sodd = self.delta.distribute_export_releases(t, cvp_max, self.delta.sodd_cvp[t], self.shasta.min_daily_uncontrolled, self.folsom.min_daily_uncontrolled, self.shasta.available_storage[t], self.folsom.available_storage[t])
    self.oroville.sodd, self.yuba.sodd = self.delta.distribute_export_releases(t, swp_max, self.delta.sodd_swp[t], self.oroville.min_daily_uncontrolled, self.yuba.min_daily_uncontrolled, self.oroville.available_storage[t], self.yuba.available_storage[t])
    if self.shasta.sodd > self.shasta.S[t] - self.shasta.dead_pool:
      self.shasta.sodd = 0.0
    if self.oroville.sodd > self.oroville.S[t] - self.oroville.dead_pool:	  
      self.oroville.sodd = 0.0

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
    self.delta.step(t, cvp_stored_flow, swp_stored_flow, swp_pump, cvp_pump, swp_release, cvp_release, swp_available_storage, cvp_available_storage)
    proj_surplus, proj_surplus2 = self.proj_gains(t)
	
    #calculate pumping that did not occur that otherwise would have because of SL storage conditoins
    cvp_forgone = max(cvp_forgone - self.delta.TRP_pump[t], 0.0)
    swp_forgone = max(swp_forgone - self.delta.HRO_pump[t], 0.0)
		    
    return self.delta.HRO_pump[t], self.delta.TRP_pump[t], self.delta.swp_allocation[t], self.delta.cvp_allocation[t], proj_surplus, proj_surplus2, swp_forgone, cvp_forgone, self.delta.available_flood_swp, self.delta.available_flood_cvp
	
	
			
  def simulate_south(self, t, hro_pump, trp_pump, swp_alloc, cvp_alloc, proj_surplus, proj_surplus2, swp_forgone, cvp_forgone, swp_AF, cvp_AF, wyt):
    ####Maintain the same date/time accounting as the northern part of the model
    startYear = int(self.index.year[0])
    d = self.index.dayofyear[t]
    current_year = int(self.index.year[t])
    dowy = water_day(d,calendar.isleap(current_year))
    dowy_md = [122, 150, 181, 211, 242, 272, 303, 334, 365, 30, 60, 91]
    m = int(self.index.month[t])
    if m >= 10:
      wateryear = current_year - startYear
    else:
      wateryear = current_year - startYear - 1  
    da = int(self.index.day[t])
    if m == 12:
      m1 = 1
    else:
      m1 = m + 1

    #####Pumping and project allocations (projections of future pumping) are passed 
	#####Into the southern model from the delta calcs in the northern model
    self.trp_pumping[t] = trp_pump
    self.hro_pumping[t] = hro_pump
    self.cvp_allocation[t] = cvp_alloc
    self.swp_allocation[t] = swp_alloc
	
	####Various infrastructure & regulatory changes that 
	####occurred during the duration of the 1996-2016 calibration period
    self.update_regulations_south(t,dowy,m,current_year)
	  
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
    extra_s, extra_f = self.step_san_luis(t, m, da)
	
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
    for x in self.urban_list:
      x.get_urban_demand(t, m, da, wateryear)
	  
    if m == 10 and da == 1:      
      self.annual_SWP[wateryear] += sum(self.observed_hro[(t):(t+364)])
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


	
    ##Get Article 21 water from San Luis
    flow_type = "recharge"
    overflow_deliveries = 0#no flood deliveries to non-contractors in swp or cvp
	#for san luis - need to know if we can use the xvc from california aquduct - check for turnout to xvc from kern river and fkc
    #self.calaqueduct.flow_directions['recharge']['xvc'] = self.find_bi_directional(self.fkc.turnout_use[22] > 0.0 or self.kernriverchannel.turnout_use[4] > 0.0, "normal")
    ###find flood releases for the SWP at san luis (self.sanluisstate.min_daily_uncontrolled) - also find release toggles (for northern reservoir pumping coordination w/ san luis) and numdays_fillup for SWP district recharge decisions
    swp_release, swp_release2, self.sanluisstate.min_daily_uncontrolled, self.sanluisstate.numdays_fillup['demand'] = self.find_pumping_release(self.sanluisstate.S[t+1], 6680.0*cfs_tafd, self.sanluisstate.monthly_demand, self.sanluisstate.monthly_demand_must_fill, self.swpdelta.allocation[t-1]/self.swpdelta.total, 0.45*proj_surplus, 0.45*proj_surplus2, swp_AF, self.swpdelta.projected_carryover, self.swpdelta.tot_carryover, wyt, t, 'swp')
    #article21 releases from san luis - state
    self.canal_contract['caa'] = [self.swpdelta]#for swp flood releases, only swp contracts are considered
	
    self.set_canal_direction(flow_type)   
    self.flood_operations(t, dowy, wateryear, self.sanluisstate, flow_type, overflow_deliveries)	  
	
    ###find flood releases for the CVP at san luis (self.sanluisfederal.min_daily_uncontrolled) - also find release toggles (for northern reservoir pumping coordination w/ san luis) and numdays_fillup for SWP district recharge decisions
    cvp_release, cvp_release2, self.sanluisfederal.min_daily_uncontrolled, self.sanluisfederal.numdays_fillup['demand'] = self.find_pumping_release(self.sanluisfederal.S[t+1], 4430.0*cfs_tafd, self.sanluisfederal.monthly_demand, self.sanluisfederal.monthly_demand_must_fill, (self.cvpdelta.allocation[t-1] + self.cvpexchange.allocation[t-1])/(self.cvpexchange.total+self.cvpdelta.total), 0.55*proj_surplus, 0.55*proj_surplus2, cvp_AF, self.cvpdelta.projected_carryover, self.cvpdelta.tot_carryover, wyt, t, 'cvp')
    #flood releases from san luis - federal
    self.canal_contract['caa'] = [self.cvpdelta, self.cvpexchange, self.crossvalley]

    self.set_canal_direction(flow_type)
    self.flood_operations(t, dowy, wateryear, self.sanluisfederal, flow_type, overflow_deliveries)	  
    self.set_canal_direction(flow_type)

    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]#reset california aqueduct contracts to be all san luis contracts

    ##Flood Deliveries - 4 flood sources - Millerton, Isabella, Success, and Kaweah
    ####This function finds the expected # of days that a reservoir will fill
	####districts use this numdays_fillup attribute to determine when to recharge
	####carryover water
    for reservoir in [self.millerton, self.isabella, self.kaweah, self.success]:
      reservoir.find_flow_pumping(t, m, dowy, wyt, 'demand')
    ##What is the priority for reservoirs getting to use the canals to route flood releases?
	##Note: most of the contracts have provisions that flood flows 'cannot displace' scheduled 
    ##deliveries (i.e. you can't use flood releases to fill demand that would be met by your contract
	##schedule), so might want to put this AFTER regular delivery routing
    flood_order_list = [self.millerton, self.isabella, self.success, self.kaweah]
    #toggle to enable flood releases to go to districts/banks that don't have a contract w/the reservoir
    #only san luis restricts flood releases to contractors only (b/c otherwise they just dont pump)
    overflow_deliveries = 1
    for a in flood_order_list:
      #if flow is already on a bi-directional canal, it becomes closed to canals going the other direction
	  #checks the calaqueduct turnout to xvc is used, if not, xvc is open to fkc and kern river
      self.set_canal_direction(flow_type)

      #self.fkc.flow_directions['recharge']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
      #self.kernriverchannel.flow_directions['recharge']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
      #release flood flows to canals
      self.flood_operations(t, dowy, wateryear, a, flow_type, overflow_deliveries)
	  


            			                		  		
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
      priority_allocation = 0.0
      secondary_allocation = 0.0
      for yy in self.get_iterable(this_reservoir_all_contract):
        total_res_deliveries += yy.annual_deliveries[wateryear]
        total_res_carryover += yy.tot_carryover
        if yy.allocation_priority == 1:
          priority_allocation += yy.total
        else:
          secondary_allocation += yy.total
      #san luis doesn't have available_storage forecasts, so input from northern model is used
	  #for state & federal portions
      if reservoir.key == "SLS":
        total_allocation = self.swp_allocation[t] - self.pumping_turnback['SLS'] + y.tot_new_alloc
      elif reservoir.key == "SLF":
        total_allocation = self.cvp_allocation[t] - self.pumping_turnback['SLF'] + y.tot_new_alloc
      else:
        #otherwise, total allocation at the reservoir is equal to available storage + deliveries - the total carryover storage
        total_allocation = reservoir.available_storage[t] + total_res_deliveries - total_res_carryover
		
      y.calc_allocation(t, dowy, total_allocation, priority_allocation, secondary_allocation, wyt)

	
    ##Find contract 'storage pools' - how much water is available right now	
	##san luis federal storage is divided between 3 water contracts - cvpdelta, exchange, and crossvalley
	##millerton storage is divided between 2 water contracts - friant1 and friant2
    for y in self.contract_list:
      #for a specific contract, look up the reservoir it is stored in
      reservoir = self.contract_reservoir[y.key]
      #then find all the contracts associated with that reservoir
      this_reservoir_all_contract = self.reservoir_contract[reservoir.key]
      total_res_deliveries = 0.0
      priority_storage = 0.0
      for yy in self.get_iterable(this_reservoir_all_contract):
        #find the total deliveries made from this reservoir, ytd
        total_res_deliveries += yy.annual_deliveries[wateryear]
        #if some contracts at a reservoir have 'priority' over storage space
		#(i.e., cvpdelta and exchange contracts have priority over the federal
		#san luis storage), calculate the total allocation volume that has priority
		#in a reservoir
        if yy.storage_priority == 1:
          priority_storage += yy.allocation[t] + yy.tot_carryover
      ##contract storage pools are the existing storage plus all the deliveries
      ##that have been made so far in that water year - so 'storage pool' is all
      ##the contract water that has already come into the reservoir, even water
      ##that has already been delivered	  
      total_water = reservoir.S[t] + total_res_deliveries
      #find the storage pool for each contract
      y.find_storage_pool(t, wateryear, total_water, reservoir.S[t], priority_storage)


    #estimate annual demand for urban cal aqueduct branches
    for x in self.urban_list:
      if dowy < 150 and current_year > 2000:
        x.annualdemand = x.annual_pumping[wateryear] - x.ytd_pumping[wateryear]

	##Update District Contracts
    #self.assign_uncontrolled(t, wateryear)
    for y in self.contract_list:
      y.projected_carryover = 0.0
    #for each contract in each district, what is the district's share of (i) currently available (surface water) storage and (ii) expected remaining allocation
    for x in self.district_list:
      for y in self.contract_list:
        y.projected_carryover += x.update_balance(t, wateryear, y.storage_pool[t], y.allocation[t], y.available_water[t], y.name, y.tot_carryover, y.type)
      ##summation of all projected contracts for each water district (total surface water expected)
    counter = 0
    #find the 'in leiu' recovery capacity at each in-leiu recharge district using this day's irrigation demand
	#recovery is based on the surface water allocations for the in-leiu bank (i.e., the surface water that they give their banking partners
	#when the partners want to recover banked water
    self.update_leiu_capacity()
	
    for x in self.district_list:
      #district can request recovery of their banked water
      x.open_recovery(dowy)
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
    
	#recover banked groundwater
    #only looking at GW exchanges for a few contracts
    self.canal_contract['caa'] = [self.swpdelta]#reset california aqueduct contracts to be all san luis contracts
    self.canal_contract['fkc'] = [self.friant1]#reset california aqueduct contracts to be all san luis contracts
    for z in [self.calaqueduct, self.fkc, self.kernriverchannel]:
      for y in self.canal_contract[z.name]:
        exchange_contract = y.name
        delivery_key = exchange_contract + "_banked"
        self.set_canal_direction(flow_type)
		
        #self.fkc.flow_directions['recovery']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
        #self.kernriverchannel.flow_directions['recovery']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
        #self.calaqueduct.flow_directions['recovery']['xvc'] = self.find_bi_directional(self.fkc.turnout_use[22] > 0.0 or self.kernriverchannel.turnout_use[4], "reverse")
        canal_size = len(self.canal_district[z.name])
        total_canal_demand = self.search_canal_demand(dowy,z, "none", z.name, 'normal', flow_type, wateryear, 'recovery')
        #self.route_recovery(z, exchange_contract, "normal", flow_type, "none", delivery_key, wateryear,dowy)
		
    self.canal_contract['caa'] = [self.swpdelta, self.cvpdelta, self.cvpexchange, self.crossvalley]#reset california aqueduct contracts to be all san luis contracts
    self.canal_contract['fkc'] = [self.friant1, self.friant2]#reset california aqueduct contracts to be all san luis contracts
		
    for x in self.district_list:
      for y in x.contract_list:
        contract_object = self.contract_keys[y]
        reservoir = self.contract_reservoir[contract_object.key]
        x.open_recharge(m-1, da, wateryear, reservoir.numdays_fillup['demand'], y, wyt)
	##Direct deliveries from surface water sources
    flow_type = "recharge"
    for a in [self.sanluis, self.isabella, self.millerton, self.success, self.kaweah]:
      for z in self.reservoir_canal[a.key]:
        self.set_canal_direction(flow_type)

        #self.fkc.flow_directions['recharge']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
        #self.kernriverchannel.flow_directions['recharge']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
        #self.calaqueduct.flow_directions['recovery']['xvc'] = self.find_bi_directional(self.fkc.turnout_use[22] > 0.0 or self.kernriverchannel.turnout_use[4], "reverse")

        canal_size = len(self.canal_district[z.name])
        total_canal_demand = self.search_canal_demand(dowy, z, a.key, z.name, 'normal', flow_type, wateryear,'delivery')
        available_flow = 0.0
        for zz in total_canal_demand:
          available_flow += total_canal_demand[zz]
        excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, z, a.key, z.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'delivery')

        #total_canal_demand = self.find_contract_demand(t, dowy, wateryear, z, a.key, z.name, 'normal',flow_type)
        #excess_water, unmet_demand = self.deliver_contracts(t, dowy, z, a.key, z.name, total_canal_demand, canal_size, wateryear, 'normal',flow_type)
		
    self.set_canal_direction(flow_type)
	##Deliveries for banking
    flow_type = "recharge"
    for a in [self.sanluis, self.isabella, self.millerton, self.success, self.kaweah]:
      for z in self.reservoir_canal[a.key]:
        self.set_canal_direction(flow_type)

        #self.fkc.flow_directions['recovery']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
        #self.kernriverchannel.flow_directions['recovery']['xvc'] = self.find_bi_directional(self.calaqueduct.turnout_use[15] > 0.0, "reverse")
        #self.calaqueduct.flow_directions['recovery']['xvc'] = self.find_bi_directional(self.fkc.turnout_use[22] > 0.0 or self.kernriverchannel.turnout_use[4], "reverse")

        canal_size = len(self.canal_district[z.name])
        total_canal_demand = self.search_canal_demand(dowy, z, a.key, z.name, 'normal',flow_type,wateryear,'banking')
        available_flow = 0.0
        for zz in total_canal_demand:
          available_flow += total_canal_demand[zz]

        excess_water, unmet_demand = self.distribute_canal_deliveries(dowy, z, a.key, z.name, available_flow, canal_size, wateryear, 'normal', flow_type, 'banking')
		
    self.set_canal_direction(flow_type)

        #priority_canal_banked, secondary_canal_banked  = self.find_contract_banked(z, a.key, z.name, 'normal',flow_type)
        #excess_water_banked, unmet_priority, unmet_secondary = self.deliver_banked(z, a.key, z.name, priority_canal_banked + secondary_canal_banked, canal_size, wateryear, 'normal',flow_type)
		
    #swp/cvp_pump - find maximum pumping levels based on space in san luis(inputs for the northern model)
	#swp/cvp_release -  toggle for 'max pumping' releases, based on space in san luis (inputs for the northern model)
    swp_pump, cvp_pump, swp_release, cvp_release = self.find_san_luis_space(t, swp_release, cvp_release, 6680.0*cfs_tafd, 4430.0*cfs_tafd)
	
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
            new_alloc, carryover = x.calc_carryover(y.storage_pool[t] - lastYearCarryover, wateryear, y.type, y.name)
            y.tot_new_alloc += new_alloc
            y.tot_carryover += carryover
	  
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
	
  def find_san_luis_space(self, t, swp_release, cvp_release, swp_pump_max, cvp_pump_max):
    #if there is no additional storage in san luis, send toggle variable to the northern model to turn 'off'
	#pumping at teh delta (so no wasted pumping if there is no room in san luis)
    if self.sanluisstate.S[t+1] + swp_pump_max > 1020.0:
      swp_release = 0
    if self.sanluisfederal.S[t+1] + cvp_pump_max >	1020.0:
      cvp_release = 0	
    if swp_release == 0 and cvp_release == 1:
      swp_pump = max(2042.0 - (self.sanluisfederal.S[t+1] + self.sanluisstate.S[t+1]), 0.0)
      cvp_pump = 999.0
    elif cvp_release == 0 and swp_release == 1:
      cvp_pump = max(2042.0 - (self.sanluisfederal.S[t+1] + self.sanluisstate.S[t+1]), 0.0)
      swp_pump = 999.0
    elif swp_release == 0 and cvp_release == 0:
      swp_pump = max(1021.0 - self.sanluisstate.S[t+1], 0.0)
      cvp_pump = max(1021.0 - self.sanluisfederal.S[t+1], 0.0)
    else:
      swp_pump = 999.0
      cvp_pump = 999.0
	  
    return swp_pump, cvp_pump, swp_release, cvp_release
	

  def find_pumping_release(self, start_storage, pump_max, month_demand, month_demand_must_fill, allocation, proj_surplus, proj_surplus2, flood_supply, projected_carryover, current_carryover, wyt, t, key):
   ##this function is used by the swpdelta & cvpdelta contracts to manage san luis reservoir storage
	##and coordinate pumping at the delta
    ##state and federal storage portions managed seperately
    d = int(self.index.dayofyear[t-1])
    m = int(self.index.month[t-1])
    y = int(self.index.year[t-1])
    da = int(self.index.day[t-1])
    dowy = water_day(d,calendar.isleap(y))
   
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    dowy_eom = [123, 150, 181, 211, 242, 272, 303, 333, 364, 30, 60, 91] 
    month_evaluate = m - 1
    first_month_frac = max(days_in_month[month_evaluate] - da, 0.0)/days_in_month[month_evaluate]
	
	
	###Initial storage projections - current month
	##calculate expected deliveries during this month from san luis
    expected_demands = (month_demand[wyt][month_evaluate]*allocation + month_demand_must_fill[wyt][month_evaluate])/days_in_month[month_evaluate]
    
	#how much 'unstored' pumping can we expect into San Luis?
    #self.month_averages comes from self.predict_delta_gains
	#proj_surplus & proj_surplus2 are generated in the northern model, from 8RI regression in self.predict_delta_gains
    if month_evaluate >=9 or month_evaluate <= 2:
      projected_month_gains = self.month_averages[month_evaluate]*proj_surplus/days_in_month[month_evaluate]
    else:
      projected_month_gains = self.month_averages[month_evaluate]*proj_surplus2/days_in_month[month_evaluate]
	  
    #expected monthly change in san luis storage
    net_monthly = (projected_month_gains - expected_demands)*max(days_in_month[month_evaluate] - da, 0.0)
    #favorable E/I conditions for pumping in July-January
	#but starting in 2007, OMR rules go into effect in January,
	#so only max pumping period through December
    if y == 2007 and m >= 6:
      end_pumping = 11
    elif y > 2007:
      end_pumping = 11
    else:
      end_pumping = 0
	  
    #find the max amount of pumping that can occur during
    #the season with favorable E/I conditions	
    if month_evaluate >= 6 or month_evaluate == end_pumping:
      net_pumping = (pump_max - projected_month_gains)*max(days_in_month[month_evaluate] - da, 0.0)
    else:
      net_pumping = 0.0
	  
    #there is an ability to pump from June - March (April & May the pumps are shut down)
    if month_evaluate >= 5 or month_evaluate <= 2:
      available_pumping = (pump_max-projected_month_gains)*max(days_in_month[month_evaluate] - da, 0.0)
	  
    ##Enter into a loop for projecting storage & pumping forward one month at a time
	##start with current estimates
    next_month_storage = start_storage#running storage levels
    this_month_days = max(days_in_month[month_evaluate] - da, 0.0)#running days in a month
    article21 = 0.0#initialize article 21 release estimates
    numdays_fillup = 999.9#initialize numdays_fillup variable
    total_days_remaining = 0.0#used for estimates of how long san luis will take to fill up (for districts to make carryover decisions)

    if m >=6 and m < 10:
      #during june - sept, only pump if water is needed 
      pumping_toggle = 0#toggle for releasing water to maximum pumping levels
      tax_free_toggle = 0#toggle for releasing water to 'tax free' pumping levels
    else:
      #during oct-may, pump unless san luis is full
      pumping_toggle = 1#toggle for releasing water to maximum pumping levels
      tax_free_toggle = 1#toggle for releasing water to 'tax free' pumping levels
	  
    ##loop through all months until april (april/may have very limited pumping, should not plan for any pumping to occur then)
	##this loop helps to project storage in san luis up to a year out > so we know in advance if we need to pump or will be filling the reservoir
	##note: this loop will go through one water year and into the next one
    while month_evaluate >= 5 or month_evaluate < 3:
      #estimate storage at the end of this month by adding monthly change to the running storage tally
      next_month_storage += net_monthly
      
	  ##can we reach the storage targets only using 'tax free' pumping?
      ##how much water can we expect to pump w/o additional E/I tax through the end of the month?
      if dowy <= dowy_eom[month_evaluate]:#running water year is the same as the beginning of the loop
        #how much 'tax free' pumping through the end of this month? - total tax free remaining at the current simulation day, minus total tax free remaining at the end of the looped month
        running_tax_free_pumping = self.max_tax_free[wyt][key][dowy] - self.max_tax_free[wyt][key][dowy_eom[month_evaluate]]
      else:#looped into the next water year, so we have to calculate the tax free pumping remaining through the end of the current year, then add in the tax free remaining through the looped month in the next year
        running_tax_free_pumping = self.max_tax_free[wyt][key][dowy] + self.max_tax_free[wyt][key][0] - self.max_tax_free[wyt][key][dowy_eom[month_evaluate]]
      #running_tax_free_pumping will be added to the net_month storage variable, so we don't want to double-count 'unstored pumping'
      if running_tax_free_pumping > available_pumping:
        running_tax_free_pumping = available_pumping
	  ##note - beginning month = m; looped month = month_evaluate
      if m >=6 and m < 10:#if the loop starts between june and september
        if start_storage > 1020.0:
          #if san luis storage is currently greater than capacity, no pumping, article21 releases triggered
          pumping_toggle = max(0, pumping_toggle)
          tax_free_toggle = max(0, tax_free_toggle)
          article21 = max(start_storage - 1020.0, 0.0)
          numdays_fillup = 0.0#if this condition is hit, no more days needed to fill reservoir (already full)
        elif next_month_storage < 0.0:
          #if expected storage is less than 0 in any month, pump at max, no article 21
          pumping_toggle = max(1, pumping_toggle)
          tax_free_toggle = max(1, tax_free_toggle)
          article21 =  0.0
          numdays_fillup = min(numdays_fillup, 999.9)#reservoir does not fill up in this condition (if it was full in prior loop months, retains its value)
        elif next_month_storage + net_pumping < projected_carryover and month_evaluate == 11:
          #if projected storage, w/max pumping, does not reach district's carryover amount by December, start max pumping
          pumping_toggle = max(1, pumping_toggle)
          tax_free_toggle = max(1, tax_free_toggle)
          numdays_fillup = min(numdays_fillup, 999.9)
          article21 = 0.0
        elif next_month_storage < projected_carryover and month_evaluate == 11:
          #if projected storage, w no releases for pumping, does not reach district's carryover amount by December, start releasing to tax free level (but not max)
          article21 = 0.0
          pumping_toggle = max(0, pumping_toggle)
          tax_free_toggle = max(1, tax_free_toggle)
          numdays_fillup = min(numdays_fillup, 999.9)
        elif next_month_storage + net_pumping < 1020.0 and month_evaluate == 2:
          #if projected storage, w/max pumping, is not full by march, start max pumping
          tax_free_toggle = max(1, tax_free_toggle)
          pumping_toggle = max(1, pumping_toggle)
          article21 = 0.0
          numdays_fillup = min(numdays_fillup, 999.9)
        elif next_month_storage + running_tax_free_pumping < 1020.0 and month_evaluate == 2:
          #if projected storage, w/only the tax free pumping is not full by march, pump at the tax free level (but not max)
          tax_free_toggle = max(1, tax_free_toggle)
          pumping_toggle = max(0, pumping_toggle)
          article21 = 0.0
          numdays_fillup = min(numdays_fillup, 999.9)
        else:
          #if none of those conditions are met, no pumping needed
          article21 = 0.0
          pumping_toggle = max(0,pumping_toggle)
          tax_free_toggle = max(0,tax_free_toggle)
          if next_month_storage + running_tax_free_pumping < 1020.0:
            numdays_fillup = min(numdays_fillup, 999.9)
          else:
            numdays_fillup = min(numdays_fillup,total_days_remaining)
	  ##note - beginning month = m; looped month = month_evaluate
      else:#if the loop begins between october and march
        if next_month_storage + min(flood_supply, net_pumping) > 1020.0:
          #if the flood water in the Sacramento River Reservoirs will increase the storage past capacity in any month,
		  #only release tax free amount (not max)
          pumping_toggle = 0
          tax_free_toggle = min(1, tax_free_toggle)
          #article21 flows are the expected extra flows divided by the number of days until the end of the month
          if total_days_remaining > 0.0:
            article21 = max((next_month_storage + min(flood_supply, net_pumping) - 1020.0 )/total_days_remaining, article21)
          else:
            article21 = max(next_month_storage + min(flood_supply, net_pumping) - 1020.0,article21)
          numdays_fillup = min(numdays_fillup,total_days_remaining)#record how many days until the reservoir is expected to fill up
        else:
          #all other times, pump at maximum level
          #if the 'tax free' pumping will take you over the capacity, release article 21 flows
          pumping_toggle = min(1, pumping_toggle)
          tax_free_toggle =  min(1, tax_free_toggle)		  
          article21 = max(0.0, article21)
          numdays_fillup = min(numdays_fillup,999.99)

			
      ##After we calculate what the pumping for SL based off projections from this month, we step the month
      ##forward and project new storage & pumping for the next month, and re-evaluate all releases.  From Oct-Mar, if
      ##any month triggers the pumping to stop, the pumping stops.  From June-Sept, if any month triggers the pumping, the
	  ##pumping occurs
      month_evaluate += 1
      if month_evaluate > 11:
        month_evaluate = 0
      #new 'unstored pumping' projections
      if month_evaluate >=9 or month_evaluate <= 2:
        projected_month_gains = self.month_averages[month_evaluate]*proj_surplus/days_in_month[month_evaluate]
      else:
        projected_month_gains = self.month_averages[month_evaluate]*proj_surplus2/days_in_month[month_evaluate]
      #new maximum pumping projections
      if month_evaluate >= 6 or month_evaluate == end_pumping:
        net_pumping += (pump_max-projected_month_gains)*days_in_month[month_evaluate]
      #
      if month_evaluate >= 5 or month_evaluate <= 2:
        available_pumping += (pump_max-projected_month_gains)*days_in_month[month_evaluate]
      expected_demands = (month_demand[wyt][month_evaluate]*allocation + month_demand_must_fill[wyt][month_evaluate])/days_in_month[month_evaluate]
      net_monthly = (projected_month_gains - expected_demands)*days_in_month[month_evaluate]
      total_days_remaining += this_month_days
      this_month_days = days_in_month[month_evaluate]



    return pumping_toggle, tax_free_toggle, article21, numdays_fillup
      
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
#############################  State Variables that use data from more than one obejct class#########################
#####################################################################################################################	  
  		  
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
          for y in x.contract_list:
            for yy in self.reservoir_contract[res.key]:
              if y == yy.name:
                use_reservoir = 1
          if use_reservoir == 1:
            for monthcounter in range(0,12):
              if x.must_fill == 1:
                res.monthly_demand_must_fill[wyt][monthcounter] += x.monthlydemand[wyt][monthcounter]*days_in_month[monthcounter]
              else:
                res.monthly_demand[wyt][monthcounter] += x.monthlydemand[wyt][monthcounter]*days_in_month[monthcounter]
              			  
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

	
  def flood_operations(self, t, dowy, wateryear, reservoir, flow_type, overflow_toggle):
    ###available flood taken from reservoir step
	###min-daily-uncontrolled is based on reservoir forecasts & available recharge space
    #releases from the flood pool, or in anticipation of the flood releases
    #'anticipation' releases are only made if they are at least as large as the
	#total recharge capacity at the reservoir
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
      for demand_type in ['contractor', 'turnout', 'excess']:
        flood_demand[demand_type] = np.zeros(len(self.reservoir_canal[reservoir.key]))
        flood_demand['tot_' + demand_type] = 0.0
		  
      ##Search for districts to take water
      ##Note: Millerton deliveries water to two seperate canals - their demands calculated seperately and split proportionally
      canal_counter = 0
      for z in self.reservoir_canal[reservoir.key]:
        #total flood deliveries on each canal to each priority type
        #flood_demand['contractor'][canal_counter], flood_demand['turnout'][canal_counter], flood_demand['excess'][canal_counter] = self.find_canal_demand(dowy, z, reservoir.key, z.name, 'normal',flow_type,wateryear)
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
          type_list = ['contractor', 'turnout', 'excess']
        else:
          type_list = ['contractor',]
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
    if flow_type == "recharge":
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[15], "normal", "normal", flow_type, 'xvc')
      self.fkc.find_bi_directional(self.calaqueduct.turnout_use[15], "normal", "reverse", flow_type, 'xvc')
      self.kernriverchannel.find_bi_directional(self.calaqueduct.turnout_use[15], "normal", "reverse", flow_type, 'xvc')

      self.calaqueduct.find_bi_directional(self.fkc.turnout_use[22], "reverse", "normal", flow_type, 'xvc')
      self.fkc.find_bi_directional(self.fkc.turnout_use[22], "reverse", "reverse", flow_type, 'xvc')
      self.kernriverchannel.find_bi_directional(self.fkc.turnout_use[22], "reverse", "reverse", flow_type, 'xvc')

      self.calaqueduct.find_bi_directional(self.kernriverchannel.turnout_use[4], "reverse", "normal", flow_type, 'xvc')
      self.fkc.find_bi_directional(self.kernriverchannel.turnout_use[4], "reverse", "reverse", flow_type, 'xvc')
      self.kernriverchannel.find_bi_directional(self.kernriverchannel.turnout_use[4], "reverse", "reverse", flow_type, 'xvc')
	  
    elif flow_type == "recovery":
      self.calaqueduct.find_bi_directional(self.calaqueduct.turnout_use[15], "reverse", "reverse", flow_type, 'xvc')
      self.fkc.find_bi_directional(self.calaqueduct.turnout_use[15], "reverse", "normal", flow_type, 'xvc')
      self.kernriverchannel.find_bi_directional(self.calaqueduct.turnout_use[15], "reverse", "normal", flow_type, 'xvc')

      self.calaqueduct.find_bi_directional(self.fkc.turnout_use[22], "normal", "reverse", flow_type, 'xvc')
      self.fkc.find_bi_directional(self.fkc.turnout_use[22], "normal", "normal", flow_type, 'xvc')
      self.kernriverchannel.find_bi_directional(self.fkc.turnout_use[22], "normal", "normal", flow_type, 'xvc')

      self.calaqueduct.find_bi_directional(self.kernriverchannel.turnout_use[4], "normal", "reverse", flow_type, 'xvc')
      self.fkc.find_bi_directional(self.kernriverchannel.turnout_use[4], "normal", "normal", flow_type, 'xvc')
      self.kernriverchannel.find_bi_directional(self.kernriverchannel.turnout_use[4], "normal", "normal", flow_type, 'xvc')

	  
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
            canal_range = (0, 0)
          else:
            ending_point -= 1			  
            canal_range = (starting_point, ending_point)
      elif flow_dir == "reverse":
        starting_point = len(self.canal_district[canal.name]) - 1
        if prev_canal == "none":
          canal_range = range(starting_point, -1, -1)
        else:
          for ending_point, new_canal in enumerate(self.canal_district[canal.name]):
            if new_canal.key == prev_canal:
              break
          if ending_point == (len(self.canal_district[canal.name])- 1):
            canal_range = (0,0)
          else:
            ending_point += 1
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
      type_list = ['contractor', 'turnout', 'excess']
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
   # is returned by the function as 'excess flow'
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
              priorities = wb_member.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, search_type, contract_canal)
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
          priorities = x.set_demand_priority(priority_list, contract_list, demand_constraint, deliveries, search_type, contract_canal)
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
            priorities = x.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, search_type, contract_canal, wb_member.contract_list)
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
        if turnout_available > 0.0 and location_delivery > 0.0:
          new_excess_flow, canal_demands = self.distribute_canal_deliveries(dowy, x, canal.key, contract_canal, location_delivery, new_canal_size, wateryear, new_flow_dir, flow_type, search_type)
          #update canal demands
          for zz in type_list:
            canal.demand[zz][canal_loc] = canal_demands[zz]
          if new_excess_flow > 0.0:
            for zz in type_list:
              canal.demand[zz][canal_loc] = 0.0
          #record deliveries
          location_delivery -= new_excess_flow
		  
      #record flow and turnout on each canal, check for capacity turnback at the next node				
      available_flow, turnback_flow, turnback_end = canal.update_canal_use(available_flow, location_delivery, flow_dir, canal_loc, starting_point, canal_size, type_list)
	  
      #if there is more demand/available water than canal capacity at the next canal node, the 'extra' water (that was expected to be delivered down-canal in earlier calculations) can be distributed among upstream nodes if there is remaining demand
      if turnback_flow > 0.0:		  
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
      type_list = ['contractor', 'turnout', 'excess']
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
			
      #sum demand at all canal nodes and check canal capacities for space
      sum_deliveries = 0.0
      for zz in type_list:
        type_deliveries[zz] += canal.demand[zz][canal_loc]
        sum_deliveries += type_deliveries[zz]
      existing_canal_space = canal.capacity[flow_dir][canal_loc]*cfs_tafd - canal.flow[canal_loc]
      if sum_deliveries > existing_canal_space:
        if flow_dir == "normal":
          lookback_range = range(starting_point, canal_loc + 1)
        elif flow_dir == "reverse":
          lookback_range = range(starting_point, canal_loc - 1, -1)
        for zz in type_list:
          for canal_backtrack in lookback_range:
            canal.recovery_flow_frac[zz][canal_backtrack] = min(max(min(existing_canal_space/type_deliveries[zz], 1.0), 0.0), canal.recovery_flow_frac[zz][canal_backtrack])		
          new_flow = min(type_deliveries[zz], existing_canal_space)
          existing_canal_space -= new_flow

      if search_type == "recovery":
        if isinstance(x,District):
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

          if committed > 0.0:
            if flow_dir == "normal":
              lookback_range = range(starting_point, canal_loc)
            elif flow_dir == "reverse":
              lookback_range = range(starting_point, canal_loc, -1)
            #search for waterbanks
            location_delivery = self.delivery_recovery(contract_list, canal, lookback_range, starting_point, paper_fractions, direct_recovery, flow_dir, type_list, priority_list, contract_canal, x.key, dowy, wateryear)
	#once all canal nodes have been searched, we can check to make sure the demands aren't bigger than the canal capacity, then adjust our demands	
    #type_deliveries = canal.capacity_adjust_demand(starting_point, canal_range, flow_dir, type_list)
	
    return type_deliveries
	
  def delivery_recovery(self, contract_list, canal, lookback_range, starting_point, paper_fractions, direct_recovery, flow_dir, type_list, priority_list, contract_canal, delivery_loc_name, dowy, wateryear):
    #Loop back through the canal looking for waterbank sources to make paper trades with
    available_flow = 0.0
    toggle_district_recharge = 0
    for lookback_loc in lookback_range:
      location_pumpout = 0.0
      recovery_source = self.canal_district[canal.name][lookback_loc]
      search_type = "recovery"
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
			  
              priorities = recovery_source.set_demand_priority("N/A", "N/A", priority_bank_space, deliveries, search_type, "N/A")
              priority_turnout_adjusted = {}
              #need to adjust the water request to account for the banking partner share of the turnout
              for zz in type_list:
                priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][lookback_loc]
              for zz in type_list:
                paper_amount = priority_turnout_adjusted[zz]*paper_fractions[zz]
                direct_amount = priority_turnout_adjusted[zz]*(1-paper_fractions[zz])
                trade_amount = paper_amount*canal.recovery_flow_frac[zz][lookback_loc]
                wb_member.get_paper_trade(trade_amount, contract_list, wateryear)
                recovery_source.adjust_recovery(trade_amount, xx, wateryear)
                location_pumpout += trade_amount
                if delivery_loc_name == wb_member.key:
                  demand_constraint = recovery_source.find_node_output()
                  flow_constraint = direct_amount*canal.recovery_flow_frac[zz][lookback_loc]
                  max_direct_recovery = min(demand_constraint, flow_constraint, recovery_source.inleiubanked[xx]/num_members)
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
            priorities = recovery_source.set_demand_priority("NA", "N/A", priority_bank_space, deliveries, search_type, "N/A", wb_member.contract_list)
            priority_turnout_adjusted = {}


            #need to adjust the water request to account for the banking partner share of the turnout
            for zz in type_list:
              priority_turnout_adjusted[zz] = priorities[zz]*canal.turnout_frac[zz][lookback_loc]
            #finds how much water can be delivered through paper trades (exchange of GW recovery for stored SW)
			#and how much water can be delivered directly
			#canal.recovery_flow_frac is the adjustment needed if the bank runs into canal capacity constraints
            for zz in type_list:
              paper_amount = priority_turnout_adjusted[zz]*paper_fractions[zz]
              direct_amount = priority_turnout_adjusted[zz]*(1-paper_fractions[zz])#direct deliveries 
              trade_amount = paper_amount*canal.recovery_flow_frac[zz][lookback_loc]#paper trades
              wb_member.get_paper_trade(trade_amount, contract_list, wateryear)#exchange GW for SW 
              recovery_source.adjust_recovery(trade_amount, xx, wateryear)#adjust accounts
              location_pumpout += trade_amount
			  #if the GW is being delivered to the WB owner, more water can be delivered (not constrained by 
			  #another district's willingness to trade SW storage)
              if delivery_loc_name == wb_member.key:
                demand_constraint = recovery_source.find_node_demand(contract_list, xx, num_members, search_type)
                flow_constraint = direct_amount*canal.recovery_flow_frac[zz][lookback_loc]
                max_direct_recovery = min(demand_constraint, flow_constraint, recovery_source.banked[xx]/num_members)
                actual_delivery = wb_member.direct_recovery_delivery(max_direct_recovery, wateryear)
                direct_recovery -= actual_delivery
                recovery_source.adjust_recovery(actual_delivery, xx, wateryear)
                location_pumpout += actual_delivery
			
        #recalculate the 'recovery demand' at each waterbank			
        self.find_node_demand_bank(recovery_source, canal, lookback_loc, contract_list, priority_list, contract_canal, dowy, wateryear, search_type, type_list)
        current_recovery = 0.0
        for xx in recovery_source.participant_list:
          current_recovery = recovery_source.recovery_use[xx]
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
          priorities = district_node.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, search_type, contract_canal)
          for zz in type_list:
            canal.demand[zz][canal_loc] += priorities[zz]
          #can't purchase more than the turnout capacity

    else:
      #find if district wants to purchase this type of flow
      deliveries =  district_node.set_request_constraints(demand_constraint, search_type, contract_list, 0.0, dowy)
      #find what priority district has for flow purchases
      priorities = district_node.set_demand_priority(priority_list, contract_list, demand_constraint, deliveries, search_type, contract_canal)
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
        priorities = bank_node.set_demand_priority(priority_list, contract_list, priority_bank_space, deliveries, search_type, contract_canal, wb_member.contract_list)
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
	
  def update_regulations_south(self,t,dowy,m,y):
    ##San Joaquin River Restoration Project, started in October of 2009 (WY 2009)
	##Additional Releases from Millerton Lake depending on WYT
    if y >= 2006:
      self.semitropic.leiu_recovery = 0.7945
    if y == 2009 and dowy == 1:
      expected_outflow_releases = {}
      for wyt in ['W', 'AN', 'BN', 'D', 'C']:
        expected_outflow_releases[wyt] = np.zeros(366)
      self.millerton.calc_expected_min_release(expected_outflow_releases, np.zeros(12),1)

    if y == 2009 and m >= 10:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)
    elif y > 2009:
      self.millerton.sjrr_release = self.millerton.sj_riv_res_flows(t, dowy)
    if t == 3866:
      self.isabella.capacity = 361.25
      self.isabella.tocs_rule['storage'] = [[302.6,170,170,245,245,361.25,361.25,302.6],  [302.6,170,170,245,245,361.25,361.25,302.6]]
    if y == 2014 and dowy == 1:
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
      self.kwbcanal.capacity["normal"] = [750.0, 750.0, 0.0, 0.0]
      self.kwbcanal.capacity["reverse"] = [0.0, 440.0, 800.0, 800.0]
      self.kwbcanal.capacity["closed"] = [0.0, 0.0, 0.0, 0.0]
      self.kwb.initial_recharge = 1212.12
      self.kwb.recovery = 0.7863
      self.kwb.tot_storage = 2.4
      self.find_all_triggers()
	  
      ####Calculates the requests for SWP allocations in WY 1997-2000
      ###when less than full allocation was requested by MWD.  This is unlikely to 
      ###occur in the future
    total_tableA = 0.0
    if y == 1996:
      self.swpdelta.max_allocation = 2977.0
      request_empty = 4124.0 - 2977.0
    elif y == 1997:
      self.swpdelta.max_allocation = 3191.0
      request_empty = 4124.0 - 3191.0
    elif y == 1998:
      self.swpdelta.max_allocation = 3214.0
      request_empty = 4124.0 - 3214.0
    elif y == 1999:
      self.swpdelta.max_allocation = 3617.0
      request_empty = 4124.0 - 3617.0
    else:
      self.swpdelta.max_allocation = 4124.0
      request_empty = 0.0
    for x in self.district_list:
      contractor_toggle = 0
      for contract in x.contract_list:
        if contract == 'tableA':
          contractor_toggle = 1
      if contractor_toggle == 1:	  
        if y < 2000:
          if x.key == "SOC":
            x.table_a_request = x.initial_table_a*self.swpdelta.total - request_empty
          elif x.key == "SOB":
            x.table_a_request = x.initial_table_a*self.swpdelta.total 
          elif x.key == "CCA":
            x.table_a_request = x.initial_table_a*self.swpdelta.total
          else:
            x.table_a_request = x.initial_table_a*self.swpdelta.total
          total_tableA += x.table_a_request
    for x in self.district_list:
      contractor_toggle = 0
      for contract in x.contract_list:
        if contract == 'tableA':
          contractor_toggle = 1
      if contractor_toggle == 1:	  
        if y < 2000:
          x.project_contract['tableA'] = x.table_a_request/total_tableA
        else:
          x.project_contract['tableA'] = x.initial_table_a
    
  def update_regulations_north(self,t,dowy):
    m = int(self.index.month[t])
    y = int(self.index.year[t])

	##Yuba River Accord, started in Jan of 2006 (repaces minimum flow requirements)
    if y >= 2006:
      self.yuba.env_min_flow = self.yuba.env_min_flow_ya
      self.yuba.temp_releases = self.yuba.temp_releases_ya
	  
  def get_iterable(self, x):
    if isinstance(x, cl.Iterable):
      return x
    else:
      return (x,)
	  	  
  def proj_gains(self,t):
    d = int(self.index.dayofyear[t])
    y = int(self.index.year[t])
    m = int(self.index.month[t])
    dowy = water_day(d,calendar.isleap(y))
    startYear = int(self.index.year[0])
    if m >= 10:
      wateryear = y - startYear
    else:
      wateryear = y - startYear - 1
    total_gains2 = self.delta_gains_regression2[dowy][0]*self.total_fnf[dowy][wateryear] + self.delta_gains_regression2[dowy][1]
    total_gains = self.delta_gains_regression[dowy][0]*self.total_fnf[dowy][wateryear] + self.delta_gains_regression[dowy][1]

    return total_gains, total_gains2

		
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

###GRAVEYARD######################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################
##################################################################################################################################################

  def calc_carryover_banking(self, t, m, dowy, wyt, wateryear):
    projection_length = 15
    dowy_md = [122, 150, 181, 211, 242, 272, 303, 334, 365, 31, 60, 91]
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    reservoir_change_rate = {}
    running_storage = {}
    running_extra_storage = {}
    fillup_reach = {}
    pumping = {}
    if t < projection_length:
      flow_range = range(0,projection_length)
    else:
      flow_range = range(t-projection_length, t)
	  
    for res in self.reservoir_list:
      if res.key == "SLS":
        current_storage = self.sanluisstate.S[t+1] 
      elif res.key == "SLF":
        current_storage = self.sanluisfederal.S[t+1]
      else:
        current_storage = res.S[t+1]

      running_extra_storage['storage'] = 0.0
      running_extra_storage['carryover'] = 0.0
      for y in self.reservoir_contract[res.key]:
        running_extra_storage['storage'] += max(y.tot_carryover - y.annual_deliveries[wateryear], 0.0)

      res.min_daily_uncontrolled = 0.0
      for y in self.reservoir_contract[res.key]:
        block_start = dowy
        for change_rate in ['deliveries', 'recharge']:
          running_storage[change_rate] = current_storage
          fillup_reach[change_rate] = {}
          for storage_volume in ['carryover', 'storage']:
            y.numdays_fillup[change_rate][storage_volume] = 0.0
            fillup_reach[change_rate][storage_volume] = 0
			
        first_of_month_shift = dowy - (1 + dowy_md[m-1] - days_in_month[m-1])
        this_month_flow = 0.0
        cross_counter = 0
        for month_counter in range(0,12):
          month_evaluate = m - 1 + month_counter
          if month_evaluate > 11:
            month_evaluate -= 12
          if month_evaluate == 9 and month_counter > 0:
            next_year = 365
            this_month_flow = 0
            cross_counter = 1
          elif month_evaluate == 3:
            this_month_flow = 0
            next_year = 0
          elif month_evaluate == 7:
            this_month_flow = 0
            next_year = 0
          else:
            next_year = 0
          
          if res.key == 'SLS':
            if cross_counter == 0:
              if t < 1:
                remaining_flow_proj = max(self.swpdelta.lastYearForecast - self.ytd_pump_hro[t-first_of_month_shift] - this_month_flow, 0.0)
              else:
                remaining_flow_proj = max(self.swpdelta.allocation[t-first_of_month_shift-1] - self.ytd_pump_hro[t-first_of_month_shift] - this_month_flow, 0.0)
            else:
              if t < 1:
                remaining_flow_proj = max(self.swpdelta.lastYearForecast - this_month_flow, 0.0)
              else:
                remaining_flow_proj = max(self.swpdelta.allocation[t-first_of_month_shift-1] - this_month_flow, 0.0)

          elif res.key == 'SLF':
            if cross_counter == 0:
              if t < 1:
                remaining_flow_proj = max(self.cvpdelta.lastYearForecast - self.ytd_pump_trp[t-first_of_month_shift] - this_month_flow, 0.0)
              else:
                remaining_flow_proj = max(self.cvpdelta.allocation[t-first_of_month_shift-1] - self.ytd_pump_trp[t-first_of_month_shift] - this_month_flow, 0.0)
            else:
              if t < 1:
                remaining_flow_proj = max(self.cvpdelta.lastYearForecast - this_month_flow, 0.0)
              else:
                remaining_flow_proj = max(self.cvpdelta.allocation[t-first_of_month_shift-1] - this_month_flow, 0.0)
          else:
            if cross_counter == 0:
              if month_evaluate >=9 or month_evaluate < 3:
                remaining_flow_proj = max(res.rainflood_inf[t-first_of_month_shift] - res.rainflood_flows - this_month_flow, 0.0)
              elif month_evaluate >= 3 and month_evaluate < 7:
                remaining_flow_proj = max(res.snowflood_inf[t-first_of_month_shift] - res.snowflood_flows - this_month_flow, 0.0)
              elif month_evaluate == 8 or month_evaluate == 9:
                remaining_flow_proj = max(res.baseline_inf[t-first_of_month_shift] - res.baseline_flows - this_month_flow, 0.0)
            elif cross_counter == 1:
              if month_evaluate >=9 or month_evaluate < 3:
                remaining_flow_proj = max(res.rainflood_inf[t-first_of_month_shift] - this_month_flow, 0.0)
              elif month_evaluate >= 3 and month_evaluate < 7:
                remaining_flow_proj = max(res.snowflood_inf[t-first_of_month_shift] - this_month_flow, 0.0)
              elif month_evaluate == 8 or month_evaluate == 9:
                remaining_flow_proj = max(res.baseline_inf[t-first_of_month_shift] - this_month_flow, 0.0)
          if month_evaluate == 3 or month_evaluate == 4:
            pumping['SLF'] = 750*cfs_tafd
            pumping['SLS'] = 750*cfs_tafd
          else:
            pumping['SLF'] = 6680*cfs_tafd
            pumping['SLS'] = 4430*cfs_tafd

          if month_counter == 0:
            if res.key == 'SLF':
              project = 'cvp'
            elif res.key == 'SLS':
              project = 'swp'
            if res.key == 'SLF' or res.key == 'SLS':
              if month_evaluate >=9 or month_evaluate < 6:
                ##E/I ratio is 0.65 duing oct-jan, 0.35 during feb-jun, and 0.65 from july-oct
                total_taxed_july_sept = 92.0*pumping[res.key] - self.max_tax_free[wyt][project][274]
              else:
                total_taxed_july_sept = (365.0 - dowy_md[month_evaluate]-days_in_month[month_evaluate])*pumping[res.key] - self.max_tax_free[wyt][project][dowy_md[month_evaluate]-days_in_month[month_evaluate]]

              month_flow_int = max(remaining_flow_proj - self.max_tax_free[wyt][project][dowy_md[month_evaluate]] - total_taxed_july_sept, pumping[res.key]*days_in_month[month_evaluate], 0.0)
            else:
              month_flow_int = (remaining_flow_proj*res.flow_shape['slope'][month_evaluate]+res.flow_shape['intercept'][month_evaluate])*remaining_flow_proj
              init_storage_proj = current_storage + (np.mean(res.Q[t:(t+5)]) - (res.monthly_demand[wyt][month_evaluate] + res.monthly_demand_must_fill[wyt][month_evaluate]))*30.0
              future_cap_date = dowy + 30
              if future_cap_date > 363:
                future_cap_date -= 363
              init_storage_cap = res.current_tocs(future_cap_date, res.fci[t])
              res.min_daily_uncontrolled = max(init_storage_proj - init_storage_cap, 0.0)/30.0
          else:
            if res.key == 'SLF':
              project = 'cvp'
            elif res.key == 'SLS':
              project = 'swp'

            if res.key == 'SLF' or res.key == 'SLS':
              if month_evaluate >=9 or month_evaluate < 6:
                ##E/I ratio is 0.65 duing oct-jan, 0.35 during feb-jun, and 0.65 from july-oct
                total_taxed_july_sept = 92.0*pumping[res.key] - self.max_tax_free[wyt][project][274]
              else:
                total_taxed_july_sept = (365.0 - dowy_md[month_evaluate]-days_in_month[month_evaluate])*pumping[res.key] - self.max_tax_free[wyt][project][dowy_md[month_evaluate]-days_in_month[month_evaluate]]

              month_flow_int = max(remaining_flow_proj - self.max_tax_free[wyt][project][dowy_md[month_evaluate]] - total_taxed_july_sept, pumping[res.key]*days_in_month[month_evaluate], 0.0)
            else:
              month_flow_int = (remaining_flow_proj*res.flow_shape['slope'][month_evaluate]+res.flow_shape['intercept'][month_evaluate])*remaining_flow_proj
          
          this_month_flow += month_flow_int
          reservoir_change_rate['recharge'] = month_flow_int/days_in_month[month_evaluate] - (res.monthly_demand[wyt][month_evaluate] + res.monthly_demand_must_fill[wyt][month_evaluate])
          reservoir_change_rate['deliveries'] = month_flow_int/days_in_month[month_evaluate]
          block_end = dowy_md[month_evaluate]
          if res.key == "SLS" or res.key == "SLF":
            storage_cap_start = 1020.0
            storage_cap_end = 1020.0
          else:
            storage_cap_start = res.current_tocs(block_start,res.fci[t])
            storage_cap_end = res.current_tocs(block_end, res.fci[t])
			
          if (block_end - block_start + next_year) > 0.0:
            for change_rate in ['deliveries', 'recharge']:
              running_contract = 0.0
              for end_target in ['carryover', 'storage']:
                storage_cap_start_use = storage_cap_start + running_extra_storage[end_target]
                storage_cap_end_use = storage_cap_end + running_extra_storage[end_target]
                eom_storage = running_storage[change_rate] + reservoir_change_rate[change_rate]*(block_end - block_start + next_year)
                differential_storage_change = reservoir_change_rate[change_rate] - (storage_cap_end - storage_cap_start)/(block_end - block_start + next_year)

                if eom_storage > storage_cap_end_use and fillup_reach[change_rate][end_target] == 0:
                  if differential_storage_change > 0.0:
                    day_cross_carryover = (storage_cap_start - running_storage[change_rate])/differential_storage_change
                  else:
                    day_cross_carryover = 0.0	
                  y.numdays_fillup[change_rate][end_target] += day_cross_carryover
                  fillup_reach[change_rate][end_target] = 1
                elif fillup_reach[change_rate][end_target] == 0:
                  y.numdays_fillup[change_rate][end_target] += block_end - block_start + next_year
                  if month_counter == 11:
                    y.numdays_fillup[change_rate][end_target] = 999
                
			  
                if eom_storage > storage_cap_end_use and end_target == 'carryover' and change_rate == 'recharge':
                  this_month_min_release = (eom_storage - storage_cap_end_use ) / (block_end + cross_counter*365 - dowy)
                  res.min_daily_uncontrolled = max(this_month_min_release, res.min_daily_uncontrolled)
					
                else:
                  res.min_daily_uncontrolled = max(0.0, res.min_daily_uncontrolled)

                           
              running_storage[change_rate] = eom_storage
            block_start = block_end
			
        running_extra_storage['carryover'] += max(y.tot_carryover - y.annual_deliveries[wateryear], 0.0)
        running_extra_storage['storage'] += max(y.storage_pool[t] - y.annual_deliveries[wateryear], 0.0)
	
  def assign_uncontrolled(self, t, wateryear):
    for z in self.pumping_turnback:
      cv_available = self.crossvalley.storage_pool[t] - self.crossvalley.annual_deliveries[wateryear]
      cd_available = self.cvpdelta.storage_pool[t] - self.cvpdelta.annual_deliveries[wateryear]
      ce_available = self.cvpexchange.storage_pool[t] - self.cvpexchange.annual_deliveries[wateryear]
      f2_available = self.friant2.storage_pool[t] - self.friant2.annual_deliveries[wateryear]
      f1_available = self.friant1.storage_pool[t] - self.friant1.annual_deliveries[wateryear]
      sw_available = self.swpdelta.storage_pool[t] - self.swpdelta.annual_deliveries[wateryear]
      kn_available = self.kernriver.storage_pool[t] - self.kernriver.annual_deliveries[wateryear]
      tl_available = self.tuleriver.storage_pool[t] - self.tuleriver.annual_deliveries[wateryear]
      kw_available = self.kaweahriver.storage_pool[t] - self.kaweahriver.annual_deliveries[wateryear]

      if z == 'SLF':
        if cv_available > 0.0:
          self.crossvalley.turnback_frac = min(self.pumping_turnback[z]/cv_available, 1.0)
          self.crossvalley.pumping_turnback = self.crossvalley.turnback_frac*cv_available
        else:
          self.crossvalley.turnback_frac = 0.0
          self.crossvalley.pumping_turnback = 0.0		  
        if cd_available > 0.0:
          self.cvpdelta.turnback_frac = min(max(self.pumping_turnback[z]-cv_available, 0.0)/cd_available, 1.0)
          self.cvpdelta.pumping_turnback = self.cvpdelta.turnback_frac*cd_available
        else:
          self.cvpdelta.turnback_frac = 0.0
          self.cvpdelta.pumping_turnback = 0.0		  
        if ce_available > 0.0:
          self.cvpexchange.turnback_frac = min(max(self.pumping_turnback[z] - cv_available - cd_available, 0.0)/ce_available, 1.0)
          self.cvpexchange.pumping_turnback = self.cvpexchange.turnback_frac*ce_available
        else:
          self.cvpexchange.turnback_frac = 0.0	
          self.cvpexchange.pumping_turnback = 0.0
      elif z == 'MIL':
        if f2_available > 0.0:
          self.friant2.turnback_frac = min(self.pumping_turnback[z]/f2_available, 1.0)
          self.friant2.pumping_turnback = self.friant2.turnback_frac*f2_available
        else:
          self.friant2.turnback_frac = 0.0
          self.friant2.pumping_turnback = 0.0
        if f1_available > 0.0:
          self.friant1.turnback_frac = min(max(self.pumping_turnback[z]-f2_available, 0.0)/f1_available, 1.0)
          self.friant1.pumping_turnback = self.friant1.turnback_frac*f1_available
        else:
          self.friant1.turnback_frac = 0.0
          self.friant1.pumping_turnback = 0.0
      elif z == 'SLS':
        if sw_available > 0.0:
          self.swpdelta.turnback_frac = min(self.pumping_turnback[z]/sw_available, 1.0)
          self.swpdelta.pumping_turnback = self.swpdelta.turnback_frac*sw_available
        else: 
          self.swpdelta.turnback_frac = 0.0
          self.swpdelta.pumping_turnback = 0.0
      elif z == 'SUC':
        if tl_available > 0.0:
          self.tuleriver.turnback_frac = min(self.pumping_turnback[z]/tl_available, 1.0)
          self.tuleriver.pumping_turnback = self.tuleriver.turnback_frac*tl_available
        else:
          self.tuleriver.turnback_frac = 0.0
          self.tuleriver.pumping_turnback = 0.0
      elif z == 'ISB':
        if kn_available > 0.0:
          self.kernriver.turnback_frac = min(self.pumping_turnback[z]/kn_available, 1.0)
          self.kernriver.pumping_turnback = self.kernriver.turnback_frac*kn_available
        else:
          self.kernriver.turnback_frac = 0.0
          self.kernriver.pumping_turnback = 0.0
      elif z == 'KWH':
        if kw_available > 0.0:
          self.kaweahriver.turnback_frac = min(self.pumping_turnback[z]/kw_available, 1.0)
          self.kaweahriver.pumping_turnback = self.kaweahriver.turnback_frac*kw_available
        else:
          self.kaweahriver.turnback_frac = 0.0
          self.kaweahriver.pumping_turnback = 0.0
		
    for y in self.contract_list:
      for x in self.district_list:
        if y.type == 'contract':
          x.turnback[y.name] = y.turnback_frac*((y.storage_pool[t] - y.tot_carryover)*x.project_contract[y.name] - x.deliveries[y.name][wateryear] + x.carryover[y.name] + x.paper_balance[y.name])
        elif y.type == 'right':
          x.turnback[y.name] = y.turnback_frac*((y.storage_pool[t] - y.tot_carryover)*x.rights[y.name]['capacity'] - x.deliveries[y.name][wateryear] + x.carryover[y.name] + x.paper_balance[y.name])

		  
		  
  def find_canal_demand(self, dowy, canal, prev_canal, contract_canal, flow_dir,flow_type,wateryear):
    #find the search range for this canal
    if flow_dir == "closed":
      return (0.0, 0.0, 0.0)
    else:
      canal_range, starting_point = self.set_canal_range(flow_dir, flow_type, canal, prev_canal)

    for canal_loc in canal_range:
      x = self.canal_district[canal.name][canal_loc]
      if isinstance(x, District):
        canal.demand['contractor'][canal_loc] = 0.0
        canal.demand['turnout'][canal_loc] = 0.0
        canal.demand['excess'][canal_loc] = 0.0
        total_current_balance = 0.0
        total_projected_allocation = 0.0
        total_deliveries = 0.0
        total_remaining_carryover = 0.0
        uncontrolled_deliveries = 0.0
        for y in self.canal_contract[contract_canal]:
          #if (y.storage_pool[t] - y.pumping_turnback - y.annual_deliveries[wateryear]) > 0.1*y.total:
            #total_current_balance += max(x.current_balance[y.name], x.projected_supply[y.name], 0.0)
          #else:
          total_projected_allocation += max(x.projected_supply[y.name], 0.0)
          total_deliveries += x.delivery_carryover[y.name]
          total_current_balance += max(x.current_balance[y.name], 0.0)
          total_remaining_carryover += max(x.carryover[y.name] - x.deliveries[y.name][wateryear], 0.0)
        if x.annualdemand > 0.0:
          total_demand_met = min(max(total_projected_allocation/(x.annualdemand*x.surface_water_sa*x.seepage), 0.0), 1.0)
        else:
          total_demand_met = 1.0
        if x.must_fill == 0:
          if dowy < 242:
            demand_constraint = min(total_deliveries, x.dailydemand_start*x.surface_water_sa*x.seepage)
          else:
            if contract_canal == "fkc":
              demand_constraint = max(x.dailydemand_start*total_demand_met*x.surface_water_sa*x.seepage, 0.0)
            else:
              demand_constraint = max(x.dailydemand_start*x.surface_water_sa*x.seepage, 0.0)
        elif x.must_fill == 1:
          demand_constraint = x.dailydemand*x.seepage
		  
        flood_need = total_projected_allocation - x.annualdemand - x.max_direct_recharge[0]*(365-dowy) - x.pre_flood_demand
        if x.seasonal_connection == 1 and total_remaining_carryover < x.dailydemand*x.seepage*x.surface_water_sa and flood_need < 0.0:
          #uncontrolled_deliveries = max(x.dailydemand*x.seepage - min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], x.dailydemand*x.seepage, demand_constraint, total_current_balance), 0.0)
          uncontrolled_deliveries = max(x.dailydemand*x.seepage*x.surface_water_sa, 0.0)
        else:
          uncontrolled_deliveries = 0.0

        contractor_toggle = 0
        priority_toggle = 0
        for yy in self.get_iterable(self.canal_priority[canal.name]):
          if yy.name == contract_canal:
            priority_toggle = 1
        if priority_toggle == 1:
          for y in self.canal_contract[contract_canal]:
            for yx in x.contract_list:
              if y.name == yx:
                contractor_toggle = 1
          if contractor_toggle == 1:
          #canal.demand['contractor'][canal_loc] = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], x.dailydemand + max(x.in_district_storage- x.current_recharge_storage, 0.0))
            canal.demand['contractor'][canal_loc] = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], max(x.in_district_storage- x.current_recharge_storage, 0.0) + uncontrolled_deliveries)
          else:
            #canal.demand['turnout'][canal_loc] = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], x.dailydemand + max(x.in_district_storage - x.current_recharge_storage, 0.0))
            canal.demand['turnout'][canal_loc] = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], max(x.in_district_storage - x.current_recharge_storage, 0.0) + uncontrolled_deliveries)
        else:
          canal.demand['excess'][canal_loc] = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], max(x.in_district_storage- x.current_recharge_storage, 0.0) + uncontrolled_deliveries)
		  
		  
      elif isinstance(x, Waterbank):
        canal.demand['contractor'][canal_loc] = 0.0
        canal.demand['turnout'][canal_loc] = 0.0
        canal.demand['excess'][canal_loc] = 0.0
        priority_toggle = 0
        for yy in self.get_iterable(self.canal_priority[canal.name]):
          if yy.name == contract_canal:
            priority_toggle = 1
        if priority_toggle == 1:
          for xx in x.participant_list:
            contractor_toggle = 0
            for wb_member in self.get_iterable(self.district_keys[xx]):
              for y in self.canal_contract[contract_canal]:
                for yx in wb_member.contract_list:
                  if y.name == yx:
                    contractor_toggle = 1
            if contractor_toggle == 1:
              canal.demand['contractor'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)
            else:
              canal.demand['turnout'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)
        else:
          for xx in x.participant_list:
            canal.demand['excess'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
			
        if canal.demand['contractor'][canal_loc] > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
          canal.demand['contractor'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]
          canal.demand['turnout'][canal_loc] = 0.0
        elif (canal.demand['contractor'][canal_loc] + canal.demand['turnout'][canal_loc]) > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
          canal.demand['turnout'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc] - canal.demand['contractor'][canal_loc]
        elif (canal.demand['contractor'][canal_loc] + canal.demand['turnout'][canal_loc] + canal.demand['excess'][canal_loc]) > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
          canal.demand['excess'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc] - canal.demand['contractor'][canal_loc] - canal.demand['turnout'][canal_loc]
		  
      elif isinstance(x, Canal): 
        if canal.turnout[flow_dir][canal_loc] > 0.0:
          new_flow_dir = canal.flow_directions[flow_type][x.name]
          canal.demand['contractor'][canal_loc], canal.demand['turnout'][canal_loc], canal.demand['excess'][canal_loc] = self.find_canal_demand(dowy, x, canal.key, contract_canal, new_flow_dir,flow_type,wateryear)
          if canal.demand['contractor'][canal_loc] > canal.turnout[flow_dir][canal_loc]*cfs_tafd:
            canal.demand['contractor'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd
          elif (canal.demand['contractor'][canal_loc] + canal.demand['turnout'][canal_loc]) > canal.turnout[flow_dir][canal_loc]*cfs_tafd:
            canal.demand['turnout'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.demand['contractor'][canal_loc]
          elif (canal.demand['contractor'][canal_loc] + canal.demand['turnout'][canal_loc] + canal.demand['excess'][canal_loc]) > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
            canal.demand['excess'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc] - canal.demand['contractor'][canal_loc] - canal.demand['turnout'][canal_loc]
        else:
          canal.demand['contractor'][canal_loc] = 0.0
          canal.demand['turnout'][canal_loc] = 0.0
          canal.demand['excess'][canal_loc] = 0.0

    contractor_deliveries = 0.0
    turnout_deliveries = 0.0
    excess_deliveries = 0.0
    contractor_unmet = 0.0
    turnout_unmet = 0.0
    excess_unmet = 0.0
    if flow_dir == "normal":
      canal_range = range((starting_point+1),canal_size)
      first_constraint = starting_point + 1
    elif flow_dir == "reverse":
      canal_range = range(starting_point-1,0,-1)
      first_constraint = starting_point - 1
    available_flow = canal.capacity[flow_dir][first_constraint]*cfs_tafd - canal.flow[first_constraint]
    for canal_loc in canal_range:
      if flow_dir == "normal":
        sum_range = range(canal_loc,canal_size)
      elif flow_dir == "reverse":
        sum_range = range(canal_loc,0,-1)
      total_demands = 0.0
      aux_demands = 0.0
      excess_demands = 0.0
      for sum_point in sum_range:
        total_demands += canal.demand['contractor'][sum_point]
        aux_demands += canal.demand['turnout'][sum_point]
        excess_demands += canal.demand['excess'][sum_point]
      if total_demands > available_flow:
        if total_demands > 0.0:
          demand_fraction_c = available_flow/total_demands
        else:
          demand_fraction_c = 0.0
        demand_fraction_t = 0.0
        demand_fraction_e = 0.0
        contractor_deliveries += canal.demand['contractor'][canal_loc]*demand_fraction_c
        contractor_unmet += canal.demand['contractor'][canal_loc]*(1-demand_fraction_c)
        turnout_unmet += canal.demand['turnout'][canal_loc]
        excess_unmet += canal.demand['excess'][canal_loc]
      elif (total_demands + aux_demands) > available_flow:
        demand_fraction_c = 1.0
        if aux_demands > 0.0:
          demand_fraction_t = (available_flow - total_demands)/aux_demands
        else:
          demand_fraction_t = 0.0
        demand_fraction_e = 0.0
        contractor_deliveries += canal.demand['contractor'][canal_loc]
        turnout_deliveries += canal.demand['turnout'][canal_loc]*demand_fraction_t
        turnout_unmet += canal.demand['turnout'][canal_loc]*(1-demand_fraction_t)
        excess_unmet += canal.demand['excess'][canal_loc]
      elif (total_demands + aux_demands + excess_demands) > available_flow:
        demand_fraction_c = 1.0
        demand_fraction_t = 1.0
        if excess_demands > 0.0:
          demand_fraction_e = (available_flow - total_demands - aux_demands)/excess_demands
        else:
          demand_fraction_e = 0.0

        contractor_deliveries += canal.demand['contractor'][canal_loc]
        turnout_deliveries += canal.demand['turnout'][canal_loc]
        excess_deliveries += canal.demand['excess'][canal_loc]*demand_fraction_e
        excess_unmet += canal.demand['excess'][canal_loc]*(1-demand_fraction_e)
      else:
        contractor_deliveries += canal.demand['contractor'][canal_loc]
        turnout_deliveries += canal.demand['turnout'][canal_loc]
        excess_deliveries += canal.demand['excess'][canal_loc]
        demand_fraction_c = 1.0
        demand_fraction_t = 1.0
        demand_fraction_e = 1.0
		 
      available_flow -=  canal.demand['contractor'][canal_loc]*demand_fraction_c + canal.demand['turnout'][canal_loc]*demand_fraction_t + canal.demand['excess'][canal_loc]*demand_fraction_e
      if flow_dir == "normal":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc+1]*cfs_tafd + canal.flow[canal_loc + 1],0.0)
      elif flow_dir == "reverse":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc-1]*cfs_tafd + canal.flow[canal_loc - 1],0.0)
      available_flow -= turnback_flows
      if turnback_flows < contractor_unmet:
        contractor_deliveries += turnback_flows
        contractor_unmet -= turnback_flows
      elif turnback_flows < (contractor_unmet + turnout_unmet):
        contractor_deliveries += contractor_unmet
        contractor_unmet = 0.0
        turnout_deliveries += (turnback_flows - contractor_unmet)
        turnout_unmet -= (turnback_flows - contractor_unmet)
      else:
        contractor_deliveries += contractor_unmet
        turnout_deliveries += turnout_unmet
        excess_deliveries += excess_unmet
        contractor_unmet = 0.0
        turnout_unmet = 0.0
        excess_unmet = 0.0
				  
    return contractor_deliveries, turnout_deliveries, excess_deliveries
	
  def find_contract_demand(self, t, dowy, wateryear, canal, prev_canal, contract_canal, flow_dir,flow_type):
    for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
      if new_canal.key == prev_canal:
        break
    if flow_dir == "normal":
      canal_size = len(self.canal_district[canal.name])
      canal_range = range((starting_point+1),canal_size)
    elif flow_dir == "reverse":
      canal_range = range((starting_point-1),0,-1)
    else:
      return (0.0)
	  
    priority_toggle = 0
    for yy in self.get_iterable(self.canal_priority[canal.name]):
      if yy.name == contract_canal:
        priority_toggle = 1
    if priority_toggle == 0:
      return (0.0)

    for canal_loc in canal_range:
      x = self.canal_district[canal.name][canal_loc]
      if isinstance(x, District):
        total_current_balance = 0.0
        total_projected_allocation = 0.0
        total_recharge = 0.0
        total_deliveries = 0.0
        total_carryover = 0.0
        total_turnback = 0.0
        total_id = 0.0
        total_borrow_water = 0.0
        canal.demand[contract_canal][canal_loc] = 0.0
        for y in self.canal_contract[contract_canal]:
          #if (y.storage_pool[t] - y.pumping_turnback - y.annual_deliveries[wateryear]) > 0.1*y.total:
            #total_current_balance += max(x.current_balance[y.name], x.projected_supply[y.name], 0.0)
          #else:
          total_current_balance += max(x.current_balance[y.name], 0.0)
          total_projected_allocation += max(x.projected_supply[y.name], 0.0)
          total_recharge += x.recharge_carryover[y.name]
          total_deliveries += x.delivery_carryover[y.name]
          total_carryover += x.carryover[y.name]
          total_id += x.deliveries[y.name][wateryear]
          total_borrow_water += y.borrow_water

        if x.annualdemand > 0.0:
          total_demand_met = min(max(total_projected_allocation/(x.annualdemand*x.surface_water_sa*x.seepage), 0.0), 1.0)
        else:
          total_demand_met = 1.0
        if x.must_fill == 0:
          if dowy < 242:
            demand_constraint = min(total_deliveries, x.dailydemand_start*total_demand_met*x.surface_water_sa*x.seepage)
          else:
            if contract_canal == "fkc":
              demand_constraint = max(x.dailydemand_start*total_demand_met*x.surface_water_sa*x.seepage, 0.0)
            else:
              demand_constraint = max(x.dailydemand_start*total_demand_met*x.surface_water_sa*x.seepage, 0.0)
        elif x.must_fill == 1:
          demand_constraint = x.dailydemand
        if x.seasonal_connection == 1:
          total_storage_pool = total_current_balance
          canal.demand[contract_canal][canal_loc] = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], x.dailydemand*x.seepage, demand_constraint, total_storage_pool)
        else:
          canal.demand[contract_canal][canal_loc] = 0.0

      elif isinstance(x, Waterbank):
        canal.demand[contract_canal][canal_loc] = 0.0

      elif isinstance(x, Canal): 
        if canal.turnout[flow_dir][canal_loc] > 0.0:
          new_flow_dir = canal.flow_directions[flow_type][x.name]
          canal.demand[contract_canal][canal_loc] = self.find_contract_demand(t, dowy, wateryear, x, canal.key, contract_canal, new_flow_dir,flow_type)
          if canal.demand[contract_canal][canal_loc] > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
            canal.demand[contract_canal][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]
        else:
          canal.demand[contract_canal][canal_loc] = 0.0

			
    contract_deliveries = 0.0
    contract_unmet = 0.0
    if flow_dir == "normal":
      canal_range = range((starting_point+1),canal_size)
      first_constraint = starting_point + 1
    elif flow_dir == "reverse":
      canal_range = range(starting_point-1,0,-1)
      first_constraint = starting_point - 1
    available_flow = canal.capacity[flow_dir][first_constraint]*cfs_tafd - canal.flow[first_constraint]
    for canal_loc in canal_range:
      if flow_dir == "normal":
        sum_range = range(canal_loc,canal_size)
      elif flow_dir == "reverse":
        sum_range = range(canal_loc,0,-1)
      total_demands = 0.0
      for sum_point in sum_range:
        total_demands += canal.demand[contract_canal][sum_point]
      if total_demands > available_flow:
        if total_demands > 0.0:
          demand_fraction = available_flow/total_demands
        else:
          demand_fraction = 0.0
        contract_deliveries += canal.demand[contract_canal][canal_loc]*demand_fraction
        contract_unmet += canal.demand[contract_canal][canal_loc]*(1-demand_fraction)
      else:
        contract_deliveries += canal.demand[contract_canal][canal_loc]
        demand_fraction = 1.0 
		
      available_flow -=  canal.demand[contract_canal][canal_loc]*demand_fraction
      if flow_dir == "normal":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc+1]*cfs_tafd + canal.flow[canal_loc + 1],0.0)
      elif flow_dir == "reverse":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc-1]*cfs_tafd + canal.flow[canal_loc - 1],0.0)
	  
      available_flow -= turnback_flows
      if turnback_flows < contract_unmet:
        contract_deliveries += turnback_flows
        contract_unmet -= turnback_flows
      else:
        contract_deliveries += contract_unmet
        contract_unmet = 0.0
    return contract_deliveries
	
  def find_contract_banked(self, canal, prev_canal, contract_canal, flow_dir,flow_type):
    for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
      if new_canal.key == prev_canal:
        break

    if flow_dir == "normal":
      canal_size = len(self.canal_district[canal.name])
      canal_range = range((starting_point+1),canal_size)
    elif flow_dir == "reverse":
      canal_range = range((starting_point-1),0,-1)
    else:
      return (0.0, 0.0)
    priority_toggle = 0
    for yy in self.get_iterable(self.canal_priority[canal.name]):
      if yy.name == contract_canal:
        priority_toggle = 1
    if priority_toggle == 0:
      return (0.0, 0.0)

    for canal_loc in canal_range:
      x = self.canal_district[canal.name][canal_loc]
      if isinstance(x, District):
        canal.demand['priority'][canal_loc] = 0.0
        canal.demand['secondary'][canal_loc] = 0.0
        direct_recharge_available = max(x.in_district_storage - x.current_recharge_storage, 0.0)
        total_current_balance = 0.0
        total_projected_supply = 0.0
        total_borrow = 0.0
        total_carryover_recharge = 0.0
        user_supplies = 0.0
        if direct_recharge_available > 0.0:
          for y in self.canal_contract[contract_canal]:
            total_current_balance += max(x.current_balance[y.name], 0.0)
            total_carryover_recharge += x.recharge_carryover[y.name]
            total_projected_supply += x.projected_supply[y.name]
            total_borrow += y.borrow_water
          total_supplies = max(total_current_balance, 0.0)
          user_supplies = max(min(total_supplies, total_carryover_recharge), 0.0)
          canal.demand['priority'][canal_loc] = min(user_supplies, direct_recharge_available)
		  
        if x.in_leiu_banking:
          total_capacity = x.dailydemand*x.seepage
          current_storage = 0.0
          for xx in x.participant_list:
            current_storage += x.direct_storage[xx]
          total_capacity += max(x.in_district_storage - current_storage, 0.0)
          for xx in x.participant_list:
            member_supplies = 0.0
            for wb_member in self.get_iterable(self.district_keys[xx]):
              total_current_balance = 0.0
              total_carryover_recharge = 0.0
              total_projected_supply = 0.0
              total_borrow = 0.0
              for y in self.canal_contract[contract_canal]:
                total_current_balance += max(wb_member.current_balance[y.name], 0.0)
                total_carryover_recharge += max(wb_member.recharge_carryover[y.name], 0.0)
                total_projected_supply += max(wb_member.projected_supply[y.name], 0.0)
                total_borrow += y.borrow_water
              
              total_supplies = max(total_current_balance, 0.0)
				
              recharge_available = max(wb_member.use_recharge,total_carryover_recharge)
              member_supplies += max(min(total_supplies,recharge_available), 0.0)
              member_priority_space = total_capacity*x.leiu_ownership[xx]
            if member_supplies > member_priority_space:
              canal.demand['priority'][canal_loc] += max(member_priority_space, 0.0)
              canal.demand['secondary'][canal_loc] += member_supplies - max(member_priority_space, 0.0)
            else:
              canal.demand['priority'][canal_loc] += member_supplies


			  
          if canal.demand['priority'][canal_loc] > total_capacity:
            canal.demand['priority'][canal_loc] = total_capacity
            canal.demand['secondary'][canal_loc] = 0.0
          elif canal.demand['secondary'][canal_loc] > total_capacity - canal.demand['priority'][canal_loc]:
            canal.demand['secondary'][canal_loc] = total_capacity - canal.demand['priority'][canal_loc]
          if canal.demand['priority'][canal_loc] > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
            canal.demand['priority'][canal_loc] = (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc])
            canal.demand['secondary'][canal_loc] = 0.0
          elif (canal.demand['priority'][canal_loc] + canal.demand['secondary'][canal_loc]) > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
            canal.demand['secondary'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc] - canal.demand['priority'][canal_loc]
			
          #canal.demand['priority'][canal_loc] = max(x.in_district_storage - x.current_recharge_storage, canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], 0.0)
          #canal.demand['secondary'][canal_loc] = 0.0
        if x.seasonal_connection == 0:
          canal.demand['priority'][canal_loc] = 0.0
          canal.demand['secondary'][canal_loc] = 0.0
      elif isinstance(x, Waterbank):
        canal.demand['priority'][canal_loc] = 0.0
        canal.demand['secondary'][canal_loc] = 0.0
        current_storage = 0.0
        total_secondary_demand = 0.0
        for xx in x.participant_list:
          member_supplies = 0.0
          current_storage += x.storage[xx]
          for wb_member in self.get_iterable(self.district_keys[xx]):
            total_supplies = 0.0
            total_borrow = 0.0
            for y in self.canal_contract[contract_canal]:
              total_supplies += min(wb_member.recharge_carryover[y.name],wb_member.current_balance[y.name], 0.0)
              total_borrow += y.borrow_water
            if total_supplies > 0.0:
              member_supplies += total_supplies
          if member_supplies > (x.tot_storage*x.ownership[xx] - x.storage[xx]):
            canal.demand['priority'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
            total_secondary_demand += member_supplies - max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
          else:
            canal.demand['priority'][canal_loc] += member_supplies
			
        if canal.demand['priority'][canal_loc] > x.tot_storage - current_storage:
          canal.demand['priority'][canal_loc] = x.tot_storage - current_storage
          canal.demand['secondary'][canal_loc] = 0.0
        else:
          canal.demand['secondary'][canal_loc] = min(x.tot_storage - current_storage, total_secondary_demand)
		  
        if canal.demand['priority'][canal_loc] > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
          canal.demand['priority'][canal_loc] = (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc])
          canal.demand['secondary'][canal_loc] = 0.0
        elif (canal.demand['priority'][canal_loc] + canal.demand['secondary'][canal_loc]) > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
          canal.demand['secondary'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc] - canal.demand['priority'][canal_loc]
		  
		  
      elif isinstance(x, Canal): 
        if canal.turnout[flow_dir][canal_loc] > 0.0:
          new_flow_dir = canal.flow_directions[flow_type][x.name]
          canal.demand['priority'][canal_loc], canal.demand['secondary'][canal_loc] = self.find_contract_banked(x, canal.key, contract_canal, new_flow_dir,flow_type)
          if canal.demand['priority'][canal_loc] > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
            canal.demand['priority'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]
          elif (canal.demand['priority'][canal_loc] + canal.demand['secondary'][canal_loc]) > (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]):
            canal.demand['secondary'][canal_loc] = canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc] - canal.demand['priority'][canal_loc]
        else:
          canal.demand['priority'][canal_loc] = 0.0
          canal.demand['secondary'][canal_loc] = 0.0
	  
    priority_deliveries = 0.0
    priority_unmet = 0.0
    secondary_deliveries = 0.0
    secondary_unmet = 0.0
    if flow_dir == "normal":
      canal_range = range((starting_point+1),canal_size)
      first_constraint = starting_point + 1
    elif flow_dir == "reverse":
      canal_range = range(starting_point-1,0,-1)
      first_constraint = starting_point - 1
    available_flow = canal.capacity[flow_dir][first_constraint]*cfs_tafd - canal.flow[first_constraint]
    for canal_loc in canal_range:
      if flow_dir == "normal":
        sum_range = range(canal_loc,canal_size)
      elif flow_dir == "reverse":
        sum_range = range(canal_loc,0,-1)
      priority_demands = 0.0
      secondary_demands = 0.0
      for sum_point in sum_range:
        priority_demands += canal.demand['priority'][sum_point]
        secondary_demands += canal.demand['secondary'][sum_point]
      if priority_demands > available_flow:
        if priority_demands > 0.0:
          demand_fraction_p = available_flow/priority_demands
        else:
          demand_fraction_p = 0.0
        demand_fraction_s = 0.0
		
        priority_deliveries += canal.demand['priority'][canal_loc]*demand_fraction_p
        priority_unmet += canal.demand['priority'][canal_loc]*(1-demand_fraction_p)
      elif (priority_demands + secondary_demands) > available_flow:
        demand_fraction_p = 1.0
        if secondary_demands > 0.0:
          demand_fraction_s = (available_flow - priority_demands)/secondary_demands
        else:
          demand_fraction_s = 0.0
		
        priority_deliveries += canal.demand['priority'][canal_loc]
        secondary_deliveries += canal.demand['secondary'][canal_loc]*demand_fraction_s
        secondary_unmet += canal.demand['secondary'][canal_loc]*(1-demand_fraction_s)
      else:
        priority_deliveries += canal.demand['priority'][canal_loc]
        secondary_deliveries += canal.demand['secondary'][canal_loc]
        demand_fraction_p = 1.0
        demand_fraction_s = 1.0
		
      available_flow -=  canal.demand['priority'][canal_loc]*demand_fraction_p + canal.demand['secondary'][canal_loc]*demand_fraction_s
      if flow_dir == "normal":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc+1]*cfs_tafd + canal.flow[canal_loc + 1],0.0)
      elif flow_dir == "reverse":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc-1]*cfs_tafd + canal.flow[canal_loc - 1],0.0)
      available_flow -= turnback_flows
      if turnback_flows < priority_unmet:
        priority_deliveries += turnback_flows
        priority_unmet -= turnback_flows
      elif turnback_flows < (priority_unmet + secondary_unmet):
        priority_deliveries += priority_unmet
        priority_unmet = 0.0
        secondary_deliveries += (turnback_flows - priority_unmet)
        secondary_unmet -= (turnback_flows - priority_unmet)
      else:
        priority_deliveries += priority_unmet
        secondary_deliveries += secondary_unmet
        priority_unmet = 0.0
        secondary_unmet = 0.0
				  
    return priority_deliveries, secondary_deliveries

	
  def deliver_contracts(self, t, dowy, canal, prev_canal, contract_canal, deliveries, canal_size, wateryear, flow_dir,flow_type):
    for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
      if new_canal.key == prev_canal:
        break
    
    available_flow = deliveries
    if flow_dir == "normal":
      canal_range = range((starting_point+1),canal_size)
      initial_loc = starting_point+1
    elif flow_dir == "reverse":
      full_canal = len(self.canal_district[canal.name])
      canal_range =  range((starting_point-1),full_canal - canal_size,-1)
      initial_loc = starting_point-1
    else:
      excess_flow = available_flow
      return (excess_flow, 0.0)
	  
    priority_toggle = 0
    for yy in self.get_iterable(self.canal_priority[canal.name]):
      if yy.name == contract_canal:
        priority_toggle = 1
    if priority_toggle == 0:
      return (available_flow, 0.0)


    excess_flow = 0.0
    if available_flow > canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc]:
      excess_flow = available_flow - (canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc])
      available_flow = canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc]

    total_demands = 0.0
    contract_deliveries = 0.0	
    for canal_loc in canal_range:
      total_demands += canal.demand[contract_canal][canal_loc]
    if total_demands < available_flow:
      excess_flow += available_flow - total_demands
      available_flow = total_demands
	
    for canal_loc in canal_range:
      if total_demands > 0.0:
        demand_fraction = min(available_flow/total_demands,1.0)
      else:
        demand_fraction = 0.0
      total_demands -= canal.demand[contract_canal][canal_loc]
      location_delivery = min(canal.demand[contract_canal][canal_loc]*demand_fraction, canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc])

	
      x = self.canal_district[canal.name][canal_loc]

      if isinstance(x, District):
        total_current_balance = 0.0
        total_projected_allocation = 0.0
        total_recharge = 0.0
        total_deliveries = 0.0
        total_borrow_water = 0.0
        for y in self.canal_contract[contract_canal]:
          #if (y.storage_pool[t] - y.pumping_turnback - y.annual_deliveries[wateryear]) > 0.1*y.total:
            #total_current_balance += max(x.current_balance[y.name], x.projected_supply[y.name], 0.0)
          #else:
          total_current_balance += max(x.current_balance[y.name], 0.0)
          total_projected_allocation += max(x.projected_supply[y.name], 0.0)
          total_recharge += x.recharge_carryover[y.name]
          total_deliveries += x.delivery_carryover[y.name]
          total_borrow_water += y.borrow_water
        if x.annualdemand > 0.0:
          total_demand_met = min(max(total_projected_allocation/x.annualdemand*x.surface_water_sa*x.seepage, 0.0), 1.0)
        else:
          total_demand_met = 1.0
        if x.must_fill == 0:
          if dowy < 242:
            demand_constraint = min(total_deliveries, x.dailydemand_start*x.surface_water_sa*total_demand_met*x.seepage)
          else:
            if contract_canal == "fkc":
              demand_constraint = max(x.dailydemand_start*x.surface_water_sa*total_demand_met*x.seepage, 0.0)
            else:
              demand_constraint = max(x.dailydemand_start*x.surface_water_sa*total_demand_met*x.seepage, 0.0)
        elif x.must_fill == 1:
          demand_constraint = x.dailydemand
        total_storage_pool = total_current_balance
        location_delivery = max(min(x.dailydemand*x.seepage, demand_constraint, total_storage_pool, location_delivery), 0.0)
        if x.seasonal_connection == 0:
          location_delivery = 0.0
          canal.demand[contract_canal][canal_loc] = 0.0
        x.dailydemand -= location_delivery/x.seepage
        demand_constraint -= location_delivery
        tcb = total_current_balance 
        tcb -= location_delivery
        canal.demand[contract_canal][canal_loc] = max(min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], x.dailydemand*x.seepage, demand_constraint, tcb), 0.0)

        for y in self.canal_contract[contract_canal]:
            #if (y.storage_pool[t] - y.pumping_turnback - y.annual_deliveries[wateryear]) > 0.1*y.total:
              #contract_delivery = location_delivery*max(x.current_balance[y.name], x.projected_supply[y.name])/total_current_balance
            #else:
          if total_current_balance > 0.0:
            contract_delivery = location_delivery*max(min(x.current_balance[y.name]/total_current_balance, 1.0), 0.0)
          elif total_projected_allocation > 0.0:
            contract_delivery = location_delivery*max(min(x.projected_supply[y.name]/total_projected_allocation, 1.0), 0.0)
          else:
            contract_delivery = 0.0
          x.deliveries[y.name][wateryear] += contract_delivery
          x.current_balance[y.name] -= contract_delivery
          y.annual_deliveries[wateryear] += contract_delivery
          y.daily_deliveries += contract_delivery
          x.delivery_carryover[y.name] -= contract_delivery
			   		
        		
      elif isinstance(x,Waterbank):
        canal.demand[contract_canal][canal_loc] = 0.0

      elif isinstance(x, Canal):
        new_flow_dir = canal.flow_directions[flow_type][x.name]
        new_canal_size = len(self.canal_district[x.name])
        if (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]) > 0.0 and location_delivery > 0.0:
          new_excess_flow, canal.demand[contract_canal][canal_loc] = self.deliver_contracts(t, dowy, x, canal.key, contract_canal, location_delivery, new_canal_size, wateryear, new_flow_dir,flow_type)
          location_delivery -= new_excess_flow
          if new_excess_flow > 0.0:
            canal.demand[contract_canal][canal_loc] = 0.0
        else:
          location_delivery = 0.0
		  
      canal.turnout_use[canal_loc] += location_delivery	  
      canal.flow[canal_loc] += available_flow 
      available_flow -=  location_delivery
      convey_min = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], canal.capacity[flow_dir][canal_loc]*cfs_tafd - canal.flow[canal_loc])
      if canal.demand[contract_canal][canal_loc] > convey_min:
         canal.demand[contract_canal][canal_loc] = convey_min


      if flow_dir == "normal":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc+1]*cfs_tafd + canal.flow[canal_loc+1],0.0)
      elif flow_dir == "reverse":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc-1]*cfs_tafd + canal.flow[canal_loc-1],0.0)
			  
      if turnback_flows > 0.005:
        available_flow -= turnback_flows
        if flow_dir == "normal":
          turnback_end = canal_loc + 1
          for removal_flow in range((starting_point+1),canal_loc+1):
            canal.flow[removal_flow] -= turnback_flows

        elif flow_dir == "reverse":
          turnback_end = len(self.canal_district[canal.name]) - canal_loc - 1
          for removal_flow in range((starting_point-1),canal_loc-1,-1):
            canal.flow[removal_flow] -= turnback_flows
        remaining_excess_flow, unmet_holder = self.deliver_contracts(t, dowy, canal, prev_canal, contract_canal, turnback_flows, turnback_end, wateryear, flow_dir, flow_type)
        excess_flow += remaining_excess_flow
		  	  
    unmet_demand = 0.0
    for canal_loc in canal_range:
      unmet_demand += canal.demand[contract_canal][canal_loc]
	  
    return excess_flow, unmet_demand

  def deliver_banked(self, canal, prev_canal, contract_canal, deliveries, canal_size, wateryear, flow_dir, flow_type):
    for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
      if new_canal.key == prev_canal:
        break
		
    available_flow = deliveries
    if flow_dir == "normal":
      canal_range = range((starting_point+1),canal_size)
      initial_loc = starting_point+1
    elif flow_dir == "reverse":
      full_canal = len(self.canal_district[canal.name])
      canal_range =  range((starting_point-1),full_canal - canal_size,-1)
      initial_loc = starting_point-1
    else:
      excess_flow = available_flow
      return (excess_flow, 0.0, 0.0, 0.0)
	  
    priority_toggle = 0
    for yy in self.get_iterable(self.canal_priority[canal.name]):
      if yy.name == contract_canal:
        priority_toggle = 1
    if priority_toggle == 0:
      return (available_flow, 0.0, 0.0)

    
    excess_flow = 0.0
    if available_flow > canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc]:
      excess_flow = available_flow - (canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc])
      available_flow = canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc]
    priority_demands = 0.0
    priority_deliveries = 0.0	
    secondary_demands = 0.0
    secondary_deliveries = 0.0	
    unmet_demand = 0.0
    for canal_loc in canal_range:
      priority_demands += canal.demand['priority'][canal_loc]
      secondary_demands += canal.demand['secondary'][canal_loc]   
	  
    if (priority_demands + secondary_demands) < available_flow:
      excess_flow += available_flow - (priority_demands + secondary_demands)
      available_flow = priority_demands + secondary_demands
    for canal_loc in canal_range:
      if priority_demands > available_flow:	  
        if priority_demands > 0.0:
          demand_fraction_p = min(max(available_flow/priority_demands,0.0),1.0)
        else:
          demand_fraction_p = 0.0
        demand_fraction_s = 0.0
      elif (priority_demands + secondary_demands) > available_flow:
        demand_fraction_p = 1.0
        if secondary_demands > 0.0:
          demand_fraction_s = min(max((available_flow-priority_demands)/secondary_demands,0.0),1.0)
        else:
          demand_fraction_s = 0.0
      else:
        demand_fraction_s = 1.0
        demand_fraction_p = 1.0
		
      priority_demands -= canal.demand['priority'][canal_loc]
      secondary_demands -= canal.demand['secondary'][canal_loc]
      location_delivery = min(canal.demand['priority'][canal_loc]*demand_fraction_p + canal.demand['secondary'][canal_loc]*demand_fraction_s, canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc])
      x = self.canal_district[canal.name][canal_loc]

      if isinstance(x,District):
        direct_recharge_available = max(x.in_district_storage - x.current_recharge_storage, 0.0)
        contract_deliveries = 0.0
        total_recharge = 0.0
        total_current_balance = 0.0
        total_projected_supply = 0.0
        total_borrow = 0.0
        if x.seasonal_connection == 0:
          location_delivery = 0.0
          self.canal.demand['priority'][canal_loc] = 0.0
          self.canal.demand['secondary'][canal_loc] = 0.0

        if direct_recharge_available > 0.0:
          for y in self.canal_contract[contract_canal]:
            total_recharge += max(x.recharge_carryover[y.name], 0.0)
            total_current_balance += max(x.current_balance[y.name], 0.0)
            total_projected_supply += max(x.projected_supply[y.name], 0.0)
            total_borrow += y.borrow_water
          total_supplies = max(total_current_balance, 0.0)
          total_available = min(total_recharge, total_supplies, location_delivery)
          for y in self.canal_contract[contract_canal]:
            if total_current_balance > 0.0:			
              contract_deliveries = total_available*max(x.current_balance[y.name], 0.0)/total_current_balance
            elif total_projected_supply > 0.0:
              contract_deliveries = total_available*max(x.projected_supply[y.name], 0.0)/total_projected_supply
            else:
              contract_deliveries = 0.0

            x.deliveries[y.name][wateryear] += contract_deliveries
            x.deliveries['recharged'][wateryear] += contract_deliveries
            y.annual_deliveries[wateryear] += contract_deliveries
            y.daily_deliveries += contract_deliveries

            x.current_balance[y.name] -= contract_deliveries
            x.use_recharge -= min(contract_deliveries, x.use_recharge)
            x.recharge_carryover[y.name] -= min(contract_deliveries, x.recharge_carryover[y.name])
            x.current_recharge_storage += contract_deliveries
          canal.demand['priority'][canal_loc] -= contract_deliveries
          canal.demand['secondary'][canal_loc] = 0.0
          location_delivery -= contract_deliveries
        
        if x.in_leiu_banking:
          total_priority = 0.0
          total_secondary = 0.0
          total_capacity = x.dailydemand*x.seepage
          current_storage = 0.0
          total_capacity += max(x.in_district_storage - x.current_recharge_storage, 0.0)
          if location_delivery > total_capacity:
            location_delivery = total_capacity
          for xx in x.participant_list:
            member_supplies = 0.0
            member_priority_space = x.dailydemand*x.seepage*x.leiu_ownership[xx] + max(x.leiu_ownership[xx]*(x.in_district_storage - x.current_recharge_storage), 0.0)
            for wb_member in self.get_iterable(self.district_keys[xx]):
              total_current_balance = 0.0
              total_carryover_recharge = 0.0
              total_projected_supply = 0.0
              total_borrow = 0.0
              for y in self.canal_contract[contract_canal]:
                total_current_balance += max(wb_member.current_balance[y.name], 0.0)
                total_carryover_recharge += wb_member.recharge_carryover[y.name]
                total_projected_supply += wb_member.projected_supply[y.name]
                total_borrow += y.borrow_water
              total_supplies = max(total_current_balance, 0.0)
              available_recharge = max(total_carryover_recharge, wb_member.use_recharge)
              member_supplies += max(min(total_supplies, available_recharge), 0.0)
            total_priority += min(member_supplies, member_priority_space)
            total_secondary += max(member_supplies - member_priority_space, 0.0)
          if total_priority >= location_delivery:
            if total_priority > 0.0:		  
              turnout_frac_p = location_delivery/total_priority
            else:
              turnout_frac_p = 0.0
            turnout_frac_s = 0.0
          elif (total_priority + total_secondary) >= location_delivery:
            turnout_frac_p = 1.0
            if total_secondary > 0.0:		  
              turnout_frac_s = (location_delivery - total_priority)/total_secondary
            else:
              turnout_frac_s = 0.0
          else:
            turnout_frac_p = 1.0
            turnout_frac_s = 1.0
            location_delivery = total_priority + total_secondary
			
          canal.demand['priority'][canal_loc] = 0.0
          canal.demand['secondary'][canal_loc] = 0.0
          for xx in x.participant_list:
            member_supplies = 0.0
            member_priority_space = x.dailydemand*x.seepage*x.leiu_ownership[xx] + max(x.leiu_ownership[xx]*(x.in_district_storage - x.current_recharge_storage), 0.0)
            for wb_member in self.get_iterable(self.district_keys[xx]):
              total_current_balance = 0.0
              total_carryover_recharge = 0.0
              total_projected_supply = 0.0
              total_borrow = 0.0
              for y in self.canal_contract[contract_canal]:
                total_current_balance += max(wb_member.current_balance[y.name], 0.0)
                total_carryover_recharge += wb_member.recharge_carryover[y.name]
                total_projected_supply += wb_member.projected_supply[y.name]
                total_borrow += y.borrow_water
              total_supplies = max(total_current_balance, 0.0)
				
              available_recharge = max(total_carryover_recharge,wb_member.use_recharge)
              member_supplies += max(min(total_supplies, available_recharge), 0.0)
            member_deliveries = min(member_supplies, member_priority_space)*turnout_frac_p + max(member_supplies-member_priority_space, 0.0)*turnout_frac_s
            for y in self.canal_contract[contract_canal]:
              if total_current_balance > 0.0:
                contract_deliveries = member_deliveries*max(wb_member.current_balance[y.name], 0.0)/total_current_balance
              elif total_projected_supply > 0.0:
                contract_deliveries = member_deliveries*max(wb_member.projected_supply[y.name], 0.0)/total_projected_supply
              else:
                contract_deliveries = 0.0
              wb_member.deliveries[y.name][wateryear] += contract_deliveries
              wb_member.deliveries['recharged'][wateryear] += contract_deliveries
              y.annual_deliveries[wateryear] += contract_deliveries
              y.daily_deliveries += contract_deliveries

              wb_member.current_balance[y.name] -= contract_deliveries
              wb_member.use_recharge -= min(contract_deliveries,wb_member.use_recharge)
              wb_member.recharge_carryover[y.name] -= min(contract_deliveries,wb_member.recharge_carryover[y.name])
              if contract_deliveries > x.dailydemand*x.seepage:
                x.current_recharge_storage += (contract_deliveries - x.dailydemand*x.seepage)
                x.deliveries['inleiu'][wateryear] += contract_deliveries
                x.inleiubanked[xx] += x.dailydemand*x.seepage + (contract_deliveries - x.dailydemand*x.seepage)*.9
                x.dailydemand = 0.0
              else:
                x.deliveries['inleiu'][wateryear] += contract_deliveries
                x.dailydemand -= contract_deliveries/x.seepage
                x.inleiubanked[xx] += contract_deliveries
			
		    ####Recalculate New Demand
            member_supplies -= member_deliveries
            if member_supplies > ( x.dailydemand*x.leiu_ownership[xx]*x.seepage + max(x.leiu_ownership[xx]*(x.in_district_storage - x.current_recharge_storage), 0.0)):
              canal.demand['priority'][canal_loc] += max(x.dailydemand*x.leiu_ownership[xx]*x.seepage + max(x.leiu_ownership[xx]*(x.in_district_storage - x.current_recharge_storage), 0.0) - member_deliveries, 0.0)
              canal.demand['secondary'][canal_loc] += member_supplies - max(x.dailydemand*x.seepage*x.leiu_ownership[xx] + max(x.leiu_ownership[xx]*(x.in_district_storage - x.current_recharge_storage), 0.0) - member_deliveries, 0.0)
            else:
              canal.demand['priority'][canal_loc] += member_supplies

          ##Update Demand Constraints
          if canal.demand['priority'][canal_loc] > x.dailydemand*x.seepage:
            canal.demand['priority'][canal_loc] = x.dailydemand*x.seepage
            canal.demand['secondary'][canal_loc] = 0.0
          elif (canal.demand['secondary'][canal_loc] + canal.demand['priority'][canal_loc])  > x.dailydemand*x.seepage:
            canal.demand['secondary'][canal_loc] = x.dailydemand*x.seepage - canal.demand['priority'][canal_loc]
      if isinstance(x, Waterbank):
        total_priority = 0.0
        total_secondary = 0.0
        current_storage = 0.0
        for xx in x.participant_list:
          current_storage += x.storage[xx]
        if location_delivery > (x.tot_storage - current_storage):
          location_delivery = x.tot_storage - current_storage
        for xx in x.participant_list:
          member_supplies = 0.0
          for wb_member in self.get_iterable(self.district_keys[xx]):
            total_supplies = 0.0
            total_borrow = 0.0
            for y in self.canal_contract[contract_canal]:
              total_supplies += min(wb_member.recharge_carryover[y.name],wb_member.current_balance[y.name], 0.0)
              total_borrow += y.borrow_water
            if total_supplies > 0.0:
              member_supplies += total_supplies

            #total_current_balance = 0.0
            #total_carryover_recharge = 0.0
            #total_projected_supply = 0.0
            #total_borrow = 0.0
            #for y in self.canal_contract[contract_canal]:
              #total_current_balance += max(wb_member.current_balance[y.name], 0.0)
              #total_carryover_recharge += wb_member.recharge_carryover[y.name]
              #total_projected_supply += wb_member.projected_supply[y.name]
              #total_borrow += y.borrow_water
            #total_supplies = max(total_current_balance, 0.0)
			  
            #available_recharge = max(total_carryover_recharge,wb_member.use_recharge)
            #if available_recharge > 0.0:
              #member_supplies += max(min(total_supplies, available_recharge), 0.0)
          member_priority_space = max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
          total_priority += min(member_supplies, member_priority_space)
          total_secondary += max(member_supplies - member_priority_space, 0.0)
            
        if total_priority >= location_delivery:
          if total_priority > 0.0:		  
            turnout_frac_p = location_delivery/total_priority
          else:
            turnout_frac_p = 0.0
          turnout_frac_s = 0.0
        elif (total_priority + total_secondary) >= location_delivery:
          turnout_frac_p = 1.0
          if total_secondary > 0.0:		  
            turnout_frac_s = (location_delivery - total_priority)/total_secondary
          else:
            turnout_frac_s = 0.0
        else:
          turnout_frac_p = 1.0
          turnout_frac_s = 1.0
          location_delivery = total_priority + total_secondary
	 
        canal.demand['priority'][canal_loc] = 0.0
        canal.demand['secondary'][canal_loc] = 0.0

        for xx in x.participant_list:
          member_supplies = 0.0
          for wb_member in self.get_iterable(self.district_keys[xx]):
            total_supplies = 0.0
            total_borrow = 0.0
            for y in self.canal_contract[contract_canal]:
              total_supplies += min(wb_member.recharge_carryover[y.name],wb_member.current_balance[y.name], 0.0)
              total_borrow += y.borrow_water
            if total_supplies > 0.0:
              member_supplies += total_supplies
          member_priority_space = max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
          member_deliveries = min(member_supplies, member_priority_space)*turnout_frac_p + max(member_supplies-member_priority_space, 0.0)*turnout_frac_s
          for wb_member in self.get_iterable(self.district_keys[xx]):	  
            for y in self.canal_contract[contract_canal]:
              if member_supplies > 0.0:
                contract_deliveries = member_deliveries*max(wb_member.recharge_carryover[y.name], wb_member.current_balance[y.name], 0.0)/member_supplies
              else:
                contract_deliveries = 0.0
			  
              wb_member.deliveries[y.name][wateryear] += contract_deliveries
              wb_member.deliveries['recharged'][wateryear] += contract_deliveries
              y.annual_deliveries[wateryear] += contract_deliveries
              y.daily_deliveries += contract_deliveries
              wb_member.current_balance[y.name] -= contract_deliveries
              wb_member.use_recharge -= min(contract_deliveries,wb_member.use_recharge)
              wb_member.recharge_carryover[y.name] -= min(contract_deliveries,wb_member.recharge_carryover[y.name])
			  


			
          x.storage[xx] += member_deliveries
          current_storage += member_deliveries
		  ####Recalculate New Demand
          member_supplies -= member_deliveries
          if member_supplies > (x.tot_storage*x.ownership[xx] - x.storage[xx]):
            canal.demand['priority'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
            canal.demand['secondary'][canal_loc] += member_supplies - max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
          else:
            canal.demand['priority'][canal_loc] += member_supplies

        ##Update Demand Constraints
        current_tot_storage = 0.0
        for xx in x.participant_list:
          current_tot_storage += x.storage[xx]
        if canal.demand['priority'][canal_loc] > (x.tot_storage - current_tot_storage):
          canal.demand['priority'][canal_loc] = x.tot_storage - current_tot_storage
          canal.demand['secondary'][canal_loc] = 0.0
        elif (canal.demand['secondary'][canal_loc] + canal.demand['priority'][canal_loc])  > x.tot_storage - current_tot_storage:
          canal.demand['secondary'][canal_loc] = x.tot_storage - current_tot_storage - canal.demand['priority'][canal_loc]
		  	  
      elif isinstance(x, Canal):
        new_flow_dir = canal.flow_directions[flow_type][x.name]
        new_canal_size = len(self.canal_district[x.name])
        if (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]) > 0.0 and location_delivery > 0.0:
          new_excess_flow, canal.demand['priority'][canal_loc], canal.demand['secondary'][canal_loc] = self.deliver_banked(x, canal.key, contract_canal, location_delivery, new_canal_size, wateryear, new_flow_dir, flow_type)
          location_delivery -= new_excess_flow
          if new_excess_flow > 0.0:
            canal.demand['priority'][canal_loc] = 0.0
            canal.demand['secondary'][canal_loc] = 0.0

        else:
          location_delivery = 0.0
		  
      canal.turnout_use[canal_loc] += location_delivery
      canal.flow[canal_loc] += available_flow       
      available_flow -=  location_delivery
      convey_min = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], canal.capacity[flow_dir][canal_loc]*cfs_tafd - canal.flow[canal_loc])
      if canal.demand['priority'][canal_loc] > convey_min:
         canal.demand['priority'][canal_loc] = convey_min
         canal.demand['secondary'][canal_loc] = 0.0
      elif canal.demand['priority'][canal_loc] + canal.demand['secondary'][canal_loc] > convey_min:
        canal.demand['secondary'][canal_loc] = convey_min - canal.demand['priority'][canal_loc]
		
      if flow_dir == "normal":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc+1]*cfs_tafd + canal.flow[canal_loc+1],0.0)
      elif flow_dir == "reverse":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc-1]*cfs_tafd + canal.flow[canal_loc-1],0.0)
		
      if turnback_flows > 0.005:
        available_flow -= turnback_flows

        if flow_dir == "normal":
          turnback_end = canal_loc + 1
          for removal_flow in range((starting_point+1),canal_loc+1):
            canal.flow[removal_flow] -= turnback_flows
            turnback_end = canal_loc + 1

        elif flow_dir == "reverse":
          turnback_end = len(self.canal_district[canal.name]) - canal_loc - 1
          for removal_flow in range((starting_point-1),canal_loc-1,-1):
            canal.flow[removal_flow] -= turnback_flows

        remaining_excess_flow, unmet_demand_priority, unmet_demand_secondary = self.deliver_banked(canal, prev_canal, contract_canal, turnback_flows, turnback_end, wateryear, flow_dir, flow_type)
        excess_flow += remaining_excess_flow
			
    unmet_priority = 0.0
    unmet_secondary = 0.0
    for canal_loc in canal_range:
      unmet_priority += canal.demand['priority'][canal_loc]
      unmet_secondary += canal.demand['secondary'][canal_loc]

    return excess_flow, unmet_priority, unmet_secondary
	
	
  def deliver_flood_flows(self, dowy, canal, prev_canal, contract_canal, deliveries, canal_size, wateryear, flow_dir, flow_type, delivery_key):
    for starting_point, new_canal in enumerate(self.canal_district[canal.name]):
      if new_canal.key == prev_canal:
        break
    contractor_deliveries = 0.0
    turnout_deliveries = 0.0
    excess_deliveries = 0.0
    available_flow = deliveries

    if flow_dir == "normal":
      canal_range = range((starting_point+1),canal_size)
      initial_loc = starting_point + 1
    elif flow_dir == "reverse":
      full_canal = len(self.canal_district[canal.name])
      canal_range =  range((starting_point-1),full_canal - canal_size,-1)
      initial_loc = starting_point - 1
    else:
      return (excess_flow, 0.0, 0.0)
	  
    excess_flow = 0.0
    if available_flow > canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc]:
      excess_flow = available_flow - (canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc])
      available_flow = canal.capacity[flow_dir][initial_loc]*cfs_tafd - canal.flow[initial_loc]

    total_demands = 0.0
    aux_demands = 0.0
    excess_demands = 0.0
    for canal_loc in canal_range:
      total_demands += canal.demand['contractor'][canal_loc]
      aux_demands += canal.demand['turnout'][canal_loc]
      excess_demands += canal.demand['excess'][canal_loc]
    if (total_demands + aux_demands + excess_demands) < available_flow:
      excess_flow += available_flow - total_demands - aux_demands - excess_demands
      available_flow = total_demands + aux_demands + excess_demands
	  
    unmet_demand = 0.0
    for canal_loc in canal_range:

      if total_demands > available_flow:
        if total_demands > 0.0:
          demand_fraction_c = available_flow/total_demands
        else:
          demand_fraction_c = 0.0
        demand_fraction_t = 0.0
        demand_fraction_e = 0.0
        contractor_deliveries += canal.demand['contractor'][canal_loc]*demand_fraction_c
      elif (total_demands + aux_demands) > available_flow:
        demand_fraction_c = 1.0
        if aux_demands > 0.0:
          demand_fraction_t = (available_flow - total_demands)/aux_demands
        else:
          demand_fraction_t = 0.0
        demand_fraction_e = 0.0
        contractor_deliveries += canal.demand['contractor'][canal_loc]
        turnout_deliveries += canal.demand['turnout'][canal_loc]*demand_fraction_t
      elif (total_demands + aux_demands + excess_demands) > available_flow:
        demand_fraction_c = 1.0
        demand_fraction_t = 1.0
        if excess_demands > 0.0:
          demand_fraction_e = (available_flow - total_demands - aux_demands)/excess_demands
        else:
          demand_fraction_e = 0.0
        contractor_deliveries += canal.demand['contractor'][canal_loc]
        turnout_deliveries += canal.demand['turnout'][canal_loc]
        excess_deliveries += canal.demand['excess'][canal_loc]*demand_fraction_e

      else:
        contractor_deliveries += canal.demand['contractor'][canal_loc]
        turnout_deliveries += canal.demand['turnout'][canal_loc]
        excess_deliveries += canal.demand['excess'][canal_loc]
        demand_fraction_c = 1.0
        demand_fraction_t = 1.0
        demand_fraction_e = 1.0
	
      total_demands -= canal.demand['contractor'][canal_loc]
      aux_demands -= canal.demand['turnout'][canal_loc]
      excess_demands -= canal.demand['excess'][canal_loc]
	  
      location_delivery = min(canal.demand['contractor'][canal_loc]*demand_fraction_c + canal.demand['turnout'][canal_loc]*demand_fraction_t + canal.demand['excess'][canal_loc]*demand_fraction_e, canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc])

      x = self.canal_district[canal.name][canal_loc]

      if isinstance(x, District):
        #if location_delivery < x.dailydemand:
          #x.dailydemand -= location_delivery
        #elif location_delivery < x.dailydemand + max(x.in_district_storage - x.current_recharge_storage, 0.0):
          #x.current_recharge_storage += (location_delivery - x.dailydemand)
          #x.dailydemand = 0.0
        #else:
          #location_delivery = x.dailydemand + max(x.in_district_storage - x.current_recharge_storage, 0.0)
          #x.current_recharge_storage = x.in_district_storage
          #x.dailydemand = 0.0
        uncontrolled_deliveries = 0.0
        total_projected_allocation = 0.0
        total_deliveries = 0.0
        total_current_balance = 0.0
        total_remaining_carryover = 0.0
        for y in self.canal_contract[contract_canal]:
          #if (y.storage_pool[t] - y.pumping_turnback - y.annual_deliveries[wateryear]) > 0.1*y.total:
            #total_current_balance += max(x.current_balance[y.name], x.projected_supply[y.name], 0.0)
          #else:
          total_projected_allocation += max(x.projected_supply[y.name], 0.0)
          total_deliveries += x.delivery_carryover[y.name]
          total_current_balance += max(x.current_balance[y.name], 0.0)
          total_remaining_carryover += max(x.carryover[y.name] - x.deliveries[y.name][wateryear], 0.0)

        if x.annualdemand > 0.0:
          total_demand_met = min(max(total_projected_allocation/(x.annualdemand*x.surface_water_sa*x.seepage), 0.0), 1.0)
        else:
          total_demand_met = 1.0
        if x.must_fill == 0:
          if dowy < 242:
            demand_constraint = min(total_deliveries, x.dailydemand_start*x.surface_water_sa*x.seepage)
          else:
            if contract_canal == "fkc":
              demand_constraint = max(x.dailydemand_start*total_demand_met*x.surface_water_sa*x.seepage, 0.0)
            else:
              demand_constraint = max(x.dailydemand_start*x.surface_water_sa*x.seepage, 0.0)
        elif x.must_fill == 1:
          demand_constraint = x.dailydemand*x.seepage
        flood_need = total_projected_allocation - x.annualdemand - x.max_direct_recharge[0]*(365-dowy) - x.pre_flood_demand
        if x.seasonal_connection == 1 and total_remaining_carryover < x.dailydemand*x.seepage*x.surface_water_sa and flood_need < 0.0:
          #uncontrolled_deliveries = max(x.dailydemand*x.seepage - min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], x.dailydemand*x.seepage, demand_constraint, total_current_balance), 0.0)
          uncontrolled_deliveries = x.dailydemand*x.seepage*x.surface_water_sa
        else:
          uncontrolled_deliveries = 0.0


        if location_delivery < uncontrolled_deliveries:
          x.dailydemand -= location_delivery
        elif location_delivery < (uncontrolled_deliveries + max(x.in_district_storage - x.current_recharge_storage, 0.0)):
          x.dailydemand -= uncontrolled_deliveries
          x.current_recharge_storage += max(location_delivery - uncontrolled_deliveries, 0.0)
        else:
          location_delivery = uncontrolled_deliveries + max(x.in_district_storage - x.current_recharge_storage, 0.0)
          x.dailydemand -= uncontrolled_deliveries
          x.current_recharge_storage = x.in_district_storage
		  
        x.deliveries[delivery_key][wateryear] += location_delivery
		  
        total_current_balance = 0.0
        contractor_toggle = 0
        priority_toggle = 0
        for yy in self.get_iterable(self.canal_priority[canal.name]):
          if yy.name == contract_canal:
            priority_toggle = 1
        if priority_toggle == 1:
          for y in self.canal_contract[contract_canal]:
            for yx in x.contract_list:
              if y.name == yx:
                contractor_toggle = 1
          if contractor_toggle == 1:
          #canal.demand['contractor'][canal_loc] = x.dailydemand + max(x.in_district_storage - x.current_recharge_storage, 0.0)
            canal.demand['contractor'][canal_loc] = max(uncontrolled_deliveries - min(location_delivery, uncontrolled_deliveries)  + x.in_district_storage - x.current_recharge_storage, 0.0)

          else:
            #canal.demand['contractor'][canal_loc] = x.dailydemand + max(x.in_district_storage - x.current_recharge_storage, 0.0)
            canal.demand['turnout'][canal_loc] = max(x.in_district_storage - x.current_recharge_storage, 0.0)
        else:
          canal.demand['excess'][canal_loc] = max(uncontrolled_deliveries - min(location_delivery, uncontrolled_deliveries) + x.in_district_storage - x.current_recharge_storage, 0.0)

	  
      elif isinstance(x, Waterbank):
        total_contractor = 0.0
        total_turnout = 0.0
        total_excess = 0.0
        current_storage = 0.0
        for xx in x.participant_list:
          current_storage += x.storage[xx]
        if location_delivery > (x.tot_storage - current_storage):
          location_delivery = x.tot_storage - current_storage

        priority_toggle = 0
        for yy in self.get_iterable(self.canal_priority[canal.name]):
          if yy.name == contract_canal:
            priority_toggle = 1
        if priority_toggle == 1:
          for xx in x.participant_list:
            contractor_toggle = 0
            for wb_member in self.get_iterable(self.district_keys[xx]):
              for y in self.canal_contract[contract_canal]:
                for yx in wb_member.contract_list:
                  if y.name == yx:
                    contractor_toggle = 1
            if contractor_toggle == 1:
              total_contractor += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)
            else:
              total_turnout += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
        else:
          for xx in x.participant_list:
            total_excess += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
			
        if total_contractor >= location_delivery:
          if total_contractor > 0.0:		  
            turnout_frac_c = min(location_delivery/total_contractor, 1.0)
          else:
            turnout_frac_c = 0.0
          turnout_frac_t = 0.0
          turnout_frac_e = 0.0
        elif (total_contractor + total_turnout) >= location_delivery:
          turnout_frac_c = 1.0
          if total_turnout > 0.0:		  
            turnout_frac_t = min((location_delivery - total_contractor)/total_turnout, 1.0)
          else:
            turnout_frac_t = 0.0
          turnout_frac_e = 0.0
        elif (total_contractor + total_turnout + total_excess) >= location_delivery:
          turnout_frac_c = 1.0
          turnout_frac_t = 1.0
          if total_excess > 0.0:		  
            turnout_frac_e = min((location_delivery - total_contractor - total_turnout)/total_excess, 1.0)
          else:
            turnout_frac_e = 0.0

        else:
          turnout_frac_c = 1.0
          turnout_frac_t = 1.0
          turnout_frac_e = 1.0
          location_delivery = total_contractor + total_turnout + total_excess
        
        current_storage = 0.0
        canal.demand['contractor'][canal_loc] = 0.0
        canal.demand['turnout'][canal_loc] = 0.0
        canal.demand['excess'][canal_loc] = 0.0
        priority_toggle = 0
        for yy in self.get_iterable(self.canal_priority[canal.name]):
          if yy.name == contract_canal:
            priority_toggle = 1
        if priority_toggle == 1:
          for xx in x.participant_list:
            contractor_toggle = 0
            for wb_member in self.get_iterable(self.district_keys[xx]):
              for y in self.canal_contract[contract_canal]:
                for yx in wb_member.contract_list:
                  if y.name == yx:
                    contractor_toggle = 1
            if contractor_toggle == 1:
              wb_member.deliveries[delivery_key][wateryear] += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)*turnout_frac_c
              x.storage[xx] += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)*turnout_frac_c
              current_storage += x.storage[xx]
              canal.demand['contractor'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
            else:
              wb_member.deliveries[delivery_key][wateryear] += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)*turnout_frac_t
              x.storage[xx] += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)*turnout_frac_t
              current_storage += x.storage[xx]
              canal.demand['turnout'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)
        else:
          for xx in x.participant_list:
            for wb_member in self.get_iterable(self.district_keys[xx]):
              wb_member.deliveries[delivery_key][wateryear] += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)*turnout_frac_e
              x.storage[xx] += max(x.tot_storage*x.ownership[xx] - x.storage[xx],0.0)*turnout_frac_e
              current_storage += x.storage[xx]
              canal.demand['excess'][canal_loc] += max(x.tot_storage*x.ownership[xx] - x.storage[xx], 0.0)
            
        if canal.demand['contractor'][canal_loc] > (x.tot_storage - current_storage):
          canal.demand['contractor'][canal_loc] = x.tot_storage - current_storage
          canal.demand['turnout'][canal_loc] = 0.0
          canal.demand['excess'][canal_loc] = 0.0
        elif (canal.demand['turnout'][canal_loc] + canal.demand['contractor'][canal_loc])  > x.tot_storage - current_storage:
          canal.demand['turnout'][canal_loc] = x.tot_storage - current_storage - canal.demand['contractor'][canal_loc]
          canal.demand['excess'][canal_loc] = 0.0
        elif (canal.demand['turnout'][canal_loc] + canal.demand['contractor'][canal_loc] + canal.demand['excess'][canal_loc])  > x.tot_storage - current_storage:
          canal.demand['excess'][canal_loc] = x.tot_storage - current_storage - canal.demand['contractor'][canal_loc] - canal.demand['excess'][canal_loc]

      elif isinstance(x, Canal):
        
        new_flow_dir = canal.flow_directions[flow_type][x.name]
        new_canal_size = len(self.canal_district[x.name])
        if (canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc]) > 0.0 and location_delivery > 0.0:
          new_excess_flow, canal.demand['contractor'][canal_loc], canal.demand['turnout'][canal_loc], canal.demand['excess'][canal_loc] = self.deliver_flood_flows(dowy, x, canal.key, contract_canal, location_delivery, new_canal_size, wateryear, new_flow_dir, flow_type, delivery_key)
          location_delivery -= new_excess_flow
          if new_excess_flow > 0.0:
            canal.demand['contractor'][canal_loc] = 0.0
            canal.demand['turnout'][canal_loc] = 0.0
            canal.demand['excess'][canal_loc] = 0.0
        else:
          location_delivery = 0.0
		  
      canal.turnout_use[canal_loc] += location_delivery
      canal.flow[canal_loc] += available_flow
      available_flow -=  location_delivery
      convey_min = min(canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc], canal.capacity[flow_dir][canal_loc]*cfs_tafd - canal.flow[canal_loc])
      if canal.demand['contractor'][canal_loc] > convey_min:
        canal.demand['contractor'][canal_loc] = convey_min
        canal.demand['turnout'][canal_loc] = 0.0
        canal.demand['excess'][canal_loc] = 0.0
      elif canal.demand['contractor'][canal_loc] + canal.demand['turnout'][canal_loc] > convey_min:
        canal.demand['turnout'][canal_loc] = convey_min - canal.demand['contractor'][canal_loc]
        canal.demand['excess'][canal_loc] = 0.0
      elif (canal.demand['contractor'][canal_loc] + canal.demand['turnout'][canal_loc] + canal.demand['excess'][canal_loc]) > convey_min:
        canal.demand['excess'][canal_loc] = convey_min - canal.demand['contractor'][canal_loc] - canal.demand['excess'][canal_loc]

      if flow_dir == "normal":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc+1]*cfs_tafd + canal.flow[canal_loc+1],0.0)
      elif flow_dir == "reverse":
        turnback_flows = max(available_flow - canal.capacity[flow_dir][canal_loc-1]*cfs_tafd + canal.flow[canal_loc-1],0.0)
		
      if turnback_flows > 0.005:
        available_flow -= turnback_flows
        if flow_dir == "normal":
          turnback_end = canal_loc + 1
          for removal_flow in range((starting_point+1),canal_loc+1):
            canal.flow[removal_flow] -= turnback_flows

        elif flow_dir == "reverse":
          turnback_end = len(self.canal_district[canal.name]) - canal_loc - 1
          for removal_flow in range((starting_point-1),canal_loc-1,-1):
            canal.flow[removal_flow] -= turnback_flows

        remaining_excess_flow, unmet_contractor, unmet_turnout, unmet_excess = self.deliver_flood_flows(dowy, canal, prev_canal, contract_canal, turnback_flows, turnback_end, wateryear, flow_dir, flow_type, delivery_key)
        excess_flow += remaining_excess_flow
			
    unmet_contractor = 0.0
    unmet_turnout = 0.0
    unmet_excess = 0.0
    for canal_loc in canal_range:
      unmet_contractor += canal.demand['contractor'][canal_loc]
      unmet_turnout += canal.demand['turnout'][canal_loc]
      unmet_excess += canal.demand['excess'][canal_loc]

    return excess_flow, unmet_contractor, unmet_turnout, unmet_excess

	
  def route_recovery(self, canal, exchange_contract, flow_dir, flow_type, prev_canal, delivery_key, wateryear, dowy):
    canal_size = len(self.canal_district[canal.name])
    if flow_dir == "normal":
      starting_point = 0
      if prev_canal == "none":
        canal_range = range(starting_point,canal_size)
      else:
        for x in range(starting_point,canal_size):
          canal_member = self.canal_district[canal.name][x]
          if canal_member.key == prev_canal:
            break
        ending_point = x
        if x == starting_point:
          return 0.0
        canal_range = range(starting_point,ending_point)
    elif flow_dir == "reverse":
      starting_point = len(self.canal_district[canal.name]) - 1
      if prev_canal == "none":
        canal_range = range(starting_point,-1,-1)
      else:
        for x in range(starting_point,-1,-1):
          canal_member = self.canal_district[canal.name][x]
          if canal_member.key == prev_canal:
            break
        if x == starting_point:
          return 0.0
        ending_point = x
        canal_range = range(starting_point,ending_point,-1)
    else:
      return 0.0
	  
    canal.supplies = np.zeros(canal_size)
    total_recovery = 0.0
    for canal_loc in canal_range:
      x = self.canal_district[canal.name][canal_loc]
      if isinstance(x,Waterbank):
        tot_supplies = 0.0
        tot_excess_storage = 0.0
        excess_storage = 0.0
        for xx in x.participant_list:
          supply_deficit = 0.0
          member_trades = 0
          if x.delivery_type[xx] == "direct":
            member_trades = 1
          for wb_member in self.get_iterable(self.district_keys[xx]):
            for member_contracts in self.get_iterable(wb_member.contract_list):
              if member_contracts == exchange_contract:
                member_trades = 1
          if member_trades == 1:
            for wb_member in self.get_iterable(self.district_keys[xx]):
              if wb_member.use_recovery == 1.0:
                supply_deficit += max(wb_member.dailydemand,0.0)
            member_recover = max(min(x.banked[xx],supply_deficit),0.0)
          else:
            member_recover = 0.0
          excess_storage = 0.0
          if member_recover > (x.ownership[xx]*x.recovery - x.recovery_use[xx]):
            excess_storage = member_recover - max(x.ownership[xx]*x.recovery - x.recovery_use[xx], 0.0)
            member_recover = max(x.ownership[xx]*x.recovery - x.recovery_use[xx], 0.0)
            tot_excess_storage += excess_storage
			
          x.recovery_use[xx] += member_recover
          x.additional_supplies[xx] = excess_storage
          tot_supplies += member_recover

		  
        max_outflow = min(x.recovery-x.tot_recovery_use,canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc])

        if tot_supplies > max_outflow:
          total_over = 0.0
          for xx in x.participant_list:
            total_over += max(x.recovery_use[xx] - x.ownership[xx]*x.recovery, 0.0)
          if total_over > 0.0:
            over_frac = min((tot_supplies - max_outflow)/total_over, 1.0)
          else:
            over_frac = 0.0
          for xx in x.participant_list:
            x.recovery_use[xx] -= max(x.recovery_use[xx] - x.ownership[xx]*x.recovery, 0.0)*over_frac
          excess_reduction = max(tot_supplies - max_outflow - total_over, 0.0)
          for xx in x.participant_list:
            if (x.recovery + excess_reduction > 0.0):
              x.recovery_use[xx] = x.recovery_use[xx]*x.recovery/(excess_reduction+x.recovery)
          tot_supplies = max_outflow
        elif tot_supplies < max_outflow and tot_excess_storage > 0.0:
          excess_storage_fraction = min((max_outflow - tot_supplies)/tot_excess_storage,1.0)
          tot_supplies += min((max_outflow - tot_supplies),tot_excess_storage)
          for xx in x.participant_list:
            x.recovery_use[xx] += excess_storage_fraction*x.additional_supplies[xx]
			
        x.tot_recovery_use += tot_supplies
        canal.supplies[canal_loc] = tot_supplies		        
        total_recovery += tot_supplies
		
      elif isinstance(x,District):
        direct_delivery = self.find_direct_recovery(canal,x.key,x,flow_dir,flow_type,delivery_key,wateryear)
        total_recovery -= direct_delivery
        paper_delivery = self.find_paper_recovery(total_recovery,exchange_contract,canal,x.key,x,flow_dir,flow_type,delivery_key,wateryear)
        total_recovery -= paper_delivery
        canal.supplies[canal_loc] = 0.0
        if x.in_leiu_banking:
          tot_supplies = 0.0
          tot_excess_storage = 0.0
          excess_storage = 0.0
          for xx in x.participant_list:
            supply_deficit = 0.0
            member_trades = 0
            if x.leiu_delivery_type[xx] == "direct":
              member_trades = 1
            for wb_member in self.get_iterable(self.district_keys[xx]):
              for member_contracts in self.get_iterable(wb_member.contract_list):
                if member_contracts == exchange_contract:
                  member_trades = 1
            if member_trades == 1:
              for wb_member in self.get_iterable(self.district_keys[xx]):
                if wb_member.use_recovery == 1.0:
                  supply_deficit += max(wb_member.dailydemand,0.0)
              member_recover = max(min(x.inleiubanked[xx],supply_deficit),0.0)
            else:
              member_recover = 0.0
            excess_storage = 0.0
            if member_recover > (x.leiu_ownership[xx]*x.leiu_recovery - x.leiu_recovery_use[xx]):
              excess_storage = member_recover - max(x.leiu_ownership[xx]*x.leiu_recovery - x.leiu_recovery_use[xx], 0.0)
              member_recover = max(x.leiu_ownership[xx]*x.leiu_recovery - x.leiu_recovery_use[xx], 0.0)
              tot_excess_storage += excess_storage
			
            x.leiu_recovery_use[xx] += member_recover
            x.leiu_additional_supplies[xx] = excess_storage
            tot_supplies += member_recover
            max_outflow = min(x.leiu_recovery-x.tot_leiu_recovery_use,canal.turnout[flow_dir][canal_loc]*cfs_tafd - canal.turnout_use[canal_loc])

          if tot_supplies > max_outflow:
            total_over = 0.0
            for xx in x.participant_list:
              total_over += max(x.leiu_recovery_use[xx] - x.leiu_ownership[xx]*x.leiu_recovery, 0.0)
            if total_over > 0.0:
              over_frac = min((tot_supplies - max_outflow)/total_over, 1.0)
            else:
              over_frac = 0.0
            for xx in x.participant_list:
              x.leiu_recovery_use[xx] -= max(x.leiu_recovery_use[xx] - x.leiu_ownership[xx]*x.leiu_recovery, 0.0)*over_frac
            excess_reduction = max(tot_supplies - max_outflow - total_over, 0.0)
            for xx in x.participant_list:
              if (x.leiu_recovery + excess_reduction > 0.0):
                x.leiu_recovery_use[xx] = x.leiu_recovery_use[xx]*x.leiu_recovery/(excess_reduction+x.leiu_recovery)
            tot_supplies = max_outflow
          elif tot_supplies < max_outflow and tot_excess_storage > 0.0:
            excess_storage_fraction = min((max_outflow - tot_supplies)/tot_excess_storage,1.0)
            tot_supplies += min((max_outflow - tot_supplies),tot_excess_storage)
            for xx in x.participant_list:
              x.leiu_recovery_use[xx] += excess_storage_fraction*x.leiu_additional_supplies[xx]
			
          x.tot_leiu_recovery_use += tot_supplies
          canal.supplies[canal_loc] = tot_supplies		        
          total_recovery += tot_supplies	
          for xx in x.participant_list:
            for wb_member in self.get_iterable(self.district_keys[xx]):
              if wb_member.use_recovery == 1.0:
                if x.leiu_recovery_use[xx] < wb_member.dailydemand:
                  trading_partner = 0.0
                  for member_contracts in self.get_iterable(wb_member.contract_list):
                    if member_contracts == exchange_contract:
                      trading_partner = 1.0
                  max_to_trade = x.projected_supply[exchange_contract] + x.deliveries[exchange_contract][wateryear] - x.paper_balance[exchange_contract]
                  max_leiu_paper = max(max_to_trade*x.leiu_trade_cap + x.paper_balance[exchange_contract],0.0)/(366-dowy)
                  delivery_amount = max(min(wb_member.dailydemand - x.leiu_recovery_use[xx], max(x.current_balance[exchange_contract], 0.0), x.inleiubanked[xx],max_leiu_paper*x.leiu_ownership[xx]),0.0)
                  wb_member.paper_balance[exchange_contract] += delivery_amount
                  x.paper_balance[exchange_contract] -= delivery_amount
                  x.deliveries['leiupumping'][wateryear] += delivery_amount

					
      elif isinstance(x,Canal):  
        flow_dir_new = canal.flow_directions[flow_type][x.name]
        canal.supplies[canal_loc] = self.route_recovery(x,exchange_contract,flow_dir_new,flow_type,canal.key,delivery_key,wateryear,dowy)
        total_recovery += canal.supplies[canal_loc]

      if flow_dir == "normal":
        turnback_flows = max(total_recovery - canal.capacity[flow_dir][canal_loc+1]*cfs_tafd + canal.flow[canal_loc + 1],0.0)
        end_point = canal_loc + 1
      elif flow_dir == "reverse":
        turnback_flows = max(total_recovery - canal.capacity[flow_dir][canal_loc]*cfs_tafd + canal.flow[canal_loc],0.0)
        end_point = canal_loc - 1
      if turnback_flows > 0.0:
        if total_recovery > 0.0:
          turnback_frac = turnback_flows/total_recovery
        else:
          turnback_frac = 0.0		
        self.turnback_canal_recovery(turnback_frac,canal,x.key,flow_dir,flow_type)
      else:
        turnback_flows = 0.0
      total_recovery -= turnback_flows
    if prev_canal == "none":
      turback_flows = total_recovery
      if turnback_flows > 0.0:
        turnback_frac = 1.0
        self.turnback_canal_recovery(turnback_frac, canal, "none", flow_dir, flow_type)
    return total_recovery		
                
  def find_direct_recovery(self,canal,prev_object,recovery_destination,flow_dir,flow_type,delivery_key,wateryear):
    canal_size = len(self.canal_district[canal.name])
    if flow_dir == "normal":
      starting_point = 0
      for x in range(starting_point,canal_size):
        canal_member = self.canal_district[canal.name][x]
        if canal_member.key == prev_object:
          break
      if x == starting_point:
        return 0.0
      ending_point = x
      canal_range = range(starting_point,ending_point)
    elif flow_dir == "reverse":
      starting_point = len(self.canal_district[canal.name]) - 1
      for x in range(starting_point,-1,-1):
        canal_member = self.canal_district[canal.name][x]
        if canal_member.key == prev_object:
          break
      if x == starting_point:
        return 0.0
      ending_point = x
      canal_range = range(starting_point,ending_point,-1)
    else:
      return 0.0
    total_delivery = 0.0
    for y in canal_range:
      source_object = self.canal_district[canal.name][y]
      if isinstance(source_object,District):
        if source_object.in_leiu_banking:
          if recovery_destination.key in source_object.participant_list:
            delivery_amount = min(recovery_destination.dailydemand, source_object.leiu_recovery_use[recovery_destination.key] - source_object.bank_deliveries[recovery_destination.key])
            source_object.bank_deliveries[recovery_destination.key] += delivery_amount
            total_delivery += delivery_amount
            source_object.inleiubanked[recovery_destination.key] -= delivery_amount
            source_object.deliveries['leiupumping'][wateryear] += delivery_amount
            recovery_destination.dailydemand -= delivery_amount
            recovery_destination.deliveries[delivery_key][wateryear] += delivery_amount
            canal.supplies[y] -= delivery_amount			
      elif isinstance(source_object,Waterbank):
        if recovery_destination.key in source_object.participant_list:
          delivery_amount = min(recovery_destination.dailydemand,source_object.recovery_use[recovery_destination.key] - source_object.bank_deliveries[recovery_destination.key])
          source_object.bank_deliveries[recovery_destination.key] += delivery_amount
          total_delivery += delivery_amount
          source_object.banked[recovery_destination.key] -= delivery_amount
          recovery_destination.dailydemand -= delivery_amount
          recovery_destination.deliveries[delivery_key][wateryear] += delivery_amount
          canal.supplies[y] -= delivery_amount

      elif isinstance(source_object,Canal):
        flow_dir = canal.flow_directions[flow_type][source_object.name]
        object_delivery = self.find_direct_recovery(source_object,canal.key,recovery_destination,flow_dir,flow_type,delivery_key,wateryear)
        canal.supplies[y] -= object_delivery
        total_delivery += object_delivery
      #canal.flow[y] += total_delivery
	  
    return total_delivery
	
  def find_paper_recovery(self,total_recovery,exchange_contract,canal,prev_object,recovery_destination,flow_dir,flow_type,delivery_key,wateryear):
    canal_size = len(self.canal_district[canal.name])
    if flow_dir == "normal":
      starting_point = 0
      for x in range(starting_point,canal_size):
        canal_member = self.canal_district[canal.name][x]
        if canal_member.key == prev_object:
          break
      if x == starting_point:
        return 0.0
      ending_point = x
      canal_range = range(starting_point,ending_point)
    elif flow_dir == "reverse":
      starting_point = len(self.canal_district[canal.name]) - 1
      for x in range(starting_point,-1,-1):
        canal_member = self.canal_district[canal.name][x]
        if canal_member.key == prev_object:
          break
      if x == starting_point:
        return 0.0
      ending_point = x
      canal_range = range(starting_point,ending_point,-1)
    else:
      return 0.0
    total_delivery = 0.0
    node_demand = recovery_destination.dailydemand
    trade_balance = max(recovery_destination.current_balance[exchange_contract], 0.0)
    total_request = min(node_demand,trade_balance,total_recovery)

    if total_request > 0.0:
      for y in canal_range:
        source_object = self.canal_district[canal.name][y]
        if isinstance(source_object,District):
          if source_object.in_leiu_banking:
            for xx in source_object.participant_list:
              num_members = len(self.get_iterable(self.district_keys[xx]))
              mult_delivery = 0.0
              for wb_member in self.get_iterable(self.district_keys[xx]):
                trading_partner = 0.0
                for member_contracts in self.get_iterable(wb_member.contract_list):
                  if member_contracts == exchange_contract:
                    trading_partner = 1.0
                delivery_amount = trading_partner * min(max(recovery_destination.dailydemand - recovery_destination.min_direct_recovery,0.0), max(total_request/total_recovery, 1.0)*(source_object.leiu_recovery_use[xx] - source_object.bank_deliveries[xx]), max(recovery_destination.current_balance[exchange_contract],0.0))/num_members
                mult_delivery += delivery_amount
                wb_member.paper_balance[exchange_contract] += delivery_amount
                wb_member.deliveries['exchanged_GW'][wateryear] += delivery_amount
				
              source_object.bank_deliveries[xx] += mult_delivery
              total_delivery += mult_delivery
              source_object.inleiubanked[xx] -= mult_delivery
              source_object.deliveries['leiupumping'][wateryear] += mult_delivery
              recovery_destination.paper_balance[exchange_contract] -= mult_delivery
              recovery_destination.dailydemand -= mult_delivery
              recovery_destination.deliveries[delivery_key][wateryear] += mult_delivery
              recovery_destination.deliveries['exchanged_SW'][wateryear] += mult_delivery
              canal.supplies[y] -= mult_delivery
			  
        elif isinstance(source_object,Waterbank):
          for xx in source_object.participant_list:
            num_members = len(self.get_iterable(self.district_keys[xx]))
            mult_delivery = 0.0
            for wb_member in self.get_iterable(self.district_keys[xx]):
              trading_partner = 0.0
              for member_contracts in self.get_iterable(wb_member.contract_list):
                if member_contracts == exchange_contract:
                  trading_partner = 1.0
              delivery_amount = trading_partner * min(recovery_destination.dailydemand, max(total_request/total_recovery,1.0)*(source_object.recovery_use[xx] - source_object.bank_deliveries[xx]), max(recovery_destination.current_balance[exchange_contract], 0.0))/num_members
              mult_delivery += delivery_amount
              wb_member.paper_balance[exchange_contract] += delivery_amount
              wb_member.deliveries['exchanged_GW'][wateryear] += delivery_amount
			  
            source_object.bank_deliveries[xx] += mult_delivery
            total_delivery += mult_delivery
            source_object.banked[xx] -= mult_delivery
            recovery_destination.paper_balance[exchange_contract] -= mult_delivery
            recovery_destination.dailydemand -= mult_delivery
            recovery_destination.deliveries[delivery_key][wateryear] += mult_delivery
            recovery_destination.deliveries['exchanged_SW'][wateryear] += mult_delivery
            canal.supplies[y] -= mult_delivery
			  
        elif isinstance(source_object,Canal):
          flow_dir = canal.flow_directions[flow_type][source_object.name]
          object_delivery = self.find_paper_recovery(total_recovery, exchange_contract, source_object, canal.key, recovery_destination, flow_dir,flow_type,delivery_key,wateryear)
          canal.supplies[y] -= object_delivery
          total_delivery += object_delivery
        #canal.flow[y] += total_delivery
    return total_delivery	  
  
  def turnback_canal_recovery(self,turnback,canal,prev_object,flow_dir,flow_type):
    canal_size = len(self.canal_district[canal.name])
    if flow_dir == "normal":
      starting_point = 0
      canal_range = range(starting_point,canal_size)
    elif flow_dir == "reverse": 
      starting_point = canal_size - 1
      canal_range = range(starting_point,-1,-1)
    elif flow_dir == "closed":
      return
	  
    for y in range(starting_point,canal_size):
      return_object = self.canal_district[canal.name][y]
      if return_object.key == prev_object:
        break
      
      new_object = self.canal_district[canal.name][y]
      if new_object.key == prev_object:
        break
      if isinstance(new_object, Canal):
        flow_dir = canal.flow_directions[flow_type][new_object.name]
        self.turnback_canal_recovery(turnback,new_object,canal.key,flow_dir,flow_type)
      elif isinstance(new_object, Waterbank):
        for xx in new_object.participant_list:
          member_turnback = (new_object.recovery_use[xx] - new_object.bank_deliveries[xx])*turnback
          new_object.recovery_use[xx] -= member_turnback
          canal.supplies[y] -= member_turnback
          new_object.tot_recovery_use -= member_turnback
      elif isinstance(new_object,District):
        if new_object.in_leiu_banking:
          for xx in new_object.participant_list:
            member_turnback = (new_object.leiu_recovery_use[xx] - new_object.bank_deliveries[xx])*turnback
            new_object.leiu_recovery_use[xx] -= member_turnback
            canal.supplies[y] -= member_turnback
            new_object.tot_leiu_recovery_use -= member_turnback
			
  def find_turnback_pool(self, t):
    ##This function creates the 'turnback pool' (note: only for SWP contracts now, can be used for others)
    ##finding contractors with 'extra' contract water that they would like to sell, and contractors who would
    ##like to purchase that water.  
    turnback_sellers = 0.0
    turnback_buyers = 0.0
    for x in self.district_list:
      for y in x.contract_list:
        if y == "tableA":
          total_recharge_ability =  x.max_direct_recharge[0]*30.0 + x.max_direct_recharge[1]*31.0 + x.max_direct_recharge[2]*31.0 + x.max_direct_recharge[3]*30.0 + x.max_direct_recharge[4]*31.0 + x.max_direct_recharge[5]*30.0 + x.max_direct_recharge[6]*31.0
          total_projected_supply = 0.0
          for yy in x.contract_list:
            total_projected_supply += x.projected_supply[yy]
          #districts sell water if their projected contracts are greater than their remaining annual demand, plus their remaining recharge capacity in this water year, plus their recharge capacity in the next water year (through January)
          turnback_sellers += max(total_projected_supply - x.annualdemand - total_recharge_ability - x.pre_flood_demand, 0.0)
          #districts don't buy extra water if they have an in-lieu banking program (b/c they can just accept the extra water from banking partners)
          if x.in_leiu_banking:
            turnback_buyers += 0.0
          else:
            ##districts buy turnback water if their annual demands are greater than their projected supply plus their capacity to recover banked groundwater
            turnback_buyers += max(x.annualdemand - total_projected_supply - x.max_recovery*122, 0.0)
    #once we know how much water is in the 'selling' pool and the 'buying' pool, we can determine the total turnback pool - min(buying,selling), then
    #determine what % of each request is filled (i.e., if the selling pool is only 1/2 of the buying pool, then buyers only get 1/2 of their request, or visa versa	
    if min(turnback_sellers, turnback_buyers) > 0.0:
      sellers_frac = -1*min(turnback_sellers, turnback_buyers)/turnback_sellers
      buyers_frac = min(turnback_sellers, turnback_buyers)/turnback_buyers
      for x in self.district_list:
        for y in x.contract_list:
          #the buying/selling fractiosn are applied to the same calculations above (about buying or selling needs), and then turnback pools are added/subtracted to the districts contract
          if y == "tableA":
            total_recharge_ability =  x.max_direct_recharge[0]*30.0 + x.max_direct_recharge[1]*31.0 + x.max_direct_recharge[2]*31.0 + x.max_direct_recharge[3]*30.0 + x.max_direct_recharge[4]*31.0 + x.max_direct_recharge[5]*30.0 + x.max_direct_recharge[6]*31.0
            total_projected_supply = 0.0
            for yy in x.contract_list:
              total_projected_supply += x.projected_supply[yy]
            if total_projected_supply - x.annualdemand - total_recharge_ability - x.pre_flood_demand > 0.0:
              x.turnback_pool[y] = max(total_projected_supply - x.annualdemand - total_recharge_ability - x.pre_flood_demand, 0.0)*sellers_frac
            elif x.annualdemand - total_projected_supply - x.max_recovery*122 > 0.0:
              if x.in_leiu_banking:
                x.turnback_pool[y] = 0.0
              else:
                x.turnback_pool[y] = max(x.annualdemand - total_projected_supply - x.max_recovery*122, 0.0)*buyers_frac


  def reservoir_results_as_df(self):
    #df = pd.DataFrame()
    #for x in self.district_list:
      #df = pd.concat([df, x.results_as_df()], axis=1)
    #return df
	
    df = pd.DataFrame()
    names = ['SLS', 'SLF', 'MIL', 'ISB']
    things = [self.sanluisstate.S, self.sanluisfederal.S, self.millerton.S, self.isabella.S]
    for n,t in zip(names,things):
      df[n] = pd.Series(t)
    return df

  def swp_delivery_type_as_df(self):
    df = pd.DataFrame()
    names = ['tableA', 'carryover', 'turnback', 'article21']
    for n in names:
      df[n] = pd.Series(self.annual_SWP_delivery_type[n])
	  
    return df
	  
  def annual_results_as_df(self):
    df = pd.DataFrame()
    df = pd.Series(self.annual_SWP)
    for x in self.district_list:
      df = pd.concat([df, x.annual_results_as_df()], axis = 1)

    return df
