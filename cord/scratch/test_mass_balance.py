import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd

cfs_tafd = 2.29568411*10**-5 * 86400 / 1000

df = pd.read_csv('../data/cord-data.csv', index_col=0, parse_dates=True)

# df = df['10-01-2005':]

for k in ['ORO', 'SHA', 'FOL']:
  dSdt = df[k+'_storage'].diff()
  df[k+'_in'].plot()
  df[k+'_in'] = dSdt/cfs_tafd + df[k+'_out'] + df[k+'_evap']
  df[k+'_in'].plot()
  dSdt = (df[k+'_in'] - df[k+'_out'] - df[k+'_evap']) * cfs_tafd
  # df[k+'_storage'].plot() 
  # (df[k+'_storage'].iloc[0] + dSdt.cumsum()).plot()
  plt.show()