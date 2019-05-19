import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cord import *
from matplotlib.patches import Rectangle
import scipy.stats as stats
import datetime


init_plotting()
sns.set()

validation_flows = pd.read_csv('cord/data/input/cord-data.csv', index_col = 0, parse_dates= True)
simulation_flows = pd.read_csv('cord/data/input/cord-data-sim.csv', index_col = 0, parse_dates= True)

A=validation_flows['ORO_inf'] * 1.98
B=validation_flows['SAC_gains'] * 1.98
C=simulation_flows['ORO_inf'] * 1.98
D=simulation_flows['SAC_gains'] * 1.98
date1 = '1996-10-01'
date2 = '2016-09-30'
start = datetime.datetime.strptime(date1, '%Y-%m-%d')
end = datetime.datetime.strptime(date2, '%Y-%m-%d')
step = datetime.timedelta(days=1)
datetime_list = []
while start <= end:
  datetime_list.append(start.date())
  start += step
  
date1 = '1905-10-01'
date2 = '2016-09-30'
start = datetime.datetime.strptime(date1, '%Y-%m-%d')
end = datetime.datetime.strptime(date2, '%Y-%m-%d')
step = datetime.timedelta(days=1)
datetime_list2 = []
while start <= end:
  datetime_list2.append(start.date())
  start += step

fig = plt.figure(figsize=(8, 6)) 
gs = gridspec.GridSpec(2, 1) 
ax0 = plt.subplot(gs[0, 0])
p1 = ax0.plot(datetime_list, np.log(A), color='k', alpha = 1.0, linewidth = 1)
p2 = ax0.plot(datetime_list2, np.log(C), color='red', alpha = 0.6, linewidth = 1)

ax1 = plt.subplot(gs[1, 0])
p1 = ax1.plot(datetime_list, np.log(B), color='k', alpha = 1.0, linewidth = 1)
p2 = ax1.plot(datetime_list2, np.log(D), color='red', alpha = 0.6, linewidth = 1)
ax0.set_xlim([datetime.date(1905, 10, 1), datetime.date(2016, 9, 30)])
ax1.set_xlim([datetime.date(1905, 10, 1), datetime.date(2016, 9, 30)])
ax0.set_ylabel('Daily flow, ln(AF)')
ax1.set_ylabel('Daily flow, ln(AF)')
ax0.set_xlabel('')
ax1.set_ylim([-3.0, 15.0])
ax0.set_xticklabels('')
ax0.set_title('Oroville Reservoir Inflow')
ax1.set_title('Sacramento Delta Incremental Gains')
plt.legend(('Historical Observation', 'Simulated From Full-Natural-Flow'), fontsize = 14, loc = 'lower right', ncol = 2)
for item in [ax1.yaxis.label, ax0.yaxis.label]:
  item.set_fontsize(14)  
for item in (ax1.get_xticklabels()):
  item.set_fontsize(14) 

plt.show()

plotter.plot_almond_costs(25)
plotter.plot_almond_costs(15)
plotter.plot_almond_costs(23)
######################################################################################
###Plot Model Validation Results
######################################################################################
northern_results = pd.read_csv('cord/data/results/reservoir_results_no_validation.csv', index_col=0, parse_dates=True)
southern_results = pd.read_csv('cord/data/results/reservoir_results_so_validation.csv', index_col=0, parse_dates=True)
observations = pd.read_csv('cord/data/input/cord-data.csv', index_col=0, parse_dates=True)
x2_results = pd.read_csv('cord/data/results/x2DAYFLOW.csv', index_col=0, parse_dates=True)

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
plot_dim_1 = 3
plot_dim_2 = 3
reservoir_list = ['SHA', 'ORO', 'FOL', 'YRS', 'MIL', 'PFT', 'KWH', 'SUC', 'ISB']
title_list = ['SHASTA', 'OROVILLE', 'FOLSOM', 'NEW BULLARDS BAR', 'MILLERTON', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA']
plotter.make_reservoir_plots(northern_results, southern_results, observations, simulated_unit, observed_unit, reservoir_list, title_list, data_type, plot_dim_1, plot_dim_2, 'W')

data_type = '_X2'
simulated_unit = 1.0
observed_unit = 1.0
plot_dim_1 = 1
plot_dim_2 = 1
plotter.make_x2_plots(x2_results, data_type, plot_dim_1, plot_dim_2, 'W')


##############################
###SAN LUIS VALIDATION FIGURES
##############################
san_luis_list = ['SLS', 'SLF']
title_list = ['State (SWP) Portion', 'Federal (CVP) Portion']
data_type = '_storage'
simulated_unit = 1.0/1000.0
observed_unit = 1.0/1000000.0
plotter.make_san_luis_plots(southern_results, observations, simulated_unit, observed_unit, san_luis_list, title_list, data_type, 'W')


##############################
###BANK VALIDATION FIGURES
##############################
semitropic_observations = pd.read_csv('cord/data/input/semitropic_historical.csv')
arvin_observations = pd.read_csv('cord/data/input/arvin_historical.csv')
rosedale_observations = pd.read_csv('cord/data/input/rosedale_historical.csv')
banking_simulations = pd.read_csv('cord/data/results/leiu_results_annual_validation.csv')
banked_simulations = pd.read_csv('cord/data/results/bank_results_annual_validation.csv')
x = np.arange(1906,2017)

plotter.make_leiubank_plots(banking_simulations, semitropic_observations, [130.0, 0.0], ['MET',], ['Metropolitan',], 'SMI', 'Semitropic', range(1997,2015),1997)
plotter.make_leiubank_plots(banking_simulations, arvin_observations, [0.0, 0.0], ['MET',], ['Metropolitan',], 'ARV', 'Arvin Edison', range(1997,2015),1997)
plotter.make_bank_plots(banked_simulations, rosedale_observations, 0.0, ['BVA', 'CTL' ], ['Buena Vista', 'Castaic Lake'], 'R21', 'Rosedale Rio Bravo', range(2004,2017), 1997)
plotter.make_bank_plots(banked_simulations, rosedale_observations, 0.0, ['ARV', 'DLE'], ['Arvin Edison', 'Delano Earlimart'], 'R21', 'Rosedale Rio Bravo', range(2004,2017), 1997)


plotter.make_leiubank_plots_storage(banking_simulations, semitropic_observations, [130.0, 0.0], ['MET', 'SOB'], ['Metropolitan', 'South Bay'], 'SMI', 'Semitropic', range(1997,2015))
plotter.make_leiubank_plots_storage(banking_simulations, arvin_observations,[0.0, 0.0], ['MET',],['Metropolitan',], 'ARV', 'Arvin Edison', range(1997,2015))

######################################################################################
###Plot Simulation Results
######################################################################################
district_results = pd.read_csv('cord/data/results/annual_district_results_simulation.csv')
canal_results = pd.read_csv('cord/data/results/canal_results_validation.csv')
contract_results = pd.read_csv('cord/data/results/contract_results_annual_simulation.csv')

######################
###CANAL FIGURES######
######################
canal_key = 'XVC'
node_keys = ['BLY', 'AEC', 'FKC', 'KNR', 'GSL', 'BRM', 'B2800', 'PIO', 'IVR', 'KWB', 'BVA']
node_labels = ['Buena Vista WSD', 'Kern Water Bank', 'Irvine Ranch WD', 'Pioneer Project', 'Bakersfield 2800 Acres', 'Berrenda Mesa Banking Project' 'Goose Slough', 'Kern River', 'Friant-Kern Canal', 'Arvin Edison Canal', 'Beardsly Canal']
color_list = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'grey', 'indianred', 'black', 'pink', 'cyan']
bottom_value = np.zeros(len(canal_results['XVC_BVA']))

#init_plotting()
#sns.set()
#fig1 = plt.figure()
#ax0 = fig1.add_subplot(111)
#legend_dict = {}
#for x, colr, nme in zip(node_keys, color_list, node_labels):
  #top_value = canal_results[canal_key +  '_' + x]
  #base = np.arange(len(top_value))
  #print(x)
  #print(colr)
  #print(nme)
  #legend_dict[nme] = plt.fill_between(base,top_value,bottom_value, color = colr, alpha = 0.6)
  #bottom_value = top_value
#plt.xlabel('Time)')
#plt.ylabel('Deliveries on the Cross-Valley Canal (tAF)')
#legend_obj = tuple([legend_dict[e] for e in legend_dict])
#legend_names = tuple(legend_dict)
#plt.show()
######################
###PUMPING PDF FIGURES
######################
annual_pumping = district_results['0']
title = 'SWP Pumping'
thresholds = [0.01, 0.05, 0.1, 1.0]
threshold_list = ['1% Risk', '5% Risk', '20% Risk', 'Wettest 80%']
plotter.show_pumping_pdf(annual_pumping, 'SWP Pumping', max(annual_pumping), thresholds, threshold_list, [0.4,0.4,0.4,0.4] )
dwr_pumping = [250.0,750.0,750.0,750.0,750.0,750.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0, 2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0, 3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,4250.0,4250.0]
dwr_pumping2013 = [250.0, 750.0, 750.0,750.0,750.0,750.0,750.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0]
dwr_pumping2017 = [250.0,750.0,750.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1250.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0,1750.0, 2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2250.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0,2750.0, 3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3250.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,3750.0,4050.0,4050.0]
bins = [0.0, 500.0,1000.0,1500.0,2000.0,2500.0,3000.0,3500.0,4000.0,4500.0]
fig = plt.figure()
ax0 = fig.add_subplot(111)
kde = stats.gaussian_kde(annual_pumping)
pos = np.linspace(0.0, 4100.0, 101)
plt.hist([dwr_pumping2013,dwr_pumping, dwr_pumping2017], bins, color = ['cyan','lightskyblue','royalblue'], label = ['DWR 2013', 'DWR 2015', 'DWR2017'], density=True, alpha = 0.7)
p1 = plt.fill_between(pos, kde(pos), alpha = 0.7, facecolor = 'indianred')
plt.legend((Rectangle((0,0),1,1,color='cyan'),Rectangle((0,0),1,1,color='lightskyblue'),Rectangle((0,0),1,1,color='royalblue'), p1), ('DWR 2013', 'DWR 2015','DWR 2017', 'CALFEWS'), fontsize = 14)
ax0.set_ylabel('Probability')
ax0.set_yticklabels('')
plt.xlim([0.0,4500.0])
ax0.set_xlabel('Annual SWP Deliveries (tAF)')
for item in [ax0.xaxis.label, ax0.yaxis.label]:
  item.set_fontsize(20)  
for item in (ax0.get_xticklabels()):
  item.set_fontsize(16) 

plt.show()


fig = plt.figure()
ax1 = fig.add_subplot(111)
semi_deliveries = district_results['LHL_delivery']
semi_take = district_results['LHL_leiu_accepted']
semi_give = (district_results['LHL_leiu_delivered'] - semi_take)*-1.0
semi_bank_number = district_results['LHL_banked_accepted']
semi_bank = np.zeros(len(semi_bank_number))
for x in range(0,len(semi_bank_number)):
  semi_bank[x] = max(semi_bank_number[x] - semi_deliveries[x], 0.0)
  
x = np.arange(1906,2017)
z = np.zeros(len(semi_bank))
  #ax1.fill_between(x,data[0],data[1], color = 'xkcd:cornflower')
  #ax1.fill_between(x,data[1],data[2], color = 'xkcd:denim blue')
ax1.fill_between(x,semi_deliveries,z, color = 'blue', alpha = 0.2)
ax1.fill_between(x,semi_bank_number,semi_deliveries, color = 'blue', alpha = 0.5)
#ax1.fill_between(x,semi_take+semi_bank,semi_take, color = 'blue', alpha = 0.8)
#ax1.fill_between(x,z,semi_give, color = 'red', alpha = 0.5)
#ax1.set_ylabel('Net flow out of Semtropic (tAF)   Net flow into Semtropic (tAF) ')
ax1.set_ylabel('Annual irrigation deliveries within Lost Hills (tAF)')

sq1 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.2, markersize = 10, markerfacecolor = 'royalblue')
sq2 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.5, markersize = 10, markerfacecolor = 'royalblue')
sq3 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.5, markersize = 10, markerfacecolor = 'royalblue')
sq4 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.5, markersize = 10, markerfacecolor = 'indianred')
p2 = ax1.plot(x,np.zeros(len(x)), color='k', alpha = 0.7, linewidth = 2)

plt.xlim([1906, 2016])
plt.ylim([0, 100])
for item in [ax1.xaxis.label, ax1.yaxis.label]:
  item.set_fontsize(16)  
for item in (ax1.get_xticklabels() + ax1.get_yticklabels()):
  item.set_fontsize(14) 
#plt.legend((sq1, sq2, sq4), ("Table A Deliveries", "Bank Deposits to Semitropic", "Bank Withdrawals from Semitropic"), ncol = 1, fontsize = 14, loc = 'lower left')

plt.legend((sq1, sq2), ("Table A Deliveries", "Banked Recovery Deliveries"), ncol = 1, fontsize = 14, loc = 'upper right')
plt.show()

#plotter.show_pumping_bar(annual_pumping, 'SWP Pumping', max(annual_pumping))
##############################
###DEFICIT PLANNING FIGURES
##############################
delivery_risks = pd.read_csv('cord/data/results/delivery_risk_WON.csv')

delivery_risks_true = pd.read_csv('cord/data/annual_private_reults_simulation.csv')

year_range = np.arange(1906,2017) 
use_storage = False
use_flood = False
adjust_demand = False
show_demand = False
adjust_land = False
plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 0.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, False)
show_demand = True
plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 0.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, False)

use_storage = True
#plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 0.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, True)
plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 0.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, False)
use_flood = True
#plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 0.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, True)
plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 0.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, False)

adjust_demand = True
#plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 20.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, True)
plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 20.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, False)

adjust_land = True
#plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 20.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, True)
plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 20.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 0.0, year_range, False)
plotter.make_deficit_plots_true(delivery_risks_true, 'WON', 20.0, show_demand, use_storage, use_flood, adjust_demand, adjust_land, 500.0, year_range, False)



risk_deliveries50 = pd.read_csv('cord/data/results/annual_private_risk_50.csv')
risk_deliveries95 = pd.read_csv('cord/data/results/annual_private_risk_95.csv')
risk_deliveries99 = pd.read_csv('cord/data/results/annual_private_risk_99.csv')
plotter.make_private_plots(risk_deliveries50, 'WON', year_range)
plotter.make_private_plots(risk_deliveries95, 'WON', year_range)
plotter.make_private_plots(risk_deliveries99, 'WON', year_range)

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

plotter.show_insurance_payouts(annual_pumping, revenue_series, color_series, alpha_dict, 1500.0, 'SWP Pumping', 'Lost Hills', 14.0, True)

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
  
plotter.show_insurance_payouts(annual_pumping, revenue_series, color_series, alpha_dict, 1200.0, 'SWP Pumping', 'Semitropic', 45.0, True)

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


