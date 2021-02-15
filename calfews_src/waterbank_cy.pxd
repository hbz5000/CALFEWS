cdef public class Waterbank()[object Waterbank_object, type Waterbank_type]:

  cdef:
    public double initial_recharge, recovery, tot_storage, recharge_rate, tot_current_storage, current_requested, loss_rate

    public int thismonthuse, monthusecounter, monthemptycounter, iter_count, number_years, is_Canal, is_District, is_Private, \
                is_Waterbank, is_Reservoir

    public str key, name

    public list participant_list, participant_type, canal_rights, recharge_rate_series, recharge_decline

    public dict ownership, bank_cap, storage, recovery_use, banked, bank_timeseries

  # cdef double find_node_demand(self, list contract_list, str xx, int num_members, str search_type)
