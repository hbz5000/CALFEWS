# cython: profile=True
import numpy as np 
import pandas as pd
import json
from .util import *

cdef class Contract():
 
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

  def __init__(self, model, name, key):
    self.key = key
    self.name = name

    for k,v in json.load(open('calfews_src/contracts/%s_properties.json' % key)).items():
        setattr(self,k,v)
	
	#daily state variables for contract allocation & availability
    self.allocation = [0.0 for _ in range(model.T)]
    self.storage_pool = [0.0 for _ in range(model.T)]
    self.available_water = [0.0 for _ in range(model.T)]
	
    #keep track of deliveries made daily/annually from the contract
    self.annual_deliveries = [0.0 for _ in range(model.number_years)]
    self.flood_deliveries = [0.0 for _ in range(model.number_years)]
    self.daily_deliveries = 0.0
	
    self.tot_carryover = 0.0#contract carryover
    self.running_carryover = 0.0
    self.lastYearForecast = self.maxForecastValue#last year's allocation forecast (used to make forecast during the beginning of the year)
    self.projected_carryover = 0.0#projecting the carryover storage for next year (based on individual district storage accounts)
    self.max_allocation = self.total#full allocation for the contract
    self.tot_new_alloc = 0.0#carryover water that is transferred to next year's allocation (rather than district carryover)
	
	#dictionaries to keep track of data for output
    self.daily_supplies = {}
    supply_types = ['contract', 'carryover', 'turnback', 'flood', 'total_carryover']
    for x in supply_types:
      self.daily_supplies[x] = np.zeros(model.T)

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


  cdef void calc_allocation(self, int t, int dowy, double forecast_available, double priority_contract, double secondary_contract, str wyt):
    #this function calculates the contract allocation based on snowpack-based flow forecast
    #before March, allocations are assumed to be equal to last year's allocation (capped at some level)
    #unless the snowpack is large enough to expect larger flows (i.e., low snowpack early in the year doesn't
    #cause contracts to predict super-low allocations
    cdef double forecast_used
    
    if dowy < 90:
      if forecast_available > self.maxForecastValue:
        if self.allocation_priority == 1:
          forecast_used = forecast_available*self.total/priority_contract
        else:#if the contract doesn't have priority, the allocation is the available water minus all priority allocations
          forecast_used = (forecast_available - priority_contract)*self.total/secondary_contract
      elif self.lastYearForecast < forecast_available:
        if self.allocation_priority == 1:
          forecast_used = forecast_available*self.total/priority_contract
        else:#if the contract doesn't have priority, the allocation is the available water minus all priority allocations
          forecast_used = (forecast_available - priority_contract)*self.total/secondary_contract
      else:
        if self.allocation_priority == 1:
          forecast_used = min(self.lastYearForecast, self.maxForecastValue)*self.total/priority_contract
        else:#if the contract doesn't have priority, the allocation is the available water minus all priority allocations
          forecast_used = (min(self.lastYearForecast, self.maxForecastValue)- priority_contract)*self.total/secondary_contract
    else:
      #if the contract has priority, the allocation is just the available (forecasted) water
      if self.allocation_priority == 1:
        forecast_used = forecast_available*self.total/priority_contract
      else:#if the contract doesn't have priority, the allocation is the available water minus all priority allocations
        forecast_used = (forecast_available - priority_contract)*self.total/secondary_contract
    
    if dowy == 360:
      if self.allocation_priority == 1:
        forecast_used = forecast_available*self.total/priority_contract
      else:#if the contract doesn't have priority, the allocation is the available water minus all priority allocations
        forecast_used = (forecast_available - priority_contract)*self.total/secondary_contract
      self.lastYearForecast = forecast_available
      #if self.lastYearForecast > self.maxForecastValue:
        #self.lastYearForecast = self.maxForecastValue
    if forecast_used > self.max_allocation:
      forecast_used = self.max_allocation
	  
    self.allocation[t] = max(min(forecast_used,self.total*self.reduction[wyt]), 0.0)
	

  cdef void find_storage_pool(self, int t, int wateryear, double total_water, double reservoir_storage, double priority_storage):
    #this function finds the storage pool for each contract, given the 'total water'
	#that has come into a given reservoir (storage + deliveries) and the total priority
	#storage that must be filled before this contract's storage
    if self.storage_priority == 1:
      #what is the fraction of the allocation that is available to the contract right now
	  #all contracts with priority storage share the 'total_water' - i.e. if 1/2 of the priority storage
	  #has already come into the reservoir, then 1/2 of the contract's allocation is 'currently available'
      if priority_storage > 0.0:
        self.storage_pool[t] = min(1.0, total_water/priority_storage)*(self.allocation[t])
        self.available_water[t] = reservoir_storage * (self.allocation[t])/priority_storage
      else:
        self.storage_pool[t] = self.allocation[t]
        self.available_water[t] = reservoir_storage
    else:
      #if the contract doesn't have priority, the contract has to wait for the total_water to be greater than the
	  #priority storage before any of that water is available to them
      self.storage_pool[t] = min(self.allocation[t], max(total_water - priority_storage, 0.0))
      self.available_water[t] = max(min(total_water - priority_storage, self.allocation[t], reservoir_storage), 0.0)
	  	  

  cdef void adjust_accounts(self, double contract_deliveries, str search_type, int wateryear):
    #this function records deliveries made on a contract by year - for use in determining if 
    if search_type == "flood":
      self.flood_deliveries[wateryear] += contract_deliveries
    else:
      self.annual_deliveries[wateryear] += contract_deliveries
      self.daily_deliveries += contract_deliveries
	  

  cdef void accounting(self, int t, double deliveries, double carryover, double turnback, double flood):
    self.daily_supplies['contract'][t] += max(deliveries - max(carryover, 0.0) - max(turnback, 0.0), 0.0)
    self.daily_supplies['carryover'][t] += max(min(carryover, deliveries), 0.0)
    self.daily_supplies['turnback'][t] += max(min(turnback, deliveries - carryover), 0.0) 
    self.daily_supplies['flood'][t] += flood
    self.daily_supplies['total_carryover'][t] += carryover





