# cython: profile=True
import numpy as np 
import matplotlib.pyplot as plt
import collections as cl
import pandas as pd
from .scenario import Scenario
import json
from .util import *
from .crop_cy cimport Crop
from .canal_cy cimport Canal
from .contract_cy cimport Contract



cdef class District():

  def __iter__(self):
    self.iter_count = 0
    return self
  
  def __next__(self):
    if self.iter_count == 0:
      self.iter_count += 1
      return self
    else:
      raise StopIteration

  def __len__(self):
    return 1

  def __init__(self, model, name, key, scenario_file = 'baseline'):
    self.is_Canal = 0
    self.is_District = 1
    self.is_Private = 0
    self.is_Waterbank = 0
    self.is_Reservoir = 0

    self.T = model.T
    self.key = key
    self.name = name

    for k, v in json.load(open('calfews_src/districts/%s_properties.json' % key)).items():
      setattr(self, k, v)
    if ((scenario_file == 'baseline') == False):
      for k,v in json.load(open(scenario_file)).items():
        setattr(self,k,v)

    #intialize crop acreages and et demands for crops
    self.irrdemand = Crop(self.zone)
	  #initialize dictionary to hold different delivery types
    self.deliveries = {}
    self.contract_list_all = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2','kaweah', 'tule', 'kern','kings']
    self.non_contract_delivery_list = ['recover_banked','inleiu_irrigation','inleiu_recharge','leiupumping','exchanged_GW','exchanged_SW','undelivered_trades']

    for x in self.contract_list_all:
      #normal contract deliveries
      self.deliveries[x] = np.zeros(model.number_years)
	    #uncontrolled deliveries from contract
      self.deliveries[x + '_flood'] = np.zeros(model.number_years)
      # contract-specific recharge (same as 'recharged', but disaggregated)
      self.deliveries[x + '_recharged'] = np.zeros(model.number_years)
      #deliveries from a groundwater bank (reocrded by banking partner recieving recovery water)
      self.deliveries[x+ '_flood_irrigation'] = np.zeros(model.number_years)
  	#deliveries from a groundwater bank (reocrded by banking partner recieving recovery water)
    self.deliveries['recover_banked'] = np.zeros(model.number_years)
  	#deliveries to a in-leiu bank from a banking partner (recorded by the district acting as a bank)
    self.deliveries['inleiu_irrigation'] = np.zeros(model.number_years)
    self.deliveries['inleiu_recharge'] = np.zeros(model.number_years)

	  #deliveries from an in leiu bank to a banking partner (recorded by the district acting as a bank)
    self.deliveries['leiupumping'] = np.zeros(model.number_years)
    #deliveries made from a districts bank to third-party district (district recieves a surface water 'paper' credit)
    self.deliveries['exchanged_GW'] = np.zeros(model.number_years)
    #recorded when a district recieves water from a bank owned by another district (district gives a surface water 'paper' credit)
    self.deliveries['exchanged_SW'] = np.zeros(model.number_years)
    self.deliveries['undelivered_trades'] = np.zeros(model.number_years)
	
    #set dictionaries to keep track of different 'color' water for each contract
    self.current_balance = {}#contract water currently available in surface water storage
    self.paper_balance = {}#balance (positive) or negative of paper trades made from groundwater banks
    self.turnback_pool = {}#water purchased from intra-contract marketes (June 1st)
    self.projected_supply = {}#projected annual allocation to each contract
    self.carryover = {}#water 'carried over' in surface water storage from previous year's contract
    self.recharge_carryover = {}#amount of water that the district wants to request contract deliveries for recharge
    self.delivery_carryover = {}#amount of water to deliver immediately becuase of surface storage spillage
    self.contract_carryover_list = {}#maximum carryover storage on contract
    self.carryover['tot'] = 0.0
    self.projected_supply['tot'] = 0.0
    self.dynamic_recharge_cap ={}
    self.days_to_fill = {}
    #initialize values for all contracts in dictionaries
    for y in self.contract_list_all:
      self.current_balance[y] = 0.0
      self.paper_balance[y] = 0.0
      self.turnback_pool[y] = 0.0
      self.projected_supply[y] = 0.0
      self.carryover[y] = 0.0
      self.recharge_carryover[y] = 0.0
      self.delivery_carryover[y] = 0.0
      self.contract_carryover_list[y] = 0.0
      self.dynamic_recharge_cap[y] = 999.0
      self.days_to_fill[y] = 999.0
	  
    # hold all output
    self.daily_supplies_full = {}
    # delivery_list = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2','kaweah', 'tule', 'kern']
    # for x in self.contract_list_all:
    #   self.daily_supplies_full[x + '_delivery'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_flood'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_flood_irrigation'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_recharged'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_projected'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_paper'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_carryover'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_turnback'] = np.zeros(self.T)
    #   self.daily_supplies_full[x + '_dynamic_recharge_cap'] = np.zeros(self.T)

    # for x in self.non_contract_delivery_list:
    #   self.daily_supplies_full[x] = np.zeros(self.T)
    # for x in ['recover_banked', 'inleiu_irrigation', 'inleiu_recharge', 'leiupumping', 'exchanged_GW', 'exchanged_SW', 'pumping', 'irr_demand', 'tot_demand', 'dynamic_recovery_cap']:
    #   self.daily_supplies_full[x] = np.zeros(self.T)  
	
    # ['recover_banked', 'inleiu', 'leiupumping', 'recharged', 'exchanged_GW', 'exchanged_SW', 'undelivered_trades']

    #Initialize demands
    self.annualdemand = {}
    self.annualdemand[0] = 0.0
    self.dailydemand = {}
    self.dailydemand[0] = 0.0
    self.dailydemand_start = {}
    self.dailydemand_start[0] = 0.0

    #recovery and pumping variables
    self.annual_pumping = {}
    self.annual_pumping[0] = 0.0
    self.use_recharge = 0.0
    self.use_recovery = 0.0
    self.extra_leiu_recovery = 0.0
    self.max_recovery = 0.0
    self.recovery_capacity_remain = 0.0
    self.max_leiu_exchange = 0.0
    self.direct_recovery_delivery = 0.0
    self.pre_flood_demand = 0.0
    self.recharge_rate = self.in_district_direct_recharge*cfs_tafd

    #for in-district recharge & counters (for keeping track of how long a basin has been continuously 'wet'
    self.thismonthuse = 0
    self.monthusecounter = 0
    self.monthemptycounter = 0
    self.current_recharge_storage = 0.0
    self.private_fraction = [0.0]
    self.has_private = 0
    self.has_pesticide = 0
    self.has_pmp = 0
	
    #banking dictionaries to keep track of individual member use & accounts
    if self.in_leiu_banking:
      self.recovery_use = {}
      self.inleiubanked = {}
      self.contract_exchange = {}
      self.leiu_additional_supplies = {}
      self.bank_deliveries = {}
      self.tot_leiu_recovery_use = 0.0
      self.direct_storage = {}
      self.bank_timeseries = {}
      self.recharge_rate_series = []
      self.leiu_trade_cap = 0.5
      for x in self.participant_list:
        self.recovery_use[x] = 0.0
        self.inleiubanked[x] = 0.0
        self.leiu_additional_supplies[x] = 0.0
        self.bank_deliveries[x] = 0.0
        self.direct_storage[x] = 0.0
        self.bank_timeseries[x] = np.zeros(self.T)
        self.contract_exchange[x] = np.zeros(self.T)



##################################SENSITIVITY ANALYSIS#################################################################
  def set_sensitivity_factors(self, et_factor, acreage_factor, irr_eff_factor, recharge_decline_factor):
    wyt_list = ['W', 'AN', 'BN', 'D', 'C']
    for wyt in wyt_list:
      for i,v in enumerate(self.crop_list):
        self.acreage[wyt][i] = self.acreage[wyt][i]*acreage_factor
        for monthloop in range(0,12):
          self.irrdemand.etM[v][wyt][monthloop] = self.irrdemand.etM[v][wyt][monthloop]*et_factor
    self.seepage = 1.0 + irr_eff_factor
    for recharge_count in range(0, len(self.recharge_decline)):
      self.recharge_decline[recharge_count] = 1.0 - recharge_decline_factor*(1.0 - self.recharge_decline[recharge_count])

      
#####################################################################################################################
##################################DEMAND CALCULATION#################################################################
#####################################################################################################################

  def find_baseline_demands(self,wateryear, non_leap_year, days_in_month):
    self.monthlydemand = {}
    wyt_list = ['W', 'AN', 'BN', 'D', 'C']
    crop_wyt_list = ['AN', 'AN', 'BN', 'D', 'C']
    
    for wyt, cwyt in zip(wyt_list, crop_wyt_list):
      self.monthlydemand[wyt] = np.zeros(12)
      for monthloop in range(0,12):
        self.monthlydemand[wyt][monthloop] += self.urban_profile[monthloop]*self.MDD/days_in_month[non_leap_year][monthloop]
        if self.has_pesticide == 1:
          for i,v in enumerate(self.acreage_by_year):
            self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][cwyt][monthloop],0.0)*(self.acreage_by_year[v][wateryear]-self.private_acreage[v][wateryear])/(12.0*days_in_month[non_leap_year][monthloop])
            #self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][cwyt][monthloop] - self.irrdemand.etM['precip'][cwyt][monthloop],0.0)*(self.acreage_by_year[v][wateryear]-self.private_acreage[v][wateryear])/(12.0*days_in_month[non_leap_year][monthloop])
        elif self.has_pmp == 1:
          for crop in self.pmp_acreage:
            self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[crop][cwyt][monthloop],0.0)*max(self.pmp_acreage[crop]-self.private_acreage[crop], 0.0)/(12.0*days_in_month[non_leap_year][monthloop])
            #self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[crop][cwyt][monthloop] - self.irrdemand.etM['precip'][cwyt][monthloop],0.0)*max(self.pmp_acreage[crop]-self.private_acreage[crop], 0.0)/(12.0*days_in_month[non_leap_year][monthloop])
        else:
          for i,v in enumerate(self.crop_list):
            self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][cwyt][monthloop],0.0)*(self.acreage[cwyt][i]-self.private_acreage[v])/(12.0*days_in_month[non_leap_year][monthloop])
          	  	
			
  cdef void calc_demand(self, int wateryear, int year_index, int da, int m, list days_in_month, int m1, str wyt):
    #from the monthlydemand dictionary (calculated at the beginning of each wateryear based on ag acreage and urban demands), calculate the daily demand and the remaining annual demand
    cdef int monthday, irrseason
    monthday = days_in_month[year_index][m-1]
    self.dailydemand[0] = self.monthlydemand[wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[wyt][m1-1]*da/monthday
    if self.dailydemand[0] < 0.0:
      self.dailydemand[0] = 0.0
    #calculate that days 'starting' demand (b/c demand is filled @multiple times, and if we only want to fill a certain fraction of that demand (based on projections of supply & demand for the rest of the year), we want to base that fraction on that day's total demand, not the demand left after other deliveries are made
    self.dailydemand_start[0] = self.monthlydemand[wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[wyt][m1-1]*da/monthday
	  #pro-rate this month's demand based on the day of the month when calculating remaining annual demand
    self.annualdemand[0] = max(self.monthlydemand[wyt][m-1]*(monthday-da), 0.0)
    self.irrseasondemand = 0.0
    for irrseason in range(6,9):
      self.irrseasondemand += max(self.monthlydemand[wyt][irrseason]*days_in_month[year_index][irrseason], 0.0)
    if m > 9:
      for monthloop in range(m, 12):
        self.annualdemand[0] += max(self.monthlydemand[wyt][monthloop]*days_in_month[year_index][monthloop],0.0)
      for monthloop in range(0,9):
        self.annualdemand[0] += max(self.monthlydemand[wyt][monthloop]*days_in_month[year_index+1][monthloop], 0.0)
    else:
      for monthloop in range(m, 9):
        self.annualdemand[0] += max(self.monthlydemand[wyt][monthloop]*days_in_month[year_index][monthloop], 0.0)
		
		
  def find_pre_flood_demand(self, year_index, days_in_month, wyt):
    #calculates an estimate for water use in the Oct-Dec period (for use in recharge_carryover calculations), happens Oct 1
    self.pre_flood_demand = self.monthlydemand[wyt][9]*days_in_month[year_index][9] + self.monthlydemand[wyt][10]*days_in_month[year_index][10] + self.monthlydemand[wyt][11]*days_in_month[year_index][11]
		  

  cdef void get_urban_demand(self, int t, int m, int da, int dowy, int wateryear, int year_index, list dowy_eom, double total_delta_pumping, double allocation_change, str model_mode):
    #this function finds demands for the 'branch pumping' urban nodes - Socal, South Bay, & Central Coast
	  #demand is equal to pumping of the main california aqueduct and into the branches that services these areas
    #cal aqueduct urban demand comes from pumping data, calc seperately
    cdef:
      double sri_estimate, sri_estimate_int, todays_demand_regression_error
      int start_of_month, cross_counter_y, monthloop, monthcounter, start_next_month, random_component, sort_year
      str wyt

    if model_mode == 'validation':  
      self.dailydemand[0] = self.pumping[0][t]/1000.0
      self.dailydemand_start[0] = self.pumping[0][t]/1000.0
      ##Keep track of ytd pumping to Cal Aqueduct Branches
      self.ytd_pumping[0][wateryear] += self.dailydemand[0]
      sri_estimate = (total_delta_pumping*self.delivery_percent_coefficient[0][dowy][0] + self.delivery_percent_coefficient[0][dowy][1])*total_delta_pumping
      self.annualdemand[0] = max(0.0, (self.annual_pumping[0][wateryear]*min(dowy, 240.0) + sri_estimate*(240.0 - min(dowy, 240.0)))/240.0 - self.ytd_pumping[0][wateryear])
      if m == 10 and da == 1:
        start_of_month = 0
        cross_counter_y = 0
	      ###Divide aqueduct branch pumping into 'monthly demands'
        for monthloop in range(0,12):
          monthcounter = monthloop + 9
          if monthcounter > 11:
            monthcounter -= 12
            cross_counter_y = 1
          start_next_month = dowy_eom[year_index+cross_counter_y][monthcounter] + 1
          for wyt in ['W', 'AN', 'BN', 'D', 'C']:
            self.monthlydemand[wyt][monthcounter] = np.mean(self.pumping[0][(t + start_of_month):(t + start_next_month)])/1000.0
          start_of_month = start_next_month
    else:

      ###If simulation (no observations), get daily, monthly, annual demands from seasonally adjusted delta pumping based estimates, with random errors
      sri_estimate_int = total_delta_pumping*self.delivery_percent_coefficient[0][dowy][0] + self.delivery_percent_coefficient[0][dowy][1]
      if m == 10 and da == 1:
        self.last_days_demand_regression_error = 0.0
        todays_demand_regression_error = 0.0
      else:
        random_component = np.random.randint(0, len(self.demand_auto_errors[0][dowy]) )
        todays_demand_regression_error = allocation_change * self.delivery_percent_coefficient[0][dowy][2] + self.delivery_percent_coefficient[0][dowy][3] + self.last_days_demand_regression_error - self.demand_auto_errors[0][dowy][random_component]
        self.last_days_demand_regression_error = todays_demand_regression_error * 1.0
        sri_estimate = total_delta_pumping * (sri_estimate_int - todays_demand_regression_error)
        self.annualdemand[0] = max(sri_estimate - self.ytd_pumping[0][wateryear], 1.0)

      for sort_year in range(0, len(self.hist_demand_dict['annual_sorted'][dowy])):
        if total_delta_pumping > self.hist_demand_dict['annual_sorted'][dowy][sort_year]:
          break
      self.k_close_wateryear = sort_year
      self.dailydemand[0] += self.annualdemand[0]*self.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]
      self.dailydemand_start[0] += self.annualdemand[0]*self.hist_demand_dict['daily_fractions'][self.k_close_wateryear][dowy]

      if da == 1:
        self.monthlydemand = {}
        for wyt in ['W', 'AN', 'BN', 'D', 'C']:
          self.monthlydemand[wyt] = np.zeros(12)

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
          start_next_month = dowy_eom[year_index+cross_counter_y][monthcounter] + 1
          for wyt in ['W', 'AN', 'BN', 'D', 'C']:
            self.monthlydemand[wyt][monthcounter] += self.annualdemand[0]*np.mean(self.hist_demand_dict['daily_fractions'][self.k_close_wateryear][start_of_month:start_next_month])
          start_of_month = start_next_month
    
      self.ytd_pumping[0][wateryear] += self.dailydemand[0]

		
  def set_pmp_acreage(self, water_constraint_by_source, land_constraint, x0):
    self.acreage_by_pmp_crop_type = self.irrdemand.find_pmp_acreage(water_constraint_by_source,land_constraint, x0)
    self.pmp_acreage = {}
    i = 0
    for crop in self.irrdemand.crop_list:
      district_crops = self.irrdemand.crop_keys[crop]
      if district_crops in self.pmp_acreage:
        self.pmp_acreage[district_crops] += self.acreage_by_pmp_crop_type[i]/1000.0
      else:
        self.pmp_acreage[district_crops] = self.acreage_by_pmp_crop_type[i]/1000.0
      i += 1

		
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################PROJECT CONTRACTS#################################################################
#####################################################################################################################

  cdef (double, double) update_balance(self, int t, int wateryear, double water_available, double projected_allocation, double current_water, str key, double tot_carryover, str balance_type):
    ###This function takes input from the contract class (water_available, projected_allocation, tot_carryover) to determine how much of their allocation remains
    ##water_available is the current contract storage in the reservoir *plus* all deliveries from the given year.  The deliveries, paper trades, and turnback pool accounts for each district
    ##are used to get a running tally of the surface water that is currently available to them.  (tot_carryover is subtracted from the current balance - districts only get access to *their* 
    ##carryover storage - which is added to their individual current balance (self.carryover[key])
    ##projected_allocation is the water that is forecasted to be available on each contract through the end of the water year *plus* water that has already been delivered on that contract
    ##individual deliveries are then subtracted from this total to determine the individual district's projected contract allocation remaining in that year
    cdef:
      double frac_to_district, district_storage, annual_allocation, storage_balance

    if self.has_private == 1:
      if self.has_pesticide == 1:
        frac_to_district = 1.0 - self.private_fraction[wateryear]
      else:
        frac_to_district = 1.0 - self.private_fraction[0]
    else:
      frac_to_district = 1.0

    if balance_type == 'contract':
      #district_storage - district's water that is currently available (in storage at reservoir)
      #(water_available - tot_carryover)*self.project_contract[key] - individual district share of the existing (in storage) contract balance, this includes contract water that has already been delivered to all contractors
      #self.deliveries[key][wateryear] - individual district deliveries (how much of 'their' contract has already been delivered)
      #self.carryover[key] - individual district share of contract carryover
      #paper_balance[key] - keeps track of 'paper' groundwater trades (negative means they have accepted GW deliveries in exchange for trading some of their water stored in reservoir, positive means they sent their banked GW to another district in exchage for SW storage
      #turnback_pool[key] - how much water was bought/sold on the turnback pool(negative is sold, positive is bought)
      district_storage = (water_available-tot_carryover)*self.project_contract[key]*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key]  + self.paper_balance[key] + self.turnback_pool[key]
      #annual allocation - remaining (undelivered) district share of expected total contract allocation
	    #same as above, but projected_allocation*self.project_contract[key] - individual share of expected total contract allocation, this includes contract water that has already been delivered to all contractors
      annual_allocation = projected_allocation*self.project_contract[key]*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      storage_balance =   current_water*self.project_contract[key]*frac_to_district + max(self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key] - self.deliveries[key][wateryear], 0.0)

    elif balance_type == 'right':
      #same as above, but for contracts that are expressed as 'rights' instead of allocations
      district_storage = (water_available-tot_carryover)*self.rights[key]['capacity']*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      annual_allocation = projected_allocation*self.rights[key]['capacity']*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      storage_balance = current_water*self.rights[key]['capacity']*frac_to_district + max(self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key] - self.deliveries[key][wateryear], 0.0)
    
    self.current_balance[key] = max(min(storage_balance,annual_allocation), 0.0)
    self.projected_supply[key] = max(annual_allocation,0.0)
	  
    return max(self.projected_supply[key] - self.annualdemand[0], 0.0) , max(self.carryover[key] - self.deliveries[key][wateryear], 0.0)
	


  cdef (double, double) calc_carryover(self, double existing_balance, int wateryear, str balance_type, str key):
    #at the end of each wateryear, we tally up the full allocation to the contract, how much was used (and moved around in other balances - carryover, 'paper balance' and turnback_pools) to figure out how much each district can 'carryover' to the next year
    cdef:
      double frac_to_district, annual_allocation, max_carryover, reallocated_water, carryover
    
    if self.has_private == 1:
      if self.has_pesticide == 1:
        frac_to_district = 1.0 - self.private_fraction[wateryear]
      else:
        frac_to_district = 1.0 - self.private_fraction[0]
    else:
      frac_to_district = 1.0
    
    if balance_type == 'contract':
      annual_allocation = existing_balance*self.project_contract[key]*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      max_carryover = self.contract_carryover_list[key]
    elif balance_type == 'right':
      annual_allocation = existing_balance*self.rights[key]['capacity']*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      max_carryover = self.contract_carryover_list[key]

    reallocated_water = max(annual_allocation - max_carryover, 0.0)
    carryover = min(max_carryover, annual_allocation)
    self.carryover[key] = carryover
    self.paper_balance[key] = 0.0
    self.turnback_pool[key] = 0.0
	
    return reallocated_water, carryover
		
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################RECHARGE/RECOVERY TRIGGERS#########################################################
#####################################################################################################################
	
  cdef void open_recovery(self, int t, int dowy, int wateryear, double target_eoy):
    #this function determines if a district wants to recover banked water
	  #based on their demands and existing supplies
    cdef:
      double total_balance, total_recovery, existing_carryover, total_needs
      str contract_key

    total_balance = 0.0
    total_recovery = (366-dowy)*self.max_recovery + self.extra_leiu_recovery
    self.recovery_capacity_remain = total_recovery
    existing_carryover = 0.0
    for contract_key in self.contract_list:
      total_balance += self.projected_supply[contract_key]
      existing_carryover += max(self.carryover[contract_key] - self.deliveries[contract_key][wateryear], 0.0)
	
    total_needs = self.annualdemand[0]*self.seepage*self.surface_water_sa*self.recovery_fraction
    if (total_balance + total_recovery) < total_needs + target_eoy:
      if existing_carryover > 0.0:
        self.use_recovery = 0.0
      else:
        if total_needs > 0.0:
          self.use_recovery = min(max(total_recovery/total_needs, 0.0), 1.0)
        else:
          self.use_recovery = 0.0
    else:
      self.use_recovery = 0.0
	  	  
    self.min_direct_recovery = max(self.annualdemand[0] - total_balance,0.0)/(366-dowy)
	  	  


  cdef void open_recharge(self, int t, int m, int da, int wateryear, int year_index, list days_in_month, double numdays_fillup, double numdays_fillup2, str key, str wyt, list reachable_turnouts, double additional_carryover):
    #for a given contract owned by the district (key), how much recharge can they expect to be able to use
    #before the reservoir associated w/ that contract fills to the point where it needs to begin spilling water
    #(numdays_fillup) - i.e., how much surface water storage can we keep before start losing it
    #self.recharge_carryover is the district variable that shows how much 'excess' allocation there is on a particular
    #contract - i.e., how much of the allocation will not be able to be recharged before the reservoir spills
    cdef:
      double total_recharge, total_recharge2, carryover_storage_proj, spill_release_carryover, service_area_adjust, adjusted_sw_sa, days_left, days_left2, \
              this_month_recharge, this_month_recharge2, total_available_for_recharge
      int is_reachable, monthcounter, monthcounter_loop, next_year_counter
      str x, y

    total_recharge = 0.0
    total_recharge2 = 0.0
    carryover_storage_proj = 0.0
    spill_release_carryover = 0.0
    is_reachable = 0
    self.dynamic_recharge_cap[key] = 999.0
    self.days_to_fill[key] = min(numdays_fillup, numdays_fillup2)
    for x in reachable_turnouts:
      for y in self.turnout_list:
        if y == x:
          is_reachable = 1
          break
      if is_reachable == 1:
        break
    if is_reachable == 0:
      service_area_adjust = 0.0
    else:
      service_area_adjust = 1.0
	  
    adjusted_sw_sa = self.surface_water_sa*service_area_adjust
    
    if numdays_fillup < 365.0:

      ##how many days remain before the reservoir fills? 		  
      days_left = numdays_fillup
      days_left2 = numdays_fillup2
	    #tabulate how much water can be recharged between now & reservoir fillup (current month)
      this_month_recharge = (self.max_direct_recharge[0] + self.max_leiu_recharge[0])*min(days_in_month[year_index][m] - da,days_left)
      this_month_recharge2 = (self.max_direct_recharge[0] + self.max_leiu_recharge[0])*min(days_in_month[year_index][m] - da,days_left2)
      total_recharge += this_month_recharge
      total_recharge2 += this_month_recharge2
	    #days before fillup remaining after current month
      days_left -= (days_in_month[year_index][m] - da)
      days_left2 -= (days_in_month[year_index][m] - da)
	
      ###if days_left remains positive (i.e., reservoir fills after the end of the current month)
      ###loop through future months to determine how much water can be recharged before reservoir fills
      monthcounter = 0
      monthcounter_loop = 0
      next_year_counter = 0
      while (monthcounter + monthcounter_loop) < 11 and days_left > 0.0:
        monthcounter += 1
        if (monthcounter + m) > 11:
          monthcounter -= 12
          monthcounter_loop = 12
          next_year_counter = 1
		
 	      # continue to tabulate how much water can be recharged between now & reservoir fillup (future months)
        this_month_recharge = (self.max_direct_recharge[monthcounter+monthcounter_loop] + self.max_leiu_recharge[monthcounter+monthcounter_loop])*min(days_in_month[year_index+next_year_counter][m+monthcounter],days_left)
        total_recharge += this_month_recharge
        
        days_left -= days_in_month[year_index+next_year_counter][m+monthcounter]
        
      ###Uses the projected supply calculation to determine when to recharge water.  There are a number of conditions under which a 
      ###district will recharge water.  Projected allocations are compared to total demand, recharge capacity, and the probability of 
      ###surface water storage spilling carryover water.  If any of these conditions triggers recharge, the district will release water
      ##for recharge
	  
      monthcounter = 0
      monthcounter_loop = 0
      next_year_counter = 0

      while (monthcounter + monthcounter_loop) < 11 and days_left2 > 0.0:
        monthcounter += 1
        if (monthcounter + m) > 11:
          monthcounter -= 12
          monthcounter_loop = 12
          next_year_counter = 1
		
        # continue to tabulate how much water can be recharged between now & reservoir fillup (future months)
        this_month_recharge2 = (self.max_direct_recharge[monthcounter+monthcounter_loop] + self.max_leiu_recharge[monthcounter+monthcounter_loop])*min(days_in_month[year_index+next_year_counter][m+monthcounter],days_left2)
        total_recharge2 += this_month_recharge2
        days_left2 -= days_in_month[year_index+next_year_counter][m+monthcounter]
        
      ###Uses the projected supply calculation to determine when to recharge water.  There are a number of conditions under which a 
      ###district will recharge water.  Projected allocations are compared to total demand, recharge capacity, and the probability of 
      ###surface water storage spilling carryover water.  If any of these conditions triggers recharge, the district will release water
      ##for recharge
      spill_release_carryover = 0.0
      for y in self.contract_list:
        spill_release_carryover += max(self.projected_supply[y] - max(self.carryover_rights[y], additional_carryover), 0.0)
        
      spill_release_carryover -= (self.annualdemand[0]*adjusted_sw_sa + total_recharge2*service_area_adjust  + additional_carryover)
      spill_release_carryover = max(spill_release_carryover, 0.0)

      carryover_storage_proj = 0.0
      for y in self.contract_list:
        carryover_storage_proj += max(self.carryover[y] - self.deliveries[y][wateryear] - self.carryover_rights[y], 0.0)

      carryover_storage_proj -= (total_recharge*service_area_adjust)
      carryover_storage_proj = max(carryover_storage_proj, 0.0)
		
      ##The amount of recharge a district wants is then saved and sent to the canal class where it 'looks' for an available spot to recharge the water
      #self.recharge_carryover[key] = max(carryover_release_proj, carryover_release_current, spill_release_carryover, spill_release_storage)
      if spill_release_carryover > carryover_storage_proj:
        total_available_for_recharge = 0.0
        for y in self.contract_list:
          total_available_for_recharge += max(self.projected_supply[y], 0.0)
      
        if total_available_for_recharge > 0.0:
          self.recharge_carryover[key] = max(spill_release_carryover, 0.0)*max(self.projected_supply[key], 0.0)/total_available_for_recharge
        else:
          self.recharge_carryover[key] = 0.0
      else:
        total_available_for_recharge = 0.0
        for y in self.contract_list:
          total_available_for_recharge += max(self.carryover[y] - self.deliveries[y][wateryear], 0.0)
      
        if total_available_for_recharge > 0.0:
          self.recharge_carryover[key] = max(carryover_storage_proj, 0.0)*max(self.carryover[key] - self.deliveries[key][wateryear], 0.0)/total_available_for_recharge
        else:
          self.recharge_carryover[key] = 0.0
      self.dynamic_recharge_cap[key] = min(total_recharge2, total_recharge)
      ##Similar conditions also calculate the amount of regular tableA deliveries for direct irrigation to request
    else:
      self.delivery_carryover[key] = 0.0
      self.recharge_carryover[key] = 0.0
	  


  cdef double get_urban_recovery_target(self, int t, int dowy, int wateryear, str wyt, dict pumping, double project_contract, int demand_days, int start_month) except -1:
    cdef:
      double max_pumping_shortfall, pumping_shortfall, frac_to_district
      int monthcounter, daycounter, tot_days

    max_pumping_shortfall = 0.0
    pumping_shortfall = 0.0
    if self.has_private == 1:
      if self.has_pesticide == 1:
        frac_to_district = 1.0 - self.private_fraction[wateryear]
      else:
        frac_to_district = 1.0 - self.private_fraction[0]
    else:
      frac_to_district = 1.0

    monthcounter = start_month
    daycounter = 0
    tot_days = 0
    if demand_days > 365:
      max_pumping_shortfall = 9999.9
    else:
      while tot_days < demand_days:
        pumping_shortfall += np.sum(self.pumping[0][(t-dowy+tot_days):(t-dowy+tot_days+min(demand_days -tot_days, 30))])/1000.0 - pumping['swp']['gains'][monthcounter]*project_contract*frac_to_district
        tot_days += 30
        monthcounter += 1
        if monthcounter == 12:
          monthcounter = 0

        max_pumping_shortfall = max(pumping_shortfall, max_pumping_shortfall)
	  
    return max(max_pumping_shortfall, 0.0)
	  


  cdef tuple set_turnback_pool(self, str key, int year_index, list days_in_month):
    ##This function creates the 'turnback pool' (note: only for SWP contracts now, can be used for others)
    ##finding contractors with 'extra' contract water that they would like to sell, and contractors who would
    ##like to purchase that water.  
    cdef:
      double total_projected_supply, total_recharge_ability, contract_fraction
      str contract_key

    self.turnback_sales = 0.0
    self.turnback_purchases = 0.0
    total_projected_supply = 0.0
    total_recharge_ability = 0.0
    for contract_key in self.contract_list:
      total_projected_supply += self.projected_supply[contract_key]
    for month_count in range(0, 6):
      # total recharge Jun,Jul,Aug,Sep
      total_recharge_ability += self.max_direct_recharge[month_count]*days_in_month[year_index][month_count + 3] + self.max_leiu_recharge[month_count]*days_in_month[year_index][month_count + 3]

    if total_projected_supply > 0.0:
      contract_fraction = max(min(self.projected_supply[key]/total_projected_supply, 1.0), 0.0)
    else:
      contract_fraction = 0.0

    #districts sell water if their projected contracts are greater than their remaining annual demand, plus their remaining recharge capacity in this water year, plus their recharge capacity in the next water year (through January)
    if key in self.contract_list:
      self.turnback_sales = max(self.projected_supply[key] - self.carryover_rights[key] - (self.annualdemand[0] +  total_recharge_ability)*contract_fraction, 0.0)
      if self.in_leiu_banking:
        self.turnback_purchases = 0.0
      else:
        #districts buy turnback water if their annual demands are greater than their projected supply plus their capacity to recover banked groundwater
        self.turnback_purchases = max(self.annualdemand[0]*contract_fraction - self.projected_supply[key] - self.max_recovery*122*contract_fraction, 0.0)

    return self.turnback_sales, self.turnback_purchases	  
      


  cdef void make_turnback_purchases(self, double turnback_sellers, double turnback_buyers, str key):
    #once we know how much water is in the 'selling' pool and the 'buying' pool, we can determine the total turnback pool - min(buying,selling), then
    #determine what % of each request is filled (i.e., if the selling pool is only 1/2 of the buying pool, then buyers only get 1/2 of their request, or visa versa	
    cdef:
      double sellers_frac, buyers_frac, total_projected_supply
      str contract_key

    if min(turnback_sellers, turnback_buyers) > 0.0:
      sellers_frac = -1*min(turnback_sellers, turnback_buyers)/turnback_sellers
      buyers_frac = min(turnback_sellers, turnback_buyers)/turnback_buyers
      total_projected_supply = 0.0
      for contract_key in self.contract_list:
      #the buying/selling fractiosn are applied to the same calculations above (about buying or selling needs), and then turnback pools are added/subtracted to the districts contract
        total_projected_supply += self.projected_supply[contract_key]
      if self.turnback_sales > 0.0:
        self.turnback_pool[key] = max(self.turnback_sales, 0.0)*sellers_frac
        self.projected_supply[key] += max(self.turnback_sales, 0.0)*sellers_frac
      elif self.turnback_purchases > 0.0:
        if self.in_leiu_banking:
          self.turnback_pool[key] = 0.0
        else:
          self.turnback_pool[key] = max(self.turnback_purchases, 0.0)*buyers_frac
        self.projected_supply[key] += max(self.turnback_purchases, 0.0)*buyers_frac
	
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################DETERMINE DELIVERIES ON CANAL######################################################
#####################################################################################################################

			
  cdef double find_node_demand(self, list contract_list, str search_type, int partial_demand_toggle, int toggle_recharge)  except *:
    cdef:
      double access_mult, total_projected_allocation, private_add, total_demand_met, annualdemand, dailydemand, dailydemand_start, demand_constraint, private_demand, private_delivery, projected_supply
      str private_key, contract_key
      Contract contract_obj

    #this function is used to calculate the current demand at each 'district' node
    access_mult = self.surface_water_sa*self.seepage#this accounts for water seepage & the total district area that can be reached by SW canals (seepage is >= 1.0; surface_water_sa <= 1.0)
	
    total_projected_allocation = 0.0
    private_add = 0.0
    if self.has_private == 1:
      for private_key in self.private_demand:
        private_demand, private_delivery = self.private_demand[private_key], self.private_delivery[private_key]
        private_add += min(self.private_demand[private_key], self.private_delivery[private_key])

    for contract_obj in contract_list:
      projected_supply = self.projected_supply[contract_obj.name]
      total_projected_allocation += max(projected_supply, 0.0)#projected allocation

    #percentage of demand filled in the day is equal to the total projected allocation as a percent of annual demand
	  #(i.e., if allocations are projected to be 1/2 of annual demand, then they try to fill 50% of daily irrigation demands with surface water
    annualdemand = self.annualdemand[0]
    dailydemand_start = self.dailydemand_start[0]
    dailydemand = self.dailydemand[0]
    if annualdemand*access_mult > 0.0 and partial_demand_toggle == 1:
      if self.must_fill == 1:
      #pumping to urban branches of the Cal Aqueduct is 'must fill', (i.e., demand is always met)
        total_demand_met = 1.0
      else:
        if annualdemand*access_mult > 0.0:
          total_demand_met = 1.0
        else:
          total_demand_met = 0.0		
    else:
      total_demand_met = 1.0
    #self.dailydemand_start is the initial daily district demand (self.dailydemand is updated as deliveries are made) - we try to fill the total_demand_met fraction of dailydemand_start, or what remains of demand in self.dailydemand, whichever is smaller
    if search_type == 'flood':
      if annualdemand > 0.0 and total_projected_allocation > 0.0:
        demand_constraint = (1.0 - min(total_projected_allocation/annualdemand, 1.0))*max(min(dailydemand_start*access_mult*total_demand_met, dailydemand*access_mult),0.0)
      else:
        demand_constraint = max(min(dailydemand_start*access_mult*total_demand_met, dailydemand*access_mult),0.0)

    else:
      demand_constraint = max(min(dailydemand_start*access_mult*total_demand_met, dailydemand*access_mult),0.0)
    #if we want to include recharge demands in the demand calculations, add available recharge space
    if toggle_recharge == 1:
      demand_constraint += max(self.in_district_storage - self.current_recharge_storage, 0.0)
    return demand_constraint + private_add
	


  cdef double find_node_output(self):
    #this function calculates the total recovery capacity that is contained in each district node (i.e. in leiu banks)
    cdef double current_recovery_use, output_constraint

    if self.in_leiu_banking:
      current_recovery_use = 0.0
      for x in self.recovery_use:
        current_recovery_use += self.recovery_use[x]
      output_constraint = self.leiu_recovery - current_recovery_use
    else:
      output_constraint = 0.0
	  
    return output_constraint
	

  cdef tuple find_leiu_output(self, list contract_list):
    cdef:
      double member_constraint
      int bank_counter, bank_contract_counter
      str bank_contract_key
      list total_contract
      Contract exchange_contract_obj

    member_constraint = 0.0
    total_contract = [0.0 for _ in range(len(self.contract_list))]
    if self.in_leiu_banking:
      bank_counter = 0
      for bank_contract_key in self.contract_list:
        for exchange_contract_obj in contract_list:
          if bank_contract_key == exchange_contract_obj.name:
            member_constraint += max(min(self.current_balance[bank_contract_key], self.projected_supply[bank_contract_key]), 0.0)
            total_contract[bank_counter] += max(min(self.current_balance[bank_contract_key], self.projected_supply[bank_contract_key]), 0.0) 
        bank_counter += 1
		
      if member_constraint > 0.0:
        for bank_contract_counter in range(0, len(total_contract)):
          total_contract[bank_contract_counter] = total_contract[bank_contract_counter]/member_constraint
    
    return member_constraint, total_contract
     
	
  cdef double set_request_constraints(self, double demand, str search_type, list contract_list, double bank_space, double bank_capacity, int dowy, int wateryear) except *:
    #this function is used to determine if a district node 'wants' to make a request
    #under the different usage types (flood, delievery, banking, or recovery) under a given contract (contract_list)
    cdef:
      double total_carryover_recharge, total_current_balance, private_add, total_projected_supply, conservative_estimate
      int carryover_toggle, delta_toggle, member_trades
      str xx, contract_key
      Contract contract_obj
    
    self.projected_supply['tot'] = 0.0
    for contract_key in self.contract_list:
      self.projected_supply['tot'] += self.projected_supply[contract_key]

    #for banking, a district requests water if they have enough contract water currently in surface water storage and they have 'excess' water for banking (calculated in self.open_recharge)
    if search_type == "banking":
      total_carryover_recharge = 0.0
      total_current_balance = 0.0
      for contract_obj in contract_list:
        total_carryover_recharge += max(self.recharge_carryover[contract_obj.name], 0.0)
        total_current_balance += max(self.current_balance[contract_obj.name], 0.0)
      return min(total_carryover_recharge, total_current_balance, max(bank_capacity - bank_space, 0.0))

    #for normal irrigation deliveries, a district requests water if they have enough water currently
	  #in surface water storage under the given contract
    elif search_type == "delivery":
      private_add = 0.0
      if self.has_private == 1:
        for xx in self.private_demand:
          private_add += min(self.private_demand[xx], self.private_delivery[xx])
      total_current_balance = 0.0
      total_projected_supply = 0.0
      carryover_toggle = 0
      if self.project_contract['exchange'] > 0.0:
        delta_toggle = 1
      elif self.project_contract['cvpdelta'] > 0.0:
        if dowy < 150 or dowy + self.days_to_fill['cvpdelta'] < 365:
          delta_toggle = 1
        else:
          delta_toggle = 0
      else:
        delta_toggle = 0

      for contract_obj in contract_list:
        total_current_balance += max(self.current_balance[contract_obj.name], 0.0)
        total_projected_supply += max(self.projected_supply[contract_obj.name], 0.0)
        if self.carryover[contract_obj.name] > self.deliveries[contract_obj.name][wateryear]:
          carryover_toggle = 1

      if self.seasonal_connection == 1:
        if self.must_fill == 1:
          return max(min(demand, total_current_balance), 0.0) + private_add
        elif (carryover_toggle == 1) or (total_projected_supply > self.annualdemand[0]):
          return max(min(demand, total_current_balance), 0.0) + private_add
        elif delta_toggle == 1:
          return max(min(demand, total_current_balance, total_projected_supply), 0.0) + private_add
        else:
          conservative_estimate = max(min((dowy- 211.0)/(273.0 - 211.0), 1.0), 0.0)
          if self.annualdemand[0] > 0.0:
            return max(min(demand*min(conservative_estimate*total_projected_supply/self.annualdemand[0], 1.0), demand, total_current_balance), 0.0) + private_add
          else:
            return max(min(demand,total_current_balance), 0.0) + private_add

      else:
        return private_add

    #for flood deliveries, a district requests water if they don't have
	  #excess contract water that they don't think they can recharge (i.e. they don't purchase
	  #flood water if they can't use all their contract water
    elif search_type == "flood":
      return demand

    #for recovery, a district requests recovery water from a bank if they have contracts under the current contract being searched (i.e., so they aren't requesting water that will be 
    #sent to another district that can't make 'paper' trades with them) and if they have their 'recovery threshold' triggered (self.use_recovery, calculated in self.open_recovery)
    elif search_type == "recovery":
      member_trades = 0
      for contract_key in self.contract_list:
        for contract_obj in contract_list:
          if contract_key == contract_obj.name:
            member_trades = 1
            break
        if member_trades == 1:
          break
      if member_trades == 1:
        if self.use_recovery > 0.0:
          return min(max(self.dailydemand[0]*self.surface_water_sa*self.seepage*self.use_recovery, 0.0), max(bank_space, 0.0))
        else:
          return 0.0
      else:
        return 0.0
		
    	  

  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal, str message=''):
    #this function takes the calculated demand at each district node and classifies those demands by 'priority' - the priority classes and rules change for each delivery type
    cdef:
      int contractor_toggle, priority_toggle
      str contract_key
      dict demand_dict
      Canal canal_obj
      Contract contract_obj

    demand_dict = {}
    #for flood deliveries, the priority structure is based on if you have a contract with the reservoir that is being spilled, if you have a turnout on a canal that is a 'priority canal' 
    #for the spilling reservoir, and then finally if you are not on a priority canal for spilling
    if search_type == 'flood':
      contractor_toggle = 0
      priority_toggle = 0
      for canal_obj in priority_list:#canals that have 'priority' from the given reservoir
        if canal_obj.name == contract_canal:#current canal
          priority_toggle = 1
      if priority_toggle == 1:
        for contract_obj in contract_list:#contracts that are being spilled (b/c they are held at the spilling reservoir)
          for contract_key in self.contract_list:
            if contract_obj.name == contract_key:
              contractor_toggle = 1
        if contractor_toggle == 1:
          demand_dict['contractor'] = max(min(demand,delivery), 0.0)
          demand_dict['alternate'] = min(delivery - demand_dict['contractor'], demand_constraint-demand_dict['contractor'])
          demand_dict['turnout'] = 0.0
          demand_dict['excess'] = 0.0
        else:
          demand_dict['contractor'] = 0.0
          demand_dict['alternate'] = 0.0
          demand_dict['turnout'] = max(min(demand,delivery), 0.0)
          demand_dict['excess'] = 0.0
      else:
        demand_dict['contractor'] = 0.0
        demand_dict['alternate'] = 0.0
        demand_dict['turnout'] = 0.0
        demand_dict['excess'] = max(min(demand,delivery), 0.0)
    #irrigation deliveries have only one type of priority (the contract that is currently being deliveried)
    elif search_type == 'delivery':
      demand_dict[contract_canal] = max(min(demand,delivery), 0.0)
    #in-leiu banks have demands that are either priority (capacity that the district has direct ownership over) or secondary (excess capacity that isn't being used by the owner)
    elif search_type == 'banking':
      priority_toggle = 0
      for canal_obj in priority_list:#canals that have 'priority' from the given reservoir
        if canal_obj.name == contract_canal:#current canal
          priority_toggle = 1
      if priority_toggle == 1:
        demand_dict['priority'] = max(min(demand,delivery), 0.0)
        demand_dict['secondary'] = min(delivery - demand_dict['priority'], demand_constraint - demand_dict['priority'])
      else:
        demand_dict['priority'] = 0.0
        demand_dict['secondary'] = max(min(delivery, demand_constraint), 0.0)

    #recovery is the same priority structure as banking, but we use different names (initial & supplemental) to keep things straight)
    elif search_type == 'recovery':
      if self.in_leiu_banking:
        demand_dict['initial'] = max(min(demand,delivery), 0.0)
        demand_dict['supplemental'] = min(delivery - demand_dict['initial'], demand_constraint - demand_dict['initial'])
      else:
        demand_dict['initial'] = 0.0
        demand_dict['supplemental'] = 0.0

    return demand_dict



  cdef double find_leiu_priority_space(self, double demand_constraint, int num_members, str member_name, int toggle_recharge, str search_type):
    #this function finds how much 'priority' space in the recharge/recovery capacity is owned by a member (member_name) in a given in-leiu bank (i.e. this function is attached to the district that owns the bank - and the banking member is represented by 'member_name' input variable)
    cdef double priority_space, available_banked, initial_capacity

    if search_type == "recovery":
      priority_space = max(min(self.leiu_recovery*self.leiu_ownership[member_name] - self.recovery_use[member_name], demand_constraint), 0.0)
      available_banked = self.inleiubanked[member_name]
      return min(priority_space, available_banked)
    else:
      initial_capacity = self.dailydemand_start[0]*self.surface_water_sa*self.seepage
      if toggle_recharge == 1:
        initial_capacity += self.in_district_storage
      priority_space = max(min((self.leiu_ownership[member_name]*initial_capacity - self.bank_deliveries[member_name]), demand_constraint)/num_members, 0.0)
      return priority_space


  cdef (double, double, double) set_deliveries(self, dict priorities, dict type_fractions, list type_list, str search_type, int toggle_district_recharge, str member_name, int wateryear):
    #this function takes the deliveries, seperated by priority, and updates the district's daily demand and/or recharge storage
    cdef:
      double final_deliveries, total_direct_deliveries, total_recharge_deliveries, total_deliveries, private
      str zz, xx

    final_deliveries = 0.0
    total_direct_deliveries = 0.0
    total_recharge_deliveries = 0.0
    for zz in type_list:
      total_deliveries = priorities[zz]*type_fractions[zz]
      final_deliveries += total_deliveries
	  
    if self.has_private == 1:
      private = 0.0
      for xx in self.private_demand:
        private += min(self.private_demand[xx], self.private_delivery[xx])
      if search_type == 'flood':
        total_recharge_deliveries = min(max(final_deliveries - private, 0.0), self.in_district_storage - self.current_recharge_storage)
        total_direct_deliveries = min(max(final_deliveries - private - total_recharge_deliveries, 0.0)/self.seepage, self.dailydemand[0]*self.surface_water_sa)
      else:
        total_direct_deliveries = min(max(final_deliveries - private, 0.0)/self.seepage, self.dailydemand[0]*self.surface_water_sa)
        if toggle_district_recharge == 1:
          total_recharge_deliveries = min(max((final_deliveries - private)/self.seepage - total_direct_deliveries, 0.0), self.in_district_storage - self.current_recharge_storage)
        else:
          total_recharge_deliveries = 0.0
      self.dailydemand[0] -= total_direct_deliveries
      self.current_recharge_storage += total_recharge_deliveries
    else:
      if search_type == 'flood':
        total_recharge_deliveries = min(max(final_deliveries, 0.0), self.in_district_storage - self.current_recharge_storage)
        total_direct_deliveries = min(max(final_deliveries - total_recharge_deliveries, 0.0)/self.seepage, self.dailydemand[0]*self.surface_water_sa)
      else:
        total_direct_deliveries = min(max(final_deliveries, 0.0)/self.seepage, self.dailydemand[0]*self.surface_water_sa)
        if toggle_district_recharge == 1:
          total_recharge_deliveries = min(max((final_deliveries)/self.seepage - total_direct_deliveries, 0.0), self.in_district_storage - self.current_recharge_storage)
        else:
          total_recharge_deliveries = 0.0
      self.dailydemand[0] -= total_direct_deliveries
      self.current_recharge_storage += total_recharge_deliveries
		
    return total_direct_deliveries, total_recharge_deliveries, final_deliveries - total_direct_deliveries - total_recharge_deliveries
				
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################ADJUSST ACCOUNTS AFTER DELIVERY####################################################
#####################################################################################################################

  cdef double give_paper_trade(self, double trade_amount, list contract_list, int wateryear, str district_name):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
  	#trade, giving up a surface water contract allocation (contract_list) to the district
  	#that owned the groundwater that was recovered
    cdef:
      double total_alloc, actual_delivery
      Contract contract_obj

    if self.seepage > 0.0:
      total_alloc = 0.0
      for contract_obj in contract_list:
        total_alloc += self.projected_supply[contract_obj.name]
      actual_delivery = min(trade_amount, total_alloc, self.dailydemand[0]*self.seepage*self.surface_water_sa)
      self.dailydemand[0] -= actual_delivery/self.seepage	  
      if total_alloc > 0.0:
        for contract_obj in contract_list:
          self.paper_balance[contract_obj.name] -= actual_delivery*self.projected_supply[contract_obj.name]/total_alloc
		  
      self.deliveries['exchanged_SW'][wateryear] += actual_delivery

    return actual_delivery 
		

  cdef void give_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear, str district_name):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
    #trade, giving up a surface water contract allocation (contract_list) to the district
    #that owned the groundwater that was recovered
    cdef:
      int contract_counter
      str contract_key

    contract_counter = 0
    for contract_key in contract_list:
      self.paper_balance[contract_key] -= trade_amount*trade_frac[contract_counter]
      contract_counter += 1
    self.deliveries['exchanged_SW'][wateryear] += trade_amount
	  

  cdef void get_paper_trade(self, double trade_amount, list contract_list, int wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	  #the paper credit is in exchange for delivering recovered groundwater to another party (district)
    cdef:
      double total_alloc, contract_frac
      Contract contract_obj

    total_alloc = 0.0
    for contract_obj in contract_list:
      total_alloc += self.projected_supply[contract_obj.name]
    if total_alloc > 0.0:
      for contract_obj in contract_list:
        self.paper_balance[contract_obj.name] += trade_amount*self.projected_supply[contract_obj.name]/total_alloc
    else:
      contract_frac = 1.0
      for y in contract_list:
        self.paper_balance[y.name] += trade_amount*contract_frac
        contract_frac = 0.0
    self.deliveries['exchanged_GW'][wateryear] += trade_amount


  cdef void get_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	  #the paper credit is in exchange for delivering recovered groundwater to another party (district)
    cdef:
      double total_alloc, contract_frac
      int contract_counter
      str y

    total_alloc = 0.0
    contract_frac = 0.0
    contract_counter = 0
    for y in contract_list:
      self.paper_balance[y] += trade_amount*trade_frac[contract_counter]
      contract_counter += 1
    self.deliveries['exchanged_GW'][wateryear] += trade_amount


  cdef double record_direct_delivery(self, double delivery, int wateryear):
    cdef double actual_delivery

    actual_delivery = min(delivery, self.dailydemand[0]*self.seepage*self.surface_water_sa)
    self.deliveries['recover_banked'][wateryear] += actual_delivery
    self.dailydemand[0] -= actual_delivery/(self.seepage*self.surface_water_sa)
    self.direct_recovery_delivery = 0.0
    return actual_delivery



  cdef double direct_delivery_bank(self, double delivery, int wateryear):
    #this function takes a delivery of recoverd groundwater and applies it to irrigation demand in a district
	  #the recovered groundwater is delivered to the district that originally owned the water, so no 'paper' trade is needed
    cdef double direct_delivery, actual_delivery

    direct_delivery = self.dailydemand[0]*self.seepage*self.surface_water_sa - self.direct_recovery_delivery
    actual_delivery = min(delivery, direct_delivery)
    #self.deliveries['recover_banked'][wateryear] += actual_delivery
    self.direct_recovery_delivery += actual_delivery
    #self.dailydemand[0] -= actual_delivery/self.seepage*self.surface_water_sa
    return actual_delivery
	

  cdef dict adjust_accounts(self, double direct_deliveries, double recharge_deliveries, list contract_list, str search_type, int wateryear, str delivery_location):
    #this function accepts water under a specific condition (flood, irrigation delivery, banking), and 
	  #adjusts the proper accounting balances
    cdef:
      double total_carryover_recharge, total_current_balance, contract_deliveries
      int flood_counter
      dict delivery_by_contract
      Contract contract_obj

    total_carryover_recharge = 0.0
    total_current_balance = 0.0
    delivery_by_contract = {}
    for contract_obj in contract_list:
      if search_type == 'flood':
        total_current_balance += 1.0
      elif search_type == 'delivery':
        total_current_balance += max(self.projected_supply[contract_obj.name], 0.0)
      elif search_type == 'banking':
        total_current_balance += max(self.recharge_carryover[contract_obj.name], 0.0)
      elif search_type == 'recovery':
        total_current_balance += max(self.current_balance[contract_obj.name], 0.0)
      delivery_by_contract[contract_obj.name] = 0.0
    flood_counter = 0
    for contract_obj in contract_list:
      #find the percentage of total deliveries that come from each contract
      if search_type == 'flood':
          if flood_counter == 0:
            contract_deliveries = (direct_deliveries + recharge_deliveries)
            flood_counter = 1
          else:
            contract_deliveries = 0.0
      elif total_current_balance > 0.0:
        if search_type == 'delivery':
          contract_deliveries = (direct_deliveries + recharge_deliveries)*max(self.projected_supply[contract_obj.name], 0.0)/total_current_balance
        elif search_type == 'banking':
          contract_deliveries = (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[contract_obj.name], 0.0)/total_current_balance
        elif search_type == 'recovery':
          contract_deliveries = (direct_deliveries + recharge_deliveries)*max(self.current_balance[contract_obj.name], 0.0)/total_current_balance

      else:
        contract_deliveries = 0.0
      delivery_by_contract[contract_obj.name] = contract_deliveries
      #flood deliveries do not count against a district's contract allocation, so the deliveries are recorded as 'flood'
      if search_type == "flood":
        if contract_deliveries > 0.0:
          self.deliveries[contract_obj.name + '_flood'][wateryear] += recharge_deliveries
          self.deliveries[contract_obj.name + '_flood_irrigation'][wateryear] += direct_deliveries
          self.deliveries[delivery_location + '_recharged'][wateryear] += recharge_deliveries
      else:
        #irrigation/banking deliveries are recorded under the contract name so they are included in the contract balance calculations
        #update the individual district accounts
        self.deliveries[contract_obj.name][wateryear] += contract_deliveries
        self.current_balance[contract_obj.name] -= contract_deliveries
        if search_type == 'banking':
          #if deliveries ar for banking, update banking accounts
          self.deliveries[delivery_location + '_recharged'][wateryear] += recharge_deliveries
          self.deliveries[contract_obj.name + '_recharged'][wateryear] += contract_deliveries
          self.recharge_carryover[contract_obj.name] -= min(contract_deliveries, self.recharge_carryover[contract_obj.name])
    int_sum = 0.0

    return delivery_by_contract
	

  cdef void adjust_bank_accounts(self, str member_name, double direct_deliveries, double recharge_deliveries, int wateryear):
    #when deliveries are made for banking, keep track of the member's individual accounts
    self.bank_deliveries[member_name] += direct_deliveries + recharge_deliveries#keeps track of how much of the capacity is being used in the current timestep
    self.deliveries['inleiu_irrigation'][wateryear] += direct_deliveries#if deliveries being made 'inleiu', then count as inleiu deliveries
    self.deliveries['inleiu_recharge'][wateryear] += recharge_deliveries#if deliveries being made 'inleiu', then count as inleiu deliveries
    self.inleiubanked[member_name] += (direct_deliveries + recharge_deliveries) * self.inleiuhaircut#this is the running account of the member's banking storage
	

  cdef void adjust_recovery(self, double deliveries, str member_name, int wateryear):
    #if recovery deliveries are made, adjust the banking accounts and account for the recovery capacity use
    self.inleiubanked[member_name] -= deliveries#this is the running account of the member's banking storage
    self.deliveries['leiupumping'][wateryear] += deliveries
    self.recovery_use[member_name] += deliveries#keeps track of how much of the capacity is being used in the current timestep


  cdef void adjust_exchange(self, double deliveries, str member_name, int wateryear):
    #if recovery deliveries are made, adjust the banking accounts and account for the recovery capacity use
    self.inleiubanked[member_name] -= deliveries#this is the running account of the member's banking storage
    self.deliveries['leiupumping'][wateryear] += deliveries
    self.contract_exchange[member_name][wateryear] += deliveries

	
  def absorb_storage(self):
    #water delivered to a bank as 'storage' (on the surface) is 'absorbed', clearing up storage space for the next timestep
    #also triggers self.thismonthuse, which keeps track of how many conecutive months a recharge bank is used (and the effect on the recharge rate of the spreading pool)
    if self.in_leiu_banking:
      if self.current_recharge_storage > self.recharge_rate*0.75:
        self.thismonthuse = 1
      if self.current_recharge_storage > 0.0:
        absorb_fraction = min(self.in_district_direct_recharge*cfs_tafd/self.current_recharge_storage,1.0)
        for x in self.participant_list:
          self.current_recharge_storage -= self.current_recharge_storage*absorb_fraction
    else:
      if self.current_recharge_storage > self.recharge_rate*0.75:
        self.thismonthuse = 1
      if self.current_recharge_storage > 0.0:
        absorb_fraction = min(self.recharge_rate/self.current_recharge_storage,1.0)
      self.current_recharge_storage -= self.current_recharge_storage*absorb_fraction
    self.current_recharge_storage = max(self.current_recharge_storage, 0.0)

#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################RECORD STATE VARIABLES###############################################################
#####################################################################################################################

  def reset_recharge_recovery(self):
    self.max_direct_recharge = [0. for _ in range(12)]
    self.max_leiu_recharge = [0. for _ in range(12)]
    self.total_banked_storage = 0.0
    self.max_leiu_exchange = 0.0


  cdef void set_daily_supplies_full(self, str key, double value, int t):
    ### only create timeseries for keys that actually ever triggered
    if abs(value) > 1e-13:
      try:
        self.daily_supplies_full[key][t] = value
      except:
        self.daily_supplies_full[key] =  np.zeros(self.T)
        self.daily_supplies_full[key][t] = value


  cdef void accounting_full(self, int t, int wateryear):
    cdef str x

    # keep track of all contract amounts
    for x in self.contract_list_all:
      ### only store info for contracts that actually happen
      self.set_daily_supplies_full(x + '_delivery', self.deliveries[x][wateryear], t)
      self.set_daily_supplies_full(x + '_flood', self.deliveries[x + '_flood'][wateryear], t)
      self.set_daily_supplies_full(x + '_flood_irrigation', self.deliveries[x + '_flood_irrigation'][wateryear], t)
      self.set_daily_supplies_full(x + '_recharged', self.deliveries[x + '_recharged'][wateryear], t)
      self.set_daily_supplies_full(x + '_projected', self.projected_supply[x], t)
      self.set_daily_supplies_full(x + '_paper', self.paper_balance[x], t)
      self.set_daily_supplies_full(x + '_carryover', self.carryover[x], t)
      self.set_daily_supplies_full(x + '_turnback', self.turnback_pool[x], t)
      self.set_daily_supplies_full(x + '_dynamic_recharge_cap', self.dynamic_recharge_cap[x], t)

    for x in self.delivery_location_list:
      self.set_daily_supplies_full(x + '_recharged', self.deliveries[x + '_recharged'][wateryear], t)

    for x in self.non_contract_delivery_list:
      self.set_daily_supplies_full(x, self.deliveries[x][wateryear], t)
      
    self.set_daily_supplies_full('pumping', self.annual_private_pumping, t)
    self.set_daily_supplies_full('irr_demand', self.dailydemand_start[0], t)
    self.set_daily_supplies_full('tot_demand', self.annualdemand[0], t)
    self.set_daily_supplies_full('recover_banked', self.deliveries['recover_banked'][wateryear], t)
    self.set_daily_supplies_full('inleiu_irrigation', self.deliveries['inleiu_irrigation'][wateryear], t)
    self.set_daily_supplies_full('inleiu_recharge', self.deliveries['inleiu_recharge'][wateryear], t)
    self.set_daily_supplies_full('leiupumping', self.deliveries['leiupumping'][wateryear], t)
    self.set_daily_supplies_full('exchanged_GW', self.deliveries['exchanged_GW'][wateryear], t)
    self.set_daily_supplies_full('exchanged_SW', self.deliveries['exchanged_SW'][wateryear], t)
    self.set_daily_supplies_full('dynamic_recovery_cap', self.recovery_capacity_remain, t)

  
  cdef void accounting_leiubank(self, int t):
    #takes banked storage (in in-leiu banks) and builds timeseries of member accounts
    cdef:
      double stacked_amount
      str x 
      
    stacked_amount = 0.0
    self.recharge_rate_series.append(self.recharge_rate)
    for x in self.participant_list:
      self.bank_timeseries[x][t] = self.inleiubanked[x]
      stacked_amount += self.inleiubanked[x]
