from .crop_cy cimport Crop

cdef class District():

  cdef:
    public double leiu_recovery, in_district_direct_recharge, in_district_storage, recovery_fraction, surface_water_sa, seepage, \
                inleiuhaircut, MDD, use_recharge, use_recovery, extra_leiu_recovery, max_recovery, max_leiu_exchange, \
                direct_recovery_delivery, pre_flood_demand, tot_leiu_recovery_use, leiu_trade_cap, loss_rate, initial_table_a, \
                total_banked_storage, min_direct_recovery, turnback_sales, turnback_purchases, annual_private_pumping, \
                irrseasondemand, recharge_rate, last_days_demand_regression_error, recovery_capacity_remain, table_a_request, \
                current_recharge_storage, current_requested

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
                dailydemand_start
                
    public Crop irrdemand