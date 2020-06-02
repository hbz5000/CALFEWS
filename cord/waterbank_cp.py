from __future__ import division
import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import collections as cl
import json
from .util import *


class Waterbank():
  __slots__ = ["T", "index", "number_years", "key", "name", "participant_list", "participant_type", "canal_rights",
               "initial_recharge", "recovery", "tot_storage", "recharge_decline", "ownership", "bank_cap",
               "recharge_rate", "tot_current_storage", "loss_rate", "storage", "recovery_use", "banked",
               "bank_timeseries", "annual_timeseries", "recharge_rate_series", "thismonthuse", "monthusecounter",
               "monthemptycounter", 'current_requested', 'iter_count', 'number_years']

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

  is_Canal = False
  is_Delta = False
  is_District = False
  is_Private = False
  is_Reservoir = False
  is_Waterbank = True

  def __init__(self, model, name, key):
    # self.T = len(df)
    # self.index = df.index
    # self.number_years = self.index.year[self.T - 1] - self.index.year[0]
    self.key = key
    self.name = name
    for k,v in json.load(open('cord/banks/%s_properties.json' % key)).items():
        setattr(self,k,v)
		
    self.recharge_rate = self.initial_recharge*cfs_tafd
    self.tot_current_storage = 0.0 #total above-ground storage being used in water bank 
    self.loss_rate = 0.06 #how much of banked deliveries is lost duing spreading
    
	#dictionaries for individual member use of the bank
    self.storage = {}#how much water delivered to bank this time step
    self.recovery_use = {}#how much recovery capacity is being used by a memeber this time step
    self.banked = {} #how much water is stored in the groundwater banking account of the member
	#timeseries for export to csv
    self.bank_timeseries = {}#daily
    self.annual_timeseries = {}#annual
    self.recharge_rate_series = np.zeros(model.T)#daily recharge rate
    for x in self.participant_list:
      self.storage[x] = 0.0
      self.bank_timeseries[x] = np.zeros(model.T)
      self.annual_timeseries[x] = np.zeros(model.number_years)
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

	  
  def find_node_demand(self,contract_list,xx,num_members, search_type):
    #this function finds the maximum 'demand' available at each node - if
	#in recovery mode, max demand is the available recovery capacity
	#all other modes, max demand is the available recharge space
    if search_type == "recovery":
      #recovery mode - sum the (pumping) capacity use of each wb member
      current_recovery_use = 0.0
      for x in self.recovery_use:
        current_recovery_use += self.recovery_use[x]
      demand_constraint = max(self.recovery - current_recovery_use, 0.0)
    else:
      #recharge mode - sum the (spreading basin) capacity use of each wb member
      current_storage = 0.0
      for xx in self.participant_list:
        current_storage += self.storage[xx]

      demand_constraint = max(self.tot_storage - current_storage, 0.0)

    return demand_constraint

  def find_priority_space(self, num_members, xx, search_type):
    #this function finds how much 'priority' space in the recharge/recovery capacity is owned by a member (member_name) in a given bank 
    if search_type == "recovery":
      initial_capacity =  max(self.recovery*self.ownership[xx]/num_members - self.recovery_use[xx], 0.0)
      available_banked = self.banked[xx]
      return min(initial_capacity, available_banked)
    else:
      initial_capacity = max(self.tot_storage*self.ownership[xx]/num_members - self.storage[xx], 0.0)
      return initial_capacity

	
  def set_demand_priority(self, priority_list, contract_list, demand, delivery, demand_constraint, search_type, contract_canal, current_canal, member_contracts):
    #this function creates a dictionary (demand_dict) that has a key for each 'priority type' associated with the flow
	#different types of flow (flood, delivery, banking, recovery) have different priority types
    demand_dict = {}
    #for flood flows, determine if the wb members have contracts w/ the flooding reservoir - 1st priority
	#if not, do they have turnouts on the 'priority' canals - 2nd priority
	#if not, the demand is 'excess' - 3rd priority (so that flood waters only use certain canals unless the flood releases are big enough)
    if search_type == 'flood':
      priority_toggle = 0
      contractor_toggle = 0
      canal_toggle = 0
      for yy in priority_list:
        if yy.name == contract_canal:
          priority_toggle = 1
      if priority_toggle == 1:
        for y in contract_list:
          for yx in member_contracts:
            if y.name == yx:
              contractor_toggle = 1
        for yy in self.canal_rights:
          if yy == current_canal:
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
      for yy in self.canal_rights:
        if yy == current_canal:
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


  def set_deliveries(self, priorities,type_fractions,type_list,member_name):
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

	
  def adjust_recovery(self, deliveries, member_name, wateryear):
    #this function adjusts the waterbank accounts & capacity usage after
	#a wb member uses recovery
    self.banked[member_name] -= deliveries#bank account
    self.recovery_use[member_name] += deliveries#capacity use
	
  def sum_storage(self):
    #this function calculates the total capacity use in a recharge basin
    self.tot_current_storage = 0.0
    for x in self.participant_list:
      self.tot_current_storage += self.storage[x]
 
  def absorb_storage(self):
    #this function takes water applied to a recharge basin and 'absorbs' it into the
	#ground, clearing up capacity in the recharge basin and adding to the 'bank' accounts
	#of the wb member that applied it
    if self.tot_current_storage > self.recharge_rate*0.75:
      self.thismonthuse = 1
    if self.tot_current_storage > 0.0:
      absorb_fraction = min(self.recharge_rate/self.tot_current_storage,1.0)
      self.tot_current_storage -= self.tot_current_storage*absorb_fraction
      for x in self.participant_list:
        self.banked[x] += self.storage[x]*absorb_fraction*(1.0-self.loss_rate)#bank account (only credit a portion of the recharge to the bank acct)
        self.storage[x] -= self.storage[x]*absorb_fraction#capacity use

  def accounting(self, t, m, da, wateryear):
    #this stores bank account balances in a daily dictionary (for export to 
    stacked_amount = 0.0
    self.recharge_rate_series[t] = self.recharge_rate
    for x in self.participant_list:
      self.bank_timeseries[x][t] = self.banked[x]
      stacked_amount += self.banked[x]
    # if m == 9 and da == 29:
    #   #annual dictionary stores the annual change in gw bank balances
    #   for x in self.participant_list:
    #     sum_total = 0.0
    #     for year_counter in range(0, wateryear):
    #       sum_total += self.annual_timeseries[x][year_counter]
    #     self.annual_timeseries[x][wateryear] = self.banked[x] - sum_total
	  	
  # def bank_as_df(self, index):
  #   #take daily bank account balances (w/running recharge capacities) and save them as a data frame (for export to csv)
  #   df = pd.DataFrame()
  #   for n in self.participant_list:
  #     df['%s_%s' % (self.key,n)] = pd.Series(self.bank_timeseries[n], index = index)
  #   df['%s_rate' % self.key] = pd.Series(self.recharge_rate_series, index = index)
  #   return df
	
  # def annual_bank_as_df(self):
  #   #save annual bank changes as data frame (for export to csv)
  #   df = pd.DataFrame()
  #   for n in self.participant_list:
  #     df['%s_%s_leiu' % (self.key,n)] = pd.Series(self.annual_timeseries[n])
  #   return df



