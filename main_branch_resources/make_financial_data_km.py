# change input file names
# adjust number of years 
import numpy as np
import pandas as pd
import h5py
import json
import matplotlib.pyplot as plt
from itertools import compress
import calfews_src
#from read_hdf5_output import get_results_sensitivity_number
import seaborn as sns
import os
import pickle


os.chdir('C:/Users/km663/Documents/Papers/ErrorPropagation/CALFEWS__Feb2020/ORCA_COMBINED-master/ORCA_COMBINED-master')
sns.set_style('darkgrid')

def set_district_keys():
  ##this creates the index to compare PMP district codes with CALFEWS output keys
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
  
  return district_pmp_keys

  
def calculate_district_reveneues(year_range, sensitivity_range, district_display_key, district_pmp_keys):
  
  ###district delivery data are cumulative through each year, to find annual tota
  ###we need an index of the last day in each year
  numYears = len(year_range)
  fig, ax = plt.subplots()
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
  
  #with open('calfews_src/data/results/baseline_wy2017/p0/modelso0.pkl', 'rb') as f:
  #   pickle.load(f)
  #read model data (so we know district contracts, etc..)
 # modelno = pd.read_pickle('calfews_src/data/results/baseline_wy2017_DryYearAdded/p0/modelno0.pkl')
  #modelso = pd.read_pickle('calfews_src/data/results/baseline_wy2017_DryYearAdded/p0/modelso0.pkl')
#  modelno = pd.read_pickle('calfews_src/data/results/baseline_wy2017_GWCorrected/p0/modelno0.pkl')
#  modelso = pd.read_pickle('calfews_src/data/results/baseline_wy2017_GWCorrected/p0/modelso0.pkl')
  #modelno = pd.read_pickle('calfews_src/data/results/baseline_wy2017_NoGWCorrection/p0/modelno0.pkl')
  #modelso = pd.read_pickle('calfews_src/data/results/baseline_wy2017_NoGWCorrection/p0/modelso0.pkl')
  modelno = pd.read_pickle('calfews_src/data/results/baseline_wy2017_bias_corrected/p0/modelno0.pkl')
  modelso = pd.read_pickle('calfews_src/data/results/baseline_wy2017_bias_corrected/p0/modelso0.pkl')
  #read price data from PMP
  district_prices = pd.read_csv('calfews_src/postprocess/district_water_prices.csv')
  district_prices.set_index('PMPDKEY', inplace = True)
  banking_price = 50.0#volumetric rate to deliver water to a bank
  #create dictionary to store annual district revenues
  district_revenues = {}
  for x in district_pmp_keys:
    district_revenues[x] = np.zeros((numYears, len(sensitivity_range)))
	
  #read CALFEWS output data
  
  #output_file = 'calfews_src/data/results/baseline_wy2017_GWCorrected/p0/results_p0.hdf5'
  output_file = 'calfews_src/data/results/baseline_wy2017_bias_corrected/p0/results_p0.hdf5'
  revenues_save_file = {}
  for sensitivity_realization in sensitivity_range:
    print("sensitivity_realization =",sensitivity_realization)
    #read CALFEWS output by sensitivity run
    df_data_by_sensitivity_number, df_factors_by_sensitivity_number = get_results_sensitivity_number(output_file, sensitivity_realization)
    for x in district_pmp_keys:
      ##FOR EACH DISTRICT - REVENUES
      direct_deliveries = np.zeros(numYears)##direct deliveries - revenue to district 
      use_bank = np.zeros(numYears)##district banked/recovered their water at another's bank (cost to district)
      sell_bank = np.zeros(numYears)##district banked/recovered another's water at their bank (revenue to district)
      #find district's price to their customers
      district_position = district_prices.loc[x]
      water_price = district_position['PMPWCST']
	  
      #Deliveries made directly to customers (not accounting for seasonal price changes)
      for contract in modelso.__getattribute__(district_pmp_keys[x]).contract_list:
        for output in ['delivery', 'carryover', 'flood']:          # list district outputs, for contract/right allocations
          output_key = district_pmp_keys[x] + '_' + contract + '_' + output
          if output_key in df_data_by_sensitivity_number:
            type_value = df_data_by_sensitivity_number[output_key]
            for yearNum in range(0, len(end_of_year)):
              direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]

      #Recharged water is not delivered to customers (but it is counted in above deliveries), so no revenue is generated
      output_key = district_pmp_keys[x] + '_recharged'   	  
      if output_key in df_data_by_sensitivity_number:
        type_value = df_data_by_sensitivity_number[output_key]
        for yearNum in range(0, len(end_of_year)):
          direct_deliveries[yearNum] -= type_value[end_of_year[yearNum]]
          direct_deliveries[yearNum] = max(direct_deliveries[yearNum], 0.0)
	
      #Deliveries/withdrawals from district bank by banking partners (revenue generating)
      for output in ['inleiu_recharge', 'leiupumping']:
        output_key = district_pmp_keys[x] + '_' + output
        if output_key in df_data_by_sensitivity_number:
          type_value = df_data_by_sensitivity_number[output_key]
          for yearNum in range(0, len(end_of_year)):
            sell_bank[yearNum] += type_value[end_of_year[yearNum]]
    	
      #Deliveries to district bank by banking partners (revenue generating) PLUS irrigation sale to in-district customer
      output_key = district_pmp_keys[x] + '_inleiu_irrigation'
      if output_key in df_data_by_sensitivity_number:
        type_value = df_data_by_sensitivity_number[output_key]
        for yearNum in range(0, len(end_of_year)):
          direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]
          sell_bank[yearNum] += type_value[end_of_year[yearNum]]
		  
      ##Withdrawals from out-of-district bank by district (cost generating), delivered to customers (revenue generating)      
      output_key = district_pmp_keys[x] + '_recover_banked'
      if output_key in df_data_by_sensitivity_number:
        type_value = df_data_by_sensitivity_number[output_key]
        for yearNum in range(0, len(end_of_year)):
          direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]
          use_bank[yearNum] += type_value[end_of_year[yearNum]]
    
      ##Withdrawals from out-of-district bank by district (cost generating), exchanged with another district (revenue is already counted under contract delivery)
      output_key = district_pmp_keys[x] + '_exchanged_GW'
      if output_key in df_data_by_sensitivity_number:
        type_value = df_data_by_sensitivity_number[output_key]
        for yearNum in range(0, len(end_of_year)):
          use_bank[yearNum] += type_value[end_of_year[yearNum]]
    
      #Recovered groundwater from another district delivered to district customers (revenue generating) that was exchanged for district surface water
      output_key = district_pmp_keys[x] + '_exchanged_SW'
      if output_key in df_data_by_sensitivity_number:
        type_value = df_data_by_sensitivity_number[output_key]
        for yearNum in range(0, len(end_of_year)):
          direct_deliveries[yearNum] += type_value[end_of_year[yearNum]]
      

      if district_display_key == district_pmp_keys[x]:
        total_revenues = (direct_deliveries * water_price + sell_bank * banking_price - use_bank * banking_price)/1000.0#total revenue in million $
        ax.plot(year_range, total_revenues)
        revenues_save_file['S' + str(sensitivity_realization)] = total_revenues
        del total_revenues
  revenues_save_file = pd.DataFrame(revenues_save_file, index = year_range)
  revenues_save_file.to_csv('calfews_src/data/results/Financial_output/BC/' + district_display_key + '_revenues.csv')
  ax.set_xlim((min(year_range), max(year_range)))
  ax.set_xticks(np.arange(min(year_range), max(year_range), np.round(len(year_range)/10)))
  ax.set_ylabel('Total Irrigation District Revenue, Banking and Deliveries')
  plt.show()      
	  
district_pmp_keys = set_district_keys()
#year_range = np.arange(1997, 2017)
year_range = np.arange(2007, 2017)
sensitivity_range = np.arange(1)
district_display_key = 'semitropic'

calculate_district_reveneues(year_range, sensitivity_range, district_display_key, district_pmp_keys)

for x_dist in district_pmp_keys:
    print(district_pmp_keys[x_dist])
    district_display_key = district_pmp_keys[x_dist]
    calculate_district_reveneues(year_range, sensitivity_range, district_display_key, district_pmp_keys)
