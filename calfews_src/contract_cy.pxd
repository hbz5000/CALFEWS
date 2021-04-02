cdef class Contract():

  cdef:

    public double total, maxForecastValue, carryover, daily_deliveries, tot_carryover, running_carryover, projected_carryover, \
                max_allocation, tot_new_alloc, lastYearForecast, epsilon

    public int allocation_priority, storage_priority, iter_count

    public str key, name, type

    public list allocation, storage_pool, available_water, annual_deliveries, flood_deliveries, contractors

    public dict reduction, daily_supplies


  cdef void calc_allocation(self, int t, int dowy, double forecast_available, double priority_contract, double secondary_contract, str wyt)

  cdef void find_storage_pool(self, int t, int wateryear, double total_water, double reservoir_storage, double priority_storage)

  cdef void adjust_accounts(self, double contract_deliveries, str search_type, int wateryear)

  cdef void accounting(self, int t, double deliveries, double carryover, double turnback, double flood)


  