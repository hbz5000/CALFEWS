import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import math 
import scipy.stats as stats
from matplotlib import gridspec
from matplotlib.lines import Line2D
from .util import *
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter
import matplotlib.pylab as pl
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from .sanker import Sanker
import imageio

class Visualizer():

  def __init__(self, district_list, private_list, city_list, contract_list, bank_list, leiu_list):

    self.district_list = district_list.copy()
    self.private_list = private_list.copy()
    for x in city_list:
      self.private_list.append(x)
    self.contract_list = contract_list
    self.bank_list = bank_list
    self.leiu_list = leiu_list
    self.private_districts = {}
    for x in self.private_list:
      self.private_districts[x.name] = []
      for xx in x.district_list:
        self.private_districts[x.name].append(xx)
    inflow_inputs = pd.read_csv('calfews_src/data/input/calfews_src-data.csv', index_col=0, parse_dates=True)
    x2_results = pd.read_csv('calfews_src/data/input/x2DAYFLOW.csv', index_col=0, parse_dates=True)
    self.observations = inflow_inputs.join(x2_results)
    self.observations['delta_outflow'] = self.observations['delta_inflow'] + self.observations['delta_depletions'] - self.observations['HRO_pump'] - self.observations['TRP_pump']

    self.index_o = self.observations.index
    self.T_o = len(self.observations)
    self.day_month_o = self.index_o.day
    self.month_o = self.index_o.month
    self.year_o = self.index_o.year
    kern_bank_observations = pd.read_csv('calfews_src/data/input/kern_water_bank_historical.csv')
    kern_bank_observations = kern_bank_observations.set_index('Year')
    semitropic_bank_observations = pd.read_csv('calfews_src/data/input/semitropic_bank_historical.csv')
    semitropic_bank_observations = semitropic_bank_observations.set_index('Year')
    total_bank_kwb = np.zeros(self.T_o)
    total_bank_smi = np.zeros(self.T_o)
    for x in range(0, self.T_o):
      if self.month_o[x] > 9:
        year_str = self.year_o[x]
      else:
        year_str = self.year_o[x] - 1
      if self.month_o[x] == 9 and self.day_month_o[x] == 30:
        year_str = self.year_o[x]
      total_bank_kwb[x] = kern_bank_observations.loc[year_str, 'Ag'] + kern_bank_observations.loc[year_str, 'Mixed Purpose']
      deposit_history = semitropic_bank_observations[semitropic_bank_observations.index <= year_str]      
      total_bank_smi[x] = deposit_history['Metropolitan'].sum() + deposit_history['South Bay'].sum()

    self.observations['kwb_accounts'] = pd.Series(total_bank_kwb, index=self.observations.index)
    self.observations['smi_accounts'] = pd.Series(total_bank_smi, index=self.observations.index)
    
  def get_results_sensitivity_number(self, results_file, sensitivity_number, start_month, start_year, start_day):
    self.values = {}
    numdays_index = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    with h5py.File(results_file, 'r') as f:
      data = f['s' + str(sensitivity_number)]
      names = data.attrs['columns']
      names = list(map(lambda x: str(x).split("'")[1], names))
      df_data = pd.DataFrame(data[:], columns=names)
      for x in df_data:
        self.values[x] = df_data[x]

    datetime_index = []
    monthcount = start_month
    yearcount = start_year
    daycount = start_day
    leapcount = np.remainder(start_year, 4)

    for t in range(0, len(self.values[x])):
      datetime_index.append(str(yearcount) + '-' + str(monthcount) + '-' + str(daycount))
      daycount += 1
      if leapcount == 0 and monthcount == 2:
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

    self.values['Datetime'] = pd.to_datetime(datetime_index) 
    self.values = pd.DataFrame(self.values)
    self.values = self.values.set_index('Datetime')
    self.index = self.values.index
    self.T = len(self.values.index)
    self.day_year = self.index.dayofyear
    self.day_month = self.index.day
    self.month = self.index.month
    self.year = self.index.year
    self.starting_year = self.index.year[0]
    self.ending_year = self.index.year[-1]
    self.number_years = self.ending_year - self.starting_year
    total_kwb_sim = np.zeros(len(self.values))
    total_smi_sim = np.zeros(len(self.values))
    for district_partner in ['DLR', 'KCWA', 'ID4', 'SMI', 'TJC', 'WON', 'WRM']:
      total_kwb_sim += self.values['kwb_' + district_partner]
    self.values['kwb_total'] = pd.Series(total_kwb_sim, index = self.values.index)
    for district_partner in ['SOB', 'MET']:
      total_smi_sim += self.values['semitropic_' + district_partner]
    self.values['smi_total'] = pd.Series(total_smi_sim, index = self.values.index)


  def set_figure_params(self):

    self.figure_params = {}


    self.figure_params['delta_pumping'] = {}
    self.figure_params['delta_pumping']['extended_simulation'] = {}
    self.figure_params['delta_pumping']['extended_simulation']['outflow_list'] =  ['delta_outflow', 'delta_outflow']
    self.figure_params['delta_pumping']['extended_simulation']['pump1_list'] =  ['delta_HRO_pump', 'HRO_pump']
    self.figure_params['delta_pumping']['extended_simulation']['pump2_list'] =  ['delta_TRP_pump', 'TRP_pump']
    self.figure_params['delta_pumping']['extended_simulation']['scenario_labels'] =  ['Model Validation', 'Extended Simulation']
    self.figure_params['delta_pumping']['extended_simulation']['simulation_labels'] =  ['delta_HRO_pump', 'delta_TRP_pump', 'delta_outflow']
    self.figure_params['delta_pumping']['extended_simulation']['observation_labels'] =  ['HRO_pump', 'TRP_pump', 'delta_outflow']
    self.figure_params['delta_pumping']['extended_simulation']['agg_list'] =  ['AS-OCT', 'AS-OCT', 'D']
    self.figure_params['delta_pumping']['extended_simulation']['unit_mult'] =  [1.0, 1.0, cfs_tafd]
    self.figure_params['delta_pumping']['extended_simulation']['max_value_list'] =  [5000, 5000, 15]       
    self.figure_params['delta_pumping']['extended_simulation']['use_log_list'] =  [False, False, True]
    self.figure_params['delta_pumping']['extended_simulation']['use_cdf_list'] =  [False, False, True]
    self.figure_params['delta_pumping']['extended_simulation']['scenario_type_list'] =  ['observation', 'validation', 'scenario']
    self.figure_params['delta_pumping']['extended_simulation']['x_label_list'] = ['Total Pumping, SWP Delta Pumps (tAF/year)', 'Total Pumping, CVP Delta Pumps (tAF/year)', 'Daily Exceedence Probability', '']
    self.figure_params['delta_pumping']['extended_simulation']['y_label_list'] = ['Probability Density', 'Probability Density', 'Daily Delta Outflow (tAF)', 'Relative Frequency of Water-year Types within Simulation']
    self.figure_params['delta_pumping']['extended_simulation']['legend_label_names1'] = ['Historical (1996-2016) Observations', 'Historical (1996-2016) Model Validation', 'Extended Simulation']
    self.figure_params['delta_pumping']['extended_simulation']['legend_label_names2'] = ['Critical', 'Dry', 'Below Normal', 'Above Normal', 'Wet']

    self.figure_params['state_estimation'] = {}
    for x in ['publication', 'sacramento', 'sanjoaquin', 'tulare']:
      self.figure_params['state_estimation'][x] = {}
      self.figure_params['state_estimation'][x]['non_log'] = ['Snowpack (SWE)',]
      self.figure_params['state_estimation'][x]['predictor values'] = ['Mean Inflow, Prior 30 Days (tAF/day)','Snowpack (SWE)']
      self.figure_params['state_estimation'][x]['colorbar_label_index'] = [0, 30, 60, 90, 120, 150, 180]
      self.figure_params['state_estimation'][x]['colorbar_label_list'] = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'] 
      self.figure_params['state_estimation'][x]['subplot_annotations'] = ['A', 'B', 'C', 'D']
      self.figure_params['state_estimation'][x]['forecast_periods'] = [30,'SNOWMELT']
      self.figure_params['state_estimation'][x]['all_cols'] = ['DOWY', 'Snowpack', '30MA']
      self.figure_params['state_estimation'][x]['forecast_values'] = []
      for forecast_days in self.figure_params['state_estimation'][x]['forecast_periods']:
        if forecast_days == 'SNOWMELT':
          self.figure_params['state_estimation'][x]['forecast_values'].append('Flow Estimation, Snowmelt Season (tAF)')
          self.figure_params['state_estimation'][x]['all_cols'].append('Snowmelt Flow')
        else:  
          self.figure_params['state_estimation'][x]['forecast_values'].append('Flow Estimation, Next ' + str(forecast_days) + ' Days (tAF)')
          self.figure_params['state_estimation'][x]['all_cols'].append(str(forecast_days) + ' Day Flow')

    self.figure_params['state_estimation']['publication']['watershed_keys'] = ['SHA', 'ORO', 'MIL', 'ISB']
    self.figure_params['state_estimation']['publication']['watershed_labels'] = ['Shasta', 'Oroville', 'Millerton', 'Isabella']

    self.figure_params['state_estimation']['sacramento']['watershed_keys'] = ['SHA', 'ORO', 'FOL', 'YRS']
    self.figure_params['state_estimation']['sacramento']['watershed_labels'] = ['Shasta', 'Oroville', 'Folsom', 'New Bullards Bar']

    self.figure_params['state_estimation']['sanjoaquin']['watershed_keys'] = ['NML', 'DNP', 'EXC', 'MIL']
    self.figure_params['state_estimation']['sanjoaquin']['watershed_labels'] = ['New Melones', 'Don Pedro', 'Exchequer', 'Millerton']

    self.figure_params['state_estimation']['tulare']['watershed_keys'] = ['PFT', 'KWH', 'SUC', 'ISB']
    self.figure_params['state_estimation']['tulare']['watershed_labels'] = ['Pine Flat', 'Kaweah', 'Success', 'Isabella']

    self.figure_params['model_validation'] = {}
    for x in ['delta', 'sierra', 'sanluis', 'bank']:
      self.figure_params['model_validation'][x] = {}
    
    self.figure_params['model_validation']['delta']['title_labels'] = ['State Water Project Pumping', 'Central Valley Project Pumping', 'Delta X2 Location']
    num_subplots = len(self.figure_params['model_validation']['delta']['title_labels'])
    self.figure_params['model_validation']['delta']['label_name_1'] = ['delta_HRO_pump', 'delta_TRP_pump', 'delta_x2']
    self.figure_params['model_validation']['delta']['label_name_2'] = ['HRO_pump', 'TRP_pump', 'DAY_X2']
    self.figure_params['model_validation']['delta']['unit_converstion_1'] = [1.0, 1.0, 1.0]
    self.figure_params['model_validation']['delta']['unit_converstion_2'] = [cfs_tafd, cfs_tafd, 1.0]
    self.figure_params['model_validation']['delta']['y_label_timeseries'] = ['Pumping (tAF/week)', 'Pumping (tAF/week)', 'X2 inland distance (km)']
    self.figure_params['model_validation']['delta']['y_label_scatter'] = ['(tAF/yr)', '(tAF/yr)', '(km)']
    self.figure_params['model_validation']['delta']['timeseries_timestep'] = ['W', 'W', 'W']
    self.figure_params['model_validation']['delta']['scatter_timestep'] = ['AS-OCT', 'AS-OCT', 'M']
    self.figure_params['model_validation']['delta']['aggregation_methods'] = ['sum', 'sum', 'mean']
    self.figure_params['model_validation']['delta']['notation_location'] = ['top'] * num_subplots
    self.figure_params['model_validation']['delta']['show_legend'] = [True] * num_subplots

    self.figure_params['model_validation']['sierra']['title_labels'] = ['Shasta', 'Oroville', 'Folsom', 'New Bullards Bar', 'New Melones', 'Don Pedro', 'Exchequer', 'Millerton', 'Pine Flat', 'Kaweah', 'Success', 'Isabella']
    num_subplots = len(self.figure_params['model_validation']['sierra']['title_labels'])
    self.figure_params['model_validation']['sierra']['label_name_1'] = ['shasta_S', 'oroville_S', 'folsom_S', 'yuba_S', 'newmelones_S', 'donpedro_S', 'exchequer_S', 'millerton_S', 'pineflat_S', 'kaweah_S', 'success_S', 'isabella_S']
    self.figure_params['model_validation']['sierra']['label_name_2'] = ['SHA_storage', 'ORO_storage', 'FOL_storage', 'YRS_storage', 'NML_storage', 'DNP_storage', 'EXC_storage', 'MIL_storage', 'PFT_storage', 'KWH_storage', 'SUC_storage', 'ISB_storage']
    self.figure_params['model_validation']['sierra']['unit_converstion_1'] = [1.0/1000.0] * num_subplots
    self.figure_params['model_validation']['sierra']['unit_converstion_2'] = [1.0/1000000.0] * num_subplots
    self.figure_params['model_validation']['sierra']['y_label_timeseries'] = ['Storage (mAF)'] * num_subplots
    self.figure_params['model_validation']['sierra']['y_label_scatter'] = []
    self.figure_params['model_validation']['sierra']['timeseries_timestep'] = ['W'] * num_subplots
    self.figure_params['model_validation']['sierra']['scatter_timestep'] = []
    self.figure_params['model_validation']['sierra']['aggregation_methods'] = ['mean'] * num_subplots
    self.figure_params['model_validation']['sierra']['notation_location'] = ['bottom'] * num_subplots
    self.figure_params['model_validation']['sierra']['show_legend'] = [False] * num_subplots
    counter_kaweah = self.figure_params['model_validation']['sierra']['title_labels'].index('Kaweah')
    counter_success = self.figure_params['model_validation']['sierra']['title_labels'].index('Success')
    counter_isabella = self.figure_params['model_validation']['sierra']['title_labels'].index('Isabella')
    self.figure_params['model_validation']['sierra']['notation_location'][counter_kaweah] = 'top'  
    self.figure_params['model_validation']['sierra']['notation_location'][counter_success] = 'topright'  
    self.figure_params['model_validation']['sierra']['show_legend'][counter_isabella] = True  

    self.figure_params['model_validation']['sanluis']['title_labels'] = ['State (SWP) Portion, San Luis Reservoir', 'Federal (CVP) Portion, San Luis Reservoir']
    num_subplots = len(self.figure_params['model_validation']['sanluis']['title_labels'])
    self.figure_params['model_validation']['sanluis']['label_name_1'] = ['sanluisstate_S', 'sanluisfederal_S']
    self.figure_params['model_validation']['sanluis']['label_name_2'] = ['SLS_storage', 'SLF_storage']
    self.figure_params['model_validation']['sanluis']['unit_converstion_1'] = [1.0/1000.0] * num_subplots
    self.figure_params['model_validation']['sanluis']['unit_converstion_2'] = [1.0/1000000.0] * num_subplots
    self.figure_params['model_validation']['sanluis']['y_label_timeseries'] = ['Storage (mAF)'] * num_subplots
    self.figure_params['model_validation']['sanluis']['y_label_scatter'] = ['(mAF)'] * num_subplots
    self.figure_params['model_validation']['sanluis']['timeseries_timestep'] = ['W'] * num_subplots
    self.figure_params['model_validation']['sanluis']['scatter_timestep'] = ['M'] * num_subplots
    self.figure_params['model_validation']['sanluis']['aggregation_methods'] = ['point'] * num_subplots
    self.figure_params['model_validation']['sanluis']['notation_location'] = ['top'] * num_subplots
    self.figure_params['model_validation']['sanluis']['show_legend'] = [True] * num_subplots

    self.figure_params['model_validation']['bank']['title_labels'] = ['Kern Water Bank Accounts', 'Semitropic Water Bank Accounts']
    num_subplots = len(self.figure_params['model_validation']['bank']['title_labels'])
    self.figure_params['model_validation']['bank']['label_name_1'] = ['kwb_total', 'smi_total']
    self.figure_params['model_validation']['bank']['label_name_2'] = ['kwb_accounts', 'smi_accounts']
    self.figure_params['model_validation']['bank']['unit_converstion_1'] = [1.0/1000.0] * num_subplots
    self.figure_params['model_validation']['bank']['unit_converstion_2'] = [1.0/1000000.0, 1.0/1000.0]
    self.figure_params['model_validation']['bank']['y_label_timeseries'] = ['Storage (mAF)'] * num_subplots
    self.figure_params['model_validation']['bank']['y_label_scatter'] = ['(mAF)'] * num_subplots
    self.figure_params['model_validation']['bank']['timeseries_timestep'] = ['W'] * num_subplots
    self.figure_params['model_validation']['bank']['scatter_timestep'] = ['AS-OCT'] * num_subplots
    self.figure_params['model_validation']['bank']['aggregation_methods'] = ['change'] * num_subplots
    self.figure_params['model_validation']['bank']['notation_location'] = ['top'] * num_subplots
    self.figure_params['model_validation']['bank']['show_legend'] = [False] * num_subplots
    self.figure_params['model_validation']['bank']['show_legend'][0] = True

    self.figure_params['state_response'] = {}
    self.figure_params['state_response']['sanluisstate_losthills'] = {}
    self.figure_params['state_response']['sanluisstate_losthills']['contract_list'] = ['swpdelta',]
    self.figure_params['state_response']['sanluisstate_losthills']['contributing_reservoirs'] = ['delta_uncontrolled_swp', 'oroville', 'yuba']
    self.figure_params['state_response']['sanluisstate_losthills']['groundwater_account_names'] = ['LHL','WON']
    self.figure_params['state_response']['sanluisstate_losthills']['reservoir_features'] = ['S', 'days_til_full', 'flood_deliveries'] 
    self.figure_params['state_response']['sanluisstate_losthills']['reservoir_feature_colors'] = ['teal', '#3A506B', '#74B3CE', 'steelblue'] 
    self.figure_params['state_response']['sanluisstate_losthills']['district_contracts'] = ['tableA',]
    self.figure_params['state_response']['sanluisstate_losthills']['subplot_titles'] = ['State Water Project Delta Operations', 'Lost Hills Drought Management', 'San Luis Reservoir Operations', 'Lost Hills Flood Management']
    self.figure_params['state_response']['sanluisstate_losthills']['legend_list_1'] = ['Y.T.D Delta Pumping', 'Projected Unstored Exports', 'Projected Stored Exports, Oroville', 'Projected Stored Exports, New Bullards']
    self.figure_params['state_response']['sanluisstate_losthills']['legend_list_2'] = ['Storage', 'Projected Days to Fill', 'Flood Release Deliveries']
    self.figure_params['state_response']['sanluisstate_losthills']['legend_list_3'] = ['Remaining SW Allocation', 'SW Deliveries', 'Private GW Pumping', 'District GW Bank Recovery', 'Remaining GW Bank Recovery Capacity']
    self.figure_params['state_response']['sanluisstate_losthills']['legend_list_4'] = ['Carryover Recharge Capacity', 'Recharged from Contract Allocation' 'Recharge of Uncontrolled Flood Spills']
    
    self.figure_params['state_response'] = {}
    self.figure_params['state_response']['sanluisstate_wheeler'] = {}
    self.figure_params['state_response']['sanluisstate_wheeler']['contract_list'] = ['swpdelta',]
    self.figure_params['state_response']['sanluisstate_wheeler']['contributing_reservoirs'] = ['delta_uncontrolled_swp', 'oroville', 'yuba']
    self.figure_params['state_response']['sanluisstate_wheeler']['groundwater_account_names'] = ['WRM']
    self.figure_params['state_response']['sanluisstate_wheeler']['reservoir_features'] = ['S', 'days_til_full', 'flood_deliveries'] 
    self.figure_params['state_response']['sanluisstate_wheeler']['reservoir_feature_colors'] = ['teal', '#3A506B', '#74B3CE', 'lightsteelblue'] 
    self.figure_params['state_response']['sanluisstate_wheeler']['district_contracts'] = ['tableA',]
    self.figure_params['state_response']['sanluisstate_wheeler']['subplot_titles'] = ['State Water Project Delta Operations', 'Wheeler Ridge Drought Management', 'San Luis Reservoir Operations', 'Wheeler Ridge Flood Management']
    self.figure_params['state_response']['sanluisstate_wheeler']['legend_list_1'] = ['Y.T.D Delta Pumping', 'Projected Unstored Exports', 'Projected Stored Exports, Oroville', 'Projected Stored Exports, New Bullards']
    self.figure_params['state_response']['sanluisstate_wheeler']['legend_list_2'] = ['Storage', 'Projected Days to Fill', 'Flood Release Deliveries']
    self.figure_params['state_response']['sanluisstate_wheeler']['legend_list_3'] = ['Remaining SW Allocation', 'SW Deliveries', 'Private GW Pumping', 'District GW Bank Recovery', 'Remaining GW Bank Recovery Capacity']
    self.figure_params['state_response']['sanluisstate_wheeler']['legend_list_4'] = ['Carryover Recharge Capacity', 'Recharge of Uncontrolled Flood Spills', 'Recharged from Contract Allocation']

    self.figure_params['district_water_use'] = {}
    self.figure_params['district_water_use']['physical'] = {}
    self.figure_params['district_water_use']['physical']['district_groups'] = ['Municipal Districts', 'Kern County Water Agency', 'CVP - Friant Contractors', 'CVP - San Luis Contractors', 'Groundwater Banks']
    self.figure_params['district_water_use']['physical']['Municipal Districts'] = ['bakersfield', 'ID4', 'fresno', 'southbay', 'socal', 'centralcoast']
    self.figure_params['district_water_use']['physical']['Kern County Water Agency'] = ['berrenda', 'belridge', 'buenavista', 'cawelo', 'henrymiller', 'losthills', 'rosedale', 'semitropic', 'tehachapi', 'tejon', 'westkern', 'wheeler', 'northkern', 'kerntulare']
    self.figure_params['district_water_use']['physical']['CVP - Friant Contractors'] = ['arvin', 'delano', 'pixley', 'exeter', 'kerntulare', 'lindmore', 'lindsay', 'lowertule', 'porterville', 'saucelito', 'shaffer', 'sosanjoaquin', 'teapot', 'terra', 'chowchilla', 'maderairr', 'tulare', 'fresnoid']
    self.figure_params['district_water_use']['physical']['CVP - San Luis Contractors'] = ['westlands', 'panoche', 'sanluiswater', 'delpuerto'] 
    self.figure_params['district_water_use']['physical']['Groundwater Banks'] = ['stockdale', 'kernriverbed', 'poso', 'pioneer', 'kwb', 'b2800', 'irvineranch', 'northkernwb']
    self.figure_params['district_water_use']['physical']['subplot columns'] = 2
    self.figure_params['district_water_use']['physical']['color map'] = 'YlGbBu_r'
    self.figure_params['district_water_use']['physical']['write file'] = True

    self.figure_params['district_water_use']['account'] = {}
    self.figure_params['district_water_use']['account']['district_groups'] = ['Municipal Districts', 'Kern County Water Agency', 'CVP - Friant Contractors', 'CVP - San Luis Contractors']
    self.figure_params['district_water_use']['account']['Municipal Districts'] = ['bakersfield', 'ID4', 'fresno', 'southbay', 'socal', 'centralcoast']
    self.figure_params['district_water_use']['account']['Kern County Water Agency'] = ['berrenda', 'belridge', 'buenavista', 'cawelo', 'henrymiller', 'losthills', 'rosedale', 'semitropic', 'tehachapi', 'tejon', 'westkern', 'wheeler']
    self.figure_params['district_water_use']['account']['CVP - Friant Contractors'] = ['arvin', 'delano', 'pixley', 'exeter', 'kerntulare', 'lindmore', 'lindsay', 'lowertule', 'porterville', 'saucelito', 'shaffer', 'sosanjoaquin', 'teapot', 'terra', 'chowchilla', 'maderairr', 'tulare', 'fresnoid']
    self.figure_params['district_water_use']['account']['CVP - San Luis Contractors'] = ['westlands', 'panoche', 'sanluiswater', 'delpuerto'] 
    self.figure_params['district_water_use']['account']['subplot columns'] = 2
    self.figure_params['district_water_use']['account']['color map'] = 'BrBG_r'
    self.figure_params['district_water_use']['account']['write file'] = False

    self.figure_params['flow_diagram'] = {}
    self.figure_params['flow_diagram']['tulare'] = {}
    self.figure_params['flow_diagram']['tulare']['column1'] = ['Shasta', 'Folsom', 'Oroville', 'New Bullards', 'Uncontrolled']
    self.figure_params['flow_diagram']['tulare']['row1'] = ['Delta Outflow', 'Carryover',]
    self.figure_params['flow_diagram']['tulare']['column2'] = ['San Luis (Fed)', 'San Luis (State)', 'Millerton', 'Isabella', 'Pine Flat', 'Kaweah', 'Success']
    self.figure_params['flow_diagram']['tulare']['row2'] = ['Carryover',]
    self.figure_params['flow_diagram']['tulare']['column3'] = ['Exchange', 'CVP-Delta', 'Cross Valley', 'State Water Project', 'Friant Class 1','Friant Class 2', 'Kern River', 'Kings River', 'Kaweah River', 'Tule River', 'Flood']
    self.figure_params['flow_diagram']['tulare']['row3'] = ['Private Pumping', 'GW Banks']
    self.figure_params['flow_diagram']['tulare']['column4'] = ['Exchange', 'CVP-Delta', 'Urban', 'KCWA', 'CVP-Friant','Other']
    self.figure_params['flow_diagram']['tulare']['row4'] = ['Carryover',]
    self.figure_params['flow_diagram']['tulare']['column5'] = ['Irrigation', 'Urban', 'In-Lieu Recharge', 'Direct Recharge']
    self.figure_params['flow_diagram']['tulare']['titles'] = ['Sacramento Basin\nSupplies', 'Tulare Basin\nSupplies', 'Surface Water\nContract Allocations', 'Contractor Groups', 'Water Use Type']
    
   
  def scenario_compare(self, folder_name, figure_name, plot_name, validation_values, show_plot):


    outflow_list = self.figure_params[figure_name][plot_name]['outflow_list']
    pump1_list = self.figure_params[figure_name][plot_name]['pump1_list']
    pump2_list = self.figure_params[figure_name][plot_name]['pump2_list']
    scenario_labels = self.figure_params[figure_name][plot_name]['scenario_labels']
    simulation_labels = self.figure_params[figure_name][plot_name]['simulation_labels']
    observation_labels = self.figure_params[figure_name][plot_name]['observation_labels']
    agg_list = self.figure_params[figure_name][plot_name]['agg_list']
    unit_mult = self.figure_params[figure_name][plot_name]['unit_mult']
    max_value_list = self.figure_params[figure_name][plot_name]['max_value_list']      
    use_log_list = self.figure_params[figure_name][plot_name]['use_log_list']
    use_cdf_list = self.figure_params[figure_name][plot_name]['use_cdf_list']
    scenario_type_list = self.figure_params[figure_name][plot_name]['scenario_type_list']
    x_label_list = self.figure_params[figure_name][plot_name]['x_label_list']
    y_label_list = self.figure_params[figure_name][plot_name]['y_label_list']
    legend_label_names1 = self.figure_params[figure_name][plot_name]['legend_label_names1']
    legend_label_names2 = self.figure_params[figure_name][plot_name]['legend_label_names2']
    
    color1 = sns.color_palette('spring', n_colors = 3)
    color2 = sns.color_palette('summer', n_colors = 3)
    color_list = np.array([color1[0], color1[2], color2[0]]) 
    max_y_val = np.zeros(len(simulation_labels))
 

    fig = plt.figure(figsize = (20, 16))
    gs = gridspec.GridSpec(3,2, width_ratios=[3,1], figure = fig)
    ax1 = plt.subplot(gs[0, 0])
    ax2 = plt.subplot(gs[1, 0])
    ax3 = plt.subplot(gs[2, 0])
    ax4 = plt.subplot(gs[:, 1])
    axes_list = [ax1, ax2, ax3]
    counter = 0
    for sim_label, obs_label, agg, max_value, use_log, use_cdf, ax_loop in zip(simulation_labels, observation_labels, agg_list, max_value_list, use_log_list, use_cdf_list, axes_list):
      data_type_dict = {}
      data_type_dict['scenario'] = self.values[sim_label].resample(agg).sum() * unit_mult[0]
      data_type_dict['validation'] = validation_values[sim_label].resample(agg).sum() * unit_mult[1]
      data_type_dict['observation'] = self.observations[obs_label].resample(agg).sum() * unit_mult[2]
      
      if use_log:
        for scen_type in scenario_type_list:
          values_int = data_type_dict[scen_type]
          data_type_dict[scen_type] = np.log(values_int[values_int > 0])

      for scen_type in scenario_type_list:
        max_y_val[counter] = max([max(data_type_dict[scen_type]), max_y_val[counter]]) 
      counter += 1

      if use_cdf:
        for scen_type, color_loop in zip(scenario_type_list, color_list):
          cdf_values = np.zeros(100)
          values_int = data_type_dict[scen_type]
          for x in range(0, 100):
            x_val = int(np.ceil(max_value)) * (x/100)
            cdf_values[x] = len(values_int[values_int > x_val])/len(values_int)
          ax_loop.plot(cdf_values, np.arange(0, int(np.ceil(max_value)), int(np.ceil(max_value))/100), linewidth = 3, color = color_loop)
      else:
        pos = np.linspace(0, max_value, 101)
        for scen_type, color_loop in zip(scenario_type_list, color_list):
          kde_est = stats.gaussian_kde(data_type_dict[scen_type])
          ax_loop.fill_between(pos, kde_est(pos), edgecolor = 'black', alpha = 0.6, facecolor = color_loop)

    sri_dict = {}
    sri_dict['validation'] = validation_values['delta_forecastSRI']
    sri_dict['scenario'] = self.values['delta_forecastSRI']

    sri_cutoffs = {}
    sri_cutoffs['W'] = [9.2, 100]
    sri_cutoffs['AN'] = [7.8, 9.2]
    sri_cutoffs['BN'] = [6.6, 7.8]
    sri_cutoffs['D'] = [5.4, 6.6]
    sri_cutoffs['C'] = [0.0, 5.4]
    wyt_list = ['W', 'AN', 'BN', 'D', 'C']
    scenario_type_list = ['validation', 'scenario']
    colors = sns.color_palette('RdBu_r', n_colors = 5)
    percent_years = {}
    for wyt in wyt_list:
      percent_years[wyt] = np.zeros(len(scenario_type_list))
    for scen_cnt, scen_type in enumerate(scenario_type_list):
      ann_sri = []
      for x_cnt, x in enumerate(sri_dict[scen_type]):
        if sri_dict[scen_type].index.month[x_cnt] == 9 and sri_dict[scen_type].index.day[x_cnt] == 30:
          ann_sri.append(x)
      ann_sri = np.array(ann_sri)
      for x_cnt, wyt in enumerate(wyt_list):
        mask_value = (ann_sri >= sri_cutoffs[wyt][0]) & (ann_sri < sri_cutoffs[wyt][1]) 
        percent_years[wyt][scen_cnt] = len(ann_sri[mask_value])/len(ann_sri)

    colors = sns.color_palette('RdBu_r', n_colors = 5)
    last_type = np.zeros(len(scenario_type_list))
    for cnt, x in enumerate(wyt_list):
      ax4.bar(['Validated Period\n(1997-2016)', 'Extended Simulation\n(1906-2016)'], percent_years[x], alpha = 1.0, label = wyt, facecolor = colors[cnt], edgecolor = 'black', bottom = last_type)
      last_type += percent_years[x]

    ax1.set_xlim([0.0, 500.0* np.ceil(max_y_val[0]/500.0)])
    ax2.set_xlim([0.0, 500.0* np.ceil(max_y_val[1]/500.0)])
    ax3.set_xlim([0.0, 1.0])
    ax4.set_ylim([0, 1.15])

    ax1.set_yticklabels('')
    ax2.set_yticklabels('')
    label_list = []
    loc_list = []
    for value_x in range(0, 120, 20):
      label_list.append(str(value_x) + ' %')
      loc_list.append(value_x/100.0)
    ax4.set_yticklabels(label_list)
    ax4.set_yticks(loc_list)
    ax3.set_xticklabels(label_list)
    ax3.set_xticks(loc_list)
  
    ax3.set_yticklabels(['4', '8', '16', '32', '64', '125', '250', '500', '1000', '2000', '4000'])
    ax3.set_yticks([np.log(4), np.log(8), np.log(16), np.log(32), np.log(64), np.log(125), np.log(250), np.log(500), np.log(1000), np.log(2000), np.log(4000)])
    ax3.set_ylim([np.log(4), np.log(4000)])

    for ax, x_lab, y_lab in zip([ax1, ax2, ax3, ax4], x_label_list, y_label_list):
      ax.set_xlabel(x_lab, fontsize = 16, fontname = 'Gill Sans MT', fontweight = 'bold')
      ax.set_ylabel(y_lab, fontsize = 16, fontname = 'Gill Sans MT', fontweight = 'bold')
      ax.grid(False)
      for tick in ax.get_xticklabels():
        tick.set_fontname('Gill Sans MT')
        tick.set_fontsize(14)
      for tick in ax.get_yticklabels():
        tick.set_fontname('Gill Sans MT')
        tick.set_fontsize(14)
          
    legend_elements = []
    for x_cnt, x in enumerate(legend_label_names1):
      legend_elements.append(Patch(facecolor = color_list[x_cnt], edgecolor = 'black', label = x))
    ax1.legend(handles = legend_elements, loc = 'upper left', framealpha  = 0.7, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':14}) 

    legend_elements_2 = []
    for x_cnt, x in enumerate(legend_label_names2):
      legend_elements_2.append(Patch(facecolor = colors[x_cnt], edgecolor = 'black', label = x))

    ax4.legend(handles = legend_elements_2, loc = 'upper left', framealpha  = 0.7, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':14}) 
    plt.savefig(folder_name + figure_name + '_' + plot_name + '.png', dpi = 150, bbox_inches = 'tight', pad_inches = 0.0)
    if show_plot:
      plt.show()
    plt.close()

  def make_deliveries_by_district(self, folder_name, figure_name, plot_name, scenario_name, show_plot):

    district_group_list = self.figure_params[figure_name][plot_name]['district_groups']
    district_groups = {}
    for x in district_group_list:
      district_groups[x] = self.figure_params[figure_name][plot_name][x]
    name_bridge = {}
    name_bridge['semitropic'] = 'KER01'
    name_bridge['westkern'] = 'KER02' 
    name_bridge['wheeler'] = 'KER03'
    name_bridge['kerndelta'] = 'KER04'
    name_bridge['arvin'] = 'KER05'
    name_bridge['belridge'] = 'KER06'
    name_bridge['losthills'] = 'KER07'
    name_bridge['northkern'] = 'KER08'
    name_bridge['northkernwb'] = 'KER08'
    name_bridge['ID4'] = 'KER09'
    name_bridge['sosanjoaquin'] = 'KER10'  
    name_bridge['berrenda'] = 'KER11'
    name_bridge['buenavista'] = 'KER12'
    name_bridge['cawelo'] = 'KER13'
    name_bridge['rosedale'] = 'KER14'
    name_bridge['shaffer'] = 'KER15'
    name_bridge['henrymiller'] = 'KER16'  
    name_bridge['kwb'] = 'KER17'
    name_bridge['b2800'] = 'KER17'
    name_bridge['pioneer'] = 'KER17'
    name_bridge['irvineranch'] = 'KER17'
    name_bridge['kernriverbed'] = 'KER17'
    name_bridge['poso'] = 'KER17'
    name_bridge['stockdale'] = 'KER17'

    name_bridge['delano'] = 'KeT01'
    name_bridge['kerntulare'] = 'KeT02' 
    name_bridge['lowertule'] = 'TUL01'
    name_bridge['tulare'] = 'TUL02'
    name_bridge['lindmore'] = 'TUL03'
    name_bridge['saucelito'] = 'TUL04'
    name_bridge['porterville'] = 'TUL05'
    name_bridge['lindsay'] = 'TUL06'
    name_bridge['exeter'] = 'TUL07'
    name_bridge['terra'] = 'TUL08'
    name_bridge['teapot'] = 'TUL09'

    name_bridge['bakersfield'] = 'BAK'     
    name_bridge['fresno'] = 'FRE' 
    name_bridge['southbay'] = 'SOB'
    name_bridge['socal'] = 'SOC'
    name_bridge['tehachapi'] = 'TEH'
    name_bridge['tejon'] = 'TEJ'
    name_bridge['centralcoast'] = 'SLO'    
    name_bridge['pixley'] = 'PIX'
    name_bridge['chowchilla'] = 'CHW'  
    name_bridge['maderairr'] = 'MAD'
    name_bridge['fresnoid'] = 'FSI'
    name_bridge['westlands'] = 'WTL'
    name_bridge['panoche'] = 'PAN'
    name_bridge['sanluiswater'] = 'SLW'   
    name_bridge['delpuerto'] = 'DEL'

    n_cols = self.figure_params[figure_name][plot_name]['subplot columns']
    write_file = self.figure_params[figure_name][plot_name]['write file']
    figure_color_map = self.figure_params[figure_name][plot_name]['color map']

    location_type = plot_name

    self.total_irrigation_by_district = {}
    self.total_recharge_by_district = {}
    self.total_pumping_by_district = {}
    self.total_recharge_out_of_district = {}
    self.total_pumping_out_of_district = {}

    for bank in self.bank_list:
      self.total_recharge_by_district[bank.name] = np.zeros(self.number_years)
      self.total_irrigation_by_district[bank.name] = np.zeros(self.number_years)
      self.total_pumping_by_district[bank.name] = np.zeros(self.number_years)
      self.total_recharge_out_of_district[bank.name] = np.zeros(self.number_years)
      self.total_pumping_out_of_district[bank.name] = np.zeros(self.number_years)

    for district in self.district_list:
      self.total_irrigation_by_district[district.name] = np.zeros(self.number_years)
      self.total_recharge_by_district[district.name] = np.zeros(self.number_years)
      self.total_pumping_by_district[district.name] = np.zeros(self.number_years)
      self.total_recharge_out_of_district[district.name] = np.zeros(self.number_years)
      self.total_pumping_out_of_district[district.name] = np.zeros(self.number_years)

    for district in self.district_list:

      inleiu_name = district.name + '_inleiu_irrigation'
      inleiu_recharge_name = district.name + '_inleiu_recharge'
      direct_recover_name = district.name + '_recover_banked'
      indirect_surface_name = district.name + '_exchanged_SW'
      indirect_ground_name = district.name + '_exchanged_GW'
      inleiu_pumping_name = district.name +  '_leiupumping'
      pumping_name = district.name + '_pumping'
      recharge_name = district.name + '_' + district.key + '_recharged'


      for year_num in range(0, self.number_years):
        year_str = str(year_num + self.starting_year + 1)
        ###GW/SW exchanges, 
        if indirect_surface_name in self.values:
          total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), indirect_surface_name]
          #count irrigation deliveries for district that gave up SW (for GW in canal)
          self.total_irrigation_by_district[district.name][year_num] += total_delivery

        ###GW/SW exchanges, 
        if indirect_ground_name in self.values:
          total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), indirect_ground_name]
          #count irrigation deliveries for district that gave up SW (for GW in canal)
          if location_type == 'account':
            self.total_pumping_out_of_district[district.name][year_num] += total_delivery
            self.total_irrigation_by_district[district.name][year_num] -= total_delivery


        ##In leiu deliveries for irrigation
        if inleiu_name in self.values:
          total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), inleiu_name]
          #attibute inleiu deliveries for irrigation to district operating the bank
          self.total_irrigation_by_district[district.name][year_num] += total_delivery
        if inleiu_recharge_name in self.values:
          total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), inleiu_recharge_name]
          #attibute inleiu deliveries for irrigation to district operating the bank
          self.total_recharge_by_district[district.name][year_num] += total_recharge

        #GW recovery 
        if direct_recover_name in self.values:
          total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), direct_recover_name]
          #if classifying by physical location, attribute to district recieving water (as irrigation)
          if location_type == 'physical':
            self.total_irrigation_by_district[district.name][year_num] += total_delivery
          #if classifying by account, attribute to district recieving water as GW from out of district
          elif location_type == 'account':
            self.total_pumping_out_of_district[district.name][year_num] += total_delivery
  
        ##Pumnping for inleiu recovery     
        if inleiu_pumping_name in self.values:
          total_leiupumping = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), inleiu_pumping_name]
          #if classifying by physical location, to district operating the bank
          if location_type == 'physical':
            self.total_pumping_by_district[district.name][year_num] += total_leiupumping
         
        #Recharge, in- and out- of district          
        if recharge_name in self.values:
          total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), recharge_name]
          self.total_recharge_by_district[district.name][year_num] += total_recharge
        for bank_name in self.bank_list:
          bank_recharge_name = district.name + '_' + bank_name.key + '_recharged'
          if bank_recharge_name in self.values:
            total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), bank_recharge_name]
            if location_type == 'physical':
              self.total_recharge_by_district[bank_name.name][year_num] += total_recharge#      for bank_name in self.leiu_list:
            elif location_type == 'account':
              self.total_recharge_out_of_district[bank_name.name][year_num] += total_recharge#      for bank_name in self.leiu_list:
        for bank_name in self.leiu_list:
          bank_recharge_name = district.name + '_' + bank_name.key + '_recharged'
          if bank_recharge_name in self.values:
            total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), bank_recharge_name]
            if location_type == 'account':
              self.total_recharge_out_of_district[bank_name.name][year_num] += total_recharge#      for bank_name in self.leiu_list:

      #Contract deliveries (minus deliveries made for recharge (accouted for above) 
      for contract in self.contract_list:
        delivery_name = district.name + '_' + contract.name + '_delivery'
        recharge_name = district.name + '_' + contract.name + '_recharged'
        flood_irr_name = district.name + '_' + contract.name + '_flood_irrigation'
        for year_num in range(0, self.number_years):
          year_str = str(year_num + self.starting_year + 1)
          ###All deliveries made from a district's contract
          if delivery_name in self.values:
            total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), delivery_name]
            self.total_irrigation_by_district[district.name][year_num] += total_delivery         
          ##Deliveries made for recharge are subtracted from the overall contract deliveries
          if recharge_name in self.values:
            total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), recharge_name]
            self.total_irrigation_by_district[district.name][year_num] -= total_recharge
          #flood water used for irrigation - always attribute as irrigation
          if flood_irr_name in self.values:
            total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), flood_irr_name]
            self.total_irrigation_by_district[district.name][year_num] += total_delivery
        
      ##Pumping (daily values aggregated by year)
      if pumping_name in self.values:
        anuual_pumping = 0.0
        for x in range(0, len(self.index)):
          if self.month[x] == 10 and self.day_month[x] == 1:
            annual_pumping = 0.0
          else:
            annual_pumping += self.values.loc[self.index[x], pumping_name]
            if self.month[x] == 9 and self.day_month[x] == 30:            
              self.total_pumping_by_district[district.name][self.year[x] - self.starting_year - 1] += annual_pumping          

      #Get values for any private entities within the district      
      for private_name in self.private_list:
        private = private_name.name
        if district.key in self.private_districts[private]:
          inleiu_name = private + '_' + district.key + '_inleiu_irrigation'
          inleiu_recharge_name = private + '_' + district.key + '_inleiu_irrigation'
          direct_recover_name = private + '_' + district.key + '_recover_banked'
          indirect_surface_name = private + '_' + district.key + '_exchanged_SW'
          indirect_ground_name = private + '_' + district.key + '_exchanged_GW'
          inleiu_pumping_name = private + '_' + district.key + '_leiupumping'
          pumping_name = private + '_' + district.key + '_pumping'
          recharge_name = private + '_' + district.key + '_' + district.key + '_recharged'


          for year_num in range(0, self.number_years):
            year_str = str(year_num + self.starting_year + 1)
            ###GW/SW exchanges, 
            if indirect_surface_name in self.values:
              total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), indirect_surface_name]
              #count irrigation deliveries for district that gave up SW (for GW in canal)
              self.total_irrigation_by_district[district.name][year_num] += total_delivery

            ###GW/SW exchanges, 
            if indirect_ground_name in self.values:
              total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), indirect_ground_name]
              #count irrigation deliveries for district that gave up SW (for GW in canal)
              if location_type == 'account':
                self.total_pumping_out_of_district[district.name][year_num] += total_delivery

                self.total_irrigation_by_district[district.name][year_num] -= total_delivery


            ##In leiu deliveries for irrigation
            if inleiu_name in self.values:
              total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), inleiu_name]
              #attibute inleiu deliveries for irrigation to district operating the bank
              self.total_irrigation_by_district[district.name][year_num] += total_delivery
            if inleiu_recharge_name in self.values:
              total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), inleiu_recharge_name]
              #attibute inleiu deliveries for irrigation to district operating the bank
              self.total_recharge_by_district[district.name][year_num] += total_recharge

            #GW recovery 
            if direct_recover_name in self.values:
              total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), direct_recover_name]
              #if classifying by physical location, attribute to district recieving water (as irrigation)
              if location_type == 'physical':
                self.total_irrigation_by_district[district.name][year_num] += total_delivery
              #if classifying by account, attribute to district recieving water as GW from out of district
              elif location_type == 'account':
                self.total_pumping_out_of_district[district.name][year_num] += total_delivery

  
            ##Pumnping for inleiu recovery     
            if inleiu_pumping_name in self.values:
              total_leiupumping = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), inleiu_pumping_name]
              #if classifying by phyiscal location, to district operating the bank
              if location_type == 'physical':
                self.total_pumping_by_district[district.name][year_num] += total_leiupumping
         
            #Recharge, in- and out- of district          
            if recharge_name in self.values:
              total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), recharge_name]
              self.total_recharge_by_district[district.name][year_num] += total_recharge
            for bank_name in self.bank_list:
              bank_recharge_name = private + '_' + district.key + '_' + bank_name.key + '_recharged'
              if bank_recharge_name in self.values:
                total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), bank_recharge_name]
                if location_type == 'physical':
                  self.total_recharge_by_district[bank_name.name][year_num] += total_recharge
                elif location_type == 'account':
                  self.total_recharge_out_of_district[district.name][year_num] += total_recharge
            for bank_name in self.leiu_list:
              bank_recharge_name = private + '_' + district.key + '_' + bank_name.key + '_recharged'
              if bank_recharge_name in self.values:
                total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), bank_recharge_name]
                if location_type == 'account':
                  self.total_recharge_out_of_district[district.name][year_num] += total_recharge

          #Contract deliveries (minus deliveries made for recharge (accouted for above) 
          for contract in self.contract_list:
            delivery_name = private + '_' + district.key + '_' + contract.name + '_delivery'
            recharge_name = private + '_' + district.key + '_' + contract.name + '_recharged'
            flood_irr_name = private + '_' + district.key + '_' + contract.name + '_flood_irrigation'
            for year_num in range(0, self.number_years):
              year_str = str(year_num + self.starting_year + 1)
              ###All deliveries made from a district's contract
              if delivery_name in self.values:
                total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), delivery_name]
                self.total_irrigation_by_district[district.name][year_num] += total_delivery         
              ##Deliveries made for recharge are subtracted from the overall contract deliveries
              if recharge_name in self.values:
                total_recharge = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), recharge_name]
                self.total_irrigation_by_district[district.name][year_num] -= total_recharge
              #flood water used for irrigation - always attribute as irrigation
              if flood_irr_name in self.values:
                total_delivery = self.values.loc[pd.DatetimeIndex([year_str + '-9-29']), flood_irr_name]
                self.total_irrigation_by_district[district.name][year_num] += total_delivery
        
          ##Pumping (daily values aggregated by year)
          if pumping_name in self.values:
            annual_pumping = 0.0
            for x in range(0, len(self.index)):
              if self.month[x] == 10 and self.day_month[x] == 1:
                annual_pumping = 0.0
              else:
                annual_pumping += self.values.loc[self.index[x], pumping_name]
                if self.month[x] == 9 and self.day_month[x] == 30:            
                  self.total_pumping_by_district[district.name][self.year[x] - self.starting_year - 1] += annual_pumping

    for bank_name in self.bank_list:
      for partner_name in bank_name.participant_list:
        account_name = bank_name.name + '_' + partner_name
        if account_name in self.values:
          annual_pumping = 0.0
          yesterday_account = 0.0
          for x in range(0, len(self.index)):
            if self.month[x] == 10 and self.day_month[x] == 1:
              annual_pumping = 0.0
            else:
              today_account = self.values.loc[self.index[x], account_name]
              annual_pumping += max(yesterday_account - today_account, 0.0)
              yesterday_account = today_account * 1.0
              if self.month[x] == 9 and self.day_month[x] == 30:
                if location_type == 'physical':            
                  self.total_pumping_by_district[bank_name.name][self.year[x] - self.starting_year - 1] += annual_pumping          


    if location_type == 'physical':
      colors = sns.color_palette('YlGnBu_r', n_colors = len(district_groups))
      fig, ax = plt.subplots(3, figsize = (8, 18))
    elif location_type == 'account':
      n_rows = int(np.ceil(len(district_groups)/n_cols))
      colors = sns.color_palette('BrBG_r', n_colors = 7)
      fig, ax = plt.subplots(n_rows, n_cols, figsize = (16,12))
    sns.set()    
    if location_type == 'physical':
      total_deliveries = np.zeros(self.number_years)
      for x_cnt, x in enumerate(district_groups):
        for y in district_groups[x]:
          total_deliveries += self.total_irrigation_by_district[y] + self.total_recharge_by_district[y]
      plotting_order = np.argsort(total_deliveries)
    
      prev_list = np.zeros(self.number_years)
      prev_list2 = np.zeros(self.number_years)
      prev_list3 = np.zeros(self.number_years)
      for x_cnt, x in enumerate(district_groups):
        for y in district_groups[x]:          
          this_list = prev_list + self.total_irrigation_by_district[y]
          ax[0].fill_between(np.arange(self.number_years), prev_list[plotting_order], this_list[plotting_order], color = colors[x_cnt], edgecolor = 'black')
          prev_list = this_list * 1.0
          this_list2 = prev_list2 + self.total_recharge_by_district[y]
          ax[1].fill_between(np.arange(self.number_years), prev_list2[plotting_order], this_list2[plotting_order], color = colors[x_cnt], edgecolor = 'black')
          prev_list2 = this_list2 * 1.0
          this_list3 = prev_list3 + self.total_pumping_by_district[y]
          ax[2].fill_between(np.arange(self.number_years), prev_list3[plotting_order], this_list3[plotting_order], color = colors[x_cnt], edgecolor = 'black')
          prev_list3 = this_list3 * 1.0



      ax[2].set_xlabel('Frequency of Years with Fewer Total Surface Water Deliveries', fontsize = 14, fontname = 'Gill Sans MT')

      ax[0].set_ylabel('Surface Water Consumptive Use (tAF/year)', fontsize = 14, fontname = 'Gill Sans MT')
      ax[1].set_ylabel('Direct Groundwater Recharge (tAF/year)', fontsize = 14, fontname = 'Gill Sans MT')
      ax[2].set_ylabel('Groundwater Pumping (tAF/year)', fontsize = 14, fontname = 'Gill Sans MT')

      ax[0].set_ylim([0, np.ceil(max(prev_list)/500.0) * 500.0])
      ax[1].set_ylim([0, np.ceil(max(prev_list2)/500.0) * 500.0])
      ax[2].set_ylim([0, np.ceil(max(prev_list3)/500.0) * 500.0])

      for x in range(0, 3):
        ax[x].set_xlim([0, self.number_years - 1])
        ax[x].set_xticks([0, int(np.ceil(self.number_years/2)), self.number_years])
        ax[x].set_xticklabels(['0%', '50%', '100%'])
        ax[x].grid(False)
        for tick in ax[x].get_xticklabels():
          tick.set_fontname('Gill Sans MT')
        for tick in ax[x].get_yticklabels():
          tick.set_fontname('Gill Sans MT')
          
      legend_elements = []
      for cnt, xx in enumerate(district_group_list):
        legend_elements.append(Patch(facecolor = colors[cnt], edgecolor = 'black', label = xx))
      ax[0].legend(handles = legend_elements, loc = 'lower right', framealpha  = 0.7, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':10}) 

      plt.savefig(folder_name + figure_name + '_' + plot_name + '.png', dpi = 150, bbox_inches = 'tight', pad_inches = 0.0)
      if write_file:
        final_district_irrigation = pd.DataFrame(index = np.arange(self.starting_year, self.starting_year + self.number_years))
        final_district_recharge = pd.DataFrame(index = np.arange(self.starting_year, self.starting_year + self.number_years))
        final_district_pumping = pd.DataFrame(index = np.arange(self.starting_year, self.starting_year + self.number_years))
        for y in name_bridge:
          file_col_name = name_bridge[y]
          if file_col_name in final_district_irrigation:
            final_district_irrigation[file_col_name] += self.total_irrigation_by_district[y]
            final_district_recharge[file_col_name] += self.total_recharge_by_district[y]
            final_district_pumping[file_col_name] += self.total_pumping_by_district[y]
          else:
            final_district_irrigation[file_col_name] = self.total_irrigation_by_district[y]
            final_district_recharge[file_col_name] = self.total_recharge_by_district[y]
            final_district_pumping[file_col_name] = self.total_pumping_by_district[y]
        final_district_irrigation.to_csv(folder_name + 'irrigation_by_year_' + scenario_name + '.csv')
        final_district_recharge.to_csv(folder_name + 'recharge_by_year_' + scenario_name + '.csv')
        final_district_pumping.to_csv(folder_name + 'pumping_by_year_' + scenario_name + '.csv')
    
    elif location_type == 'account':
      counter_x = 0
      counter_y = 0
      for x_cnt, x in enumerate(district_groups):
        total_deliveries = np.zeros(self.number_years)
        for y in district_groups[x]:
          total_deliveries += self.total_irrigation_by_district[y] + self.total_recharge_by_district[y] + self.total_recharge_out_of_district[y]
        plotting_order = np.argsort(total_deliveries)
        
        prev_list = np.zeros(self.number_years)        
        for y in district_groups[x]:          
          this_list = prev_list + self.total_irrigation_by_district[y]
          ax[counter_x][counter_y].fill_between(np.arange(self.number_years), prev_list[plotting_order], this_list[plotting_order], color = colors[0], edgecolor = 'black')
          prev_list = this_list * 1.0

        for y in district_groups[x]:          
          this_list = prev_list + self.total_pumping_out_of_district[y]
          ax[counter_x][counter_y].fill_between(np.arange(self.number_years), prev_list[plotting_order], this_list[plotting_order], color = colors[4], edgecolor = 'black')
          prev_list = this_list * 1.0

        for y in district_groups[x]:          
          this_list = prev_list + self.total_pumping_by_district[y]
          ax[counter_x][counter_y].fill_between(np.arange(self.number_years), prev_list[plotting_order], this_list[plotting_order], color = colors[5], edgecolor = 'black')
          prev_list = this_list * 1.0

        for y in district_groups[x]:          
          this_list = prev_list + self.total_recharge_by_district[y]
          ax[counter_x][counter_y].fill_between(np.arange(self.number_years), prev_list[plotting_order], this_list[plotting_order], color = colors[1], edgecolor = 'black')
          prev_list = this_list * 1.0

        for y in district_groups[x]:          
          this_list = prev_list + self.total_recharge_out_of_district[y]
          ax[counter_x][counter_y].fill_between(np.arange(self.number_years), prev_list[plotting_order], this_list[plotting_order], color = colors[2], edgecolor = 'black')
          prev_list = this_list * 1.0

        ax[counter_x][counter_y].set_title(x, fontsize = 16, weight = 'bold', fontname = 'Gill Sans MT')
        ax[counter_x][counter_y].set_ylim([0, np.ceil(max(prev_list)/500.0) * 500.0])
        counter_x += 1
        if counter_x == n_rows:
          counter_x = 0
          counter_y += 1

        
      for x in range(0, n_rows):
        for y in range(0, n_cols):
          ax[x][y].set_xlim([0, self.number_years])
          ax[x][y].set_xticks([0, int(np.ceil(self.number_years/2)), self.number_years])
          ax[x][y].set_xticklabels(['0%', '50%', '100%'])
          if x == n_rows - 1:
            ax[x][y].set_xlabel('Frequency of Years with Fewer Total Surface Water Deliveries', fontsize = 14, fontname = 'Gill Sans MT')
          if y == 0:
            ax[x][y].set_ylabel('Annual water use by type (tAF)', fontsize = 16, fontname = 'Gill Sans MT')
          ax[x][y].grid(False)
          for tick in ax[x][y].get_xticklabels():
            tick.set_fontname('Gill Sans MT')
          for tick in ax[x][y].get_yticklabels():
            tick.set_fontname('Gill Sans MT')

      legend_elements = []
      legend_list = ['Consumptive Use', 'In-District Recharge', 'Out-of-District Recharge', 'Out-of-District GW Recovery', 'In-District GW Pumping']
      color_numbers = [0, 1, 2, 4, 5]
      for cnt, xx in enumerate(legend_list):
        legend_elements.append(Patch(facecolor = colors[color_numbers[cnt]], edgecolor = 'black', label = xx))
      ax[0][0].legend(handles = legend_elements, loc = 'lower right', framealpha  = 0.7, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':10}) 

      for x in range(0,2):
        for y in range(0,2):
          for tick in ax[x][y].get_xticklabels():
            tick.set_fontname('Gill Sans MT')
          for tick in ax[x][y].get_yticklabels():
            tick.set_fontname('Gill Sans MT')
      plt.savefig(folder_name + figure_name + '_' + plot_name + '_' + scenario_name + '.png', dpi = 150, bbox_inches = 'tight', pad_inches = 0.0)

    if show_plot:
      plt.show()
    plt.close()


  def plot_forecasts(self, folder_name, figure_name, plot_name, n_colors, scatter_interval, range_sensitivity, show_plot):

    predictor_list = self.figure_params[figure_name][plot_name]['predictor values']
    forecast_list = self.figure_params[figure_name][plot_name]['forecast_values']
    forecast_periods = self.figure_params[figure_name][plot_name]['forecast_periods']
    non_log_list = self.figure_params[figure_name][plot_name]['non_log']
    colorbar_labels = self.figure_params[figure_name][plot_name]['colorbar_label_list']
    colorbar_index = self.figure_params[figure_name][plot_name]['colorbar_label_index']
    all_cols = self.figure_params[figure_name][plot_name]['all_cols']    
    subplot_label = self.figure_params[figure_name][plot_name]['subplot_annotations']
    watershed_keys = self.figure_params[figure_name][plot_name]['watershed_keys']
    watershed_labels = self.figure_params[figure_name][plot_name]['watershed_labels']

    #Initialize Figure
    sns.set()
    colors = sns.color_palette('YlGnBu_r', n_colors = n_colors)
    num_cols = len(forecast_list)
    num_rows = len(watershed_keys)
    fig = plt.figure(figsize = (16, 10))
    gs = gridspec.GridSpec(num_rows,num_cols)
    #subplot counts
    counter_x = 0
    counter_y = 0

    #Plot colorbar
    fig.subplots_adjust(right=0.9)
    cbar_ax = fig.add_axes([0.9187, 0.15, 0.025, 0.7])
    sm = plt.cm.ScalarMappable(cmap=pl.cm.YlGnBu_r, norm=plt.Normalize(vmin=0, vmax=n_colors))
    clb1 = plt.colorbar(sm, cax = cbar_ax, ticks=colorbar_index)
    clb1.ax.set_yticklabels(colorbar_labels) 
    clb1.ax.invert_yaxis()
    clb1.ax.tick_params(labelsize=16)
    for item in clb1.ax.yaxis.get_ticklabels():
      item.set_fontname('Gill Sans MT')  

    ##Loop through reservoirs
    for key, key_label in zip(watershed_keys, watershed_labels):
      #Get reservoir flow and snowpack timeseries
      Q = self.observations['%s_inf' % key]
      QMA = self.observations['%s_inf' % key].rolling(window=30).mean() * cfs_tafd
      SNPK = self.observations['%s_snow' % key].values
      scatterplot_values = pd.DataFrame(index = self.observations.index, columns = all_cols)
       
      #recalfews_src predictor and observed variables at each timestep
      for x in range(0, len(Q)):      
        index_val = self.observations.index[x]
        day_year_val = index_val.dayofyear
        if index_val.month > 9:
          dowy = max(day_year_val - 273, 0)
        else:
          dowy = min(day_year_val + 92, 364)
        #Predictor variables
        scatterplot_values.at[index_val, 'DOWY'] = dowy
        scatterplot_values.at[index_val, 'Snowpack (SWE)'] = SNPK[x]
        scatterplot_values.at[index_val, 'Mean Inflow, Prior 30 Days (tAF/day)'] = QMA[x]
        
        #Observed variables (loop through list)
        for count_f, forecast_pd in enumerate(forecast_periods):
          if forecast_pd == 'SNOWMELT':
            april_start = (181 - dowy) + x
            july_end = (303 - dowy) + x
            index_snowmelt = (self.observations.index > self.observations.index[april_start]) & (self.observations.index < self.observations.index[july_end])
            scatterplot_values.at[index_val, forecast_list[count_f]] = np.sum(Q[index_snowmelt]) * cfs_tafd
          else:
            if x < len(Q) - forecast_pd:
              index_f = (self.observations.index > self.observations.index[x]) & (self.observations.index < self.observations.index[x + forecast_pd - 1])
            else:
              index_f = (self.observations.index > self.observations.index[x]) & (self.observations.index < self.observations.index[len(Q) - 1])
            scatterplot_values.at[index_val, forecast_list[count_f]] = np.sum(Q[index_f]) * cfs_tafd
                
      ##Find min/max values in each predictor/observed dataset, use to scale axis for each subplot
      min_plot = {}
      max_plot = {}
      for aa in predictor_list:
        min_plot[aa] = 999998
        max_plot[aa] = -999999.9
      for aa in forecast_list:
        min_plot[aa] = 999998
        max_plot[aa] = -999999.9
      counter = 0
      for dowy_loop in range(0, n_colors):
        if counter == scatter_interval:            
          dowy_loop_values = scatterplot_values[scatterplot_values['DOWY'] == dowy_loop]    
          for index, row in dowy_loop_values.iterrows():
            for aa, bb in zip(predictor_list, forecast_list):
              if aa in non_log_list and ~pd.isnull(row[aa]) and ~pd.isnull(row[bb]) and row[bb] > 0.0:
                max_plot[aa] = max(row[aa], max_plot[aa])
                min_plot[aa] = min(row[aa], min_plot[aa])
                max_plot[bb] = max(math.log(row[bb]), max_plot[bb])
                min_plot[bb] = min(math.log(row[bb]), min_plot[bb])
              elif ~pd.isnull(row[aa]) and row[aa] > 0.0 and ~pd.isnull(row[bb]) and row[bb] > 0.0:
                  max_plot[aa] = max(math.log(row[aa]), max_plot[aa])
                  min_plot[aa] = min(math.log(row[aa]), min_plot[aa])
                  max_plot[bb] = max(math.log(row[bb]), max_plot[bb])
                  min_plot[bb] = min(math.log(row[bb]), min_plot[bb])
        counter += 1
        if counter == scatter_interval + 1:
          counter = 0
      ##Small buffer around max/min values
      for bb in forecast_list:
        max_plot[bb] += 0.075 * (max_plot[bb] - min_plot[bb])
        min_plot[bb] -= 0.075 * (max_plot[bb] - min_plot[bb])
      for aa in predictor_list:
        max_plot[aa] += 0.075 * (max_plot[aa] - min_plot[aa])
        if aa in non_log_list:
          min_plot[aa] -= min(0.075 * (max_plot[aa] - min_plot[aa]), min_plot[aa])
        else:
          min_plot[aa] -= 0.075 * (max_plot[aa] - min_plot[aa])
    #plotting  
    #subplot loops  
      for aa, bb in zip(predictor_list, forecast_list):
        ax0 = plt.subplot(gs[counter_x,counter_y])
        #find regression equation for all points in each day of the year (Oct - Apr)
        for risk_alpha in range(0, 10):
          counter = 0
          for dowy in range(0, n_colors):
            this_dowy = scatterplot_values[scatterplot_values['DOWY'] == dowy]
            counter_array = 0
            predictor = np.zeros(len(this_dowy[aa]))
            observor = np.zeros(len(this_dowy[bb]))
            ##Only keep positive values
            for index, row in this_dowy.iterrows():
              if aa in non_log_list:
                if ~pd.isnull(row[aa]) and ~pd.isnull(row[bb]) and row[bb] > 0.0:
                  predictor[counter_array] = row[aa] 
                  observor[counter_array] = math.log(row[bb])
                  counter_array += 1
              else:
                if ~pd.isnull(row[aa]) and row[aa] > 0.0 and ~pd.isnull(row[bb]) and row[bb] > 0.0:
                  predictor[counter_array] = math.log(row[aa]) 
                  observor[counter_array] = math.log(row[bb])
                  counter_array += 1
            #Remove zeros for regression
            predictor = predictor[0:counter_array]
            observor = observor[0:counter_array]
            #Run regression, plot points and regression line
            #Color point and line to day-of-year
            if np.sum(np.power(predictor, 2)) > 0.0:
              coef = np.polyfit(predictor, observor, 1)
              predictor_std = np.std(predictor)
              x_calfews_src = [min(predictor) - predictor_std * risk_alpha / range_sensitivity, max(predictor) + predictor_std * risk_alpha / range_sensitivity]
              y_calfews_src = [(min(predictor) - predictor_std * risk_alpha / range_sensitivity) * coef[0] + coef[1], (max(predictor) + predictor_std * risk_alpha / range_sensitivity) * coef[0] + coef[1]]
              ax0.plot(x_calfews_src, y_calfews_src, color = colors[dowy], zorder = 3, linewidth = 3, alpha = (10.0 - risk_alpha)/ 10.0)
              if risk_alpha == 0:
                if counter == scatter_interval:
                  ax0.scatter(predictor, observor, s = 100, color = colors[dowy], edgecolor = 'black', linewidths = 2.0, alpha = 1.0, zorder = 5)      
                #Only show 1 daily point from each month (daily timestep)
            counter += 1
            if counter == scatter_interval + 1:
              counter = 0
            
        ##Write non-log values to overwrite log-scale ticklabels
        xtick_loc = []
        xtick_lab = []
        ytick_loc = []
        ytick_lab = []
        start_flow = .25/256.0
        if aa not in non_log_list:
          while math.log(start_flow) > min_plot[aa]:
            start_flow = start_flow * 0.5
          while math.log(start_flow) < max_plot[aa]:
            start_flow = start_flow * 2.0
            xtick_loc.append(math.log(start_flow))
            xtick_lab.append(str(start_flow))
          ax0.set_xticks(xtick_loc)
          ax0.set_xticklabels(xtick_lab)
        start_flow = 25.0/256.0
        if bb not in non_log_list:
          while math.log(start_flow) > min_plot[bb]:
            start_flow = start_flow / 2.0
          while math.log(start_flow) < max_plot[bb]:
            start_flow = start_flow * 2.0
            ytick_loc.append(math.log(start_flow))
            ytick_lab.append(str(start_flow))
          ax0.set_yticks(ytick_loc)
          ax0.set_yticklabels(ytick_lab)
        #Format Plot
        if counter_x == 0:
          ax0.set_title(bb, fontsize = 16, fontname = 'Gill Sans MT', fontweight = 'bold')
        if counter_y == 0:
          ax0.set_ylabel(key_label)
        ax0.yaxis.set_label_coords(-.15, 0.5)
        fig.text(0.04, 0.5, 'Reservoir Inflow (tAF)', va='center', rotation='vertical', fontsize = 14, fontname = 'Gill Sans MT')

        if counter_x == num_rows - 1:
          ax0.set_xlabel(aa)          
        ax0.set_xlim([min_plot[aa], max_plot[aa]])
        ax0.set_ylim([min_plot[bb], max_plot[bb]])
        ax0.grid(False)
        #ax0.set_ylabel(bb)
        #annotation_location_x = 0.8 * (max_plot[aa] - min_plot[aa]) + min_plot[aa]
        #annotation_location_y = 0.05 * (max_plot[bb] - min_plot[bb]) + min_plot[bb]
        #ax0.annotate(subplot_label[counter_x + counter_y * num_rows], xy=(annotation_location_x, annotation_location_y), color='0.1', fontsize = 36, fontname = 'Gill Sans MT', fontweight = 'bold')
        for item in [ax0.xaxis.label, ax0.yaxis.label]:
          item.set_fontsize(14)
          item.set_fontname('Gill Sans MT')  
        for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
          item.set_fontsize(14)
          item.set_fontname('Gill Sans MT')
        if counter_x == num_rows - 1 and counter_y == num_cols - 1:
          custom_lines = [Line2D([0], [0], marker = 'o', markeredgewidth = 3, markeredgecolor='black', markerfacecolor = 'none', markersize = 15, lw=0, label = 'historical observation'), Line2D([0], [0], color='black', lw=4, label = 'daily regression estimator')]
          L = ax0.legend(handles = custom_lines, loc = 'lower right', fontsize = 12)
          plt.setp(L.texts, family='Gill Sans MT')
        counter_y += 1
        if counter_y == num_cols:
          counter_y = 0
          counter_x += 1      

    plt.savefig(folder_name + figure_name + '_' + plot_name + '.png', dpi = 150, bbox_inches = 'tight', pad_inches = 0.0)
    if show_plot:
      plt.show()
    plt.close()

  def show_state_response(self, folder_name, figure_name, reservoir_name, district_label, district_key, district_private_labels, district_private_keys, show_plot):
    
    plot_name = reservoir_name + '_' + district_label
    contract_list = self.figure_params[figure_name][plot_name]['contract_list']
    available_water_keys = self.figure_params[figure_name][plot_name]['contributing_reservoirs']
    gw_key_list = self.figure_params[figure_name][plot_name]['groundwater_account_names']
    reservoir_features = self.figure_params[figure_name][plot_name]['reservoir_features']
    reservoir_feature_colors = self.figure_params[figure_name][plot_name]['reservoir_feature_colors']
    district_contracts = self.figure_params[figure_name][plot_name]['district_contracts']
    subplot_titles = self.figure_params[figure_name][plot_name]['subplot_titles']   
    legend_list_1 = self.figure_params[figure_name][plot_name]['legend_list_1']
    legend_list_2 = self.figure_params[figure_name][plot_name]['legend_list_2']
    legend_list_3 = self.figure_params[figure_name][plot_name]['legend_list_3']
    legend_list_4 = self.figure_params[figure_name][plot_name]['legend_list_4']
    sns.set()
    fig, ax = plt.subplots(2,2, figsize=(20,10))    
    ###################################
    ##Read & make data for figure [0][0]
    n_colors = len(contract_list) + len(available_water_keys)
    aw_colors = sns.color_palette('afmhot_r', n_colors = n_colors)
    aw_colors2 = sns.color_palette('afmhot_r', n_colors = 5)

    ##Find Deliveries, make cumulative throught the year
    for del_count, contract_del in enumerate(contract_list):
      if contract_del == 'swpdelta':
        daily_deliveries = self.values['delta_HRO_pump']
      elif contract_del == 'cvpdelta':
        daily_deliveries = self.values['delta_TRP_pump']
      else:
        daily_deliveries = self.values[contract_del + '_contract'] + self.values[reservoir_name + '_flood']
      cumulative_deliveries = np.zeros(len(daily_deliveries))
      if contract_del == 'swpdelta' or contract_del == 'cvpdelta' or contract_del == 'cvpexchange':     
        for x in range(0, len(daily_deliveries)):
          if self.day_month[x] == 1 and self.month[x] == 10:
            cumulative_deliveries[x] = daily_deliveries[x]
          else:
            cumulative_deliveries[x] = cumulative_deliveries[x-1] + daily_deliveries[x]
      else:
        for x in range(0, len(daily_deliveries)):
          cumulative_deliveries[x] = daily_deliveries[x]

      ##Plot deliveries w/ projections for future delivery
      if del_count == 0:
        plt_clr = aw_colors[del_count]
        ax[0][0].fill_between(self.index, np.zeros(len(daily_deliveries)), cumulative_deliveries, color = plt_clr, edgecolor = plt_clr, alpha = 0.8)
        bottom = cumulative_deliveries
        for clr_cnt, res_aw in enumerate(available_water_keys):
          if res_aw == 'delta_uncontrolled_swp' or res_aw == 'delta_uncontrolled_cvp':
            available_water = self.values[res_aw]
          else:
            available_water = self.values[res_aw + '_available_storage']
          available_water[available_water < 0.0] = 0.0
          plt_clr = aw_colors[clr_cnt + 1]
          ax[0][0].fill_between(self.index, bottom, available_water + bottom, color = plt_clr, edgecolor = plt_clr, alpha = 0.8)
          bottom += available_water
      else:
        plt_clr = aw_colors[del_count + len(available_water_keys) - 1]
        ax[0][0].fill_between(self.index, bottom, cumulative_deliveries + bottom, color = delivery_color, edgecolor = delivery_color, alpha = 0.8)
        bottom += cumulative_deliveries
      
      #Plot Projected allocation as a line
      plt_clr = 'beige'
      if contract_del == 'swpdelta':
        project_allocation = self.values['delta_swp_allocation']
      elif contract_del == 'cvpdelta':
        project_allocation = self.values['delta_cvp_allocation']
      else:
        project_allocation = self.values[contract_del + '_allocation']
      ax[0][0].plot(self.index, project_allocation, linewidth = 2.0, color = 'beige', path_effects=[pe.Stroke(linewidth=5, foreground='black'), pe.Normal()])
      contract_deliveries_y_max = np.ceil((max(bottom.values) * 1.2)/1000.9) * 1000.0
      contract_deliveries_y_min = 0.0
     
    ###################################
    ##Read & make data for figure [1][0]
    #Three x-axes, stacked
    ax2 = ax[1][0].twinx()
    ax2o = ax[1][0].twinx()
    axis_order = [ax2o, ax2, ax[1][0]]
    plot_range_res_flood = {}
    bottom = np.zeros(len(self.index))
    #plot reservoir features on each x-axis
    for fts, sub_ax, fts_clr in zip(reservoir_features, axis_order, reservoir_feature_colors):
      daily_res_values = self.values[reservoir_name + '_' + fts]
      if fts == 'flood_deliveries' or fts == 'flood_spill':
        cumulative_res_values = np.zeros(len(daily_res_values))
        for x in range(0, len(daily_res_values)):  
          if self.day_month[x] == 1 and self.month[x] == 10:
            cumulative_res_values[x] = daily_res_values[x]
          else:
            cumulative_res_values[x] = daily_res_values[x] + cumulative_res_values[x-1]
        
        sub_ax.fill_between(self.index, np.zeros(len(cumulative_res_values)), cumulative_res_values * (-1), facecolor = fts_clr, edgecolor = 'black', linewidth = 0.5)
        plot_range_res_flood[fts] = [-1 * np.ceil(max(cumulative_res_values) / 100) * 100, 0.0]
      elif fts == 'days_til_full':
        plot_range_res_flood[fts] = [0.0, 200.0]
        daily_res_values[daily_res_values > 200.0] = 200.0
        sub_ax.fill_between(self.index, np.zeros(len(daily_res_values)), daily_res_values, facecolor = fts_clr, edgecolor = 'none', linewidth = 0.5)        
      else:
        sub_ax.fill_between(self.index, np.zeros(len(daily_res_values)), daily_res_values, facecolor = fts_clr, edgecolor = 'black', linewidth = 0.5)
        plot_range_res_flood[fts] = [0.0, np.ceil(max(daily_res_values) / 100) * 100]
    #Dividing lines between x-axis  
    ax2.plot(self.index, np.zeros(len(self.index)), color = 'black', linewidth = 3.0, zorder = 5) 
    ax2o.plot(self.index, np.zeros(len(self.index)), color = 'black', linewidth = 3.0, zorder = 5) 

    ###################################
    ##Read & make data for figure [0][1]

    ##Get remaining demand in the water year
    daily_demand = self.values[district_label + '_irr_demand']
    for x in district_private_labels:
      daily_demand += self.values[x + '_' + district_key + '_irr_demand']
    ##Get private pumping in water year
    private_gw = self.values[district_label + '_pumping']
    for x in district_private_labels:
      private_gw += self.values[x + '_' + district_key + '_pumping']
    #Get cumulative irrigation (all surface sources)
    total_irrigation = np.zeros(len(daily_demand))
    for contract in district_contracts:
      delivery_name = district_label + '_' + contract + '_delivery'
      recharge_name = district_label + '_' + contract + '_recharged'
      flood_irr_name = district_label + '_' + contract + '_flood_irrigation'
      if delivery_name in self.values:
        total_irrigation += self.values[delivery_name]
      if recharge_name in self.values:
        total_irrigation -= self.values[recharge_name]
      if flood_irr_name in self.values:
        total_irrigation += self.values[flood_irr_name]    
    for x in district_private_labels:
      for contract in district_contracts:
        delivery_name = x + '_' + district_key + '_' + contract + '_delivery'
        recharge_name = x + '_' + district_key + '_' + contract + '_recharged'
        flood_irr_name = x + '_' + district_key + '_' + contract + '_flood_irrigation'
        if delivery_name in self.values:
          total_irrigation += self.values[delivery_name]
        if recharge_name in self.values:
          total_irrigation -= self.values[recharge_name]
        if flood_irr_name in self.values:
          total_irrigation += self.values[flood_irr_name]    

    ##Aggregate Irrigation Demands by wateryear
    total_demand = np.zeros(self.number_years)
    remaining_demand = np.zeros(self.T)
    cumulative_gw_pump = np.zeros(self.T)
    for x in range(0, len(daily_demand)):
      if self.month[x] >= 10:
        wateryear = self.year[x] - self.year[0]
      else:
        wateryear = self.year[x] - self.year[0] - 1
      if self.month[x] == 10 and self.day_month[x] == 1:
        total_demand[wateryear] = daily_demand[x]
      else:
        total_demand[wateryear] += daily_demand[x]
    for x in range(0, len(daily_demand)):
      if self.month[x] >= 10:
        wateryear = self.year[x] - self.year[0]
      else:
        wateryear = self.year[x] - self.year[0] - 1
      if self.month[x] == 10 and self.day_month[x] == 1:
        remaining_demand[x] = total_demand[wateryear]
        cumulative_gw_pump[x] = private_gw[x]
      else:
        remaining_demand[x] = remaining_demand[x-1] - daily_demand[x]
        cumulative_gw_pump[x] = cumulative_gw_pump[x-1] + private_gw[x]
    
    #Get total groundwater banking storage
    bank_list = ['pioneer', 'kwb', 'berrendawb', 'b2800', 'northkernwb', 'rosedale', 'semitropic', 'arvin']
    total_bank_accounts = np.zeros(len(daily_demand))
    for bank_name in bank_list:
      if bank_name + '_' + district_key in self.values:
        total_bank_accounts += self.values[bank_name + '_' + district_key]
      for gw_acct in district_private_keys:
        if bank_name + '_' + gw_acct in self.values:
          total_bank_accounts += self.values[bank_name + '_' + gw_acct] 
    #Get cap on groundwater pumping
    if district_label + '_dynamic_recovery_cap' in self.values:
      recovery_cap = self.values[district_label + '_dynamic_recovery_cap']
      for prv in district_private_labels:
        recovery_cap += self.values[prv + '_' + district_key  + '_dynamic_recovery_cap']
      for cnt, x in enumerate(recovery_cap):
        if total_bank_accounts[cnt] > x:
          total_bank_accounts[cnt] = x
    #Get total projected surface water allocations
    total_projected = np.zeros(len(daily_demand))
    for dist_con in district_contracts:
      total_projected += self.values[district_label + '_' + dist_con + '_projected']
      for prv in district_private_labels:
        total_projected += self.values[prv + '_' + district_key + '_' + dist_con + '_projected']
        
    #Get total use of groundwater banking
    recovery_use = np.zeros(len(daily_demand))
    if district_label + '_recover_banked' in self.values:
      recovery_use += self.values[district_label + '_recover_banked']
    if district_label + '_exchanged_GW' in self.values:
      recovery_use += self.values[district_label + '_exchanged_GW']
    for prv in district_private_labels:
      if prv + '_' + district_key + '_recover_banked' in self.values:
        recovery_use += self.values[prv + '_' + district_key + '_recover_banked']
      if prv + '_' + district_key + '_exchanged_GW' in self.values:
        recovery_use += self.values[prv + '_' + district_key + '_exchanged_GW'] 

    ax[0][1].fill_between(self.index, np.zeros(len(total_projected)), total_projected, facecolor = aw_colors2[0], edgecolor = 'black', linewidth = 0.25, alpha = 0.8)
    ax[0][1].fill_between(self.index, total_projected , total_projected + total_bank_accounts, facecolor = aw_colors2[4], edgecolor = 'black', linewidth = 0.25, alpha = 0.8)
    ax[0][1].fill_between(self.index, np.zeros(len(total_irrigation)), total_irrigation*(-1.0), facecolor = aw_colors2[1], edgecolor = 'black', linewidth = 0.25, alpha = 0.8)     
    ax[0][1].fill_between(self.index, total_irrigation*(-1.0), (total_irrigation + cumulative_gw_pump)*(-1.0), facecolor = aw_colors2[2], edgecolor = 'black', linewidth = 0.25, alpha = 0.8) 
    ax[0][1].fill_between(self.index, (total_irrigation + cumulative_gw_pump)*(-1.0), (total_irrigation + cumulative_gw_pump + recovery_use)*(-1.0), facecolor = aw_colors2[3], edgecolor = 'black', linewidth = 0.25) 
    ax[0][1].plot(self.index, remaining_demand, color = 'beige', linewidth = 3.0, path_effects=[pe.Stroke(linewidth=5, foreground='black'), pe.Normal()], zorder = 5)
    ax[0][1].plot(self.index, np.zeros(len(self.index)), color = 'black', linewidth = 1.0)
    plot_lim_drought_op = np.ceil(1.2 * max( [ max( total_irrigation + cumulative_gw_pump + recovery_use ), max( total_projected + total_bank_accounts ) ] ) / 100.0 ) * 100.0
    
    ##################################################
    ##Read & make data for figure [1][1]
    initial_carryover = np.zeros(len(self.index))
    total_deliveries = np.zeros(len(self.index))
    total_recharged = np.zeros(len(self.index))
    contract_flood_recharge = np.zeros(len(self.index))
    total_recharge_cap = np.zeros(len(self.index))

    ##Find deliveries made for recharge and remaining carryover
    for dist_con in district_contracts:
      initial_carryover += self.values[district_label + '_' + dist_con + '_carryover']
      total_deliveries += self.values[district_label + '_' + dist_con + '_delivery']
      total_recharged += self.values[district_label + '_' + dist_con + '_recharged']
      contract_flood_recharge += self.values[district_label + '_' + dist_con + '_flood']
      total_recharge_cap += self.values[district_label + '_' + dist_con + '_dynamic_recharge_cap']
      for prv in district_private_labels:
        initial_carryover += self.values[prv + '_' + district_key + '_' + dist_con + '_carryover'] 
        total_deliveries += self.values[prv + '_' + district_key + '_' + dist_con + '_delivery']
        total_recharged += self.values[prv + '_' + district_key + '_' + dist_con + '_recharged']
        contract_flood_recharge += self.values[prv + '_' + district_key + '_' + dist_con + '_flood']
        total_recharge_cap += self.values[prv + '_' + district_key + '_' + dist_con + '_dynamic_recharge_cap']
        cnt = 0
              
      remaining_carryover = np.zeros(len(initial_carryover))
      numdays_fillup  = self.values[reservoir_name + '_days_til_full']
      for x in range(0, len(initial_carryover)):
        if self.month[x] > 9:
          dowy = self.day_year[x] - 273
        else:
          dowy = self.day_year[x] + 92
        if dowy + numdays_fillup[x] > 365:
          remaining_carryover[x] += max(initial_carryover[x] - total_deliveries[x], 0.0) + max(total_projected[x] - remaining_demand[x], 0.0)
        else:
          remaining_carryover[x] += max(initial_carryover[x] - total_deliveries[x], 0.0)

    consecutive_counter = 0
    daily_recharge = np.zeros(len(total_recharged))
    daily_contract_flood_recharge = np.zeros(len(total_recharged))
    cum_recharge = np.zeros(len(total_recharged))
    cum_contract_flood_recharge = np.zeros(len(total_recharged))
    for x in range(0, len(total_recharged)):  
      #Find recharge by flood period
      if self.month[x] == 10 and self.day_month[x] == 1:
        daily_recharge[x] = total_recharged[x]
        daily_contract_flood_recharge[x] = contract_flood_recharge[x]
      else:
        daily_recharge[x] = total_recharged[x] - total_recharged[x-1]
        daily_contract_flood_recharge[x] = contract_flood_recharge[x] - contract_flood_recharge[x-1]

      if daily_recharge[x] + daily_contract_flood_recharge[x] == 0.0:
        consecutive_counter += 1
        if consecutive_counter > 10:
          cum_recharge[x] = 0.0
          cum_contract_flood_recharge[x] = 0.0
        else:
          cum_recharge[x] = daily_recharge[x] + cum_recharge[x-1]
          cum_contract_flood_recharge[x] = daily_contract_flood_recharge[x] + cum_contract_flood_recharge[x-1]
      else:
        consecutive_counter = 0
        cum_recharge[x] = daily_recharge[x] + cum_recharge[x-1]
        cum_contract_flood_recharge[x] = daily_contract_flood_recharge[x] + cum_contract_flood_recharge[x-1]


    ###Plot Figure
    ax[1][1].fill_between(self.index, np.zeros(len(total_recharge_cap)), total_recharge_cap, color = reservoir_feature_colors[1])
    ax[1][1].plot(self.index, remaining_carryover, color = 'beige', linewidth = 3.0, path_effects=[pe.Stroke(linewidth=5, foreground='black'), pe.Normal()], zorder = 5)
    ax[1][1].fill_between(self.index, np.zeros(len(total_recharged)), total_recharged*(-1.0), facecolor = reservoir_feature_colors[3], edgecolor = 'black', linewidth = 1.0)
    ax[1][1].fill_between(self.index, total_recharged*(-1.0), contract_flood_recharge*(-1.0) + total_recharged*(-1.0), facecolor = reservoir_feature_colors[2], edgecolor = 'black', linewidth = 1.0)
    ax[1][1].plot(self.index, np.zeros(len(self.index)), color = 'black', linewidth = 1.0, zorder = 4) 


    ax[0][0].grid(False, axis = 'both')
    ax[0][0].set_xlim([self.index[0], self.index[-1]])
    ax[0][0].set_ylim([contract_deliveries_y_min, contract_deliveries_y_max])
    ax[0][0].set_title(subplot_titles[0], fontsize = 16, weight = 'bold', fontname = 'Gill Sans MT')
    ax[0][0].set_ylabel('Project Allocation (tAF)', fontsize = 12, weight = 'bold', fontname = 'Gill Sans MT')

    ax[0][1].grid(False, axis = 'both')
    y_loc = np.arange(plot_lim_drought_op * (-1.0), plot_lim_drought_op + plot_lim_drought_op / 4, plot_lim_drought_op / 4)
    y_lab = np.absolute(y_loc) 
    ax[0][1].set_yticks(y_loc)
    ax[0][1].set_yticklabels(y_lab)
    ax[0][1].set_xlim([self.index[5845], self.index[-1]])
    ax[0][1].set_ylim([-1 * plot_lim_drought_op, plot_lim_drought_op])
    ax[0][1].set_title(subplot_titles[1], fontsize = 16, weight = 'bold', fontname = 'Gill Sans MT')
    ax[0][1].set_ylabel('                                     Water Source \n Annual GW Use (tAF)       Projections (tAF)        ', fontsize = 12, weight = 'bold', fontname = 'Gill Sans MT')

    counter_min = -2
    counter_max = 0
    tick_label_list = []
    for x, y in zip(reservoir_features, axis_order):
      plot_extent = plot_range_res_flood[x][1] - plot_range_res_flood[x][0]
      max_value = plot_range_res_flood[x][1] + plot_extent * counter_max
      min_value = plot_range_res_flood[x][0] + plot_extent * counter_min
   
      y.set_ylim([min_value, max_value])
      y.grid(False, axis = 'both')
      y.set_yticks([])
      tick_label_list.append(int(0.9 * plot_range_res_flood[x][1]))
      tick_label_list.append(int(0.5 * (plot_range_res_flood[x][1] - plot_range_res_flood[x][0]) + plot_range_res_flood[x][0]))
      tick_label_list.append(int(0.1 * (plot_range_res_flood[x][1] - plot_range_res_flood[x][0]) + plot_range_res_flood[x][0]))
      y.set_xlim([self.index[0], self.index[-1]])
      counter_max += 1
      counter_min += 1      
    tick_loc_list = []
    counter_extend = 1.0
    for xx in reservoir_features:
      tick_loc_list.append(plot_range_res_flood[x][1] + plot_extent * (counter_extend + 0.9))
      tick_loc_list.append(plot_range_res_flood[x][1] + plot_extent * (counter_extend + 0.5))
      tick_loc_list.append(plot_range_res_flood[x][1] + plot_extent * (counter_extend + 0.1))
      counter_extend -= 1
    y.set_yticks(tick_loc_list)
    y.set_yticklabels(np.absolute(tick_label_list))
    y.set_title(subplot_titles[2], fontsize = 16, weight = 'bold', fontname = 'Gill Sans MT')
    y.set_ylabel('     Flood              Fill Time                              \nOperations (tAF)       (days)        Storage (tAF)      ', fontsize = 12, weight = 'bold', fontname = 'Gill Sans MT')


    ax[1][1].grid(False, axis = 'both')
    axis_max = np.ceil(max([max(total_recharged + contract_flood_recharge), max(remaining_carryover)])/10.0) * 10
    tick_loc = np.arange(-1 * axis_max, axis_max + axis_max/4, axis_max/4)
    tick_lab = np.absolute(tick_loc)
    ax[1][1].set_yticks(tick_loc)
    ax[1][1].set_yticklabels(tick_lab)
    ax[1][1].set_ylim([-1 * axis_max, axis_max])
    ax[1][1].set_xlim([self.index[2924], self.index[4018]])
    ax[1][1].set_title(subplot_titles[3], fontsize = 16, weight = 'bold', fontname = 'Gill Sans MT')
    ax[1][1].set_ylabel('                                     Recharge/Carryover \n    Total Recharge (tAF)      Projections (tAF)         ', fontsize = 12, weight = 'bold', fontname = 'Gill Sans MT')

    legend_elements = []
    for cnt, xx in enumerate(legend_list_1):
      legend_elements.append(Patch(facecolor = aw_colors[cnt], edgecolor = 'black', label = xx))
    legend_elements.append(Line2D([0], [0], color = 'beige', linewidth = 3.0, label = 'Projected SWP Allocation'))
    ax[0][0].legend(handles = legend_elements, loc = 'upper left', ncol = 2, framealpha  = 0.4, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':10}) 

    legend_elements = []
    for cnt, xx in enumerate(legend_list_2):
      legend_elements.append(Patch(facecolor = reservoir_feature_colors[cnt], edgecolor = 'black', label = xx))
    ax[1][0].legend(handles = legend_elements, loc = 'lower right', framealpha  = 0.4, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':10}) 

    legend_elements = []
    for cnt, xx in enumerate(legend_list_3):
      legend_elements.append(Patch(facecolor = aw_colors2[cnt], edgecolor = 'black', label = xx))
    legend_elements.append(Line2D([0], [0], color = 'beige', linewidth = 3.0, label = 'Remaining Irrigation Demand'))
    ax[0][1].legend(handles = legend_elements, loc = 'lower left', ncol = 2, framealpha  = 0.4, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':10}) 

    legend_elements = []
    for cnt, xx in enumerate(legend_list_4):
      legend_elements.append(Patch(facecolor = reservoir_feature_colors[cnt+1], edgecolor = 'black', label = xx))
    legend_elements.append(Line2D([0], [0], color = 'beige', linewidth = 3.0, label = 'Current/Projected Carryover Storage'))
    ax[1][1].legend(handles = legend_elements, loc = 'lower left', framealpha  = 0.4, shadow = True, prop={'family':'Gill Sans MT','weight':'bold','size':10}) 

    for x in range(0,2):
      for y in range(0,2):
        for tick in ax[x][y].get_xticklabels():
          tick.set_fontname('Gill Sans MT')
        for tick in ax[x][y].get_yticklabels():
          tick.set_fontname('Gill Sans MT')
  
    #ax[0][0].text(self.index[6575], 7200, 'A', fontsize = 24, weight = 'bold', fontname = 'Gill Sans MT')
    #ax[1][0].text(self.index[6575], 1700, 'C', fontsize = 24, weight = 'bold', fontname = 'Gill Sans MT')
    #ax[0][1].text(self.index[7162], 400, 'B', fontsize = 24, weight = 'bold', fontname = 'Gill Sans MT')
    #ax[1][1].text(self.index[3909], -60, 'D', fontsize = 24, weight = 'bold', fontname = 'Gill Sans MT')


    plt.savefig(folder_name + figure_name + '_' + plot_name + '.png', dpi = 300, bbox_inches = 'tight', pad_inches = 0.0)
    if show_plot:
      plt.show()   
    plt.close()

  def make_validation_timeseries(self, folder_name, figure_name, plot_name, show_plot, use_scatter, num_cols = 1):
    #Set plotting parameters    
    simulated_list = self.figure_params[figure_name][plot_name]['label_name_1']
    simulated_unit = self.figure_params[figure_name][plot_name]['unit_converstion_1']
    observed_list = self.figure_params[figure_name][plot_name]['label_name_2']
    observed_unit = self.figure_params[figure_name][plot_name]['unit_converstion_2']
    title_list = self.figure_params[figure_name][plot_name]['title_labels']
    y_labels = self.figure_params[figure_name][plot_name]['y_label_timeseries']
    freq = self.figure_params[figure_name][plot_name]['timeseries_timestep']
    agg_method = self.figure_params[figure_name][plot_name]['aggregation_methods']
    r_not = self.figure_params[figure_name][plot_name]['notation_location']
    show_legend = self.figure_params[figure_name][plot_name]['show_legend']
    if use_scatter:
      scatter_labels = self.figure_params[figure_name][plot_name]['y_label_scatter']
      freq2 = self.figure_params[figure_name][plot_name]['scatter_timestep']
      
    sns.set()
    counter_row = 0
    counter_col = 0
    end_of_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    #Set plotting grid
    num_rows = int(np.ceil(len(simulated_list)/ num_cols)) 
    fig = plt.figure(figsize = (16, 3 * num_rows))
    if use_scatter: 
      gs = gridspec.GridSpec(len(simulated_list), 4)
    else:
      gs = gridspec.GridSpec(num_rows, num_cols)

    for counter, sim_name in enumerate(simulated_list):
      if use_scatter:  
        ax0 = plt.subplot(gs[counter,0:3])  
        ax1 = plt.subplot(gs[counter,3])
      else:
        ax0 = plt.subplot(gs[counter_row,counter_col])

      ##Get simulation results
      agg_meth = agg_method[counter]  
      simulated_values = self.values[sim_name]
      ##Get observed values
      obs_name = observed_list[counter]
      observed_values = self.observations[obs_name]
      if agg_meth == 'sum':
        simulated_week = simulated_values.resample(freq[counter]).sum() * simulated_unit[counter]  
        observed_week = observed_values.resample(freq[counter]).sum() * observed_unit[counter]
      elif agg_meth == 'mean':
        simulated_week = simulated_values.resample(freq[counter]).mean() * simulated_unit[counter]  
        observed_week = observed_values.resample(freq[counter]).mean() * observed_unit[counter]
      elif agg_meth == 'point':
        observed_week = observed_values.resample(freq[counter]).mean() * observed_unit[counter]
        simulated_week = simulated_values.resample(freq[counter]).mean() * simulated_unit[counter]  
      elif agg_meth == 'change':
        observed_week = observed_values.resample(freq[counter]).mean() * observed_unit[counter]
        simulated_week = simulated_values.resample(freq[counter]).mean() * simulated_unit[counter]  

      edge_space_week = 0.05 * (max([max(simulated_week.values), max(observed_week.values)]) - min([min(simulated_week.values), min(observed_week.values)]))
        
      ##Plot weekly validation  
      observed_week.plot(ax=ax0, color='k', use_index=True, alpha = 0.7, linewidth = 3)
      simulated_week.plot(ax=ax0, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)

      ##Annotate figures
      ax0.set_title(title_list[counter], weight = 'bold', fontname = 'Gill Sans MT')
      ax0.set_xlim(min(self.values.index[0], self.observations.index[0]), max(self.values.index[-1], self.observations.index[-1]))
      ax0.set_ylim([min([min(simulated_week.values), min(observed_week.values)]) - edge_space_week, max([max(simulated_week.values), max(observed_week.values)]) + edge_space_week])
      ax0.set_xlabel('')
      r0 = np.corrcoef(observed_week.values,simulated_week.values)[0,1]
      if show_legend[counter]:
        ax0.legend(['Observed', 'Simulated'], ncol=1)
      if r_not[counter] == 'top':
        starting_loc = int(len(self.values.index) * 0.01)
        ax0.annotate('$R^2 = %.2f$' % r0**2, xy=(self.values.index[starting_loc], max([max(simulated_week.values), max(observed_week.values)]) - edge_space_week), color='0.1')
      elif r_not[counter] == 'topright':
        starting_loc = int(len(self.values.index) * 0.2)
        ax0.annotate('$R^2 = %.2f$' % r0**2, xy=(self.values.index[-1 * starting_loc], max([max(simulated_week.values), max(observed_week.values)]) - edge_space_week), color='0.1')
      elif r_not[counter] == 'bottom':
        starting_loc = int(len(self.values.index) * 0.01)
        ax0.annotate('$R^2 = %.2f$' % r0**2, xy=(self.values.index[starting_loc], min([min(simulated_week.values), min(observed_week.values)])), color='0.1')
      if counter_col == 0:
        ax0.set_ylabel(y_labels[counter])
      else:
        ax0.set_ylabel('')
      if counter_row < num_rows - 1:
        ax0.set_xticklabels('')

      for item in [ax0.xaxis.label, ax0.yaxis.label, ax0.title]:
        item.set_fontsize(14)
        item.set_fontname('Gill Sans MT')  
      for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
        item.set_fontsize(14)
        item.set_fontname('Gill Sans MT')

      if use_scatter:
        ##Get aggregated values
        if agg_meth == 'sum':
          observed_year = observed_values.resample(freq2[counter]).sum() * observed_unit[counter]
          simulated_year = simulated_values.resample(freq2[counter]).sum() * simulated_unit[counter]
        elif agg_meth == 'mean':
          simulated_year = simulated_values.resample(freq2[counter]).mean() * simulated_unit[counter]
          observed_year = observed_values.resample(freq2[counter]).mean() * observed_unit[counter]
        elif agg_meth == 'point':
          simulated_year = simulated_values.resample(freq2[counter]).mean() * simulated_unit[counter]
          observed_year = observed_values.resample(freq2[counter]).mean() * observed_unit[counter]
          month_counter = 10
          year_counter = self.starting_year
          for xxx in range(0, len(observed_year)):
            simulated_year[xxx] = simulated_values.loc[pd.DatetimeIndex([str(year_counter) + '-' + str(month_counter) + '-' + str(end_of_month[month_counter - 1])])]*simulated_unit[counter]
            observed_year[xxx] = observed_values.loc[pd.DatetimeIndex([str(year_counter) + '-' + str(month_counter) + '-' + str(end_of_month[month_counter - 1])])]*observed_unit[counter]
            month_counter += 1
            if month_counter == 13:
              month_counter = 1
              year_counter += 1 
        elif agg_meth == 'change':
          observed_year = observed_values.resample(freq2[counter]).mean() * observed_unit[counter]
          simulated_year = simulated_values.resample(freq2[counter]).mean() * simulated_unit[counter]  
          month_counter = 10
          year_counter = self.starting_year
          for xxx in range(0, len(observed_year)):
            if freq2[counter] == 'M':
              simulated_int_start = simulated_values.loc[pd.DatetimeIndex([str(year_counter) + '-' + str(month_counter) + '-' + str(end_of_month[month_counter - 1])])]*simulated_unit[counter]
              observed_int_start = observed_values.loc[pd.DatetimeIndex([str(year_counter) + '-' + str(month_counter) + '-' + str(end_of_month[month_counter - 1])])]*observed_unit[counter]
              if xxx < len(observed_year) - 1:
                month_counter += 1
                if month_counter == 13:
                  month_counter = 1
                  year_counter += 1
                simulated_int_end = simulated_values.loc[pd.DatetimeIndex([str(year_counter) + '-' + str(month_counter) + '-' + str(end_of_month[month_counter - 1])])]*simulated_unit[counter]
                observed_int_end = observed_values.loc[pd.DatetimeIndex([str(year_counter) + '-' + str(month_counter) + '-' + str(end_of_month[month_counter - 1])])]*observed_unit[counter]
                simulated_year[xxx] = simulated_int_end.values - simulated_int_start.values
                observed_year[xxx] = observed_int_end.values - observed_int_start.values
            elif freq2[counter] == 'AS-OCT':
              simulated_int_start = simulated_values.loc[pd.DatetimeIndex([str(year_counter) + '-10-01'])]*simulated_unit[counter]
              simulated_int_end = simulated_values.loc[pd.DatetimeIndex([str(year_counter + 1) + '-9-30'])]*simulated_unit[counter]
              observed_int_start = observed_values.loc[pd.DatetimeIndex([str(year_counter) + '-10-01'])]*observed_unit[counter]
              observed_int_end = observed_values.loc[pd.DatetimeIndex([str(year_counter + 1) + '-9-30'])]*observed_unit[counter]
              year_counter += 1
              simulated_year[xxx] = simulated_int_end.values - simulated_int_start.values
              observed_year[xxx] = observed_int_end.values - observed_int_start.values

        edge_space = 0.05 * (max([max(simulated_year.values), max(observed_year.values)]) - min([min(simulated_year.values), min(observed_year.values)]))
        ##Plot 1:1 validation line
        ax1.plot([min([min(observed_year.values), min(simulated_year.values)]) - edge_space, max([max(observed_year.values), max(simulated_year.values)]) + edge_space], [min([min(observed_year.values), min(simulated_year.values)]) - edge_space, max([max(observed_year.values), max(simulated_year.values)]) + edge_space], linestyle = 'dashed', color = 'black', linewidth = 3, zorder = 3)    

        #Color scatterplot by cycle index
        scatter_index = np.zeros(len(simulated_year))              
        if freq2[counter] == 'M':
          n_colors = 12
          colors = sns.color_palette("RdBu", n_colors=n_colors)
          month_int = self.month[0]
          #Give each value in timeseries a month value (1-12) index
          for sc_idx in range(0, len(scatter_index)):
            scatter_index[sc_idx] = month_int
            month_int += 1
            if month_int == 13:
              month_int = 1
          #new color for each month
          for index_val in range(0, n_colors):
            this_month_sim = simulated_year.values[scatter_index == index_val]
            this_month_obs = observed_year.values[scatter_index == index_val]
            ax1.scatter(this_month_obs, this_month_sim, s=25, color = colors[index_val], edgecolor='black', alpha=1.0, zorder = 5)
          #Annotate Colorbar
          sm = plt.cm.ScalarMappable(cmap=pl.cm.RdBu, norm=plt.Normalize(vmin=0, vmax=12))
          clb1 = plt.colorbar(sm, ax = ax1, ticks=[0, 6, 12])
          clb1.ax.set_yticklabels(['Sept', 'Mar', 'Oct']) 
        else:
          n_colors = self.number_years
          colors = sns.color_palette("YlGn", n_colors=n_colors)
          year_int = self.year[0] + 1
          #Give each value in timeseries a year value index
          for sc_idx in range(0, len(scatter_index)):
            scatter_index[sc_idx] = year_int
            year_int += 1        
          #new color for each year
          for index_val in range(0, self.number_years):
            this_month_sim = simulated_year.values[scatter_index == (index_val + self.starting_year + 1)]
            this_month_obs = observed_year.values[scatter_index == (index_val + self.starting_year + 1)]
            ax1.scatter(this_month_obs, this_month_sim, s=75, color = colors[index_val], edgecolor='black', alpha=1.0, zorder = 5)
          #Annotate Colorbar
          sm = plt.cm.ScalarMappable(cmap=pl.cm.YlGn, norm=plt.Normalize(vmin = self.starting_year + 1, vmax=self.ending_year))
          clb1 = plt.colorbar(sm, ax = ax1, ticks=[self.starting_year+1, self.starting_year + 1 + int(self.number_years/2), self.ending_year])
          clb1.ax.set_yticklabels([self.starting_year+1, self.starting_year + 1 + int(self.number_years/2), self.ending_year])

        #Annotate figures
        if freq2[counter] == 'M':
          scatter_title = 'Monthly'
        else:
          scatter_title = 'Annual'
        ax1.set_ylabel('Simulated ' + scatter_labels[counter])
        ax1.set_xlabel('Observed ' + scatter_labels[counter])
        ax1.set_title(scatter_title + ' Observed vs. Simulated', weight = 'bold', fontname = 'Gill Sans MT')
        r1 = np.corrcoef(observed_year.values,simulated_year.values)[0,1]
        ax1.annotate('$R^2 = %.2f$' % r1**2, xy=(min([min(simulated_year.values), min(observed_year.values)]),max([max(simulated_year.values), max(observed_year.values)]) - edge_space), color='0.1') 
        ax1.set_xlim([min([min(simulated_year.values), min(observed_year.values)]) - edge_space,max([max(simulated_year.values), max(observed_year.values)]) + edge_space])
        ax1.set_ylim([min([min(simulated_year.values), min(observed_year.values)]) - edge_space,max([max(simulated_year.values), max(observed_year.values)]) + edge_space])
        for item in [ax1.xaxis.label, ax1.yaxis.label, ax1.title]:
          item.set_fontsize(14)
          item.set_fontname('Gill Sans MT')  
        for item in (ax1.get_xticklabels() + ax1.get_yticklabels()):
          item.set_fontsize(14)
          #item.set_fontname('Gill Sans MT')      
      
      counter_row += 1
      if counter_row == num_rows:
        counter_row = 0
        counter_col += 1

    plt.tight_layout()  
    plt.savefig(folder_name + figure_name + '_' + plot_name + '.png', dpi = 150, bbox_inches = 'tight', pad_inches = 0.0)
    if show_plot:
      plt.show()
    plt.close()

  def plot_account_flows(self, folder_name, fig_name, plot_name, timesteps, snapshot_range):
    open_area = 0.2
    min_label_height = 0.06
    source_types = ['delivered', 'projected']
    source_alphas = [0.8, 0.2]

    color_list = ['teal', 'steelblue', 'forestgreen', 'forestgreen', 'forestgreen', 'olive', 'olive', 'goldenrod', 'darkorange', 'indianred', 'orchid', 'slategray']
    color_groups = ['delta', 'tableA', 'exchange', 'cvpdelta', 'cvc', 'friant1', 'friant2', 'kern', 'kings', 'kaweah', 'tule', 'ground']

    source_groups = ['shasta', 'folsom', 'oroville', 'yuba', 'uncontrolled']
    destination_groups = ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success', 'delta', 'carryover']
    destination_groups_b = ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']
    away_groups = ['delta', 'carryover']
    segment_dictionary = make_source_dictionaries(source_groups, destination_groups, source_types, color_groups, timesteps)

    source_groups_ii = ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success', 'carryover']
    source_groups_ii_b = ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']
    destination_groups_ii = ['cvpexchange', 'cvpdelta', 'crossvalley', 'swpdelta', 'friant1', 'friant2', 'kernriver', 'kingsriver', 'kaweahriver', 'tuleriver', 'flood']
    away_groups_ii = ['carryover']
    segment_dictionary_ii = make_source_dictionaries(source_groups_ii, destination_groups_ii, source_types, color_groups, timesteps)

    source_groups_iii = ['cvpexchange', 'cvpdelta', 'crossvalley', 'swpdelta', 'friant1', 'friant2', 'kernriver', 'kingsriver', 'kaweahriver', 'tuleriver', 'flood', 'private pumping', 'groundwater banks']
    source_groups_iii_b = ['cvpexchange', 'cvpdelta', 'crossvalley', 'swpdelta', 'friant1', 'friant2', 'kernriver', 'kingsriver', 'kaweahriver', 'tuleriver', 'flood']
    destination_groups_iii = ['exchange', 'cvpsanluis', 'urban', 'kcwa', 'cvpfriant', 'othermisc']
    away_groups_iii = ['private pumping', 'groundwater banks']
    segment_dictionary_iii = make_source_dictionaries(source_groups_iii, destination_groups_iii, source_types, color_groups, timesteps)

    source_groups_iv = ['exchange', 'cvpsanluis', 'urban', 'kcwa', 'cvpfriant', 'othermisc']
    destination_groups_iv = ['irrigation', 'urban', 'in-lieu recharge', 'direct recharge', 'carryover']
    destination_groups_iv_b = ['irrigation', 'urban', 'in-lieu recharge', 'direct recharge']
    away_groups_iv = ['carryover']
    segment_dictionary_iv = make_source_dictionaries(source_groups_iv, destination_groups_iv, source_types, color_groups, timesteps)


    district_groups = {}
    district_groups['urban'] = ['socal', 'southbay', 'centralcoast', 'metropolitan', 'castaic', 'coachella', 'bakersfield', 'fresno']
    district_groups['kcwa'] = ['berrenda', 'belridge', 'buenavista', 'cawelo', 'henrymiller', 'ID4', 'kerndelta', 'losthills', 'rosedale', 'semitropic', 'tehachapi', 'tejon', 'westkern', 'wheeler', 'kcwa', 'wonderful', 'dudleyridge','otherswp']
    district_groups['cvpsanluis'] =  ['sanluiswater', 'panoche', 'delpuerto', 'westlands','othercvp']
    district_groups['cvpfriant'] = ['arvin', 'delano', 'pixley', 'exeter', 'kerntulare', 'lindmore', 'lindsay', 'lowertule', 'porterville', 'saucelito', 'shaffer', 'sosanjoaquin', 'teapot', 'terra', 'tulare', 'fresnoid', 'chowchilla', 'maderairr','otherfriant','othercrossvalley']
    district_groups['exchange'] = ['otherexchange',]

    district_groups['othermisc'] = ['northkern', 'tularelake', 'othertule', 'otherkaweah', 'consolidated', 'alta', 'kaweahdelta', 'krwa']
    urban_district_list = ['socal', 'southbay', 'centralcoast', 'metropolitan', 'castaic', 'coachella', 'bakersfield', 'fresno']
    private_district_list = ['wonderful', 'metropolitan', 'castaic', 'coachella']
    private_district_keys  = {}
    private_district_keys['wonderful'] = ['LHL', 'BLR', 'BDM']
    private_district_keys['metropolitan'] = ['SOC',]
    private_district_keys['castaic'] = ['SOC',]
    private_district_keys['coachella'] = ['SOC',]
   
    pumping_names = ['delta_TRP_pump', 'delta_HRO_pump']
    reservoir_locs = ['sanluisfederal', 'sanluisstate']
    project_names = ['cvp', 'swp']
    project_color_groups = ['exchange', 'tableA']
    storage_releases = {}
    storage_releases['cvp'] = ['shasta', 'folsom']
    storage_releases['swp'] = ['oroville', 'yuba']

    for t in range(0, timesteps):

      for pump, res, proj, res_color in zip(pumping_names, reservoir_locs, project_names, project_color_groups):
        daily_pumping = self.values.loc[self.index[t], pump]
        pumping_accounted = 0.0
        total_stored_to_delta = 0.0
        if self.month[t] == 10 and self.day_month[t] == 1:
          for release_name in storage_releases[proj]:
            this_release = self.values.loc[self.index[t], release_name + '_R_to_delta']
            segment_dictionary[release_name]['delivered'][res][res_color][t] = max( min( daily_pumping - pumping_accounted, this_release), 0.0)
            segment_dictionary[release_name]['delivered']['delta'][res_color][t] = max( min( this_release + pumping_accounted - daily_pumping, this_release), 0.0)
            pumping_accounted += this_release
          segment_dictionary['uncontrolled']['delivered'][res]['delta'][t] = max( daily_pumping - pumping_accounted, 0.0)
          total_stored_to_delta += max(pumping_accounted - daily_pumping, 0.0)
        else:
          for release_name in storage_releases[proj]:
            this_release = self.values.loc[self.index[t], release_name + '_R_to_delta']
            segment_dictionary[release_name]['delivered'][res][res_color][t] = max( min( daily_pumping - pumping_accounted, this_release), 0.0)  + segment_dictionary[release_name]['delivered'][res][res_color][t - 1]
            segment_dictionary[release_name]['delivered']['delta'][res_color][t] = max( min( this_release + pumping_accounted - daily_pumping, this_release), 0.0)  + segment_dictionary[release_name]['delivered']['delta'][res_color][t - 1]
            pumping_accounted += this_release
          segment_dictionary['uncontrolled']['delivered'][res]['delta'][t] = max( daily_pumping - pumping_accounted, 0.0) + segment_dictionary['uncontrolled']['delivered'][res]['delta'][t - 1]
          total_stored_to_delta += max(pumping_accounted - daily_pumping, 0.0)

      total_delta_outflow = self.values.loc[self.index[t], 'delta_outflow'] 
      if self.month[t] == 10 and self.day_month[t] == 1:
        segment_dictionary['uncontrolled']['delivered']['delta']['delta'][t] = max( total_delta_outflow - total_stored_to_delta, 0.0)
      else:
        segment_dictionary['uncontrolled']['delivered']['delta']['delta'][t] = max( total_delta_outflow - total_stored_to_delta, 0.0) + segment_dictionary['uncontrolled']['delivered']['delta']['delta'][t - 1]

      uncontrolled_to_delta = 0.0   
      for proj, res_so, res_color in zip(project_names, reservoir_locs, project_color_groups):
        total_project_pumping = 0.0
        for res_no in storage_releases[proj]:
          total_project_pumping += segment_dictionary[res_no]['delivered'][res_so][res_color][t]
        total_project_pumping += segment_dictionary['uncontrolled']['delivered'][res_so]['delta'][t]

        allocation_name = 'delta_' + proj + '_allocation'
        delta_name = 'delta_uncontrolled_' + proj
        remaining_allocation = max(self.values.loc[self.index[t], allocation_name] - total_project_pumping, 0.0) 
        delta_allocation =  max(self.values.loc[self.index[t], delta_name], 0.0)
        segment_dictionary['uncontrolled']['projected'][res_so]['delta'][t] = max( min( delta_allocation, remaining_allocation), 0.0)
        uncontrolled_to_delta += max( delta_allocation - remaining_allocation, 0.0)
        running_available_storage = 0.0
        for res_no in storage_releases[proj]:
          available_storage_name = res_no + '_available_storage'
          res_available_storage = max(self.values.loc[self.index[t], available_storage_name], 0.0)
          segment_dictionary[res_no]['projected'][res_so][res_color][t] = max( min( res_available_storage, remaining_allocation - delta_allocation - running_available_storage), 0.0)
          segment_dictionary[res_no]['projected']['carryover'][res_color][t] = max( min( res_available_storage + running_available_storage + delta_allocation - remaining_allocation, res_available_storage), 0.0)
          segment_dictionary[res_no]['projected']['delta'][res_color][t] = self.values.loc[self.index[t], res_no + '_outflow_release']
          running_available_storage += res_available_storage

#      delta_req_name = 'delta_remaining_outflow'
#      delta_req_outflow = self.values.loc[self.index[t], delta_req_name]
#      for proj in project_names:
#        for res_no in storage_releases[proj]:
#          print(delta_req_outflow)
#          res_req_outflow_name = res_no + '_outflow_release'
#          delta_req_outflow -= max(self.values.loc[self.index[t], res_req_outflow_name], 0.0)
#          print(delta_req_outflow)
#      segment_dictionary['uncontrolled']['projected']['delta']['delta'][t] = uncontrolled_to_delta + max(delta_req_outflow, 0.0)
      segment_dictionary['uncontrolled']['projected']['delta']['delta'][t] = uncontrolled_to_delta
 


      contract_names = {}
      contract_keys = {}
      contract_names['sanluisfederal'] = ['exchange', 'cvpdelta', 'cvc']
      contract_names['sanluisstate'] = ['tableA',]
      contract_names['millerton'] = ['friant1', 'friant2']
      contract_names['isabella'] = ['kern',]
      contract_names['pine flat'] = ['kings',]
      contract_names['kaweah'] = ['kaweah',]
      contract_names['success'] = ['tule',]

      contract_keys['sanluisfederal'] = ['cvpexchange', 'cvpdelta', 'crossvalley']
      contract_keys['sanluisstate'] = ['swpdelta',]
      contract_keys['millerton'] = ['friant1', 'friant2']
      contract_keys['isabella'] = ['kernriver',]
      contract_keys['pine flat'] = ['kingsriver',]
      contract_keys['kaweah'] = ['kaweahriver',]
      contract_keys['success'] = ['tuleriver',]

      for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
        
        carryover_flood_label = res_name + '_reclaimed_carryover'
        contract_flood_label = res_name + '_contract_flooded'
        if contract_flood_label in self.values:
          contract_flood_loss = self.values.loc[self.index[t], contract_flood_label]    
        if carryover_flood_label in self.values:
          carryover_flood_loss = self.values.loc[self.index[t], carryover_flood_label]

        for contract_name, contract_key in zip(contract_names[res_name], contract_keys[res_name]):
          carryover_label = contract_key + '_carryover'
          tot_carryover = 0.0
          if carryover_label in self.values:
            tot_carryover = min(self.values.loc[self.index[t], contract_key + '_carryover'], 0.0)#get negative carryover values
          segment_dictionary_ii[res_name]['delivered'][contract_key][contract_name][t] = self.values.loc[self.index[t], contract_key + '_contract']
          segment_dictionary_ii[res_name]['projected'][contract_key][contract_name][t] = max(self.values.loc[self.index[t], contract_key + '_allocation'] - self.values.loc[self.index[t], contract_key + '_contract'] + tot_carryover, 0.0)
#          segment_dictionary_ii[res_name]['projected'][contract_key][contract_name][t] = max(self.values.loc[self.index[t], contract_key + '_allocation'], 0.0)

          if contract_key + '_flood' in self.values:
            if contract_flood_label in self.values:
              segment_dictionary_ii[res_name]['delivered']['flood'][contract_name][t] = min(self.values.loc[self.index[t], contract_key + '_flood'], contract_flood_loss)
              segment_dictionary_ii['carryover']['delivered']['flood'][contract_name][t] = self.values.loc[self.index[t], contract_key + '_flood'] - min(self.values.loc[self.index[t], contract_key + '_flood'], contract_flood_loss)
              contract_flood_loss -= min(self.values.loc[self.index[t], contract_key + '_flood'], contract_flood_loss)
            else:
              segment_dictionary_ii[res_name]['delivered']['flood'][contract_name][t] = self.values.loc[self.index[t], contract_key + '_flood']
            if carryover_flood_label in self.values:
              total_shifted = min(carryover_flood_loss, segment_dictionary_ii[res_name]['projected'][contract_key][contract_name][t] + segment_dictionary_ii[res_name]['delivered'][contract_key][contract_name][t])
           
              segment_dictionary_ii['carryover']['projected'][contract_key][contract_name][t] += (total_shifted - min(total_shifted, segment_dictionary_ii[res_name]['delivered'][contract_key][contract_name][t]))
              segment_dictionary_ii[res_name]['projected'][contract_key][contract_name][t] -= (total_shifted - min(total_shifted, segment_dictionary_ii[res_name]['delivered'][contract_key][contract_name][t]))
              segment_dictionary_ii['carryover']['delivered'][contract_key][contract_name][t] += min(total_shifted, segment_dictionary_ii[res_name]['delivered'][contract_key][contract_name][t])
              segment_dictionary_ii[res_name]['delivered'][contract_key][contract_name][t] -= min(total_shifted, segment_dictionary_ii[res_name]['delivered'][contract_key][contract_name][t])
              carryover_flood_loss -= total_shifted

          for district_group in destination_groups_iii:
            for district_name in district_groups[district_group]:
              tot_carryover = 0.0
              tot_delivered = 0.0
              tot_projected = 0.0
              tot_flood = 0.0
              tot_flood_irr = 0.0
              tot_recharge = 0.0
              if district_name in private_district_list:
                for host_district_keys in private_district_keys[district_name]:
                  carryover_label = district_name + '_' + host_district_keys + '_' + contract_name + '_carryover'
                  delivery_label = district_name + '_' + host_district_keys + '_' + contract_name + '_delivery'
                  projected_label = district_name + '_' + host_district_keys + '_' + contract_name + '_projected'
                  flood_label = district_name + '_' + host_district_keys + '_' + contract_name + '_flood'
                  flood_irr_label = district_name + '_' + host_district_keys + '_' + contract_name + '_flood_irrigation'
                  recharge_label = district_name + '_' + host_district_keys + '_' + contract_name + '_recharged'
                  if carryover_label in self.values:
                    tot_carryover += self.values.loc[self.index[t], carryover_label]
                  if delivery_label in self.values:
                    tot_delivered += self.values.loc[self.index[t], delivery_label]
                  if projected_label in self.values:
                    tot_projected += self.values.loc[self.index[t], projected_label]
                  if flood_label in self.values:
                    tot_flood += self.values.loc[self.index[t], flood_label]
                  if flood_irr_label in self.values:
                    tot_flood_irr += self.values.loc[self.index[t], flood_irr_label]
                  if recharge_label in self.values:
                    tot_recharge += self.values.loc[self.index[t], recharge_label]
              else:
                carryover_label = district_name + '_' + contract_name + '_carryover'
                delivery_label = district_name + '_' + contract_name + '_delivery'
                projected_label = district_name + '_' + contract_name + '_projected'
                flood_label = district_name + '_' + contract_name + '_flood'
                flood_irr_label = district_name + '_' + contract_name + '_flood_irrigation'
                recharge_label = district_name + '_' + contract_name + '_recharged'
                if carryover_label in self.values:
                  tot_carryover = self.values.loc[self.index[t], carryover_label]
                if delivery_label in self.values:
                  tot_delivered = self.values.loc[self.index[t], delivery_label]
                if projected_label in self.values:
                  tot_projected = self.values.loc[self.index[t], projected_label]
                if flood_label in self.values:
                  tot_flood = self.values.loc[self.index[t], flood_label]
                if flood_irr_label in self.values:
                  tot_flood_irr = self.values.loc[self.index[t], flood_irr_label]
                if recharge_label in self.values:
                  tot_recharge = self.values.loc[self.index[t], recharge_label]

              segment_dictionary_ii['carryover']['delivered'][contract_key][contract_name][t] += max(min(tot_carryover, tot_delivered), 0.0)
              segment_dictionary_ii['carryover']['projected'][contract_key][contract_name][t] += max(tot_carryover - tot_delivered, 0.0)

              segment_dictionary_iii[contract_key]['delivered'][district_group][contract_name][t] += max(tot_delivered, 0.0)
              segment_dictionary_iii[contract_key]['projected'][district_group][contract_name][t] += max(tot_projected, 0.0)
              segment_dictionary_iii['flood']['delivered'][district_group][contract_name][t] += tot_flood
              segment_dictionary_iii['flood']['delivered'][district_group][contract_name][t] += tot_flood_irr

              tot_delivered -= tot_recharge
              tot_recharge += tot_flood
              if district_name in urban_district_list:
                segment_dictionary_iv[district_group]['delivered']['urban'][contract_name][t] += tot_delivered
              else:
                segment_dictionary_iv[district_group]['delivered']['irrigation'][contract_name][t] += tot_delivered

              segment_dictionary_iv[district_group]['delivered']['direct recharge'][contract_name][t] += tot_recharge
              segment_dictionary_iv[district_group]['delivered']['in-lieu recharge'][contract_name][t] += tot_flood_irr

      for district_group in destination_groups_iii:
        for district_name in district_groups[district_group]:
          if district_name in private_district_list:
            pumping_labels = []
            location_labels = []
            host_district_labels = []
            for host_district_keys in private_district_keys[district_name]:
              pumping_labels.append(district_name + '_' + host_district_keys + '_pumping')
              pumping_labels.append(district_name + '_' + host_district_keys + '_recover_banked')
              pumping_labels.append(district_name + '_' + host_district_keys + '_exchanged_GW')
              host_district_labels.append(host_district_keys)
              location_labels.append('private pumping')
              location_labels.append('groundwater banks')
              location_labels.append('groundwater banks')
          else:
            pumping_labels = [district_name + '_pumping', district_name + '_recover_banked', district_name + '_exchanged_GW']
            location_labels = ['private pumping', 'groundwater banks', 'groundwater banks']
            host_district_labels = [district_name, district_name, district_name]


          
          for pumping_label, location_label, host_district in zip(pumping_labels, location_labels, host_district_labels):
            tot_pumping = 0.0
            if pumping_label in self.values:
              if location_label == 'private pumping':
                if self.month[t] > 9:
                  dowy = max(self.day_year[t] - 273, 0)
                else:
                  dowy = self.day_year[t] + 92
                tot_pumping = np.sum(self.values.loc[self.index[(t-dowy):t], pumping_label])
              else:
                tot_pumping = self.values.loc[self.index[t], pumping_label]
              if district_name in urban_district_list:
                segment_dictionary_iii[location_label]['delivered'][district_group]['ground'][t] += tot_pumping                 
                segment_dictionary_iv[district_group]['delivered']['urban']['ground'][t] += tot_pumping
              else:
                segment_dictionary_iii[location_label]['delivered'][district_group]['ground'][t] += tot_pumping                 
                segment_dictionary_iv[district_group]['delivered']['irrigation']['ground'][t] += tot_pumping


              if pumping_label == district_name + '_exchanged_GW':
                max_contract = 0.0
                final_contract_name = []
                for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
                  for contract_name in contract_names[res_name]:
                    if district_name in private_district_list:
                      contract_delivery_label = district_name + '_' + host_district + '_' + contract_name + '_delivery'
                    else:
                      contract_delivery_label = district_name + '_' + contract_name + '_delivery'
                    if contract_delivery_label in self.values:
                      if self.values.loc[self.index[t], contract_delivery_label] >= max_contract:
                        final_contract_name = []
                        final_contract_name.append(contract_name)
                        max_contract = self.values.loc[self.index[t], contract_delivery_label]

                if len(final_contract_name) == 1:
                  if district_name in urban_district_list:
                    segment_dictionary_iv[district_group]['delivered']['urban'][final_contract_name[0]][t] -= tot_pumping
                  else:
                    segment_dictionary_iv[district_group]['delivered']['irrigation'][final_contract_name[-1]][t] -= tot_pumping

          tot_exchange = 0.0
          if district_name in private_district_list:
            for host_district in private_district_keys[district_name]:
              exchanged_label = district_name + '_' + host_district + '_exchanged_GW'
              if exchanged_label in self.values:
                tot_exchange = self.values.loc[self.index[t], exchanged_label] 

                max_contract = 0.0
                final_contract_name = []
                for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
                  for contract_name in contract_names[res_name]:
                    contract_delivery_label = district_name + '_' + host_district + '_' + contract_name + '_delivery'
                    if contract_delivery_label in self.values:
                      if self.values.loc[self.index[t], contract_delivery_label] >= max_contract:
                        final_contract_name = []
                        final_contract_name.append(contract_name)
                        max_contract = self.values.loc[self.index[t], contract_delivery_label]
                if len(final_contract_name) == 1:
                  if district_name in urban_district_list:
                    segment_dictionary_iv[district_group]['delivered']['urban'][final_contract_name[0]][t] += tot_exchange
                  else:
                    segment_dictionary_iv[district_group]['delivered']['irrigation'][final_contract_name[-1]][t] += tot_exchange
              
              inlieu_label = district_name + '_' +  host_district + '_inleiu_irrigation'
              if inlieu_label in self.values:
                tot_inlieu = self.values.loc[self.index[t], inlieu_label]
                max_contract = 0.0
                final_contract_name = []
                for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
                  for contract_name in contract_names[res_name]:
                    contract_delivery_label = district_name + '_' + host_district + '_' + contract_name + '_delivery'
                    if contract_delivery_label in self.values:
                      if self.values.loc[self.index[t], contract_delivery_label] >= max_contract:
                        final_contract_name = []
                        final_contract_name.append(contract_name)
                        max_contract = self.values.loc[self.index[t], contract_delivery_label]
                if len(final_contract_name) == 1:
                  segment_dictionary_iv['urban']['delivered']['in-lieu recharge'][final_contract_name[0]][t] += tot_inlieu
                  segment_dictionary_iv['urban']['delivered']['direct recharge'][final_contract_name[0]][t] -= tot_inlieu
                else:
                  segment_dictionary_iv['urban']['delivered']['in-lieu recharge'][final_contract_name[-1]][t] += tot_inlieu
                  segment_dictionary_iv['urban']['delivered']['direct recharge'][final_contract_name[-1]][t] -= tot_inlieu

          else:
            exchanged_label = district_name + '_exchanged_GW'
            if exchanged_label in self.values:
              tot_exchange = self.values.loc[self.index[t], exchanged_label]

              max_contract = 0.0
              final_contract_name = []
              for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
                for contract_name in contract_names[res_name]:
                  contract_delivery_label = district_name + '_' + contract_name + '_delivery'
                  if contract_delivery_label in self.values:
                    if self.values.loc[self.index[t], contract_delivery_label] >= max_contract:
                      final_contract_name = []
                      final_contract_name.append(contract_name)
                      max_contract = self.values.loc[self.index[t], contract_delivery_label]
              if len(final_contract_name) == 1:
                if district_name in urban_district_list:
                  segment_dictionary_iv[district_group]['delivered']['urban'][final_contract_name[0]][t] += tot_exchange
                else:
                  segment_dictionary_iv[district_group]['delivered']['irrigation'][final_contract_name[-1]][t] += tot_exchange
              
            inlieu_label = district_name + '_inleiu_irrigation'
            if inlieu_label in self.values:
              tot_inlieu = self.values.loc[self.index[t], inlieu_label]
              max_contract = 0.0
              final_contract_name = []
              for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
                for contract_name in contract_names[res_name]:
                  contract_delivery_label = district_name + '_' + contract_name + '_delivery'
                  if contract_delivery_label in self.values:
                    if self.values.loc[self.index[t], contract_delivery_label] >= max_contract:
                      final_contract_name = []
                      final_contract_name.append(contract_name)
                      max_contract = self.values.loc[self.index[t], contract_delivery_label]
              if len(final_contract_name) == 1:
                segment_dictionary_iv['urban']['delivered']['in-lieu recharge'][final_contract_name[0]][t] += tot_inlieu
                segment_dictionary_iv['urban']['delivered']['direct recharge'][final_contract_name[0]][t] -= tot_inlieu
              else:
                segment_dictionary_iv['urban']['delivered']['in-lieu recharge'][final_contract_name[-1]][t] += tot_inlieu
                segment_dictionary_iv['urban']['delivered']['direct recharge'][final_contract_name[-1]][t] -= tot_inlieu


          tot_projected = 0.0
          for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
            for contract_name in contract_names[res_name]:
              if district_name in private_district_list:
                for host_district in private_district_keys[district_name]:
                  contract_projected_label = district_name + '_' +  host_district + '_' + contract_name + '_projected'
                  if contract_projected_label in self.values:
                    tot_projected += self.values.loc[self.index[t], contract_projected_label]
              else:
                contract_projected_label = district_name + '_' + contract_name + '_projected'
                if contract_projected_label in self.values:
                  tot_projected += self.values.loc[self.index[t], contract_projected_label]

          tot_demand = 0.0
          if district_name in private_district_list:
            for host_district in private_district_keys[district_name]:
              demand_name = district_name + '_' + host_district + '_tot_demand'
              if demand_name in self.values:
                tot_demand += self.values.loc[self.index[t], demand_name]
          else:
            demand_name = district_name + '_tot_demand'
            if demand_name in self.values:
              tot_demand = self.values.loc[self.index[t], demand_name]

          projected_pumping = max(tot_demand - tot_projected, 0.0)
          segment_dictionary_iii['private pumping']['projected'][district_group]['ground'][t] += projected_pumping
          if district_name in urban_district_list:
            segment_dictionary_iv[district_group]['projected']['urban']['ground'][t] += projected_pumping
          else:
            segment_dictionary_iv[district_group]['projected']['irrigation']['ground'][t] += projected_pumping

          if tot_projected > 0.0:
            projected_fraction = min(max(tot_demand/tot_projected, 0.0), 1.0)
          else:
            projected_fraction = 0.0
    
          for res_name in ['sanluisfederal', 'sanluisstate', 'millerton', 'isabella', 'pine flat', 'kaweah', 'success']:
            for contract_name in contract_names[res_name]:
              if district_name in private_district_list:
                for host_district in private_district_keys[district_name]:
                  contract_projected_label = district_name + '_' +  host_district + '_' + contract_name + '_projected'
                  if contract_projected_label in self.values:
                    if district_name in urban_district_list:
                      segment_dictionary_iv[district_group]['projected']['urban'][contract_name][t] += projected_fraction * self.values.loc[self.index[t], contract_projected_label]
                    else:
                      segment_dictionary_iv[district_group]['projected']['irrigation'][contract_name][t] += projected_fraction * self.values.loc[self.index[t], contract_projected_label]
                    segment_dictionary_iv[district_group]['projected']['carryover'][contract_name][t] += ( 1.0 - projected_fraction )* self.values.loc[self.index[t], contract_projected_label]
              else:
                contract_projected_label = district_name + '_' + contract_name + '_projected'
                if contract_projected_label in self.values:
                  if district_name in urban_district_list:
                    segment_dictionary_iv[district_group]['projected']['urban'][contract_name][t] += projected_fraction * self.values.loc[self.index[t], contract_projected_label]
                  else:
                    segment_dictionary_iv[district_group]['projected']['irrigation'][contract_name][t] += projected_fraction * self.values.loc[self.index[t], contract_projected_label]
                  segment_dictionary_iv[district_group]['projected']['carryover'][contract_name][t] += ( 1.0 - projected_fraction )* self.values.loc[self.index[t], contract_projected_label]


    source_sizes, destination_sizes = make_group_sums(source_groups, destination_groups, source_types, color_groups, timesteps, segment_dictionary)
    source_sizes_ii, destination_sizes_ii = make_group_sums(source_groups_ii, destination_groups_ii, source_types, color_groups, timesteps, segment_dictionary_ii)
    source_sizes_iii, destination_sizes_iii = make_group_sums(source_groups_iii, destination_groups_iii, source_types, color_groups, timesteps, segment_dictionary_iii)
    source_sizes_iv, destination_sizes_iv = make_group_sums(source_groups_iv, destination_groups_iv, source_types, color_groups, timesteps, segment_dictionary_iv)

    scale_i =  find_axis_scale(timesteps, source_groups, source_sizes, source_groups, source_sizes, open_area, min_label_height)
    scale_ii =  find_axis_scale(timesteps, destination_groups_b, destination_sizes, source_groups_ii_b, source_sizes_ii, open_area, min_label_height)
    scale_iii =  find_axis_scale(timesteps, destination_groups_ii, destination_sizes_ii, source_groups_iii_b, source_sizes_iii, open_area, min_label_height)
    scale_iv =  find_axis_scale(timesteps, destination_groups_iii, destination_sizes_iii, source_groups_iv, source_sizes_iv, open_area, min_label_height)
    scale_v =  find_axis_scale(timesteps, destination_groups_iv_b, destination_sizes_iv, destination_groups_iv_b, destination_sizes_iv, open_area, min_label_height)

    scale_away_i =  find_away_scale(timesteps, away_groups, destination_sizes, open_area, min_label_height)
    scale_away_ii =  find_away_scale(timesteps, away_groups_ii, source_sizes_ii, open_area, min_label_height)
    scale_away_iii =  find_away_scale(timesteps, away_groups_iii, source_sizes_iii, open_area, min_label_height)
    scale_away_iv =  find_away_scale(timesteps, away_groups_iv, destination_sizes_iv, open_area, min_label_height)

    for snapshot_t in range(snapshot_range[0], snapshot_range[1]):
      data_figure = Sanker()

      running_start = 0.0
      source_starting_point = find_starting_point(running_start, source_groups, source_sizes, snapshot_t, open_area, scale_i, min_label_height)  
      destination_starting_point = find_starting_point(running_start, source_groups_ii_b, source_sizes_ii, snapshot_t, open_area, scale_ii, min_label_height)  

      running_start = scale_away_i*0.2
      away_group_starting_point = find_starting_point(running_start, away_groups, destination_sizes, snapshot_t, open_area, scale_away_i * 1.2, min_label_height)  

      plot_position = 0
      for type, alpha_type in zip(source_types, source_alphas):
        for cl_count, cl in enumerate(color_groups):  
          for src_count, src in enumerate(source_groups):
            running_dest = 0.0
            for dest_count, dest in enumerate(destination_groups_b):

              source_low = source_starting_point[src] * 1.0
              source_high = source_starting_point[src] + segment_dictionary[src][type][dest][cl][snapshot_t]

              dest_low = destination_starting_point[dest] * 1.0
              dest_high = destination_starting_point[dest] + segment_dictionary[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey([source_low, source_high], [dest_low, dest_high], scale_i, scale_ii, plot_position, color_list[cl_count], alpha_type)

              source_starting_point[src] += segment_dictionary[src][type][dest][cl][snapshot_t]
              destination_starting_point[dest] += segment_dictionary[src][type][dest][cl][snapshot_t]

            for dest_count, dest in enumerate(away_groups):

              source_low = source_starting_point[src] * 1.0
              source_high = source_starting_point[src] + segment_dictionary[src][type][dest][cl][snapshot_t]

              dest_low = away_group_starting_point[dest] * 1.0
              dest_high = away_group_starting_point[dest] + segment_dictionary[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey2([source_low, source_high], [dest_low, dest_high], scale_i, scale_away_i*1.4, plot_position, color_list[cl_count], alpha_type)


              source_starting_point[src] += segment_dictionary[src][type][dest][cl][snapshot_t]
              away_group_starting_point[dest] += segment_dictionary[src][type][dest][cl][snapshot_t]

      
      plot_position = 1
      running_start = 0.0
      source_starting_point_ii = find_starting_point(running_start, source_groups_ii_b, source_sizes_ii, snapshot_t, open_area, scale_ii, min_label_height)  
      destination_starting_point_ii = find_starting_point(running_start, destination_groups_ii, destination_sizes_ii, snapshot_t, open_area, scale_iii, min_label_height)  

      running_start = scale_away_ii*0.2
      away_starting_point_ii = find_starting_point(running_start, away_groups_ii, source_sizes_ii, snapshot_t, open_area, scale_away_ii * 1.2, min_label_height)  

      for type, alpha_type in zip(source_types, source_alphas):
        for cl_count, cl in enumerate(color_groups):  
          for src_count, src in enumerate(source_groups_ii_b):
            running_dest = 0.0
            for dest_count, dest in enumerate(destination_groups_ii):
 
              source_low = source_starting_point_ii[src] * 1.0
              source_high = source_starting_point_ii[src] + segment_dictionary_ii[src][type][dest][cl][snapshot_t]

              dest_low = destination_starting_point_ii[dest] * 1.0
              dest_high = destination_starting_point_ii[dest] + segment_dictionary_ii[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey([source_low, source_high], [dest_low, dest_high], scale_ii, scale_iii, plot_position, color_list[cl_count], alpha_type)

              source_starting_point_ii[src] += segment_dictionary_ii[src][type][dest][cl][snapshot_t]
              destination_starting_point_ii[dest] += segment_dictionary_ii[src][type][dest][cl][snapshot_t]

          for src_count, src in enumerate(away_groups_ii):
            for dest_count, dest in enumerate(destination_groups_ii):

              source_low = away_starting_point_ii[src] * 1.0
              source_high = away_starting_point_ii[src] + segment_dictionary_ii[src][type][dest][cl][snapshot_t]

              dest_low = destination_starting_point_ii[dest] * 1.0
              dest_high = destination_starting_point_ii[dest] + segment_dictionary_ii[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey3([source_low, source_high], [dest_low, dest_high], scale_away_ii*1.4, scale_iii, plot_position, color_list[cl_count], alpha_type)

              away_starting_point_ii[src] += segment_dictionary_ii[src][type][dest][cl][snapshot_t]
              destination_starting_point_ii[dest] += segment_dictionary_ii[src][type][dest][cl][snapshot_t]

      plot_position = 2
      running_start = 0.0
      source_starting_point_iii = find_starting_point(running_start, source_groups_iii_b, source_sizes_iii, snapshot_t, open_area, scale_iii, min_label_height)  
      destination_starting_point_iii = find_starting_point(running_start, destination_groups_iii, destination_sizes_iii, snapshot_t, open_area, scale_iv, min_label_height)  

      running_start = scale_away_iii*0.2
      away_starting_point_iii = find_starting_point(running_start, away_groups_iii, source_sizes_iii, snapshot_t, open_area, scale_away_iii * 1.2, min_label_height)  

      for type, alpha_type in zip(source_types, source_alphas):
        for cl_count, cl in enumerate(color_groups):  
          for src_count, src in enumerate(source_groups_iii_b):
            running_dest = 0.0
            for dest_count, dest in enumerate(destination_groups_iii):
 
              source_low = source_starting_point_iii[src] * 1.0
              source_high = source_starting_point_iii[src] + segment_dictionary_iii[src][type][dest][cl][snapshot_t]

              dest_low = destination_starting_point_iii[dest] * 1.0
              dest_high = destination_starting_point_iii[dest] + segment_dictionary_iii[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey([source_low, source_high], [dest_low, dest_high], scale_iii, scale_iv, plot_position, color_list[cl_count], alpha_type)

              source_starting_point_iii[src] += segment_dictionary_iii[src][type][dest][cl][snapshot_t]
              destination_starting_point_iii[dest] += segment_dictionary_iii[src][type][dest][cl][snapshot_t]

          for src_count, src in enumerate(away_groups_iii):
            for dest_count, dest in enumerate(destination_groups_iii):

              source_low = away_starting_point_iii[src] * 1.0
              source_high = away_starting_point_iii[src] + segment_dictionary_iii[src][type][dest][cl][snapshot_t]

              dest_low = destination_starting_point_iii[dest] * 1.0
              dest_high = destination_starting_point_iii[dest] + segment_dictionary_iii[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey3([source_low, source_high], [dest_low, dest_high], scale_away_iii*1.4, scale_iv, plot_position, color_list[cl_count], alpha_type)

              away_starting_point_iii[src] += segment_dictionary_iii[src][type][dest][cl][snapshot_t]
              destination_starting_point_iii[dest] += segment_dictionary_iii[src][type][dest][cl][snapshot_t]
      running_start = 0.0
      source_starting_point_iv = find_starting_point(running_start, source_groups_iv, source_sizes_iv, snapshot_t, open_area, scale_iv, min_label_height)  
      destination_starting_point_iv = find_starting_point(running_start, destination_groups_iv_b, destination_sizes_iv, snapshot_t, open_area, scale_v, min_label_height)  

      running_start = scale_away_iv*0.2
      away_group_starting_point_iv = find_starting_point(running_start, away_groups_iv, destination_sizes_iv, snapshot_t, open_area, scale_away_iv * 1.2, min_label_height)  

      plot_position = 3
      for type, alpha_type in zip(source_types, source_alphas):
        for cl_count, cl in enumerate(color_groups):  
          for src_count, src in enumerate(source_groups_iv):
            running_dest = 0.0
            for dest_count, dest in enumerate(destination_groups_iv_b):

              source_low = source_starting_point_iv[src] * 1.0
              source_high = source_starting_point_iv[src] + segment_dictionary_iv[src][type][dest][cl][snapshot_t]

              dest_low = destination_starting_point_iv[dest] * 1.0
              dest_high = destination_starting_point_iv[dest] + segment_dictionary_iv[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey([source_low, source_high], [dest_low, dest_high], scale_iv, scale_v, plot_position, color_list[cl_count], alpha_type)

              source_starting_point_iv[src] += segment_dictionary_iv[src][type][dest][cl][snapshot_t]
              destination_starting_point_iv[dest] += segment_dictionary_iv[src][type][dest][cl][snapshot_t]

            for dest_count, dest in enumerate(away_groups_iv):

              source_low = source_starting_point_iv[src] * 1.0
              source_high = source_starting_point_iv[src] + segment_dictionary_iv[src][type][dest][cl][snapshot_t]

              dest_low = away_group_starting_point_iv[dest] * 1.0
              dest_high = away_group_starting_point_iv[dest] + segment_dictionary_iv[src][type][dest][cl][snapshot_t]
              data_figure.add_sankey2([source_low, source_high], [dest_low, dest_high], scale_iv, scale_away_iv*1.4, plot_position, color_list[cl_count], alpha_type)


              source_starting_point_iv[src] += segment_dictionary_iv[src][type][dest][cl][snapshot_t]
              away_group_starting_point_iv[dest] += segment_dictionary_iv[src][type][dest][cl][snapshot_t]

      column_1_names = self.figure_params[fig_name][plot_name]['column1']
      column_2_names = self.figure_params[fig_name][plot_name]['column2']
      column_3_names = self.figure_params[fig_name][plot_name]['column3']
      column_4_names = self.figure_params[fig_name][plot_name]['column4']
      column_5_names = self.figure_params[fig_name][plot_name]['column5']
      row_1_names = self.figure_params[fig_name][plot_name]['row1']
      row_2_names = self.figure_params[fig_name][plot_name]['row2']
      row_3_names = self.figure_params[fig_name][plot_name]['row3']
      row_4_names = self.figure_params[fig_name][plot_name]['row4']
      fig_titles  = self.figure_params[fig_name][plot_name]['titles']

      prev_values = 0.0
      src_count = 0

      for src, label_name in zip(source_groups, column_1_names):
        data_figure.add_sankey_label(source_sizes[src][snapshot_t], scale_i, 0.02, [src_count, 0], open_area, source_groups, min_label_height, prev_values, label_name, unit_label = 'mAF')
        prev_values += source_sizes[src][snapshot_t]
        src_count += 1
      prev_values = 0.0
      dst_count = 0
      for dst, label_name in zip(source_groups_ii_b, column_2_names):
        data_figure.add_sankey_label(source_sizes_ii[dst][snapshot_t], scale_ii, 0.02, [dst_count, 1], open_area, source_groups_ii_b, min_label_height, prev_values, label_name, unit_label = 'mAF')
        prev_values += source_sizes_ii[dst][snapshot_t]
        dst_count += 1 
      prev_values = scale_away_i * 0.2
      dst_count = 0
      for dst, label_name in zip(away_groups, row_1_names):
        data_figure.add_sankey_label_horizontal(destination_sizes[dst][snapshot_t], scale_away_i*1.4, 0.03, [dst_count, 1.1], open_area * scale_away_i  * 1.2 / (len(away_groups) - 1), prev_values, label_name, unit_label = 'mAF')
        prev_values += destination_sizes[dst][snapshot_t]
        dst_count += 1
      prev_values = 0.0
      dst_count = 0
      for dst, label_name in zip(destination_groups_ii, column_3_names):
        data_figure.add_sankey_label(destination_sizes_ii[dst][snapshot_t], scale_iii, 0.02, [dst_count, 2], open_area, destination_groups_ii, min_label_height, prev_values, label_name, unit_label = 'mAF')
        prev_values += destination_sizes_ii[dst][snapshot_t]
        dst_count += 1
      prev_values = scale_away_ii * 1.6
      if scale_away_ii > 0.0:
        dst_count = 0
        for dst, label_name in zip(away_groups_ii, row_2_names):
          data_figure.add_sankey_label_horizontal(source_sizes_ii[dst][snapshot_t], scale_away_ii*1.4, 0.03, [dst_count, 1.1], open_area * scale_away_ii  * 1.2 / (len(away_groups_ii)), prev_values, label_name, unit_label = 'mAF')
          prev_values += source_sizes_ii[dst][snapshot_t]
          dst_count += 1

      prev_values = 0.0
      dst_count = 0
      for dst, label_name in zip(destination_groups_iii, column_4_names):
        data_figure.add_sankey_label(destination_sizes_iii[dst][snapshot_t], scale_iv, 0.02, [dst_count, 3], open_area, destination_groups_iii, min_label_height, prev_values, label_name, unit_label = 'mAF')
        prev_values += destination_sizes_iii[dst][snapshot_t]
        dst_count += 1
      prev_values = scale_away_iii * 3.0
      dst_count = 0
      for dst, label_name in zip(away_groups_iii, row_3_names):
#        if dst == 'groundwater banks':
#          data_figure.add_sankey_label_horizontal(total_bank_storage[snapshot_t], scale_away_iii*1.4, 0.03, [dst_count, 1.1], open_area * scale_away_iii * 1.2  / (len(away_groups_iii) - 1), prev_values, 'gw bank', unit_label = 'mAF')
#        else:
        data_figure.add_sankey_label_horizontal(source_sizes_iii[dst][snapshot_t], scale_away_iii*1.4, 0.03, [dst_count, 1.1], open_area * scale_away_iii * 1.2  / (len(away_groups_iii) - 1), prev_values, label_name, unit_label = 'mAF')
        prev_values += source_sizes_iii[dst][snapshot_t]
        dst_count += 1 
      prev_values = 0.0
      dst_count = 0
      for dst, label_name in zip(destination_groups_iv_b, column_5_names):
        data_figure.add_sankey_label(destination_sizes_iv[dst][snapshot_t], scale_v, 0.02, [dst_count, 4], open_area, destination_groups_iv_b, min_label_height, prev_values, label_name, unit_label = 'mAF')
        prev_values += destination_sizes_iv[dst][snapshot_t]
        dst_count += 1
      prev_values = scale_away_iv * 4.4
      dst_count = 0
      for dst, label_name in zip(away_groups_iv, row_4_names):
        data_figure.add_sankey_label_horizontal(destination_sizes_iv[dst][snapshot_t], scale_away_iv*1.4, 0.03, [dst_count, 1.1], open_area  * scale_away_iv * 1.2 / len(away_groups_iv), prev_values, label_name, unit_label = 'mAF')
        prev_values += destination_sizes_iv[dst][snapshot_t]
        dst_count += 1
      xlim = [0 - 0.25, 4 + 0.25]
      ylim = [-0.15, 1.2]
      label_names = ['N. Delta Supplies', 'Tulare Basin Supplies', 'Contract Allocations', 'Contractors', 'Water Use']
      for pos, x in enumerate(fig_titles):
        data_figure.add_sankey_title(pos, x, -.075)
      month_name = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
      print(snapshot_t, end = " ")
      print(month_name[self.month[snapshot_t] - 1])
      data_figure.add_sankey_title(2, month_name[self.month[snapshot_t] - 1] + ' ' + str(self.day_month[snapshot_t]) + ', '+ str(self.year[snapshot_t]), 1.18)
      data_figure.format_sankey(xlim, ylim, folder_name + 'cali_sankey_' + str(snapshot_t))
      del data_figure
#      plt.show()
      plt.close()

  def add_sankey2(self, loc1, loc2, scale_src, scale_away, plot_position, color, alpha, zorder_num = 2):
    x = np.linspace(0, scale_away, 100)
    bottom_multiplier = (1.1 - loc1[0]/scale_src)/pow(loc2[1], 2.0)
    top_multiplier = (1.1 - loc1[1]/scale_src)/pow(loc2[0], 2.0)

    x_plot = np.linspace(plot_position, plot_position + 1.0, 100)
    z_bottom = bottom_multiplier * pow(x, 2.0) + loc1[0]/scale_src
    z_top = top_multiplier * pow(x, 2.0) + loc1[1]/scale_src
    z_top[z_top > 1.1] = 1.1
    z_bottom[z_bottom > 1.1] = 1.1
    self.ax.fill_between(x_plot, z_bottom, z_top, color= color, alpha = alpha, edgecolor = 'b', linewidth = 0.0, zorder = zorder_num) 

  def add_sankey3(self, loc1, loc2, scale_away, scale_dest, plot_position, color, alpha, zorder_num = 2):
    x = np.linspace(0, 1, 100)
    bottom_multiplier = (1.1 - loc2[0]/scale_dest)/pow((loc1[0]/scale_away)-1.0, 2.0)
    top_multiplier = (1.1 - loc2[1]/scale_dest)/pow((loc1[1]/scale_away)-1.0, 2.0)

    x_plot = np.linspace(plot_position, plot_position + 1.0, 100)
    z_bottom = bottom_multiplier * pow(x - 1, 2.0) + loc2[0]/scale_dest
    z_top = top_multiplier * pow(x - 1, 2.0) + loc2[1]/scale_dest
    z_top[z_top > 1.1] = 1.1
    z_bottom[z_bottom > 1.1] = 1.1
    self.ax.fill_between(x_plot, z_bottom, z_top, color= color, alpha = alpha, edgecolor = 'b', linewidth = 0.0, zorder = zorder_num) 


  def make_gif(self, figure_base, figure_year, figure_range_start, figure_range_end):
    image_list = []
    for fig_num in range(figure_range_start, figure_range_end):
      file_name = figure_base + '_' + str(fig_num) + '.png'
      image_list.append(imageio.imread(file_name))
    imageio.mimwrite(figure_base + figure_year + '.gif', image_list)



def make_source_dictionaries(source_groups, destination_groups, source_types, color_groups, timesteps):
  
  segment_dictionary = {}
  for sg in source_groups:
    segment_dictionary[sg] = {}
    for st in source_types:
      segment_dictionary[sg][st] = {}
      for dg in destination_groups:
        segment_dictionary[sg][st][dg] = {}
        for cl in color_groups:
          segment_dictionary[sg][st][dg][cl] = np.zeros(timesteps)

  return segment_dictionary

def make_group_sums(source_groups, destination_groups, source_types, color_groups, timesteps, segment_dictionary):
  source_sizes = {}
  destination_sizes = {}
  for sg in source_groups:
    source_sizes[sg] = np.zeros(timesteps)
  source_sizes['total'] = np.zeros(timesteps)
  for dg in destination_groups:       
    destination_sizes[dg] = np.zeros(timesteps)
  destination_sizes['total'] = np.zeros(timesteps)

  for t in range(0, timesteps):
    for sg in source_groups:
      for st in source_types:
        for dg in destination_groups:
          for cl in color_groups:
            source_sizes[sg][t] += segment_dictionary[sg][st][dg][cl][t]
            source_sizes['total'][t] += segment_dictionary[sg][st][dg][cl][t]
            destination_sizes[dg][t] += segment_dictionary[sg][st][dg][cl][t]
            destination_sizes['total'][t] += segment_dictionary[sg][st][dg][cl][t]

  return source_sizes, destination_sizes

def find_axis_scale(timesteps, destination_groups, destination_sizes, source_groups, source_sizes, open_area, min_height):

  scale = 0.00001
  open_area = max( max(len(source_groups), len(destination_groups)) * min_height, open_area)
  for t in range(0, timesteps):
    scale_int = 0.0
    scale_int_2 = 0.0
    for src in source_groups:
      scale_int += source_sizes[src][t] / ( 1 - open_area )
    for dst in destination_groups:
      scale_int_2 += destination_sizes[dst][t] / ( 1 - open_area )

    scale = max(scale, scale_int, scale_int_2)

  return scale

   
def find_away_scale(timesteps, away_groups, away_sizes, open_area, min_height):

  scale_away = 0.000001
  open_area = max ( len(away_groups) * min_height, open_area)
  for t in range(0, timesteps):
    scale_away_int = 0.0
    for awy in away_groups:
      scale_away_int += away_sizes[awy][t] / ( 1 - open_area )

    scale_away = max(scale_away, scale_away_int)

  return scale_away

def find_starting_point(running_start, source_groups, source_sizes, timestep, open_area, scale, min_height):

  source_starting_point = {}
  open_area = max( len(source_groups) * min_height, open_area)
  for src in source_groups:
    source_starting_point[src] = running_start
    if len(source_groups) > 1:
      running_start += source_sizes[src][timestep] + open_area * scale/(len(source_groups) - 1)
    else:
      running_start += source_sizes[src][timestep] + open_area * scale/len(source_groups)

  return source_starting_point


  def add_sankey_label(self, block_height, loc_scale, block_width, block_position, open_space, prev_values, block_label, unit_label = 'tAF'):
    min_height = 0.05
    top = (prev_values + block_height)/loc_scale + block_position[0] * open_space/loc_scale
    bottom = prev_values/loc_scale + block_position[0] * open_space/loc_scale
    total_height = top - bottom
    if total_height < min_height:
      top += (min_height - total_height)*0.5
      bottom -= (min_height - total_height)*0.5

    left = block_position[1] - block_width
    right = block_position[1] + block_width
    self.ax.fill_between([left, right], [bottom, bottom], [top, top], facecolor= 'lightgray', alpha = 1.0, edgecolor = 'black', linewidth = 2.0, zorder = 20)
    if unit_label == 'tAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height)) + ' tAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == 'mAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height/100)/10) + ' mAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == '%':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height*100)/100) + ' %', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)

  def add_sankey_label_horizontal(self, block_height, loc_scale, block_width, block_position, open_space, prev_values, block_label, unit_label = 'tAF'):
    min_height = 0.05
    right = (prev_values + block_height)/loc_scale + block_position[0] * open_space/loc_scale
    left = prev_values/loc_scale + block_position[0] * open_space/loc_scale

    bottom = block_position[1] - block_width
    top = block_position[1] + block_width

    self.ax.fill_between([left, right], [bottom, bottom], [top, top], facecolor= 'lightgray', alpha = 1.0, edgecolor = 'black', linewidth = 2.0, zorder = 20)
    if unit_label == 'tAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height)) + ' tAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == 'mAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height/100)/10) + ' mAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == '%':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height*100)/100) + ' %', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)


  def add_sankey_title(self, column, title, height):
    self.ax.text(column, height, title, fontsize = 20, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center', horizontalalignment='center') 

  def format_sankey(self, xlim, ylim, fig_name):
    self.ax.set_xlim(xlim)
    self.ax.set_ylim(ylim)
    self.ax.axis('off')
    plt.savefig(fig_name + '.png', dpi = 150, bbox_inches = 'tight', pad_inches = 0.0)



