import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cord import *

#plotter.plot_almond_costs()
######################################################################################
###Plot Model Validation Results
######################################################################################
northern_results = pd.read_csv('cord/data/results/reservoir_results_no_validation.csv', index_col=0, parse_dates=True)
southern_results = pd.read_csv('cord/data/results/reservoir_results_so_validation.csv', index_col=0, parse_dates=True)
observations = pd.read_csv('cord/data/input/cord-data.csv', index_col=0, parse_dates=True)

##############################
###PUMPING VALIDATION FIGURES
##############################
pump_list = ['HRO_pump', 'TRP_pump']
title_list = ['State Water Project', 'Central Valley Project']
simulated_unit = 1.0
observed_unit = cfs_tafd
label_loc = [115, 76]
#plotter.make_pumping_plots(northern_results, observations, simulated_unit, observed_unit, pump_list, title_list, label_loc, 'W', 'AS-OCT')

###############################
###RESERVOIR VALIDATION FIGURES
###############################
data_type = '_storage'
simulated_unit = 1.0/1000.0
observed_unit = 1.0/1000000.0
plot_dim_1 = 4
plot_dim_2 = 2
reservoir_list = ['SHA', 'ORO', 'FOL', 'YRS', 'NML', 'DNP', 'EXC']
title_list = ['SHASTA', 'OROVILLE', 'FOLSOM', 'NEW BULLARDS BAR', 'NEW MELONES', 'DON PEDRO', 'EXCHEQUER']
#plotter.make_reservoir_plots(northern_results, observations, simulated_unit, observed_unit, reservoir_list, title_list, data_type, plot_dim_1, plot_dim_2, 'W')

##############################
###SAN LUIS VALIDATION FIGURES
##############################
san_luis_list = ['SLS', 'SLF']
title_list = ['State (SWP) Portion', 'Federal (CVP) Portion']
data_type = '_storage'
simulated_unit = 1.0/1000.0
observed_unit = 1.0/1000000.0
#plotter.make_san_luis_plots(southern_results, observations, simulated_unit, observed_unit, san_luis_list, title_list, data_type, 'W')

######################################################################################
###Plot Simulation Results
######################################################################################
district_results = pd.read_csv('cord/data/results/annual_district_results_simulation.csv')
contract_results = pd.read_csv('cord/data/results/contract_results_annual_simulation.csv')

######################
###PUMPING PDF FIGURES
######################
annual_pumping = district_results['0']
title = 'SWP Pumping'
thresholds = [0.01, 0.05, 0.2, 1.0]
threshold_list = ['1% Risk', '5% Risk', '20% Risk', 'Wettest 80%']
#plotter.show_pumping_pdf(annual_pumping, 'SWP Pumping', max(annual_pumping), thresholds, threshold_list)


##############################
###REVENUE SCATTERPLOT FIGURES
##############################
modelplot = Model('cord/data/input/cord-data.csv', 'cord/data/input/cord-data.csv', '10-01-1996', 'simulation')
modelplot.initialize_water_districts()
modelplot.losthills.price = 129.74
modelplot.semitropic.price = 103.0
modelplot.losthills.assessment = 0.0
modelplot.semitropic.assessment = 40.0
modelplot.losthills.bank_get = 0.0
modelplot.semitropic.bank_get = 112.33
modelplot.losthills.bank_give = 0.0
modelplot.semitropic.bank_give = 86.33

timeseries_revenues = {}
average_revenue = {}
for x in [modelplot.semitropic, modelplot.losthills]:
  timeseries_revenues[x.key] = {}
  average_revenue[x.key] = {}
  for type in ['delivery', 'recovery', 'banking']:
    timeseries_revenues[x.key][type], average_revenue[x.key][type] = plotter.find_district_revenues(district_results, x.key, x.acreage['W'], x.price, x.assessment, x.bank_get, x.bank_give, type)

for x in [modelplot.semitropic, modelplot.losthills]:
  if x.in_leiu_banking:
    plotter.show_district_revenues(timeseries_revenues[x.key],0,40.0, 'banking')
  else:
    plotter.show_district_revenues(timeseries_revenues[x.key],0,14.0, 'recovery')
	
	
legend_names = ['Table A Deliveries', 'All Deliveries (inc. GW Recovery)']
stored_names = ['delivery', 'recovery']
color_names = ['black', 'black']
alpha_values = [0.2, 0.7]
revenue_series = {}
color_series = {}
alpha_dict = {}
for x,y,z,aa in zip(legend_names, stored_names, color_names, alpha_values):
  revenue_series[x] = timeseries_revenues['LHL'][y]
  color_series[x] = z  
  alpha_dict[x] = aa

plotter.show_insurance_payouts(annual_pumping, revenue_series, color_series, alpha_dict, 1700.0, 'SWP Pumping', 'Lost Hills', 14.0, True)

legend_names = ['Table A Deliveries', 'All Revenue (inc. Bank Operations)']
stored_names = ['delivery', 'banking']
color_names = ['black', 'black']
alpha_values = [0.2, 0.7]

revenue_series = {}
color_series = {}
alpha_dict = {}

for x,y,z,aa in zip(legend_names, stored_names, color_names, alpha_values):
  revenue_series[x] = timeseries_revenues['SMI'][y]
  color_series[x] = z
  alpha_dict[x] = aa
  
plotter.show_insurance_payouts(annual_pumping, revenue_series, color_series, alpha_dict, 1400.0, 'SWP Pumping', 'Semitropic', 45.0, True)

###############################
###MITIGATION BAR GRAPH FIGURES
###############################
premium_rate = 0.4
control_level = ['10', '5']
insurance_strike = 1700.0
insurance_payment = [0.5, 0.75]
plotter.compare_mitigation_performance(timeseries_revenues['LHL']['recovery'], annual_pumping, premium_rate, control_level, insurance_strike, insurance_payment, 'Lost Hills')
#control_level = '5'
#insurance_payment = 0.75
#plotter.compare_mitigation_performance(timeseries_revenues['LHL']['recovery'], annual_pumping, premium_rate, control_level, insurance_strike, insurance_payment, 'Lost Hills')

premium_rate = 0.4
control_level = ['10', '5']
insurance_strike = 1400.0
insurance_payment = [0.75, 0.9]
plotter.compare_mitigation_performance(timeseries_revenues['SMI']['banking'], annual_pumping, premium_rate, control_level, insurance_strike, insurance_payment, 'Semitropic')
#control_level = '5'
#insurance_payment = 0.9
#plotter.compare_mitigation_performance(timeseries_revenues['SMI']['banking'], annual_pumping, premium_rate, control_level, insurance_strike, insurance_payment, 'Semitropic')


