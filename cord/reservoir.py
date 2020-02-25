from __future__ import division
import numpy as np 
import calendar
import matplotlib.pyplot as plt
import pandas as pd
import json
from .util import *


class Reservoir():

  def __init__(self, df, df_short, name, key, model_mode):
    self.T = len(df)
    self.index = df.index
    self.day_year = self.index.dayofyear
    self.day_month = self.index.day
    self.year = self.index.year
    self.starting_year = int(self.year[0])
    self.ending_year = int(self.year[self.T-1])
    self.number_years = self.ending_year - self.starting_year
    self.month = self.index.month
    self.dowy = water_day(self.day_year, self.year)
    self.water_year = water_year(self.month, self.year, self.starting_year)

    self.leap = leap(np.arange(min(self.year), max(self.year)+2))
    year_list = np.arange(min(self.year), max(self.year)+2)
    self.days_in_month = days_in_month(year_list, self.leap)
    self.dowy_eom = dowy_eom(year_list, self.leap)
    self.non_leap_year = first_non_leap_year(self.dowy_eom)
    self.leap_year = first_leap_year(self.dowy_eom)
    self.first_d_of_month = first_d_of_month(self.dowy_eom, self.days_in_month)

    self.T_short = len(df_short)
    self.short_day_year = df_short.index.dayofyear
    self.short_day_month = df_short.index.day
    self.short_month = df_short.index.month
    self.short_year = df_short.index.year
    self.short_starting_year = self.short_year[0]
    self.short_ending_year = int(self.short_year[self.T_short-1])
    self.short_dowy = water_day(self.short_day_year, self.short_year)
    self.short_water_year = water_year(self.short_month, self.short_year, self.short_starting_year)
	
    self.short_leap = leap(np.arange(min(self.short_year), max(self.short_year)+2))
    short_year_list = np.arange(min(self.short_year), max(self.short_year)+2)
    self.short_days_in_month = days_in_month(short_year_list, self.short_leap)


    self.days_through_month = [60, 91, 122, 150, 181]
    self.hist_wyt = ['W', 'W', 'W', 'AN', 'D', 'D', 'AN', 'BN', 'AN', 'W', 'D', 'C', 'D', 'BN', 'W', 'BN', 'D', 'C', 'C', 'AN']

    self.key = key
    self.name = name
    self.forecastWYT = "AN"

	##Reservoir Parameters
    self.S = np.zeros(self.T)
    self.R = np.zeros(self.T)
    self.tocs = np.zeros(self.T)
    self.available_storage = np.zeros(self.T)
    self.flood_storage = np.zeros(self.T)
    self.Rtarget = np.zeros(self.T)
    self.R_to_delta = np.zeros(self.T)
    self.days_til_full = np.zeros(self.T)
    self.flood_spill = np.zeros(self.T)
    self.flood_deliveries = np.zeros(self.T)
    if self.key == "SLS":
      #San Luis - State portion
      #San Luis Reservoir is off-line so it doesn't need the full reservoir class parameter set contained in the KEY_properties.json files
      #self.Q = df['HRO_pump'] * cfs_tafd
      self.dead_pool = 40
      self.S[0] = 740.4
    elif self.key == "SLF":
      #San Luis - Federal portion
      #self.Q = df['TRP_pump'] * cfs_tafd
      self.dead_pool = 40
      self.S[0] = 174.4
    elif self.key != "SNL":
      #for remaining reservoirs, load parameters from KEY_properties.json file (see reservoir\readme.txt
      for k,v in json.load(open('cord/reservoir/%s_properties.json' % key)).items():
          setattr(self,k,v)
      #load timeseries inputs from cord-data.csv input file
      self.Q = df['%s_inf'% key].values * cfs_tafd
      self.E = df['%s_evap'% key].values * cfs_tafd
      ####Note - Shasta FCI values are not right - the original calculation units are in AF, but it should be in CFS
	  ####so the actual values are high.  Just recalculate here instead of changing input files
      if self.key == "SHA":
        self.fci = np.zeros(self.T)
        self.fci[0] = 100000
        for x in range(1, self.T):
          dowy = self.dowy[x]
          if dowy > 260:
            self.fci[x] = 0
          elif dowy == 0:
            self.fci[x] = 100000
          else:
            self.fci[x] = self.fci[x-1]*0.95 + self.Q[x]*tafd_cfs
      else:
        self.fci = df['%s_fci' % key].values
      self.SNPK = df['%s_snow' % key].values
      self.precip = df['%s_precip'% key].values * cfs_tafd
      self.downstream = df['%s_gains'% key].values * cfs_tafd
      self.fnf = df['%s_fnf'% key].values / 1000000.0
      self.R[0] = 0
      use_capacity = False
      storage_start_date = df.index[0]
      if storage_start_date in df_short.index: #keyvan
        storage_start_index = df_short.index.get_loc(storage_start_date)
      else:
        use_capacity = True
      if use_capacity:
        self.S[0] = self.capacity
        self.EOS_target = (self.capacity - 1000.0)/2 + 1000.0
        self.lastYearEOS_target = (self.capacity - 1000.0)/2 + 1000.0
      else:
        self.S[0] = df_short['%s_storage' % key].iloc[storage_start_index] / 1000.0
        self.EOS_target = df_short['%s_storage' % key].iloc[storage_start_index] / 1000.0
        self.lastYearEOS_target = df_short['%s_storage' % key].iloc[storage_start_index] / 1000.0
	  
    #Environmental release requirements
    #environmental rules are dependent on the water year type	
    if self.key == "YRS":
      self.wytlist = ['W', 'AN', 'BN', 'D', 'C', 'EC']
    else:
      self.wytlist = ['W', 'AN', 'BN', 'D', 'C']
    #dictionnaries containing expected remaining environmental releases from reservoir (as a function of day-of-the-wateryear)
    self.cum_min_release = {}
    self.oct_nov_min_release = {}
    self.aug_sept_min_release = {}
    for wyt in self.wytlist:
      self.cum_min_release[wyt] = np.zeros(366)
      self.oct_nov_min_release[wyt] = np.zeros(366)
      self.aug_sept_min_release[wyt] = np.zeros(366)
    self.exceedence_level = 9
    
	##Reservoir "decisions"
    self.din = 0.0
    self.dout = 0.0
    self.envmin = 0.0	
    self.sodd = 0.0
    self.basinuse = 0.0
    self.consumed_releases = 0.0
    
    self.sjrr_release = 0.0
    self.eos_day = 0
	##Vectors for flow projections
    self.rainfnf_stds = np.zeros(365)
    self.snowfnf_stds = np.zeros(365)
    self.raininf_stds = np.zeros(365)
    self.snowinf_stds = np.zeros(365)
    self.baseinf_stds = np.zeros(365)
    self.rainflood_fnf = np.zeros(self.T)
    self.snowflood_fnf = np.zeros(self.T)
    self.short_rainflood_fnf = np.zeros(self.T_short)
    self.short_snowflood_fnf = np.zeros(self.T_short)

    self.rainflood_inf = np.zeros(self.T)##linear projections (i.e. 50% exceedence)
    self.snowflood_inf = np.zeros(self.T)##linear projections (i.e. 50% exceedence)
    self.baseline_inf = np.zeros(self.T)
    self.rainflood_forecast = np.zeros(self.T)##projections w/ confindence (i.e. 90% exceedence - changes throughout year)
    self.snowflood_forecast = np.zeros(self.T)##projections w/ confindence (i.e. 90% exceedence - changes throughout year)
    self.baseline_forecast = np.zeros(self.T)##projections w/ confindence (i.e. 90% exceedence - changes throughout year)
    self.evap_forecast = 0.0
    self.max_direct_recharge = np.zeros(12)
    self.monthly_demand = {}
    self.monthly_demand_full = {}
    self.monthly_demand_must_fill = {}
    self.numdays_fillup = {}
    self.lastYearRainflood = 9999.9
    self.variable_min_flow = 0.0
    self.min_daily_overflow = 0.0


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


  def find_available_storage(self, t):
    ##this function uses the linear regression variables calculated in find_release_func (called before simulation loop) to figure out how
    ##much 'excess' storage is available to be released to the delta with the explicit intention of running the pumps.  This function is calculated
    ##each timestep before the reservoirs' individual step function is called
    m = self.month[t]
    da = self.day_month[t]
    dowy = self.dowy[t]
    wyt = self.forecastWYT

	###Find the target end of year storage, and the expected minimum releases, at the beginning of each water year
    if m == 10 and da == 1:
      self.rainflood_flows = 0.0##total observed flows in Oct-Mar, through the current day
      self.snowflood_flows = 0.0##total observed flows in Apr-Jul, through the current day
      self.baseline_flows = 0.0
	  
	  ##Exceedence level for flow forecasts (i.e. 2 is ~90%, 9 is ~50%)
	  ##If year starts in drought conditions, be conservative in Oct-Dec, otherwise, normal operations until January
      if self.key == "FOL" or self.key == "YRS":
        self.exceedence_level = 2
      else:
        if wyt == 'D' or wyt == 'C':
          self.exceedence_level = 2
        else:
          self.exceedence_level = 9

      ###Evap. projections are a perfect forecast (not much variation, didn't feel like making a seperate forecast for evap)
      self.evap_forecast = sum(self.E[(t):(t + 364)])
      self.eos_day = t
    if m == 8 and da == 1:
      self.lastYearEOS_target = self.EOS_target
      self.lastYearRainflood = self.rainflood_flows

	##Update the target EOS storage as the water year type forecasts change
    self.calc_EOS_storage(t,self.eos_day)###end-of-september target storage, based on the storage at the beginning of october
    ##Update the projected evaporation (its a perfect forecast)
    self.evap_forecast -= self.E[t]
    
	##Forecast exccedence levels set the percentile from which we forecast flows (i.e. 90% exceedence means 90% of years, with same snow conditions, would have higher flow)
	## excedence level 9 is 50% exceedence, level 1 is 90% exceedence.  Be more conservative with forecasts in drier years
    if m < 8:
      if self.key == "FOL" or self.key == "YRS":
        self.exceedence_level = min(m+2,7)
      else:
        if wyt == 'D' or wyt == 'C':
          self.exceedence_level = min(m+2,7)
        else:
          self.exceedence_level = 9
    elif m == 8 or m == 9:
      self.exceedence_level = 9
	  
    ##YTD observed flows (divided between rainflood and snowflood seasons) 
    if dowy < self.days_through_month[self.melt_start]:
      self.rainflood_flows += self.Q[t]##add to the total flow observations 
    elif dowy < 304:
      self.snowflood_flows += self.Q[t]##add to the total flow observations (
    else:
      self.baseline_flows += self.Q[t]
	###Rain- and snow-flood forecasts are predictions of future flows to come into the reservoir, for a given confidence interval (i.e. projections minus YTD observations)
    if dowy < self.days_through_month[self.melt_start]:
      ##Forecasts are adjusted for a given exceedence level (i.e. 90%, 50%, etc)
      #self.rainflood_forecast[t] = min(self.lastYearRainflood, self.rainflood_inf[t] + self.raininf_stds[dowy]*z_table_transform[self.exceedence_level]) - self.rainflood_flows
      self.rainflood_forecast[t] = min(self.lastYearRainflood, self.rainflood_inf[t] + self.raininf_stds[dowy]*z_table_transform[self.exceedence_level])

      self.snowflood_forecast[t] = (self.snowflood_inf[t] + self.snowinf_stds[dowy]*z_table_transform[self.exceedence_level])
      self.baseline_forecast[t] = self.baseline_inf[t] + self.baseinf_stds[dowy]*z_table_transform[self.exceedence_level]
      if self.rainflood_forecast[t] < 0.0:
        self.rainflood_forecast[t] = 0.0
      if self.snowflood_forecast[t] < 0.0:
        self.snowflood_forecast[t] = 0.0
      if self.baseline_forecast[t] < 0.0:
        self.baseline_forecast[t] = 0.0
    elif dowy < 304:
      self.rainflood_forecast[t] = 0.0##no oct-mar forecasts are made after march (already observed) 
      #self.snowflood_forecast[t] = (self.snowflood_inf[t] + self.snowinf_stds[dowy]*z_table_transform[self.exceedence_level]) - self.snowflood_flows
      self.snowflood_forecast[t] = (self.snowflood_inf[t] + self.snowinf_stds[dowy]*z_table_transform[self.exceedence_level])

      self.baseline_forecast[t] = self.baseline_inf[t] + self.baseinf_stds[dowy]*z_table_transform[self.exceedence_level]
      if self.snowflood_forecast[t] < 0.0:
        self.snowflood_forecast[t] = 0.0	
      if self.baseline_forecast[t] < 0.0:
        self.baseline_forecast[t] = 0.0	  
    else:
      self.rainflood_forecast[t] = 0.0
      self.snowflood_forecast[t] = 0.0
      #self.baseline_forecast[t] = self.baseline_inf[t] + self.baseinf_stds[dowy]*z_table_transform[self.exceedence_level] - self.baseline_flows
      self.baseline_forecast[t] = self.baseline_inf[t] + self.baseinf_stds[dowy]*z_table_transform[self.exceedence_level]
	
    #available storage is storage in reservoir in exceedence of end-of-september target plus forecast for oct-mar (adjusted for already observed flow)
	#plus forecast for apr-jul (adjusted for already observed flow) minus the flow expected to be released for environmental requirements (at the reservoir, not delta)
    self.available_storage[t] = self.S[t] - self.EOS_target + self.rainflood_forecast[t] + self.snowflood_forecast[t] + self.baseline_forecast[t] - self.cum_min_release[wyt][dowy] - self.evap_forecast - self.aug_sept_min_release[wyt][dowy]
     
    self.flood_storage[t] = self.S[t] - self.max_fcr + self.rainflood_forecast[t] - max(self.cum_min_release[wyt][dowy] - self.cum_min_release[wyt][181], 0.0)
    if dowy < 123:
      self.available_storage[t] = max(self.available_storage[t], (self.S[t] - self.lastYearEOS_target)*(123-dowy)/123 + self.available_storage[t]*dowy/123)
    if self.S[t] < self.EOS_target and dowy > 274:
      self.available_storage[t] = min(self.available_storage[t], 0.0)
      self.flood_storage[t] = min(self.flood_storage[t], 0.0)
	  
	  
  def use_saved_storage(self, t, m, wyt, dowy):
    swp_extra = 0.0
    if wyt == 'D' or wyt == 'C':
      if m >= 10 or m == 1:
        swp_extra = max(self.S[t] - self.carryover_target[wyt] - self.dry_year_carryover[wyt] - self.oct_nov_min_release[wyt][dowy], 0.0)
      #else:
        #swp_extra = max(min(self.available_storage[t], 0.0) + max(self.saved_water - self.dry_year_carryover[wyt], 0.0), 0.0)
    else:
      if m >= 10 or m == 1:
        swp_extra = max(self.S[t] - self.lastYearEOS_target - self.oct_nov_min_release[wyt][dowy], 0.0)
		
    return swp_extra
	    
  def release_environmental(self,t,basinWYT):
    ###This function calculates how much water will be coming into the delta
    ###based on environmental requirements (and flood control releases).
    ###The additions to the delta contained in self.envmin represent the releases
    ###from the reservoir, minus any calls on water rights that would come from this
    ###reservoir.  This number does not include downstream 'gains' to the delta,
    ###although when those gains can be used to meet demands which would otherwise 'call'
    ###in their water rights, those gains are considered consumed before the delta but
	###no release is required from the reservoir (the reason for this is how water is 
	###accounted at the delta for dividing SWP/CVP pumping)
    d = self.day_year[t]
    m = self.month[t]
    dowy = self.dowy[t]
    wyt = self.forecastWYT
    year = self.year[t] - self.starting_year
    	
	####ENVIRONMENTAL FLOWS
	##What releases are needed directly downstream of reservoir
    self.basinuse = np.interp(d, self.first_d_of_month[year], self.nodd)
    self.gains_to_delta += self.basinuse
	
    if self.nodd_meets_envmin:
      reservoir_target_release = max(max(self.env_min_flow[wyt][m-1]*cfs_tafd - self.basinuse,0.0), self.variable_min_flow)
    else:
      reservoir_target_release = max(self.env_min_flow[wyt][m-1]*cfs_tafd, self.variable_min_flow)

	###What releases are needed to meet flow requirements further downstream (at a point we can calculate 'gains')
    downstream_target_release = (self.temp_releases[basinWYT][m-1]*cfs_tafd - self.downstream[t])
      
	####FLOOD CONTROL
	##Top of storage pool
    self.tocs[t], self.max_fcr = self.current_tocs(dowy, self.fci[t])
    #What size release needs to be made
    W = self.S[t] + self.Q[t]
    self.fcr = max(0.2*(W-self.tocs[t]),0.0)

	###Based on the above requirements, what flow will make it to the delta?
    self.envmin = max(reservoir_target_release, downstream_target_release,self.sjrr_release, self.fcr)
    self.envmin = min(self.envmin, W - self.dead_pool)
    self.envmin -= self.consumed_releases
	      
  def step(self, t):
	###What are the contract obligations north-of-delta (only for Northern Reservoirs)
    self.envmin += (self.basinuse + self.consumed_releases)
	##What is the constraining factor - flood, consumptive demands, or environment?
    self.Rtarget[t] = self.envmin + self.sodd + self.din + self.dout
    # then clip based on constraints
    W = self.S[t] + self.Q[t]
    self.R[t] = max(min(self.Rtarget[t], W - self.dead_pool), 0.0)
    self.R[t] = min(self.R[t], self.max_outflow * cfs_tafd)
	#save this value as 'forced spills' to add to delta inflow
	#in model.py
    self.force_spill = max(W - self.R[t] - self.capacity, 0.0)
    self.fcr += self.force_spill
    self.R[t] +=  self.force_spill # spill
    if t < (self.T - 1):
      self.S[t+1] = max(W - self.R[t] - self.E[t], 0) # mass balance update
    self.R_to_delta[t] = max(self.R[t] - self.basinuse - self.consumed_releases, 0) # delta calcs need this
	
	
  def find_flow_pumping(self, t, m, dowy, wyt, release):
    # projection_length = 15
    # first_of_month_shift = dowy - (1 + self.dowy_eom[m-1] - self.days_in_month[m-1])
	###This function allows us to predict, at a monthly step, how much
    ###flow might come into the reservoir, and the rate at which we will
    ###have to release it, starting right now, in order to avoid spilling water
    ###from flood control rules.  This considers the variable inflow over time but
    ###also the variable flood control rules over time
    # if t < projection_length:
    #   flow_range = range(0,projection_length)
    # else:
    #   flow_range = range(t-projection_length, t)

    year = self.year[t] - self.starting_year
    current_storage = self.S[t]#starting storage
    running_storage = current_storage#storage after each (monthly) timestep

    self.min_daily_uncontrolled = 0.0#rate at which flow has to be released in order to avoid overtopping
    self.max_daily_uncontrolled = 999.99#rate which flow cannot be released pass in order to avoid missing EOS targets
    self.uncontrolled_available = 0.0#maximum volume 'above' flood control, w/o releases
    self.numdays_fillup[release] = 999.99#number of days until reservoir fills
    self.numdays_fillup['lookahead'] = 999.99
    numdays_fillup_next_year = 999.99
    total_applied = 0.0
    drawdown_toggle = 0
    numdays_fillup_cap = 999.99
    uncontrolled_cap = 0.0
    additional_drawdown_cap = 0.0
    self.min_daily_overflow = 0.0

    # this_month_flow = 0.0#period-to-date flow (for calculating monthly distribution)
    cross_counter_wy = 0
    cross_counter_y = 0
    excess_toggle = 0
    excess_toggle2 = 0
    for month_counter in range(0,6):
      month_evaluate = m - 1 + month_counter
      if month_evaluate > 11:
        month_evaluate -= 12
      if month_evaluate == 9 and month_counter > 0:
        #restart flow count for new period (Oct-Mar)
        # this_month_flow = 0
        cross_counter_wy = 1
      elif month_evaluate == 0 and month_counter > 0:
        cross_counter_y = 1
      # elif month_evaluate == 3:
      #   #restart flow count for new period (Apr-July)
      #   this_month_flow = 0
      # elif month_evaluate == 7:
      #   #restart flow count for new perio (Aug-Sept)
      #   this_month_flow = 0

      #Project flow for this month
	  ##find an estimate for the remaining flow in the given period
	  ### i.e. total period projection - observed period flow - running monthly flow count
      ##monthly flow projections based on regression run in create_flow_shapes
      start_of_month = self.dowy_eom[year+cross_counter_y][month_evaluate] - self.days_in_month[year+cross_counter_y][month_evaluate] + 1
      block_start = np.where(month_counter == 0, dowy, start_of_month)
      #current month end dowy
      block_end = self.dowy_eom[year+cross_counter_y][month_evaluate]

      if t < 30:
        if np.sum(self.fnf[0:t])*30.0/(t+1) <= 0.0:
          running_fnf = -6.0
        else:
          running_fnf = np.log(np.sum(self.fnf[0:t])*30.0/(t+1))
      else:
        if np.sum(self.fnf[(t-30):(t-1)]) <= 0.0:
          running_fnf = -6.0
        else:
          running_fnf = np.log(np.sum(self.fnf[(t-30):(t-1)]))

      #if self.key == "MIL" and dowy < 180:
        #if month_evaluate > 2 and month_evaluate < 7:
          #month_flow_int = np.exp(self.flow_shape_regression['slope'][dowy][month_evaluate]*self.SNPK[t] + self.flow_shape_regression['intercept'][dowy][month_evaluate])/(block_end - start_of_month + 1)
        #else:
          #month_flow_int = np.exp(self.flow_shape_regression['slope'][dowy][month_evaluate]*min(running_fnf,0.25) + self.flow_shape_regression['intercept'][dowy][month_evaluate])/(block_end - start_of_month + 1)
      #else:
      if month_evaluate > 2 and month_evaluate < 7:
          #if dowy > 181 and dowy < 304:
            #month_flow_int = (self.flow_shape_regression['slope'][dowy][month_evaluate]*running_fnf + self.flow_shape_regression['intercept'][dowy][month_evaluate])/(block_end - start_of_month + 1)
          #else:
        month_flow_int = np.exp(self.flow_shape_regression['slope'][dowy][month_evaluate]*self.SNPK[t] + self.flow_shape_regression['intercept'][dowy][month_evaluate])/(block_end - start_of_month + 1)
      else:
        month_flow_int = np.exp(self.flow_shape_regression['slope'][dowy][month_evaluate]*running_fnf + self.flow_shape_regression['intercept'][dowy][month_evaluate])/(block_end - start_of_month + 1)

      #month_flow_int = (remaining_flow_proj*self.flow_shape['slope'][month_evaluate]+self.flow_shape['intercept'][month_evaluate])*remaining_flow_proj
	  #running tally of total flow in the month
      # this_month_flow += month_flow_int
      #current month start dowy
	  #what are the mandatory releases between now and the end of this month?
      if release == 'demand':
        if self.key == "MIL":
          if month_evaluate > 8 or month_evaluate < 2:
            total_mandatory_releases = (self.cum_min_release[wyt][block_start] - self.cum_min_release[wyt][block_end+1] + self.aug_sept_min_release[wyt][block_start] - self.aug_sept_min_release[wyt][block_end+1])/(block_end-block_start + 1)
          else:
            total_mandatory_releases = (self.monthly_demand[wyt][month_evaluate] + self.monthly_demand_must_fill[wyt][month_evaluate])/(block_end-start_of_month+1) + (self.cum_min_release[wyt][block_start] - self.cum_min_release[wyt][block_end+1] + self.aug_sept_min_release[wyt][block_start] - self.aug_sept_min_release[wyt][block_end+1])/(block_end-block_start + 1)
        else:
          total_mandatory_releases = (self.monthly_demand[wyt][month_evaluate] + self.monthly_demand_must_fill[wyt][month_evaluate])/(block_end-start_of_month+1) + (self.cum_min_release[wyt][block_start] - self.cum_min_release[wyt][block_end+1] + self.aug_sept_min_release[wyt][block_start] - self.aug_sept_min_release[wyt][block_end+1])/(block_end-block_start + 1)
		  
        total_possible_releases = (self.monthly_demand_full[wyt][month_evaluate] + self.monthly_demand_must_fill[wyt][month_evaluate])/(block_end-start_of_month+1) + (self.cum_min_release[wyt][block_start] - self.cum_min_release[wyt][block_end+1] + self.aug_sept_min_release[wyt][block_start] - self.aug_sept_min_release[wyt][block_end+1])/(block_end-block_start + 1)
        additional_drawdown_cap += max(total_possible_releases - total_mandatory_releases, 0.0)*(block_end - block_start + 1)


      elif release == 'env':
        # Note: cum_min_release is indexed 0 (for cum total before year starts), 1 for min release left after subtracting first day, ..., to 366 after last day. So for each month, we want the end of this month minus end of last month, indexed +1
        total_mandatory_releases = (self.cum_min_release[wyt][block_start] - self.cum_min_release[wyt][block_end+1] + self.aug_sept_min_release[wyt][block_start] - self.aug_sept_min_release[wyt][block_end+1])/(block_end-block_start + 1)
      #expected change in reservoir storage
      #reservoir_change_rate = (month_flow_int - total_mandatory_releases)/self.days_in_month[year+cross_counter_y][month_evaluate]
      if month_counter == 0:
        month_flow_int = max(month_flow_int, np.mean(self.Q[(t-min(t,4)):t]))
      reservoir_change_rate = month_flow_int - total_mandatory_releases
	  
      if reservoir_change_rate < 0.0:
        drawdown_toggle = 1
        numdays_fillup_cap = 999.9

      #flood control pool at start and end of the month
      if self.key == 'MIL' or self.key == "KWH":
        storage_cap_start, max_cap_start = self.current_tocs(np.where(block_start > 0, block_start - 1, 0) ,self.fci[t])
        storage_cap_end, max_cap_end = self.current_tocs(block_end, self.fci[t])
      else:
        storage_cap_start = self.capacity * 1.0
        storage_cap_end = self.capacity * 1.0
      eom_storage = running_storage

      crossover_date = 0.0
      #expected storage at the end of the month
      eom_storage = running_storage + reservoir_change_rate*(block_end - block_start + 1)
      if eom_storage < self.dead_pool:
        break
      self.max_daily_uncontrolled = min(max((eom_storage - self.EOS_target)/ min(block_end + 1 + cross_counter_wy*365 - dowy, self.numdays_fillup[release]), self.min_daily_uncontrolled), self.max_daily_uncontrolled)
      if eom_storage > storage_cap_end:
        #rate of release to avoid flood pool
        if storage_cap_start > running_storage:
          #this_month_min_release = (eom_storage - storage_cap_end ) / (block_end + 1 + cross_counter_wy*365 - dowy)
          if self.key == 'MIL' or self.key == 'KWH':
            this_month_min_release = max((eom_storage - storage_cap_end) / min((block_end + 1 + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), 0.0)
            total_min_release = eom_storage - storage_cap_end
          else:
            this_month_min_release = max((eom_storage - self.capacity) / min((block_end + 1 + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), 0.0)
            total_min_release = eom_storage - self.capacity

          #volume of water over the flood pool, no release
          differential_storage_change = reservoir_change_rate - (storage_cap_end - storage_cap_start)/(block_end - block_start + 1)
          crossover_date = (storage_cap_start - running_storage)/differential_storage_change
        else:
          crossover_date = 0.0
          if (block_start + cross_counter_wy*365 - dowy) > 0.0:
            if self.key == 'MIL' or self.key == 'KWH':
              this_month_min_release = max((running_storage - storage_cap_start)/min((block_start + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), (eom_storage - storage_cap_end) / min((block_end + 1 + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), 0.0)
              total_min_release = max(running_storage - storage_cap_start, eom_storage - storage_cap_end)
            else:
              this_month_min_release = max((running_storage - self.capacity)/min((block_start + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), (eom_storage - self.capacity) / min((block_end + 1 + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), 0.0)
              total_min_release = max(running_storage - self.capacity, eom_storage - self.capacity)

          else:
            if self.key == 'MIL' or self.key == 'KWH':
              this_month_min_release = max(running_storage - storage_cap_start, (eom_storage - storage_cap_end) / min((block_end + 1 + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), 0.0)
              total_min_release = max(running_storage - storage_cap_start, eom_storage - storage_cap_end)

            else:
              this_month_min_release = max(running_storage - self.capacity, (eom_storage - self.capacity) / min((block_end + 1 + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), 0.0)
              total_min_release = max(running_storage - self.capacity, eom_storage - self.capacity)

        
        numdays_fillup = max(block_start + crossover_date + cross_counter_wy*365 - dowy, 1.0)
        if cross_counter_wy == 1:
          numdays_fillup_next_year = block_start + crossover_date + cross_counter_wy*365 - dowy
		  
        #total volume & rate are the maximum monthly value over the next 12 months
        self.min_daily_uncontrolled = max(min(this_month_min_release, self.max_daily_uncontrolled), self.min_daily_uncontrolled)
        if release == 'demand':
          if (min(reservoir_change_rate, self.min_daily_uncontrolled) + (self.monthly_demand[wyt][month_evaluate] + self.monthly_demand_must_fill[wyt][month_evaluate])/(block_end-start_of_month+1)) > (self.total_capacity*cfs_tafd+.1):
            if excess_toggle == 0:
              excess_toggle = 1
              fillup_fraction = 31.0/(block_start - dowy + 1 + cross_counter_wy*365)
            self.min_daily_uncontrolled += max(min(reservoir_change_rate, self.min_daily_uncontrolled) + (self.monthly_demand[wyt][month_evaluate] + self.monthly_demand_must_fill[wyt][month_evaluate])/(block_end-start_of_month+1) - self.total_capacity*cfs_tafd,0.0)*fillup_fraction
			
        if release == 'env':
          self.numdays_fillup[release] = min(numdays_fillup, self.numdays_fillup[release])
          self.numdays_fillup['lookahead'] = min(numdays_fillup_next_year, self.numdays_fillup['lookahead'])
          self.uncontrolled_available = max(total_min_release, self.uncontrolled_available)
        elif release == 'demand':
          self.uncontrolled_available = max(total_min_release, self.uncontrolled_available)

          if self.uncontrolled_available > additional_drawdown_cap:
            self.numdays_fillup[release] = min(numdays_fillup, self.numdays_fillup[release])
            self.numdays_fillup['lookahead'] = min(numdays_fillup_next_year, self.numdays_fillup['lookahead'])
            self.min_daily_overflow = max(self.uncontrolled_available/min((block_end + 1 + cross_counter_wy*365 - dowy), self.numdays_fillup[release]), self.min_daily_overflow)
          if (min(reservoir_change_rate, self.min_daily_overflow) + (self.monthly_demand_full[wyt][month_evaluate] + self.monthly_demand_must_fill[wyt][month_evaluate])/(block_end-start_of_month+1)) > (self.total_capacity*cfs_tafd+.1) and self.uncontrolled_available > additional_drawdown_cap:
            if excess_toggle2 == 0:
              excess_toggle2 = 1
              fillup_fraction2 = 31.0/(block_end - dowy + 1 + cross_counter_wy*365)
            self.min_daily_overflow += max(min(reservoir_change_rate, self.min_daily_overflow) + (self.monthly_demand_full[wyt][month_evaluate] + self.monthly_demand_must_fill[wyt][month_evaluate])/(block_end-start_of_month+1) - self.total_capacity*cfs_tafd, 0.0)*fillup_fraction2         

      running_storage = eom_storage





  def current_tocs(self,dowy,ix):
  ##Interpolates rules from tocs_rule in *_properties.json file to get the top of the conservation
  ##pool in order to determine flood control releases in reservoir.step
    for i,v in enumerate(self.tocs_rule['index']):
      if ix > v:
        break
    storage_bounds = np.zeros(2)
    index_bounds = np.zeros(2)
    day_bounds = np.ones(2)*self.capacity
    for x, y in enumerate(self.tocs_rule['dowy'][i-1]):
      if dowy < y:
        day_bounds[1] = min(day_bounds[1], self.tocs_rule['storage'][i-1][x])
    for x, y in enumerate(self.tocs_rule['dowy'][i]):
      if dowy < y:
        day_bounds[0] = min(day_bounds[0], self.tocs_rule['storage'][i][x])
		
    storage_bounds[1] = np.interp(dowy, self.tocs_rule['dowy'][i-1], self.tocs_rule['storage'][i-1])
    storage_bounds[0] = np.interp(dowy, self.tocs_rule['dowy'][i], self.tocs_rule['storage'][i])
    index_bounds[1] = self.tocs_rule['index'][i-1]
    index_bounds[0] = self.tocs_rule['index'][i]
    return np.interp(ix, index_bounds, storage_bounds), np.interp(ix, index_bounds, day_bounds)

  def rights_call(self,downstream_flow, reset = 0):
    if reset == 0:
      if downstream_flow < 0.0:
        self.consumed_releases = downstream_flow*-1.0
        self.gains_to_delta = 0.0
      else:
        self.consumed_releases = 0.0
        self.gains_to_delta = downstream_flow
    else:
      if downstream_flow < 0.0:
        self.consumed_releases -= downstream_flow
      else:
        self.gains_to_delta += downstream_flow
	  
  def sj_riv_res_flows(self,t,d,toggle_short_series = 0):
    ##Interpolates rules from sj_restoration_proj in *_properties.json file (note: only for Lake Millerton)
	##to get the total daily releases needed to be made under the SJ River Restoration Program (note: rules go into effect
	##in 2009 - they are triggered by the model.update_regulations function
    for i,v in enumerate(self.sj_restoration_proj['dowy']):
      if v > d:
        break
    
    if toggle_short_series == 1:
      ix = self.short_rainflood_fnf[t] + self.short_snowflood_fnf[t]
    else:
      ix = self.rainflood_fnf[t] + self.snowflood_fnf[t]
    release_schedule = self.sj_restoration_proj['release'][i]
    return np.interp(ix, self.sj_restoration_proj['index'], release_schedule)*cfs_tafd
	
  def calc_EOS_storage(self,t,eos_day):
    ##calculate the target end-of-september storage at each reservoir which is used to determine how much excess storage is available for delta pumping releases
    if t == 0:
      startingStorage = self.S[eos_day]
    else:
      startingStorage = max(self.S[eos_day], self.EOS_target)
    self.saved_water = max(startingStorage - self.carryover_target[self.forecastWYT], 0.0)*self.carryover_excess_use
    self.EOS_target = min(self.saved_water + self.carryover_target[self.forecastWYT], self.max_carryover_target)
	
  def set_oct_nov_rule(self, t, m):
    if m == 10 or m == 11:
      self.variable_min_flow = self.Q[t]
    else:
      self.variable_min_flow = 0.0
	  
  def find_emergency_supply(self, t, m, dowy):
    
    if t < 30:
      if np.sum(self.fnf[0:t])*30.0/(t+1) > 0.0:
        running_fnf = np.log(np.sum(self.fnf[0:t])*30.0/(t+1))
      else:
        running_fnf = -6.0
    else:
      if np.sum(self.fnf[(t-30):(t-1)]) > 0.0:
        running_fnf = np.log(np.sum(self.fnf[(t-30):(t-1)]))
      else:
        running_fnf = -6.0
    if m < 10:
      flow_oct_nov = np.exp(self.flow_shape_regression['slope'][dowy][9]*running_fnf + self.flow_shape_regression['intercept'][dowy][9]) + np.exp(self.flow_shape_regression['slope'][dowy][10]*running_fnf + self.flow_shape_regression['intercept'][dowy][10])
    elif m == 10:
      flow_oct_nov = np.exp(self.flow_shape_regression['slope'][dowy][9]*running_fnf + self.flow_shape_regression['intercept'][dowy][9])*(31-dowy)/31 + np.exp(self.flow_shape_regression['slope'][dowy][10]*running_fnf + self.flow_shape_regression['intercept'][dowy][10])
    elif m == 11:
      flow_oct_nov = np.exp(self.flow_shape_regression['slope'][dowy][10]*running_fnf + self.flow_shape_regression['intercept'][dowy][10])*(61-dowy)/30
    else:
      flow_oct_nov = 0.0

    emergency_available = self.S[t] - max(self.oct_nov_min_release[self.forecastWYT][dowy] - flow_oct_nov, 0.0) - self.dead_pool
	
    return emergency_available
	
  def calc_expected_min_release(self,delta_req,depletions,sjrr_toggle):
    ##this function calculates the total expected releases needed to meet environmental minimums used in the find_available_storage function
    ##calclulated as a pre-processing function (w/find_release_func)
    startYear = self.short_year[0]
    startFeb = (self.dowy_eom[self.non_leap_year][0] + 1)
    startAug = (self.dowy_eom[self.non_leap_year][6] + 1)
    for wyt in self.wytlist:
      self.cum_min_release[wyt][0] = 0.0
      self.aug_sept_min_release[wyt][0] = 0.0	  
      self.oct_nov_min_release[wyt][0] = 0.0 	  

    ##the cum_min_release is a 365x1 vector representing each day of the coming water year.  In each day, the value is equal to 
	##the total expected minimum releases remaining in the water year, so that the 0 index is the sum of all expected releases,
	##with the total value being reduce as the index values go up, until the value is zero at the last index spot
    downstream_release = {}
    for wyt in self.wytlist:
      downstream_release[wyt] = np.zeros(12)

    if self.has_downstream_target_flow:
      current_obs = np.zeros(12)
      for t in range(1,self.T_short):
        dowy = self.short_dowy[t - 1]
        m = self.short_month[t - 1]
        da = self.short_day_month[t - 1]
        y = self.short_year[t - 1] - self.short_starting_year
        wateryear = self.short_water_year[t - 1]
        wyt = self.hist_wyt[wateryear]
        if m == 9 and da == 30:
          for month_count in range(0,9):
            if current_obs[month_count]/self.short_days_in_month[y][month_count] > downstream_release[wyt][month_count]:
              downstream_release[wyt][month_count] = current_obs[month_count]/self.short_days_in_month[y][month_count]
          for month_count in range(9,12):
            if current_obs[month_count]/self.short_days_in_month[y-1][month_count] > downstream_release[wyt][month_count]:
              downstream_release[wyt][month_count] = current_obs[month_count]/self.short_days_in_month[y-1][month_count]
          current_obs = np.zeros(12)
        if sjrr_toggle == 1:
          sjrr_flow = self.sj_riv_res_flows(t, dowy, 1)
          downstream_req = max(self.temp_releases[wyt][m-1]*cfs_tafd, sjrr_flow)
        else:
          sjrr_flow = 0.0
          downstream_req = self.temp_releases[wyt][m-1]*cfs_tafd
		
        current_obs[m-1] += max(downstream_req - self.downstream_short[t-1],0.0)
      for x in range(0,12):
        for wyt in self.wytlist:
          downstream_release[wyt][x] = max((delta_req[wyt][x]*cfs_tafd-depletions[x])*self.delta_outflow_pct + max(downstream_release[wyt][x] - self.temp_releases[wyt][x],0.0), downstream_release[wyt][x])
		  
    if self.nodd_meets_envmin:
	   ###First, the total environmental minimum flows are summed over the whole year at day 0
      for x in range(1,365):
        for wyt in self.wytlist:
          m = self.month[x - 1]
          reservoir_target_release = self.env_min_flow[wyt][m-1]*cfs_tafd
          downstream_needs = downstream_release[wyt][m-1]
          if x < startAug:
            self.cum_min_release[wyt][0] += max(reservoir_target_release,downstream_needs)
          else:
            self.aug_sept_min_release[wyt][0] += max(reservoir_target_release,downstream_needs)	  
          if x < startFeb:
            self.oct_nov_min_release[wyt][0] += max(reservoir_target_release,downstream_needs)	  
	    ##THen, we loop through all 365 index spots, removing one day of releases at a time until index 365 = 0.0
      for x in range(1,365):
        for wyt in self.wytlist:
          m = self.month[x - 1]
          reservoir_target_release = self.env_min_flow[wyt][m-1]*cfs_tafd
          downstream_needs = downstream_release[wyt][m-1]
          if x < startAug:
            self.cum_min_release[wyt][x] = self.cum_min_release[wyt][x-1] - max(reservoir_target_release,downstream_needs)
            self.aug_sept_min_release[wyt][x] = self.aug_sept_min_release[wyt][0]
          else:
            self.aug_sept_min_release[wyt][x] = self.aug_sept_min_release[wyt][x-1] - max(reservoir_target_release,downstream_needs)
          if x < startFeb:
            self.oct_nov_min_release[wyt][x] = self.oct_nov_min_release[wyt][x-1] - max(reservoir_target_release,downstream_needs)
          else:
            self.oct_nov_min_release[wyt][x] = self.oct_nov_min_release[wyt][0]

    else:
	##Same as above, but north of delta demands are included w/ release requirements
      for x in range(1,365):
        for wyt in self.wytlist:
          m = self.month[x - 1]
          reservoir_target_release = self.env_min_flow[wyt][m-1]*cfs_tafd
          downstream_needs = downstream_release[wyt][m-1] + np.interp(x,self.first_d_of_month[self.non_leap_year], self.nodd)
          if x < startAug:
            self.cum_min_release[wyt][0] += max(reservoir_target_release,downstream_needs)
          else:
            self.aug_sept_min_release[wyt][0] += max(reservoir_target_release,downstream_needs)	  
          if x < startFeb:
            self.oct_nov_min_release[wyt][0] += max(reservoir_target_release,downstream_needs)	  
			
      for x in range(1,365):
        for wyt in self.wytlist:
          m = self.month[x - 1]
          reservoir_target_release = self.env_min_flow[wyt][m-1]*cfs_tafd
          downstream_needs = downstream_release[wyt][m-1] + np.interp(x,self.first_d_of_month[self.non_leap_year], self.nodd)
          if x < startAug:
            self.cum_min_release[wyt][x] = self.cum_min_release[wyt][x-1] - max(reservoir_target_release,downstream_needs)
            self.aug_sept_min_release[wyt][x] = self.aug_sept_min_release[wyt][0]
          else:
            self.aug_sept_min_release[wyt][x] = self.aug_sept_min_release[wyt][x-1] - max(reservoir_target_release,downstream_needs)
          if x < startFeb:
            self.oct_nov_min_release[wyt][x] = self.oct_nov_min_release[wyt][x-1] - max(reservoir_target_release,downstream_needs)
          else:
            self.oct_nov_min_release[wyt][x] = self.oct_nov_min_release[wyt][0]
	
  def create_flow_shapes(self, df_short):
    flow_series = df_short['%s_inf'% self.key].values * cfs_tafd
    snow_series = df_short['%s_snow'% self.key].values
    fnf_series = df_short['%s_fnf'% self.key].values / 1000000.0
    startYear = self.short_starting_year
    endYear = self.short_ending_year
    numYears = endYear - startYear
    self.flow_shape_regression = {}
    self.flow_shape_regression['slope'] = np.zeros((365,12))
    self.flow_shape_regression['intercept'] = np.zeros((365,12))
    monthly_flow = np.zeros((12, (endYear - startYear)))
    running_fnf = np.zeros((365,(endYear - startYear)))
    max_snow = np.zeros((365,(endYear - startYear)))
    prev_fnf = 0.0
    for t in range(1,(self.T_short)):
      m = self.short_month[t-1]
      dowy = self.short_dowy[t-1]
      wateryear = self.short_water_year[t-1]
      monthly_flow[m-1][wateryear] += flow_series[t-1]
      prev_fnf += fnf_series[t-1]
      max_snow[dowy][wateryear] = snow_series[t-1]
      if t > 30:
        prev_fnf -= fnf_series[t-31]
      if t < 30:
        if prev_fnf <= 0.0:
          running_fnf[dowy][wateryear] = -6.0
        else:
          running_fnf[dowy][wateryear] = np.log(prev_fnf*30.0/t)
      else:
        #if self.key == "MIL" and dowy < 180:
          #running_fnf[dowy][wateryear] = min(prev_fnf, 0.25)
        #else:
        if prev_fnf <= 0.0:
          running_fnf[dowy][wateryear] = -6.0
        else:
          running_fnf[dowy][wateryear] = np.log(prev_fnf)

    scatterplot_values = pd.DataFrame(columns = ['December 30MA', 'February 30MA', 'April 30MA', 'December plus 1 Flow', 'December plus 2 Flow', 'December plus 3 Flow', 'December plus 1 Pred', 'December plus 2 Pred','December plus 3 Pred','February plus 1 Flow', 'February plus 2 Flow', 'February plus 3 Flow', 'February plus 1 Pred', 'February plus 2 Pred', 'February plus 3 Pred', 'April plus 1 Flow', 'April plus 2 Flow', 'April plus 3 Flow', 'April plus 1 Pred', 'April plus 2 Pred', 'April plus 3 Pred'])
    for x in range(0,365): 
      if self.key == "XXX":
        fig = plt.figure()
      #regress for gains in oct-mar period and april-jul period. Use non-leap year.
      coef_save = np.zeros((12,2))
      for mm in range(0,12):
        if x <= self.dowy_eom[self.non_leap_year][mm]:
          if mm > 2 and mm < 7:
            #if x > 181 and x < 304:
              #one_year_runfnf = running_fnf[x]
            #else:
            one_year_runfnf = max_snow[x]
          else:
            one_year_runfnf = running_fnf[x]
          monthly_flow_predict = np.zeros(numYears)
          for yy in range(0,numYears):
            if monthly_flow[mm][yy] > 0.0:
              monthly_flow_predict[yy] = np.log(monthly_flow[mm][yy])
            else:
              monthly_flow_predict = -3.0
        else:
          monthly_flow_predict = np.zeros(numYears-1)
          one_year_runfnf = np.zeros(numYears-1)
          for yy in range(1,numYears):
            if monthly_flow[mm][yy] > 0.0:
              monthly_flow_predict[yy-1] = np.log(monthly_flow[mm][yy])
            else:
              monthly_flow_predict[yy-1] = -3.0
            if mm > 2 and mm < 7:
              #if x > 181 and x < 304:
                #one_year_runfnf[yy-1] = running_fnf[x][yy-1]
              #else:
              one_year_runfnf[yy-1] = max_snow[x][yy-1]
            else:
              one_year_runfnf[yy-1] = running_fnf[x][yy-1]
        if np.sum(one_year_runfnf) == 0.0:
          coef[0] = 0.0
          coef[1] = np.mean(monthly_flow_predict)
        else:
          coef = np.polyfit(one_year_runfnf, monthly_flow_predict, 1)
        self.flow_shape_regression['slope'][x][mm] = coef[0]
        self.flow_shape_regression['intercept'][x][mm] = coef[1]
        if x == 61:
          if mm == 11:
            scatterplot_values['December 30MA'] = one_year_runfnf
            scatterplot_values['December plus 1 Flow'] = monthly_flow_predict
            scatterplot_values['December plus 1 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
          if mm == 0:
            scatterplot_values['December plus 2 Flow'] = monthly_flow_predict
            scatterplot_values['December plus 2 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
          if mm == 1:
            scatterplot_values['December plus 3 Flow'] = monthly_flow_predict
            scatterplot_values['December plus 3 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
        elif x == 121:
          if mm == 1:
            scatterplot_values['February 30MA'] = one_year_runfnf
            scatterplot_values['February plus 1 Flow'] = monthly_flow_predict
            scatterplot_values['February plus 1 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
          if mm == 2:
            scatterplot_values['February plus 2 Flow'] = monthly_flow_predict
            scatterplot_values['February plus 2 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
          if mm == 3:
            scatterplot_values['February plus 3 Flow'] = monthly_flow_predict
            scatterplot_values['February plus 3 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
        elif x == 180:
          if mm == 3:
            scatterplot_values['April 30MA'] = one_year_runfnf
            scatterplot_values['April plus 1 Flow'] = monthly_flow_predict
            scatterplot_values['April plus 1 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
          if mm == 4:
            scatterplot_values['April plus 2 Flow'] = monthly_flow_predict
            scatterplot_values['April plus 2 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))
          if mm == 5:
            scatterplot_values['April plus 3 Flow'] = monthly_flow_predict
            scatterplot_values['April plus 3 Pred'] = coef[0] * one_year_runfnf + coef[1] * np.ones(len(one_year_runfnf))

         
        if self.key == "XXX":
          coef_save[mm][0] = coef[0]
          coef_save[mm][1] = coef[1]
          r = np.corrcoef(one_year_runfnf,monthly_flow_predict)[0,1]
          #print(x, end = " ")
          #print(mm, end = " ")
          #print(r, end = " ")

      if self.key == "XXX":
        for mm in range(0,12):
          ax1 = fig.add_subplot(4,3,mm+1)
          if x <= self.dowy_eom[self.non_leap_year][mm]:
            monthly_flow_predict = monthly_flow[mm]
            if mm > 2 and mm < 7:
              #if x > 181 and x < 304:
                #one_year_runfnf = running_fnf[x]
              #else:
              one_year_runfnf = max_snow[x]
            else:
              one_year_runfnf = running_fnf[x]
          else:
            monthly_flow_predict = np.zeros(numYears-1)
            one_year_runfnf = np.zeros(numYears-1)
            for yy in range(1,numYears):
              monthly_flow_predict[yy-1] = monthly_flow[mm][yy]
              if mm > 2 and mm < 7:
                #if x > 181 and x < 304:
                  #one_year_runfnf[yy-1] = running_fnf[x][yy-1]
                #else:
                one_year_runfnf[yy-1] = max_snow[x][yy-1]
              else:
                one_year_runfnf[yy-1] = running_fnf[x][yy-1]

          ax1.scatter(one_year_runfnf, monthly_flow_predict, s=50, c='red', edgecolor='none', alpha=0.7)
          ax1.plot([0.0, np.max(one_year_runfnf)], [coef_save[mm][1], (np.max(one_year_runfnf)*coef_save[mm][0] + coef_save[mm][1])],c='red')
          ax1.set_xlim([np.min(one_year_runfnf), np.max(one_year_runfnf)])
        plt.show()
        plt.close()
    scatterplot_values.to_csv('manuscript_figures/Figure3/' + self.key + '_flow_forecast_scatter.csv')

			
  def find_release_func(self, df_short):
    ##this function is used to make forecasts when calculating available storage for export releases from reservoir
    ##using data from 1996 to 2016 (b/c data is available for all inputs needed), calculate total flows in oct-mar period and apr-jul period
    ##based on linear regression w/snowpack (apr-jul) and w/inflow (oct-mar)
    ##this function is called before simulation loop, and the linear regression coefficient & standard deviation of linear regresion residuals
    ##is used in the find_available_storage function
    startYear = self.short_starting_year
    endYear = self.short_ending_year
    numYears = endYear - startYear
    Q_predict = df_short['%s_inf'% self.key].values * cfs_tafd
    fnf_predict = df_short['%s_fnf'% self.key].values / 1000000.0
    SNPK_predict = df_short['%s_snow' % self.key].values

    rainfnf = np.zeros(numYears)###total full-natural flow OCT-MAR
    snowfnf = np.zeros(numYears)###total full-natural flow APR-JUL
    fnf_regression = np.zeros((365,4))##constants for linear regression: 2 for oct-mar, 2 for apr-jul
    rainfnf_cumulative = np.zeros((365,numYears))###cumulative daily full-natural flow, rainfall runoff
    snowfnf_cumulative = np.zeros((365,numYears))###cumulative daily full-natural flow, snowmelt runoff

    raininf = np.zeros(numYears)##total reservoir inflow, OCT-Start of snowmelt season
    snowinf = np.zeros(numYears)##total reservoir inflow, Start of snowmelt season - July
    baseinf = np.zeros(numYears)##total reservoir inflow, Aug-Sept
    inf_regression = np.zeros((365,6))##constants for linear regression: 2 for oct-mar, 2 for apr-jul, 2 for Aug-Sept
    raininf_cumulative = np.zeros((365,numYears))##cumulative daily reservoir inflow, rainfall runoff
    snowinf_cumulative = np.zeros((365,numYears))##cumulative daily reservoir inflow, snowmelt runoff
    baseinf_cumulative = np.zeros((365,numYears))##cumulative daily reservoir inflow, baseline runoff

    
    snowPattern = np.zeros((365,numYears))###daily cumulative snowpack
	
    section = 0;##1 is oct-mar, 2 is apr-jul, 3 is aug-sept
    current_year = 0;
    complete_year = 0;##complete year counts all the years that have complete oct-jul data (partial years not used for lin. regression)
    for t in range(1,self.T_short):
      ##Get date information
      dowy = self.short_dowy[t - 1]
      m = self.short_month[t - 1]
      da = self.short_day_month[t - 1]
      
	  #Use date information to determine if its the rainflood season
      if m == 10:
        section_fnf = 1
        section_inf = 1
      elif m == 4:
        section_fnf = 2##SRI & SJI are both divided into Oct-Mar and April-July
      elif m == 8 and da == 1:
        section_fnf = 3
        section_inf = 3
        complete_year += 1##if data exists through end of jul, counts as a 'complete year' for linear regression purposes

      if m == self.melt_start:
        section_inf = 2###for reservoir inflows, section 2 is given a variable start month, runs through end of September
		
	  #find the cumulative full natural flows through each day of the rainflood season - each day has a unique 21 value (year) vector which is the independent variable in the regression to predict total rainflood season flows
      if m == 10 and da == 1:
        current_year +=1
        rainfnf_cumulative[dowy][current_year-1] = fnf_predict[t-1]
        snowfnf_cumulative[dowy][current_year-1] = 0
      elif section_fnf == 1:
        rainfnf_cumulative[dowy][current_year-1] = rainfnf_cumulative[dowy-1][current_year-1] + fnf_predict[t-1]
        snowfnf_cumulative[dowy][current_year-1] = 0
      elif section_fnf == 2:
        rainfnf_cumulative[dowy][current_year-1] = rainfnf_cumulative[dowy-1][current_year-1] ##no rainflood predictions after the rainflood season ends
        snowfnf_cumulative[dowy][current_year-1] = snowfnf_cumulative[dowy-1][current_year-1] + fnf_predict[t-1]
      elif section_fnf == 3:
        rainfnf_cumulative[dowy][current_year-1] = rainfnf_cumulative[dowy-1][current_year-1]
        snowfnf_cumulative[dowy][current_year-1] = snowfnf_cumulative[dowy-1][current_year-1]

	  #find the cumulative reservoir inflows through each day of the rainflood season - each day has a unique 21 value (year) vector which is the independent variable in the regression to predict total rainflood season flows
      if m == 10 and da == 1:
        raininf_cumulative[dowy][current_year-1] = Q_predict[t-1]
        snowinf_cumulative[dowy][current_year-1] = 0.0
        baseinf_cumulative[dowy][current_year-1] = 0.0
      elif section_inf == 1:
        raininf_cumulative[dowy][current_year-1] = raininf_cumulative[dowy-1][current_year-1] + Q_predict[t-1]
        snowinf_cumulative[dowy][current_year-1] = 0.0
        baseinf_cumulative[dowy][current_year-1] = 0.0
      elif section_inf == 2:
        raininf_cumulative[dowy][current_year-1] = raininf_cumulative[dowy-1][current_year-1] ##no rainflood predictions after the rainflood season ends
        snowinf_cumulative[dowy][current_year-1] = snowinf_cumulative[dowy-1][current_year-1] + Q_predict[t-1]
        baseinf_cumulative[dowy][current_year-1] = 0.0
      elif section_inf == 3:
        raininf_cumulative[dowy][current_year-1] = raininf_cumulative[dowy-1][current_year-1]
        snowinf_cumulative[dowy][current_year-1] = snowinf_cumulative[dowy-1][current_year-1]
        baseinf_cumulative[dowy][current_year-1] = baseinf_cumulative[dowy-1][current_year-1] + Q_predict[t-1]
		
	  ##find cumulative snowpack through each day of the year - each day has a unique 21 value (year) vector giving us 365 sepearte lin regressions)	  
      snowPattern[dowy][current_year-1] = SNPK_predict[t-1]
 
	  #find the total full natural flows during the rainflood and snowflood seasons
      if section_fnf == 1:
        rainfnf[current_year-1] += fnf_predict[t-1] ##total oct-mar inflow (one value per year - Y vector in lin regression)
      elif section_fnf == 2:
        snowfnf[current_year-1] += fnf_predict[t-1] ##total apr-jul inflow (one value per year - Y vector in lin regression)

	  #find the total reservoir inflow during the rainflood and snowmelt seasons
      if section_inf == 1:
        raininf[current_year-1] += Q_predict[t-1] ##total oct-mar inflow (one value per year - Y vector in lin regression)
      elif section_inf == 2:
        snowinf[current_year-1] += Q_predict[t-1] ##total apr-jul inflow (one value per year - Y vector in lin regression)
      elif section_inf == 3:
        baseinf[current_year-1] += Q_predict[t-1]
    scatterplot_values = pd.DataFrame(columns = ['December Snowpack', 'February Snowpack', 'April Snowpack', 'Snowmelt Flow', 'D Pred Flow High', 'D Pred Flow Low', 'F Pred Flow High', 'F Pred Flow Low', 'A Pred Flow High', 'A Pred Flow Low'])
    for x in range(1,365):
      
	  ########Full natural flow regressions
	  ########################################################################################################################
	  ###rainflood season regression - full natural flow (regress cumulative full natural flow through each day with total full natural flow, Oct-Mar)
      one_year_flow = rainfnf_cumulative[x-1]##this days set of cumulative flow values (X vector)
      if sum(one_year_flow) == 0.0:
        coef[0] = 0.0
        coef[1] = np.mean(rainfnf)
      else:
        coef = np.polyfit(one_year_flow[0:(complete_year-1)],rainfnf[0:(complete_year-1)],1)###regression of cumulative flow through a day of the rain-flood season with total flow in that rain-flood season
      fnf_regression[x-1][0] = coef[0]
      fnf_regression[x-1][1] = coef[1]
      pred_dev = np.zeros(complete_year)
      for y in range(1,complete_year):
        pred_dev[y-1] = rainfnf[y-1] - coef[0]*one_year_flow[y-1] - coef[1]##how much was the linear regression off actual observations
      
      self.rainfnf_stds[x-1] = np.std(pred_dev)##standard deviations of linear regression residuals 
		##use z-score to make estimate at different confidence levels, ie 90% exceedence is linear regression plus standard deviation * -1.28, z table in util.py
      
	  ###snowflood season regression - full natural flow (regress cumulative snowpack & full natural flow through each day with total full natural flow, April-Jul)
      one_year_snow = snowPattern[x-1]##this days set of cumulative snowpack values (X vector)
      if sum(one_year_snow) == 0.0:
        coef[0] = 0.0
        coef[1] = np.mean(snowfnf)
      else:
        coef = np.polyfit(one_year_snow[0:(complete_year-1)],snowfnf[0:(complete_year-1)],1)
      fnf_regression[x-1][2] = coef[0]
      fnf_regression[x-1][3] = coef[1]
      pred_dev = np.zeros(complete_year)
      for y in range(1,complete_year):
        pred_dev[y-1] = snowfnf[y-1] - coef[0]*one_year_snow[y-1] - coef[1]##how much was the linear regression off actual observations

      self.snowfnf_stds[x-1] = np.std(pred_dev)##standard deviations of linear regression residuals
      ##for conservative estimate, ie 90% exceedence is linear regression plus standard deviation * -1.28, z table in util.py
	  #########################################################################################################################
	  
	  
	  ################Reservoir Inflow regressions
	  #########################################################################################################################
	  ###rainflood season regression - reservoir inflow (regress cumulative reservoir inflow through each day with total full natural flow, Oct-Start of Snowmelt Season at that reservroi)
      one_year_flow = raininf_cumulative[x-1]##this days set of cumulative flow values (X vector)
      remaining_flow = np.zeros(numYears)
      for xx in range(0, numYears):
        remaining_flow[xx] = raininf[xx] - one_year_flow[xx]
      if sum(one_year_flow) == 0.0:
        coef[0] = 0.0
        coef[1] = np.mean(raininf)
      else:
        coef = np.polyfit(one_year_flow[0:(complete_year-1)],remaining_flow[0:(complete_year-1)],1)###regression of cumulative flow through a day of the rain-flood season with total flow in that rain-flood season
      inf_regression[x-1][0] = coef[0]
      inf_regression[x-1][1] = coef[1]
      pred_dev = np.zeros(complete_year)

      for y in range(1,complete_year):
        pred_dev[y-1] = remaining_flow[y-1] - coef[0]*one_year_flow[y-1] - coef[1]##how much was the linear regression off actual observations
      self.raininf_stds[x-1] = np.std(pred_dev)##standard deviations of linear regression residuals
      self.raininf_stds[x-1] = 0.0
		##use z-score to make estimate at different confidence levels, ie 90% exceedence is linear regression plus standard deviation * -1.28, z table in util.py
	  ###snowflood season regression - reservoir inflow (regress cumulative snowpack & reservoir inflow through each day with total reservoir inflow, Snowmelta season at the reservoir)
      one_year_snow = snowPattern[x-1]##this days set of cumulative snowpack values (X vector)
      remaining_snow = np.zeros(numYears)
      for xx in range(0, numYears):
        remaining_snow[xx] = snowinf[xx] - snowinf_cumulative[x-1][xx]
      
      if sum(one_year_snow) == 0.0:
        coef[0] = 0.0
        coef[1] = np.mean(snowinf)
      else:
        coef = np.polyfit(one_year_snow[0:(complete_year-1)],remaining_snow[0:(complete_year-1)],1)
      inf_regression[x-1][2] = coef[0]
      inf_regression[x-1][3] = coef[1]
      pred_dev = np.zeros(complete_year)
      for y in range(1,complete_year):
        pred_dev[y-1] = remaining_snow[y-1] - coef[0]*one_year_snow[y-1] - coef[1]##how much was the linear regression off actual observations

      self.snowinf_stds[x-1] = np.std(pred_dev)##standard deviations of linear regression residuals
      if x == 61:
        scatterplot_values['December Snowpack'] = one_year_snow[0:(complete_year-1)]
        scatterplot_values['D Pred Flow High'] = coef[0]*one_year_snow[0:(complete_year-1)] + (coef[1] + self.snowinf_stds[x-1])*np.ones(complete_year-1)
        scatterplot_values['D Pred Flow Low'] = coef[0]*one_year_snow[0:(complete_year-1)] + (coef[1] - self.snowinf_stds[x-1])*np.ones(complete_year-1)
      
      if x == 123:
        scatterplot_values['February Snowpack'] = one_year_snow[0:(complete_year-1)]
        scatterplot_values['F Pred Flow High'] = coef[0]*one_year_snow[0:(complete_year-1)] + (coef[1] + self.snowinf_stds[x-1])*np.ones(complete_year-1)
        scatterplot_values['F Pred Flow Low'] = coef[0]*one_year_snow[0:(complete_year-1)] + (coef[1] - self.snowinf_stds[x-1])*np.ones(complete_year-1)
      
      if x == 182:
        scatterplot_values['April Snowpack'] = one_year_snow[0:(complete_year-1)]
        scatterplot_values['A Pred Flow High'] = coef[0]*one_year_snow[0:(complete_year-1)] + (coef[1] + self.snowinf_stds[x-1])*np.ones(complete_year-1)
        scatterplot_values['A Pred Flow Low'] = coef[0]*one_year_snow[0:(complete_year-1)] + (coef[1] - self.snowinf_stds[x-1])*np.ones(complete_year-1)

      ##for conservative estimate, ie 90% exceedence is linear regression plus standard deviation * -1.28, z table in util.py
	  ###baseline season regression - reservoir inflow (regress cumulative snowpack & reservoir inflow through each day with total reservoir inflow, Aug-Sept at the reservoir)
      one_year_snow = snowPattern[x-1]##this days set of cumulative snowpack values (X vector)
      remaining_base = np.zeros(numYears)
      for xx in range(0, numYears):
        remaining_base[xx] = baseinf[xx] - baseinf_cumulative[x-1][xx]
      
      if sum(one_year_snow) == 0.0:
        coef[0] = 0.0
        coef[1] = np.mean(baseinf)
      else:
        coef = np.polyfit(one_year_snow[0:(complete_year-1)],remaining_base[0:(complete_year-1)],1)
      inf_regression[x-1][4] = coef[0]
      inf_regression[x-1][5] = coef[1]
	  
      pred_dev = np.zeros(complete_year)
      for y in range(1,complete_year):
        pred_dev[y-1] = remaining_base[y-1] - coef[0]*one_year_snow[y-1] - coef[1]##how much was the linear regression off actual observations

      self.baseinf_stds[x-1] = np.std(pred_dev)##standard deviations of linear regression residuals
          
      	 
    scatterplot_values['Snowmelt Flow'] = snowinf[0:(complete_year-1)]
    #scatterplot_values.to_csv(self.key + '_snow_forecast_scatter.csv')
	  ############################################################################################################################################################
    for t in range(1,self.T):
      m = self.month[t - 1]
      da = self.day_month[t - 1]
      dowy = self.dowy[t - 1]
	  
      running_rain_fnf = np.sum(self.fnf[(t-dowy):(min(t, t-dowy+180))])
      running_rain_inf = np.sum(self.Q[(t-dowy):(min(t, t-dowy+180))])
      self.rainflood_fnf[t-1] = fnf_regression[dowy][0]*running_rain_fnf + fnf_regression[dowy][1]
      self.snowflood_fnf[t-1] = fnf_regression[dowy][2]*self.SNPK[t-1] + fnf_regression[dowy][3]

      self.rainflood_inf[t-1] = inf_regression[dowy][0]*running_rain_inf + inf_regression[dowy][1]
      self.snowflood_inf[t-1] = inf_regression[dowy][2]*self.SNPK[t-1] + inf_regression[dowy][3]
      self.baseline_inf[t-1] = inf_regression[dowy][4]*self.SNPK[t-1] + inf_regression[dowy][5]
    current_year = 0
    for t in range(1, self.T_short):
      dowy = self.short_dowy[t - 1]
      m = self.short_month[t - 1]
      da = self.short_day_month[t - 1]
      if m == 10 and da == 1:
        current_year += 1
      self.short_rainflood_fnf[t-1] = fnf_regression[dowy-1][0]*raininf_cumulative[dowy][current_year-1] + fnf_regression[dowy-1][1]
      self.short_snowflood_fnf[t-1] = fnf_regression[dowy-1][2]*SNPK_predict[t-1] + fnf_regression[dowy-1][3]

	  
	  
  def accounting_as_df(self, index):
    df = pd.DataFrame()
    names = ['storage', 'tocs', 'available_storage', 'flood_storage', 'out', 'numdays_fillup', 'flood_spill', 'flood_delivery']
    things = [self.S, self.tocs, self.available_storage, self.flood_storage, self.R, self.days_til_full, self.flood_spill, self.flood_deliveries]
    for n,t in zip(names,things):
      df['%s_%s' % (self.key,n)] = pd.Series(t, index=index)
    return df
