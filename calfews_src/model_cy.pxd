from .reservoir_cy cimport Reservoir
from .delta_cy cimport Delta
from .canal_cy cimport Canal
from .district_cy cimport District
from .private_cy cimport Private
from .waterbank_cy cimport Waterbank
from .contract_cy cimport Contract
from .participant_cy cimport Participant


cdef class Model():
 
  cdef:

    public int T, starting_year, ending_year, number_years, T_short, short_starting_year, short_ending_year, short_number_years, \
                sensitivity_sample_number, omr_rule_start, non_leap_year

    public bint use_sensitivity

    public str model_mode, demand_type

    public list df, day_year, day_month, month, year, dowy, water_year, df_short, short_day_year, short_day_month, short_month, \
                short_year, short_dowy, short_water_year, short_days_in_month, days_in_month, dowy_eom, leap, \
                first_d_of_month, sensitivity_sample_names, sensitivity_sample, sensitivity_factors, running_fnf, \
                reservoir_list, city_list, swp_allocation, annual_SWP, hro_pumping, district_list, forecastSRI, contract_list, \
                waterbank_list, canal_list, observed_trp, cvp_allocation, trp_pumping, observed_hro, private_list, annual_CVP, \
                ytd_pump_hro, ytd_pump_trp, observed_hro_pred, urban_list, leiu_list


    public dict delta_gains_regression, canal_reservoir, canal_contract, canal_priority, reservoir_contract, contract_turnouts, \
                contract_reservoir, reservoir_canal, canal_district, pumping_turnback, max_tax_free, district_keys, \
                contract_keys, allocation_losses, district_keys_len, canal_district_len


    public Reservoir shasta, oroville, folsom, yuba, newmelones, donpedro, exchequer, millerton, sanluisstate, sanluisfederal, \
                sanluis, isabella, success, kaweah, pineflat

    public Delta delta 

    public Canal fkc, madera, xvc, calaqueduct, kwbcanal, aecanal, kerncanal, calloway, lerdo, beardsley, kernriverchannel, \
                kaweahriverchannel, tuleriverchannel, kingsriverchannel

    public District berrenda, belridge, buenavista, cawelo, henrymiller, ID4, kerndelta, losthills, rosedale, semitropic, \
                tehachapi, tejon, westkern, wheeler, kcwa, bakersfield, northkern, arvin, delano, pixley, exeter, kerntulare, \
                lindmore, lindsay, lowertule, porterville, saucelito, shaffer, sosanjoaquin, teapot, terra, tulare, fresno, \
                fresnoid, socal, southbay, centralcoast, dudleyridge, tularelake, westlands, chowchilla, maderairr, othertule,\
                otherkaweah, otherfriant, othercvp, otherexchange, othercrossvalley, otherswp, consolidated, alta, krwa, \
                kaweahdelta, sanluiswater, panoche, delpuerto

    public Private wonderful, metropolitan, castaic, coachella

    public Waterbank stockdale, kernriverbed, poso, pioneer, kwb, berrendawb, b2800, wkwb, irvineranch, northkernwb, aewb

    public Contract friant1, friant2, swpdelta, cvpdelta, cvpexchange, crossvalley, kernriver, tuleriver, kaweahriver, kingsriver

  cdef dict search_canal_demand(self, int dowy, Canal canal, str prev_canal, str contract_canal, str flow_dir, str flow_type, int wateryear, str search_type, dict existing_deliveries, str message=*)
  
  cdef tuple distribute_canal_deliveries(self, int dowy, Canal canal, str prev_canal, str contract_canal, double available_flow, int canal_size, int wateryear, str flow_dir, str flow_type, str search_type, str message=*)
  
  cdef void find_node_demand_bank(self, Waterbank bank_node, Canal canal, int canal_loc, list contract_list, list priority_list, str contract_canal, int dowy, int wateryear, str search_type, list type_list)
  
  cdef (double, double) delivery_recovery(self, list contract_list, Canal canal, lookback_range, int starting_point, dict paper_fractions, double direct_recovery, str flow_dir, list type_list, list priority_list, str contract_canal, str delivery_loc_name, int dowy, int wateryear)
  
  cdef void flood_operations(self, int t, int m, int dowy, int wateryear, Reservoir reservoir, str flow_type, int overflow_toggle, str wyt)
  
  cdef void find_node_demand_district(self, District district_node, Canal canal, int canal_loc, double demand_constraint, list contract_list, list priority_list, str contract_canal, int dowy, int wateryear, str search_type, list type_list, int toggle_district_recharge)

  cdef tuple set_canal_range(self, str flow_dir, str flow_type, Canal canal, str prev_canal, int canal_size)

  cdef void update_carryover(self, double spill, str key, int wateryear)

  cdef void set_canal_direction(self, str flow_type)

  cdef (int, int, int, int, double, double) simulate_south(self, int t, double hro_pump, double trp_pump, double swp_alloc, double cvp_alloc, dict proj_surplus, dict max_pumping, double swp_forgone, double cvp_forgone, double swp_AF, double cvp_AF, double swp_AS, double cvp_AS, str wyt, str wytSC, dict max_tax_free, dict flood_release, dict flood_volume) except *

  cdef tuple simulate_north(self, int t, int swp_release, int cvp_release, int swp_release2, int cvp_release2, double swp_pump, double cvp_pump)

  cdef void agg_contract_demands(self, int year_index, int m)

  cdef void appropriate_carryover(self, double forgone, str key, int wateryear)

  cdef void find_recharge_bank(self, int m, str wyt)

  cdef void find_leiu_exchange(self, int wateryear, int dowy)

  cdef void find_recharge_leiu(self, int m, str wyt)

  cdef void find_recharge_indistrict(self,int m, str wyt)

  cdef void update_leiu_capacity(self)

  cdef tuple proj_gains(self, int t, int dowy, int m, int year_index)

  cdef (int, int, double, double, double) find_pumping_release(self, int m, int da, int year_index, int start_storage, dict month_demand, dict month_demand_must_fill, dict expected_pumping, double projected_carryover, double current_carryover, str wyt, int t, str key)

######### init
  cdef tuple northern_initialization_routine(self, scenario=*)

  cdef void initialize_northern_res(self) except *

  cdef void initialize_delta_ops(self)

  cdef void southern_initialization_routine(self, scenario=*) except *

  cdef void initialize_southern_res(self) except *

  cdef void project_urban(self, str datafile, str datafile_cvp, str datafile_pumping) except *

  cdef void predict_delta_gains(self)

  cdef void initialize_water_districts(self, scenario=*)
