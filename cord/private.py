from __future__ import division
import numpy as np 
import matplotlib.pyplot as plt
import collections as cl
import pandas as pd
from .crop import Crop
import json
from .util import *


class Private():

  def __init__(self, df, key, land_fraction):
    self.T = len(df)
    self.starting_year = df.index.year[0]
    self.number_years = df.index.year[-1]-df.index.year[0]
    self.key = key
    self.leap = leap(np.arange(min(df.index.year), max(df.index.year) + 2))
    year_list = np.arange(min(df.index.year), max(df.index.year) + 2)
    self.days_in_month = days_in_month(year_list, self.leap)
    self.dowy_eom = dowy_eom(year_list, self.leap)
    self.non_leap_year = first_non_leap_year(self.dowy_eom)
    self.turnback_use = True


    for k,v in json.load(open('cord/private/%s_properties.json' % key)).items():
        setattr(self,k,v)
		
    self.contract_fractions = {}
    for x in self.district_list:
      self.contract_fractions[x] = land_fraction

    #intialize crop acreages and et demands for crops
    self.irrdemand = {}
    for x in self.district_list:
      self.irrdemand[x] = Crop(self.zone[x])
	#initialize dictionary to hold different delivery types
    self.deliveries = {}
    self.contract_list_all = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2','kaweah', 'tule', 'kern', 'kings']
    self.non_contract_delivery_list = ['inleiu','leiupumping','recharged','exchanged_SW', 'recover_banked']

    for district in self.district_list:
      self.deliveries[district] = {}
      for x in self.contract_list_all:
        #normal contract deliveries
        self.deliveries[district][x] = np.zeros(self.number_years)
	    #uncontrolled deliveries from contract
        self.deliveries[district][x + '_flood'] = np.zeros(self.number_years)
        self.deliveries[district][x + '_flood_irrigation'] = np.zeros(self.number_years)

      for x in self.non_contract_delivery_list:
	    #deliveries from a groundwater bank (reocrded by banking partner recieving recovery water)
        self.deliveries[district][x] = np.zeros(self.number_years)
    self.deliveries['exchanged_GW'] = np.zeros(self.number_years)
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
    #initialize values for all contracts in dictionaries
    for z in self.district_list:
      self.current_balance[z] = {}
      self.turnback_pool[z] = {}
      self.projected_supply[z] = {}
      self.carryover[z] = {}
      self.recharge_carryover[z] = {}
      self.delivery_carryover[z] = {}
      self.contract_carryover_list[z] = {}
      for y in self.contract_list_all:
        self.current_balance[z][y] = 0.0
        self.paper_balance[y] = 0.0
        self.turnback_pool[z][y] = 0.0
        self.projected_supply[z][y] = 0.0
        self.carryover[z][y] = 0.0
        self.recharge_carryover[z][y] = 0.0
        self.delivery_carryover[z][y] = 0.0
        self.contract_carryover_list[z][y] = 0.0
	  
    #initialize dictionaries to 'store' daily state variables (for export to csv)
    self.daily_supplies = {}
    supply_list = ['paper', 'carryover', 'allocation', 'delivery', 'leiu_accepted', 'banked', 'pumping', 'leiu_delivered', 'recharge_delivery', 'recharge_uncontrolled', 'banked_storage', 'annual_demand', 'contract_available', 'carryover_available', 'use_recharge', 'use_recovery', 'numdays', 'recharge_cap', 'recovery_cap']

    for x in supply_list:
      self.daily_supplies[x] = np.zeros(self.T)

    #initialize dictionaries to 'store' annual change in state variables (for export to csv)
    self.annual_supplies = {}
    supply_list = ['delivery', 'leiu_accepted', 'leiu_delivered', 'banked_accepted', 'recharge_uncontrolled', 'recharge_delivery', 'banked_storage', 'acreage']
    for x in supply_list:
      self.annual_supplies[x] = np.zeros(self.number_years)

    # hold all output
    self.daily_supplies_full = {}
    self.demand_days = {}
    self.demand_days['current'] = {}
    self.demand_days['lookahead'] = {}

    # delivery_list = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2','kaweah', 'tule', 'kern']
    for x in self.contract_list_all:
      self.daily_supplies_full[x + '_delivery'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_flood'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_projected'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_paper'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_carryover'] = np.zeros(self.T)
      self.daily_supplies_full[x + '_turnback'] = np.zeros(self.T)
      self.demand_days['current'][x] = 0.0
      self.demand_days['lookahead'][x] = 0.0

    for x in self.non_contract_delivery_list:
      self.daily_supplies_full[x] = np.zeros(self.T)

    # ['recover_banked', 'inleiu', 'leiupumping', 'recharged', 'exchanged_GW', 'exchanged_SW', 'undelivered_trades']
    #Initialize demands
    self.annualdemand = {}
    self.dailydemand = {}
    self.dailydemand_start = {}
    self.per_acre = {}
    self.total_acreage = 0.0
    self.unmet_et = {}
    for x in self.district_list:
      self.per_acre[x] = {}
      self.unmet_et[x] = np.zeros(self.number_years)
      self.unmet_et[x + "_total"] = np.zeros(self.number_years)
      self.dailydemand_start[x] = 0.0
      self.dailydemand[x] = 0.0
      for v in self.crop_list:
        self.per_acre[x][v] = {}
        self.per_acre[x][v]['mature'] = 0.0
        self.per_acre[x][v]['immature'] = 0.0

    #recovery and pumping variables
    #self.recovery_fraction = 0.5
    self.annual_pumping = 0.0
    self.use_recharge = 0.0
    self.use_recovery = 0.0
    self.extra_leiu_recovery = 0.0
    self.max_recovery = 0.0
    self.max_leiu_exchange = 0.0
    self.total_banked_storage = 0.0
    self.direct_recovery_delivery = {}
    for x in self.district_list:
      self.direct_recovery_delivery[x] = 0.0
	
    #for in-district recharge & counters (for keeping track of how long a basin has been continuously 'wet'
    self.recharge_rate = self.in_district_direct_recharge*cfs_tafd
    self.thismonthuse = 0
    self.monthusecounter = 0
    self.monthemptycounter = 0
    self.current_recharge_storage = 0.0

	


#####################################################################################################################
##################################DEMAND CALCULATION#################################################################
#####################################################################################################################
  def permanent_crop_growth(self, wateryear):
    self.total_acreage = 0.0
    for x in self.district_list:
      irrigation = 0.0
      missing_demand = self.unmet_et[x][wateryear-1]
      for y in self.contract_list_all:
        irrigation += self.deliveries[x][y][wateryear-1]
      irrigation -= self.deliveries[x]['recharged'][wateryear-1]
      percent_filled = {}
      for v in self.crop_list:
        percent_filled[v] = np.zeros(25)
      for ageloop in range(24, -1, -1):
        for v in self.crop_list:
          if ageloop < self.crop_maturity[v]:
            total_et = self.per_acre[x][v]['immature']*(self.acreage[x][v][ageloop])
          else:
            total_et = self.per_acre[x][v]['mature']*(self.acreage[x][v][ageloop])
          if total_et > 0.0:
            percent_filled[v][ageloop] = 1.0 - max(min(missing_demand/total_et, 1.0), 0.0)
          else:
            percent_filled[v][ageloop] = 0.0
          missing_demand -= total_et*(1.0 - percent_filled[v][ageloop])
      for v in self.crop_list:
        for ageloop in range(24, 0, -1):
          self.acreage[x][v][ageloop] = self.acreage[x][v][ageloop-1]*percent_filled[v][ageloop-1]
          self.total_acreage += self.acreage[x][v][ageloop]
        self.acreage[x][v][0] = self.initial_planting[x][v]
        self.total_acreage += self.acreage[x][v][0]
    for x in self.district_list:
      self.per_acre[x] = {}
      for v in self.crop_list:
        self.per_acre[x][v] = {}
        self.per_acre[x][v]['mature'] = 0.0
        self.per_acre[x][v]['immature'] = 0.0

		
    self.find_baseline_demands()
		
  def find_baseline_demands(self):
    self.monthlydemand = {}
    self.agedemand = {}
    wyt_list = ['W', 'AN', 'BN', 'D', 'C']
    for district in self.district_list:
      self.monthlydemand[district] = {}
      self.agedemand[district] = {}
      district_et = self.irrdemand[district]
      for wyt in wyt_list:
        self.monthlydemand[district][wyt] = np.zeros(12)
        self.agedemand[district][wyt] = np.zeros(25)
        for i,v in enumerate(self.crop_list):
          annualET = 0.0
          annualETimm = 0.0
          for monthloop in range(0,12):
            annualET += max(district_et.etM[v][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)/(12.0)
            annualETimm += max(district_et.etM[v + '_immature'][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)/(12.0)
          for ageloop in range(0,25):
            if ageloop < self.crop_maturity[v]:
              self.agedemand[district][wyt][ageloop] += self.acreage[district][v][ageloop]*annualET*self.seepage[district]
            else:
              self.agedemand[district][wyt][ageloop] += self.acreage[district][v][ageloop]*annualETimm
        for monthloop in range(0,12):
          self.monthlydemand[district][wyt][monthloop] += self.urban_profile[district][monthloop]*self.MDD[district]/self.days_in_month[self.non_leap_year][monthloop]
          for i,v in enumerate(self.crop_list):
            age_length = len(self.acreage[district][v])
            acres_mature = np.sum(self.acreage[district][v][self.crop_maturity[v]:age_length])
            acres_immature = np.sum(self.acreage[district][v][0:self.crop_maturity[v]])
            district_et = self.irrdemand[district]
            self.monthlydemand[district][wyt][monthloop] += max(district_et.etM[v][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)*acres_mature/(12.0*self.days_in_month[self.non_leap_year][monthloop])
            self.monthlydemand[district][wyt][monthloop] += max(district_et.etM[v + '_immature'][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)*acres_immature/(12.0*self.days_in_month[self.non_leap_year][monthloop])
    
  def calc_demand(self, wateryear, year, da, m, m1, wyt):
    #from the monthlydemand dictionary (calculated at the beginning of each wateryear based on ag acreage and urban demands), calculate the daily demand and the remaining annual demand
    monthday = self.days_in_month[year][m-1]
    for x in self.district_list:
      self.dailydemand[x] = self.monthlydemand[x][wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[x][wyt][m1-1]*da/monthday
      if self.dailydemand[x] < 0.0:
        self.dailydemand[x] = 0.0
    for x in self.district_list:
      district_et = self.irrdemand[x]
      for v in self.crop_list:
        self.per_acre[x][v]['mature'] += (max(district_et.etM[v][wyt][m-1] - district_et.etM['precip'][wyt][m-1],0.0)*((monthday-da)/monthday) + max(district_et.etM[v][wyt][m1-1] - district_et.etM['precip'][wyt][m1-1],0.0)*(da/monthday))/(12.0*self.days_in_month[self.non_leap_year][m-1]) 
        self.per_acre[x][v]['immature'] += (max(district_et.etM[v + '_immature'][wyt][m-1] - district_et.etM['precip'][wyt][m-1],0.0)*((monthday-da)/monthday) + max(district_et.etM[v][wyt][m1-1] - district_et.etM['precip'][wyt][m1-1],0.0)*(da/monthday))/(12.0*self.days_in_month[self.non_leap_year][m-1]) 
    #calculate that days 'starting' demand (b/c demand is filled @multiple times, and if we only want to fill a certain fraction of that demand (based on projections of supply & demand for the rest of the year), we want to base that fraction on that day's total demand, not the demand left after other deliveries are made
      self.dailydemand_start[x] = self.monthlydemand[x][wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[x][wyt][m1-1]*da/monthday
      if self.dailydemand_start[x] < 0.0:
        self.dailydemand_start[x] = 0.0

	#pro-rate this month's demand based on the day of the month when calculating remaining annual demand
      self.annualdemand[x] = max(self.monthlydemand[x][wyt][m-1]*(monthday-da), 0.0)
      if m > 9:
        for monthloop in range(m, 12):
          self.annualdemand[x] += max(self.monthlydemand[x][wyt][monthloop]*self.days_in_month[year][monthloop],0.0)
        for monthloop in range(0,9):
          self.annualdemand[x] += max(self.monthlydemand[x][wyt][monthloop]*self.days_in_month[year+1][monthloop], 0.0)
      else:
        for monthloop in range(m, 9):
          self.annualdemand[x] += max(self.monthlydemand[x][wyt][monthloop]*self.days_in_month[year][monthloop], 0.0)
		  
  def get_urban_demand(self, t, m, da, wateryear, year, sri, dowy, total_delta_pumping):
    #this function finds demands for the 'branch pumping' urban nodes - Socal, South Bay, & Central Coast
	#demand is equal to pumping of the main california aqueduct and into the branches that services these areas
    #cal aqueduct urban demand comes from pumping data, calc seperately
    for district in self.district_list:
      self.dailydemand[district] = self.pumping[district][t]/1000.0
      self.dailydemand_start[district] = self.pumping[district][t]/1000.0
      self.ytd_pumping[district][wateryear] += self.dailydemand[district]
      sri_estimate = (sri*self.delivery_percent_coefficient[district][dowy][0] + self.delivery_percent_coefficient[district][dowy][1])*total_delta_pumping
      self.annualdemand[district] = max(0.0, (self.annual_pumping[district][wateryear]*dowy + sri_estimate*(364.0 - dowy))/364.0 - self.ytd_pumping[district][wateryear])

    ##Keep track of ytd pumping to Cal Aqueduct Branches
    if m == 10 and da == 1:
      self.monthlydemand = {}
      for district in self.district_list:
        self.monthlydemand[district] = {}
        for wyt in ['W', 'AN', 'BN', 'D', 'C']:
          self.monthlydemand[district][wyt] = np.zeros(12)	

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
          for district in self.district_list:
            self.monthlydemand[district][wyt][monthcounter] = np.mean(self.pumping[district][(t + start_of_month):(t + start_next_month)])/1000.0
        start_of_month = start_next_month

				
  def find_unmet_et(self, district_name, wateryear, dowy):
    self.unmet_et[district_name][wateryear] += self.dailydemand[district_name]
    self.unmet_et[district_name + "_total"][wateryear] += self.dailydemand_start[district_name]

  def find_pre_flood_demand(self, wyt, year):
    #calculates an estimate for water use in the Oct-Dec period (for use in recharge_carryover calculations), happens Oct 1
    self.pre_flood_demand = self.monthlydemand[wyt][9]*self.days_in_month[year][9] + self.monthlydemand[wyt][10]*self.days_in_month[year][10] + self.monthlydemand[wyt][11]*self.days_in_month[year][11]
		  
		
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################PROJECT CONTRACTS#################################################################
#####################################################################################################################

		
  def update_balance(self, t, wateryear, water_available, projected_allocation, current_water, key, tot_carryover, balance_type, district_name, project_contract, rights):
    ###This function takes input from the contract class (water_available, projected_allocation, tot_carryover) to determine how much of their allocation remains
	##water_available is the current contract storage in the reservoir *plus* all deliveries from the given year.  The deliveries, paper trades, and turnback pool accounts for each district
	##are used to get a running tally of the surface water that is currently available to them.  (tot_carryover is subtracted from the current balance - districts only get access to *their* 
	##carryover storage - which is added to their individual current balance (self.carryover[key])
	##projected_allocation is the water that is forecasted to be available on each contract through the end of the water year *plus* water that has already been delivered on that contract
	##individual deliveries are then subtracted from this total to determine the individual district's projected contract allocation remaining in that year
    if balance_type == 'contract':
      #district_storage - district's water that is currently available (in storage at reservoir)
      #(water_available - tot_carryover)*self.project_contract[key] - individual district share of the existing (in storage) contract balance, this includes contract water that has already been delivered to all contractors
	  #self.deliveries[key][wateryear] - individual district deliveries (how much of 'their' contract has already been delivered)
	  #self.carryover[key] - individual district share of contract carryover
	  #paper_balance[key] - keeps track of 'paper' groundwater trades (negative means they have accepted GW deliveries in exchange for trading some of their water stored in reservoir, positive means they sent their banked GW to another district in exchage for SW storage
	  #turnback_pool[key] - how much water was bought/sold on the turnback pool(negative is sold, positive is bought)
      district_storage = (water_available-tot_carryover)*project_contract[key]*self.private_fraction[district_name] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      #annual allocation - remaining (undelivered) district share of expected total contract allocation
	  #same as above, but projected_allocation*self.project_contract[key] - individual share of expected total contract allocation, this includes contract water that has already been delivered to all contractors
      annual_allocation = projected_allocation*project_contract[key]*self.private_fraction[district_name] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      storage_balance = current_water*project_contract[key]*self.private_fraction[district_name] + max(self.carryover[district_name][key] + self.turnback_pool[district_name][key] - self.deliveries[district_name][key][wateryear], 0.0)

    elif balance_type == 'right':
      #same as above, but for contracts that are expressed as 'rights' instead of allocations
      district_storage = (water_available-tot_carryover)*rights[key]['capacity']*self.private_fraction[district_name] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      annual_allocation = projected_allocation*rights[key]['capacity']*self.private_fraction[district_name] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      storage_balance = current_water*rights[key]['capacity']*self.private_fraction[district_name] + max(self.carryover[district_name][key] + self.turnback_pool[district_name][key] - self.deliveries[district_name][key][wateryear], 0.0)
    
    self.current_balance[district_name][key] = storage_balance
    self.projected_supply[district_name][key] = annual_allocation
    if balance_type == 'contract':
      contract_amount = project_contract[key]
    else:
      contract_amount = rights[key]['capacity']
	  
    if key == 'tableA' and self.key == "XXX":
      print(wateryear, end = " ")
      print(t, end = " ")
      print(self.key, end = " ")
      print("%.2f" % projected_allocation, end = " ")
      print("%.2f" % self.deliveries[district_name][key][wateryear], end = " ")
      print("%.2f" % self.deliveries[district_name]['recharged'][wateryear], end = " ")
      print("%.2f" % self.deliveries[district_name]['recover_banked'][wateryear], end = " ")
      print("%.2f" % self.deliveries['exchanged_GW'][wateryear], end = " ")
      print("%.2f" % self.projected_supply[district_name][key], end = " ")
      print("%.2f" % self.annualdemand[district_name], end = " ")
      print("%.2f" % self.recharge_carryover[district_name][key], end = " ")
      print("%.2f" % self.use_recovery)

	  
	
    return max(self.carryover[district_name][key] - self.deliveries[district_name][key][wateryear], 0.0)
	
  def apply_paper_balance(self, key, wyt, wateryear):
    ytd_deliveries = {}
    remaining_projected = {}
    remaining_paper = self.paper_balance[key]
    ind_paper_balance = {}
    for x in self.district_list:
      ytd_deliveries[x] = self.deliveries[x][key][wateryear] - self.deliveries[x]['recharged'][wateryear]
      ind_paper_balance[x] = 0.0
      if self.projected_supply[x][key] < 0.0:
        ind_paper_balance[x] = min(self.projected_supply[x][key]*-1.0, remaining_paper)
        remaining_paper = max(self.projected_supply[x][key] + remaining_paper, 0.0)
      remaining_projected[x] = self.projected_supply[x][key] + ind_paper_balance[x]
    self.age_death = 25
    if remaining_paper > 0.0:
      for ageloop in range(0,25):
        for x in self.district_list:
          if self.agedemand[x][wyt][ageloop] < ytd_deliveries[x]:
            ytd_deliveries[x] -= self.agedemand[x][wyt][ageloop]
          elif self.agedemand[x][wyt][ageloop] < (ytd_deliveries[x] + remaining_projected[x]) :
            remaining_projected[x] -= (self.agedemand[x][wyt][ageloop] - ytd_deliveries[x])
            ytd_deliveries[x] = 0.0
          elif self.agedemand[x][wyt][ageloop] < (ytd_deliveries[x] + remaining_projected[x] + remaining_paper):
            ind_paper_balance[x] += (self.agedemand[x][wyt][ageloop] - ytd_deliveries[x] - remaining_projected[x])
            remaining_paper -= (self.agedemand[x][wyt][ageloop] - ytd_deliveries[x] - remaining_projected[x])
            ytd_deliveries[x] = 0.0
            remaining_projected[x] = 0.0
          elif remaining_paper > 0.0:
            ind_paper_balance[x] += remaining_paper
            remaining_paper = 0.0
            self.age_death = ageloop
      if remaining_paper > 0.0:
        for x in self.district_list:
          ind_paper_balance[x] += remaining_paper/len(self.district_list)
    for x in self.district_list:
      self.projected_supply[x][key] += ind_paper_balance[x]
      self.current_balance[x][key] += (max(ind_paper_balance[x] + self.carryover[x][key] + self.turnback_pool[x][key] - self.deliveries[x][key][wateryear], 0.0) - max(self.carryover[x][key] + self.turnback_pool[x][key] - self.deliveries[x][key][wateryear], 0.0))
      self.current_balance[x][key] = min(self.projected_supply[x][key],self.current_balance[x][key]) 
 	
    total_carryover = 0.0	
    for x in self.district_list:
      total_carryover += max(self.projected_supply[x][key] - self.annualdemand[x], 0.0)
	  
    return total_carryover
        
  def apply_paper_balance_urban(self, key, wyt, wateryear):
    #ytd_deliveries = {}
    #remaining_projected = {}
    #remaining_paper = self.paper_balance[key]
    #ind_paper_balance = {}
    #total_remaining = 0.0
    #num_districts = 0.0
    total_used = 0.0
    if self.paper_balance[key] > 0.0:
      for xx in self.district_list:
        if self.projected_supply[xx][key] < 0.0:
          total_used_int = min(self.paper_balance[key] - total_used, self.projected_supply[xx][key]*(-1.0))
          self.projected_supply[xx][key] += total_used_int
          total_used += total_used_int
      if self.paper_balance[key] > total_used:
        for xx in self.district_list:
          self.projected_supply[xx][key] += (self.paper_balance[key] - total_used)/len(self.district_list)
    else:
      for xx in self.district_list:
        if self.projected_supply[xx][key] > 0.0:
          total_used_int = min(total_used - self.paper_balance[key], self.projected_supply[xx][key])
          self.projected_supply[xx][key] -= total_used_int
          total_used += total_used_int
      if self.paper_balance[key]*(-1.0) < total_used:
        for xx in self.district_list:
          self.projected_supply[xx][key] += (self.paper_balance[key] + total_used)/len(self.district_list)
    total_carryover = 0.0
    for x in self.district_list:
      total_carryover += max(self.projected_supply[x][key] - self.annualdemand[x], 0.0)
    #for x in self.district_list:
      #ytd_deliveries[x] = self.deliveries[x][key][wateryear] - self.deliveries[x]['recharged'][wateryear]
      #ind_paper_balance[x] = 0.0
      #if self.projected_supply[x][key] < 0.0:
        #ind_paper_balance[x] = min(self.projected_supply[x][key]*-1.0, remaining_paper)
        #remaining_paper = max(self.projected_supply[x][key] + remaining_paper, 0.0)
      #remaining_projected[x] = self.projected_supply[x][key] + ind_paper_balance[x]
      #total_remaining += remaining_projected[x]
      #num_districts += 1.0
    #target_projected = (total_remaining + remaining_paper)/num_districts
	
    #if remaining_paper > 0.0:
      #for x in self.district_list:
        #extra_balance = min(max(target_projected- remaining_projected[x], 0.0), remaining_paper)
        #ind_paper_balance[x] += extra_balance
        #remaining_paper -= extra_balance
    #for x in self.district_list:
      #self.projected_supply[x][key] += ind_paper_balance[x]
      #self.current_balance[x][key] += (max(ind_paper_balance[x] + self.carryover[x][key] + self.turnback_pool[x][key] - self.deliveries[x][key][wateryear], 0.0) - max(self.carryover[x][key] + self.turnback_pool[x][key] - self.deliveries[x][key][wateryear], 0.0))
      #self.current_balance[x][key] = min(self.projected_supply[x][key],self.current_balance[x][key]) 
    #total_carryover = 0.0	
    #for x in self.district_list:
      #total_carryover += max(self.projected_supply[x][key] - self.annualdemand[x], 0.0)

    return total_carryover
        
      
  def calc_carryover(self, existing_balance, wateryear, balance_type, key, district_name, project_contract, rights):
    #at the end of each wateryear, we tally up the full allocation to the contract, how much was used (and moved around in other balances - carryover, 'paper balance' and turnback_pools) to figure out how much each district can 'carryover' to the next year
    if balance_type == 'contract':
      annual_allocation = existing_balance*project_contract[key]*self.private_fraction[district_name] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      max_carryover = self.contract_carryover_list[district_name][key]
    elif balance_type == 'right':
      annual_allocation = existing_balance*rights[key]['capacity']*self.private_fraction[district_name] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      max_carryover = self.contract_carryover_list[district_name][key]
	  
    self.carryover[district_name][key] = annual_allocation
    self.turnback_pool[district_name][key] = 0.0	
		
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################RECHARGE/RECOVERY TRIGGERS#########################################################
#####################################################################################################################
	
  def open_recovery(self, t, dowy, wyt, wateryear, use_delivery_tolerance, additional_carryover):
    #this function determines if a district wants to recover banked water
	#based on their demands and existing supplies
    if use_delivery_tolerance:
      risk_index = int(np.floor(self.banking_risk_level*len(self.delivery_risk)))
      at_risk_years = self.delivery_risk < self.total_banked_storage*-1.0
      new_values = self.delivery_risk[at_risk_years]
      new_years = self.delivery_risk_rate[at_risk_years]
      if (len(new_values)-1) < risk_index:
        delivery_tolerance = 0.0
      else:
        rates = np.zeros(len(new_values))
        for x in range(0, len(new_values)):
          rates[x] = (new_values[x] + self.total_banked_storage)/new_years[x]
        sorted_rates = np.sort(rates)
        delivery_tolerance = sorted_rates[risk_index]*-1.0
    else:
      delivery_tolerance = 0.0
      self.target_annual_demand = 999999.9
      #for district in self.district_list:
        #self.target_annual_demand += self.annual_pumping[district][wateryear]
    total_balance = 0.0
    total_deliveries = 0.0
    total_needs = 0.0
    for district in self.district_list:
      for contract in self.contract_list:
        total_balance += self.projected_supply[district][contract]
        total_deliveries += self.deliveries[district][contract][wateryear]
      total_deliveries += self.deliveries[district]['recover_banked'][wateryear]
      total_needs += self.annualdemand[district]*self.seepage[district]
    #total_recovery = (366-dowy)*self.max_recovery + self.max_leiu_exchange
    total_recovery = (366-dowy)*self.max_recovery + self.max_leiu_exchange

    total_needs += additional_carryover
    self.daily_supplies['recovery_cap'][t] = total_recovery

    if (total_balance + total_recovery) < total_needs and (total_balance + total_deliveries) < (self.target_annual_demand - delivery_tolerance):
      self.use_recovery = 1.0
    else:
      self.use_recovery = 0.0
	  
      	  
  def open_recharge(self,t,m,da,wateryear,year,numdays_fillup, numdays_fillup2, key, wyt, reachable_turnouts, additional_carryover, contract_allocation):
    #for a given contract owned by the district (key), how much recharge can they expect to be able to use
	#before the reservoir associated w/ that contract fills to the point where it needs to begin spilling water
	#(numdays_fillup) - i.e., how much surface water storage can we keep before start losing it
	#self.recharge_carryover is the district variable that shows how much 'excess' allocation there is on a particular
	#contract - i.e., how much of the allocation will not be able to be recharged before the reservoir spills
    total_recharge = 0.0
    total_recharge2 = 0.0
    carryover_storage_proj = 0.0
    spill_release_carryover = 0.0
    service_area_adjust = {}

    for x in self.district_list:
      is_reachable = 0
      for turnout in reachable_turnouts:
        for y in self.turnout_list[x]:
          if y == turnout:
            is_reachable = 1
            break
        if is_reachable == 1:
          break
      if is_reachable == 1:
        service_area_adjust[x] = 1.0
      else:
        service_area_adjust[x] = 0.0
	  
    adjusted_sw_sa = service_area_adjust
    
    #for x in self.district_list:
      #spill_release_carryover += max(self.projected_supply[x][key] - self.annualdemand[x]*adjusted_sw_sa[x], 0.0)

    ###Find projected recharge available to district
    #if spill_release_carryover > 0.0:
      #total_recharge_capacity = (self.max_direct_recharge[0] + self.max_leiu_recharge[m])*(self.days_in_month[year][m]-da)
        ##calculate both direct & in leiu recharge available to the district through the end of this water year
      #if m < 8:
        #for future_month in range(m+1,9):
          #total_recharge_capacity += self.max_direct_recharge[future_month - m]*self.days_in_month[year][future_month] + self.max_leiu_recharge[future_month]*self.days_in_month[year+1][future_month]
      #elif m > 8:
        #for future_month in range(m+1,12):
          #total_recharge_capacity += self.max_direct_recharge[future_month - m]*self.days_in_month[year][future_month] + self.max_leiu_recharge[future_month]*self.days_in_month[year+1][future_month]
        #for future_month in range(0,9):
          #total_recharge_capacity += self.max_direct_recharge[future_month - m]*self.days_in_month[year+1][future_month] + self.max_leiu_recharge[future_month]*self.days_in_month[year+1][future_month]
      #else:
        #total_recharge_capacity = 0.0
      #spill_release_carryover -= total_recharge_capacity
      #spill_release_carryover -= additional_carryover
      #spill_release_carryover = max(spill_release_carryover, 0.0)
    

    if numdays_fillup < 365.0:
      ##how many days remain before the reservoir fills? 		  
      days_left = numdays_fillup
	  #tabulate how much water can be recharged between now & reservoir fillup (current month)
      this_month_recharge = (self.max_direct_recharge[0] + self.max_leiu_recharge[0])*min(self.days_in_month[year][m] - da,days_left)
      total_recharge += this_month_recharge
	  #days before fillup remaining after current month
      days_left -= (self.days_in_month[year][m] - da)
	  
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
	  
      spill_release_carryover = 0.0
      for xx in self.district_list:
        for y in self.contract_list:
          spill_release_carryover += max(self.projected_supply[xx][y] - self.annualdemand[xx]*service_area_adjust[xx] - self.carryover_rights[xx][y], 0.0)
      spill_release_carryover -= (total_recharge2  + self.demand_days['lookahead'][key])
      spill_release_carryover = max(spill_release_carryover, 0.0)

      carryover_storage_proj = 0.0
      for xx in self.district_list:
        for y in self.contract_list:
          carryover_storage_proj += max(self.carryover[xx][y] - self.deliveries[xx][y][wateryear] - self.carryover_rights[xx][y], 0.0)
      carryover_storage_proj -= (total_recharge + self.demand_days['current'][key])
      carryover_storage_proj = max(carryover_storage_proj, 0.0)

      #carryover_release_proj = min(carryover_storage_proj, max(total_recharge_available - total_recharge_capacity,0.0))
      #carryover_release_current = max(self.carryover[key] - self.deliveries[key][wateryear] - total_recharge_carryover, 0.0)
      #if contract_carryover > 0.0:
      #spill_release_carryover = max(self.carryover[key] - self.deliveries[key][wateryear] - total_recharge, 0.0)
      #else:
      #spill_release_carryover = max(self.projected_supply[key] - self.annualdemand*adjusted_sw_sa - total_recharge*service_area_adjust - self.contract_carryover_list[key]*adjusted_sw_sa, 0.0)
      district_fracs = {}
      if spill_release_carryover > carryover_storage_proj:
        total_available_for_recharge = 0.0
        for xx in self.district_list:
          for y in self.contract_list:
            total_available_for_recharge += max(self.projected_supply[xx][y], 0.0)
          total_available_for_recharge -= self.annualdemand[xx]

        if total_available_for_recharge > 0.0:		  
          for xx in self.district_list:
            district_fracs[xx] = max(self.projected_supply[xx][key] - self.annualdemand[xx], 0.0)/total_available_for_recharge
            self.recharge_carryover[xx][key] = max(spill_release_carryover, 0.0)*district_fracs[xx]
        else:
          for xx in self.district_list:
            self.recharge_carryover[key] = 0.0
      else:
        total_available_for_recharge = 0.0
        for xx in self.district_list:
          for y in self.contract_list:
            total_available_for_recharge += max(self.carryover[xx][y] - self.deliveries[xx][y][wateryear], 0.0)
        if total_available_for_recharge > 0.0:		  
          for xx in self.district_list:
            district_fracs[xx] = max(self.carryover[xx][key] - self.deliveries[xx][key][wateryear], 0.0)/total_available_for_recharge
            self.recharge_carryover[xx][key] = max(carryover_storage_proj, 0.0)*district_fracs[xx]
        else:
          for xx in self.district_list:
            self.recharge_carryover[xx][key] = 0.0
      if contract_allocation == 0:
        total_secondary_contract = 0.0        
        for xx in self.district_list:
          total_secondary_contract += self.projected_supply[xx][key]
        if total_secondary_contract > 0.0:
          for xx in self.district_list:
            self.recharge_carryover[xx][key] = max(self.recharge_carryover[xx][key], (total_secondary_contract - total_recharge - self.demand_days['current'][key])*(self.projected_supply[xx][key]/total_secondary_contract), 0.0)
        
    else:
      for x in self.district_list:
        self.recharge_carryover[x][key] = 0.0
		
    self.daily_supplies['numdays'][t] = numdays_fillup
    self.daily_supplies['recharge_cap'][t] = total_recharge

    
		
      
  def get_urban_recovery_target(self, pumping, project_contract, wateryear, dowy, year, wyt, demand_days, t, district, start_month):
    max_pumping_shortfall = 0.0
    pumping_shortfall = 0.0
    monthcounter = start_month
    daycounter = 0
    tot_days = 0
    if demand_days > 365.0:
      max_pumping_shortfall = 999.9
    else:
      while tot_days < demand_days:
        pumping_shortfall += np.sum(self.pumping[district][(t-dowy+tot_days):(t-dowy+tot_days+min(demand_days - tot_days, 30))]/1000.0) - pumping['swp']['gains'][monthcounter]*project_contract*self.private_fraction[district]
        tot_days += 30
        monthcounter += 1
        if monthcounter == 12:
          monthcounter = 0

        max_pumping_shortfall = max(pumping_shortfall, max_pumping_shortfall)	  

  	  
    return max(max_pumping_shortfall, 0.0)
	
  def set_turnback_pool(self, key, year, additional_carryover):
    ##This function creates the 'turnback pool' (note: only for SWP contracts now, can be used for others)
    ##finding contractors with 'extra' contract water that they would like to sell, and contractors who would
    ##like to purchase that water.  
    self.turnback_sales = 0.0
    self.turnback_purchases = 0.0
    total_recharge_ability = 0.0
    total_projected_supply = 0.0
    for y in self.contract_list:
      for xx in self.district_list:
        total_projected_supply += self.projected_supply[xx][y]
      for month_count in range(0, 4):
        # total recharge Jun,Jul,Aug,Sep
        total_recharge_ability += self.max_direct_recharge[month_count]*self.days_in_month[year][month_count + 5]
    
    contract_fraction = 0.0
    if total_projected_supply > 0.0:
      for xx in self.district_list:
        contract_fraction += max(min(self.projected_supply[xx][key]/total_projected_supply, 1.0), 0.0)
    else:
      contract_fraction = 0.0
	  
    #districts sell water if their projected contracts are greater than their remaining annual demand, plus their remaining recharge capacity in this water year, plus their recharge capacity in the next water year (through January)
    self.turnback_sales = {}
    self.turnback_purchases = {}

    for x in self.district_list:
      self.turnback_sales[x] = 0.0
      self.turnback_purchases[x] = 0.0
      self.turnback_sales[x] += max(self.projected_supply[xx][key] - (self.annualdemand[xx] + total_recharge_ability + additional_carryover)*contract_fraction, 0.0)
      self.turnback_purchases[x] += max(self.annualdemand[xx]*contract_fraction - self.projected_supply[xx][key] - self.max_recovery*122*contract_fraction, 0.0)

    return self.turnback_sales, self.turnback_purchases	  
      
  def make_turnback_purchases(self, turnback_sellers, turnback_buyers, key):
    #once we know how much water is in the 'selling' pool and the 'buying' pool, we can determine the total turnback pool - min(buying,selling), then
    #determine what % of each request is filled (i.e., if the selling pool is only 1/2 of the buying pool, then buyers only get 1/2 of their request, or visa versa	
    if min(turnback_sellers, turnback_buyers) > 0.0:
      sellers_frac = -1*min(turnback_sellers, turnback_buyers)/turnback_sellers
      buyers_frac = min(turnback_sellers, turnback_buyers)/turnback_buyers
      for x in self.district_list:
        if self.turnback_sales[x] > 0.0:
          self.turnback_pool[x][key] = max(self.turnback_sales[x], 0.0)*sellers_frac
        elif self.turnback_purchases[x] > 0.0:
          self.turnback_pool[x][key] = max(self.turnback_purchases[x], 0.0)*buyers_frac

#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################DETERMINE DELIVERIES ON CANAL######################################################
#####################################################################################################################

			
  def find_node_demand(self,contract_list, search_type, district_name):
    #this function is used to calculate the current demand at each 'district' node
    access_mult = self.seepage[district_name]#this accounts for water seepage & the total district area that can be reached by SW canals (seepage is >= 1.0; surface_water_sa <= 1.0)
    total_projected_allocation = 0.0
    for y in contract_list:
      total_projected_allocation += max(self.projected_supply[district_name][y.name], 0.0)#projected allocation

    #percentage of demand filled in the day is equal to the total projected allocation as a percent of annual demand
	#(i.e., if allocations are projected to be 1/2 of annual demand, then they try to fill 50% of daily irrigation demands with surface water
    total_demand_met = 1.0
    #self.dailydemand_start is the initial daily district demand (self.dailydemand is updated as deliveries are made) - we try to fill the total_demand_met fraction of dailydemand_start, or what remains of demand in self.dailydemand, whichever is smaller
    if search_type == 'flood':
      if self.annualdemand[district_name] > 0.0 and total_projected_allocation > self.annualdemand[district_name]:
        demand_constraint = (1.0 - min(total_projected_allocation/self.annualdemand[district_name], 1.0))*max(min(self.dailydemand_start[district_name]*access_mult*total_demand_met, self.dailydemand[district_name]*access_mult),0.0)	  
      else:
        demand_constraint = max(min(self.dailydemand_start[district_name]*access_mult*total_demand_met, self.dailydemand[district_name]*access_mult),0.0)	  

    else:
      demand_constraint = max(min(self.dailydemand_start[district_name]*access_mult*total_demand_met, self.dailydemand[district_name]*access_mult),0.0)
    #if we want to include recharge demands in the demand calculations, add available recharge space
			  
    return demand_constraint     
	
  def set_request_to_district(self, demand, search_type, contract_list, bank_space, dowy, district_name):
    #this function is used to determine if a district node 'wants' to make a request
	#under the different usage types (flood, delievery, banking, or recovery) under a given contract
	#(contract_list)
    self.projected_supply[district_name]['tot'] = 0.0
    for y in self.current_balance[district_name]:
      self.projected_supply[district_name]['tot'] += self.projected_supply[district_name][y]
    #for flood deliveries, a district requests water if they don't have
	#excess contract water that they don't think they can recharge (i.e. they don't purchase
	#flood water if they can't use all their contract water
    if search_type == "flood":
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
      total_current_balance = 0.0
      total_projected_supply = 0.0
      for y in contract_list:
        total_current_balance += max(self.current_balance[district_name][y.name], 0.0)
        total_projected_supply += max(self.projected_supply[district_name][y.name], 0.0)
      if self.seasonal_connection[district_name] == 1:
        if self.must_fill == 1:
          return min(total_current_balance, total_projected_supply)
        else:
          return min(total_current_balance, total_projected_supply)
      else:
        return 0.0
    else:
      return 0.0
		
  def set_request_constraints(self, demand, search_type, contract_list, bank_space, bank_capacity, dowy, wateryear):		
    #for banking, a district requests water if they have enough contract water currently in surface water storage and they have 'excess' water for banking (calculated in self.open_recharge)
    if search_type == "banking":
      total_carryover_recharge = 0.0
      total_current_balance = 0.0
      for x in self.district_list:
        for y in contract_list:
          total_carryover_recharge += max(self.recharge_carryover[x][y.name], 0.0)
          total_current_balance += max(self.current_balance[x][y.name], 0.0)
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
          for x in self.district_list:
            total_request = min(max(self.dailydemand[x]*self.seepage[x], 0.0), max(bank_space, 0.0))
        else:
          total_request = 0.0
      else:
        total_request = 0.0
		
      return total_request
		
    if search_type == "flood":
      return demand
		
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
      demand_dict['initial'] = max(min(demand,delivery), 0.0)
      demand_dict['supplemental'] = min(delivery - max(min(demand,delivery), 0.0), demand_constraint - demand_dict['initial'])
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

  def set_deliveries(self, priorities,type_fractions,type_list,toggle_district_recharge,member_name, wateryear):
    #this function takes the deliveries, seperated by priority, and updates the district's daily demand and/or recharge storage
    final_deliveries = 0.0
    for zz in type_list:
      #deliveries at this priority level
      total_deliveries = priorities[zz]*type_fractions[zz]
      #running total of all deliveries at this node
      final_deliveries += total_deliveries
      #deliveries first go to direct irrigation, if demand remains
      total_direct_deliveries = min(total_deliveries/self.seepage, self.dailydemand*self.surface_water_sa)
      #if deliveries are for recharge, send remaining deliveries to recharge
      if toggle_district_recharge == 1:
        total_recharge_deliveries = max(total_deliveries/self.seepage - self.dailydemand*self.surface_water_sa, 0.0)
      else:
        total_recharge_deliveries = 0.0
      #adjust demand/recharge space
      self.dailydemand -= total_direct_deliveries
      self.current_recharge_storage += total_recharge_deliveries
		
    return final_deliveries
				
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################ADJUSST ACCOUNTS AFTER DELIVERY####################################################
#####################################################################################################################

  def give_paper_trade(self, trade_amount, contract_list, wateryear, district):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
	#trade, giving up a surface water contract allocation (contract_list) to the district
	#that owned the groundwater that was recovered
    if self.seepage[district] > 0.0:
      total_alloc = 0.0
      for y in contract_list:
        total_alloc += self.projected_supply[district][y.name]
      actual_delivery = max(min(trade_amount, total_alloc, self.dailydemand[district]*self.seepage[district]), 0.0)
      self.dailydemand[district] -= actual_delivery/self.seepage[district]
      if total_alloc > 0.0:
        for y in contract_list:
          self.paper_balance[y.name] -= actual_delivery*self.projected_supply[district][y.name]/total_alloc
        self.deliveries[district]['exchanged_SW'][wateryear] += actual_delivery
    
    return actual_delivery
		
  def give_paper_exchange(self, trade_amount, contract_list, trade_frac, wateryear, district_name):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
	#trade, giving up a surface water contract allocation (contract_list) to the district
	#that owned the groundwater that was recovered
    contract_counter = 0
    for y in contract_list:
      self.paper_balance[y.name] -= trade_amount*trade_frac[contract_counter]
      contract_counter += 1
    self.deliveries[district_name]['exchanged_SW'][wateryear] += trade_amount

	  
  def get_paper_trade(self, trade_amount, contract_list, wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	#the paper credit is in exchange for delivering recovered groundwater to another party (district)
    total_alloc = 0.0
    contract_frac = 0.0
    for y in contract_list:
      for x in self.district_list:
        total_alloc += self.projected_supply[x][y.name]
    if total_alloc > 0.0:
      for y in contract_list:
        for x in self.district_list:
          self.paper_balance[y.name] += trade_amount*self.projected_supply[x][y.name]/total_alloc

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

  def record_direct_delivery(self, delivery, wateryear, district):
    actual_delivery = min(delivery, self.dailydemand[district]*self.seepage[district])

    self.deliveries[district]['recover_banked'][wateryear] += actual_delivery
    self.dailydemand[district] -= actual_delivery/(self.seepage[district])
    self.direct_recovery_delivery[district] = 0.0

    return actual_delivery

  def direct_delivery_bank(self, delivery, wateryear, district):
    #this function takes a delivery of recoverd groundwater and applies it to irrigation demand in a district
	#the recovered groundwater is delivered to the district that originally owned the water, so no 'paper' trade is needed
    actual_delivery = min(delivery, self.dailydemand[district]*self.seepage[district] - self.direct_recovery_delivery[district])
    self.direct_recovery_delivery[district] += actual_delivery
    #self.deliveries[district]['recover_banked'][wateryear] += actual_delivery
    #self.dailydemand[district] -= actual_delivery/self.seepage[district]*self.surface_water_sa[district]
    return actual_delivery
	
  def adjust_accounts(self, direct_deliveries, recharge_deliveries, contract_list, search_type, wateryear):
    #this function accepts water under a specific condition (flood, irrigation delivery, banking), and 
	#adjusts the proper accounting balances
    total_recharge_balance = 0.0
    total_current_balance = 0.0
 
    delivery_by_contract = {}
    for y in contract_list:
      for x in self.district_list:
        total_current_balance += max(self.current_balance[x][y.name], 0.0)
        total_recharge_balance += max(self.recharge_carryover[x][y.name], 0.0)
      delivery_by_contract[y.name] = 0.0
    flood_counter = 0
    for y in contract_list:
      #find the percentage of total deliveries that come from each contract
      contract_deliveries = 0.0
      if search_type == 'flood':
          if flood_counter == 0:
            contract_deliveries = (direct_deliveries + recharge_deliveries)
            flood_counter = 1
          else:
            contract_deliveries = 0.0
      elif total_current_balance > 0.0:
        for x in self.district_list:
          if search_type == 'delivery':
            contract_deliveries += (direct_deliveries + recharge_deliveries)*max(self.projected_supply[x][y.name], 0.0)/total_current_balance
          elif search_type == 'banking':
            contract_deliveries += (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][y.name], 0.0)/total_current_balance
          elif search_type == 'recovery':
            contract_deliveries += (direct_deliveries + recharge_deliveries)*max(self.current_balance[x][y.name], 0.0)/total_current_balance
      else:
        contract_deliveries = 0.0

      delivery_by_contract[y.name] = contract_deliveries
      #flood deliveries do not count against a district's contract allocation, so the deliveries are recorded as 'flood'
      if search_type == "flood":
        for x in self.district_list:
          if contract_deliveries > 0.0:
            self.deliveries[x][y.name + '_flood'][wateryear] += recharge_deliveries
            self.deliveries[x][y.name + '_flood_irrigation'][wateryear] += direct_deliveries
      else:
        #irrigation/banking deliveries are recorded under the contract name so they are included in the 
		#contract balance calculations
        #update the individual district accounts
        if search_type == 'banking':
          for x in self.district_list:
            if total_recharge_balance > 0.0:
              self.deliveries[x][y.name][wateryear] += (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][y.name], 0.0)/total_recharge_balance
              self.current_balance[x][y.name] -= (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][y.name], 0.0)/total_recharge_balance
              self.deliveries[x]['recharged'][wateryear] += (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][y.name], 0.0)/total_recharge_balance
              self.recharge_carryover[x][y.name] -= min((direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][y.name], 0.0)/total_recharge_balance, self.recharge_carryover[x][y.name])
        else:
          for x in self.district_list:
            if total_current_balance > 0.0:
              self.deliveries[x][y.name][wateryear] += (direct_deliveries + recharge_deliveries)*max(self.current_balance[x][y.name], 0.0)/total_current_balance
              self.current_balance[x][y.name] -= (direct_deliveries + recharge_deliveries)*max(self.current_balance[x][y.name], 0.0)/total_current_balance
	
    return delivery_by_contract
	
  def adjust_account_district(self, actual_deliveries, contract_list, search_type, wateryear, district_name):
    total_current_balance = 0.0
    delivery_by_contract = {}
    for y in contract_list:
      if search_type == 'flood':
        total_current_balance += 1.0
      elif search_type == 'delivery':
        total_current_balance += max(self.projected_supply[district_name][y.name], 0.0)
      elif search_type == 'banking':
        total_current_balance += max(self.recharge_carryover[district_name][y.name], 0.0)
      elif search_type == 'recovery':
        total_current_balance += max(self.current_balance[district_name][y.name], 0.0)
      delivery_by_contract[y.name] = 0.0
    flood_counter = 0
    for y in contract_list:
      #find the percentage of total deliveries that come from each contract
      if total_current_balance > 0.0:
        if search_type == 'flood':
          if flood_counter == 0:
            contract_deliveries = actual_deliveries
            flood_counter = 1
          else:
            contract_deliveries = 0.0
        elif search_type == 'delivery':
          contract_deliveries = actual_deliveries*max(self.projected_supply[district_name][y.name], 0.0)/total_current_balance
        elif search_type == 'banking':
          contract_deliveries = actual_deliveries*max(self.recharge_carryover[district_name][y.name], 0.0)/total_current_balance
        elif search_type == 'recovery':
          contract_deliveries = actual_deliveries*max(self.current_balance[district_name][y.name], 0.0)/total_current_balance

      else:
        contract_deliveries = 0.0
      delivery_by_contract[y.name] = contract_deliveries
      #flood deliveries do not count against a district's contract allocation, so the deliveries are recorded as 'flood'
      if search_type == "flood":
        self.deliveries[district_name][y.name + '_flood'][wateryear] += contract_deliveries
      else:
        #irrigation/banking deliveries are recorded under the contract name so they are included in the 
		#contract balance calculations
        #update the individual district accounts
        self.deliveries[district_name][y.name][wateryear] += contract_deliveries
        self.current_balance[district_name][y.name] -= contract_deliveries
        if search_type == 'banking':
          #if deliveries ar for banking, update banking accounts
          self.deliveries[district_name]['recharged'][wateryear] += contract_deliveries
          self.recharge_carryover[district_name][y.name] -= min(contract_deliveries, self.recharge_carryover[district_name][y.name])

    self.dailydemand[district_name] -= min(actual_deliveries/self.seepage[district_name],self.dailydemand[district_name])

    return delivery_by_contract

	
  def adjust_bank_accounts(self, member_name, deliveries, wateryear):
    #when deliveries are made for banking, keep track of the member's individual accounts
    self.bank_deliveries[member_name] += deliveries#keeps track of how much of the capacity is being used in the current timestep
    self.deliveries['inleiu'][wateryear] += deliveries#if deliveries being made 'inleiu', then count as inleiu deliveries
    self.inleiubanked[member_name] += deliveries * self.inleiuhaircut#this is the running account of the member's banking storage
	
  def adjust_recovery(self, deliveries, member_name, wateryear):
    #if recovery deliveries are made, adjust the banking accounts and account for the recovery capacity use
    self.inleiubanked[member_name] -= deliveries#this is the running account of the member's banking storage
    self.deliveries['leiupumping'][wateryear] += deliveries
    self.recovery_use[member_name] += deliveries#keeps track of how much of the capacity is being used in the current timestep

  def adjust_exchange(self, deliveries, member_name, wateryear):
    #if recovery deliveries are made, adjust the banking accounts and account for the recovery capacity use
    self.inleiubanked[member_name] -= deliveries#this is the running account of the member's banking storage
    self.deliveries['leiupumping'][wateryear] += deliveries

	
  def absorb_storage(self):
    #water delivered to a bank as 'storage' (on the surface) is 'absorbed', clearing up storage space for the next timestep
    #also triggers self.thismonthuse, which keeps track of how many conecutive months a recharge bank is used (and the effect on the recharge rate of the spreading pool)
    if self.in_leiu_banking:
      if self.current_recharge_storage > 0.0:
        self.thismonthuse = 1
        absorb_fraction = min(self.in_district_direct_recharge*cfs_tafd/self.current_recharge_storage,1.0)
        for x in self.participant_list:
          self.current_recharge_storage -= self.current_recharge_storage*absorb_fraction
    else:
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
      self.daily_supplies_full[x + '_projected'][t] = self.projected_supply[x]
      self.daily_supplies_full[x + '_paper'][t] = self.paper_balance[x]
      self.daily_supplies_full[x + '_carryover'][t] = self.carryover[x]

      self.daily_supplies_full[x + '_turnback'][t] = self.turnback_pool[x]
    for x in self.non_contract_delivery_list:
      self.daily_supplies_full[x][t] = self.deliveries[x][wateryear]


  def accounting(self,t, da, m, wateryear,key):
    #takes delivery/allocation values and builds timeseries that show what water was used for (recharge, banking, irrigation etc...)
	#delivery/allocation data are set cumulatively - so that values will 'stack' in a area plot.
	#Allocations are positive (stack above the x-axis in a plot)
    total_projected_supply = 0.0
    total_carryover = 0.0
    total_recharge = 0.0
    self.daily_supplies['annual_demand'][t] = 0.0
    for district_name in self.district_list:
      total_projected_supply += self.projected_supply[district_name][key]
      total_carryover += max(self.carryover[district_name][key] - self.deliveries[district_name][key][wateryear], 0.0)
      total_recharge += max(self.recharge_carryover[district_name][key], 0.0)
      self.daily_supplies['annual_demand'][t] += self.annualdemand[district_name]

    self.daily_supplies['contract_available'][t] += total_projected_supply
    self.daily_supplies['carryover_available'][t] += total_carryover
    if total_recharge > 0.0:
      self.daily_supplies['use_recharge'][t] = 1.0
    self.daily_supplies['use_recovery'][t] = self.use_recovery
    self.daily_supplies['paper'][t] += total_projected_supply
    self.daily_supplies['carryover'][t] += max(total_projected_supply - self.paper_balance[key], 0.0)
    self.daily_supplies['allocation'][t] += max(total_projected_supply - total_carryover - self.paper_balance[key], 0.0)
      #while deliveries are negative (stack below the x-axis in a plot) - the stacking adjustments come in self.accounting_banking_activity()
	
    if m == 9 and da == 30:
      total_deliveries = 0.0
      for district_name in self.district_list:
        self.annual_supplies['delivery'][wateryear] += self.deliveries[district_name][key][wateryear]
        self.annual_supplies['recharge_uncontrolled'][wateryear] += self.deliveries[district_name][key + '_flood'][wateryear]
		
        total_deliveries += self.deliveries[district_name][key][wateryear]
      self.deliveries['undelivered_trades'][wateryear] += max(self.paper_balance[key] - total_deliveries, 0.0)
	
  def accounting_banking_activity(self, t, da, m, wateryear):
    #this is an adjustment for 'delivery' (the delivery values are negative, so adding 'recharged' and 'exchanged_GW' is removing them from the count for 'deliveries' - we only want deliveries for irrigation, not for recharge
    #exchanged_GW is GW that has been pumped out of a bank and 'delivered' to another district. the district gets credit in the reservoir, and deliveries of SW from that reservoir are recorded as 'deliveries' - but we don't want to count that here
	#exchanged_SW is GW that has been pumped out of a bank, not owned by the district, and delivered to that district (i.e., the other side of the exchanged_GW in a GW exchange).  This should technically count as an irrigation delivery from a contract
	#(we want to record that as delivery here) but it doesn't get recorded that way upon delivery.  so we add it back here when were are recording accounts (i.e. exchanged_GW and exchanged_SW are counters to help us square the records from GW exchanges)
    for x in self.district_list:
      self.daily_supplies['delivery'][t] -= self.deliveries[x]['recharged'][wateryear]
      self.daily_supplies['recharge_delivery'][t] += self.deliveries[x]['recharged'][wateryear]

      self.daily_supplies['banked'][t] += self.deliveries[x]['recover_banked'][wateryear]

      self.daily_supplies['delivery'][t] += self.deliveries[x]['exchanged_SW'][wateryear]	  
      self.daily_supplies['leiu_delivered'][t] += self.deliveries[x]['leiupumping'][wateryear]
      self.daily_supplies['leiu_accepted'][t] += self.deliveries[x]['inleiu'][wateryear]

    self.daily_supplies['delivery'][t] -= self.deliveries['exchanged_GW'][wateryear]
    self.daily_supplies['banked'][t] += self.deliveries['exchanged_GW'][wateryear]
	
    self.daily_supplies['banked_storage'][t] += self.total_banked_storage
	
    if m == 9 and da == 30:
      for x in self.district_list:
        self.annual_supplies['delivery'][wateryear] += self.deliveries[x]['exchanged_SW'][wateryear]
        self.annual_supplies['delivery'][wateryear] -= self.deliveries[x]['recharged'][wateryear]
        self.annual_supplies['banked_accepted'][wateryear] += self.deliveries[x]['recover_banked'][wateryear]
		
        self.annual_supplies['leiu_accepted'][wateryear] += self.deliveries[x]['inleiu'][wateryear]
        self.annual_supplies['leiu_delivered'][wateryear] += self.deliveries[x]['leiupumping'][wateryear]
        self.annual_supplies['recharge_delivery'][wateryear] += self.deliveries[x]['recharged'][wateryear]

      self.annual_supplies['delivery'][wateryear] -= self.deliveries['exchanged_GW'][wateryear]

      recharged_recovery = 0.0
      if self.annual_supplies['delivery'][wateryear] < 0.0:
        recharged_recovery = self.annual_supplies['delivery'][wateryear]
        self.annual_supplies['delivery'][wateryear] = 0.0
      self.annual_supplies['banked_accepted'][wateryear] += self.deliveries['exchanged_GW'][wateryear] - self.deliveries['undelivered_trades'][wateryear]
      self.annual_supplies['banked_storage'][wateryear] = self.total_banked_storage
      self.annual_supplies['acreage'][wateryear] = self.total_acreage

	
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

