import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from cord import *


######################################################################################
###Plot Simulation Results
######################################################################################
district_results = pd.read_csv('cord/data/results/annual_district_results_simulation.csv')
contract_results = pd.read_csv('cord/data/results/contract_results_annual_simulation.csv')

modelplot = Model('cord/data/input/cord-data.csv', 'cord/data/input/cord-data.csv', '10-01-1996', 'simulation')
modelplot.initialize_water_districts()

kern_county_list = [modelplot.berrenda, modelplot.belridge, modelplot.buenavista, modelplot.cawelo, modelplot.henrymiller, modelplot.kerndelta, modelplot.losthills, modelplot.rosedale, modelplot.semitropic, modelplot.tehachapi, modelplot.tejon, modelplot.westkern, modelplot.wheeler, modelplot.dudleyridge]

modelplot.berrenda.price = 90.0
modelplot.belridge.price = 180.0
modelplot.buenavista.price = 22.0
modelplot.cawelo.price = 80.0
modelplot.henrymiller.price = 129.74
modelplot.kerndelta.price = 40.0
modelplot.losthills.price = 129.74
modelplot.rosedale.price = 0.0
modelplot.semitropic.price = 103.0
modelplot.tehachapi.price = 385.0
modelplot.tejon.price = 385.0
modelplot.westkern.price = 0.0
modelplot.wheeler.price = 85.0
modelplot.dudleyridge.price = 129.74

modelplot.berrenda.assessment = 156.0
modelplot.belridge.assessment = 0.0
modelplot.buenavista.assessment = 38.0
modelplot.cawelo.assessment = 397.0
modelplot.henrymiller.assessment = 0.0
modelplot.kerndelta.assessment = 10.0
modelplot.losthills.assessment = 0.0
modelplot.rosedale.assessment = 12.0
modelplot.semitropic.assessment = 40.0
modelplot.tehachapi.assessment = 0.0
modelplot.tejon.assessment = 0.0
modelplot.westkern.assessment = 0.0
modelplot.wheeler.assessment = 400.0 
modelplot.dudleyridge.assessment = 0.0

modelplot.berrenda.bank_get = 0.0
modelplot.belridge.bank_get = 0.0
modelplot.buenavista.bank_get = 0.0
modelplot.cawelo.bank_get = 0.0
modelplot.henrymiller.bank_get = 0.0
modelplot.kerndelta.bank_get = 0.0
modelplot.losthills.bank_get = 0.0
modelplot.rosedale.bank_get = 0.0
modelplot.semitropic.bank_get = 112.33
modelplot.tehachapi.bank_get = 0.0
modelplot.tejon.bank_get = 0.0
modelplot.westkern.bank_get = 0.0
modelplot.wheeler.bank_get = 0.0 
modelplot.dudleyridge.bank_get = 0.0

modelplot.berrenda.bank_give = 0.0
modelplot.belridge.bank_give = 0.0
modelplot.buenavista.bank_give = 0.0
modelplot.cawelo.bank_give = 0.0
modelplot.henrymiller.bank_give = 0.0
modelplot.kerndelta.bank_give = 0.0
modelplot.losthills.bank_give = 0.0
modelplot.rosedale.bank_give = 0.0
modelplot.semitropic.bank_give = 86.33
modelplot.tehachapi.bank_give = 0.0
modelplot.tejon.bank_give = 0.0
modelplot.westkern.bank_give = 0.0
modelplot.wheeler.bank_give = 0.0 
modelplot.dudleyridge.bank_give = 0.0

annual_pumping = district_results['0']
annual_pumping_cvp = district_results['1']
expected_value_swp = 0.0
expected_value_cvp = 0.0
expected_value_swp_3ya = 0.0
expected_value_cvp_3ya = 0.0
expected_value_swp_2ya = 0.0
expected_value_cvp_2ya = 0.0
strike_swp = 1500
strike_cvp = 1250

for x in range(0,len(annual_pumping)):
  expected_value_swp += max(strike_swp- annual_pumping[x], 0.0)/len(annual_pumping)
  expected_value_cvp += max(strike_cvp - annual_pumping_cvp[x], 0.0)/len(annual_pumping)
  print(x, end = " ")
  print(np.mean(annual_pumping[(x-1):x]), end = " ")
  print(annual_pumping[x], end = " ")
  print(expected_value_swp)


for x in range(1, len(annual_pumping)):
  expected_value_swp_2ya += max(strike_swp - np.mean(annual_pumping[(x-1):(x+1)]), 0.0)/(len(annual_pumping)-1)
  expected_value_cvp_2ya += max(strike_cvp - np.mean(annual_pumping_cvp[(x-1):(x+1)]), 0.0)/(len(annual_pumping)-1)

annual_pumping_cvp_3ya = np.zeros(len(annual_pumping)-2)
annual_pumping_swp_3ya = np.zeros(len(annual_pumping)-2)
for x in range(2, len(annual_pumping)):
  expected_value_swp_3ya += max(strike_swp - np.mean(annual_pumping[(x-2):(x+1)]), 0.0)/(len(annual_pumping)-2)
  expected_value_cvp_3ya += max(strike_cvp - np.mean(annual_pumping_cvp[(x-2):(x+1)]), 0.0)/(len(annual_pumping)-2)
  annual_pumping_swp_3ya[x-2] = annual_pumping[x-2] + annual_pumping[x-1] + annual_pumping[x]
  annual_pumping_cvp_3ya[x-2] = annual_pumping_cvp[x-2] + annual_pumping_cvp[x-1] + annual_pumping_cvp[x]

  
  

print(expected_value_swp)
print(expected_value_cvp)
print(expected_value_swp_3ya)
print(expected_value_cvp_3ya)
print(expected_value_swp_2ya)
print(expected_value_cvp_2ya)


sorted_pumping = np.sort(annual_pumping_cvp_3ya)
ten_percent = sorted_pumping[int(np.ceil(.2*len(annual_pumping_swp_3ya)))]
five_percent = sorted_pumping[int(np.ceil(.05*len(annual_pumping_swp_3ya)))]
one_percent = sorted_pumping[0]
print(np.mean(annual_pumping_cvp))
print(ten_percent)
print(five_percent)
print(one_percent)
sorted_pumping = np.sort(annual_pumping_swp_3ya)
ten_percent = sorted_pumping[int(np.ceil(.2*len(annual_pumping_swp_3ya)))]
five_percent = sorted_pumping[int(np.ceil(.05*len(annual_pumping_swp_3ya)))]
one_percent = sorted_pumping[0]
print(np.mean(annual_pumping))
print(ten_percent)
print(five_percent)
print(one_percent)

timeseries_revenues = {}
average_revenue = {}
kcwa_revenues = {}
for type in ['delivery', 'recovery', 'banking']:
  kcwa_revenues[type] = np.zeros(len(district_results))

key_list = ['BDM', 'BLR', 'LHL']
kern_county_keys = ['BDM', 'BLR', 'BVA', 'CWO', 'HML', 'KND', 'LHL', 'RRB', 'SMI', 'THC', 'TJC', 'WKN', 'WRM', 'DLR']
plotter.show_recovery(district_results, key_list, 'SWP Pumping')
contract_type = 'SLS'
plotter.show_contract_types(contract_results, contract_type)
plotter.show_pumping_pdf(annual_pumping, 'SWP Pumping', 4000.0)
#plotter.compare_contracts()
for x in kern_county_list:
  timeseries_revenues[x.key] = {}
  average_revenue[x.key] = {}
  for type in ['delivery', 'recovery', 'banking']:
    timeseries_revenues[x.key][type], average_revenue[x.key][type] = plotter.find_district_revenues(district_results, x.key, x.acreage['W'], x.price, x.assessment, x.bank_get, x.bank_give, type)
    kcwa_revenues[type] += timeseries_revenues[x.key][type]
for x in [modelplot.semitropic, modelplot.losthills]:
  if x.in_leiu_banking:
    plotter.show_district_revenues(timeseries_revenues[x.key],0,40.0, 'banking')
  else:
    plotter.show_district_revenues(timeseries_revenues[x.key],0,14.0, 'recovery')


plotter.show_district_revenues(kcwa_revenues, 90.0, 180.0, 'banking')
plotter.show_recovery_historic(district_results, timeseries_revenues, average_revenue, kern_county_keys, 1976, 1980, -80.0, 0.0, 20.0, 0.0, 1000.0, 250.0, 0)
plotter.show_recovery_historic(district_results, timeseries_revenues, average_revenue, kern_county_keys, 1986, 1994, -80.0, 0.0, 20.0, 0.0, 1000.0, 250.0, 0)
plotter.show_recovery_historic(district_results, timeseries_revenues, average_revenue, kern_county_keys, 2012, 2017, -80.0, 0.0, 20.0, 0.0, 1000.0, 250.0, 0)

max_volumetric_price = 150.0
max_total_price = 400.0
contingency_increments = 30
insurance_increments = 20
evaluation_length = 30
group_revenues = {}
group_averages = {}
group_value_at_risk = {}
for type in ['delivery', 'recovery', 'banking', 'price']:
  group_revenues[type] = np.zeros(len(annual_pumping))
  group_averages[type] = 0.0
  group_value_at_risk[type] = 0.0
  
group_revenues['CF'] = np.zeros((contingency_increments, len(annual_pumping)*evaluation_length))
group_revenues['insurance'] = np.zeros((contingency_increments*insurance_increments, len(annual_pumping)*evaluation_length))
group_averages['CF'] = np.zeros(contingency_increments)
group_averages['insurance'] = np.zeros(contingency_increments*insurance_increments)
group_value_at_risk['CF'] = np.zeros(contingency_increments)
group_value_at_risk['insurance'] = np.zeros(contingency_increments*insurance_increments)

plotter.show_insurance_payouts(annual_pumping, timeseries_revenues['LHL']['delivery'], timeseries_revenues['LHL']['recovery'], 1500.0, 1500.0, 'SWP Pumping', 'Lost Hills', 12.0)
plotter.show_insurance_payouts(annual_pumping, timeseries_revenues['SMI']['delivery'], timeseries_revenues['SMI']['banking'], 2000.0, 2000.0, 'SWP Pumping', 'Semitropic', 45.0)



mitigate_list = [modelplot.semitropic, modelplot.losthills, modelplot.semitropic, modelplot.losthills]
for x in mitigate_list:
  district_deliveries = district_results[x.key + '_banked_accepted']
  timeseries_revenues[x.key]['price'], average_revenue[x.key]['price'] = find_pricing_mitigation(district_deliveries, x.acreage['W'], average_revenue[x.key]['recovery'], max_volumetric_price, max_total_price, x.price, x.assessment)
  timeseries_revenues[x.key]['CF'] = {}
  timeseries_revenues[x.key]['insurance'] = {}
  average_revenue[x.key]['CF'] = {}
  average_revenue[x.key]['insurance'] = {}
  x.value_at_risk = {}
  insurance_cutoff = {}
  insurance_cutoff['delivery'] = 2.5
  insurance_cutoff['recovery'] = 0.75
  insurance_cutoff['price'] = 1.0
  insurance_cutoff['banking'] = 2.0
  for start_type in ['banking', 'recovery']:
    timeseries_revenues[x.key]['CF'][start_type] = np.zeros((contingency_increments, len(annual_pumping)*evaluation_length))
    average_revenue[x.key]['CF'][start_type] = np.zeros(contingency_increments)
    annual_cost = {}
    annual_cost['CF'] = {}
    annual_cost['CF']['contribution'] = np.zeros(contingency_increments)
    annual_cost['CF']['premium'] = np.zeros(contingency_increments)

    for contingency_index in range(0,contingency_increments):
      contingency_fund_start = 1.5*contingency_index*average_revenue[x.key][start_type]/contingency_increments
      insurance_strike = 0.0
      insurance_cost = 0.0
      insurance_payout = np.zeros(2)
      timeseries_revenues[x.key]['CF'][start_type][contingency_index][:], average_revenue[x.key]['CF'][start_type][contingency_index] = plotter.find_insurance_mitigation(annual_pumping, timeseries_revenues[x.key][start_type], average_revenue[x.key][start_type], evaluation_length, insurance_cost, insurance_strike, insurance_payout, contingency_fund_start, insurance_cutoff[start_type])
      annual_cost['CF']['contribution'][contingency_index] = contingency_fund_start*1.96/30 
    
    annual_cost['insurance'] = {}
    annual_cost['insurance']['contribution'] = np.zeros(contingency_increments*insurance_increments)
    annual_cost['insurance']['premium'] = np.zeros(contingency_increments*insurance_increments)
    
    timeseries_revenues[x.key]['insurance'][start_type] = np.zeros((contingency_increments*insurance_increments, len(annual_pumping)*evaluation_length))
    average_revenue[x.key]['insurance'][start_type] = np.zeros(contingency_increments*insurance_increments)    
    for contingency_index in range(0,contingency_increments):
      contingency_fund_start = 1.0*contingency_index*average_revenue[x.key][start_type]/contingency_increments
      for insurance_index in range(0, insurance_increments):
        insurance_strike = insurance_index*50.0 + 1000.0
        insurance_payout = plotter.find_insurance_payment_constant(annual_pumping, timeseries_revenues[x.key][start_type], insurance_strike)
        insurance_cost = plotter.price_insurance(annual_pumping, insurance_strike, insurance_payout, 1.4)
        timeseries_revenues[x.key]['insurance'][start_type][contingency_index*insurance_increments + insurance_index][:], average_revenue[x.key]['insurance'][start_type][contingency_index*insurance_increments + insurance_index] = plotter.find_insurance_mitigation(annual_pumping, timeseries_revenues[x.key][start_type], average_revenue[x.key][start_type], evaluation_length, insurance_cost, insurance_strike, insurance_payout, contingency_fund_start, insurance_cutoff[start_type]) 
        annual_cost['insurance']['contribution'][contingency_index*insurance_increments + insurance_index] = contingency_fund_start*1.96/30
        annual_cost['insurance']['premium'][contingency_index*insurance_increments + insurance_index] = insurance_cost
 
  
    x.value_at_risk[start_type] = {}
    percentile = 0.99
    for type in [start_type, 'CF', 'insurance']:
      if type == 'CF':
        x.value_at_risk[start_type]['CF'] = np.zeros(contingency_increments)
        print(contingency_index)
        for contingency_index in range(0,contingency_increments):
          print(contingency_index, end = " ")
          x.value_at_risk[start_type]['CF'][contingency_index] = plotter.show_value_at_risk(timeseries_revenues[x.key]['CF'][start_type][contingency_index], average_revenue[x.key]['CF'][start_type][contingency_index], percentile)
      elif type == 'insurance':
        x.value_at_risk[start_type]['insurance'] = np.zeros(contingency_increments*insurance_increments)
        for insurance_index in range(0,contingency_increments*insurance_increments):
          print(insurance_index, end = " ")
          x.value_at_risk[start_type]['insurance'][insurance_index] = plotter.show_value_at_risk(timeseries_revenues[x.key]['insurance'][start_type][insurance_index], average_revenue[x.key]['insurance'][start_type][insurance_index], percentile)
      else:
        x.value_at_risk[start_type]['none'] = 0.0
        print('none')
        x.value_at_risk[start_type]['none'] = plotter.show_value_at_risk(timeseries_revenues[x.key][start_type], average_revenue[x.key][start_type], percentile)

	
    contingency_figure_index = plotter.find_index(x.value_at_risk[start_type]['CF'], average_revenue[x.key]['CF'][start_type], insurance_cutoff[start_type])
    insurance_figure_index = plotter.find_index(x.value_at_risk[start_type]['insurance'], average_revenue[x.key]['insurance'][start_type], insurance_cutoff[start_type])
    fig1 = plt.figure()
    ax0 = fig1.add_subplot(111)
    ax1 = plt.plot(timeseries_revenues[x.key]['CF'][start_type][contingency_figure_index],color = 'red', linewidth = 3)  
    ax1 = plt.plot(timeseries_revenues[x.key]['insurance'][start_type][insurance_figure_index],color = 'blue', linewidth = 3)  
    plt.show()
	
    bar_shapes = plotter.find_revenue_buckets(timeseries_revenues[x.key], contingency_figure_index, insurance_figure_index, start_type)
    plotter.show_revenue_variability(bar_shapes, average_revenue[x.key], contingency_figure_index, insurance_figure_index, start_type, annual_cost, max(timeseries_revenues[x.key][start_type]))

plotter.show_insurance_payouts(annual_pumping, timeseries_revenues[x.key]['delivery'], timeseries_revenues[x.key]['recovery'], 2000.0)

type_list = ['delivery', 'recovery', 'banking', 'price']
certain_revenues = np.zeros(5)
var1_revenues = np.zeros(5)
var2_revenues = np.zeros(5)
for i,v in enumerate(type_list):
  certain_revenues[i] = wonderful_averages[v] - wonderful_var['99%'][v]
  var1_revenues[i] = wonderful_var['95%'][v]
  var2_revenues[i] = wonderful_var['99%'][v] - wonderful_var['95%'][v]
for x in wonderful_list:
  for contingency_index in range(0, contingency_increments):
    if x.value_at_risk['CF'][contingency_index] < 0.5:
      x.index_use = contingency_index
      break
  max_revenue = 0.0
  for insurance_index in range(0, contingency_increments*insurance_increments):
    if x.value_at_risk['insurance'][insurance_index] < 0.45 and x.average_revenue['insurance'][insurance_index] > max_revenue:
      x.index_use_2 = insurance_index
      max_revenue = x.average_revenue['insurance'][insurance_index]
	
  certain_revenues[3] += (x.average_revenue['CF'][int(x.index_use)] - x.value_at_risk2['CF'][int(x.index_use)])
  var1_revenues[3] += (x.value_at_risk['CF'][int(x.index_use)])
  var2_revenues[3] += (x.value_at_risk2['CF'][int(x.index_use)] - x.value_at_risk['CF'][int(x.index_use)])

  certain_revenues[4] += (x.average_revenue['insurance'][int(x.index_use_2)] - x.value_at_risk2['insurance'][int(x.index_use_2)])
  var1_revenues[4] += (x.value_at_risk['insurance'][int(x.index_use_2)])
  var2_revenues[4] += (x.value_at_risk2['insurance'][int(x.index_use_2)] - x.value_at_risk['insurance'][int(x.index_use_2)])



for x in wonderful_list:
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  for contingency_index in range(0,contingency_increments):
    zero_counter = 0
    for insurance_index in range(0,insurance_increments):
      xxx = contingency_index*insurance_increments + insurance_index
      if zero_counter == 0 or x.value_at_risk['insurance'][xxx] > 0.001:  
        print(zero_counter, end = " ")
        print(x.value_at_risk['insurance'][xxx])
        ax1.scatter(x.average_revenue['insurance'][xxx], x.value_at_risk['insurance'][xxx], s=50, c='orange', edgecolor='none', alpha=0.7)
      if x.value_at_risk['insurance'][xxx] < 0.001:
        zero_counter = 1
      else:
        zero_counter = 0
  zero_counter = 0
  for xx in range(0,contingency_increments):
    if zero_counter == 0 or x.value_at_risk['CF'][xx] > 0.001:  
      ax1.scatter(x.average_revenue['CF'][xx], x.value_at_risk['CF'][xx], s=50, c='purple', edgecolor='none', alpha=0.7)
    if x.value_at_risk['CF'][xx] < 0.001:
      zero_counter = 1
    else:
      zero_counter = 0
  ax1.scatter(x.average_revenue['price'], x.value_at_risk['price'], s=50, c='green', edgecolor='none', alpha=0.7)
  ax1.scatter(x.average_revenue['banking'], x.value_at_risk['banking'], s=50, c='red', edgecolor='none', alpha=0.7) 
  ax1.scatter(x.average_revenue['delivery'], x.value_at_risk['delivery'], s=50, c='steelblue', edgecolor='none', alpha=0.7)


  connectorX = {}
  connectorY = {}
  connectorX['banking'] = np.zeros(2)
  connectorY['banking'] = np.zeros(2)
  connectorX['price'] = np.zeros(3)
  connectorY['price'] = np.zeros(3)
  connectorX['CF'] = np.zeros(contingency_increments+1)
  connectorY['CF'] = np.zeros(contingency_increments+1)
  connectorX['insurance'] = np.zeros((contingency_increments,insurance_increments+1))
  connectorY['insurance'] = np.zeros((contingency_increments,insurance_increments+1))

  connectorX['banking'][0] = x.average_revenue['delivery']
  connectorY['banking'][0] = x.value_at_risk['delivery']
  connectorX['price'][0] = x.average_revenue['delivery']
  connectorY['price'][0] = x.value_at_risk['delivery']
  connectorX['banking'][1] = x.average_revenue['banking']
  connectorY['banking'][1] = x.value_at_risk['banking']
  connectorX['price'][1] = x.average_revenue['banking']
  connectorY['price'][1] = x.value_at_risk['banking']
  connectorX['price'][2] = x.average_revenue['price']
  connectorY['price'][2] = x.value_at_risk['price']
  connectorX['CF'][0] = x.average_revenue['banking']
  connectorY['CF'][0] = x.value_at_risk['banking']
  ins_breakpoint = np.zeros(contingency_increments)
  for xx in range(0,contingency_increments):
    connectorX['CF'][1+xx] = x.average_revenue['CF'][xx]
    connectorY['CF'][1+xx] = x.value_at_risk['CF'][xx]
    connectorX['insurance'][xx][0] = x.average_revenue['CF'][xx]
    connectorY['insurance'][xx][0] = x.value_at_risk['CF'][xx]
    for xxx in range(0,insurance_increments):
      connectorX['insurance'][xx][1+xxx] = x.average_revenue['insurance'][xx*insurance_increments+xxx]
      connectorY['insurance'][xx][1+xxx] = x.value_at_risk['insurance'][xx*insurance_increments+xxx]	
      if x.value_at_risk['insurance'][xx*insurance_increments+xxx] < 0.001:
        ins_breakpoint[xx] = xxx + 1
      elif xxx == insurance_increments - 1:
        ins_breakpoint[xx] = insurance_increments
		
    if x.value_at_risk['CF'][xx] < 0.001:
      breakpoint = xx + 1
    elif xx == contingency_increments - 1:
      breakpoint = contingency_increments
	  
  for xxx in range(0,breakpoint):
    ax1.plot(connectorX['insurance'][xxx][0:int(ins_breakpoint[xxx]+1)], connectorY['insurance'][xxx][0:int(ins_breakpoint[xxx]+1)], color = 'orange')
  ax1.plot(connectorX['CF'][0:(breakpoint+1)], connectorY['CF'][0:(breakpoint+1)], color = 'purple')
  ax1.plot(connectorX['price'], connectorY['price'], color = 'green')
  ax1.plot(connectorX['banking'], connectorY['banking'], color = 'red')
  
  ax1.set_ylabel('95% Value-at-Risk')
  ax1.set_xlabel('Average District Revenue')
  plt.tight_layout()
  plt.show()




  #timeseries_pumping = {}
  #timeseries_pumping['single'] = np.zeros(len(district_deliveries)*30)
  #timeseries_pumping['double'] = np.zeros(len(district_deliveries)*30)
  #timeseries_pumping['triple'] = np.zeros(len(district_deliveries)*30)
  #timeseries_pumping['four'] = np.zeros(len(district_deliveries)*30)
      #for year_duration in ['single', 'double', 'triple', 'four']:
        #timeseries_pumping[year_duration][(yy-y)+(y-1)*30] = annual_pumping[yy-y_adjust]
		
      #if yy - y > 0:
        #if yy - y_adjust > 0:
          #for year_duration in ['double', 'triple', 'four']:
            #timeseries_pumping[year_duration][(yy-y)+(y-1)*30] += annual_pumping[yy-y_adjust-1]
        #else:
          #for year_duration in ['double', 'triple', 'four']:
            #timeseries_pumping[year_duration][(yy-y)+(y-1)*30] += annual_pumping[yy-1]
      #if yy - y > 1:
        #if yy - y_adjust > 1:
          #for year_duration in ['triple', 'four']:
            #timeseries_pumping[year_duration][(yy-y)+(y-1)*30] += annual_pumping[yy-y_adjust-2]
        #else:
          #for year_duration in ['triple', 'four']:
            #timeseries_pumping[year_duration][(yy-y)+(y-1)*30] += annual_pumping[yy-2]
      #if yy - y > 2:
        #if yy - y_adjust > 2:
          #timeseries_pumping['four'][(yy-y)+(y-1)*30] += annual_pumping[yy-y_adjust-3]
        #else:
          #timeseries_pumping['four'][(yy-y)+(y-1)*30] += annual_pumping[yy-3]
  #fig = plt.figure()
  #ax1 = fig.add_subplot(221)
  #ax1.scatter(timeseries_pumping['single'], timeseries_revenues[x.key]['CF'], s=50, c='steelblue', edgecolor='none', alpha=0.7)
  #ax1 = fig.add_subplot(222)
  #ax1.scatter(timeseries_pumping['double'], timeseries_revenues[x.key]['CF'], s=50, c='steelblue', edgecolor='none', alpha=0.7)
  #ax1 = fig.add_subplot(223)
  #ax1.scatter(timeseries_pumping['triple'], timeseries_revenues[x.key]['CF'], s=50, c='steelblue', edgecolor='none', alpha=0.7)
  #ax1 = fig.add_subplot(224)
  #ax1.scatter(timeseries_pumping['four'], timeseries_revenues[x.key]['CF'], s=50, c='steelblue', edgecolor='none', alpha=0.7)
  ##plt.tight_layout()
  #plt.show()  
