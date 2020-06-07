import numpy as np
import pandas as pd
import h5py
import json
import matplotlib.pyplot as plt
from itertools import compress
from cord import *
from cord.visualizer import Visualizer

#results hdf5 file location from CALFEWS simulations
output_folder = 'cord/data/results/'
output_file = output_folder + 'baseline_wy2017/p0/results_p19962016.hdf5'
output_file_sim = output_folder + 'baseline_wy2017/p0/results_p19062016.hdf5'
##get model variable names
modelno = pd.read_pickle(output_folder + 'modelno0.pkl')
modelso = pd.read_pickle(output_folder + 'modelso0.pkl')

##Folder to write visualization files
results_folder = 'cord/data/results/figures/'

##plot figures in python
show_plot = False
##Set up data for validation results
validation = Visualizer(modelso.district_list, modelso.private_list, modelso.city_list, modelso.contract_list, modelso.waterbank_list, modelso.leiu_list)
validation.get_results_sensitivity_number(output_file, 19962016, 10, 1996, 1)
validation.set_figure_params()
#Set up data for scenario results
simulation = Visualizer(modelso.district_list, modelso.private_list, modelso.city_list, modelso.contract_list, modelso.waterbank_list, modelso.leiu_list)
simulation.get_results_sensitivity_number(output_file_sim, 19062016, 10, 1905, 1)
simulation.set_figure_params()

##Compare Delta pumping/outflow distributions between scenarios
print('Scenario Comp')
plot_type = 'delta_pumping'
plot_name = 'Extended Simulation'
simulation.scenario_compare(results_folder, plot_type, plot_name, validation.values, show_plot)

#Plot district deliveries - both the physical location (for links w/GW and PMP modelling) and the 'account' - for financial risk
plot_type = 'district_water_use'
water_use_plots = ['physical', 'account']
for plot_name in water_use_plots:
  print('Deliveries ' + plot_name)
  ##Uses the 'scenario' files
  #simulation.make_deliveries_by_district(results_folder, plot_type, plot_name, show_plot)
  validation.make_deliveries_by_district(results_folder, plot_type, plot_name, '19972016', show_plot)
  simulation.make_deliveries_by_district(results_folder, plot_type, plot_name, '19062016', show_plot)

##Plot snowpack/flow relationships for different watersheds
plot_type = 'state_estimation'
forecast_plots = ['publication', 'sacramento', 'sanjoaquin', 'tulare']
n_days_colorbar = 180
scatter_plot_interval = 30
range_sensitivity = 5.0 # higher number limits range of regression function plotting closer to the range of the data
for plot_name in forecast_plots:
  print('Forcasts ' + plot_name)
  validation.plot_forecasts(results_folder, plot_type, plot_name, n_days_colorbar, scatter_plot_interval, range_sensitivity, show_plot)

#Plot 'states' for contracts, reservoirs, districts
reservoir_name = 'sanluisstate'
district_label = 'wheeler'
district_key = 'WRM'
plot_type = 'state_response'
district_private_labels = []
district_private_keys = []
print('State Response, ' + district_key)
##Uses the 'vaidation' files
validation.show_state_response(results_folder, plot_type, reservoir_name, district_label, district_key, district_private_labels, district_private_keys, show_plot)

##Plot validation between model & observations
print('Model Validation')
#delta pumping variables
plot_type = 'model_validation'
plot_name = 'delta'
use_scatter = True
validation.make_validation_timeseries(results_folder, plot_type, plot_name, show_plot, use_scatter)

#sierra reservoirs
plot_name = 'sierra'
use_scatter = False
num_cols = 3
validation.make_validation_timeseries(results_folder, plot_type, plot_name, show_plot, use_scatter, num_cols)

#san luis reservoirs
plot_name = 'sanluis'
use_scatter = True
validation.make_validation_timeseries(results_folder, plot_type, plot_name, show_plot, use_scatter)

#groundwater banks
plot_name = 'bank'
use_scatter = True
validation.make_validation_timeseries(results_folder, plot_type, plot_name, show_plot, use_scatter)

#sankey diagrams - write figures for water 'flows' in each day, then write to GIF
plot_type = 'flow_diagram'
plot_name = 'tulare'
timesteps = 20000 #timesteps need to be greater than the snapshot range
snapshot_range = (14600, 14975)
results_folder = 'cord/data/results/sankeys/'
simulation.plot_account_flows(results_folder, plot_type, plot_name, timesteps, snapshot_range)	
simulation.make_gif(results_folder + 'cali_sankey', '1946', 14601, 14975)


