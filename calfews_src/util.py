import calendar
import numpy as np
import pandas as pd
import h5py
import json
from itertools import compress
import gc

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
