cdef class Contract():

  cdef:

    public double total, maxForecastValue, carryover, daily_deliveries, tot_carryover, running_carryover, projected_carryover, \
                max_allocation, tot_new_alloc, lastYearForecast

    public int allocation_priority, storage_priority, iter_count

    public str key, name, type

    public list allocation, storage_pool, available_water, annual_deliveries, flood_deliveries, contractors

    public dict reduction, daily_supplies
