import calendar
import numpy as np

cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560
cfsd_mafd = 2.29568411*10**-5 * 86400 / 10 ** 6
first_of_month = [1,31,59,90,119,150,180,211,242,272,303,334]
days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
z_table_transform = [-1.645, -1.28, -1.035, -0.84, -0.675, -0.525, -0.385, -0.253, -0.125, 0, 0.125, 0.253, 0.385, 0.525, 0.675, 0.84, 1.035, 1.28, 1.645]

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
