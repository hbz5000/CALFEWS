# cython: profile=True
import numpy as np 
import matplotlib.pyplot as plt
import collections as cl
import pandas as pd
import json
from .util import *
from .crop_cy cimport Crop
from .contract_cy cimport Contract
from .canal_cy cimport Canal


cdef class Private():

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
                       
  def __init__(self, model, name, key, land_fraction):
    self.is_Canal = 0
    self.is_District = 0
    self.is_Private = 1
    self.is_Waterbank = 0
    self.is_Reservoir = 0

    self.key = key
    self.name = name

    # self.turnback_use = 1
    self.T = model.T
    for k,v in json.load(open('calfews_src/private/%s_properties.json' % key)).items():
        setattr(self,k,v)
		
    self.district_list_len = len(self.district_list)
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
    self.non_contract_delivery_list = ['inleiu','leiupumping','exchanged_GW','exchanged_SW', 'recover_banked']

    for district in self.district_list:
      self.deliveries[district] = {}
      for x in self.contract_list_all:
        #normal contract deliveries
        self.deliveries[district][x] = np.zeros(model.number_years)
	      #uncontrolled deliveries from contract
        self.deliveries[district][x + '_flood'] = np.zeros(model.number_years)
        self.deliveries[district][x + '_flood_irrigation'] = np.zeros(model.number_years)
        self.deliveries[district][x + '_recharged'] = np.zeros(model.number_years)
      for x in self.non_contract_delivery_list:
	      #deliveries from a groundwater bank (reocrded by banking partner recieving recovery water)
        self.deliveries[district][x] = np.zeros(model.number_years)
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
    self.dynamic_recharge_cap ={}
    #initialize values for all contracts in dictionaries
    for z in self.district_list:
      self.current_balance[z] = {}
      self.turnback_pool[z] = {}
      self.projected_supply[z] = {}
      self.carryover[z] = {}
      self.recharge_carryover[z] = {}
      self.delivery_carryover[z] = {}
      self.contract_carryover_list[z] = {}
      self.dynamic_recharge_cap[z] ={}
      self.paper_balance[z] = {}
      for y in self.contract_list_all:
        self.current_balance[z][y] = 0.0
        self.paper_balance[z][y] = 0.0
        self.turnback_pool[z][y] = 0.0
        self.projected_supply[z][y] = 0.0
        self.carryover[z][y] = 0.0
        self.recharge_carryover[z][y] = 0.0
        self.delivery_carryover[z][y] = 0.0
        self.contract_carryover_list[z][y] = 0.0
        self.dynamic_recharge_cap[z][y] = 0.0
	  
    # hold all output
    self.daily_supplies_full = {}
    self.demand_days = {}
    self.demand_days['current'] = {}
    self.demand_days['lookahead'] = {}

    # delivery_list = ['tableA', 'cvpdelta', 'exchange', 'cvc', 'friant1', 'friant2','kaweah', 'tule', 'kern']
    for z in self.district_list:
      for x in self.contract_list_all:
        # self.daily_supplies_full[z + '_' + x + '_delivery'] = np.zeros(model.T)
        # self.daily_supplies_full[z + '_' + x + '_flood'] = np.zeros(model.T)
        # self.daily_supplies_full[z + '_' + x + '_projected'] = np.zeros(model.T)
        # self.daily_supplies_full[z + '_' + x + '_paper'] = np.zeros(model.T)
        # self.daily_supplies_full[z + '_' + x + '_carryover'] = np.zeros(model.T)
        # self.daily_supplies_full[z + '_' + x + '_turnback'] = np.zeros(model.T)
        # self.daily_supplies_full[z + '_' + x + '_recharged'] = np.zeros(model.T)
        # self.daily_supplies_full[z + '_' + x + '_dynamic_recharge_cap'] = np.zeros(model.T)
        self.demand_days['current'][x] = 0.0
        self.demand_days['lookahead'][x] = 0.0

      # for x in self.non_contract_delivery_list:
      #   self.daily_supplies_full[z + '_' + x] = np.zeros(model.T)
      # self.daily_supplies_full[z + '_irr_demand'] = np.zeros(model.T)
      # self.daily_supplies_full[z + '_tot_demand'] = np.zeros(model.T)
      # self.daily_supplies_full[z + '_pumping'] = np.zeros(model.T)
      # self.daily_supplies_full[z + '_dynamic_recovery_cap'] = np.zeros(model.T)

    # ['recover_banked', 'inleiu', 'leiupumping', 'recharged', 'exchanged_GW', 'exchanged_SW', 'undelivered_trades']
    #Initialize demands
    self.annualdemand = {}
    self.dailydemand = {}
    self.dailydemand_start = {}
    self.per_acre = {}
    self.total_acreage = 0.0
    self.unmet_et = {}
    self.annual_private_pumping = {}
    self.last_days_demand_regression_error = {}
    for x in self.district_list:
      self.per_acre[x] = {}
      self.annual_private_pumping[x] = 0.0
      self.unmet_et[x] = np.zeros(model.number_years)
      self.unmet_et[x + "_total"] = np.zeros(model.number_years)
      self.dailydemand_start[x] = 0.0
      self.dailydemand[x] = 0.0
      self.last_days_demand_regression_error[x] = 0.0
      for v in self.crop_list:
        self.per_acre[x][v] = {}
        self.per_acre[x][v]['mature'] = 0.0
        self.per_acre[x][v]['immature'] = 0.0

    #recovery and pumping variables
    #self.recovery_fraction = 0.5
    # self.annual_pumping = 0.0
    self.use_recharge = 0.0
    self.use_recovery = 0.0
    self.extra_leiu_recovery = 0.0
    self.max_recovery = 0.0
    self.max_leiu_exchange = 0.0
    self.total_banked_storage = 0.0
    self.recovery_capacity_remain = 0.0
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
  def permanent_crop_growth(self, wateryear, days_in_month, non_leap_year):
    self.total_acreage = 0.0
    for x in self.district_list:
      irrigation = 0.0
      missing_demand = self.unmet_et[x][wateryear-1]
      for y in self.contract_list_all:
        irrigation += self.deliveries[x][y][wateryear-1]
      irrigation -= self.deliveries[x][y + '_recharged'][wateryear-1]
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
          if self.has_pesticide[x]:
            self.acreage[x][v][ageloop] = self.initial_planting[x][v][wateryear]
          else:
            self.acreage[x][v][ageloop] = self.acreage[x][v][ageloop-1]*percent_filled[v][ageloop-1]
          self.total_acreage += self.acreage[x][v][ageloop]
        if self.has_pesticide[x]:
          self.acreage[x][v][0] = self.initial_planting[x][v][wateryear]
        else:
          self.acreage[x][v][0] = self.initial_planting[x][v]

        self.total_acreage += self.acreage[x][v][0]
    for x in self.district_list:
      self.per_acre[x] = {}
      for v in self.crop_list:
        self.per_acre[x][v] = {}
        self.per_acre[x][v]['mature'] = 0.0
        self.per_acre[x][v]['immature'] = 0.0

		
    self.find_baseline_demands(non_leap_year, days_in_month)
		
  def find_baseline_demands(self, non_leap_year, days_in_month):
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
            annualET += max(district_et.etM[v][wyt][monthloop],0.0)/(12.0)
            annualETimm += max(district_et.etM[v + '_immature'][wyt][monthloop],0.0)/(12.0)
            #annualET += max(district_et.etM[v][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)/(12.0)
            #annualETimm += max(district_et.etM[v + '_immature'][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)/(12.0)
          for ageloop in range(0,25):
            if ageloop < self.crop_maturity[v]:
              self.agedemand[district][wyt][ageloop] += self.acreage[district][v][ageloop]*annualET*self.seepage[district]
            else:
              self.agedemand[district][wyt][ageloop] += self.acreage[district][v][ageloop]*annualETimm
        for monthloop in range(0,12):
          self.monthlydemand[district][wyt][monthloop] += self.urban_profile[district][monthloop]*self.MDD[district]/days_in_month[non_leap_year][monthloop]
          for i,v in enumerate(self.crop_list):
            age_length = len(self.acreage[district][v])
            acres_mature = np.sum(self.acreage[district][v][self.crop_maturity[v]:age_length])
            acres_immature = np.sum(self.acreage[district][v][0:self.crop_maturity[v]])
            district_et = self.irrdemand[district]
            self.monthlydemand[district][wyt][monthloop] += max(district_et.etM[v][wyt][monthloop],0.0)*acres_mature/(12.0*days_in_month[non_leap_year][monthloop])
            self.monthlydemand[district][wyt][monthloop] += max(district_et.etM[v + '_immature'][wyt][monthloop],0.0)*acres_immature/(12.0*days_in_month[non_leap_year][monthloop])
            #self.monthlydemand[district][wyt][monthloop] += max(district_et.etM[v][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)*acres_mature/(12.0*days_in_month[non_leap_year][monthloop])
            #self.monthlydemand[district][wyt][monthloop] += max(district_et.etM[v + '_immature'][wyt][monthloop] - district_et.etM['precip'][wyt][monthloop],0.0)*acres_immature/(12.0*days_in_month[non_leap_year][monthloop])
    
  cdef void calc_demand(self, int wateryear, int year_index, int da, int m, list days_in_month, int non_leap_year, int m1, str wyt):
    #from the monthlydemand dictionary (calculated at the beginning of each wateryear based on ag acreage and urban demands), calculate the daily demand and the remaining annual demand
    cdef:
      int monthday, monthloop
      str x, v
      Crop crop_obj

    monthday = days_in_month[year_index][m-1]
    for x in self.district_list:
      self.dailydemand[x] = self.monthlydemand[x][wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[x][wyt][m1-1]*da/monthday
      if self.dailydemand[x] < 0.0:
        self.dailydemand[x] = 0.0
    for x in self.district_list:
      crop_obj = self.irrdemand[x]
      for v in self.crop_list:
        self.per_acre[x][v]['mature'] += (max(crop_obj.etM[v][wyt][m-1],0.0)*((monthday-da)/monthday) + max(crop_obj.etM[v][wyt][m1-1],0.0)*(da/monthday))/(12.0*days_in_month[non_leap_year][m-1]) 
        self.per_acre[x][v]['immature'] += (max(crop_obj.etM[v + '_immature'][wyt][m-1],0.0)*((monthday-da)/monthday) + max(crop_obj.etM[v][wyt][m1-1],0.0)*(da/monthday))/(12.0*days_in_month[non_leap_year][m-1]) 
        
      #calculate that days 'starting' demand (b/c demand is filled @multiple times, and if we only want to fill a certain fraction of that demand (based on projections of supply & demand for the rest of the year), we want to base that fraction on that day's total demand, not the demand left after other deliveries are made
      self.dailydemand_start[x] = self.monthlydemand[x][wyt][m-1]*(monthday-da)/monthday + self.monthlydemand[x][wyt][m1-1]*da/monthday
      if self.dailydemand_start[x] < 0.0:
        self.dailydemand_start[x] = 0.0

	    #pro-rate this month's demand based on the day of the month when calculating remaining annual demand
      self.annualdemand[x] = max(self.monthlydemand[x][wyt][m-1]*(monthday-da), 0.0)
      if m > 9:
        for monthloop in range(m, 12):
          self.annualdemand[x] += max(self.monthlydemand[x][wyt][monthloop]*days_in_month[year_index][monthloop],0.0)
        for monthloop in range(0,9):
          self.annualdemand[x] += max(self.monthlydemand[x][wyt][monthloop]*days_in_month[year_index+1][monthloop], 0.0)
      else:
        for monthloop in range(m, 9):
          self.annualdemand[x] += max(self.monthlydemand[x][wyt][monthloop]*days_in_month[year_index][monthloop], 0.0)



  cdef void get_urban_demand(self, int t, int m, int da, int wateryear, int year_index, list dowy_eom, int dowy, double total_delta_pumping, double allocation_change, str model_mode):
    #this function finds demands for the 'branch pumping' urban nodes - Socal, South Bay, & Central Coast
	  #demand is equal to pumping of the main california aqueduct and into the branches that services these areas
    #cal aqueduct urban demand comes from pumping data, calc seperately
    cdef:
      double sri_estimate, sri_estimate_int
      int start_of_month, cross_counter_y, monthloop, monthcounter, start_next_month, random_component, sort_year
      str district, wyt, yy
      dict todays_demand_regression_error

    if model_mode == 'validation':
      ####Get daily demand from pumping observations, get annual demand estimate from mix between seasonal delta pumping-based regression and pumping observations
      for district in self.district_list:
        self.dailydemand[district] = self.pumping[district][t]/1000.0
        self.dailydemand_start[district] = self.pumping[district][t]/1000.0
        self.ytd_pumping[district][wateryear] += self.dailydemand[district]
        sri_estimate = (total_delta_pumping*self.delivery_percent_coefficient[district][dowy][0] + self.delivery_percent_coefficient[district][dowy][1])*total_delta_pumping
        self.annualdemand[district] = max(0.0, (self.annual_pumping[district][wateryear]*min(dowy, 240.0) + sri_estimate*(240.0 - min(240,dowy)))/240.0 - self.ytd_pumping[district][wateryear])
      ###Get monthly estimates from pumping observations
      if m == 10 and da == 1:
        self.monthlydemand = {}
        for district in self.district_list:
          self.monthlydemand[district] = {}
          for wyt in ['W', 'AN', 'BN', 'D', 'C']:
            self.monthlydemand[district][wyt] = np.zeros(12)	
        start_of_month = 0
        cross_counter_y = 0
        for monthloop in range(0,12):
          monthcounter = monthloop + 9
          if monthcounter > 11:
            monthcounter -= 12
            cross_counter_y = 1
          start_next_month = dowy_eom[year_index+cross_counter_y][monthcounter] + 1
          for wyt in ['W', 'AN', 'BN', 'D', 'C']:
            for district in self.district_list:
              self.monthlydemand[district][wyt][monthcounter] = np.mean(self.pumping[district][(t + start_of_month):(t + start_next_month)])/1000.0
          start_of_month = start_next_month

    else:
      ###If simulation (no observations), get daily, monthly, annual demands from seasonally adjusted delta pumping based estimates, with random errors
      todays_demand_regression_error = {}
      self.k_close_wateryear = {}
      for district in self.district_list:
        sri_estimate_int = total_delta_pumping*self.delivery_percent_coefficient[district][dowy][0] + self.delivery_percent_coefficient[district][dowy][1]
        if m == 10 and da == 1:
          self.last_days_demand_regression_error[district] = 0.0
          todays_demand_regression_error[district] = 0.0
          random_component = np.random.randint(0, len(self.demand_auto_errors[district][dowy]))
        else:
          random_component = np.random.randint(0, len(self.demand_auto_errors[district][dowy]))
          todays_demand_regression_error[district] = allocation_change * self.delivery_percent_coefficient[district][dowy][2] + self.delivery_percent_coefficient[district][dowy][3] + self.last_days_demand_regression_error[district] - self.demand_auto_errors[district][dowy][random_component]
          self.last_days_demand_regression_error[district] = todays_demand_regression_error[district] * 1.0
        sri_estimate = total_delta_pumping * (sri_estimate_int - todays_demand_regression_error[district])
        self.annualdemand[district] = max(sri_estimate - self.ytd_pumping[district][wateryear], 1.0)

        for sort_year in range(0, len(self.hist_demand_dict[district]['annual_sorted'][dowy])):
          if total_delta_pumping > self.hist_demand_dict[district]['annual_sorted'][dowy][sort_year]:
            break
        self.k_close_wateryear[district] = sort_year
        self.dailydemand[district] = self.annualdemand[district]*self.hist_demand_dict[district]['daily_fractions'][self.k_close_wateryear[district]][dowy]
        self.dailydemand_start[district] = self.annualdemand[district]*self.hist_demand_dict[district]['daily_fractions'][self.k_close_wateryear[district]][dowy]
      if da == 1:
        self.monthlydemand = {}
        for yy in self.district_list:
          self.monthlydemand[yy] = {}
          for wyt in ['W', 'AN', 'BN', 'D', 'C']:
            self.monthlydemand[yy][wyt] = np.zeros(12)

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
            for district in self.district_list:
              self.monthlydemand[district][wyt][monthcounter] += self.annualdemand[district]*np.mean(self.hist_demand_dict[district]['daily_fractions'][self.k_close_wateryear[district]][start_of_month:start_next_month])
          start_of_month = start_next_month
    
      for district in self.district_list:
        self.ytd_pumping[district][wateryear] += self.dailydemand[district]

				

  def find_unmet_et(self, district_name, wateryear, dowy):
    self.unmet_et[district_name][wateryear] += self.dailydemand[district_name]
    self.unmet_et[district_name + "_total"][wateryear] += self.dailydemand_start[district_name]

  def find_pre_flood_demand(self, year_index, days_in_month, wyt):
    #calculates an estimate for water use in the Oct-Dec period (for use in recharge_carryover calculations), happens Oct 1
    self.pre_flood_demand = self.monthlydemand[wyt][9]*days_in_month[year_index][9] + self.monthlydemand[wyt][10]*days_in_month[year_index][10] + self.monthlydemand[wyt][11]*days_in_month[year_index][11]
		  
		
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################PROJECT CONTRACTS#################################################################
#####################################################################################################################

  cdef (double, double) update_balance(self, int t, int wateryear, double water_available, double projected_allocation, double current_water, str key, double tot_carryover, str balance_type, str district_name, dict project_contract, dict rights):
		###This function takes input from the contract class (water_available, projected_allocation, tot_carryover) to determine how much of their allocation remains
    ##water_available is the current contract storage in the reservoir *plus* all deliveries from the given year.  The deliveries, paper trades, and turnback pool accounts for each district
    ##are used to get a running tally of the surface water that is currently available to them.  (tot_carryover is subtracted from the current balance - districts only get access to *their* 
    ##carryover storage - which is added to their individual current balance (self.carryover[key])
    ##projected_allocation is the water that is forecasted to be available on each contract through the end of the water year *plus* water that has already been delivered on that contract
    ##individual deliveries are then subtracted from this total to determine the individual district's projected contract allocation remaining in that year
    cdef:
      double district_storage, annual_allocation, storage_balance

    if balance_type == 'contract':
      #district_storage - district's water that is currently available (in storage at reservoir)
      #(water_available - tot_carryover)*self.project_contract[key] - individual district share of the existing (in storage) contract balance, this includes contract water that has already been delivered to all contractors
	  #self.deliveries[key][wateryear] - individual district deliveries (how much of 'their' contract has already been delivered)
	  #self.carryover[key] - individual district share of contract carryover
	  #paper_balance[key] - keeps track of 'paper' groundwater trades (negative means they have accepted GW deliveries in exchange for trading some of their water stored in reservoir, positive means they sent their banked GW to another district in exchage for SW storage
	  #turnback_pool[key] - how much water was bought/sold on the turnback pool(negative is sold, positive is bought)
      district_storage = (water_available-tot_carryover)*project_contract[key]*self.private_fraction[district_name][wateryear] - self.deliveries[district_name][key][wateryear] + self.paper_balance[district_name][key] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      #annual allocation - remaining (undelivered) district share of expected total contract allocation
	  #same as above, but projected_allocation*self.project_contract[key] - individual share of expected total contract allocation, this includes contract water that has already been delivered to all contractors
      annual_allocation = projected_allocation*project_contract[key]*self.private_fraction[district_name][wateryear] - self.deliveries[district_name][key][wateryear] + self.paper_balance[district_name][key] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      storage_balance = current_water*project_contract[key]*self.private_fraction[district_name][wateryear] + self.paper_balance[district_name][key] + max(self.carryover[district_name][key] + self.turnback_pool[district_name][key] - self.deliveries[district_name][key][wateryear], 0.0)

    elif balance_type == 'right':
      #same as above, but for contracts that are expressed as 'rights' instead of allocations
      district_storage = (water_available-tot_carryover)*rights[key]['capacity']*self.private_fraction[district_name][wateryear] - self.deliveries[district_name][key][wateryear] + self.paper_balance[district_name][key] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      annual_allocation = projected_allocation*rights[key]['capacity']*self.private_fraction[district_name][wateryear] - self.deliveries[district_name][key][wateryear] + self.paper_balance[district_name][key] + self.carryover[district_name][key] + self.turnback_pool[district_name][key]
      storage_balance = current_water*rights[key]['capacity']*self.private_fraction[district_name][wateryear] + self.paper_balance[district_name][key] + max(self.carryover[district_name][key] + self.turnback_pool[district_name][key] - self.deliveries[district_name][key][wateryear], 0.0)
    
    self.current_balance[district_name][key] = storage_balance
    self.projected_supply[district_name][key] = annual_allocation
    # if balance_type == 'contract':
    #   contract_amount = project_contract[key]
    # else:
    #   contract_amount = rights[key]['capacity']
  
    return max(self.projected_supply[district_name][key] - self.annualdemand[district_name], 0.0), max(self.carryover[district_name][key] - self.deliveries[district_name][key][wateryear], 0.0)
	


  def apply_paper_balance(self, key, wyt, wateryear):
    ytd_deliveries = {}
    remaining_projected = {}
    remaining_paper = self.paper_balance[key]
    ind_paper_balance = {}
    for x in self.district_list:
      ytd_deliveries[x] = self.deliveries[x][key][wateryear] - self.deliveries[x][key + '_recharged'][wateryear]
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
          ind_paper_balance[x] += remaining_paper/self.district_list_len
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
          self.projected_supply[xx][key] += (self.paper_balance[key] - total_used)/self.district_list_len
    else:
      for xx in self.district_list:
        if self.projected_supply[xx][key] > 0.0:
          total_used_int = min(total_used - self.paper_balance[key], self.projected_supply[xx][key])
          self.projected_supply[xx][key] -= total_used_int
          total_used += total_used_int
      if self.paper_balance[key]*(-1.0) < total_used:
        for xx in self.district_list:
          self.projected_supply[xx][key] += (self.paper_balance[key] + total_used)/self.district_list_len
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
        
      

  cdef (double, double) calc_carryover(self, double existing_balance, int wateryear, str balance_type, str key, str district_name, dict project_contract, dict rights):
    #at the end of each wateryear, we tally up the full allocation to the contract, how much was used (and moved around in other balances - carryover, 'paper balance' and turnback_pools) to figure out how much each district can 'carryover' to the next year
    cdef:
      double annual_allocation, max_carryover, reallocated_water, carryover

    if balance_type == 'contract':
      annual_allocation = existing_balance*project_contract[key]*self.private_fraction[district_name][wateryear] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.paper_balance[district_name][key] + self.turnback_pool[district_name][key]
      max_carryover = self.contract_carryover_list[district_name][key]
    elif balance_type == 'right':
      annual_allocation = existing_balance*rights[key]['capacity']*self.private_fraction[district_name][wateryear] - self.deliveries[district_name][key][wateryear] + self.carryover[district_name][key] + self.paper_balance[district_name][key] + self.turnback_pool[district_name][key]
      max_carryover = self.contract_carryover_list[district_name][key]
	  
    reallocated_water = max(annual_allocation - max_carryover, 0.0)
    carryover = min(max_carryover, annual_allocation)
    self.carryover[district_name][key] = carryover
    self.turnback_pool[district_name][key] = 0.0	
    self.paper_balance[district_name][key] = 0.0
	
    return reallocated_water, carryover
		
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################RECHARGE/RECOVERY TRIGGERS#########################################################
#####################################################################################################################
	
  cdef void open_recovery(self, int t, int dowy, int wateryear, int number_years, str wyt, int use_delivery_tolerance, double additional_carryover):
    #this function determines if a district wants to recover banked water based on their demands and existing supplies
    cdef:
      double delivery_tolerance, total_balance, total_deliveries, total_needs, total_remaining_carryover, total_recovery
      int risk_index, x
      str district_key, contract_key

    if use_delivery_tolerance == 1:
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
      self.target_annual_demand = [999999.9 for _ in range(number_years)]
      #for district in self.district_list:
        #self.target_annual_demand += self.annual_pumping[district][wateryear]
    total_balance = 0.0
    total_deliveries = 0.0
    total_needs = 0.0
    for district_key in self.district_list:
      total_remaining_carryover = 0.0
      for contract_key in self.contract_list:
        total_balance += self.projected_supply[district_key][contract_key]
        total_deliveries += self.deliveries[district_key][contract_key][wateryear]
        total_remaining_carryover += max(self.carryover[district_key][contract_key] - self.deliveries[district_key][contract_key][wateryear], 0.0)
      total_deliveries += self.deliveries[district_key]['recover_banked'][wateryear]
      if total_remaining_carryover < 0.1:
        total_needs += self.annualdemand[district_key]*self.seepage[district_key]*self.recovery_fraction
    #total_recovery = (366-dowy)*self.max_recovery + self.max_leiu_exchange
    total_recovery = (366-dowy)*self.max_recovery + self.max_leiu_exchange
    self.recovery_capacity_remain = total_recovery
    total_needs += additional_carryover

    if (total_balance + total_recovery) < total_needs and (total_balance + total_deliveries) < (self.target_annual_demand[wateryear] - delivery_tolerance):
      if total_needs > 0.0:
        self.use_recovery = min(max(total_recovery/total_needs, 0.0), 1.0)
      else:
        self.use_recovery = 0.0
    else:
      self.use_recovery = 0.0
	
      	  

  cdef void open_recharge(self, int t, int m, int da, int wateryear, int year_index, list days_in_month, double numdays_fillup, double numdays_fillup2, str key, str wyt, list reachable_turnouts, double additional_carryover, int contract_allocation):
    #for a given contract owned by the district (key), how much recharge can they expect to be able to use
    #before the reservoir associated w/ that contract fills to the point where it needs to begin spilling water
    #(numdays_fillup) - i.e., how much surface water storage can we keep before start losing it
    #self.recharge_carryover is the district variable that shows how much 'excess' allocation there is on a particular
    #contract - i.e., how much of the allocation will not be able to be recharged before the reservoir spills
    cdef:
      double total_recharge, total_recharge2, carryover_storage_proj, spill_release_carryover, days_left, days_left2, \
              this_month_recharge, this_month_recharge2, total_available_for_recharge, available_recharge, total_secondary_contract
      int is_reachable, monthcounter, monthcounter_loop, next_year_counter
      str x, y, turnout, xx
      dict service_area_adjust, adjusted_sw_sa, district_fracs

    total_recharge = 0.0
    total_recharge2 = 0.0
    carryover_storage_proj = 0.0
    spill_release_carryover = 0.0
    total_available_for_recharge = 0.0
    service_area_adjust = {}

    for x in self.district_list:
      is_reachable = 0
      self.dynamic_recharge_cap[x][key] = 999.0
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
      for xx in self.district_list:
        for y in self.contract_list:
          spill_release_carryover += max(self.projected_supply[xx][y] - self.annualdemand[xx]*service_area_adjust[xx] - max(self.carryover_rights[xx][y], additional_carryover), 0.0)

      spill_release_carryover -= (total_recharge2  + self.demand_days['lookahead'][key])
      spill_release_carryover = max(spill_release_carryover, 0.0)

      carryover_storage_proj = 0.0
      for xx in self.district_list:
        for y in self.contract_list:
          carryover_storage_proj += max(self.carryover[xx][y] - self.deliveries[xx][y][wateryear] - self.carryover_rights[xx][y], 0.0)
      carryover_storage_proj -= (total_recharge + self.demand_days['current'][key])
      carryover_storage_proj = max(carryover_storage_proj, 0.0)

      district_fracs = {}
      if spill_release_carryover > carryover_storage_proj:
        total_available_for_recharge = 0.0
        for xx in self.district_list:
          available_recharge = 0.0
          for y in self.contract_list:
            available_recharge += max(self.projected_supply[xx][y], 0.0)
          total_available_for_recharge += max(available_recharge - self.annualdemand[xx] - additional_carryover, 0.0)
          
        if total_available_for_recharge > 0.0:		  
          for xx in self.district_list:
            district_fracs[xx] = max(self.projected_supply[xx][key] - self.annualdemand[xx], 0.0)/total_available_for_recharge
            self.recharge_carryover[xx][key] = max(spill_release_carryover, 0.0)*district_fracs[xx]
            self.dynamic_recharge_cap[xx][key] = total_recharge2 * district_fracs[xx]
        else:
          for xx in self.district_list:
            self.recharge_carryover[key] = 0.0
            self.dynamic_recharge_cap[xx][key] = total_recharge2 / self.district_list_len

      elif carryover_storage_proj > spill_release_carryover:
        total_available_for_recharge = 0.0
        for xx in self.district_list:
          for y in self.contract_list:
            total_available_for_recharge += max(self.carryover[xx][y] - self.deliveries[xx][y][wateryear], 0.0)
        if total_available_for_recharge > 0.0:		  
          for xx in self.district_list:
            district_fracs[xx] = max(self.carryover[xx][key] - self.deliveries[xx][key][wateryear], 0.0)/total_available_for_recharge
            self.recharge_carryover[xx][key] = max(carryover_storage_proj, 0.0)*district_fracs[xx]
            self.dynamic_recharge_cap[xx][key] = total_recharge * district_fracs[xx]            
        else:
          for xx in self.district_list:
            self.recharge_carryover[xx][key] = 0.0
            self.dynamic_recharge_cap[xx][key] = total_recharge  / self.district_list_len

      else:
        total_available_for_recharge = 0.0
        for xx in self.district_list:
          available_recharge = 0.0
          for y in self.contract_list:
            total_available_for_recharge += max(self.carryover[xx][y] - self.deliveries[xx][y][wateryear], 0.0)
            available_recharge += max(self.projected_supply[xx][y], 0.0)
          total_available_for_recharge += max(available_recharge - self.annualdemand[xx] - additional_carryover, 0.0)
        if total_available_for_recharge > 0.0:        
          for xx in self.district_list:
            district_fracs[xx] = (max(self.carryover[xx][key] - self.deliveries[xx][key][wateryear], 0.0) + max(self.projected_supply[xx][key] - self.annualdemand[xx], 0.0))/total_available_for_recharge        
            self.recharge_carryover[xx][key] = 0.0
            self.dynamic_recharge_cap[xx][key] = min(total_recharge, total_recharge2) * district_fracs[xx]
        else:
            self.recharge_carryover[xx][key] = 0.0
            self.dynamic_recharge_cap[xx][key] = min(total_recharge, total_recharge2) / self.district_list_len
          
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
    
      
  cdef double get_urban_recovery_target(self, int t, int dowy, int wateryear, str wyt, dict pumping, double project_contract, int demand_days, int start_month, str district_key):
    cdef:
      double max_pumping_shortfall, pumping_shortfall
      int monthcounter, daycounter, tot_days

    max_pumping_shortfall = 0.0
    pumping_shortfall = 0.0
    monthcounter = start_month
    daycounter = 0
    tot_days = 0
    if demand_days > 365:
      max_pumping_shortfall = 999.9
    else:
      while tot_days < demand_days:
        pumping_shortfall += np.sum(self.pumping[district_key][(t-dowy+tot_days):(t-dowy+tot_days+min(demand_days - tot_days, 30))]/1000.0) - pumping['swp']['gains'][monthcounter]*project_contract*self.private_fraction[district_key][wateryear]
        tot_days += 30
        monthcounter += 1
        if monthcounter == 12:
          monthcounter = 0

        max_pumping_shortfall = max(pumping_shortfall, max_pumping_shortfall)	  

    return max(max_pumping_shortfall, 0.0)
	

  cdef tuple set_turnback_pool(self, str key, int year_index, list days_in_month, double additional_carryover):
    ##This function creates the 'turnback pool' (note: only for SWP contracts now, can be used for others)
    ##finding contractors with 'extra' contract water that they would like to sell, and contractors who would
    ##like to purchase that water.  
    cdef:
      double total_recharge_ability, total_projected_supply, contract_fraction
      int month_count
      str contract_key, district_key

    total_recharge_ability = 0.0
    total_projected_supply = 0.0
    for contract_key in self.contract_list:
      for district_key in self.district_list:
        total_projected_supply += self.projected_supply[district_key][contract_key]
    for month_count in range(0, 6):
      # total recharge Jun,Jul,Aug,Sep
      total_recharge_ability += self.max_direct_recharge[month_count]*days_in_month[year_index][month_count +3] + self.max_leiu_recharge[month_count]*days_in_month[year_index][month_count +3]
    
    contract_fraction = 0.0
    if total_projected_supply > 0.0:
      for district_key in self.district_list:
        contract_fraction += max(min(self.projected_supply[district_key][key]/total_projected_supply, 1.0), 0.0)
    else:
      contract_fraction = 0.0
	  
    #districts sell water if their projected contracts are greater than their remaining annual demand, plus their remaining recharge capacity in this water year, plus their recharge capacity in the next water year (through January)
    self.turnback_sales = {}
    self.turnback_purchases = {}

    for district_key in self.district_list:
      self.turnback_sales[district_key] = 0.0
      self.turnback_purchases[district_key] = 0.0
      self.turnback_sales[district_key] += max(self.projected_supply[district_key][key] - (self.annualdemand[district_key] + total_recharge_ability + additional_carryover)*contract_fraction, 0.0)
      self.turnback_purchases[district_key] += max(self.annualdemand[district_key]*contract_fraction - self.projected_supply[district_key][key] - self.max_recovery*122*contract_fraction, 0.0)

    return self.turnback_sales, self.turnback_purchases	  
      


  cdef void make_turnback_purchases(self, double turnback_sellers, double turnback_buyers, str key):
    #once we know how much water is in the 'selling' pool and the 'buying' pool, we can determine the total turnback pool - min(buying,selling), then
    #determine what % of each request is filled (i.e., if the selling pool is only 1/2 of the buying pool, then buyers only get 1/2 of their request, or visa versa	
    cdef:
      double sellers_frac, buyers_frac, total_projected_supply
      str district_key
      
    #once we know how much water is in the 'selling' pool and the 'buying' pool, we can determine the total turnback pool - min(buying,selling), then
    #determine what % of each request is filled (i.e., if the selling pool is only 1/2 of the buying pool, then buyers only get 1/2 of their request, or visa versa	
    if min(turnback_sellers, turnback_buyers) > 0.0:
      sellers_frac = -1*min(turnback_sellers, turnback_buyers)/turnback_sellers
      buyers_frac = min(turnback_sellers, turnback_buyers)/turnback_buyers
      for district_key in self.district_list:
        if self.turnback_sales[district_key] > 0.0:
          self.turnback_pool[district_key][key] = max(self.turnback_sales[district_key], 0.0)*sellers_frac
        elif self.turnback_purchases[district_key] > 0.0:
          self.turnback_pool[district_key][key] = max(self.turnback_purchases[district_key], 0.0)*buyers_frac

#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################DETERMINE DELIVERIES ON CANAL######################################################
#####################################################################################################################

			
  cdef double find_node_demand(self, list contract_list, str search_type, str district_name):
    #this function is used to calculate the current demand at each 'district' node
    cdef:
      Contract contract_obj
      double demand_constraint, total_projected_allocation, access_mult, total_demand_met, annualdemand, dailydemand_start, dailydemand
      str contract_key
    
    access_mult = self.seepage[district_name]#this accounts for water seepage & the total district area that can be reached by SW canals (seepage is >= 1.0; surface_water_sa <= 1.0)
    total_projected_allocation = 0.0
    for contract_obj in contract_list:
      total_projected_allocation += max(self.projected_supply[district_name][contract_obj.name], 0.0)#projected allocation

    #percentage of demand filled in the day is equal to the total projected allocation as a percent of annual demand
	  #(i.e., if allocations are projected to be 1/2 of annual demand, then they try to fill 50% of daily irrigation demands with surface water
    total_demand_met = 1.0
    #self.dailydemand_start is the initial daily district demand (self.dailydemand is updated as deliveries are made) - we try to fill the total_demand_met fraction of dailydemand_start, or what remains of demand in self.dailydemand, whichever is smaller
    dailydemand_start = self.dailydemand_start[district_name]
    dailydemand = self.dailydemand[district_name]
    if search_type == 'flood':
      annualdemand = self.annualdemand[district_name]
      if annualdemand > 0.0 and total_projected_allocation > 0.0:
        demand_constraint = (1.0 - min(total_projected_allocation/annualdemand, 1.0))*max(min(dailydemand_start*access_mult*total_demand_met, dailydemand*access_mult),0.0)	  
      else:
        demand_constraint = max(min(dailydemand_start*access_mult*total_demand_met, dailydemand*access_mult),0.0)

    else:
      demand_constraint = max(min(dailydemand_start*access_mult*total_demand_met, dailydemand*access_mult),0.0)
      #if we want to include recharge demands in the demand calculations, add available recharge space
			  
    return demand_constraint     
	
  

  cdef double set_request_to_district(self, double demand, str search_type, list contract_list, str district_name):
    #this function is used to determine if a district node 'wants' to make a request
	  #under the different usage types (flood, delievery, banking, or recovery) under a given contract (contract_list)
    cdef:
      double total_current_balance, total_projected_supply
      str contract_key 
      Contract contract_obj

    self.projected_supply[district_name]['tot'] = 0.0
    for contract_key in self.current_balance[district_name]:
      self.projected_supply[district_name]['tot'] += self.projected_supply[district_name][contract_key]
    #for flood deliveries, a district requests water if they don't have
    #excess contract water that they don't think they can recharge (i.e. they don't purchase
    #flood water if they can't use all their contract water
    if search_type == "flood":
      return demand

    #for normal irrigation deliveries, a district requests water if they have enough water currently
	#in surface water storage under the given contract
    if search_type == "delivery":
      total_current_balance = 0.0
      total_projected_supply = 0.0
      for contract_obj in contract_list:
        total_current_balance += max(self.current_balance[district_name][contract_obj.name], 0.0)
        total_projected_supply += max(self.projected_supply[district_name][contract_obj.name], 0.0)
      if self.seasonal_connection[district_name] == 1:
        return min(total_current_balance, total_projected_supply)
      else:
        return 0.0
    else:
      return 0.0
		


  cdef double set_request_constraints(self, double demand, str search_type, list contract_list, double bank_space, double bank_capacity, int dowy, int wateryear):		
    cdef:
      double total_carryover_recharge, total_current_balance, total_request
      int member_trades
      str district_key, member_contract_key
      Contract contract_obj, exchange_contract_obj

    #for banking, a district requests water if they have enough contract water currently in surface water storage and they have 'excess' water for banking (calculated in self.open_recharge)
    if search_type == "banking":
      total_carryover_recharge = 0.0
      total_current_balance = 0.0
      for district_key in self.district_list:
        for contract_obj in contract_list:
          total_carryover_recharge += max(self.recharge_carryover[district_key][contract_obj.name], 0.0)
          total_current_balance += max(self.current_balance[district_key][contract_obj.name], 0.0)
      return min(total_carryover_recharge, total_current_balance, max(bank_capacity - bank_space, 0.0))
	  
    #for recovery, a district requests recovery water from a bank if they have contracts under the current contract being searched (i.e., so they aren't requesting water that will be sent to another district that can't make 'paper' trades with them) and if they have their 'recovery threshold' triggered (self.use_recovery, calculated in self.open_recovery)
    elif search_type == "recovery":
      member_trades = 0
      for member_contract_key in self.contract_list:
        for exchange_contract_obj in contract_list:
          if member_contract_key == exchange_contract_obj.name:
            member_trades = 1
            break
        if member_trades == 1:
          break
      if member_trades == 1:
        if self.use_recovery > 0.0:
          for x in self.district_list:
            total_request = min(max(self.dailydemand[x]*self.seepage[x]*self.use_recovery, 0.0), max(bank_space, 0.0))
        else:
          total_request = 0.0
      else:
        total_request = 0.0
		
      return total_request
		
    elif search_type == "flood":
      return demand
		
    else:
      return 0.0
	  

  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal):
    #this function takes a the calculated demand at each district node and classifies those demands by 'priority' - the priority classes and rules change for each delivery type
    cdef:
      int contractor_toggle, priority_toggle
      dict demand_dict
      Canal canal_obj
      Contract contract_obj

    demand_dict = {}
    #for flood deliveries, the priority structure is based on if you have a contract with the reservoir that is being spilled, if you have a turnout on a canal that is a 'priority canal' for the spilling reservoir, and then finally if you are not on a priority canal for spilling
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
      for canal_obj in priority_list:#canals that have 'priority' from the given reservoir
        if canal_obj.name == contract_canal:#current canal
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


  cdef double find_leiu_priority_space(self, double demand_constraint, int num_members, str member_name, int toggle_recharge, str search_type):
    #this function finds how much 'priority' space in the recharge/recovery capacity is owned by a member (member_name) in a given in-leiu bank (i.e. this function is attached to the district that owns the bank - and the banking member is represented by 'member_name' input variable)
    cdef:
      double priority_space, available_banked, initial_capacity

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
          self.paper_balance[district][y.name] -= actual_delivery*self.projected_supply[district][y.name]/total_alloc
        self.deliveries[district]['exchanged_SW'][wateryear] += actual_delivery
    return actual_delivery
		


  def give_paper_exchange(self, trade_amount, contract_list, trade_frac, wateryear, district_name):
    #this function accepts a delivery of recovered groundwater, and makes a 'paper'
	  #trade, giving up a surface water contract allocation (contract_list) to the district
	  #that owned the groundwater that was recovered
    contract_counter = 0
    for y in contract_list:
      self.paper_balance[district_name][y.name] -= trade_amount*trade_frac[contract_counter]
      contract_counter += 1
    self.deliveries[district_name]['exchanged_SW'][wateryear] += trade_amount
	  


  cdef void get_paper_trade(self, double trade_amount, list contract_list, int wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	  #the paper credit is in exchange for delivering recovered groundwater to another party (district)
    cdef:
      double district_deficit, total_balance, total_needs, total_alloc, district_portion
      str district_key, contract_key
      Contract contract_obj

    district_deficit = 0.0
    for district_key in self.district_list:
      total_balance = 0.0
      total_needs = 0.0
      for contract_key in self.contract_list:
        total_balance += self.projected_supply[district_key][contract_key]
      total_needs += self.annualdemand[district_key]*self.seepage[district_key]*self.recovery_fraction
      district_deficit += max(total_needs - total_balance, 0.0)
      
    if district_deficit > 0.0:
      for district_key in self.district_list:
        total_balance = 0.0
        for contract_key in self.contract_list:
          total_balance += self.projected_supply[district_key][contract_key]
        district_portion = max(self.annualdemand[district_key]*self.seepage[district_key]*self.recovery_fraction - total_balance, 0.0) / district_deficit
        total_alloc = 0.0
        for contract_obj in contract_list:
          total_alloc += self.projected_supply[district_key][contract_obj.name]
        if total_alloc > 0.0:
          for contract_obj in contract_list:
            self.paper_balance[district_key][contract_obj.name] += trade_amount * district_portion * self.projected_supply[district_key][contract_obj.name] / total_alloc
        else:
            self.paper_balance[district_key][contract_obj.name] += trade_amount * district_portion / len(contract_list)
        self.deliveries[district_key]['exchanged_GW'][wateryear] += trade_amount * district_portion
    else:
      district_portion = 1.0 / self.district_list_len
      for district_key in self.district_list:
        total_alloc = 0.0
        for contract_obj in contract_list:
          total_alloc += self.projected_supply[district_key][contract_obj.name]
        if total_alloc > 0.0:
          for contract_obj in contract_list:
            self.paper_balance[district_key][contract_obj.name] += trade_amount * district_portion * self.projected_supply[district_key][contract_obj.name] / total_alloc
        else:
          for contract_obj in contract_list:
            self.paper_balance[district_key][contract_obj.name] += trade_amount * district_portion / len(contract_list)
 
        self.deliveries[district_key]['exchanged_GW'][wateryear] += trade_amount * district_portion
      


  cdef void get_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear):
    #this function takes a 'paper' credit on a contract and allocates it to a district
	  #the paper credit is in exchange for delivering recovered groundwater to another party (district)
    cdef:
      double district_deficit, total_balance, total_needs
      str contract_key, district_key

    district_deficit = 0.0
    for district_key in self.district_list:
      total_balance = 0.0
      total_needs = 0.0
      for contract_key in self.contract_list:
        total_balance += self.projected_supply[district_key][contract_key]
      total_needs += self.annualdemand[district_key]*self.seepage[district_key]*self.recovery_fraction
      district_deficit += max(total_needs - total_balance, 0.0)
      
    if district_deficit > 0.0:
      for district_key in self.district_list:
        total_balance = 0.0
        for contract_key in self.contract_list:
          total_balance += self.projected_supply[district_key][contract_key]
        district_portion = max(self.annualdemand[district_key]*self.seepage[district_key]*self.recovery_fraction - total_balance, 0.0) / district_deficit
        for contract_counter, contract_key in enumerate(contract_list):
          self.paper_balance[district_key][contract_key] += trade_amount * district_portion * trade_frac[contract_counter]
        self.deliveries[district_key]['exchanged_GW'][wateryear] += trade_amount * district_portion
    
    else:
      district_portion = 1.0 / self.district_list_len
      for district_key in self.district_list:
        for contract_counter, contract_key in enumerate(contract_list):
          self.paper_balance[district_key][contract_key] += trade_amount * district_portion * trade_frac[contract_counter] 
        self.deliveries[district_key]['exchanged_GW'][wateryear] += trade_amount * district_portion



  def record_direct_delivery(self, delivery, wateryear, district):
    actual_delivery = min(delivery, self.dailydemand[district]*self.seepage[district])

    self.deliveries[district]['recover_banked'][wateryear] += actual_delivery
    self.dailydemand[district] -= actual_delivery/(self.seepage[district])
    self.direct_recovery_delivery[district] = 0.0

    return actual_delivery



  cdef double direct_delivery_bank(self, double delivery, int wateryear, str district_key):
    #this function takes a delivery of recoverd groundwater and applies it to irrigation demand in a district
	#the recovered groundwater is delivered to the district that originally owned the water, so no 'paper' trade is needed
    cdef double direct_delivery, actual_delivery
    
    direct_delivery = self.dailydemand[district_key]*self.seepage[district_key] - self.direct_recovery_delivery[district_key]
    actual_delivery = min(delivery, direct_delivery)
    self.direct_recovery_delivery[district_key] += actual_delivery
    #self.deliveries[district_key]['recover_banked'][wateryear] += actual_delivery
    #self.dailydemand[district_key] -= actual_delivery/self.seepage[district_key]*self.surface_water_sa[district_key]
    return actual_delivery
	


  cdef dict adjust_accounts(self, double direct_deliveries, double recharge_deliveries, list contract_list, str search_type, int wateryear, str delivery_location):
    #this function accepts water under a specific condition (flood, irrigation delivery, banking), and 
  	#adjusts the proper accounting balances
    cdef:
      double total_current_balance, contract_deliveries
      int flood_counter
      dict delivery_by_contract
      str contract_key, district_key
      Contract contract_obj

    total_current_balance = 0.0
 
    delivery_by_contract = {}
    for contract_obj in contract_list:
      for district_key in self.district_list:
        if search_type == 'delivery' or search_type == 'recovery':
          total_current_balance += max(self.current_balance[district_key][contract_obj.name], 0.0)
        elif search_type == 'banking':
          total_current_balance += max(self.recharge_carryover[district_key][contract_obj.name], 0.0)
      delivery_by_contract[contract_obj.name] = 0.0
    
    flood_counter = 0
    for contract_obj in contract_list:
      contract_key = contract_obj.name
      #find the percentage of total deliveries that come from each contract
      contract_deliveries = 0.0
      if search_type == 'flood':
          if flood_counter == 0:
            contract_deliveries = (direct_deliveries + recharge_deliveries)
            flood_counter = 1
          else:
            contract_deliveries = 0.0
      elif total_current_balance > 0.0:
        for district_key in self.district_list:
          if search_type == 'delivery':
            contract_deliveries += (direct_deliveries + recharge_deliveries)*max(self.current_balance[district_key][contract_key], 0.0)/total_current_balance
          elif search_type == 'banking':
            contract_deliveries += (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[district_key][contract_key], 0.0)/total_current_balance
          elif search_type == 'recovery':
            contract_deliveries += (direct_deliveries + recharge_deliveries)*max(self.current_balance[district_key][contract_key], 0.0)/total_current_balance
      else:
        contract_deliveries = 0.0
      
      delivery_by_contract[contract_key] = contract_deliveries
      #flood deliveries do not count against a district's contract allocation, so the deliveries are recorded as 'flood'
      if search_type == "flood":
        for district_key in self.district_list:
          if contract_deliveries > 0.0:
            self.deliveries[district_key][contract_key + '_flood'][wateryear] += recharge_deliveries/self.district_list_len
            self.deliveries[district_key][delivery_location + '_recharged'][wateryear] += recharge_deliveries/self.district_list_len
            self.deliveries[district_key][contract_key + '_flood_irrigation'][wateryear] += direct_deliveries/self.district_list_len
      else:
        #irrigation/banking deliveries are recorded under the contract name so they are included in the 
		#contract balance calculations
        #update the individual district accounts
        if search_type == 'banking':
          for x in self.district_list:
            if total_current_balance > 0.0:
              self.deliveries[x][contract_key][wateryear] += (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][contract_key], 0.0)/total_current_balance
              self.current_balance[x][contract_key] -= (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][contract_key], 0.0)/total_current_balance
              self.deliveries[x][contract_key + '_recharged'][wateryear] += (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][contract_key], 0.0)/total_current_balance
              self.deliveries[x][delivery_location + '_recharged'][wateryear] += (direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][contract_key], 0.0)/total_current_balance
              self.recharge_carryover[x][contract_key] -= min((direct_deliveries + recharge_deliveries)*max(self.recharge_carryover[x][contract_key], 0.0)/total_current_balance, self.recharge_carryover[x][contract_key])
        else:
          for x in self.district_list:
            if total_current_balance > 0.0:
              self.deliveries[x][contract_key][wateryear] += (direct_deliveries + recharge_deliveries)*max(self.current_balance[x][contract_key], 0.0)/total_current_balance
              self.current_balance[x][contract_key] -= (direct_deliveries + recharge_deliveries)*max(self.current_balance[x][contract_key], 0.0)/total_current_balance
    return delivery_by_contract
	


  cdef dict adjust_account_district(self, double actual_deliveries, list contract_list, str search_type, int wateryear, str district_name, str delivery_location):
    cdef:
      double total_current_balance, contract_deliveries
      int flood_counter
      dict delivery_by_contract
      Contract contract_obj

    total_current_balance = 0.0
    delivery_by_contract = {}
    for contract_obj in contract_list:
      if search_type == 'flood':
        total_current_balance += 1.0
      elif search_type == 'delivery':
        total_current_balance += max(self.projected_supply[district_name][contract_obj.name], 0.0)
      elif search_type == 'banking':
        total_current_balance += max(self.recharge_carryover[district_name][contract_obj.name], 0.0)
      elif search_type == 'recovery':
        total_current_balance += max(self.current_balance[district_name][contract_obj.name], 0.0)
      delivery_by_contract[contract_obj.name] = 0.0
    flood_counter = 0
    for contract_obj in contract_list:
      #find the percentage of total deliveries that come from each contract
      if total_current_balance > 0.0:
        if search_type == 'flood':
          if flood_counter == 0:
            contract_deliveries = actual_deliveries
            flood_counter = 1
          else:
            contract_deliveries = 0.0
        elif search_type == 'delivery':
          contract_deliveries = actual_deliveries*max(self.projected_supply[district_name][contract_obj.name], 0.0)/total_current_balance
        elif search_type == 'banking':
          contract_deliveries = actual_deliveries*max(self.recharge_carryover[district_name][contract_obj.name], 0.0)/total_current_balance
        elif search_type == 'recovery':
          contract_deliveries = actual_deliveries*max(self.current_balance[district_name][contract_obj.name], 0.0)/total_current_balance
      else:
        contract_deliveries = 0.0

      delivery_by_contract[contract_obj.name] = contract_deliveries
      #flood deliveries do not count against a district's contract allocation, so the deliveries are recorded as 'flood'
      if search_type == "flood":
        self.deliveries[district_name][contract_obj.name + '_flood'][wateryear] += contract_deliveries
      else:
        #irrigation/banking deliveries are recorded under the contract name so they are included in the 
		#contract balance calculations
        #update the individual district accounts
        self.deliveries[district_name][contract_obj.name][wateryear] += contract_deliveries
        self.current_balance[district_name][contract_obj.name] -= contract_deliveries
        if search_type == 'banking':
          #if deliveries ar for banking, update banking accounts
          self.deliveries[district_name][contract_obj.name + '_recharged'][wateryear] += contract_deliveries
          self.deliveries[district_name][delivery_location + '_recharged'][wateryear] += contract_deliveries
          self.recharge_carryover[district_name][contract_obj.name] -= min(contract_deliveries, self.recharge_carryover[district_name][contract_obj.name])

    self.dailydemand[district_name] -= min(actual_deliveries/self.seepage[district_name],self.dailydemand[district_name])

    return delivery_by_contract

	

  def adjust_bank_accounts(self, member_name, deliveries, wateryear):
    #when deliveries are made for banking, keep track of the member's individual accounts
    self.bank_deliveries[member_name] += deliveries#keeps track of how much of the capacity is being used in the current timestep
    self.deliveries['inleiu'][wateryear] += deliveries#if deliveries being made 'inleiu', then count as inleiu deliveries
    self.inleiubanked[member_name] += deliveries * self.inleiuhaircut#this is the running account of the member's banking storage
	


  cdef void adjust_recovery(self, double deliveries, str member_name, int wateryear):
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

  cdef void reset_recharge_recovery(self):
    self.max_direct_recharge = [0. for _ in range(12)]
    self.max_leiu_recharge = [0. for _ in range(12)]
    self.total_banked_storage = 0.0
    self.max_leiu_exchange = 0.0


  cdef void set_daily_supplies_full(self, str key, double value, int t, int plusequals):
    ### only create timeseries for keys that actually ever triggered. plusequals = 0 if standalone value, =1 if we want to add to current value)
    if abs(value) > 1e-13:
      try:
        if plusequals == 1:
          self.daily_supplies_full[key][t] += value
        else:
          self.daily_supplies_full[key][t] = value

      except:
        self.daily_supplies_full[key] =  np.zeros(self.T)
        self.daily_supplies_full[key][t] = value


  cdef void accounting_full(self, int t, int wateryear):
    # keep track of all contract amounts
    cdef str x, district

    for x in self.contract_list_all:
      for district in self.district_list:
        self.set_daily_supplies_full(district + '_' + x + '_paper', self.paper_balance[district][x], t, 1)
        self.set_daily_supplies_full(district + '_' + x + '_delivery', self.deliveries[district][x][wateryear], t, 1)
        self.set_daily_supplies_full(district + '_' + x + '_flood', self.deliveries[district][x + '_flood'][wateryear] + self.deliveries[district][x + '_flood_irrigation'][wateryear], t, 1)
        self.set_daily_supplies_full(district + '_' + x + '_projected', self.projected_supply[district][x], t, 1)
        self.set_daily_supplies_full(district + '_' + x + '_carryover', self.carryover[district][x], t, 1)
        self.set_daily_supplies_full(district + '_' + x + '_turnback', self.turnback_pool[district][x], t, 1)
        self.set_daily_supplies_full(district + '_' + x + '_recharged', self.deliveries[district][x + '_recharged'][wateryear], t, 1)
        self.set_daily_supplies_full(district + '_' + x + '_dynamic_recharge_cap', self.dynamic_recharge_cap[district][x], t, 0)

    for district in self.district_list:
      for x in self.delivery_location_list[district]:
        self.set_daily_supplies_full(district + '_' + x + '_recharged', self.deliveries[district][x + '_recharged'][wateryear], t, 0)

    for x in self.non_contract_delivery_list:
      for district in self.district_list:
        self.set_daily_supplies_full(district + '_' + x, self.deliveries[district][x][wateryear], t, 0)

    for district in self.district_list:
      self.set_daily_supplies_full(district + '_irr_demand', self.dailydemand_start[district], t, 1)
      self.set_daily_supplies_full(district + '_tot_demand', self.annualdemand[district], t, 1)
      self.set_daily_supplies_full(district + '_pumping', self.annual_private_pumping[district], t, 1)
      self.set_daily_supplies_full(district + '_dynamic_recovery_cap', self.recovery_capacity_remain/self.district_list_len, t, 1)

