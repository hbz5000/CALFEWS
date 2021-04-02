from .crop_cy cimport Crop
from .contract_cy cimport Contract

cdef class Private():

  cdef:
    public double in_district_direct_recharge, recovery_fraction, use_recharge, use_recovery, extra_leiu_recovery, \
                max_recovery, max_leiu_exchange, total_banked_storage, recharge_rate, recovery_capacity_remain, \
                current_recharge_storage, banking_risk_level, total_acreage, epsilon

    public int is_Canal, is_District, is_Private, is_Waterbank, is_Reservoir, turnback_use, thismonthuse, monthusecounter, \
                monthemptycounter, iter_count, age_death, T, district_list_len

    public str key, name

    public list contract_list, crop_list, contract_list_all, non_contract_delivery_list, max_leiu_recharge, \
                max_direct_recharge, district_list, delivery_risk_rate, delivery_risk, target_annual_demand

    public dict deliveries, current_balance, paper_balance, turnback_pool, projected_supply, carryover, recharge_carryover, \
                delivery_carryover, contract_carryover_list, dynamic_recharge_cap, daily_supplies_full, reservoir_contract, \
                monthlydemand, carryover_rights, hist_demand_dict, acreage, annualdemand, delivery_percent_coefficient, \
                pumping, annual_pumping, ytd_pumping, demand_auto_errors, demand_days, dailydemand, dailydemand_start, \
                pump_out_fraction, crop_maturity, contract_fractions, per_acre, unmet_et, initial_planting, agedemand, \
                direct_recovery_delivery, turnback_sales, turnback_purchases, annual_private_pumping, seepage, zone, \
                seasonal_connection, k_close_wateryear, last_days_demand_regression_error, MDD, has_pesticide, irrdemand, \
                urban_profile, contract_fraction, private_fraction, has_pmp, turnout_list, delivery_location_list, must_fill

  cdef double find_node_demand(self, list contract_list, str search_type, str district_name) except *
  
  cdef double set_request_constraints(self, double demand, str search_type, list contract_list, double bank_space, double bank_capacity, int dowy, int wateryear) except *
  
  cdef dict set_demand_priority(self, list priority_list, list contract_list, double demand, double delivery, double demand_constraint, str search_type, str contract_canal)
  
  cdef void get_paper_exchange(self, double trade_amount, list contract_list, list trade_frac, int wateryear)

  cdef void get_paper_trade(self, double trade_amount, list contract_list, int wateryear)
  
  cdef double direct_delivery_bank(self, double delivery, int wateryear, str district_key)

  cdef dict adjust_accounts(self, double direct_deliveries, double recharge_deliveries, list contract_list, str search_type, int wateryear, str delivery_location)

  cdef double find_leiu_priority_space(self, double demand_constraint, int num_members, str member_name, int toggle_recharge, str search_type)

  cdef void adjust_recovery(self, double deliveries, str member_name, int wateryear)

  cdef (double, double) update_balance(self, int t, int wateryear, double water_available, double projected_allocation, double current_water, str key, double tot_carryover, str balance_type, str district_name, dict project_contract, dict rights)

  cdef (double, double) calc_carryover(self, double existing_balance, int wateryear, str balance_type, str key, str district_name, dict project_contract, dict rights)

  cdef void open_recovery(self, int t, int dowy, int wateryear, int number_years, str wyt, int use_delivery_tolerance, double additional_carryover)

  cdef void open_recharge(self, int t, int m, int da, int wateryear, int year_index, list days_in_month, double numdays_fillup, double numdays_fillup2, str key, str wyt, list reachable_turnouts, double additional_carryover, int contract_allocation)

  cdef double get_urban_recovery_target(self, int t, int dowy, int wateryear, str wyt, dict pumping, double project_contract, int demand_days, int start_month, str district_key)

  cdef tuple set_turnback_pool(self, str key, int year_index, list days_in_month, double additional_carryover)

  cdef void make_turnback_purchases(self, double turnback_sellers, double turnback_buyers, str key)

  cdef double set_request_to_district(self, double demand, str search_type, list contract_list, str district_name)

  cdef dict adjust_account_district(self, double actual_deliveries, list contract_list, str search_type, int wateryear, str district_name, str delivery_location)

  cdef void reset_recharge_recovery(self)

  cdef void set_daily_supplies_full(self, str key, double value, int t, int plusequals)

  cdef void accounting_full(self, int t, int wateryear)

  cdef void get_urban_demand(self, int t, int m, int da, int wateryear, int year_index, list dowy_eom, int dowy, double total_delta_pumping, double allocation_change, str model_mode)

  cdef void calc_demand(self, int wateryear, int year_index, int da, int m, list days_in_month, int non_leap_year, int m1, str wyt)

