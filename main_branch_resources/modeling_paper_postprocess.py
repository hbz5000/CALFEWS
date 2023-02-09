import numpy as np
import pandas as pd
import h5py
import json
import matplotlib.pyplot as plt
from itertools import compress
from datetime import datetime
import os
import sys
from calfews_src import *
from calfews_src.visualizer import Visualizer
startTime = datetime.now()

#results hdf5 file location from CALFEWS simulations
# output_folder_val = 'results/baseline_wy2017/validation/CDEC/'
# output_folder_sim = 'results/baseline_wy2017/simulation/CDEC/'
output_folder_val = sys.argv[1] + '/'
output_folder_sim = sys.argv[2] + '/'
fig_folder = sys.argv[3] + '/'
sankeys_folder = sys.argv[4] + '/'

output_file_val = output_folder_val + 'results.hdf5'
output_file_sim = output_folder_sim + 'results.hdf5'

##get model variable names
# modelno_val = pd.read_pickle(output_folder_val+ 'modelno0.pkl')
# modelno_sim = pd.read_pickle(output_folder_sim + 'modelno0.pkl')

modelso_val = pd.read_pickle(output_folder_val + 'modelso0.pkl')
modelso_sim = pd.read_pickle(output_folder_sim + 'modelso0.pkl')

##Folder to write visualization files
# fig_folder = 'results/baseline_wy2017/figures/'
# sankeys_folder = 'results/baseline_wy2017/sankeys/'
os.makedirs(fig_folder, exist_ok=True)
os.makedirs(sankeys_folder, exist_ok=True)

##Set up data for validation results
validation = Visualizer(modelso_val.district_list, modelso_val.private_list, modelso_val.city_list, modelso_val.contract_list, modelso_val.waterbank_list, modelso_val.leiu_list)
validation.get_results_sensitivity_number(output_file_val, '', 10, 1996, 1)
validation.set_figure_params()
#Set up data for scenario results
simulation = Visualizer(modelso_sim.district_list, modelso_sim.private_list, modelso_sim.city_list, modelso_sim.contract_list, modelso_sim.waterbank_list, modelso_sim.leiu_list)
simulation.get_results_sensitivity_number(output_file_sim, '', 10, 1905, 1)
simulation.set_figure_params()

##plot figures in python
show_plot = False

print('Finish set up, ', datetime.now() - startTime)

##Compare Delta pumping/outflow distributions between scenarios
# print('Scenario Comp')
plot_type = 'delta_pumping'
plot_name = 'extended_simulation'
simulation.scenario_compare(fig_folder, plot_type, plot_name, validation.values, show_plot)
print('Finish Delta pumping/outflow figure, ', datetime.now() - startTime)

#Plot district deliveries - both the physical location (for links w/GW and PMP modelling) and the 'account' - for financial risk
plot_type = 'district_water_use'
water_use_plots = ['annual', 'monthly']
for plot_name in water_use_plots:
  # print('Deliveries ' + plot_name)
  ##Uses the 'scenario' files
  #simulation.make_deliveries_by_district(fig_folder, plot_type, plot_name, show_plot)
  validation.make_deliveries_by_district(fig_folder, plot_type, plot_name, 'validation', show_plot)
  simulation.make_deliveries_by_district(fig_folder, plot_type, plot_name, 'simulation', show_plot)
print('Finish district deliveries figure, ', datetime.now() - startTime)

##Plot snowpack/flow relationships for different watersheds
plot_type = 'state_estimation'
forecast_plots = ['publication', 'sacramento', 'sanjoaquin', 'tulare']
n_days_colorbar = 180
scatter_plot_interval = 30
range_sensitivity = 5.0 # higher number limits range of regression function plotting closer to the range of the data
for plot_name in forecast_plots:
  # print('Forcasts ' + plot_name)
  validation.plot_forecasts(fig_folder, plot_type, plot_name, n_days_colorbar, scatter_plot_interval, range_sensitivity, show_plot)
print('Finish snowpack/flow relationship figure, ', datetime.now() - startTime)

#Plot 'states' for contracts, reservoirs, districts
reservoir_name = 'sanluisstate'
district_label = 'wheeler'
district_key = 'WRM'
plot_type = 'state_response'
district_private_labels = []
district_private_keys = []
# print('State Response, ' + district_key)
##Uses the 'vaidation' files
validation.show_state_response(fig_folder, plot_type, reservoir_name, district_label, district_key, district_private_labels, district_private_keys, show_plot)
print('Finish state response figure, ', datetime.now() - startTime)

##Plot validation between model & observations
# print('Model Validation')
#delta pumping variables
plot_type = 'model_validation'
plot_name = 'delta'
use_scatter = True
validation.make_validation_timeseries(fig_folder, plot_type, plot_name, show_plot, use_scatter)

#sierra reservoirs
plot_name = 'sierra'
use_scatter = False
num_cols = 3
validation.make_validation_timeseries(fig_folder, plot_type, plot_name, show_plot, use_scatter, num_cols)

#san luis reservoirs
plot_name = 'sanluis'
use_scatter = True
validation.make_validation_timeseries(fig_folder, plot_type, plot_name, show_plot, use_scatter)

#groundwater banks
plot_name = 'bank'
use_scatter = True
validation.make_validation_timeseries(fig_folder, plot_type, plot_name, show_plot, use_scatter)
print('Finish validation figures, ', datetime.now() - startTime)

#sankey diagrams - write figures for water 'flows' in each day, then write to GIF
print('Starting Sankey diagrams (this will take a while)')
plot_type = 'flow_diagram'
plot_name = 'tulare'
timesteps = 15000 #timesteps need to be greater than the snapshot range
snapshot_range = list(range(14600, 14975))
simulation.plot_account_flows(sankeys_folder, plot_type, plot_name, timesteps, snapshot_range)	
simulation.make_gif(sankeys_folder + 'cali_sankey', '1946', snapshot_range)
print('Finish Sankey gif, ', datetime.now() - startTime)