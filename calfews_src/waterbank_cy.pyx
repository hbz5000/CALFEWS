# cython: profile=True
import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import collections as cl
import json
from .util import *
from .canal_cy cimport Canal
from .contract_cy cimport Contract


cdef class Waterbank():

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
    self.is_Canal = 0
    self.is_District = 0
    self.is_Private = 0
    self.is_Waterbank = 1
    self.is_Reservoir = 0

    self.key = key
    self.name = name
    for k,v in json.load(open('calfews_src/banks/%s_properties.json' % key)).items():
      setattr(self,k,v)
		
    self.recharge_rate = self.initial_recharge*cfs_tafd
    self.tot_current_storage = 0.0#total above-ground storage being used in water bank 
    self.loss_rate = 0.06#how much of banked deliveries is lost duing spreading
    
	#dictionaries for individual member use of the bank
    self.storage = {}#how much water delivered to bank this time step
    self.recovery_use = {}#how much recovery capacity is being used by a memeber this time step
    self.banked = {} #how much water is stored in the groundwater banking account of the member
	#timeseries for export to csv
    self.bank_timeseries = {}#daily
    self.recharge_rate_series = [0.0 for _ in range(model.T)]#daily recharge rate
    for x in self.participant_list:
      self.storage[x] = 0.0
      self.bank_timeseries[x] = np.zeros(model.T)
      self.recovery_use[x] = 0.0
      self.banked[x] = 0.0
	  
    #counters to keeps track of the duration of waterbank use (recharge rate declines after continuous use)
    self.thismonthuse = 0
    self.monthusecounter = 0
    self.monthemptycounter = 0


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


#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
##################################DETERMINE DELIVERIES ON CANAL######################################################
#####################################################################################################################

	  
  # def find_node_demand(self, list contract_list, str xx, int num_members, str search_type):
  cdef double find_node_demand(self, list contract_list, str xx, int num_members, str search_type):
    cdef:
      double current_recovery_use, recovery_use, demand_constraint, current_storage, storage
      str recovery_use_key, participant_key

    #this function finds the maximum 'demand' available at each node - if
	  #in recovery mode, max demand is the available recovery capacity
	  #all other modes, max demand is the available recharge space
    if search_type == "recovery":
      #recovery mode - sum the (pumping) capacity use of each wb member
      current_recovery_use = 0.0
      for recovery_use_key in self.recovery_use:
        current_recovery_use += self.recovery_use[recovery_use_key]
      demand_constraint = max(self.recovery - current_recovery_use, 0.0)
    else:
      #recharge mode - sum the (spreading basin) capacity use of each wb member
      current_storage = 0.0
      for participant_key in self.participant_list:
        storage = self.storage[participant_key]
        current_storage += storage

      demand_constraint = max(self.tot_storage - current_storage, 0.0)

    return demand_constraint


  # def find_priority_space(self, int num_members, str xx, str search_type):
  cdef double find_priority_space(self, int num_members, str xx, str search_type):
    #this function finds how much 'priority' space in the recharge/recovery capacity is owned by a member (member_name) in a given bank 
    cdef double initial_capacity, available_banked

    if search_type == "recovery":
      initial_capacity =  max(self.recovery*self.ownership[xx]/num_members - self.recovery_use[xx], 0.0)
      available_banked = self.banked[xx]
      return min(initial_capacity, available_banked)
    else:
      initial_capacity = max(self.tot_storage*self.ownership[xx]/num_members - self.storage[xx], 0.0)
      return initial_capacity

	

  # def set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal, str current_canal, list member_contracts):
  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal, str current_canal, list member_contracts):
    #this function creates a dictionary (demand_dict) that has a key for each 'priority type' associated with the flow
  	#different types of flow (flood, delivery, banking, recovery) have different priority types
    cdef:
      int priority_toggle, contractor_toggle, canal_toggle
      dict demand_dict
      str contract_key, canal_key
      Canal canal_obj
      Contract contract_obj

    demand_dict = {}
    #for flood flows, determine if the wb members have contracts w/ the flooding reservoir - 1st priority
	#if not, do they have turnouts on the 'priority' canals - 2nd priority
	#if not, the demand is 'excess' - 3rd priority (so that flood waters only use certain canals unless the flood releases are big enough)
    if search_type == 'flood':
      priority_toggle = 0
      contractor_toggle = 0
      canal_toggle = 0
      for canal_obj in priority_list:
        if canal_obj.name == contract_canal:
          priority_toggle = 1
      if priority_toggle == 1:
        for contract_obj in contract_list:
          for contract_key in member_contracts:
            if contract_obj.name == contract_key:
              contractor_toggle = 1
        for canal_key in self.canal_rights:
          if canal_key == current_canal:
            canal_toggle = 1
        if contractor_toggle == 1 and canal_toggle == 1:
          demand_dict['contractor'] = demand
          demand_dict['alternate'] = 0.0
          demand_dict['turnout'] = 0.0
          demand_dict['excess'] = 0.0
        elif contractor_toggle == 1:
          demand_dict['contractor'] = 0.0
          demand_dict['alternate'] = demand
          demand_dict['turnout'] = 0.0
          demand_dict['excess'] = 0.0		
        else:
          demand_dict['contractor'] = 0.0
          demand_dict['alternate'] = 0.0
          demand_dict['turnout'] = demand
          demand_dict['excess'] = 0.0
      else:
        demand_dict['contractor'] = 0.0
        demand_dict['alternate'] = 0.0
        demand_dict['turnout'] = 0.0
        demand_dict['excess'] = demand
    #if the flows are for delivery, the don't come to a water bank
    elif search_type == 'delivery':
      demand_dict[contract_canal] = 0.0
    #banking flows are priority for flows that can be taken by a wb member under their 'owned' capacity
	#secondary priority is assigned to districts that are usuing 'excess' space in the wb that they do not own (but the owner does not want to use)
    elif search_type == 'banking':
      canal_toggle = 0
      for canal_key in self.canal_rights:
        if canal_key == current_canal:
          canal_toggle = 1
      if canal_toggle == 1:
        demand_dict['priority'] = min(max(min(demand,delivery), 0.0), demand_constraint)
        demand_dict['secondary'] = min(delivery - max(min(demand,delivery), 0.0), demand_constraint -  demand_dict['priority'])
      else:
        demand_dict['priority'] = 0.0
        demand_dict['secondary'] = min(max(delivery, 0.0), demand_constraint)
	#recovery flows are similar to banking flows - first priority for wb members that are using capacity they own, second priority for wb members using 'excess' capacity
    elif search_type == 'recovery':
      demand_dict['initial'] = min(max(min(demand,delivery), 0.0), demand_constraint)
      demand_dict['supplemental'] = min(delivery - max(min(demand,delivery), 0.0), demand_constraint - demand_dict['initial'])

    return demand_dict


  cdef double set_deliveries(self, dict priorities, dict type_fractions, list type_list, str member_name):
    cdef:
      double final_deliveries, total_deliveries
      str zz
      
    final_deliveries = 0.0
    for zz in type_list:
      #deliveries at this priority level
      total_deliveries = priorities[zz]*type_fractions[zz]
      #running total of all deliveries at this node
      final_deliveries += total_deliveries
      #deliveries first go to direct irrigation, if demand remains
      #adjust demand/recharge space
      self.storage[member_name] += total_deliveries
		
    return final_deliveries
	
#####################################################################################################################
#####################################################################################################################

#####################################################################################################################
######################      UPDATE/SAVE STATE VARIABLES (BANK ACCOUT BALANCES)       ################################
#####################################################################################################################

	
  cdef void adjust_recovery(self, double deliveries, str member_name):
    #this function adjusts the waterbank accounts & capacity usage after
	#a wb member uses recovery
    self.banked[member_name] -= deliveries#bank account
    self.recovery_use[member_name] += deliveries#capacity use
	
  cdef void sum_storage(self):
    #this function calculates the total capacity use in a recharge basin
    cdef str x

    self.tot_current_storage = 0.0
    for x in self.participant_list:
      self.tot_current_storage += self.storage[x]
 

  cdef void absorb_storage(self):
    #this function takes water applied to a recharge basin and 'absorbs' it into the
    #ground, clearing up capacity in the recharge basin and adding to the 'bank' accounts
    #of the wb member that applied it
    cdef:
      double absorb_fraction
      str x 

    if self.tot_current_storage > self.recharge_rate*0.75:
      self.thismonthuse = 1
    if self.tot_current_storage > 0.0:
      absorb_fraction = min(self.recharge_rate/self.tot_current_storage,1.0)
      self.tot_current_storage -= self.tot_current_storage*absorb_fraction
      for x in self.participant_list:
        self.banked[x] += self.storage[x]*absorb_fraction*(1.0-self.loss_rate)#bank account (only credit a portion of the recharge to the bank acct)
        self.storage[x] -= self.storage[x]*absorb_fraction#capacity use


  cdef void accounting(self, t):
    #this stores bank account balances in a daily dictionary (for export to 
    cdef str x 

    self.recharge_rate_series[t] = self.recharge_rate
    for x in self.participant_list:
      self.bank_timeseries[x][t] = self.banked[x]
