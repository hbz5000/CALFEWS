cdef public class Reservoir()[object Reservoir_object, type Reservoir_type]:

  cdef:
    public double dead_pool, capacity, max_carryover_target, carryover_excess_use, sodd_pct, max_outflow, delta_outflow_pct, \
                EOS_target, lastYearEOS_target, din, dout, envmin, sodd, basinuse, consumed_releases, sjrr_release, \
                evap_forecast, lastYearRainflood, variable_min_flow, min_daily_overflow, min_daily_uncontrolled, fcr, max_fcr, \
                gains_to_delta, rainflood_flows, baseline_flows, max_daily_uncontrolled, uncontrolled_available, force_spill, \
                snowflood_flows, saved_water, total_capacity, flood_flow_min

    public int is_Canal, is_District, is_Private, is_Waterbank, is_Reservoir, T, T_short, melt_start, exceedence_level, \
                iter_count, eos_day

    public bint nodd_meets_envmin, has_downstream_target_flow, has_delta_target

    public str key, name, forecastWYT

    public list days_through_month, hist_wyt, S, R, tocs, available_storage, flood_storage, Rtarget, R_to_delta, days_til_full, \
                flood_spill, flood_deliveries, nodd, Q, E, fci, SNPK, precip, downstream, fnf, wytlist, rainfnf_stds, snowfnf_stds, \
                raininf_stds, snowinf_stds, baseinf_stds, rainflood_fnf, snowflood_fnf, short_rainflood_fnf, short_snowflood_fnf, \
                rainflood_inf, snowflood_inf, baseline_inf, rainflood_forecast, snowflood_forecast, baseline_forecast, \
                max_direct_recharge, downstream_short, fnf_short, fnf_new, total_available_storage, outflow_release, \
                reclaimed_carryover, contract_flooded

    public dict env_min_flow, temp_releases, tocs_rule, sj_restoration_proj, carryover_target, sodd_curtail_pct, exceedence, \
                cum_min_release, oct_nov_min_release, aug_sept_min_release, monthly_demand, monthly_demand_full, \
                monthly_demand_must_fill, numdays_fillup, flow_shape_regression, dry_year_carryover, env_min_flow_ya, \
                temp_releases_ya, monthly, daily_df_data, snowpack, daily_output_data, k_close_wateryear, monthly_new

