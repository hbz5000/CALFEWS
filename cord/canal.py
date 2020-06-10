from __future__ import division
import numpy as np 
import pandas as pd
import json
from .util import *

class Canal():
  __slots__ = ["key", "name", "locked", "capacity", "turnout", "recovery_feeder", "flow_directions", "name", 
               'daily_turnout', 'turnout_frac', 'recovery_flow_frac', 'flow', 'num_sites', 'daily_flow', 
               'turnout_use', 'demand', 'iter_count']
               
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

  is_Canal = 1
  is_District = 0
  is_Private = 0
  is_Waterbank = 0
  is_Reservoir = 0
  
  def __init__(self, name, key, scenario_file = 'baseline'):
    self.key = key
    self.name = name
    self.locked = 0 #toggle used to 'lock' the direction of canal flow for the entire time-step (in bi-directional canals)
    for k,v in json.load(open('cord/canals/%s_properties.json' % key)).items():
        setattr(self,k,v)
    if ((scenario_file == 'baseline') == False):
      for k, v in json.load(open(scenario_file)).items():
        setattr(self, k, v)


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
            if ((type(j) == Canal) == False):
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


  def check_flow_capacity(self, available_flow, canal_loc, flow_dir):
    #this function checks to make sure that the canal flow available for delivery is less than or equal to the capacity of the canal at the current node 
    initial_capacity = self.capacity[flow_dir][canal_loc]*cfs_tafd - self.flow[canal_loc]	
    if available_flow > initial_capacity:
      excess_flow = available_flow - initial_capacity
      available_flow = initial_capacity
    else:
      excess_flow = 0.0
   
    return available_flow, excess_flow


  def find_priority_fractions(self, node_capacity, type_fractions, type_list, canal_loc, flow_dir):
    #this function returns the % of each canal demand priority that can be filled, given the turnout capacity at the node and the total demand at that node 
    total_delivery_capacity = max(min(self.turnout[flow_dir][canal_loc]*cfs_tafd - self.turnout_use[canal_loc], node_capacity), 0.0)
    for zz in type_list:
      #find the fraction of each priority type that can be filled, based on canal capacity and downstream demands
      if self.demand[zz][canal_loc]*type_fractions[zz] > total_delivery_capacity:
        if self.demand[zz][canal_loc] > 0.0:
          type_fractions[zz] = min(total_delivery_capacity/self.demand[zz][canal_loc], 1.0)
        else:
          type_fractions[zz] = 0.0
      #update the remaining capacity for remaining priority levels
      total_delivery_capacity -= self.demand[zz][canal_loc]*type_fractions[zz]

    return type_fractions
	
  def find_turnout_adjustment(self, demand_constraint, flow_dir, canal_loc, type_list):
    #this function adjusts the total demand (by priority) at a node to reflect both the turnout capacity at that node, and the total demand possible (not by priority) at that node - priority demands are sometimes in excess of the total node demands because sometimes 'excess capacity' is shared between multiple districts - so we develop self.turnout_frac to pro-rate each member's share of that capacity so that individual requests do not exceed total capacity
    max_turnout = min(self.turnout[flow_dir][canal_loc]*cfs_tafd - self.turnout_use[canal_loc], demand_constraint)
    for zz in type_list:
      if self.demand[zz][canal_loc] > max_turnout:
        if self.demand[zz][canal_loc] > 0.0:
          self.turnout_frac[zz][canal_loc] = min(max_turnout/self.demand[zz][canal_loc], 1.0)
        else:
          self.turnout_frac[zz][canal_loc] = 0.0
        self.demand[zz][canal_loc] = max_turnout
      else:
        self.turnout_frac[zz][canal_loc] = 1.0
      max_turnout -= self.demand[zz][canal_loc]
      if max_turnout < 0.0:
        max_turnout = 0.0
	  
  def update_canal_use(self, available_flow, location_delivery, flow_dir, canal_loc, starting_point, canal_size, type_list):
    #this function checks to see if the next canal node has the capacity to take the remaining flow - if not,
	#the flow is 'turned back', removing the excess water from the canal.flow vector and reallocating it as 'turnback flows'
	#these turnback flows will be run through the previous canal nodes again, to see if any of the prior nodes (where canal capacity
	#is large enough to take the excess flow) have demand for more flow.  This runs until the current node, at which point any remaining
	#flow is considered not delivered
    #at this node, record the total delivery as 'turnout' and the total flow as 'flow' for this canal object
    self.turnout_use[canal_loc] += location_delivery
    self.flow[canal_loc] += available_flow
    evap_flows = 0.0
	#remaning available flow after delivery is made at this node
    available_flow -= location_delivery
    #direction of flow determines which node is next
    if flow_dir == "normal":
       next_step = 1
    if flow_dir == "reverse":
      next_step = -1
    #turnback flows are the remaining available flow in excess of the next node's capacity
    turnback_flows = max(available_flow - self.capacity[flow_dir][canal_loc+next_step]*cfs_tafd + self.flow[canal_loc+next_step], 0.0)
    #if there is turnback flow, we need to remove that flow from the available flow (and all recorded canal flows at previous nodes)
	#if the turnback flow can be accepted by other nodes, it will be recorded as 'flow' and 'turnout_use' then (not this function)
    if turnback_flows > 0.005:
      available_flow -= turnback_flows
      if flow_dir == "normal":
        turnback_end = canal_loc + 1
        for removal_flow in range(starting_point,canal_loc+1):
          self.flow[removal_flow] -= turnback_flows
      elif flow_dir == "reverse":
        turnback_end = canal_size - canal_loc - 1
        for removal_flow in range(starting_point,canal_loc-1,-1):
          self.flow[removal_flow] -= turnback_flows
    else:
      available_flow -= turnback_flows
      evap_flows += turnback_flows

      if flow_dir == "normal":
        for removal_flow in range(starting_point, canal_loc + 1):
          self.flow[removal_flow] -= turnback_flows
      elif flow_dir == "reverse":
        for removal_flow in range(starting_point, canal_loc-1, -1):
          self.flow[removal_flow] -= turnback_flows

      turnback_flows = 0.0
		
      #find the 'stopping point' for turnback flow deliveries (i.e., the last node)
    if flow_dir == "normal":
      turnback_end = canal_loc + 1
    elif flow_dir == "reverse":
      turnback_end = canal_size - canal_loc - 1

    return available_flow, turnback_flows, turnback_end, evap_flows
	
  def find_bi_directional(self, closed, direction_true, direction_false, flow_type, new_canal, adjust_flow_types, locked):
    #this function determines the direction of flow in a bi-directional canal.  The first time (based on the order of different delivery types) water is turned out onto that canal, the direction is set (based on the direction of flow of the turnout) and then locked for the rest of the time-step (so that other sources can't 'change' the direction of flow after deliveries have already been made)
    if closed > 0.0 and locked == 0:
      if adjust_flow_types == 1:
        self.flow_directions['recharge'][new_canal] = direction_true
        self.flow_directions['recovery'][new_canal] = direction_true
      else:
        self.flow_directions[flow_type][new_canal] = direction_true

    elif locked == 0:
      self.flow_directions[flow_type][new_canal] = direction_false	  
	  
  def accounting(self, t, name, counter):
    self.daily_turnout[name][t] = self.turnout_use[counter]
    self.daily_flow[name][t] = self.flow[counter]
	
  def accounting_as_df(self, index):
    df = pd.DataFrame()
    for n in self.daily_flow:    
      df['%s_%s_flow' % (self.key,n)] = pd.Series(self.daily_flow[n], index = index)
    for n in self.daily_turnout:
      df['%s_%s_turnout' % (self.key, n)] = pd.Series(self.daily_turnout[n], index=index)
    return df
	

      

###########################################################################################################
########################GRAVEYARD##########################################################################
###########################################################################################################
  #
  # def capacity_adjust_demand(self, starting_point, canal_range, flow_dir, type_list):
  #   #variable dictionaries have a key for each demand 'priority type'
  #   type_demands = {}#new value at every canal location - total demand of all 'downstream' nodes
  #   type_fractions = {}#new value at every canal location - ratio between canal cap @ location & tot 'downstream' demand
  #   type_deliveries = {}#running tally - how much can be delivered in total on the canal for each priority demand type
  #   type_unmet = {}#running tally - how much demand couldn't be met b/c of capacity constraints
	#
  #   #initialize canal capacity
  #   available_capacity = canal.capacity[flow_dir][starting_point]*cfs_tafd - canal.flow[starting_point]
  #   #start w/ zero for the 'running tally' variable dictionaries
  #   for zz in type_list:
  #     type_deliveries[zz] = 0.0
  #     type_unmet[zz] = 0.0
  #   #loop through all locations within the canal range
  #   for canal_loc in canal_range:
  #     #remaining range is all the canal nodes 'downstream' of current node
  #     if flow_dir == "normal":
  #       remaining_range = range(canal_loc, canal_size)
  #     elif flow_dir == "reverse":
  #       remaining_range = range(canal_loc, 0, -1)
  #     #re-initialize demands at each canal node
  #     for zz in type_list:
  #       type_demands[zz] = 0.0
  #     #sum of all demands 'downstream' of current canal node
  #     for sum_point in remaining_range:
  #       type_demands[zz] += canal.demand[zz][sum_point]
  #     #find the fraction of the total downstream demand that can be filled
	#   #based on the capacity at the current point
  #     available_capacity_int = available_capacity
  #     for zz in type_list:
  #       if type_demands[zz] > 0.0:
  #         type_fractions[zz] = min(available_capacity_int/type_demands[zz], 1.0)
  #       else:
  #         type_fractions[zz] = 0.0
  #       #the fraction is applied to demands at this canal step, and added to the running total
  #       type_deliveries[zz] += canal.demand[zz][canal_loc]*type_fractions[zz]
  #       #available capacity is now whatever the capacity at this node was, minus what was delivered
  #       available_capacity -= canal.demand[zz][canal_loc]*type_fractions[zz]
  #       #unmet demands are also added to the running total
  #       type_unmet[zz] += canal.demand[zz][canal_loc]*(1-type_fractions[zz])
  #       #the intermediate available capacity measures how much flow is left for the remaining priority levels if all
	# 	#demands of the current priority are met w/at the fraction specified
  #       available_capacity_int -= type_demands[zz]*type_fractions[zz]
  #     if flow_dir == "normal":
  #       next_step = 1
  #     elif flow_dir == "reverse":
  #       next_step = -1
  #     #check to see if the canal capacity at the next node is less the the available capacity at this node (minus the expected diversions)
  #     turnback_flows = max(available_capacity - canal.capacity[flow_dir][canal_loc+next_step]*cfs_tafd + canal.flow[canal_loc + next_step], 0.0)
  #     available_capacity -= turnback_flows
  #     #if the next step is a 'choke' point, then whatever flow can't make it past that point is redistributed 'upstream'
  #     for zz in type_list:
  #       extra_flow = min(type_unmet[zz], turnback_flows)
  #       type_deliveries[zz] += extra_flow
  #       type_unmet[zz] -= extra_flow
	#
  #   return type_deliveries
  #
	#
  # def update_canal_demands(self, priorities, type_fractions, type_list, canal_loc):
  #   for zz in type_list:
  #     self.demand[zz][canal_loc] -= priorities[zz]*type_fractions[zz]
