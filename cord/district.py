from __future__ import division
import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
from .crop import Crop
import json
from .util import *


class District():

  def __init__(self, df, key):
    self.T = len(df)
    self.index = df.index
    self.key = key
    for k,v in json.load(open('cord/districts/%s_properties.json' % key)).items():
        setattr(self,k,v)

    #intialize crop acreages and et demands for crops
    self.irrdemand = Crop(self.zone)
	#initialize dictionary to hold different delivery types
    self.deliveries = {}
    contract_list = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2', 'hidden', 'buchannon', 'eastside', 'tuolumne', 'merced', 'kings', 'kaweah', 'tule', 'kern']
    for x in contract_list:
      #normal contract deliveries
      self.deliveries[x] = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
	  #uncontrolled deliveries from contract
      self.deliveries[x + '_flood'] = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
	#deliveries from a groundwater bank (reocrded by banking partner recieving recovery water)
    self.deliveries['recover_banked'] = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
	#deliveries to a in-leiu bank from a banking partner (recorded by the district acting as a bank)
    self.deliveries['inleiu'] = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
	#deliveries from an in leiu bank to a banking partner (recorded by the district acting as a bank)
    self.deliveries['leiupumping'] = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
	#water delivered from a contract to a recharge basin (direct or in leiu, recorded by the banking partner who owned the water)
    self.deliveries['recharged'] = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
    #deliveries made from a districts bank to third-party district (district recieves a surface water 'paper' credit)
    self.deliveries['exchanged_GW'] = np.zeros((self.index.year[self.T-1] - self.index.year[0]))
    #recorded when a district recieves water from a bank owned by another district (district gives a surface water 'paper' credit)
    self.deliveries['exchanged_SW'] = np.zeros((self.index.year[self.T-1] - self.index.year[0]))

    #keeps track of the total private pumping (estimated) to occur within a district in a given year
    self.totalpumping = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
	
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
    for y in contract_list:
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
    supply_list = ['paper', 'carryover', 'allocation', 'delivery', 'leiu_accepted', 'banked', 'pumping', 'leiu_delivered', 'recharge_delivery', 'recharge_uncontrolled']
    for x in supply_list:
      self.daily_supplies[x] = np.zeros(self.T)
	
    #initialize dictionaries to 'store' annual change in state variables (for export to csv)
    self.annual_supplies = {}
    supply_list = ['delivery', 'leiu_accepted', 'leiu_delivered', 'banked_accepted']
    for x in supply_list:
      self.annual_supplies[x] = np.zeros((self.index.year[self.T-1]-self.index.year[0]))
	
    #Initialize demands
    self.annualdemand = 0.0
    self.dailydemand = 0.0
    self.find_baseline_demands()

    #recovery and pumping variables
    self.recovery_fraction = 0.5
    self.annual_pumping = 0.0
    self.use_recharge = 0.0
    self.use_recovery = 0.0
    self.extra_leiu_recovery = 0.0
    self.max_recovery = 0.0
	
    #for in-district recharge & counters (for keeping track of how long a basin has been continuously 'wet'
    self.recharge_rate = self.in_district_direct_recharge*cfs_tafd
    self.thismonthuse = 0
    self.monthusecounter = 0
    self.monthemptycounter = 0
    self.current_recharge_storage = 0.0
	
    #banking dictionaries to keep track of individual member use & accounts
    if self.in_leiu_banking:
      self.recovery_use = {}
      self.inleiubanked = {}
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


#####################################################################################################################
##################################DEMAND CALCULATION#################################################################
#####################################################################################################################
		
  def find_baseline_demands(self):
    self.monthlydemand = {}
    daysinmonth = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    wyt_list = ['W', 'AN', 'BN', 'D', 'C']
    for wyt in wyt_list:
      self.monthlydemand[wyt] = np.zeros(12)
      for monthloop in range(0,12):
        self.monthlydemand[wyt][monthloop] += self.urban_profile[monthloop]*self.MDD/daysinmonth[monthloop]
        for i,v in enumerate(self.crop_list):
          self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][wyt][monthloop] - self.irrdemand.etM['precip'][wyt][monthloop],0.0)*self.acreage[wyt][i]/(12.0*daysinmonth[monthloop])
          #self.monthlydemand[wyt][monthloop] += max(self.irrdemand.etM[v][wyt][monthloop] ,0.0)*self.acreage[wyt][i]/(12.0*daysinmonth[monthloop])
	  	
			
  def calc_demand(self, wateryear, da, m, m1, wyt):
    #from the monthlydemand dictionary (calculated at the beginning of each wateryear based on ag acreage and urban demands), calculate the daily demand and the remaining annual demand
    daysinmonth = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    monthday = daysinmonth[m-1]
    self.dailydemand = self.monthlydemand[wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[wyt][m1-1]*da/monthday
    if self.dailydemand < 0.0:
      self.dailydemand = 0.0
    #calculate that days 'starting' demand (b/c demand is filled @multiple times, and if we only want to fill a certain fraction of that demand (based on projections of supply & demand for the rest of the year), we want to base that fraction on that day's total demand, not the demand left after other deliveries are made
    self.dailydemand_start = self.dailydemand
	#pro-rate this month's demand based on the day of the month when calculating remaining annual demand
    self.annualdemand = max(self.monthlydemand[wyt][m-1]*(monthday-da), 0.0)
    if m > 9:
      for monthloop in range(m, 12):
        self.annualdemand += max(self.monthlydemand[wyt][monthloop]*daysinmonth[monthloop],0.0)
      for monthloop in range(0,9):
        self.annualdemand += max(self.monthlydemand[wyt][monthloop]*daysinmonth[monthloop], 0.0)
    else:
      for monthloop in range(m, 9):
        self.annualdemand += max(self.monthlydemand[wyt][monthloop]*daysinmonth[monthloop], 0.0)
		
		
  def find_pre_flood_demand(self, wyt):
    #calculates an estimate for water use in the Oct-Dec period (for use in recharge_carryover calculations
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    self.pre_flood_demand = self.monthlydemand[wyt][0]*days_in_month[0] + self.monthlydemand[wyt][1]*days_in_month[1] + self.monthlydemand[wyt][2]
	
  def get_urban_demand(self, t, m, da, wateryear):
    #this function finds demands for the 'branch pumping' urban nodes - Socal, South Bay, & Central Coast
	#demand is equal to pumping of the main california aqueduct and into the branches that services these areas
    dowy_md = [122, 150, 181, 211, 242, 272, 303, 334, 365, 30, 60, 91]
    #cal aqueduct urban demand comes from pumping data, calc seperately
    self.dailydemand = self.pumping[t]/1000.0
    self.dailydemand_start = self.dailydemand
    ##Keep track of ytd pumping to Cal Aqueduct Branches
    self.ytd_pumping[wateryear] += self.dailydemand
    if m == 10 and da == 1:      
      last_month = 0
	  ###Divide aqueduct branch pumping into 'monthly demands'
      for monthloop in range(0,12):
        monthcounter = monthloop + 9
        if monthcounter > 11:
          monthcounter -= 12
        this_month = dowy_md[monthcounter]
        for wyt in ['W', 'AN', 'BN', 'D', 'C']:
          self.monthlydemand[wyt][monthcounter] = np.mean(self.pumping[(t + last_month):(t + this_month)])/1000.0
        last_month = this_month + 1

		
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
    if balance_type == 'contract':
      #district_storage - district's water that is currently available (in storage at reservoir)
      #(water_available - tot_carryover)*self.project_contract[key] - individual district share of the existing (in storage) contract balance, this includes contract water that has already been delivered to all contractors
	  #self.deliveries[key][wateryear] - individual district deliveries (how much of 'their' contract has already been delivered)
	  #self.carryover[key] - individual district share of contract carryover
	  #paper_balance[key] - keeps track of 'paper' groundwater trades (negative means they have accepted GW deliveries in exchange for trading some of their water stored in reservoir, positive means they sent their banked GW to another district in exchage for SW storage
	  #turnback_pool[key] - how much water was bought/sold on the turnback pool(negative is sold, positive is bought)
      district_storage = (water_available-tot_carryover)*self.project_contract[key] - self.deliveries[key][wateryear] + self.carryover[key]  + self.paper_balance[key] + self.turnback_pool[key]
      #annual allocation - remaining (undelivered) district share of expected total contract allocation
	  #same as above, but projected_allocation*self.project_contract[key] - individual share of expected total contract allocation, this includes contract water that has already been delivered to all contractors
      annual_allocation = projected_allocation*self.project_contract[key] - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      storage_balance = current_water*self.project_contract[key] 
    elif balance_type == 'right':
      #same as above, but for contracts that are expressed as 'rights' instead of allocations
      district_storage = (water_available-tot_carryover)*self.rights[key]['capacity'] - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      annual_allocation = projected_allocation*self.rights[key]['capacity'] - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      storage_balance = current_water*self.rights[key]['capacity']
    
    self.current_balance[key] = max(min(storage_balance,annual_allocation), 0.0)
    self.projected_supply[key] = max(annual_allocation,0.0)
		  
    return max(self.projected_supply[key] - self.annualdemand, 0.0)
	

  def calc_carryover(self, existing_balance, wateryear, balance_type, key):
    #at the end of each wateryear, we tally up the full allocation to the contract, how much was used (and moved around in other balances - carryover, 'paper balance' and turnback_pools) to figure out how much each district can 'carryover' to the next year
    if balance_type == 'contract':
      annual_allocation = existing_balance*self.project_contract[key] - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      max_carryover = self.contract_carryover_list[key]
    elif balance_type == 'right':
      annual_allocation = existing_balance*self.rights[key]['capacity'] - self.deliveries[key][wateryear] + self.carryover[key] + self.paper_balance[key] + self.turnback_pool[key]
      max_carryover = self.contract_carryover_list[key]
    if key == 'cvpdelta' or key == 'exchange':
      if self.project_contract[key] > 0.0:
        print(wateryear, end = " ")
        print(key, end = " ")
        print(self.key, end = " ")
        print(existing_balance, end = " ")
        print(self.project_contract[key], end = " ")
        print("%.2f" % self.deliveries[key][wateryear], end = " ")
        print("%.2f" % self.carryover[key], end = " ")
        print("%.2f" % self.paper_balance[key], end = " ")
        print("%.2f" % self.turnback_pool[key], end = " ")
        print(annual_allocation, end = " ")
        print(max_carryover)

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
	
  def open_recovery(self, dowy):
    #this function determines if a district wants to recover banked water
	#based on their demands and existing supplies
    total_balance = 0.0
    total_recovery = (366-dowy)*self.max_recovery + self.extra_leiu_recovery
    
    for key in self.contract_list:
      total_balance += self.projected_supply[key]
	  
    if (total_balance + total_recovery) < self.annualdemand*self.seepage*self.surface_water_sa*self.recovery_fraction:
      self.use_recovery = 1.0
    else:
      self.use_recovery = 0.0
	  
    self.min_direct_recovery = max(self.annualdemand - total_balance,0.0)/(366-dowy)
    
	  	  
  def open_recharge(self,m,da,wateryear,numdays_fillup, key, wyt):
    #for a given contract owned by the district (key), how much recharge can they expect to be able to use
	#before the reservoir associated w/ that contract fills to the point where it needs to begin spilling water
	#(numdays_fillup) - i.e., how much surface water storage can we keep before start losing it
	#self.recharge_carryover is the district variable that shows how much 'excess' allocation there is on a particular
	#contract - i.e., how much of the allocation will not be able to be recharged before the reservoir spills
    daysinmonth = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    total_recharge_available = self.projected_supply['tot'] - self.annualdemand*self.surface_water_sa
    total_recharge = 0.0
    ###Find projected recharge available to district
    if total_recharge_available > 0.0:
      current_month_left = (daysinmonth[m]-da)/daysinmonth[m]
      total_recharge_capacity = (self.max_direct_recharge[0]*daysinmonth[m] + self.max_leiu_recharge[m])*current_month_left
      ##calculate both direct & in leiu recharge available to the district through the end of this water year
      if m < 8:
        for future_month in range(m+1,9):
          total_recharge_capacity += self.max_direct_recharge[future_month - m]*daysinmonth[future_month] + self.max_leiu_recharge[future_month]
      elif m > 8:
        for future_month in range(m+1,12):
          total_recharge_capacity += self.max_direct_recharge[future_month - m]*daysinmonth[future_month] + self.max_leiu_recharge[future_month]
        for future_month in range(0,9):
          total_recharge_capacity += self.max_direct_recharge[future_month - m]*daysinmonth[future_month] + self.max_leiu_recharge[future_month]
    else:
      total_recharge_capacity = 0.0
	  
    ##how many days remain before the reservoir fills? 		  
    days_left = numdays_fillup
	#tabulate how much water can be recharged between now & reservoir fillup (current month)
    this_month_recharge = (self.max_direct_recharge[0] + self.max_leiu_recharge[m]/daysinmonth[m])*min(daysinmonth[m] - da,days_left)
    total_recharge += this_month_recharge
	#days before fillup remaining after current month
    days_left -= (daysinmonth[m] - da)
	
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
		
 	  # continue to tabulate how much water can be recharged between now & reservoir fillup (future months)
      this_month_recharge = (self.max_direct_recharge[monthcounter+monthcounter_loop] + self.max_leiu_recharge[m+monthcounter]/daysinmonth[m+monthcounter])*min(daysinmonth[m+monthcounter],days_left)
      total_recharge += this_month_recharge
     
      days_left -= daysinmonth[m+monthcounter]
      if m + monthcounter == 9:
        next_year_counter = 1
        
    ###Uses the projected supply calculation to determine when to recharge water.  There are a number of conditions under which a 
	###district will recharge water.  Projected allocations are compared to total demand, recharge capacity, and the probability of 
	###surface water storage spilling carryover water.  If any of these conditions triggers recharge, the district will release water
	##for recharge
    if next_year_counter == 1:
      carryover_storage_proj = max(self.projected_supply[key] - self.annualdemand*self.surface_water_sa - total_recharge, 0.0)
    else:
      carryover_storage_proj = 0.0
    #carryover_release_proj = min(carryover_storage_proj, max(total_recharge_available - total_recharge_capacity,0.0))
    #carryover_release_current = max(self.carryover[key] - self.deliveries[key][wateryear] - total_recharge_carryover, 0.0)
    spill_release_carryover = max(self.carryover[key] - self.deliveries[key][wateryear] - total_recharge, 0.0)
    ##The amount of recharge a district wants is then saved and sent to the canal class where it 'looks' for an available spot to recharge the water
    #self.recharge_carryover[key] = max(carryover_release_proj, carryover_release_current, spill_release_carryover, spill_release_storage)
    self.recharge_carryover[key] = max(carryover_storage_proj, spill_release_carryover, 0.0)

    ##Similar conditions also calculate the amount of regular tableA deliveries for direct irrigation to request
    delivery_release = max(total_recharge_available, 0.0)
    delivery_spill_carryover = max(self.carryover[key] - self.deliveries[key][wateryear], 0.0)
    self.delivery_carryover[key] = max(delivery_spill_carryover, delivery_release)
	
  def set_turnback_pool(self, key):
    ##This function creates the 'turnback pool' (note: only for SWP contracts now, can be used for others)
    ##finding contractors with 'extra' contract water that they would like to sell, and contractors who would
    ##like to purchase that water.  
    self.turnback_sales = 0.0
    self.turnback_purchases = 0.0
    daysinmonth = [31.0, 28.0, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]
    total_recharge_ability = 0.0
    total_projected_supply = 0.0
    for y in self.contract_list:
      total_projected_supply += self.projected_supply[y]
      for month_count in range(0, 4):
        total_recharge_ability += self.max_direct_recharge[month_count]*days_in_month[month_count + 5]
    
    if total_projected_supply > 0.0:
      contract_fraction = max(min(self.projected_supply[key]/total_projected_supply, 1.0), 0.0)
    else:
      contract_fraction = 0.0
	  
    #districts sell water if their projected contracts are greater than their remaining annual demand, plus their remaining recharge capacity in this water year, plus their recharge capacity in the next water year (through January)
    self.turnback_sales = max(self.projected_supply[key] - (self.annualdemand - total_recharge_ability - self.pre_flood_demand)*contract_fraction, 0.0)
    if self.in_leiu_banking:
      self.turnback_purchases = 0.0
    else:
      ##districts buy turnback water if their annual demands are greater than their projected supply plus their capacity to recover banked groundwater
      self.turnback_purchases = max(self.annualdemand*contract_fraction - self.projected_supply[key] - self.max_recovery*122*contract_fraction, 0.0)

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

			
  def find_node_demand(self,contract_list, partial_demand_toggle,  toggle_recharge):
    #this function is used to calculate the current demand at each 'district' node
    access_mult = self.surface_water_sa*self.seepage#this accounts for water seepage & the total district area that can be reached by SW canals (seepage is >= 1.0; surface_water_sa <= 1.0)
	
    total_projected_allocation = 0.0
    total_deliveries = 0.0

    for y in contract_list:
      total_projected_allocation += max(self.projected_supply[y.name], 0.0)#projected allocation
	  #total_deliveries += self.recharge_carryover[y.name]#delivery carryover is how much carryover water is left for delivery (in the early parts of the year)

    if self.must_fill == 1:
      #pumping to urban branches of the Cal Aqueduct is 'must fill', (i.e., demand is always met)
      demand_constraint = self.dailydemand*access_mult
    else:	  
      #percentage of demand filled in the day is equal to the total projected allocation as a percent of annual demand
	  #(i.e., if allocations are projected to be 1/2 of annual demand, then they try to fill 50% of daily irrigation demands with surface water
      if self.annualdemand*access_mult > 0.0 and partial_demand_toggle == 1:
        total_demand_met = min(max(total_projected_allocation/(self.annualdemand*access_mult), 0.0), 1.0)
      else:
        total_demand_met = 1.0
      #self.dailydemand_start is the initial daily district demand (self.dailydemand is updated as deliveries are made) - we try to fill the total_demand_met fraction of dailydemand_start, or what remains of demand in self.dailydemand, whichever is smaller
      demand_constraint = min(max(total_deliveries, self.dailydemand_start*access_mult*total_demand_met), self.dailydemand*access_mult, total_projected_allocation)
      #if we want to include recharge demands in the demand calculations, add available recharge space
      if toggle_recharge == 1:
        demand_constraint += max(self.in_district_storage - self.current_recharge_storage, 0.0)*total_demand_met
			  
    return demand_constraint
	
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
	
  def set_request_constraints(self, demand, search_type, contract_list, bank_space, dowy):
    #this function is used to determine if a district node 'wants' to make a request
	#under the different usage types (flood, delievery, banking, or recovery) under a given contract
	#(contract_list)
    self.projected_supply['tot'] = 0.0
    for y in self.contract_list:
      self.projected_supply['tot'] += self.projected_supply[y]
    #for flood deliveries, a district requests water if they don't have
	#excess contract water that they don't think they can recharge (i.e. they don't purchase
	#flood water if they can't use all their contract water
    if search_type == "flood":
      tot_recharge = 0.0
      for y in contract_list:
        tot_recharge += self.recharge_carryover[y.name]
      if tot_recharge <= 0.0 and self.seasonal_connection == 1:
        return demand
      else:
        return 0.0

    #for normal irrigation deliveries, a district requests water if they have enough water currently
	#in surface water storage under the given contract
    if search_type == "delivery":
      total_current_balance = 0.0
      total_projected_supply = 0.0
      for y in contract_list:
        total_current_balance += max(self.current_balance[y.name], 0.0)
        total_projected_supply += max(self.projected_supply[y.name], 0.0)
      if self.seasonal_connection == 1:
        if self.must_fill == 1:
          return total_current_balance
        elif dowy < 242:
          if total_projected_supply > self.annualdemand or self.recharge_carryover[y.name] > 0.0:
            return total_current_balance
          else:
            return 0.0
        else:
          return total_current_balance
      else:
        return 0.0
		
    #for banking, a district requests water if they have enough contract water currently in surface water storage and they have 'excess' water for banking (calculated in self.open_recharge)
    if search_type == "banking":
      total_carryover_recharge = 0.0
      total_current_balance = 0.0
      for y in contract_list:
        total_carryover_recharge += max(self.recharge_carryover[y.name], 0.0)
        total_current_balance += max(self.current_balance[y.name], 0.0)
      return min(total_carryover_recharge, total_current_balance)
	  
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
	  
  def set_demand_priority(self, priority_list, contract_list, demand, delivery, search_type, contract_canal):
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
          demand_dict['turnout'] = 0.0
          demand_dict['excess'] = 0.0
        else:
          demand_dict['contractor'] = 0.0
          demand_dict['turnout'] = max(min(demand,delivery), 0.0)
          demand_dict['excess'] = 0.0
      else:
        demand_dict['contractor'] = 0.0
        demand_dict['turnout'] = 0.0
        demand_dict['excess'] = delivery
    #irrigation deliveries have only one type of priority (the contract that is currently being deliveried)
    elif search_type == 'delivery':
      demand_dict[contract_canal] = max(min(demand,delivery), 0.0)
    #in-leiu banks have demands that are either priority (capacity that the district has direct ownership over) or secondary (excess capacity that isn't being used by the owner)
    elif search_type == 'banking':
      demand_dict['priority'] = max(min(demand,delivery), 0.0)
      demand_dict['secondary'] = 0.0
    #recovery is the same priority structure as banking, but we use different names (initial & supplemental) to keep things straight)
    elif search_type == 'recovery':
      if self.in_leiu_banking:
        demand_dict['initial'] = max(min(demand,delivery), 0.0)
        current_recovery_use = 0.0
        for x in self.recovery_use:
          current_recovery_use += self.recovery_use[x]
        demand_dict['supplemental'] = min(delivery - max(min(demand,delivery), 0.0), self.leiu_recovery - current_recovery_use - demand_dict['initial'])
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

  def give_paper_trade(self, trade_amount, contract_list, wateryear):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
	#trade, giving up a surface water contract allocation (contract_list) to the district
	#that owned the groundwater that was recovered
    if self.seepage*self.surface_water_sa > 0.0:
      trade_alloc = 0.0
      for y in contract_list:
        total_alloc += self.projected_supply[y.name]
      if total_alloc > 0.0:
        self.dailydemand -= trade_amount/self.seepage*self.surface_water_sa
        for y in contract_list:
          self.paper_balance[y.name] -= trade_delivery*self.projected_supply[y.name]/total_alloc
        self.deliveries['exchanged_SW'][wateryear] += trade_delivery
	  
  def get_paper_trade(self, trade_amount, contract_list, wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	#the paper credit is in exchange for delivering recovered groundwater to another party (district)
    total_alloc = 0.0
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
	
  def direct_recovery_delivery(self, delivery, wateryear):
    #this function takes a delivery of recoverd groundwater and applies it to irrigation demand in a district
	#the recovered groundwater is delivered to the district that originally owned the water, so no 'paper' trade is needed
    actual_delivery = min(delivery, self.dailydemand*self.seepage*self.surface_water_sa)
    self.deliveries['recover_banked'][wateryear] += delivery
    self.dailydemand -= actual_delivery/self.seepage*self.surface_water_sa
    return actual_delivery
	
  def adjust_accounts(self, actual_deliveries, contract_list, search_type, wateryear):
    #this function accepts water under a specific condition (flood, irrigation delivery, banking), and 
	#adjusts the proper accounting balances
    total_carryover_recharge = 0.0
    total_current_balance = 0.0
    delivery_by_contract = {}
    for y in contract_list:
      total_current_balance += max(self.current_balance[y.name], 0.0)
      delivery_by_contract[y.name] = 0.0
    for y in contract_list:
      #find the percentage of total deliveries that come from each contract
      if total_current_balance > 0.0:
        contract_deliveries = actual_deliveries*max(self.current_balance[y.name], 0.0)/total_current_balance
      else:
        contract_deliveries = 0.0
      delivery_by_contract[y.name] = contract_deliveries
      #flood deliveries do not count against a district's contract allocation, so the deliveries are recorded as 'flood'
      if search_type == "flood":
        self.deliveries[y.name + '_flood'][wateryear] += contract_deliveries
      else:
        #irrigation/banking deliveries are recorded under the contract name so they are included in the 
		#contract balance calculations
        #update the individual district accounts
        self.deliveries[y.name][wateryear] += contract_deliveries
        self.current_balance[y.name] -= contract_deliveries
        if search_type == 'banking':
          #if deliveries ar for banking, update banking accounts
          self.deliveries['recharged'][wateryear] += contract_deliveries
          self.recharge_carryover[y.name] -= min(contract_deliveries, self.recharge_carryover[y.name])
		
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


#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################RECORD STATE VARIABLES###############################################################
#####################################################################################################################

  def reset_recharge_recovery(self):
    self.max_direct_recharge = np.zeros(12)
    self.max_leiu_recharge = np.zeros(12)


  def accounting(self,t, da, m, wateryear,key):
    #takes delivery/allocation values and builds timeseries that show what water was used for (recharge, banking, irrigation etc...)
	#delivery/allocation data are set cumulatively - so that values will 'stack' in a area plot.
	#Allocations are positive (stack above the x-axis in a plot)
    self.daily_supplies['paper'][t] += self.projected_supply[key]
    self.daily_supplies['carryover'][t] += max(self.projected_supply[key] - self.paper_balance[key], 0.0)
    self.daily_supplies['allocation'][t] += max(self.projected_supply[key] - self.paper_balance[key] - self.carryover[key], 0.0)
    #while deliveries are negative (stack below the x-axis in a plot) - the stacking adjustments come in self.accounting_banking_activity()
    self.daily_supplies['delivery'][t] -= self.deliveries[key][wateryear]
    self.daily_supplies['recharge_uncontrolled'][t] -= self.deliveries[key + '_flood'][wateryear] 
	
    if m == 9 and da == 29:
      self.annual_supplies['delivery'][wateryear] += self.deliveries[key][wateryear]

	
  def accounting_banking_activity(self, t, da, m, wateryear):
    #this is an adjustment for 'delivery' (the delivery values are negative, so adding 'recharged' and 'exchanged_GW' is removing them from the count for 'deliveries' - we only want deliveries for irrigation, not for recharge
    #exchanged_GW is GW that has been pumped out of a bank and 'delivered' to another district. the district gets credit in the reservoir, and deliveries of SW from that reservoir are recorded as 'deliveries' - but we don't want to count that here
	#exchanged_SW is GW that has been pumped out of a bank, not owned by the district, and delivered to that district (i.e., the other side of the exchanged_GW in a GW exchange).  This should technically count as an irrigation delivery from a contract
	#(we want to record that as delivery here) but it doesn't get recorded that way upon delivery.  so we add it back here when were are recording accounts (i.e. exchanged_GW and exchanged_SW are counters to help us square the records from GW exchanges)
    self.daily_supplies['delivery'][t] += self.deliveries['recharged'][wateryear] + self.deliveries['exchanged_GW'][wateryear] - self.deliveries['exchanged_SW'][wateryear]
    #leiu accepted are irrigation deliveries that come from the in-leiu banking district's banking partners (i.e., they use it, and record a 'balance' for whoever delivered it)
    self.daily_supplies['leiu_accepted'][t] += self.daily_supplies['delivery'][t] - self.deliveries['inleiu'][wateryear]
      #banked is uncontrolled (or flood) water that has been banked by a district (in-district)
    self.daily_supplies['banked'][t] += self.daily_supplies['leiu_accepted'][t] + self.deliveries['exchanged_SW'][wateryear] - self.deliveries['exchanged_GW'][wateryear] - self.deliveries['recover_banked'][wateryear]
    ##pumping is private pumping for irrigation
    self.daily_supplies['pumping'][t] += self.daily_supplies['banked'][t] - self.annual_private_pumping
    ##leiu_delivered is water from an in-leiu banking district that gets delivered to (recovered by) their banking partners
    self.daily_supplies['leiu_delivered'][t] += self.daily_supplies['pumping'][t] - self.deliveries['leiupumping'][wateryear]
    #recharge delivery is water recharged at a bank that comes from the district's contract amount (instead of flood/uncontrolled water)
    self.daily_supplies['recharge_delivery'][t] += self.daily_supplies['leiu_delivered'][t] - self.deliveries['recharged'][wateryear]
	
	#recharge uncontrolled is recharge water from flood flows (flood flows added in self.accounting() - this is only adjustment for stacked plot)
    self.daily_supplies['recharge_uncontrolled'][t] += self.daily_supplies['recharge_delivery'][t] 

	
    if m == 9 and da == 29:		
      self.annual_supplies['delivery'][wateryear] += self.deliveries['exchanged_SW'][wateryear] - self.deliveries['recharged'][wateryear] - self.deliveries['exchanged_GW'][wateryear]
      self.annual_supplies['banked_accepted'][wateryear] = self.annual_supplies['delivery'][wateryear]  + self.deliveries['recover_banked'][wateryear] + self.deliveries['exchanged_GW'][wateryear] - self.deliveries['exchanged_SW'][wateryear]
      self.annual_supplies['leiu_accepted'][wateryear] = self.annual_supplies['banked_accepted'][wateryear] + self.deliveries['inleiu'][wateryear]
      self.annual_supplies['leiu_delivered'][wateryear] = self.annual_supplies['leiu_accepted'][wateryear] + self.deliveries['leiupumping'][wateryear]


  def accounting_leiubank(self,t, m, da, wateryear):
    #takes banked storage (in in-leiu banks) and builds timeseries of member accounts
    stacked_amount = 0.0
    self.recharge_rate_series[t] = self.recharge_rate
    for x in self.participant_list:
      self.bank_timeseries[x][t] = self.inleiubanked[x] + stacked_amount
      stacked_amount += self.inleiubanked[x]
    if m == 9 and da == 29:
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
	  