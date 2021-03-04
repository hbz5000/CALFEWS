from .canal_cy cimport Canal
from .contract_cy cimport Contract

cdef class Waterbank():

  cdef:
    public double initial_recharge, recovery, tot_storage, recharge_rate, tot_current_storage, current_requested, loss_rate

    public int thismonthuse, monthusecounter, monthemptycounter, iter_count, number_years, is_Canal, is_District, is_Private, \
                is_Waterbank, is_Reservoir

    public str key, name

    public list participant_list, participant_type, canal_rights, recharge_rate_series, recharge_decline

    public dict ownership, bank_cap, storage, recovery_use, banked, bank_timeseries

  cdef double find_node_demand(self, list contract_list, str xx, int num_members, str search_type)

  cdef double find_priority_space(self, int num_members, str xx, str search_type)

  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal, str current_canal, list member_contracts)

  cdef double set_deliveries(self, dict priorities, dict type_fractions, list type_list, str member_name)

  cdef void adjust_recovery(self, double deliveries, str member_name)

  cdef void sum_storage(self)

  cdef void absorb_storage(self)

  cdef void accounting(self, t)

  