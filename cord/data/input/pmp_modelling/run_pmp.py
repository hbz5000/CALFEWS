### Separate out the different irrigation distrcts from tlb_irrigation_districts_all.csv


def find_parameters(all_parameters, district, use_factor):
  district_index = all_parameters['Region'] == district
  district_crops = all_parameters['Crop'][district_index]
  district_values = all_parameters['Level'][district_index]
  if use_factor == 1:
    district_factors = all_parameters['Input'][district_index]
  parameter_dict = {}
  for y in all_parameters.index[district_index]:
    if use_factor == 1:
      if district_factors[y] in parameter_dict:
        parameter_dict[district_factors[y]][district_crops[y]] = district_values[y]
      else:
        parameter_dict[district_factors[y]] = {}
        parameter_dict[district_factors[y]][district_crops[y]] = district_values[y]
    else:
      parameter_dict[district_crops[y]] = district_values[y]
    

  return parameter_dict

def objective(x, crop_list, price, tau, beta, delta, gamma, sub, leontiff, factor_costs, dis):
  
  total_revenue = 0.0
  i = 0
  for crop in crop_list:
    total_factor_beta = 0.0
    for factor in leontiff:
      if x[i]*leontiff[factor][crop] > 0.0:
        if factor == 'SUPPL' or factor == 'LABOR':
          total_factor_beta += beta[factor][crop]*((leontiff[factor][crop])**((sub-1)/sub))
        else:
          total_factor_beta += beta[factor][crop]*((x[i]*leontiff[factor][crop])**((sub-1)/sub))

		
    if total_factor_beta > 0.0:
      total_factor_beta = total_factor_beta**(sub/(sub-1))
    else:
      total_factor_beta = 0.0
    total_revenue += price[crop]*tau[crop]*total_factor_beta
    if dis == 'D03':
      print(crop, end = " ")
      print(total_factor_beta, end = " ")
      print(leontiff['SUPPL'][crop], end = " ")
      print(leontiff['LABOR'][crop], end = " ")
      print(total_revenue)
    i += 1	
  land_cost = 0.0
  linear_factor_cost = 0.0
  land_index = 0
  
  i = 0
  for crop in crop_list:
    land_cost += delta[crop]*np.exp(gamma[crop]*(x[i]))
    v = 0
    for factor in leontiff:
      if factor == 'WATER':
        linear_factor_cost += factor_costs[factor][crop]*x[i]*leontiff[factor][crop]
      elif factor == 'SUPPL' or factor == 'LABOR':
        linear_factor_cost += leontiff[factor][crop]
      v += 1
    i += 1
    if dis == 'D03':
      print(crop, end = " ")
      print(land_cost, end = " ")
      print(linear_factor_cost)
    
  return land_cost + linear_factor_cost - total_revenue
 
def constrain_resource(x, resource_constraint, leontieff, num_crops, dis):
  sum_resource = 0.0
  num_factors = 4
  for i in range(0, num_crops):
    sum_resource += x[i]*leontieff[i]
    #print(x[i], end = " ")
    #print(leontieff[i], end = " ")
    #print(i)
  #if dis == 'D02':
    #print(sum_resource, end = " ")
    #print(resource_constraint)
  return resource_constraint - sum_resource



import numpy as np 
import matplotlib.colors as mplc
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import os 
import pdb
import pandas as pd
import seaborn as sns
import re
import scipy

fig = plt.figure()
ax1 = fig.add_subplot()
legend_dict = {}
acres_by_crop = {}
acres_by_crop['OBS'] = {}
acres_by_crop['CAL'] = {}
color_list = ['black', 'gray', 'firebrick', 'red', 'darksalmon', 'sandybrown', 'gold', 'chartreuse', 'seagreen', 'deepskyblue', 'royalblue', 'darkorchid', 'darkcyan', 'crimson', 'fuchsia', 'cyan', 'green', 'yellowgreen', 'coral', 'orange', 'hotpink', 'thistle', 'azure', 'yellow', 'dimgray', 'turquoise', 'navy', 'mediumspringgreen']

tau_coef = pd.read_csv('BASETAU.csv', index_col = None)
revenue_value = pd.read_csv('BASEREV.csv', index_col = None)
leontief_coef = pd.read_csv('BASELEONTIEF.csv', index_col = None)
input_value = pd.read_csv('BASEINPUTS.csv', index_col = None)
gamma_coef = pd.read_csv('BASEGAMMA.csv', index_col = None)
eta_coef = pd.read_csv('BASEETA.csv', index_col = None)
delta_coef = pd.read_csv('BASEDELTA.csv', index_col = None)
beta_coef = pd.read_csv('BASEBETA.csv', index_col = None)
water_source_fractions = pd.read_excel('Aligned_OAE_Kern_V05.xlsx', sheet_name = 'WSOU', index_col = None)
water_source_cost = pd.read_excel('Aligned_OAE_Kern_V05.xlsx', sheet_name = 'WCST', index_col = None)
crop_price = pd.read_excel('Aligned_OAE_Kern_V05.xlsx', sheet_name = 'PRICE', index_col = None)
water_source_fractions = pd.read_excel('Aligned_OAE_Kern_V05.xlsx', sheet_name = 'WSOU', index_col = None)
land_cost = pd.read_excel('Aligned_OAE_Kern_V05.xlsx', sheet_name = 'LANDCOST', index_col = None)
labor_cost = pd.read_excel('Aligned_OAE_Kern_V05.xlsx', sheet_name = 'LABOR', index_col = None)
supply_cost = pd.read_excel('Aligned_OAE_Kern_V05.xlsx', sheet_name = 'SUPPL', index_col = None)

print(tau_coef)
print(gamma_coef)
print(eta_coef)
print(delta_coef)
print(beta_coef)
print(revenue_value)
print(input_value)
print(water_source_fractions)
print(crop_price)
print(land_cost)
print(labor_cost)
print(supply_cost)

district_codes = {}
district_codes['D01'] = 'BLR'
district_codes['D02'] = 'KND'
district_codes['D03'] = 'WRM'
district_codes['D04'] = 'WKN'
district_codes['D05'] = 'BDM'
district_codes['D06'] = 'SMI'
district_codes['D07'] = 'RRB'
district_codes['D08'] = 'BVA'
district_codes['D09'] = 'CWO'
district_codes['D10'] = 'HML'
district_codes['D11'] = 'LHL'
district_codes['fk01'] = 'DLE'
district_codes['fk02'] = 'EXE'
district_codes['fk03'] = 'KRT'
district_codes['fk04'] = 'LND'
district_codes['fk05'] = 'LDS'
district_codes['fk06'] = 'LWT'
district_codes['fk07'] = 'PRT'
district_codes['fk08'] = 'SAU'
district_codes['fk09'] = 'SFW'
district_codes['fk10'] = 'SSJ'
district_codes['fk11'] = 'TPD'
district_codes['fk12'] = 'TBA'
district_codes['fk13'] = 'TLR'
district_codes['fk14'] = 'VAN'
district_codes['ot1'] = 'DLR'
district_codes['ot2'] = 'NKN'
district_codes['ot3'] = 'OLC'
gamma_values = {}
eta_values = {}
tau_values = {}
delta_values = {}
beta_values = {}
leontief_values = {}
sub = 0.17
for xx, districts in enumerate(land_cost['DISTRICT']):
  this_district = input_value['Region'] == districts
  tau_values = find_parameters(tau_coef, districts, 0)
  beta_values = find_parameters(beta_coef, districts, 1)
  delta_values = find_parameters(delta_coef, districts, 0)
  gamma_values = find_parameters(gamma_coef, districts, 0)
  leontiff_values = find_parameters(leontief_coef, districts, 1)
  baseline_inputs = find_parameters(input_value, districts, 1)
  district_prices = {}
  baseline_land = {}
  prices = list(crop_price['DISTRICT'])
  lands = list(land_cost['DISTRICT'])
  labors = list(labor_cost['DISTRICT'])
  supplies = list(supply_cost['DISTRICT'])
  fractions = list(water_source_fractions['DISTRICT'])
  costs = list(water_source_cost['DISTRICT'])
  price_index = prices.index(districts)
  land_index = lands.index(districts)
  labor_index = labors.index(districts)
  supply_index = supplies.index(districts)
  water_fractions_index = fractions.index(districts)
  water_cost_index = costs.index(districts)
  water_cost = 0.0
  land_constraint = 0.0
  water_constraint = 0.0
  for source in water_source_fractions:
    if source != 'DISTRICT':
      water_cost += water_source_fractions[source][water_fractions_index]*water_source_cost[source][water_cost_index]

  crop_list_all = list(set(input_value['Crop'][this_district]))
  crop_list = []
  i = 0
  for crop in leontiff_values['SUPPL']:
    leontiff_values['SUPPL'][crop] = supply_cost[crop][supply_index]
    leontiff_values['LABOR'][crop] = labor_cost[crop][labor_index]
  for crop in crop_list_all:
    if leontiff_values['LAND'][crop] > 0.0:
      crop_list.append(crop)
      i += 1
  if i == 0:
    for crop in crop_list_all:
      crop_list.append(crop)
  num_crops = len(crop_list)

  factor_cost = {}
  for factor in leontiff_values:
    factor_cost[factor] = {}
  leontieff_water = {}
  leontieff_land = np.zeros(len(crop_list))
  i = 0
  district_prices = {}
  for crop in crop_list:
    land_constraint += baseline_inputs['LAND'][crop]
    water_constraint += baseline_inputs['WATER'][crop]
    district_prices[crop] = crop_price[crop][price_index]
    factor_cost['LAND'][crop] = land_cost[crop][land_index]
    factor_cost['LABOR'][crop] = labor_cost[crop][labor_index]
    factor_cost['SUPPL'][crop] = supply_cost[crop][supply_index]
    if crop == 'ALFAL' or crop == 'PASTR':
      factor_cost['WATER'][crop] = 50.0
    else:
      factor_cost['WATER'][crop] = water_cost
    leontieff_land[i] = leontiff_values['LAND'][crop]
    leontieff_water[i] = leontiff_values['WATER'][crop]
    i += 1
  bnds = []
  i = 0
  x0 = np.zeros(len(crop_list))
  for crop in crop_list:
    if leontieff_land[i] > 0.0:
      bb = (0.0, land_constraint)
      #x0[i] = land_constraint/len(crop_list)
    else:
      bb = (0.0, 0.0)
    i += 1
	  
    bnds.append(bb)

  
  con1 = {'type': 'ineq', 'fun': constrain_resource, 'args' : (land_constraint, leontieff_land, num_crops, districts)}
  con2 = {'type': 'ineq', 'fun': constrain_resource, 'args' : (water_constraint, leontieff_water, num_crops, districts)}
  cons = [con1, con2]
  print(x0)
  print(crop_list)
  print(district_prices)
  minimizer_kwargs = {"method":'SLSQP',"bounds": bnds,"args": (crop_list, district_prices, tau_values, beta_values, delta_values, gamma_values, sub, leontiff_values, factor_cost, districts), "constraints":cons}
  sol = scipy.optimize.basinhopping(objective,x0,minimizer_kwargs=minimizer_kwargs)
  #sol = minimize(objective, x0, args = (crop_list, district_prices, tau_values, beta_values, delta_values, gamma_values, sub, leontiff_values, factor_cost, districts), method = 'SLSQP', bounds = bnds, constraints = cons)
  print(districts, end = " ")
  i = 0
  print(sol)
  calculated = np.zeros(len(crop_list))
  observed = np.zeros(len(crop_list))
  land_tot = 0.0
  water_tot = 0.0
  for crop in crop_list:
    if crop not in acres_by_crop['OBS']:
      acres_by_crop['OBS'][crop] = np.zeros(len(district_codes))
      acres_by_crop['CAL'][crop] = np.zeros(len(district_codes))
    acres_by_crop['OBS'][crop][xx] = baseline_inputs['LAND'][crop]
    acres_by_crop['CAL'][crop][xx] = sol.x[i]
    calculated[i] = sol.x[i]
    land_tot += sol.x[i]
    water_tot += sol.x[i]*leontieff_water[i]
    observed[i] = baseline_inputs['LAND'][crop]
    print(crop, end = " ")
    print(sol.x[i], end = " ")
    print(baseline_inputs['LAND'][crop])
    i += 1
  print(land_constraint, end = " ")
  print(water_constraint, end = " ")
  print(land_tot, end = " ")
  print(water_tot)
  legend_dict[districts] = plt.plot(calculated, observed, 'o', color = color_list[xx])
legend_obj = tuple([legend_dict[e] for e in legend_dict])
legend_names = tuple([district_codes[e] for e in legend_dict])
plt.xlabel('Calculated Acreage')
plt.ylabel('Observed Acreage')
plt.legend(legend_names)
plt.show()
plt.close()
fig = plt.figure()
ax1 = fig.add_subplot()
i = 0
for crop in crop_list_all:
  plt.plot(acres_by_crop['CAL'][crop], acres_by_crop['OBS'][crop], 'o', color = color_list[i])
  i += 1
plt.xlabel('Calculated Acreage')
plt.ylabel('Observed Acreage')
plt.legend(crop_list_all)
plt.show()
