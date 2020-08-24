cdef class Canal():
     
  cdef:

    public int is_Canal, is_District, is_Private, is_Waterbank, is_Reservoir, locked, num_sites

    public bint recovery_feeder

    public str key, name, 

    public list turnout_use, flow

    public dict capacity, turnout, flow_directions, daily_turnout, turnout_frac, recovery_flow_frac, daily_flow, demand
