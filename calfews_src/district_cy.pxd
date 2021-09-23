from .crop_cy cimport Crop
from .canal_cy cimport Canal
from .contract_cy cimport Contract

cdef class District():

  cdef:
    public double leiu_recovery, in_district_direct_recharge, in_district_storage, recovery_fraction, surface_water_sa, seepage, \
                inleiuhaircut, MDD, use_recharge, use_recovery, extra_leiu_recovery, max_recovery, max_leiu_exchange, \
                direct_recovery_delivery, pre_flood_demand, tot_leiu_recovery_use, leiu_trade_cap, loss_rate, initial_table_a, \
                total_banked_storage, min_direct_recovery, turnback_sales, turnback_purchases, annual_private_pumping, \
                irrseasondemand, recharge_rate, last_days_demand_regression_error, recovery_capacity_remain, table_a_request, \
                current_recharge_storage, current_requested, epsilon

    public int is_Canal, is_District, is_Private, is_Waterbank, is_Reservoir, T, turnback_use, must_fill, seasonal_connection, \
                thismonthuse, monthusecounter, monthemptycounter, has_private, has_pesticide, has_pmp, k_close_wateryear, iter_count, \
                contract_list_length, number_years

    public bint in_leiu_banking

    public str key, name, zone

    public list contract_list, turnout_list, crop_list, urban_profile, participant_list, contract_list_all, non_contract_delivery_list, \
                recharge_rate_series, max_leiu_recharge, max_direct_recharge, delivery_location_list, private_fraction, recharge_decline

    public dict project_contract, rights, service, inleiucap, deliveries, current_balance, paper_balance, turnback_pool, \
                projected_supply, carryover, recharge_carryover, delivery_carryover, contract_carryover_list, dynamic_recharge_cap, \
                days_to_fill, daily_supplies_full, recovery_use, inleiubanked, contract_exchange, leiu_additional_supplies, \
                bank_deliveries, direct_storage, bank_timeseries, leiu_ownership, private_acreage, reservoir_contract, monthlydemand, \
                carryover_rights, private_demand, hist_demand_dict, acreage_by_year, private_delivery, acreage, annualdemand, \
                delivery_percent_coefficient, pumping, annual_pumping, ytd_pumping, demand_auto_errors, demand_days, dailydemand, \
                dailydemand_start, infrastructure_shares
                
    public Crop irrdemand

  cdef double find_node_demand(self, list contract_list, str search_type, int partial_demand_toggle, int toggle_recharge) except *
  
  cdef double set_request_constraints(self, double demand, str search_type, list contract_list, double bank_space, double bank_capacity, int dowy, int wateryear) except *
  
  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal)
  
  cdef void get_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear)

  cdef void get_paper_trade(self, double trade_amount, list contract_list, int wateryear)
  
  cdef double direct_delivery_bank(self, double delivery, int wateryear)

  cdef dict adjust_accounts(self, double direct_deliveries, double recharge_deliveries, list contract_list, str search_type, int wateryear, str delivery_location)

  cdef double find_node_output(self)

  cdef double find_leiu_priority_space(self, double demand_constraint, int num_members, str member_name, int toggle_recharge, str search_type)

  cdef void adjust_recovery(self, double deliveries, str member_name, int wateryear)

  cdef (double, double) update_balance(self, int t, int wateryear, double water_available, double projected_allocation, double current_water, str key, double tot_carryover, str balance_type)

  cdef (double, double) calc_carryover(self, double existing_balance, int wateryear, str balance_type, str key)

  cdef void open_recovery(self, int t, int dowy, int wateryear, double target_eoy)

  cdef void open_recharge(self, int t, int m, int da, int wateryear, int year_index, list days_in_month, double numdays_fillup, double numdays_fillup2, str key, str wyt, list reachable_turnouts, double additional_carryover)

  cdef double get_urban_recovery_target(self, int t, int dowy, int wateryear, str wyt, dict pumping, double project_contract, int demand_days, int start_month) except -1

  cdef tuple set_turnback_pool(self, str key, int year_index, list days_in_month)

  cdef void make_turnback_purchases(self, double turnback_sellers, double turnback_buyers, str key)
  
  cdef tuple find_leiu_output(self, list contract_list)

  cdef void adjust_exchange(self, double deliveries, str member_name, int wateryear)

  cdef double give_paper_trade(self, double trade_amount, list contract_list, int wateryear, str district_name)

  cdef void give_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear, str district_name)

  cdef double record_direct_delivery(self, double delivery, int wateryear)

  cdef (double, double, double) set_deliveries(self, dict priorities, dict type_fractions, list type_list, str search_type, int toggle_district_recharge, str member_name, int wateryear)

  cdef void adjust_bank_accounts(self, str member_name, double direct_deliveries, double recharge_deliveries, int wateryear)

  cdef void accounting_full(self, int t, int wateryear)

  cdef void set_daily_supplies_full(self, str key, double value, int t)

  cdef void accounting_leiubank(self, int t)

  cdef void calc_demand(self, int wateryear, int year_index, int da, int m, list days_in_month, int m1, str wyt)

  cdef void get_urban_demand(self, int t, int m, int da, int dowy, int wateryear, int year_index, list dowy_eom, double total_delta_pumping, double allocation_change, str model_mode)



  