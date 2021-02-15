cdef public class Crop()[object Crop_object, type Crop_type]:

  cdef:
    public double sub, price
    public str key
    public list water_source_list, crop_list
    public dict tau, beta, delta, gamma, leontief, eta, baseline_inputs, baseline_revenue, econ_factors, pmp_keys, crop_keys, etM
