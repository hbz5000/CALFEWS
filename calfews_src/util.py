import calendar
import numpy as np
import pandas as pd
import h5py
import json
from itertools import compress
import gc
import sys

cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560
cfsd_mafd = 2.29568411*10**-5 * 86400 / 10 ** 6
z_table_transform = [-1.645, -1.28, -1.035, -0.84, -0.675, -0.525, -0.385, -0.253, -0.125, 0, 0.125, 0.253, 0.385, 0.525, 0.675, 0.84, 1.035, 1.28, 1.645]
eps = 1e-8

# check whether each year is leap year.
def leap(y):
  leap = np.empty(len(y), dtype=bool)
  for i in range(len(y)):
    leap[i] = calendar.isleap(y[i])
  return leap.tolist()

# get first non-leap year index in historical record, to use for dowy_eom & days_in_month of non-historical record based on leap.
def first_non_leap_year(dowyeom):
  dowyeom_np = np.array(dowyeom)
  return (np.where(dowyeom_np[0][1] == 28, 0, 1)).tolist()

# get first leap year index in historical record, to use for dowy_eom & days_in_month of non-historical record based on leap.
def first_leap_year(dowyeom):
  dowyeom_np = np.array(dowyeom)
  return (np.argmax([dowyeom_np[0][1], dowyeom_np[1][1], dowyeom_np[2][1], dowyeom_np[3][1]])).tolist()

# get day of water year for historical record
def water_day(d, y):
  dowy = np.empty(len(d), dtype=int)
  for i in range(len(d)):
    if calendar.isleap(y[i]):
      day_change = 275
    else:
      day_change = 274
    if d[i] >= day_change:
      dowy[i] = d[i] - day_change
    else:
      dowy[i] = d[i] + 91
    if dowy[i] > 364:
      dowy[i] = 364
  return dowy.tolist()

# get water year of each month/year in historical record.
def water_year(month, year, startYear):
  month_np = np.array(month)
  year_np = np.array(year)

  wy = np.empty(len(year), dtype=int)
  wy[month_np >= 10] = year_np[month_np >= 10] - startYear
  wy[month_np < 10] = year_np[month_np < 10] - startYear - 1

  return wy.tolist()

# get days in each month. rows are years in historical data, accounting for leap years.
def days_in_month(year, leap):
  days = np.empty([len(year), 12], dtype=int)
  dmonth = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
  dmonth_leap = np.array([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
  for i in range(len(year)):
    if (leap[i]):
      days[i,:] = dmonth_leap
    else:
      days[i,:] = dmonth
  return days.tolist()

# get day of water year of the end of each month, 0-indexed (i.e. first day Oct = 0). rows are years in historical data, accounting for leap years.
def dowy_eom(year, leap):
  dowy = np.empty([len(year), 12], dtype=int)
  eom = np.array([122, 150, 181, 211, 242, 272, 303, 334, 364, 30, 60, 91])
  eom_leap = np.array([122, 151, 182, 212, 243, 273, 304, 335, 364, 30, 60, 91])
  for i in range(len(year)):
    if (leap[i]):
      dowy[i,:] = eom_leap
    else:
      dowy[i,:] = eom
  return dowy.tolist()

# get first day of each month, 1-indexed (i.e. first day Jan = 1). Each row is a year in historical record.
def first_d_of_month(dowyeom, daysinmonth):
  first_d = np.empty([len(dowyeom), 12], dtype=int)
  for i in range(len(dowyeom)):
    first_d[i][:] = np.array(dowyeom)[i] - np.array(daysinmonth)[i] - 90
    first_d[i][first_d[i][:] < 0] = first_d[i][first_d[i][:] < 0] + 365
  return first_d.tolist()



def model_attribute_nonzero(att, name, clean_output):
  if (clean_output):
    attsum = np.abs(att).sum()
    if attsum > eps:
      return (att, name)
    else:
      return (False, False)
  else:
    return(att, name)
      
### generator to loop through important model attributes and return non-zero data
def model_attribute_loop_generator(output_list, clean_output, modelno, modelso):
  for r in output_list['north']['reservoirs'].keys():
    for o in output_list['north']['reservoirs'][r].keys():
      if output_list['north']['reservoirs'][r][o]:
        try:
          att, name = model_attribute_nonzero(modelno.__getattribute__(r).__getattribute__(o), np.string_(r + '_' + o), clean_output)
          if list(att):
            yield list(att), name
        except:
          pass

  for r in output_list['south']['reservoirs'].keys():
    for o in output_list['south']['reservoirs'][r].keys():
      if output_list['south']['reservoirs'][r][o]:
        try:
          att, name = model_attribute_nonzero(modelso.__getattribute__(r).__getattribute__(o), np.string_(r + '_' + o), clean_output)
          if list(att):
            yield list(att), name              
        except:
          pass      
        
  for o in output_list['north']['delta'].keys():
    if output_list['north']['delta'][o]:
      try:
        att, name = model_attribute_nonzero(modelno.delta.__getattribute__(o), np.string_('delta_' + o), clean_output)     
        if list(att):
          yield list(att), name            
      except:
        pass             
      
  for c in output_list['south']['contracts'].keys():
    for o in output_list['south']['contracts'][c].keys():
      if o == 'daily_supplies':
        for t in output_list['south']['contracts'][c]['daily_supplies'].keys():
          if output_list['south']['contracts'][c]['daily_supplies'][t]:
            try:
              att, name = model_attribute_nonzero(modelso.__getattribute__(c).daily_supplies[t], np.string_(c + '_' + t), clean_output)       
              if list(att):
                yield list(att), name                     
            except:
              pass         
            
      elif output_list['south']['contracts'][c][o]:
        try:
          att, name = model_attribute_nonzero(modelso.__getattribute__(c).__getattribute__(o), np.string_(c + '_' + o), clean_output)        
          if list(att):
            yield list(att), name              
        except:
          pass       
        
  for d in output_list['south']['districts'].keys():
    for o in output_list['south']['districts'][d].keys():
      try:
        att, name = model_attribute_nonzero(modelso.__getattribute__(d).daily_supplies_full[o], np.string_(d + '_' + o), clean_output)       
        if list(att):
          yield list(att), name                  
      except:
        pass
      
  for p in output_list['south']['private'].keys():
    for o in output_list['south']['private'][p].keys():
      try:
        att, name = model_attribute_nonzero(modelso.__getattribute__(p).daily_supplies_full[o], np.string_(p + '_' + o), clean_output)        
        if list(att):
          yield list(att), name                
      except:
        pass
      
  for waterbank_obj in modelso.waterbank_list:
    for partner_key, partner_series in waterbank_obj.bank_timeseries.items():
      try:
        att, name = model_attribute_nonzero(partner_series, np.string_(waterbank_obj.name + '_' + partner_key), clean_output)
        if list(att):
          yield list(att), name              
      except:
        pass

  for canal_obj in modelso.canal_list:
    for node_key, node_series in canal_obj.daily_flow.items():
      try:
        att, name = model_attribute_nonzero(node_series, np.string_(canal_obj.name + '_' + node_key + '_flow'), clean_output)
        if list(att):
          yield list(att), name              
      except:
        pass
    for node_key, node_series in canal_obj.daily_turnout.items():
      try:
        att, name = model_attribute_nonzero(node_series, np.string_(canal_obj.name + '_' + node_key + '_turnout'), clean_output)
        if list(att):
          yield list(att), name              
      except:
        pass      
  
  ### signify end of dataset
  yield (False, False)


# function to take northern & southern model, process & output data
def data_output(output_list_loc, results_folder, clean_output, sensitivity_factors, modelno, modelso, objs):
  nt = len(modelno.shasta.baseline_inf)
  with open(output_list_loc, 'r') as f:
    output_list = json.load(f)
    
  chunk = 50
  with h5py.File(results_folder + '/results.hdf5', 'a') as f:
    d = f.create_dataset('s', (nt, chunk), dtype='float', compression='gzip', chunks=(nt, chunk), maxshape=(nt, None))  

    ### use generator to loop through data and save to hdf5 in chunks
    dat = np.zeros((nt, chunk))
    names = []
    col = 0
    chunknum = 0
    initial_write = 0
    for (att, name) in model_attribute_loop_generator(output_list, clean_output, modelno, modelso):
      if name:  ### end of dataset not yet reached
        if col < chunk:
          names.append(name)
          dat[:, col] = att
          col += 1
        else:
          ### save current chunk and start new one 
          if initial_write == 0:
            ### write first set of data
            d[:] = dat[:, :]
            initial_write = 1
          else:
            ### resize and add new data
            d.resize((nt, d.shape[1] + chunk))
            d[:, -chunk:] = dat[:, :]
          ### start new chunk with current data
          dat[:, 0] = att
          col = 1
          gc.collect()

          ### save chunk of column names & start new chunk
          d.attrs['columns' + str(chunknum)] = names
          names = [name]
          chunknum += 1
          
      else: ### end of dataset reached
        if col > 0:
          ### resize and add new data
          d.resize((nt, d.shape[1] + col))
          d[:, -col:] = dat[:, :col]
          d.attrs['columns' + str(chunknum)] = names


    ### add attribute names as columns 
    d.attrs['start_date'] = str(modelno.year[0]) + '-' + str(modelno.month[0]) + '-' + str(modelno.day_month[0])

    ### add objectives
    for k, v in objs.items():
      d.attrs[k] = v

    # get sensitivity factors (note: defunct except in sensitivity mode, but leave hear so as not to break post-process scripts)
    # sensitivity_value = []
    # sensitivity_name = []
    # for k in sensitivity_factors.keys():
    #   if isinstance(sensitivity_factors[k], dict):
    #     sensitivity_value.append(sensitivity_factors[k]['realization'])
    #     sensitivity_name.append(np.string_(k))
    # d.attrs['sensitivity_factors'] = sensitivity_name
    # d.attrs['sensitivity_factor_values'] = sensitivity_value





def get_results_sensitivity_number_outside_model(results_file, sensitivity_number):
    values = {}
    numdays_index = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    with h5py.File(results_file, 'r') as f:
      ### time series of model output
      data = f['s' + sensitivity_number]
      ### get column names for data
      c = 0
      names = []
      read_data = True
      while read_data:
        try:
          colnames = data.attrs['columns' + str(c)]
          for k in colnames:
            names.append(k)
          c += 1
        except:
          read_data = False
      names = list(map(lambda x: str(x).split("'")[1], names))
      df_data = pd.DataFrame(data[:], columns=names)
      start_date = pd.to_datetime(data.attrs['start_date'])
      start_year = start_date.year
      start_month = start_date.month
      start_day = start_date.day

    datetime_index = []
    monthcount = start_month
    yearcount = start_year
    daycount = start_day
    leapcount = np.remainder(start_year, 4)

    for t in range(0, df_data.shape[0]):
      datetime_index.append(str(yearcount) + '-' + str(monthcount) + '-' + str(daycount))
      daycount += 1
      if leapcount == 0 and monthcount == 2 and ((yearcount % 100) > 0 or (yearcount % 400) == 0):
        numdays_month = numdays_index[monthcount - 1] + 1
      else:
        numdays_month = numdays_index[monthcount - 1]
      if daycount > numdays_month:
        daycount = 1
        monthcount += 1
        if monthcount == 13:
          monthcount = 1
          yearcount += 1
          leapcount += 1
        if leapcount == 4:
          leapcount = 0

    dt = pd.to_datetime(datetime_index) 
    df_data.index = dt

    return df_data



### generate a single synthetic realizaton of fnfs using MGHMM. Adapted from script by Rohini Gupta.
def MGHMM_generate_trace(nYears, uncertainty_dict, drop_date=True):

  ### use random num generator specific to this function to avoid overwriting global seed
  rng = np.random.default_rng(uncertainty_dict['synth_gen_seed'])

  # Static Parameters
  nSites = 15

  # Import stationary parameters
  mghmm_folder = 'calfews_src/data/MGHMM_synthetic/calfews_mhmm_5112022/'
  dry_state_means = np.loadtxt(mghmm_folder + 'dry_state_means.txt')
  wet_state_means = np.loadtxt(mghmm_folder + 'wet_state_means.txt')
  covariance_matrix_dry = np.loadtxt(mghmm_folder + 'covariance_matrix_dry.txt')
  covariance_matrix_wet = np.loadtxt(mghmm_folder + 'covariance_matrix_wet.txt')
  transition_matrix = np.loadtxt(mghmm_folder + 'transition_matrix.txt')

  # Apply mean multipliers
  dry_state_means_sampled = dry_state_means * uncertainty_dict['dry_state_mean_multiplier']
  wet_state_means_sampled = wet_state_means * uncertainty_dict['wet_state_mean_multiplier']

  # Apply covariance multipliers
  covariance_matrix_dry_sampled = covariance_matrix_dry * uncertainty_dict['covariance_matrix_dry_multiplier']

  for j in range(nSites):
    covariance_matrix_dry_sampled[j, j] = covariance_matrix_dry_sampled[j, j] * uncertainty_dict['covariance_matrix_dry_multiplier']

  covariance_matrix_wet_sampled = covariance_matrix_wet * uncertainty_dict['covariance_matrix_wet_multiplier']

  for j in range(nSites):
    covariance_matrix_wet_sampled[j, j] = covariance_matrix_wet_sampled[j, j] * uncertainty_dict['covariance_matrix_wet_multiplier']

  # Apply transition matrix multipliers
  transition_matrix_sampled = transition_matrix
  transition_matrix_sampled[0, 0] = max(min(transition_matrix[0, 0] + uncertainty_dict['transition_drydry_addition'], 1), 0)
  transition_matrix_sampled[1, 1] = max(min(transition_matrix[1, 1] + uncertainty_dict['transition_wetwet_addition'], 1), 0)
  transition_matrix_sampled[0, 1] = 1 - transition_matrix_sampled[0, 0]
  transition_matrix_sampled[1, 0] = 1 - transition_matrix_sampled[1, 1]

  # calculate stationary distribution to determine unconditional probabilities
  eigenvals, eigenvecs = np.linalg.eig(np.transpose(transition_matrix_sampled))
  one_eigval = np.argmin(np.abs(eigenvals - 1))
  pi = eigenvecs[:, one_eigval] / np.sum(eigenvecs[:, one_eigval])
  unconditional_dry = pi[0]
  # unconditional_wet = pi[1]

  logAnnualQ_s = np.zeros([nYears, nSites])

  states = np.empty([np.shape(logAnnualQ_s)[0]])
  if rng.uniform() <= unconditional_dry:
    states[0] = 0
    logAnnualQ_s[0, :] = rng.multivariate_normal(np.reshape(dry_state_means_sampled, -1),
                                                       covariance_matrix_dry_sampled)
  else:
    states[0] = 1
    logAnnualQ_s[0, :] = rng.multivariate_normal(np.reshape(wet_state_means_sampled, -1),
                                                       covariance_matrix_wet_sampled)

  # generate remaining state trajectory and log space flows
  for j in range(1, np.shape(logAnnualQ_s)[0]):
    if rng.uniform() <= transition_matrix_sampled[int(states[j - 1]), int(states[j - 1])]:
      states[j] = states[j - 1]
    else:
      states[j] = 1 - states[j - 1]

    if states[j] == 0:
      logAnnualQ_s[j, :] = rng.multivariate_normal(np.reshape(dry_state_means_sampled, -1),
                                                         covariance_matrix_dry_sampled)
    else:
      logAnnualQ_s[j, :] = rng.multivariate_normal(np.reshape(wet_state_means_sampled, -1),
                                                         covariance_matrix_wet_sampled)

  AnnualQ_s = np.exp(logAnnualQ_s)

  #############################################Daily Disaggregation######################

  ### read in pre - normalized data
  calfews_data = pd.read_csv(mghmm_folder + "calfews_src-data-sim-agg_norm.csv")

  yearly_sum = calfews_data.groupby(['Year']).sum()
  yearly_sum = yearly_sum.reset_index()

  # Import historic annual flows
  AnnualQ_h = pd.read_csv(mghmm_folder + "AnnualQ_h.csv", header=None)

  # Identify number of years in synthetic & historical sample
  N_s = len(AnnualQ_s)
  N_h = len(AnnualQ_h)

  # Find closest year for each synthetic sample
  index = np.zeros(N_s)

  for j in range(0, N_s):
    distance = np.zeros(N_h)
    for i in range(0, N_h):
      distance[i] = (AnnualQ_s[j, 0] - AnnualQ_h.iloc[i, 0]) ** 2
    index[j] = np.argmin(distance)

  # Assign year to the index
  closest_year = yearly_sum.Year[index]
  closest_year = closest_year.reset_index()
  closest_year = closest_year.iloc[:, 1]

  # Disaggregate to a daily value
  DailyQ_s = calfews_data
  DailyQ_s = DailyQ_s[DailyQ_s.Year < DailyQ_s.Year[0] + N_s]

  for i in range(0, N_s):
    y = np.unique(DailyQ_s.Year)[i]
    index_array = np.where(DailyQ_s.Year == np.unique(DailyQ_s.Year)[i])[0]
    newdata = DailyQ_s[DailyQ_s.index.isin(index_array)]
    newdatasize = np.shape(newdata)[0]
    olddata_array = np.where(calfews_data.Year == closest_year[i])[0]
    olddata = calfews_data[calfews_data.index.isin(olddata_array)]
    olddata = olddata.reset_index()
    olddata = olddata.iloc[:, 1:20]
    for z in range(4, 19):
      olddata.iloc[:, z] = AnnualQ_s[i, z - 4] * olddata.iloc[:, z].values
    ## fill in data, accounting for leap years. assume leap year duplicates feb 29
    if newdatasize == 365:
      if np.shape(olddata)[0] == 365:
        DailyQ_s.iloc[index_array, 4:19] = olddata.iloc[:, 4:19].values
      elif np.shape(olddata)[0] == 366:
        # if generated data has 365 days, and disaggregating 366 - day series, skip feb 29 (60th day of leap year)
        DailyQ_s.iloc[index_array[:59], 4:19] = olddata.iloc[0:59, 4:19].values
        DailyQ_s.iloc[index_array[59:365], 4:19] = olddata.iloc[60:366, 4:19].values

    elif newdatasize == 366:
      if np.shape(olddata)[0] == 366:
        DailyQ_s.iloc[index_array, 4:19] = olddata.iloc[:, 4:19].values
      elif np.shape(olddata)[0] == 365:
        # if generated data has 366 days, and disaggregating 365 - day series, repeat feb 28 (59rd day of leap year)
        DailyQ_s.iloc[index_array[:59], 4:19] = olddata.iloc[0:59, 4:19].values
        DailyQ_s.iloc[index_array[59], 4:19] = olddata.iloc[58, 4:19].values
        DailyQ_s.iloc[index_array[60:], 4:19] = olddata.iloc[59:365, 4:19].values

  if drop_date:
    DailyQ_s.drop(['Year','Month','Day','realization'], axis=1, inplace=True)
 
  return DailyQ_s

