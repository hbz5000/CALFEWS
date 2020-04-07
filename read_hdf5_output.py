import numpy as np
import pandas as pd
import h5py
import json
import matplotlib.pyplot as plt
from itertools import compress
import cord

# results hdf5 file location
output_file = 'cord/data/results/baseline_wy2017/p0/results_p0.hdf5'
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
for x in df_data:
  fix, ax = plt.subplots()
  ax.plot(df_data[x])
  ax.set_ylabel(x)
  plt.show()
