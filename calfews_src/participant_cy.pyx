# cython: profile=True
import numpy as np 
from .district_cy cimport District
from .private_cy cimport Private
from .waterbank_cy cimport Waterbank
from .canal_cy cimport Canal

### this class can be seen as a superclass that can hold district/private/waterbank/canal class objects (one at a time), 
### in cases where we need to call methods or retrieve/set attributes within lists that include multiple class types. 
### participant class lets us preallocate memory for cython/c without knowing a priori which type of object it will be.
cdef class Participant():

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

  def __init__(self):
    self.is_District = 0
    self.is_Private = 0
    self.is_Waterbank = 0
    self.is_Canal = 0


### functions - call method from correct class, depending on which one the current participant object is
  cdef double set_request_constraints(self, double demand, str search_type, list contract_list, double bank_space, double bank_capacity, int dowy, int wateryear):
    if self.is_District == 1:
      return self.district_obj.set_request_constraints(demand, search_type, contract_list, bank_space, bank_capacity, dowy, wateryear)
    elif self.is_Private == 1:
      return self.private_obj.set_request_constraints(demand, search_type, contract_list, bank_space, bank_capacity, dowy, wateryear)

  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal, str current_canal=None, list member_contracts=None):
    if self.is_District == 1:
      return self.district_obj.set_demand_priority(priority_list, contract_list, demand, delivery, demand_constraint, search_type, contract_canal)
    elif self.is_Private == 1:
      return self.private_obj.set_demand_priority(priority_list, contract_list, demand, delivery, demand_constraint, search_type, contract_canal)
    elif self.is_Waterbank == 1:
      return self.waterbank_obj.set_demand_priority(priority_list, contract_list, demand, delivery, demand_constraint, search_type, contract_canal, current_canal, member_contracts)      

  cdef void get_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear):
    if self.is_District == 1:
      self.district_obj.get_paper_exchange(trade_amount, contract_list, trade_frac, wateryear)
    elif self.is_Private == 1:
      self.private_obj.get_paper_exchange(trade_amount, contract_list, trade_frac, wateryear)

  cdef void get_paper_trade(self, double trade_amount, list contract_list, int wateryear):
    if self.is_District == 1:
      self.district_obj.get_paper_trade(trade_amount, contract_list, wateryear)
    elif self.is_Private == 1:
      self.private_obj.get_paper_trade(trade_amount, contract_list, wateryear)      

  cdef double direct_delivery_bank(self, double delivery, int wateryear, str  district_key=''):
    if self.is_District == 1:
      return self.district_obj.direct_delivery_bank(delivery, wateryear)
    elif self.is_Private == 1:
      return self.private_obj.direct_delivery_bank(delivery, wateryear, district_key)

  cdef dict adjust_accounts(self, double direct_deliveries, double recharge_deliveries, list contract_list, str search_type, int wateryear, str delivery_location):
    if self.is_District == 1:
      return self.district_obj.adjust_accounts(direct_deliveries, recharge_deliveries, contract_list, search_type, wateryear, delivery_location)
    elif self.is_Private == 1:
      return self.private_obj.adjust_accounts(direct_deliveries, recharge_deliveries, contract_list, search_type, wateryear, delivery_location)
      
  cdef double find_node_output(self):
    # should only be triggered if district
    return self.district_obj.find_node_output()

  cdef double find_leiu_priority_space(self, double demand_constraint, int num_members, str member_name, int toggle_recharge, str search_type):
    # should only be triggered if district
    return self.district_obj.find_leiu_priority_space(demand_constraint, num_members, member_name, toggle_recharge, search_type)

  cdef void adjust_recovery(self, double deliveries, str member_name, int wateryear):
    if self.is_District == 1:
      self.district_obj.adjust_recovery(deliveries, member_name, wateryear)
    elif self.is_Waterbank == 1:
      self.waterbank_obj.adjust_recovery(deliveries, member_name, wateryear)

  cdef double find_node_demand(self, list contract_list, str xx, int num_members, str search_type):
    # should only be triggered if waterbank
    return self.waterbank_obj.find_node_demand(contract_list, xx, num_members, search_type)

  cdef double find_priority_space(self, int num_members, str xx, str search_type):
    # should only be triggered if waterbank
    return self.waterbank_obj.find_priority_space(num_members, xx, search_type) 





### properties - retrieve/set attribute from district or private object, depending on which one the current participant is
  @property 
  def key(self):
    if self.is_District == 1:
      return self.district_obj.key
    elif self.is_Private == 1:
      return self.private_obj.key    
    elif self.is_Waterbank == 1:
      return self.waterbank_obj.key
    elif self.is_Canal == 1:
      return self.canal_obj.key  

  @property 
  def name(self):
    if self.is_District == 1:
      return self.district_obj.name
    elif self.is_Private == 1:
      return self.private_obj.name    
    elif self.is_Waterbank == 1:
      return self.waterbank_obj.name
    elif self.is_Canal == 1:
      return self.canal_obj.name                  

  @property 
  def contract_list(self):
    if self.is_District == 1:
      return self.district_obj.contract_list
    elif self.is_Private == 1:
      return self.private_obj.contract_list

  @property 
  def total_banked_storage(self):
    if self.is_District == 1:
      return self.district_obj.total_banked_storage
    elif self.is_Private == 1:
      return self.private_obj.total_banked_storage

  @total_banked_storage.setter
  def total_banked_storage(self, value):
    if self.is_District == 1:
      self.district_obj.total_banked_storage = value 
    elif self.is_Private == 1:
      self.private_obj.total_banked_storage = value      

  @property 
  def reservoir_contract(self):
    if self.is_District == 1:
      return self.district_obj.reservoir_contract
    elif self.is_Private == 1:
      return self.private_obj.reservoir_contract      

  @property 
  def extra_leiu_recovery(self):
    if self.is_District == 1:
      return self.district_obj.extra_leiu_recovery
    elif self.is_Private == 1:
      return self.private_obj.extra_leiu_recovery

  @extra_leiu_recovery.setter
  def extra_leiu_recovery(self, value):
    if self.is_District == 1:
      self.district_obj.extra_leiu_recovery = value 
    elif self.is_Private == 1:
      self.private_obj.extra_leiu_recovery = value 

  @property 
  def max_leiu_exchange(self):
    if self.is_District == 1:
      return self.district_obj.max_leiu_exchange
    elif self.is_Private == 1:
      return self.private_obj.max_leiu_exchange

  @max_leiu_exchange.setter
  def max_leiu_exchange(self, value):
    if self.is_District == 1:
      self.district_obj.max_leiu_exchange = value 
    elif self.is_Private == 1:
      self.private_obj.max_leiu_exchange = value        

  @property 
  def district_list(self):
    # should only be called if private
    return self.private_obj.district_list      

  @property 
  def in_leiu_banking(self):
    # should only be called if district
    return self.district_obj.in_leiu_banking    

  @property 
  def participant_list(self):
    if self.is_District == 1:
      return self.district_obj.participant_list
    elif self.is_Waterbank == 1:
      return self.waterbank_obj.participant_list
    elif self.is_Canal == 1:
      return self.canal_obj.participant_list      

  @property 
  def inleiubanked(self):
    # should only be called if district
    return self.district_obj.inleiubanked   

  @property 
  def inleiucap(self):
    # should only be called if district
    return self.district_obj.inleiucap   

  @property 
  def banked(self):
    # should only be called if waterbank
    return self.waterbank_obj.banked      

  @property 
  def bank_cap(self):
    # should only be called if waterbank
    return self.waterbank_obj.bank_cap    

  @property 
  def recovery_use(self):
    # should only be called if waterbank
    return self.waterbank_obj.recovery_use     

  @property 
  def recovery(self):
    # should only be called if waterbank
    return self.waterbank_obj.recovery                           



### functions to change value of arrays/dicts in district/private
  def max_direct_recharge(self, idx, value_to_add):
    if self.is_District == 1:
      self.district_obj.max_direct_recharge[idx] += value_to_add 
    elif self.is_Private == 1:
      self.private_obj.max_direct_recharge[idx] += value_to_add 

  def max_leiu_recharge(self, idx, value_to_add):
    if self.is_District == 1:
      self.district_obj.max_leiu_recharge[idx] += value_to_add 
    elif self.is_Private == 1:
      self.private_obj.max_leiu_recharge[idx] += value_to_add       