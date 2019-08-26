from __future__ import division
import numpy as np 
import matplotlib.pyplot as plt
import collections as cl
import pandas as pd
from .crop import Crop
from .scenario import Scenario
import json
from .util import *


class District():

  def __init__(self, df, name, key, scenario_file = 'baseline'):
    self.T = len(df)
    self.starting_year = df.index.year[0]
    self.number_years = df.index.year[-1]-df.index.year[0]
    self.key = key
    self.name = name
    self.leap = leap(np.arange(min(df.index.year), max(df.index.year) + 2))
    year_list = np.arange(min(df.index.year), max(df.index.year) + 2)
    self.days_in_month = days_in_month(year_list, self.leap)
    self.dowy_eom = dowy_eom(year_list, self.leap)
    self.non_leap_year = first_non_leap_year(self.dowy_eom)
    self.turnback_use = True

    for k, v in json.load(open('cord/districts/%s_properties.json' % key)).items():
      setattr(self, k, v)
    if ((scenario_file == 'baseline') == False):
      for k,v in json.load(open(scenario_file)).items():
          setattr(self,k,v)

    #intialize crop acreages and et demands for crops
    self.irrdemand = Crop(self.zone)
	#initialize dictionary to hold different delivery types
    self.deliveries = {}
    self.contract_list_all = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2','kaweah', 'tule', 'kern','kings']
    self.non_contract_delivery_list = ['recover_banked','inleiu_irrigation','inleiu_recharge','leiupumping','recharged','exchanged_GW','exchanged_SW','undelivered_trades']

    for x in self.contract_list_all:
      #normal contract deliveries
      self.deliveries[x] = np.zeros(self.number_years)
	    #uncontrolled deliveries from contract
      self.deliveries[x + '_flood'] = np.zeros(self.number_years)
      # contract-specific recharge (same as 'recharged', but disaggregated)
      self.deliveries[x + '_recharged'] = np.zeros(self.number_years)
    #deliveries from a groundwater bank (reocrded by banking partner recieving recovery water)
      self.deliveries[x+ '_flood_irrigation'] = np.zeros(self.number_years)
	#deliveries from a groundwater bank (reocrded by banking partner recieving recovery water)
    self.deliveries['recover_banked'] = np.zeros(self.number_years)
	#deliveries to a in-leiu bank from a banking partner (recorded by the district acting as a bank)
    self.deliveries['inleiu_irrigation'] = np.zeros(self.number_years)
    self.deliveries['inleiu_recharge'] = np.zeros(self.number_years)

	#deliveries from an in leiu bank to a banking partner (recorded by the district acting as a bank)
    self.deliveries['leiupumping'] = np.zeros(self.number_years)
	#water delivered from a contract to a recharge basin (direct or in leiu, recorded by the banking partner who owned the water)
    self.deliveries['recharged'] = np.zeros(self.number_years)
    #deliveries made from a districts bank to third-party district (district recieves a surface water 'paper' credit)
    self.deliveries['exchanged_GW'] = np.zeros(self.number_years)
    #recorded when a district recieves water from a bank owned by another district (district gives a surface water 'paper' credit)
    self.deliveries['exchanged_SW'] = np.zeros(self.number_years)
    self.deliveries['undelivered_trades'] = np.zeros(self.number_years)
	
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
	  
    #initialize dictionaries to 'store' daily state variables (for export to csv)
    self.daily_supplies = {}
    supply_list = ['paper', 'carryover', 'allocation', 'delivery', 'flood_irrigation', 'leiu_applied', 'leiu_recharged', 'banked', 'pumping', 'leiu_delivered', 'recharge_delivery', 'recharge_uncontrolled']
    for x in supply_list:
      self.daily_supplies[x] = np.zeros(self.T)

    #initialize dictionaries to 'store' annual change in state variables (for export to csv)
    self.annual_supplies = {}
    supply_list = ['delivery', 'flood_irrigation', 'leiu_applied','leiu_recharged', 'leiu_delivered', 'banked_accepted']
    for x in supply_list:
      self.annual_supplies[x] = np.zeros(self.number_years)

    # hold all output
    self.daily_supplies_full = {}
    # delivery_list = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2','kaweah', 'tule', 'kern']
    for x in self.contract_list_all:
      self.daily_supplies_full[x + '_delivery'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_flood'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_flood_irrigation'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_recharged'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_projected'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_paper'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_carryover'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_turnback'] = np.zeros(self.T)
    for x in self.non_contract_delivery_list:
      self.daily_supplies_full[x] = np.zeros(self.T)
    self.daily_supplies_full['pumping'] = np.zeros(self.T)
    self.daily_supplies_full['irr_demand'] = np.zeros(self.T)

    # ['recover_banked', 'inleiu', 'leiupumping', 'recharged', 'exchanged_GW', 'exchanged_SW', 'undelivered_trades']
    #Initialize demands
    self.annualdemand = 0.0
    self.dailydemand = 0.0

    #recovery and pumping variables
    #self.recovery_fraction = 0.5
    self.annual_pumping = 0.0
    self.use_recharge = 0.0
    self.use_recovery = 0.0
    self.extra_leiu_recovery = 0.0
    self.max_recovery = 0.0
    self.max_leiu_exchange = 0.0
    self.direct_recovery_delivery = 0.0

	
    #for in-district recharge & counters (for keeping track of how long a basin has been continuously 'wet'
    self.recharge_rate = self.in_district_direct_recharge*cfs_tafd
    self.thismonthuse = 0
    self.monthusecounter = 0
    self.monthemptycounter = 0
    self.current_recharge_storage = 0.0
    self.private_fraction = 0.0
    self.has_private = False
    self.has_pesticide = False
    self.has_pmp = False
	
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
      self.annual_timeseries = {}
      self.recharge_rate_series = np.zeros(self.T)
      self.use_recovery = 0.0
      self.leiu_trade_cap = 0.5
      for x in self.participant_list:
        self.recovery_use[x] = 0.0
        self.inleiubanked[x] = 0.0
        self.leiu_additional_supplies[x] = 0.0
        self.bank_deliveries[x] = 0.0
        self.direct_storage[x] = 0.0
        self.bank_timeseries[x] = np.zeros(self.T)
        self.annual_timeseries[x] = np.zeros(self.T)
        self.contract_exchange[x] = np.zeros(self.T)


		
  def object_equals(self, other):
    ##This function compares two instances of an object, returns True if all attributes are identical.
    equality = {}
    if (self.__dict__.keys() != other.__dict__.keys()):
      return ('Different Attributes')
    else:
      differences = 0
      for i in self.__dict__.keys():
        if type(self.__getattribute__(i)) is dict:
          equality[i] = True
          for j in self.__getattribute__(i).keys():
            if (type(self.__getattribute__(i)[j] == other.__getattribute__(i)[j]) is bool):
              if ((self.__getattribute__(i)[j] == other.__getattribute__(i)[j]) == False):
                equality[i] = False
                differences += 1
            else:
              if ((self.__getattribute__(i)[j] == other.__getattribute__(i)[j]).all() == False):
                equality[i] = False
                differences += 1
        else:
          if (type(self.__getattribute__(i) == other.__getattribute__(i)) is bool):
            equality[i] = (self.__getattribute__(i) == other.__getattribute__(i))
            if equality[i] == False:
              differences += 1
          else:
            equality[i] = (self.__getattribute__(i) == other.__getattribute__(i)).all()
            if equality[i] == False:
              differences += 1
    return (differences == 0)



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

  def find_baseline_demands(self,wateryear):
    self.monthlydemand = {}
    wyt_list = ['W', 'AN', 'BN', 'D', 'C']
    
    for wyt in wyt_list:
      self.monthlydemand[wyt] = np.zeros(12)
      for monthloop in range(0,12):
        self.monthlydemand[wyt][monthloop] += self.urban_profile[monthloop]*self.MDD/self.days_in_month[self.non_leap_year][monthloop]
        if self.has_pesticide:
          for i,v in enumerate(self.acreage_by_year):
            self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][wyt][monthloop] - self.irrdemand.etM['precip'][wyt][monthloop],0.0)*(self.acreage_by_year[v][wateryear]-self.private_acreage[v][wateryear])/(12.0*self.days_in_month[self.non_leap_year][monthloop])
        elif self.has_pmp:
          for crop in self.pmp_acreage:
            self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[crop][wyt][monthloop] - self.irrdemand.etM['precip'][wyt][monthloop],0.0)*max(self.pmp_acreage[crop]-self.private_acreage[crop], 0.0)/(12.0*self.days_in_month[self.non_leap_year][monthloop])
        else:
          for i,v in enumerate(self.crop_list):
            self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][wyt][monthloop] - self.irrdemand.etM['precip'][wyt][monthloop],0.0)*(self.acreage[wyt][i]-self.private_acreage[v])/(12.0*self.days_in_month[self.non_leap_year][monthloop])
          #self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][wyt][monthloop] ,0.0)*self.acreage[wyt][i]/(12.0*self.days_in_month[self.non_leap_year][monthloop])
	  	
			
  def calc_demand(self, wateryear, year, da, m, m1, wyt):
    #from the monthlydemand dictionary (calculated at the beginning of each wateryear based on ag acreage and urban demands), calculate the daily demand and the remaining annual demand
    monthday = self.days_in_month[year][m-1]
    self.dailydemand = self.monthlydemand[wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[wyt][m1-1]*da/monthday
    if self.dailydemand < 0.0:
      self.dailydemand = 0.0
    #calculate that days 'starting' demand (b/c demand is filled @multiple times, and if we only want to fill a certain fraction of that demand (based on projections of supply & demand for the rest of the year), we want to base that fraction on that day's total demand, not the demand left after other deliveries are made
    self.dailydemand_start = self.monthlydemand[wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[wyt][m1-1]*da/monthday
	#pro-rate this month's demand based on the day of the month when calculating remaining annual demand
    self.annualdemand = max(self.monthlydemand[wyt][m-1]*(monthday-da), 0.0)
    self.irrseasondemand = 0.0
    for irrseason in range(6,9):
      self.irrseasondemand += max(self.monthlydemand[wyt][irrseason]*self.days_in_month[year][irrseason], 0.0)
    if m > 9:
      for monthloop in range(m, 12):
        self.annualdemand += max(self.monthlydemand[wyt][monthloop]*self.days_in_month[year][monthloop],0.0)
      for monthloop in range(0,9):
        self.annualdemand += max(self.monthlydemand[wyt][monthloop]*self.days_in_month[year+1][monthloop], 0.0)
    else:
      for monthloop in range(m, 9):
        self.annualdemand += max(self.monthlydemand[wyt][monthloop]*self.days_in_month[year][monthloop], 0.0)
		
		
  def find_pre_flood_demand(self, wyt, year):
    #calculates an estimate for water use in the Oct-Dec period (for use in recharge_carryover calculations), happens Oct 1
    self.pre_flood_demand = self.monthlydemand[wyt][9]*self.days_in_month[year][9] + self.monthlydemand[wyt][10]*self.days_in_month[year][10] + self.monthlydemand[wyt][11]*self.days_in_month[year][11]
		  
  def get_urban_demand(self, t, m, da, wateryear, year, sri, dowy, total_delta_pumping):
    #this function finds demands for the 'branch pumping' urban nodes - Socal, South Bay, & Central Coast
	#demand is equal to pumping of the main california aqueduct and into the branches that services these areas
    #cal aqueduct urban demand comes from pumping data, calc seperately
    if self.has_private:
      if self.has_pesticide:
        frac_to_district = 1.0 - self.private_fraction[wateryear]
      else:
        frac_to_district = 1.0 - self.private_fraction
    else:
      frac_to_district = 1.0
	  
    self.dailydemand = self.pumping[t]/1000.0
    self.dailydemand_start = self.dailydemand
    ##Keep track of ytd pumping to Cal Aqueduct Branches
    self.ytd_pumping[wateryear] += self.dailydemand
    sri_estimate = (sri*self.delivery_percent_coefficient[dowy][0] + self.delivery_percent_coefficient[dowy][1])*total_delta_pumping*frac_to_district
    self.annualdemand = max(0.0, (self.annual_pumping[wateryear]*dowy + sri_estimate*(364.0 - dowy))/364.0 - self.ytd_pumping[wateryear])
    if m == 10 and da == 1:
      start_of_month = 0
      cross_counter_y = 0
	  ###Divide aqueduct branch pumping into 'monthly demands'
      for monthloop in range(0,12):
        monthcounter = monthloop + 9
        if monthcounter > 11:
          monthcounter -= 12
          cross_counter_y = 1
        start_next_month = self.dowy_eom[year+cross_counter_y][monthcounter] + 1
        for wyt in ['W', 'AN', 'BN', 'D', 'C']:
          self.monthlydemand[wyt][monthcounter] = np.mean(self.pumping[(t + start_of_month):(t + start_next_month)])/1000.0
        start_of_month = start_next_month
		
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

		
  def update_balance(self, t, wateryear, water_available, projected_allocation, current_water, key, tot_carryover, balance_type):
    ###This function takes input from the contract class (water_available, projected_allocation, tot_carryover) to determine how much of their allocation remains
	##water_available is the current contract storage in the reservoir *plus* all deliveries from the given year.  The deliveries, paper trades, and turnback pool accounts for each district
	##are used to get a running tally of the surface water that is currently available to them.  (tot_carryover is subtracted from the current balance - districts only get access to *their* 
	##carryover storage - which is added to their individual current balance (self.carryover[key])
	##projected_allocation is the water that is forecasted to be available on each contract through the end of the water year *plus* water that has already been delivered on that contract
	##individual deliveries are then subtracted from this total to determine the individual district's projected contract allocation remaining in that year
    if self.has_private:
      if self.has_pesticide:
        frac_to_district = 1.0 - self.private_fraction[wateryear]
      else:
        frac_to_district = 1.0 - self.private_fraction
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
    if key == 'xxx' or key == 'xxx':
      if self.rights[key]['capacity'] > 0.0:
        print(wateryear, end = " ")
        print(t, end = " ")
        print(self.key, end = " ")
        print(key, end = " ")
        print("%.2f" % projected_allocation, end = " ")
        print("%.2f" % annual_allocation, end = " ")
        print("%.2f" % frac_to_district, end = " ")
        print("%.2f" % current_water, end = " ")
        print("%.2f" % tot_carryover, end = " ")
        print("%.2f" % self.deliveries[key][wateryear], end = " ")
        print("%.2f" % self.carryover[key], end = " ")
        print("%.2f" % self.paper_balance[key], end = " ")
        print("%.2f" % self.turnback_pool[key], end = " ")
        print("%.2f" % self.current_balance[key], end = " ")
        print("%.2f" % self.projected_supply[key], end = " ")
        print("%.2f" % self.annualdemand, end = " ")
        print("%.2f" % self.dailydemand, end = " ")
        print("%.2f" % self.recharge_carryover[key], end = " ")
        print("%.2f" % self.use_recovery)
    elif key == 'xxx' or key == 'xxx':
      if self.project_contract[key] > 0.0:
        print(wateryear, end = " ")
        print(t, end = " ")
        print(self.key, end = " ")
        print(key, end = " ")
        print("%.2f" % projected_allocation, end = " ")
        print("%.2f" % annual_allocation, end = " ")
        print("%.2f" % frac_to_district, end = " ")
        print("%.2f" % current_water, end = " ")
        print("%.2f" % tot_carryover, end = " ")
        print("%.2f" % self.deliveries[key][wateryear], end = " ")
        print("%.2f" % self.carryover[key], end = " ")
        print("%.2f" % self.paper_balance[key], end = " ")
        print("%.2f" % self.turnback_pool[key], end = " ")
        print("%.2f" % self.current_balance[key], end = " ")
        print("%.2f" % self.projected_supply[key], end = " ")
        print("%.2f" % self.annualdemand, end = " ")
        print("%.2f" % self.dailydemand, end = " ")
        print("%.2f" % self.recharge_carryover[key], end = " ")
        print("%.2f" % self.use_recovery)
	  


    return max(self.projected_supply[key] - self.annualdemand, 0.0) , max(self.carryover[key] - self.deliveries[key][wateryear], 0.0)
	

  def calc_carryover(self, existing_balance, wateryear, balance_type, key):
    #at the end of each wateryear, we tally up the full allocation to the contract, how much was used (and moved around in other balances - carryover, 'paper balance' and turnback_pools) to figure out how much each district can 'carryover' to the next year
    if self.has_private:
      if self.has_pesticide:
        frac_to_district = 1.0 - self.private_fraction[wateryear]
      else:
        frac_to_district = 1.0 - self.private_fraction
    else:
      frac_to_district = 1.0

    if balance_type == 'contract':
      annual_allocation = existing_balance*self.project_contract[key]*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      max_carryover = self.contract_carryover_list[key]
    elif balance_type == 'right':
      annual_allocation = existing_balance*self.rights[key]['capacity']*frac_to_district - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      max_carryover = self.contract_carryover_list[key]

    reallocated_water = max(annual_allocation - max_carryover, 0.0)
    self.carryover[key] = min(max_carryover, annual_allocation)
    self.paper_balance[key] = 0.0
    self.turnback_pool[key] = 0.0
	
    return reallocated_water, self.carryover[key]
		
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################RECHARGE/RECOVERY TRIGGERS#########################################################
#####################################################################################################################
	
  def open_recovery(self,t, dowy, wateryear):
    #this function determines if a district wants to recover banked water
	#based on their demands and existing supplies
    total_balance = 0.0
    total_recovery = (366-dowy)*self.max_recovery + self.extra_leiu_recovery
    
    existing_carryover = 0.0
    for key in self.contract_list:
      total_balance += self.projected_supply[key]
      existing_carryover += max(self.carryover[key] - self.deliveries[key][wateryear], 0.0)
	
    total_needs = self.annualdemand*self.seepage*self.surface_water_sa*self.recovery_fraction
    if (total_balance + total_recovery) < total_needs:
      if existing_carryover > 0.0:
        self.use_recovery = 0.0
      else:
        self.use_recovery = 1.0
    else:
      self.use_recovery = 0.0
	  	  
    self.min_direct_recovery = max(self.annualdemand - total_balance,0.0)/(366-dowy)
    
	  	  
  def open_recharge(self,t,m,da,wateryear,year,numdays_fillup, numdays_fillup2, contract_carryover, key, wyt, reachable_turnouts, additional_carryover, contract_allocation):
    #for a given contract owned by the district (key), how much recharge can they expect to be able to use
	#before the reservoir associated w/ that contract fills to the point where it needs to begin spilling water
	#(numdays_fillup) - i.e., how much surface water storage can we keep before start losing it
	#self.recharge_carryover is the district variable that shows how much 'excess' allocation there is on a particular
	#contract - i.e., how much of the allocation will not be able to be recharged before the reservoir spills
    total_recharge = 0.0
    total_recharge2 = 0.0
    carryover_storage_proj = 0.0
    spill_release_carryover = 0.0
    is_reachable = 0
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
      #total_recharge_available = 0.0
      #for y in self.contract_list:
        #total_recharge_available += self.projected_supply[y]  
      #total_recharge_available -= self.annualdemand*adjusted_sw_sa*self.seepage

      ###Find projected recharge available to district
      #if total_recharge_available > 0.0:
        #total_recharge_capacity = (self.max_direct_recharge[0] + self.max_leiu_recharge[m])*(self.days_in_month[year][m]-da)
        ##calculate both direct & in leiu recharge available to the district through the end of this water year
        #if m < 8:
          #for future_month in range(m+1,9):
            #total_recharge_capacity += self.max_direct_recharge[future_month - m]*self.days_in_month[year][future_month] + self.max_leiu_recharge[future_month]*self.days_in_month[year][future_month]
        #elif m > 8:
          #for future_month in range(m+1,12):
            #total_recharge_capacity += self.max_direct_recharge[future_month - m]*self.days_in_month[year][future_month] + self.max_leiu_recharge[future_month]*self.days_in_month[year][future_month]
          #for future_month in range(0,9):
            #total_recharge_capacity += self.max_direct_recharge[future_month - m]*self.days_in_month[year+1][future_month] + self.max_leiu_recharge[future_month]*self.days_in_month[year][future_month]
      #else:
        #total_recharge_capacity = 0.0
	  
      #spill_release_carryover = max(total_recharge_available - total_recharge_capacity - additional_carryover, 0.0)

      ##how many days remain before the reservoir fills? 		  
      days_left = numdays_fillup
      days_left2 = numdays_fillup2
	  #tabulate how much water can be recharged between now & reservoir fillup (current month)
      this_month_recharge = (self.max_direct_recharge[0] + self.max_leiu_recharge[0])*min(self.days_in_month[year][m] - da,days_left)
      this_month_recharge2 = (self.max_direct_recharge[0] + self.max_leiu_recharge[0])*min(self.days_in_month[year][m] - da,days_left2)
      total_recharge += this_month_recharge
      total_recharge2 += this_month_recharge2
	  #days before fillup remaining after current month
      days_left -= (self.days_in_month[year][m] - da)
      days_left2 -= (self.days_in_month[year][m] - da)
	
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
        this_month_recharge = (self.max_direct_recharge[monthcounter+monthcounter_loop] + self.max_leiu_recharge[monthcounter+monthcounter_loop])*min(self.days_in_month[year+next_year_counter][m+monthcounter],days_left)
        total_recharge += this_month_recharge
     
        days_left -= self.days_in_month[year+next_year_counter][m+monthcounter]
        
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
        this_month_recharge2 = (self.max_direct_recharge[monthcounter+monthcounter_loop] + self.max_leiu_recharge[monthcounter+monthcounter_loop])*min(self.days_in_month[year+next_year_counter][m+monthcounter],days_left2)
        total_recharge2 += this_month_recharge2


        days_left2 -= self.days_in_month[year+next_year_counter][m+monthcounter]
        
      ###Uses the projected supply calculation to determine when to recharge water.  There are a number of conditions under which a 
	  ###district will recharge water.  Projected allocations are compared to total demand, recharge capacity, and the probability of 
	  ###surface water storage spilling carryover water.  If any of these conditions triggers recharge, the district will release water
	  ##for recharge


      #carryover_storage_proj = max(self.projected_supply[key] - self.annualdemand*adjusted_sw_sa - total_recharge*service_area_adjust - self.contract_carryover_list[key]*adjusted_sw_sa, 0.0)
      spill_release_carryover = 0.0
      for y in self.contract_list:
        spill_release_carryover += max(self.projected_supply[y] - self.carryover_rights[y], 0.0)
        
      spill_release_carryover -= (self.annualdemand*adjusted_sw_sa + total_recharge2*service_area_adjust  + self.demand_days['lookahead'][key])
      spill_release_carryover = max(spill_release_carryover, 0.0)

      carryover_storage_proj = 0.0
      for y in self.contract_list:
        carryover_storage_proj += max(self.carryover[y] - self.deliveries[y][wateryear] - self.carryover_rights[y], 0.0)

      carryover_storage_proj -= (total_recharge*service_area_adjust + self.demand_days['current'][key])
      carryover_storage_proj = max(carryover_storage_proj, 0.0)
		
      #carryover_release_proj = min(carryover_storage_proj, max(total_recharge_available - total_recharge_capacity,0.0))
      #carryover_release_current = max(self.carryover[key] - self.deliveries[key][wateryear] - total_recharge_carryover, 0.0)
      #if contract_carryover > 0.0:
      #spill_release_carryover = max(self.carryover[key] - self.deliveries[key][wateryear] - total_recharge, 0.0)
      #else:
      #spill_release_carryover = max(self.projected_supply[key] - self.annualdemand*adjusted_sw_sa - total_recharge*service_area_adjust - self.contract_carryover_list[key]*adjusted_sw_sa, 0.0)
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
      #if contract_allocation == 0:
        #self.recharge_carryover[key] = max(self.recharge_carryover[key], self.projected_supply[key] - total_recharge*service_area_adjust - self.demand_days['current'][key], 0.0)
      if key == 'xxx' or key == 'xxx' or key == 'xxx' or key == 'xxx':
        print(carryover_storage_proj, end = " ")
        print(spill_release_carryover, end = " ")
        print(total_recharge, end = " ")
        print(self.demand_days['current'][key], end = " ")
        print(total_recharge2, end = " ")
        print(self.demand_days['lookahead'][key], end = " ")
        print(total_available_for_recharge, end = " ")
        print(self.recharge_carryover[key])
      ##Similar conditions also calculate the amount of regular tableA deliveries for direct irrigation to request
    else:
      self.delivery_carryover[key] = 0.0
      self.recharge_carryover[key] = 0.0
	  
  def get_urban_recovery_target(self, pumping, project_contract, wateryear, dowy, year, wyt, demand_days, t, start_month):
    max_pumping_shortfall = 0.0
    pumping_shortfall = 0.0
    if self.has_private:
      if self.has_pesticide:
        frac_to_district = 1.0 - self.private_fraction[wateryear]
      else:
        frac_to_district = 1.0 - self.private_fraction
    else:
      frac_to_district = 1.0

    monthcounter = start_month
    daycounter = 0
    tot_days = 0
    if demand_days > 365.0:
      max_pumping_shortfall = 9999.9
    else:
      while tot_days < demand_days:
        pumping_shortfall += np.sum(self.pumping[(t-dowy+tot_days):(t-dowy+tot_days+min(demand_days -tot_days, 30))]/1000.0) - pumping['swp']['gains'][monthcounter]*project_contract*frac_to_district
        tot_days += 30
        monthcounter += 1
        if monthcounter == 12:
          monthcounter = 0

        max_pumping_shortfall = max(pumping_shortfall, max_pumping_shortfall)
	  
    return max(max_pumping_shortfall, 0.0)
	  
  def set_turnback_pool(self, key, year):
    ##This function creates the 'turnback pool' (note: only for SWP contracts now, can be used for others)
    ##finding contractors with 'extra' contract water that they would like to sell, and contractors who would
    ##like to purchase that water.  
    self.turnback_sales = 0.0
    self.turnback_purchases = 0.0
    total_recharge_ability = 0.0
    total_projected_supply = 0.0
    for y in self.contract_list:
      total_projected_supply += self.projected_supply[y]
      for month_count in range(0, 4):
        # total recharge Jun,Jul,Aug,Sep
        total_recharge_ability += self.max_direct_recharge[month_count]*self.days_in_month[year][month_count + 5]
    
    if total_projected_supply > 0.0:
      contract_fraction = max(min(self.projected_supply[key]/total_projected_supply, 1.0), 0.0)
    else:
      contract_fraction = 0.0
	  
    #districts sell water if their projected contracts are greater than their remaining annual demand, plus their remaining recharge capacity in this water year, plus their recharge capacity in the next water year (through January)
    self.turnback_sales = max(self.projected_supply[key] - self.carryover_rights[key] - (self.annualdemand + total_recharge_ability + self.pre_flood_demand)*contract_fraction, 0.0)
    if self.in_leiu_banking:
      self.turnback_purchases = 0.0
    else:
      ##districts buy turnback water if their annual demands are greater than their projected supply plus their capacity to recover banked groundwater
      self.turnback_purchases = max(self.annualdemand*contract_fraction + self.carryover_rights[key] - self.projected_supply[key] - self.max_recovery*122*contract_fraction, 0.0)

    return self.turnback_sales, self.turnback_purchases	  
      
  def make_turnback_purchases(self, turnback_sellers, turnback_buyers, key):
    #once we know how much water is in the 'selling' pool and the 'buying' pool, we can determine the total turnback pool - min(buying,selling), then
    #determine what % of each request is filled (i.e., if the selling pool is only 1/2 of the buying pool, then buyers only get 1/2 of their request, or visa versa	
    if min(turnback_sellers, turnback_buyers) > 0.0:
      sellers_frac = -1*min(turnback_sellers, turnback_buyers)/turnback_sellers
      buyers_frac = min(turnback_sellers, turnback_buyers)/turnback_buyers
      total_projected_supply = 0.0
      for y in self.contract_list:
      #the buying/selling fractiosn are applied to the same calculations above (about buying or selling needs), and then turnback pools are added/subtracted to the districts contract
        total_projected_supply += self.projected_supply[y]
      if self.turnback_sales > 0.0:
        self.turnback_pool[key] = max(self.turnback_sales, 0.0)*sellers_frac
      elif self.turnback_purchases > 0.0:
        if self.in_leiu_banking:
          self.turnback_pool[key] = 0.0
        else:
          self.turnback_pool[key] = max(self.turnback_purchases, 0.0)*buyers_frac

	
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################DETERMINE DELIVERIES ON CANAL######################################################
#####################################################################################################################

			
  def find_node_demand(self,contract_list, search_type, partial_demand_toggle,  toggle_recharge):
    #this function is used to calculate the current demand at each 'district' node
    access_mult = self.surface_water_sa*self.seepage#this accounts for water seepage & the total district area that can be reached by SW canals (seepage is >= 1.0; surface_water_sa <= 1.0)
	
    total_projected_allocation = 0.0
    private_add = 0.0
    if self.has_private:
      for xx in self.private_demand:
        private_add += min(self.private_demand[xx], self.private_delivery[xx])

    for y in contract_list:
      total_projected_allocation += max(self.projected_supply[y.name], 0.0)#projected allocation

    #percentage of demand filled in the day is equal to the total projected allocation as a percent of annual demand
	#(i.e., if allocations are projected to be 1/2 of annual demand, then they try to fill 50% of daily irrigation demands with surface water
    if self.annualdemand*access_mult > 0.0 and partial_demand_toggle == 1:
      if self.must_fill == 1:
      #pumping to urban branches of the Cal Aqueduct is 'must fill', (i.e., demand is always met)
        total_demand_met = 1.0
      else:
        if self.annualdemand*access_mult > 0.0:
          #total_demand_met = min(max(total_projected_allocation/(self.annualdemand*access_mult), 0.0), 1.0)
          total_demand_met = 1.0
        else:
          total_demand_met = 0.0		
        #total_demand_met = min(max(total_projected_allocation/(self.annualdemand*access_mult), 0.0), 1.0)
    #elif self.annualdemand*access_mult > 0.0:
      #total_demand_met = 1.0 - min(max(total_projected_allocation/(self.annualdemand*access_mult), 0.0), 1.0)
    else:
      total_demand_met = 1.0
    #self.dailydemand_start is the initial daily district demand (self.dailydemand is updated as deliveries are made) - we try to fill the total_demand_met fraction of dailydemand_start, or what remains of demand in self.dailydemand, whichever is smaller
    if search_type == 'flood':
      if self.annualdemand > 0.0 and total_projected_allocation > self.annualdemand:
        #demand_constraint = (1.0 - min(total_projected_allocation/self.annualdemand, 1.0))*max(min(self.dailydemand_start*access_mult*total_demand_met, self.dailydemand*access_mult),0.0)
        demand_constraint = max(min(self.dailydemand_start*access_mult*total_demand_met, self.dailydemand*access_mult),0.0)
      else:
        demand_constraint = max(min(self.dailydemand_start*access_mult*total_demand_met, self.dailydemand*access_mult),0.0)

    else:
      demand_constraint = max(min(self.dailydemand_start*access_mult*total_demand_met, self.dailydemand*access_mult),0.0)
    #if we want to include recharge demands in the demand calculations, add available recharge space
    if toggle_recharge == 1:
      demand_constraint += max(self.in_district_storage - self.current_recharge_storage, 0.0)
    return demand_constraint + private_add
	
  def find_node_output(self):
    #this function calculates the total recovery capacity that is contained in each district node
	#(i.e. in leiu banks)
    if self.in_leiu_banking:
      current_recovery_use = 0.0
      for x in self.recovery_use:
        current_recovery_use += self.recovery_use[x]
      output_constraint = self.leiu_recovery - current_recovery_use
    else:
      output_constraint = 0.0
	  
    return output_constraint
	
  def find_leiu_output(self, contract_list, ownership, member_name, wateryear):
    member_constraint = 0.0
    total_contract = np.zeros(len(self.contract_list))
    if self.in_leiu_banking:
      bank_counter = 0
      for bank_contracts in self.contract_list:
        for exchange_contracts in contract_list:
          if bank_contracts == exchange_contracts.name:
            #member_constraint += max(min(self.current_balance[bank_contracts]*ownership, self.projected_supply[bank_contracts]*ownership, (self.projected_supply[bank_contracts] - self.paper_balance[bank_contracts])*ownership - self.contract_exchange[member_name][wateryear]), 0.0)
            #total_contract[bank_counter] += max(min(self.current_balance[bank_contracts]*ownership, self.projected_supply[bank_contracts]*ownership, (self.projected_supply[bank_contracts] - self.paper_balance[bank_contracts])*ownership - self.contract_exchange[member_name][wateryear]), 0.0)
            member_constraint += max(min(self.current_balance[bank_contracts], self.projected_supply[bank_contracts]), 0.0)
            total_contract[bank_counter] += max(min(self.current_balance[bank_contracts], self.projected_supply[bank_contracts]), 0.0) 
        bank_counter += 1
		
      if member_constraint > 0.0:
        for bank_contract_counter in range(0, len(total_contract)):
          total_contract[bank_contract_counter] = total_contract[bank_contract_counter]/member_constraint
    
    return member_constraint, total_contract
     
	
  def set_request_constraints(self, demand, search_type, contract_list, bank_space, bank_capacity, dowy, wateryear):
    #this function is used to determine if a district node 'wants' to make a request
	#under the different usage types (flood, delievery, banking, or recovery) under a given contract
	#(contract_list)
    self.projected_supply['tot'] = 0.0
    total_recharge = 0.0
    for y in self.contract_list:
      self.projected_supply['tot'] += self.projected_supply[y]
      total_recharge += self.recharge_carryover[y]
    #for flood deliveries, a district requests water if they don't have
	#excess contract water that they don't think they can recharge (i.e. they don't purchase
	#flood water if they can't use all their contract water
    if search_type == "flood":
      if self.projected_supply['tot'] > self.annualdemand:
        return demand
      else:
        return demand
      #for y in contract_list:
        #tot_recharge += self.delivery_carryover[y.name]
      #if tot_recharge <= 0.0:
      #return demand
      #else:
        #return 0.0

    #for normal irrigation deliveries, a district requests water if they have enough water currently
	#in surface water storage under the given contract
    if search_type == "delivery":
      private_add = 0.0
      if self.has_private:
        for xx in self.private_demand:
          private_add += min(self.private_demand[xx], self.private_delivery[xx])
      total_current_balance = 0.0
      total_projected_supply = 0.0
      total_carryover = 0.0
      friant_toggle = 0
      delta_toggle = 0
      for y in contract_list:
        total_current_balance += max(self.current_balance[y.name], 0.0)
        total_projected_supply += max(self.projected_supply[y.name], 0.0)
        total_carryover += max(self.carryover[y.name] - self.deliveries[y.name][wateryear], 0.0)
      if self.project_contract['cvpdelta'] > 0.0 or self.project_contract['exchange'] > 0.0:
        delta_toggle = 1
      if self.seasonal_connection == 1:
        if self.must_fill == 1:
          return max(min(demand, total_current_balance), 0.0) + private_add
        elif total_carryover > 0.0 or total_projected_supply > self.annualdemand:
          return max(min(demand, total_current_balance), 0.0) + private_add
        elif delta_toggle == 1:
          return max(min(demand, total_current_balance, total_projected_supply), 0.0) + private_add
        #elif dowy < 273:
          #if total_projected_supply > self.irrseasondemand:
            #demand_fraction = min(max((total_projected_supply - self.irrseasondemand)/(self.annualdemand - self.irrseasondemand), 0.0), 1.0)
            #return max(min(demand_fraction*demand,total_current_balance), 0.0) + private_add
          #if self.annualdemand > 0.0:
            #return max(min(demand*min(total_projected_supply/self.annualdemand, 1.0),total_current_balance), 0.0) + private_add
          #else:
            #return max(min(demand,total_current_balance), 0.0) + private_add
        else:
          conservative_estimate = max(min((dowy- 211.0)/(273.0 - 211.0), 1.0), 0.0)
          if self.annualdemand > 0.0:
            return max(min(demand*min(conservative_estimate*total_projected_supply/self.annualdemand, 1.0),total_current_balance), 0.0) + private_add
          else:
            return max(min(demand,total_current_balance), 0.0) + private_add

      else:
        return private_add
		
    #for banking, a district requests water if they have enough contract water currently in surface water storage and they have 'excess' water for banking (calculated in self.open_recharge)
    if search_type == "banking":
      total_carryover_recharge = 0.0
      total_current_balance = 0.0
      for y in contract_list:
        total_carryover_recharge += max(self.recharge_carryover[y.name], 0.0)
        total_current_balance += max(self.current_balance[y.name], 0.0)
      return min(total_carryover_recharge, total_current_balance, max(bank_capacity - bank_space, 0.0))
	  
    #for recovery, a district requests recovery water from a bank if they have contracts under the current contract being searched (i.e., so they aren't requesting water that will be sent to another district that can't make 'paper' trades with them) and if they have their 'recovery threshold' triggered (self.use_recovery, calculated in self.open_recovery)
    if search_type == "recovery":
      member_trades = 0
      for member_contracts in self.contract_list:
        for exchange_contracts in contract_list:
          if member_contracts == exchange_contracts.name:
            member_trades = 1
      if member_trades == 1:
        if self.use_recovery == 1.0:
          total_request = min(max(self.dailydemand*self.surface_water_sa*self.seepage, 0.0), max(bank_space, 0.0))
        else:
          total_request = 0.0
      else:
        total_request = 0.0
		
      return total_request
	  
  def set_demand_priority(self, priority_list, contract_list, demand, delivery, demand_constraint, search_type, contract_canal):
    #this function takes a the calculated demand at each district node and classifies those demands by 'priority' - the priority classes and rules change for each delivery type
    demand_dict = {}
    #for flood deliveries, the priority structure is based on if you have a contract with the reservoir that is being spilled, if you have a turnout on a canal that is a 'priority canal' for the spilling reservoir, and then finally if you are not on a priority canal for spilling
    if search_type == 'flood':
      contractor_toggle = 0
      priority_toggle = 0
      for yy in priority_list:#canals that have 'priority' from the given reservoir
        if yy.name == contract_canal:#current canal
          priority_toggle = 1
      if priority_toggle == 1:
        for y in contract_list:#contracts that are being spilled (b/c they are held at the spilling reservoir)
          for yx in self.contract_list:
            if y.name == yx:
              contractor_toggle = 1
        if contractor_toggle == 1:
          demand_dict['contractor'] = max(min(demand,delivery), 0.0)
          demand_dict['alternate'] = min(delivery - max(min(demand,delivery),0.0),demand_constraint-demand_dict['contractor'])
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
      for yy in priority_list:#canals that have 'priority' from the given reservoir
        if yy.name == contract_canal:#current canal
          priority_toggle = 1
      if priority_toggle == 1:
        demand_dict['priority'] = max(min(demand,delivery), 0.0)
        demand_dict['secondary'] = min(delivery - max(min(demand,delivery),0.0),demand_constraint-demand_dict['priority'])
      else:
        demand_dict['priority'] = 0.0
        demand_dict['secondary'] = max(min(delivery, demand_constraint), 0.0)

    #recovery is the same priority structure as banking, but we use different names (initial & supplemental) to keep things straight)
    elif search_type == 'recovery':
      if self.in_leiu_banking:
        demand_dict['initial'] = max(min(demand,delivery), 0.0)
        demand_dict['supplemental'] = min(delivery - max(min(demand,delivery), 0.0), demand_constraint - demand_dict['initial'])
      else:
        demand_dict['initial'] = 0.0
        demand_dict['supplemental'] = 0.0
    return demand_dict

  def find_leiu_priority_space(self, demand_constraint, num_members, member_name, toggle_recharge, search_type):
    #this function finds how much 'priority' space in the recharge/recovery capacity is owned by a member (member_name) in a given in-leiu bank (i.e. this function is attached to the district that owns the bank - and the banking member is represented by 'member_name' input variable)
    if search_type == "recovery":
      priority_space = max(min(self.leiu_recovery*self.leiu_ownership[member_name] - self.recovery_use[member_name], demand_constraint), 0.0)
      available_banked = self.inleiubanked[member_name]
      return min(priority_space, available_banked)
    else:
      initial_capacity = self.dailydemand_start*self.surface_water_sa*self.seepage
      if toggle_recharge == 1:
        initial_capacity += self.in_district_storage
      priority_space = max(min((self.leiu_ownership[member_name]*initial_capacity - self.bank_deliveries[member_name]), demand_constraint)/num_members, 0.0)
      return priority_space

  def set_deliveries(self, priorities,type_fractions,type_list,search_type,toggle_district_recharge,member_name, wateryear):
    #this function takes the deliveries, seperated by priority, and updates the district's daily demand and/or recharge storage
    final_deliveries = 0.0
    total_direct_deliveries = 0.0
    total_recharge_deliveries = 0.0
    for zz in type_list:
      total_deliveries = priorities[zz]*type_fractions[zz]
      final_deliveries += total_deliveries
	  
    if self.has_private:
      private = 0.0
      for xx in self.private_demand:
        private += min(self.private_demand[xx], self.private_delivery[xx])
      if search_type == 'flood':
        total_recharge_deliveries = min(max(final_deliveries - private, 0.0), self.in_district_storage - self.current_recharge_storage)
        total_direct_deliveries = min(max(final_deliveries - private - total_recharge_deliveries, 0.0)/self.seepage, self.dailydemand*self.surface_water_sa)
      else:
        total_direct_deliveries = min(max(final_deliveries - private, 0.0)/self.seepage, self.dailydemand*self.surface_water_sa)
        if toggle_district_recharge == 1:
          total_recharge_deliveries = min(max((final_deliveries - private)/self.seepage - total_direct_deliveries, 0.0), self.in_district_storage - self.current_recharge_storage)
        else:
          total_recharge_deliveries = 0.0
      self.dailydemand -= total_direct_deliveries
      self.current_recharge_storage += total_recharge_deliveries
      #final_deliveries += total_recharge_deliveries
    else:
      if search_type == 'flood':
        total_recharge_deliveries = min(max(final_deliveries, 0.0), self.in_district_storage - self.current_recharge_storage)
        total_direct_deliveries = min(max(final_deliveries - total_recharge_deliveries, 0.0)/self.seepage, self.dailydemand*self.surface_water_sa)
      else:
        total_direct_deliveries = min(max(final_deliveries, 0.0)/self.seepage, self.dailydemand*self.surface_water_sa)
        if toggle_district_recharge == 1:
          total_recharge_deliveries = min(max((final_deliveries)/self.seepage - total_direct_deliveries, 0.0), self.in_district_storage - self.current_recharge_storage)
        else:
          total_recharge_deliveries = 0.0
      self.dailydemand -= total_direct_deliveries
      self.current_recharge_storage += total_recharge_deliveries
		
    return total_direct_deliveries, total_recharge_deliveries, final_deliveries - total_direct_deliveries - total_recharge_deliveries
				
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################ADJUSST ACCOUNTS AFTER DELIVERY####################################################
#####################################################################################################################

  def give_paper_trade(self, trade_amount, contract_list, wateryear, district_name):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
	#trade, giving up a surface water contract allocation (contract_list) to the district
	#that owned the groundwater that was recovered
    if self.seepage > 0.0:
      total_alloc = 0.0
      for y in contract_list:
        total_alloc += self.projected_supply[y.name]
      actual_delivery = min(trade_amount, total_alloc, self.dailydemand*self.seepage*self.surface_water_sa)
      self.dailydemand -= actual_delivery/self.seepage	  
      if total_alloc > 0.0:
        for y in contract_list:
          self.paper_balance[y.name] -= actual_delivery*self.projected_supply[y.name]/total_alloc
		  
      self.deliveries['exchanged_SW'][wateryear] += actual_delivery

    return actual_delivery 
		
  def give_paper_exchange(self, trade_amount, contract_list, trade_frac, wateryear, district_name):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
	#trade, giving up a surface water contract allocation (contract_list) to the district
	#that owned the groundwater that was recovered
    contract_counter = 0
    for y in contract_list:
      self.paper_balance[y] -= trade_amount*trade_frac[contract_counter]
      contract_counter += 1
    self.deliveries['exchanged_SW'][wateryear] += trade_amount
	  
  def get_paper_trade(self, trade_amount, contract_list, wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	#the paper credit is in exchange for delivering recovered groundwater to another party (district)
    total_alloc = 0.0
    contract_frac = 0.0
    for y in contract_list:
      total_alloc += self.projected_supply[y.name]
    if total_alloc > 0.0:
      for y in contract_list:
        self.paper_balance[y.name] += trade_amount*self.projected_supply[y.name]/total_alloc

    else:
      contract_frac = 1.0
      for y in contract_list:
        self.paper_balance[y.name] += trade_amount*contract_frac
        contract_frac = 0.0
    self.deliveries['exchanged_GW'][wateryear] += trade_amount

  def get_paper_exchange(self, trade_amount, contract_list, trade_frac, wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	#the paper credit is in exchange for delivering recovered groundwater to another party (district)
    total_alloc = 0.0
    contract_frac = 0.0
    contract_counter = 0
    for y in contract_list:
      self.paper_balance[y] += trade_amount*trade_frac[contract_counter]
      contract_counter += 1
    self.deliveries['exchanged_GW'][wateryear] += trade_amount

  def record_direct_delivery(self, delivery, wateryear):
    actual_delivery = min(delivery, self.dailydemand*self.seepage*self.surface_water_sa)
    self.deliveries['recover_banked'][wateryear] += actual_delivery
    self.dailydemand -= actual_delivery/(self.seepage*self.surface_water_sa)
    self.direct_recovery_delivery = 0.0
    return actual_delivery

  def direct_delivery_bank(self, delivery, wateryear):
    #this function takes a delivery of recoverd groundwater and applies it to irrigation demand in a district
	#the recovered groundwater is delivered to the district that originally owned the water, so no 'paper' trade is needed
    actual_delivery = min(delivery, self.dailydemand*self.seepage*self.surface_water_sa - self.direct_recovery_delivery)
    #self.deliveries['recover_banked'][wateryear] += actual_delivery
    self.direct_recovery_delivery += actual_delivery
    #self.dailydemand -= actual_delivery/self.seepage*self.surface_water_sa
    return actual_delivery
	
  def adjust_accounts(self, direct_deliveries, recharge_deliveries, contract_list, search_type, wateryear):
    #this function accepts water under a specific condition (flood, irrigation delivery, banking), and 
	#adjusts the proper accounting balances
    total_carryover_recharge = 0.0
    total_current_balance = 0.0
    delivery_by_contract = {}
    for y in contract_list:
      if search_type == 'flood':
        total_current_balance += 1.0
      elif search_type == 'delivery':
        total_current_balance += max(self.projected_supply[y.name], 0.0)
      elif search_type == 'banking':
        total_current_balance += max(self.recharge_carryover[y.name], 0.0)
      elif search_type == 'recovery':
        total_current_balance += max(self.current_balance[y.name], 0.0)
      delivery_by_contract[y.name] = 0.0
    flood_counter = 0
    for y in contract_list:
      #find the percentage of total deliveries that come from each contract
      if search_type == 'flood':
          if flood_counter == 0:
            contract_deliveries = (direct_deliveries + recharge_deliveries)
            flood_counter = 1
          else:
            contract_deliveries = 0.0
      elif total_current_balance > 0.0:
        if search_type == 'delivery':
          contract_deliveries = (direct_deliveries + recharge_deliveries)*max(self.projected_supply[y.name], 0.0)/total_current_balance
        elif search_type == 'banking':
          contract_deliveries = (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[y.name], 0.0)/total_current_balance
        elif search_type == 'recovery':
          contract_deliveries = (direct_deliveries + recharge_deliveries)*max(self.current_balance[y.name], 0.0)/total_current_balance

      else:
        contract_deliveries = 0.0
      delivery_by_contract[y.name] = contract_deliveries
      #flood deliveries do not count against a district's contract allocation, so the deliveries are recorded as 'flood'
      if search_type == "flood":
        if contract_deliveries > 0.0:
          self.deliveries[y.name + '_flood'][wateryear] += recharge_deliveries
          self.deliveries[y.name + '_flood_irrigation'][wateryear] += direct_deliveries
      else:
        #irrigation/banking deliveries are recorded under the contract name so they are included in the 
		#contract balance calculations
        #update the individual district accounts
        self.deliveries[y.name][wateryear] += contract_deliveries
        self.current_balance[y.name] -= contract_deliveries
        if search_type == 'banking':
          #if deliveries ar for banking, update banking accounts
          self.deliveries['recharged'][wateryear] += contract_deliveries
          self.deliveries[y.name+'_recharged'][wateryear] += contract_deliveries
          self.recharge_carryover[y.name] -= min(contract_deliveries, self.recharge_carryover[y.name])
		
    return delivery_by_contract
	
  def adjust_bank_accounts(self, member_name, direct_deliveries, recharge_deliveries, wateryear):
    #when deliveries are made for banking, keep track of the member's individual accounts
    self.bank_deliveries[member_name] += direct_deliveries + recharge_deliveries#keeps track of how much of the capacity is being used in the current timestep
    self.deliveries['inleiu_irrigation'][wateryear] += direct_deliveries#if deliveries being made 'inleiu', then count as inleiu deliveries
    self.deliveries['inleiu_recharge'][wateryear] += recharge_deliveries#if deliveries being made 'inleiu', then count as inleiu deliveries
    self.inleiubanked[member_name] += (direct_deliveries + recharge_deliveries) * self.inleiuhaircut#this is the running account of the member's banking storage
	
  def adjust_recovery(self, deliveries, member_name, wateryear):
    #if recovery deliveries are made, adjust the banking accounts and account for the recovery capacity use
    self.inleiubanked[member_name] -= deliveries#this is the running account of the member's banking storage
    self.deliveries['leiupumping'][wateryear] += deliveries
    self.recovery_use[member_name] += deliveries#keeps track of how much of the capacity is being used in the current timestep

  def adjust_exchange(self, deliveries, member_name, wateryear):
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
    self.max_direct_recharge = np.zeros(12)
    self.max_leiu_recharge = np.zeros(12)
    self.total_banked_storage = 0.0
    self.max_leiu_exchange = 0.0

  def accounting_full(self, t, wateryear):
    # keep track of all contract amounts
    for x in self.contract_list_all:
      self.daily_supplies_full[x + '_delivery'][t] = self.deliveries[x][wateryear]
      self.daily_supplies_full[x + '_flood'][t] = self.deliveries[x + '_flood'][wateryear]
      self.daily_supplies_full[x + '_flood_irrigation'][t] = self.deliveries[x + '_flood_irrigation'][wateryear]
      self.daily_supplies_full[x + '_recharged'][t] = self.deliveries[x + '_recharged'][wateryear]
      self.daily_supplies_full[x + '_projected'][t] = self.projected_supply[x]
      self.daily_supplies_full[x + '_paper'][t] = self.paper_balance[x]
      self.daily_supplies_full[x + '_carryover'][t] = self.carryover[x]
      self.daily_supplies_full[x + '_turnback'][t] = self.turnback_pool[x]
    for x in self.non_contract_delivery_list:
      self.daily_supplies_full[x][t] = self.deliveries[x][wateryear]
    self.daily_supplies_full['pumping'][t] = self.annual_private_pumping
    self.daily_supplies_full['irr_demand'][t] = self.dailydemand_start

  def accounting(self,t, da, m, wateryear,key):
    #takes delivery/allocation values and builds timeseries that show what water was used for (recharge, banking, irrigation etc...)
	#delivery/allocation data are set cumulatively - so that values will 'stack' in a area plot.
	#Allocations are positive (stack above the x-axis in a plot)
    self.daily_supplies['paper'][t] += self.projected_supply[key]
    self.daily_supplies['carryover'][t] += max(self.projected_supply[key] - self.paper_balance[key], 0.0)
    self.daily_supplies['allocation'][t] += max(self.projected_supply[key] - self.paper_balance[key] - self.carryover[key], 0.0)
    #while deliveries are negative (stack below the x-axis in a plot) - the stacking adjustments come in self.accounting_banking_activity()
    self.daily_supplies['delivery'][t] -= self.deliveries[key][wateryear]
    self.daily_supplies['flood_irrigation'][t] -= (self.deliveries[key][wateryear] + self.deliveries[key + '_flood_irrigation'][wateryear])
    self.daily_supplies['recharge_uncontrolled'][t] -= self.deliveries[key + '_flood'][wateryear] 
	
    if m == 9 and da == 30:
      self.annual_supplies['delivery'][wateryear] += self.deliveries[key][wateryear]
      self.annual_supplies['flood_irrigation'][wateryear] += self.deliveries[key + '_flood_irrigation'][wateryear]
      self.deliveries['undelivered_trades'][wateryear] += max(self.paper_balance[key] - self.deliveries[key][wateryear], 0.0)
	
  def accounting_banking_activity(self, t, da, m, wateryear):
    #this is an adjustment for 'delivery' (the delivery values are negative, so adding 'recharged' and 'exchanged_GW' is removing them from the count for 'deliveries' - we only want deliveries for irrigation, not for recharge
    #exchanged_GW is GW that has been pumped out of a bank and 'delivered' to another district. the district gets credit in the reservoir, and deliveries of SW from that reservoir are recorded as 'deliveries' - but we don't want to count that here
	#exchanged_SW is GW that has been pumped out of a bank, not owned by the district, and delivered to that district (i.e., the other side of the exchanged_GW in a GW exchange).  This should technically count as an irrigation delivery from a contract
	#(we want to record that as delivery here) but it doesn't get recorded that way upon delivery.  so we add it back here when were are recording accounts (i.e. exchanged_GW and exchanged_SW are counters to help us square the records from GW exchanges)
    self.daily_supplies['delivery'][t] += self.deliveries['recharged'][wateryear] + self.deliveries['exchanged_GW'][wateryear] - self.deliveries['exchanged_SW'][wateryear]
    self.daily_supplies['flood_irrigation'][t] += self.deliveries['recharged'][wateryear] + self.deliveries['exchanged_GW'][wateryear] - self.deliveries['exchanged_SW'][wateryear]

    #leiu accepted are irrigation deliveries that come from the in-leiu banking district's banking partners (i.e., they use it, and record a 'balance' for whoever delivered it)
    self.daily_supplies['leiu_applied'][t] += self.daily_supplies['flood_irrigation'][t] - self.deliveries['inleiu_irrigation'][wateryear]
    self.daily_supplies['leiu_recharged'][t] += self.daily_supplies['leiu_applied'][t] - self.deliveries['inleiu_recharge'][wateryear]

      #banked is uncontrolled (or flood) water that has been banked by a district (in-district)
    self.daily_supplies['banked'][t] += self.daily_supplies['leiu_recharged'][t] + self.deliveries['exchanged_SW'][wateryear] - self.deliveries['exchanged_GW'][wateryear] - self.deliveries['recover_banked'][wateryear]
    ##pumping is private pumping for irrigation
    self.daily_supplies['pumping'][t] += self.daily_supplies['banked'][t] - self.annual_private_pumping
    ##leiu_delivered is water from an in-leiu banking district that gets delivered to (recovered by) their banking partners
    self.daily_supplies['leiu_delivered'][t] += self.daily_supplies['pumping'][t] - self.deliveries['leiupumping'][wateryear]
    #recharge delivery is water recharged at a bank that comes from the district's contract amount (instead of flood/uncontrolled water)
    self.daily_supplies['recharge_delivery'][t] += self.daily_supplies['leiu_delivered'][t] - self.deliveries['recharged'][wateryear]
	
	#recharge uncontrolled is recharge water from flood flows (flood flows added in self.accounting() - this is only adjustment for stacked plot)
    self.daily_supplies['recharge_uncontrolled'][t] += self.daily_supplies['recharge_delivery'][t] 

    if m == 9 and da == 30:
      self.annual_supplies['delivery'][wateryear] += self.deliveries['exchanged_SW'][wateryear] - self.deliveries['recharged'][wateryear] - (self.deliveries['exchanged_GW'][wateryear] - self.deliveries['undelivered_trades'][wateryear])
      recharged_recovery = 0.0
      if self.annual_supplies['delivery'][wateryear] < 0.0:
        recharged_recovery = self.annual_supplies['delivery'][wateryear]
        self.annual_supplies['delivery'][wateryear] = 0.0
      self.annual_supplies['banked_accepted'][wateryear] = self.deliveries['recover_banked'][wateryear] + (self.deliveries['exchanged_GW'][wateryear] - self.deliveries['undelivered_trades'][wateryear]) - self.deliveries['exchanged_SW'][wateryear] + recharged_recovery
      self.annual_supplies['leiu_applied'][wateryear] = self.deliveries['inleiu_irrigation'][wateryear]
      self.annual_supplies['leiu_recharged'][wateryear] = self.deliveries['inleiu_recharge'][wateryear]
      self.annual_supplies['leiu_delivered'][wateryear] = self.deliveries['leiupumping'][wateryear]



  def accounting_leiubank(self,t, m, da, wateryear):
    #takes banked storage (in in-leiu banks) and builds timeseries of member accounts
    stacked_amount = 0.0
    self.recharge_rate_series[t] = self.recharge_rate
    for x in self.participant_list:
      self.bank_timeseries[x][t] = self.inleiubanked[x] + stacked_amount
      stacked_amount += self.inleiubanked[x]
    if m == 9 and da == 30:
      for x in self.participant_list:
        sum_total = 0.0
        for year_counter in range(0, wateryear):
          sum_total += self.annual_timeseries[x][year_counter]
        self.annual_timeseries[x][wateryear] = self.inleiubanked[x] - sum_total
	  
  def accounting_as_df(self, index):
    #wirte district accounts and deliveries into a data fram
    df = pd.DataFrame()
    for n in self.daily_supplies:    
      df['%s_%s' % (self.key,n)] = pd.Series(self.daily_supplies[n], index = index)
    return df

  def accounting_as_df_full(self, index):
    #wirte district accounts and deliveries into a data fram
    df = pd.DataFrame()
    for n in self.daily_supplies_full:
      df['%s_%s' % (self.key,n)] = pd.Series(self.daily_supplies_full[n], index = index)
    return df

  def annual_results_as_df(self):
    #wite annual district deliveries into a data frame
    df = pd.DataFrame()
    for n in self.annual_supplies:
      df['%s_%s' % (self.key,n)] = pd.Series(self.annual_supplies[n])
    return df

  def bank_as_df(self, index):
    #write leiubanking accounts (plus bank recharge rates) into a dataframe
    df = pd.DataFrame()
    for n in self.participant_list:
      df['%s_%s_leiu' % (self.key,n)] = pd.Series(self.bank_timeseries[n], index = index)
    df['%s_rate' % self.key] = pd.Series(self.recharge_rate_series, index = index)
    return df
	
  def annual_bank_as_df(self):
    #write anmual banking changes into a data frame
    df = pd.DataFrame()
    for n in self.participant_list:
      df['%s_%s_leiu' % (self.key,n)] = pd.Series(self.annual_timeseries[n])
    return df
	
  def get_iterable(self, x):
    if isinstance(x, cl.Iterable):
      return x
    else:
      return (x,)

	  
