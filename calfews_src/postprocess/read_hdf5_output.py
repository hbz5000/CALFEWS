import numpy as np
import pandas as pd
import h5py
import json
import matplotlib.pyplot as plt
from itertools import compress
import calfews_src

# results hdf5 file location
output_file = 'calfews_src/data/results/baseline_wy2017/p0/results.hdf5'
#output_file = "C:/Users/km663/Documents/Papers/ErrorPropagation/CALFEWS__Feb2020/ORCA_COMBINED-master/ORCA_COMBINED-master/calfews_src/data/results/baseline_wy2017/p0"

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
    # f = h5py.File(results_file, 'r')
    data = f['s0']
    names = data.attrs['columns']
    names = list(map(lambda x: str(x).split("'")[1], names))
    df_data = pd.DataFrame(data[:, list(compress(np.arange(len(names)), list(map(lambda x: x == column_name, names))))], columns=['s0'])
    sensitivity_factor_values = data.attrs['sensitivity_factor_values']
    for s in f.keys():
      if (s != 's0'):
        data = f[s]
        names = data.attrs['columns']
        names = list(map(lambda x: str(x).split("'")[1], names))
        df_data[s] = pd.DataFrame(data[:, list(compress(np.arange(len(names)), list(map(lambda x: x == column_name, names))))])
        sensitivity_factor_values = np.append(sensitivity_factor_values, data.attrs['sensitivity_factor_values'])
    sensitivity_factor_values = np.reshape(sensitivity_factor_values, [len(list(f.keys())), len(data.attrs['sensitivity_factor_values'])])
    sensitivity_factors = data.attrs['sensitivity_factors']
    sensitivity_factors = list(map(lambda x: str(x).split("'")[1], sensitivity_factors))
    df_sensitivity_factors = pd.DataFrame(sensitivity_factor_values, columns=sensitivity_factors)
  return df_data, df_sensitivity_factors

def make_district_revenue(numYears):
  modelno = pd.read_pickle('calfews_src/data/results/baseline_wy2017/p0/modelno0.pkl')
  modelso = pd.read_pickle('calfews_src/data/results/baseline_wy2017/p0/modelso0.pkl')
  district_prices = pd.read_csv('calfews_src\postprocess\district_water_prices.csv')
  district_prices.set_index('PMPDKEY', inplace = True)
  district_pmp_keys = {}
  district_pmp_keys['D02'] = 'kerndelta'
  district_pmp_keys['D03'] = 'wheeler'
  district_pmp_keys['D04'] = 'westkern'
  district_pmp_keys['D01'] = 'belridge'
  district_pmp_keys['D05'] = 'berrenda'
  district_pmp_keys['D06'] = 'semitropic'
  district_pmp_keys['D07'] = 'rosedale'
  district_pmp_keys['D08'] = 'buenavista'
  district_pmp_keys['D09'] = 'cawelo'
  district_pmp_keys['D10'] = 'henrymiller'
  district_pmp_keys['D11'] = 'losthills'
  district_pmp_keys['fk13'] = 'tulare'
  district_pmp_keys['fk08'] = 'saucelito'
  district_pmp_keys['fk01'] = 'delano'
  district_pmp_keys['fk06'] = 'lowertule'
  district_pmp_keys['fk03'] = 'kerntulare'
  district_pmp_keys['fk05'] = 'lindsay'
  district_pmp_keys['fk02'] = 'exeter'
  district_pmp_keys['fk04'] = 'lindmore'
  district_pmp_keys['fk07'] = 'porterville'
  district_pmp_keys['fk11'] = 'teapot'
  district_pmp_keys['fk12'] = 'terra'
  district_pmp_keys['fk13'] = 'sosanjoaquin'
  district_pmp_keys['fk09'] = 'shaffer'
  district_pmp_keys['ot2'] = 'northkern'
  district_pmp_keys['ot1'] = 'dudleyridge'
  df_data_by_sensitivity_number, df_factors_by_sensitivity_number = get_results_sensitivity_number(output_file, 0)
  dayNum = -1
  leapCount = 0
  end_of_year = np.zeros(numYears)
  for yearNum in range(0, numYears):
    dayNum += 365
    leapCount += 1
    if leapCount == 4:
      leapCount = 0
      dayNum += 1
    end_of_year[yearNum] = dayNum
  for xx in df_data_by_sensitivity_number:
    print(xx)
  for x in district_pmp_keys:
    direct_deliveries = np.zeros(numYears)
    use_bank = np.zeros(numYears)
    sell_bank = np.zeros(numYears)
    district_position = district_prices.loc[x]
    water_price = district_position['PMPWCST']
    for contract in modelso.__getattribute__(district_pmp_keys[x]).contract_list:
      for output in ['delivery', 'carryover', 'flood']:          # list district outputs, for contract/right allocations
        output_key = district_pmp_keys[x] + '_' + contract + '_' + output
        if output_key in df_data_by_sensitivity_number:
          type_value = df_data_by_sensitivity_number[output_key]
          for yearNum in range(0, len(end_of_year)):
            direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]
	
    for output in ['inleiu_recharge', 'leiupumping']:
      output_key = district_pmp_keys[x] + '_' + output
      if output_key in df_data_by_sensitivity_number:
        type_value = df_data_by_sensitivity_number[output_key]
        for yearNum in range(0, len(end_of_year)):
          sell_bank[yearNum] += type_value[end_of_year[yearNum]]
    	
    output_key = district_pmp_keys[x] + '_recover_banked'
    if output_key in df_data_by_sensitivity_number:
      type_value = df_data_by_sensitivity_number[output_key]
      for yearNum in range(0, len(end_of_year)):
        direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]
        use_bank[yearNum] += type_value[end_of_year[yearNum]]
    
    output_key = district_pmp_keys[x] + '_inleiu_irrigation'
    if output_key in df_data_by_sensitivity_number:
      type_value = df_data_by_sensitivity_number[output_key]
      for yearNum in range(0, len(end_of_year)):
        direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]
        sell_bank[yearNum] += type_value[end_of_year[yearNum]]
         
    output_key = district_pmp_keys[x] + '_exchanged_SW'
    if output_key in df_data_by_sensitivity_number:
      type_value = df_data_by_sensitivity_number[output_key]
      for yearNum in range(0, len(end_of_year)):
        direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]
    
    for output in ['recharged', 'exchanged_GW']:
      output_key = district_pmp_keys[x] + '_' + output   	  
      if output_key in df_data_by_sensitivity_number:
        type_value = df_data_by_sensitivity_number[output_key]
        for yearNum in range(0, len(end_of_year)):
          direct_deliveries[yearNum] -= type_value[end_of_year[yearNum]]
          direct_deliveries[yearNum] = max(direct_deliveries[yearNum], 0.0)
	
    	
make_district_revenue(20)    	
df_data_by_sensitivity_number, df_factors_by_sensitivity_number = get_results_sensitivity_number(output_file, 0)
df_data_by_column, df_factors_by_column = get_results_column_name(output_file, 'shasta_Q')
# df_data_by_column.to_csv('C:/Users/Andrew/Documents/DataFilesNonGit/keyvan_sensitivity/baseline_wy2017_10272019/shasta_Q.csv')
# df_factors_by_column.to_csv('C:/Users/Andrew/Documents/DataFilesNonGit/keyvan_sensitivity/baseline_wy2017_10272019/sensitivity_factors.csv')

fig1 = plt.figure()
for s in range(4):
  df_data_by_column, df_factors_by_column = get_results_column_name(output_file,
                                                                    'lowertule__deliveries__friant1_delivery')
  print(df_factors_by_column)
  for x in df_data_by_column:
    print(x)
    print(df_data_by_column[x])
  plt.plot(df_data_by_column['s' + str(s)])
plt.show()

fig2 = plt.figure()
for c in ['lowertule__deliveries__friant1_delivery', 'lowertule__deliveries__friant1_flood', 'lowertule__deliveries__friant2_delivery', 'lowertule__deliveries__tule_flood', 'lowertule__deliveries__kaweah_flood', 'lowertule__deliveries__kings_flood']:
  df_data_by_sensitivity_number, df_factors_by_sensitivity_number = get_results_sensitivity_number(output_file, 0)
  print(df_factors_by_sensitivity_number)
  for x in df_data_by_sensitivity_number:
    print(x)
    print(df_data_by_sensitivity_number[x])
  plt.plot(df_data_by_sensitivity_number[c])
plt.show()


#################################################
### output from climate ensemble to go into CAPOW
#################################################
data_folder = 'C:/Users/Andrew/Documents/DataFilesNonGit/CALFEWS_climate_ensemble/'

# given a particular column name (e.g. shasta__baseline_inf, lowertule__deliveries__friant1_delivery), get results from each sensitivity factor sample and combine into one dataframe
reservoirs = ['shasta','oroville','yuba','folsom','newmelones','donpedro','exchequer']#,'millerton','isabella','success','kaweah','pineflat']
timeseries = ['R','Q','SNPK','fnf']
results_file = data_folder + 'results.hdf5'
with h5py.File(results_file, 'r') as f:
  f = h5py.File(results_file, 'r')
  for key in list(f.keys()):
    data = f[key]
    names = data.attrs['columns']
    names = list(map(lambda x: str(x).split("'")[1], names))
    names_wanted = []
    cols_wanted = []
    for r in reservoirs:
      for t in timeseries:
        names_wanted.append(r + '_' + t)
        cols_wanted.append(np.where(list(map(lambda x: x == (r + '_' + t), names)))[0][0])
    index = pd.to_datetime(['1950-10-01','2099-09-30'])
    df_data = pd.DataFrame(data[:, cols_wanted], columns=names_wanted, index=pd.DatetimeIndex(start='1950-10-01', end='2099-09-30', freq='D'))
    df_data.to_csv(data_folder + key + '.csv')



