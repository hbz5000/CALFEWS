from .district_cy cimport District
from .private_cy cimport Private
from .waterbank_cy cimport Waterbank
from .canal_cy cimport Canal

### superclass combining district & private, so they can be preallocated in cython without knowing which one it will be

cdef class Participant():

  cdef:
    public int iter_count, is_District, is_Private, is_Waterbank, is_Canal
    public District district_obj
    public Private private_obj
    public Waterbank waterbank_obj
    public Canal canal_obj

  cdef double set_request_constraints(self, double demand, str search_type, list contract_list, double bank_space, double bank_capacity, int dowy, int wateryear)
  
  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal, str current_canal=*, list member_contracts=*)
  
  cdef void get_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear)

  cdef void get_paper_trade(self, double trade_amount, list contract_list, int wateryear)

  cdef double direct_delivery_bank(self, double delivery, int wateryear, str  district_key=*)

  cdef dict adjust_accounts(self, double direct_deliveries, double recharge_deliveries, list contract_list, str search_type, int wateryear, str delivery_location)

  cdef double find_node_output(self)

  cdef double find_leiu_priority_space(self, double demand_constraint, int num_members, str member_name, int toggle_recharge, str search_type)

  cdef void adjust_recovery(self, double deliveries, str member_name, int wateryear)

  cdef double find_node_demand(self, list contract_list, str xx, int num_members, str search_type)

  cdef double find_priority_space(self, int num_members, str xx, str search_type)

