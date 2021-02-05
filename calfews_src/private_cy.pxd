from .crop_cy cimport Crop
from .contract_cy cimport Contract

cdef class Private():

  cdef:
    public double in_district_direct_recharge, recovery_fraction, use_recharge, use_recovery, extra_leiu_recovery, \
                max_recovery, max_leiu_exchange, total_banked_storage, recharge_rate, recovery_capacity_remain, \
                current_recharge_storage, banking_risk_level, total_acreage

    public int is_Canal, is_District, is_Private, is_Waterbank, is_Reservoir, turnback_use, thismonthuse, monthusecounter, \
                monthemptycounter, iter_count, age_death, T

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

  # cdef double find_node_demand(self, list contract_list, str search_type, str district_name)