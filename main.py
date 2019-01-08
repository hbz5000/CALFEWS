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

startTime = datetime.now()

model_mode = 'simulation'
#model_mode = 'validation'
if model_mode == 'simulation':
  sd = '10-01-1905'
  input_data_file = 'cord/data/cord-data-sim.csv'
else:
  sd = '10-01-1996'
  input_data_file = 'cord/data/cord-data.csv'  

# always use shorter dataframe for expected delta releases
expected_release_datafile = 'cord/data/cord-data.csv'

# To run full dataset, short_test = -1. Else enter number of days to run, starting at sd. e.g. 365 for 1 year only.
short_test = 730

######################################################################################
# Model Class Initialization
## There are two instances of the class 'Model', one for the Nothern System and one for the Southern System
## 
modelno = Model(input_data_file, expected_release_datafile, sd, short_test)
modelso = Model(input_data_file, expected_release_datafile, sd, short_test)
print (modelno.df.shape[0], ' rows')
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
modelno.initialize_northern_res(model_mode)
print('Initialize Northern Reservoirs, time ', datetime.now() - startTime)
#initialize delta rules, calcluate expected environmental releases at each reservoir
#generates - cumulative environmental/delta releases remaining (at each reservoir)
#self.res.cum_min_release; self.res.aug_sept_min_release; self.res.oct_nov_min_release
modelno.initialize_delta_ops(model_mode)
modelso.omr_rule_start = modelno.delta.omr_rule_start
print('Initialize Delta Ops, time ', datetime.now() - startTime)

######
#calculate projection-based flow year indicies using flow & snow inputs
##note: these values are pre-processed, but represent no 'foresight' WYT & WYI index use
#snow-based projections to forecast flow, calculate running WY index & WYT
#generates:
#self.delta.forecastSJI (self.T x 1) - forecasts for san joaquin river index
#self.delta.forecastSRI (self.T x 1) - forecasts for sacramento river index
#if model_mode == 'simulation':
  #water_year_indicies = pd.read_csv('cord/data/water_year_index_simulation.csv')
  #modelno.delta.forecastSRI = water_year_indicies['SRI']
  #modelno.delta.forecastSJI = water_year_indicies['SJI']
#else:
modelno.find_running_WYI()
print('Find Water Year Indicies, time ', datetime.now() - startTime)

######
#calculate expected 'unstored' pumping at the delta (for predictions into San Luis)
#this generates:
#self.delta_gains_regression (365x2) - linear coeffecicients for predicting total unstored pumping, oct-mar, based on ytd full natural flow
#self.delta_gains_regression2 (365x2) - linear coeffecicients for predicting total unstored pumping, apr-jul, based on ytd full natural flow
#self.month_averages (12x1) - expected fraction of unstored pumping to come in each month (fraction is for total period flow, so 0.25 in feb is 25% of total oct-mar unstored flow)
modelno.predict_delta_gains()
print('Find Delta Gains, time ', datetime.now() - startTime)
if model_mode == 'simulation':
  modelno.set_regulations_current_north()
######################################################################################

######################################################################################
#preprocessing for the southern system
######################################################################################
###model.max_tax_free measures how much pumping can occur w/o additional releases for
###delta inflows (based on delta outflow requirements) from a given dowy until the end
###of the water year.  it is calculated in northern pre-processing but also passed to the
###southern model
modelso.max_tax_free = {}
modelso.max_tax_free = modelno.delta.max_tax_free
#initialize the southern reservoirs -
#generates - same values as initialize_northern_res(), but for southern reservoirs
modelso.initialize_southern_res(model_mode)
print('Initialize Southern Reservoirs, time ', datetime.now() - startTime)
#initialize water districts for southern model 
#generates - water district parameters (see cord-combined/cord/districts/readme.txt)
#self.district_list - list of district objects
#self.district_keys - dictionary pairing district keys w/district class objects
modelso.initialize_water_districts()
print('Initialize Water Districts, time ', datetime.now() - startTime)
#initialize water contracts for southern model
#generates - water contract parameters (see cord-combined/cord/contracts/readme.txt)
#self.contract_list - list of contract objects
#self.contract_keys - dictionary pairing contract keys w/contract class objects
#self.res.contract_carryover_list - record of carryover space afforded to each contract (for all district)
modelso.initialize_sw_contracts()
print('Initialize Contracts, time ', datetime.now() - startTime)
#initialize water banks for southern model
#generates - water bank parameters (see cord-combined/cord/banks/readme.txt)
#self.waterbank_list - list of waterbank objects
#self.leiu_list - list of district objects that also operate as 'in leiu' or 'direct recharge' waterbanks
modelso.initialize_water_banks()
print('Initialize Water Banks, time ', datetime.now() - startTime)
#initialize canals/waterways for southern model
#generates - canal parameters (see cord-combined/cord/canals/readme.txt)
#self.canal_list - list of canal objects
modelso.initialize_canals()
print('Initialize Canals, time ', datetime.now() - startTime)
if model_mode == 'simulation':
  modelso.set_regulations_current_south()

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
modelso.create_object_associations()
print('Create Object Associations, time ', datetime.now() - startTime)
###Applies initial carryover balances to districts
##based on initial reservoir storage conditions
##PLEASE NOTE CARRYOVER STORAGE IN SAN LUIS IS HARD-CODED
modelso.find_initial_carryover()
print('Initialize Carryover Storage, time ', datetime.now() - startTime)
##initial recovery capacities for districts, based on
##ownership stakes in waterbanks (direct + inleui)
modelso.init_tot_recovery()
print('Initialize Recovery Capacity, time ', datetime.now() - startTime)
##initial recharge capacities (projected out 12 months) for districts,
##based on ownership stakes in waterbanks (direct + inleui + indistrict)
urban_datafile = 'cord/data/cord-data-urban.csv'
urban_datafile_cvp = 'cord/data/pump-data-cvp.csv'
modelso.project_urban(urban_datafile, urban_datafile_cvp, model_mode)

#calculate how much recharge capacity is reachable from each reservoir 
#that is owned by surface water contracts held at that reservoir - used to determine
#how much flood water can be released and 'taken' by a contractor
modelso.find_all_triggers()
print('Find Triggers, time ', datetime.now() - startTime)

######################################################################################

######################################################################################
###Model Simulation
######################################################################################
timeseries_length = min(modelno.T, modelso.T)
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
  #the northern model takes variables from the southern model as inputs (initialized above), & outputs are used as input variables in the southern model
  swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF ,swp_AS, cvp_AS, flood_release, flood_volume = modelno.simulate_north(t, swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump, model_mode)
  
  swp_release, cvp_release, swp_release2, cvp_release2, swp_pump, cvp_pump = modelso.simulate_south(t, swp_pumping, cvp_pumping, swp_alloc, cvp_alloc, proj_surplus, max_pumping, swp_forgo, cvp_forgo, swp_AF, cvp_AF, swp_AS, cvp_AS, modelno.delta.forecastSJWYT, modelno.delta.max_tax_free, flood_release, flood_volume, model_mode)
######################################################################################

######################################################################################
###Record Simulation Results
######################################################################################
district_results = modelso.results_as_df('daily', modelso.district_list)
district_results.to_csv('cord/data/district_results_' + model_mode + '.csv')
district_results_annual = modelso.results_as_df('annual', modelso.district_list)
district_results_annual.to_csv('cord/data/annual_district_results_' + model_mode + '.csv')

contract_results = modelso.results_as_df('daily', modelso.contract_list)
contract_results.to_csv('cord/data/contract_results_' + model_mode + '.csv')
contract_results_annual = modelso.results_as_df('annual', modelso.contract_list)
contract_results_annual.to_csv('cord/data/contract_results_annual_' + model_mode + '.csv')

northern_res_list = [modelno.shasta, modelno.folsom, modelno.oroville, modelno.yuba, modelno.newmelones, modelno.donpedro, modelno.exchequer, modelno.delta]
southern_res_list = [modelso.sanluisstate, modelso.sanluisfederal, modelso.millerton, modelso.isabella]

reservoir_results_no = modelno.results_as_df('daily', northern_res_list)
reservoir_results_no.to_csv('cord/data/reservoir_results_no_' + model_mode + '.csv')
reservoir_results_so = modelso.results_as_df('daily', southern_res_list)
reservoir_results_so.to_csv('cord/data/reservoir_results_so_' + model_mode + '.csv')

canal_results = modelso.results_as_df('daily', modelso.canal_list)
canal_results.to_csv('cord/data/canal_results_' + model_mode + '.csv')

bank_results = modelso.bank_as_df('daily', modelso.waterbank_list)
bank_results.to_csv('cord/data/bank_results_' + model_mode + '.csv')
bank_results_annual = modelso.bank_as_df('annual', modelso.waterbank_list)
bank_results_annual.to_csv('cord/data/bank_results_annual_' + model_mode + '.csv')


leiu_results = modelso.bank_as_df('daily', modelso.leiu_list)
leiu_results.to_csv('cord/data/leiu_results_' + model_mode + '.csv')
leiu_results_annual = modelso.bank_as_df('annual', modelso.leiu_list)
leiu_results_annual.to_csv('cord/data/leiu_results_annual_' + model_mode + '.csv')

print ('completed in ', datetime.now() - startTime)



