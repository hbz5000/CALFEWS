import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cord import *

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
plotter.make_pumping_plots(northern_results, observations, simulated_unit, observed_unit, pump_list, title_list, label_loc, 'W', 'AS-OCT')

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
plotter.make_reservoir_plots(northern_results, observations, simulated_unit, observed_unit, reservoir_list, title_list, data_type, plot_dim_1, plot_dim_2, 'W')

##############################
###SAN LUIS VALIDATION FIGURES
##############################
san_luis_list = ['SLS', 'SLF']
title_list = ['State (SWP) Portion', 'Federal (CVP) Portion']
data_type = '_storage'
simulated_unit = 1.0/1000.0
observed_unit = 1.0/1000000.0
plotter.make_san_luis_plots(southern_results, observations, simulated_unit, observed_unit, san_luis_list, title_list, data_type, 'W')

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
plotter.show_pumping_pdf(annual_pumping, 'SWP Pumping', max(annual_pumping), thresholds, threshold_list)

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

legend_names = ['Table A Deliveries', 'All Deliveries (inc. GW Recovery)']
stored_names = ['delivery', 'recovery']
color_names = ['black', 'red']
revenue_series = {}
color_series = {}
for x,y,z in zip(legend_names, stored_names, color_names):
  revenue_series[x] = timeseries_revenues['LHL'][y]
  color_series[x] = z  
plotter.show_insurance_payouts(annual_pumping, revenue_series, color_series, 1700.0, 'SWP Pumping', 'Lost Hills', 12.0, True)

legend_names = ['Table A Deliveries', 'All Revenue (inc. Bank Operations)']
stored_names = ['delivery', 'banking']
color_names = ['black', 'red']
revenue_series = {}
color_series = {}
for x,y,z in zip(legend_names, stored_names, color_names):
  revenue_series[x] = timeseries_revenues['SMI'][y]
  color_series[x] = z
  
plotter.show_insurance_payouts(annual_pumping, revenue_series, color_series, 1400.0, 'SWP Pumping', 'Semitropic', 45.0, True)

###############################
###MITIGATION BAR GRAPH FIGURES
###############################
value_at_risk_target = 1.0
value_at_risk_level = 0.99
search_increments_contingency = 20
search_increments_insurance = 20
evaluation_block_length = 30
interest_rate = 0.05
premium_rate = 0.4
plotter.show_mitigation_plots(timeseries_revenues['LHL']['recovery'], annual_pumping, value_at_risk_target, value_at_risk_level, search_increments_contingency, search_increments_insurance, evaluation_block_length, interest_rate, premium_rate, 'Lost Hills')
plotter.show_mitigation_plots(timeseries_revenues['SMI']['banking'], annual_pumping, value_at_risk_target, value_at_risk_level, search_increments_contingency, search_increments_insurance, evaluation_block_length, interest_rate, premium_rate, 'Semitropic')

