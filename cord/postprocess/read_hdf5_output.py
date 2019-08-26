import numpy as np
import pandas as pd
import h5py
import json
import matplotlib.pyplot as plt
from itertools import compress

# given a particular sensitivity factor sample number, get entire model output and output as dataframe
def get_results_sensitivity_number(results_file, sensitivity_number):
  with h5py.File(results_file, 'r') as f:
    data = f['sample_' + str(sensitivity_number)]
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
    data = f['sample_0']
    names = data.attrs['columns']
    names = list(map(lambda x: str(x).split("'")[1], names))
    df_data = pd.DataFrame(data[:, list(compress(np.arange(len(names)), list(map(lambda x: x == column_name, names))))], columns=['sample_0'])
    sensitivity_factor_values = data.attrs['sensitivity_factor_values']
    for s in range(1,len(list(f.keys()))):
      data = f['sample_' + str(s)]
      names = data.attrs['columns']
      names = list(map(lambda x: str(x).split("'")[1], names))
      df_data['sample_' + str(s)] = pd.DataFrame(data[:, list(compress(np.arange(len(names)), list(map(lambda x: x == column_name, names))))])
      sensitivity_factor_values = np.append(sensitivity_factor_values, data.attrs['sensitivity_factor_values'])
    sensitivity_factor_values = np.reshape(sensitivity_factor_values, [len(list(f.keys())), len(data.attrs['sensitivity_factor_values'])])
    sensitivity_factors = data.attrs['sensitivity_factors']
    sensitivity_factors = list(map(lambda x: str(x).split("'")[1], sensitivity_factors))
    df_sensitivity_factors = pd.DataFrame(sensitivity_factor_values, columns=sensitivity_factors)
  return df_data, df_sensitivity_factors

df_data_by_sensitivity_number, df_factors_by_sensitivity_number = get_results_sensitivity_number('cord/data/results/baseline_wy2017/results.hdf5', 0)

df_data_by_column, df_factors_by_column = get_results_column_name('cord/data/results/baseline_wy2017/results.hdf5', 'lowertule__deliveries__friant1_delivery')


fig1 = plt.figure()
for s in range(30):
  df_data_by_column, df_factors_by_column = get_results_column_name('cord/data/results/baseline_wy2017/results.hdf5',
                                                                    'lowertule__deliveries__friant1_delivery')
  plt.plot(df_data_by_column['sample_' + str(s)])


fig2 = plt.figure()
for c in ['lowertule__deliveries__friant1_delivery', 'lowertule__deliveries__friant1_flood', 'lowertule__deliveries__friant2_delivery', 'lowertule__deliveries__tule_flood', 'lowertule__deliveries__kaweah_flood', 'lowertule__deliveries__kings_flood']:
  df_data_by_sensitivity_number, df_factors_by_sensitivity_number = get_results_sensitivity_number('cord/data/results/baseline_wy2017/results.hdf5', 0)
  plt.plot(df_data_by_sensitivity_number[c])



