from .model_cy cimport Model

cdef class Delta():

  cdef:
    public double last_year_vamp, cvp_aval_stor, swp_aval_stor, cvp_delta_outflow_pct, swp_delta_outflow_pct, \
                final_allocation_swp, final_allocation_cvp, rio_gains, forecastSWPPUMP, vernalis_gains, \
                delta_uncontrolled_remaining, forecastCVPPUMP, total_inflow

    public int T, omr_record_start, omr_rule_start, vamp_rule_start, first_empty_day_SWP, first_empty_day_CVP, \
                iter_count
    
    public str model_mode, key, forecastSCWYT, forecastSJWYT

    public list gains, gains_sac, gains_sj, depletions, vernalis_flow, eastside_streams, inflow, ccc, barkerslough, dmin, \
                sodd_cvp, sodd_swp, TRP_pump, HRO_pump, outflow, surplus, x2, eri, forecastSRI, forecastSJI, sac_fnf, \
                hist_OMR, hist_TRP_pump, hist_HRO_pump, fish_condition, OMR, swp_allocation, cvp_allocation, uncontrolled_swp, \
                uncontrolled_cvp, annual_HRO_pump, annual_TRP_pump, expected_depletion, remaining_outflow

    public dict min_outflow, export_ratio, omr_reqr, omr_addition, rio_vista_min, san_joaquin_min, san_joaquin_min_flow, \
                vamp_flows, new_vamp_rule, san_joaquin_add, san_joaquin_export_ratio, d_1641_export, ec_target, model_params, \
                x2constraint, target_allocation, remaining_tax_free_storage, omr_regression, x2_dict, max_tax_free, \
                expected_outflow, pump_max

  cdef (double, double) find_max_pumping(self, int d, int dowy, int t, str wyt)

  cdef void step(self, int t, int d, int da, int m, int y, int wateryear, int dowy, double cvp_flows, double swp_flows, double swp_pump, double cvp_pump)

  cdef void calc_project_allocation(self, int t, int m, int da, int wateryear)

  cdef (double, double) meet_OMR_requirement(self, int t, int m, int y, int dowy, double cvp_m, double swp_m)

  cdef void create_flow_shapes_omr(self, Model model)

