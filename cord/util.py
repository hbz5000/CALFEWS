import calendar
import numpy as np

cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560
cfsd_mafd = 2.29568411*10**-5 * 86400 / 10 ** 6
z_table_transform = [-1.645, -1.28, -1.035, -0.84, -0.675, -0.525, -0.385, -0.253, -0.125, 0, 0.125, 0.253, 0.385, 0.525, 0.675, 0.84, 1.035, 1.28, 1.645]


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

