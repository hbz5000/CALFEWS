import calendar
import numpy as np
import h5py
import json
from itertools import compress

cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560
cfsd_mafd = 2.29568411*10**-5 * 86400 / 10 ** 6
z_table_transform = [-1.645, -1.28, -1.035, -0.84, -0.675, -0.525, -0.385, -0.253, -0.125, 0, 0.125, 0.253, 0.385, 0.525, 0.675, 0.84, 1.035, 1.28, 1.645]
eps = 1e-10

# check whether each year is leap year.
def leap(y):
  leap = np.empty(len(y), dtype=bool)
  for i in range(len(y)):
    leap[i] = calendar.isleap(y[i])
  return leap

# get first non-leap year index in historical record, to use for dowy_eom & days_in_month of non-historical record based on leap.
def first_non_leap_year(dowyeom):
  return (np.where(dowyeom[0][1] == 28, 0, 1))

# get first leap year index in historical record, to use for dowy_eom & days_in_month of non-historical record based on leap.
def first_leap_year(dowyeom):
  return (np.argmax([dowyeom[0][1], dowyeom[1][1], dowyeom[2][1], dowyeom[3][1]]))

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
  return dowy

# get water year of each month/year in historical record.
def water_year(month, year, startYear):
  wy = np.empty(len(year), dtype=int)
  wy[month >= 10] = year[month >= 10] - startYear
  wy[month < 10] = year[month < 10] - startYear - 1
  return wy

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
  return days

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
  return dowy

# get first day of each month, 1-indexed (i.e. first day Jan = 1). Each row is a year in historical record.
def first_d_of_month(dowyeom, daysinmonth):
  first_d = np.empty([len(dowyeom), 12], dtype=int)
  for i in range(len(dowyeom)):
    first_d[i][:] = dowyeom[i] - daysinmonth[i] - 90
    first_d[i][first_d[i][:] < 0] = first_d[i][first_d[i][:] < 0] + 365
  return first_d

# function to take northern & southern model, process & output data
def data_output(output_list_loc, results_folder, clean_output, rank, sensitivity_number, sensitivity_factors, modelno, modelso):
  nt = modelno.shasta.baseline_inf.shape[0]
  with open(output_list_loc, 'r') as f:
    output_list = json.load(f)
  dat = np.zeros([nt, 10000])
  names = []
  col = 0
  # get all data columns listed as True in output_list file
  for r in output_list['north']['reservoirs'].keys():
    for o in output_list['north']['reservoirs'][r].keys():
      if output_list['north']['reservoirs'][r][o]:
        dat[:, col] = modelno.__getattribute__(r).__getattribute__(o)
        names.append(np.string_(r + '_' + o))
        col += 1
  for r in output_list['south']['reservoirs'].keys():
    for o in output_list['south']['reservoirs'][r].keys():
      if output_list['south']['reservoirs'][r][o]:
        dat[:, col] = modelso.__getattribute__(r).__getattribute__(o)
        names.append(np.string_(r + '_' + o))
        col += 1
  for o in output_list['north']['delta'].keys():
    if output_list['north']['delta'][o]:
      dat[:, col] = modelno.delta.__getattribute__(o)
      names.append(np.string_('delta_' + o))
      col += 1
  for c in output_list['south']['contracts'].keys():
    for o in output_list['south']['contracts'][c].keys():
      if o == 'daily_supplies':
        for t in output_list['south']['contracts'][c]['daily_supplies'].keys():
          if output_list['south']['contracts'][c]['daily_supplies'][t]:
            dat[:,col] = modelso.__getattribute__(c).daily_supplies[t]
            names.append(np.string_(c + '_' + t))
            col += 1
      elif output_list['south']['contracts'][c][o]:
        dat[:, col] = modelso.__getattribute__(c).__getattribute__(o)
        names.append(np.string_(c + '_' + o))
        col += 1
  for d in output_list['south']['districts'].keys():
    for o in output_list['south']['districts'][d].keys():
      dat[:, col] = modelso.__getattribute__(d).daily_supplies_full[o]
      names.append(np.string_(d + '_' + o))
      col += 1
  for p in output_list['south']['private'].keys():
    for o in output_list['south']['private'][p].keys():
      dat[:, col] = modelso.__getattribute__(p).daily_supplies_full[o]
      names.append(np.string_(p + '_' + o))
      col += 1

  for b in output_list['south']['waterbanks'].keys():
    for o in output_list['south']['waterbanks'][b].keys():
      dat[:, col] = modelso.__getattribute__(b).bank_timeseries[o]
      names.append(np.string_(b + '_' + o ))
      col += 1
  # now only keep columns that are non-zero over course of simulation
  dat = dat[:, :col]
  if (clean_output):
    datsum = dat.sum(axis=0)
    index = np.abs(datsum) > eps
    dat = dat[:, index]
    names = list(compress(names, index))
    col = len(names)
  # get sensitivity factors
  sensitivity_value = []
  sensitivity_name = []
  for k in sensitivity_factors.keys():
    if isinstance(sensitivity_factors[k], dict):
      sensitivity_value.append(sensitivity_factors[k]['realization'])
      sensitivity_name.append(np.string_(k))
  # output to hdf5 file
  with h5py.File(results_folder + '/results_p' + str(rank) + '.hdf5', 'a') as f:
    d = f.create_dataset('s' + str(sensitivity_number), (nt, col), dtype='float', compression='gzip')
    d.attrs['columns'] = names
    d.attrs['sensitivity_factors'] = sensitivity_name
    d.attrs['sensitivity_factor_values'] = sensitivity_value
    d[:] = dat




def data_output_climate_ensemble(output_list_loc, results_folder, clean_output, rank, flow_input_source, modelno, modelso):
  nt = modelno.shasta.baseline_inf.shape[0]
  with open(output_list_loc, 'r') as f:
    output_list = json.load(f)
  dat = np.zeros([nt, 10000])
  names = []
  col = 0
  # get all data columns listed as True in output_list file
  for r in output_list['north']['reservoirs'].keys():
    for o in output_list['north']['reservoirs'][r].keys():
      if output_list['north']['reservoirs'][r][o]:
        dat[:, col] = modelno.__getattribute__(r).__getattribute__(o)
        names.append(np.string_(r + '_' + o))
        col += 1
  for r in output_list['south']['reservoirs'].keys():
    for o in output_list['south']['reservoirs'][r].keys():
      if output_list['south']['reservoirs'][r][o]:
        dat[:, col] = modelso.__getattribute__(r).__getattribute__(o)
        names.append(np.string_(r + '_' + o))
        col += 1
  for o in output_list['north']['delta'].keys():
    if output_list['north']['delta'][o]:
      dat[:, col] = modelno.delta.__getattribute__(o)
      names.append(np.string_('delta_' + o))
      col += 1
  for c in output_list['south']['contracts'].keys():
    for o in output_list['south']['contracts'][c].keys():
      if o == 'daily_supplies':
        for t in output_list['south']['contracts'][c]['daily_supplies'].keys():
          if output_list['south']['contracts'][c]['daily_supplies'][t]:
            dat[:,col] = modelso.__getattribute__(c).daily_supplies[t]
            names.append(np.string_(c + '_' + t))
            col += 1
      elif output_list['south']['contracts'][c][o]:
        dat[:, col] = modelso.__getattribute__(c).__getattribute__(o)
        names.append(np.string_(c + '_' + o))
        col += 1
  for d in output_list['south']['districts'].keys():
    for o in output_list['south']['districts'][d].keys():
      dat[:, col] = modelso.__getattribute__(d).daily_supplies_full[o]
      names.append(np.string_(d + '_' + o))
      col += 1
      #if o == 'deliveries':
        #for o in output_list['south']['districts'][d]['deliveries'].keys():
          #if output_list['south']['districts'][d]['deliveries'][o]:
            #dat[:, col] = modelso.__getattribute__(d).daily_supplies_full[o]
            #names.append(np.string_(d + '__deliveries__' + o))
            #col += 1
      #else:
        #if output_list['south']['districts'][d][o]:
          #dat[:, col] = modelso._getattribute_(d).daily_supplies_full
  for b in output_list['south']['waterbanks'].keys():
    for o in output_list['south']['waterbanks'][b].keys():
      for p in output_list['south']['waterbanks'][b][o].keys():
        dat[:, col] = modelso.__getattribute__(b).__getattribute__(o)[p]
        names.append(np.string_(b + '_' + o + '_' + p))
        col += 1
  # now only keep columns that are non-zero over course of simulation
  dat = dat[:, :col]
  if (clean_output):
    datsum = dat.sum(axis=0)
    index = np.abs(datsum) > eps
    dat = dat[:, index]
    names = list(compress(names, index))
    col = len(names)
  # output to hdf5 file
  with h5py.File(results_folder + '/results_p' + str(rank) + '.hdf5', 'a') as f:
    d = f.create_dataset(flow_input_source, (nt, col), dtype='float', compression='gzip')
    d.attrs['columns'] = names
    d[:] = dat
