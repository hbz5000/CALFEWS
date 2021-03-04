cdef class Canal():
     
  cdef:

    public int is_Canal, is_District, is_Private, is_Waterbank, is_Reservoir, locked, num_sites

    public bint recovery_feeder

    public str key, name, 

    public list turnout_use, flow

    public dict capacity, turnout, flow_directions, daily_turnout, turnout_frac, recovery_flow_frac, daily_flow, demand

  cdef void find_turnout_adjustment(self, double demand_constraint, str flow_dir, int canal_loc, list type_list)

  cdef (double, double) check_flow_capacity(self, double available_flow, int canal_loc, str flow_dir)

  cdef dict find_priority_fractions(self, double node_capacity, dict type_fractions, list type_list, int canal_loc, str flow_dir)

  cdef (double, double, int, double) update_canal_use(self, double available_flow, double location_delivery, str flow_dir, int canal_loc, int starting_point, int canal_size, list type_list)

  cdef void find_bi_directional(self, double closed, str direction_true, str direction_false, str flow_type, str new_canal, int adjust_flow_types, int locked)

  cdef void accounting(self, int t, str name, int counter)

  
