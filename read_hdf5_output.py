import numpy as np
import pandas as pd
import h5py
import json
import matplotlib.pyplot as plt
from itertools import compress
import cord

# results hdf5 file location
output_file = 'cord/data/results/results_obs.hdf5'
output_file2 = 'cord/data/results/results_AR_1_5.hdf5'
output_file3 = 'cord/data/results/results_AR_0_5.hdf5'
#output_file = "C:/Users/km663/Documents/Papers/ErrorPropagation/CALFEWS__Feb2020/ORCA_COMBINED-master/ORCA_COMBINED-master/cord/data/results/baseline_wy2017/p0/results.hdf5"


# given a particular sensitivity factor sample number, get entire model output and output as dataframe
def get_results_sensitivity_number(results_file, sensitivity_number):
  with h5py.File(results_file, 'r') as f:
    data = f['s' + str(sensitivity_number)]
    names = data.attrs['columns']
    names = list(map(lambda x: str(x).split("'")[1], names))
    df_data = pd.DataFrame(data[:], columns=names)
    sensitivity_factors = data.attrs['sensitivity_factors']
    sensitivity_factors = list(map(lambda x: str(x).split("'")[1], sensitivity_factors))
    sensitivity_factor_values = data.attrs['sensitivity_factor_values']
    df_sensitivity_factors = pd.DataFrame(sensitivity_factor_values).transpose()
    df_sensitivity_factors.columns = sensitivity_factors
    return df_data, df_sensitivity_factors

# given a particular column name (e.g. shasta__baseline_inf, lowertule__deliveries__friant1_delivery), get results from each sensitivity factor sample and combine into one dataframe
def get_results_column_name(results_file, column_name):
  with h5py.File(results_file, 'r') as f:
    f = h5py.File(results_file, 'r')
    data = f['s0']
    names = data.attrs['columns']
    names = list(map(lambda x: str(x).split("'")[1], names))
    df_data = pd.DataFrame(data[:, list(compress(np.arange(len(names)), list(map(lambda x: x == column_name, names))))], columns=['s0'])
    sensitivity_factor_values = data.attrs['sensitivity_factor_values']
    for s in range(1,len(list(f.keys()))):
      data = f['s' + str(s)]
      names = data.attrs['columns']
      names = list(map(lambda x: str(x).split("'")[1], names))
      df_data['s' + str(s)] = pd.DataFrame(data[:, list(compress(np.arange(len(names)), list(map(lambda x: x == column_name, names))))])
      sensitivity_factor_values = np.append(sensitivity_factor_values, data.attrs['sensitivity_factor_values'])
    sensitivity_factor_values = np.reshape(sensitivity_factor_values, [len(list(f.keys())), len(data.attrs['sensitivity_factor_values'])])
    sensitivity_factors = data.attrs['sensitivity_factors']
    sensitivity_factors = list(map(lambda x: str(x).split("'")[1], sensitivity_factors))
    df_sensitivity_factors = pd.DataFrame(sensitivity_factor_values, columns=sensitivity_factors)
  return df_data, df_sensitivity_factors

df_data, df_sensitivity_factors = get_results_sensitivity_number(output_file, 0)
df_data2, df_sensitivity_factors = get_results_sensitivity_number(output_file2, 0)
df_data3, df_sensitivity_factors = get_results_sensitivity_number(output_file3, 0)
item_list = ['oroville_Q', 'delta_HRO_pump', 'sanluisstate_S', 'swpdelta_allocation', 'swpdelta_contract', 'metropolitan_tableA_projected', 'metropolitan_tableA_delivery', 'metropolitan_tableA_carryover', 'metropolitan_exchanged_GW', 'metropolitan_recover_banked', 'metropolitan_exchanged_SW']
columns = 2
fig, ax = plt.subplots(int(np.ceil(len(item_list)/2.0)), columns)
row_cnt = 0
col_cnt = 0

for x in item_list:
  ax[row_cnt][col_cnt].plot(df_data[x], color = 'r')
  ax[row_cnt][col_cnt].plot(df_data2[x], color = 'b')
  ax[row_cnt][col_cnt].plot(df_data3[x], color = 'g')
  ax[row_cnt][col_cnt].set_title(x)
  ax[row_cnt][col_cnt].set_xticklabels('')
  ax[row_cnt][col_cnt].set_ylim([0, max(df_data[x][1000:])])
  row_cnt += 1
  if row_cnt > len(item_list)/columns:
    row_cnt = 0
    col_cnt += 1 
plt.tight_layout()
plt.show()
plt.close()