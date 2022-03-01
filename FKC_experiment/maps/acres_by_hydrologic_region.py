import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import cm
import geopandas as gpd
import cropping_main
import matplotlib.pylab as pl
from crop import Crop


fruit_nut_veg_list = ['almond', 'apple', 'avocado', 'citrus', 'cucumber', 'deciduous_misc', 'grape', 'melon', 'nursery', 'onion', 'peach', 'pepper', 'pistachio', 'pond', 'potatoe', 'squash', 'strawberry', 'subtropical_misc', 'tomato', 'vegetable_small', 'walnut']
field_grain_feed = ['alfalfa', 'corn', 'cotton', 'field_misc', 'grain', 'pasture', 'rice', 'safflower'] 
crop_list = ['alfalfa', 'almond', 'apple', 'avocado', 'citrus', 'corn', 'cotton', 'cucumber', 'deciduous_misc', 'field_misc', 'grain', 'grape', 'grass', 'idle', 'melon', 'nursery', 'onion', 'pasture', 'peach', 'pepper', 'pistachio', 'pond', 'potatoe', 'rice', 'safflower', 'squash', 'strawberry', 'subtropical_misc', 'tomato', 'vegetable_small', 'walnut']
save_list = ['alfalfa', 'almond', 'apple', 'avocado', 'citrus', 'corn', 'cotton', 'cucumber', 'deciduous_misc', 'field_misc', 'grain', 'grape', 'grass', 'idle', 'melon', 'nursery', 'onion', 'pasture', 'peach', 'pepper', 'pistachio', 'pond', 'potatoe', 'rice', 'safflower', 'squash', 'strawberry', 'subtropical_misc', 'tomato', 'vegetable_small', 'walnut', 'WATERUSE']

hydrologic_regions = gpd.read_file('california_geo/CALFEWS_shapes/Hydrologic_Regions.shp')
water_districts = gpd.read_file('california_geo/CALFEWS_shapes/Water_Districts/Water_Districts.shp')
districts_by_region = gpd.sjoin(water_districts, hydrologic_regions, how = 'left', op = 'intersects')

year_range_pesticide = np.arange(1997,2017)
num_years = len(year_range_pesticide)
read_pesticide = False
year_range_pesticide_small = [2015,2016]
if read_pesticide:
  for xxx in year_range_pesticide_small:
    ag_shape = cropping_main.find_cropping(xxx)
    
    ag_shape_districts = gpd.sjoin(ag_shape, water_districts, how = 'inner', op = 'within')
    #ag_shape_districts = ag_shape_districts[save_list]
    ag_shape_districts_big = gpd.sjoin(ag_shape, water_districts, how = 'inner', op = 'intersects')
    #ag_shape_districts_big = ag_shape_districts_big[save_list]
    ag_shape_regions = gpd.sjoin(ag_shape, hydrologic_regions, how = 'inner', op = 'within')
    #ag_shape_regions = ag_shape_regions[save_list]
    ag_shape_regions_big = gpd.sjoin(ag_shape, hydrologic_regions, how = 'inner', op = 'intersects')
    #ag_shape_regions_big = ag_shape_regions_big[save_list]

    district_ag = ag_shape_districts.dissolve(by = 'AGENCYNAME', aggfunc = 'sum')
    district_ag_big = ag_shape_districts_big.dissolve(by = 'AGENCYNAME', aggfunc = 'sum')
    region_ag = ag_shape_regions.dissolve(by = 'HR_NAME', aggfunc = 'sum')
    region_ag_big = ag_shape_regions_big.dissolve(by = 'HR_NAME', aggfunc = 'sum')
    #district_ag.plot(ax = ax, column = 'WATERUSE', cmap = my_cmap, alpha = 0.8, legend = True)
    #plt.xlim((lx,rx))
    #plt.ylim((by,ty))
    #ax.set_xticklabels('')
    #ax.set_yticklabels('')
    #plt.show()
    #region_ag_for_export = region_ag[crop_list]
    #region_ag_df = region_ag_df[crop_list]
    for x in region_ag:
      print(x)
    print(save_list)
    region_ag = region_ag[save_list]
    region_ag_df = pd.DataFrame(region_ag.values, columns = save_list)
    region_ag_df.insert(0,'REGIONNAME', region_ag.index, True)
    region_ag_df.set_index('REGIONNAME', inplace = True)
    filename_region = 'california_geo/pesticide_acreage/acres_by_region_' + str(xxx) + '.csv'
    region_ag_df.to_csv(filename_region)

    region_ag_big = region_ag_big[save_list]
    region_ag_df_big = pd.DataFrame(region_ag_big.values, columns = save_list)
    region_ag_df_big.insert(0,'REGIONNAME', region_ag_big.index, True)
    region_ag_df_big.set_index('REGIONNAME', inplace = True)
    filename_region_big = 'california_geo/pesticide_acreage/acres_by_region_big_' + str(xxx) + '.csv'
    region_ag_df_big.to_csv(filename_region_big)


    district_ag = district_ag[save_list]
    district_ag_df = pd.DataFrame(district_ag.values, columns = save_list)
    district_ag_df.insert(0,'DISTRICTNAME', district_ag.index, True)
    district_ag_df.set_index('DISTRICTNAME', inplace = True)
    filename_district = 'california_geo/pesticide_acreage/acres_' + str(xxx) + '.csv'
    district_ag_df.to_csv(filename_district)

    district_ag_big = district_ag_big[save_list]
    district_ag_df_big = pd.DataFrame(district_ag_big.values, columns = save_list)
    district_ag_df_big.insert(0,'DISTRICTNAME', district_ag_big.index, True)
    district_ag_df_big.set_index('DISTRICTNAME', inplace = True)
    filename_district_big = 'california_geo/pesticide_acreage/acres_big_' + str(xxx) + '.csv'
    district_ag_df_big.to_csv(filename_district_big)



colors_field_grain_feed = pl.cm.autumn(np.linspace(0,1,len(field_grain_feed)))
colors_fruit_nut_veg = pl.cm.winter(np.linspace(0,1,len(fruit_nut_veg_list)))
plot_districts = False
if plot_districts:
  key_name = 'Tulare Lake'
  year_num = '2002'

  region_districts = districts_by_region[districts_by_region['HR_NAME'] == key_name]
  total_region = hydrologic_regions[hydrologic_regions['HR_NAME'] == key_name]
  filename = 'california_geo/pesticide_acreage/acres_big_' + year_num + '.csv'
  yearly_district = pd.read_csv(filename)
  yearly_district['AGENCYNAME'] = yearly_district['DISTRICTNAME']
  region_districts = region_districts.merge(yearly_district, on = 'AGENCYNAME', how = 'left')     
  fig, ax = plt.subplots()
  total_region.plot(ax = ax, alpha = 0.4, color = 'silver')
  region_districts.plot(ax = ax, column = 'WATERUSE', cmap = 'gist_heat', alpha = 0.8)
  plt.show()
  plt.close()

  for index, row in region_districts.iterrows():
    agency_name = row.AGENCYNAME
    district_acres = {}
    for crops in crop_list:
      district_acres[crops] = np.zeros(num_years)
    for year_num in year_range_pesticide:
      filename = 'california_geo/pesticide_acreage/acres_big_' + str(year_num) + '.csv'
      yearly_district = pd.read_csv(filename)
      yearly_district = yearly_district.set_index('DISTRICTNAME')
      if agency_name in yearly_district.index:
        for crops in crop_list:
          acre_value = yearly_district.loc[agency_name, crops]
          district_acres[crops][year_num - year_range_pesticide[0]] = acre_value
    print(agency_name)
    print(yearly_district.index)
    if agency_name in yearly_district.index:
      fig, ax = plt.subplots()
      baseline_acres = np.zeros(num_years)
      for crop_counter, crops in enumerate(field_grain_feed):
        plt.fill_between(year_range_pesticide, baseline_acres, baseline_acres + district_acres[crops], color = colors_field_grain_feed[crop_counter])
        baseline_acres += district_acres[crops]
      for crop_counter, crops in enumerate(fruit_nut_veg_list):
        plt.fill_between(year_range_pesticide, baseline_acres, baseline_acres + district_acres[crops], color = colors_fruit_nut_veg[crop_counter])
        baseline_acres += district_acres[crops]
      plt.legend([field_grain_feed, fruit_nut_veg_list])
      plt.title(agency_name)
      plt.show()
      plt.close()

year_list = np.arange(1997, 2017)
num_years = len(year_list)
total_acres = {}
legend_list = []
for crop in field_grain_feed:
  legend_list.append(crop)
for crop in fruit_nut_veg_list:
  legend_list.append(crop)
for x in hydrologic_regions['HR_NAME']:
  total_acres[x] = {}
  for y in fruit_nut_veg_list:
    total_acres[x][y] = np.zeros(num_years)
  for y in field_grain_feed: 
    total_acres[x][y] = np.zeros(num_years)
    
for year_num in year_list:
  filename = 'california_geo/pesticide_acreage/acres_by_region_' + str(year_num) + '.csv'
  region_acres = pd.read_csv(filename)
  region_acres = region_acres.set_index('REGIONNAME')
  for index, row in region_acres.iterrows():
    for x in field_grain_feed: 
      total_acres[index][x][year_num-year_list[0]] += row[x]/1000.0
    for x in fruit_nut_veg_list:
      total_acres[index][x][year_num-year_list[0]] += row[x]/1000.0
      
prev_reg = 'x'
large_region_list = ['Tulare Lake', 'Sacramento River', 'San Joaquin River']
mid_region_list = ['Central Coast', 'South Coast', 'Colorado River', 'North Coast']
small_region_list = ['South Lahontan', 'San Francisco Bay', 'North Lahontan']

nrows = 2
ncols = 2
fig, ax = plt.subplots(nrows,ncols)
reg_counter = 0
reg_counter2 = 0

for x in large_region_list:
  baseline_acres = np.zeros(num_years)
  for crop_counter, crop in enumerate(field_grain_feed):
    ax[reg_counter][reg_counter2].fill_between(np.arange(1997, 2017),baseline_acres, baseline_acres + total_acres[x][crop], color = colors_field_grain_feed[crop_counter])
    baseline_acres += total_acres[x][crop]
      
  for crop_counter, crop in enumerate(fruit_nut_veg_list):
    ax[reg_counter][reg_counter2].fill_between(np.arange(1997, 2017),baseline_acres, baseline_acres + total_acres[x][crop], color = colors_fruit_nut_veg[crop_counter])
    baseline_acres += total_acres[x][crop]
      
  if reg_counter == nrows - 1:
    ax[reg_counter][reg_counter2].set_xticks(np.arange(1997, 2017, 2))
    ax[reg_counter][reg_counter2].set_xticklabels(np.arange(1997, 2017, 2))
  else:
    ax[reg_counter][reg_counter2].set_xticklabels('')

  if reg_counter2 == 0:
    ax[reg_counter][reg_counter2].set_ylabel('Total Irrigated Area (thousand acres)')
  ax[reg_counter][reg_counter2].set_title(x)
  ax[reg_counter][reg_counter2].set_xlim((1997, 2016))
  ax[reg_counter][reg_counter2].set_ylim([0.0, 3000.0])
  reg_counter += 1
  if reg_counter == nrows:
    reg_counter = 0
    reg_counter2 += 1
for crop_counter, crop in enumerate(field_grain_feed):
  ax[nrows - 1][ncols -1].fill_between([0.0, 0.0],[0.0, 0.0], [0.0, 0.0], color = colors_field_grain_feed[crop_counter])
for crop_counter, crop in enumerate(fruit_nut_veg_list):
  ax[nrows - 1][ncols -1].fill_between([0.0, 0.0],[0.0, 0.0], [0.0, 0.0], color = colors_fruit_nut_veg[crop_counter])
ax[nrows - 1][ncols -1].legend(legend_list, ncol = 4)
ax[nrows - 1][ncols -1].set_xticklabels('')
ax[nrows - 1][ncols -1].set_yticklabels('')
ax[nrows - 1][ncols -1].axis('off')
plt.show()
plt.close()

nrows = 2
ncols = 2
fig, ax = plt.subplots(nrows,ncols)
reg_counter = 0
reg_counter2 = 0

for x in mid_region_list:
  baseline_acres = np.zeros(num_years)
  for crop_counter, crop in enumerate(field_grain_feed):
    ax[reg_counter][reg_counter2].fill_between(np.arange(1997, 2017),baseline_acres, baseline_acres + total_acres[x][crop], color = colors_field_grain_feed[crop_counter])
    baseline_acres += total_acres[x][crop]
      
  for crop_counter, crop in enumerate(fruit_nut_veg_list):
    ax[reg_counter][reg_counter2].fill_between(np.arange(1997, 2017),baseline_acres, baseline_acres + total_acres[x][crop], color = colors_fruit_nut_veg[crop_counter])
    baseline_acres += total_acres[x][crop]
      
  if reg_counter == nrows - 1:
    ax[reg_counter][reg_counter2].set_xticks(np.arange(1997, 2017, 2))
    ax[reg_counter][reg_counter2].set_xticklabels(np.arange(1997, 2017, 2))
  else:
    ax[reg_counter][reg_counter2].set_xticklabels('')
  if reg_counter2 == 0:
    ax[reg_counter][reg_counter2].set_ylabel('Total Irrigated Area (thousand acres)')
  ax[reg_counter][reg_counter2].set_title(x)
  ax[reg_counter][reg_counter2].set_xlim((1997, 2016))
  ax[reg_counter][reg_counter2].set_ylim([0.0, 650.0])
  reg_counter += 1
  if reg_counter == nrows:
    reg_counter = 0
    reg_counter2 += 1
ax[nrows - 1][ncols -1].legend(legend_list, ncol = 4)
plt.show()
plt.close()


nrows = 2
ncols = 2
fig, ax = plt.subplots(nrows,ncols)
reg_counter = 0
reg_counter2 = 0

for x in small_region_list:
  baseline_acres = np.zeros(num_years)
  for crop_counter, crop in enumerate(field_grain_feed):
    ax[reg_counter][reg_counter2].fill_between(np.arange(1997, 2017),baseline_acres, baseline_acres + total_acres[x][crop], color = colors_field_grain_feed[crop_counter])
    baseline_acres += total_acres[x][crop]
      
  for crop_counter, crop in enumerate(fruit_nut_veg_list):
    ax[reg_counter][reg_counter2].fill_between(np.arange(1997, 2017),baseline_acres, baseline_acres + total_acres[x][crop], color = colors_fruit_nut_veg[crop_counter])
    baseline_acres += total_acres[x][crop]
      
  if reg_counter == nrows - 1:
    ax[reg_counter][reg_counter2].set_xticks(np.arange(1997, 2017, 2))
    ax[reg_counter][reg_counter2].set_xticklabels(np.arange(1997, 2017, 2))
  else:
    ax[reg_counter][reg_counter2].set_xticklabels('')
  if reg_counter2 == 0:
    ax[reg_counter][reg_counter2].set_ylabel('Total Irrigated Area (thousand acres)')
  ax[reg_counter][reg_counter2].set_title(x)
  ax[reg_counter][reg_counter2].set_xlim((1997, 2016))
  ax[reg_counter][reg_counter2].set_ylim([0.0, 125.0])
  reg_counter += 1
  if reg_counter == nrows:
    reg_counter = 0
    reg_counter2 += 1
for crop_counter, crop in enumerate(field_grain_feed):
  ax[nrows - 1][ncols -1].fill_between([0.0, 0.0],[0.0, 0.0], [0.0, 0.0], color = colors_field_grain_feed[crop_counter])
for crop_counter, crop in enumerate(fruit_nut_veg_list):
  ax[nrows - 1][ncols -1].fill_between([0.0, 0.0],[0.0, 0.0], [0.0, 0.0], color = colors_fruit_nut_veg[crop_counter])
ax[nrows - 1][ncols -1].legend(legend_list, ncol = 4)
ax[nrows - 1][ncols -1].set_xticklabels('')
ax[nrows - 1][ncols -1].set_yticklabels('')
ax[nrows - 1][ncols -1].axis('off')
plt.show()
plt.close()



###Read PPIC Data
start_year = 1997
transferFile = pd.ExcelFile('california_geo/water transfer tables.xlsx')
transferTable = transferFile.parse('tech_app_b3a', header = 3)
transferValues = transferTable['Municipal and Industrial']
transferYears = transferTable['Year'] >= start_year

bankingFile = pd.ExcelFile('california_geo/gw banking numbers.xlsx')
bankingTableKern = bankingFile.parse('table c2', header = 1)
bankingValuesKern = bankingTableKern['ag']
bankingYearsKern = bankingTableKern['Year'] >= start_year

bankingTableMet = bankingFile.parse('table c3', header = 1)
bankingValuesMet = bankingTableMet['Total Banking Balances in Southern California']
bankingYearsMet = bankingTableMet['Year'] >= start_year

transfer_read = transferValues[transferYears]
banking_kern = bankingValuesKern[bankingYearsKern]
banking_met = bankingValuesMet[bankingYearsMet]
kern_ag_bank = np.zeros(num_years)
long_termTransfers = np.zeros(num_years)
transfer_read.reset_index(drop = True, inplace = True)
banking_kern.reset_index(drop = True, inplace = True)
banking_met.reset_index(drop = True, inplace = True)
for x in range(0, num_years):
  kern_ag_bank[x] = max(banking_kern[x] - banking_kern[x+1], 0.0)/1000.0 + max(banking_met[x] - banking_met[x+1], 0.0)/1000.0
  long_termTransfers[x] = transfer_read[x]/1000000.0

crop_keys, crop_key_list, irrdemand = cropping_main.find_crop_keys()
for x in crop_key_list:
  irrdemand[x] = irrdemand[x]/1000.0
total_low_water = {}
total_low_water_start = {}
change_low_water = {}
change_high_water = {}
ag_ag_transfers = {}
region_list = []
start_year = 5
region_list = ['Tulare Lake', 'Sacramento River', 'San Joaquin River', 'Colorado River', 'North Coast', 'Central Coast', 'South Coast', 'San Francisco Bay', 'North Lahontan', 'South Lahontan']

total_low_water = np.zeros(len(region_list))
total_low_water_start = np.zeros(len(region_list))
total_overdraft = np.zeros(len(region_list))
for x in region_list:
  change_low_water[x] = np.zeros(num_years)
  change_high_water[x] = np.zeros(num_years)
  ag_ag_transfers[x] = np.zeros(num_years)
width = 0.25
pos = list(range((len(region_list))))
colors_districts = pl.cm.autumn(np.linspace(0,1,3))
for region_counter, region_type in enumerate(region_list):
  for crop_type in field_grain_feed:
    total_low_water[region_counter] += irrdemand[crop_type]*total_acres[region_type][crop_type][num_years-1]/12.0
    total_low_water_start[region_counter] += irrdemand[crop_type]*total_acres[region_type][crop_type][start_year]/12.0
    for year_num in range(num_years):
      change_low_water[region_type][year_num] += (irrdemand[crop_type]*total_acres[region_type][crop_type][0] - irrdemand[crop_type]*total_acres[region_type][crop_type][year_num])/12.0
  for crop_type in fruit_nut_veg_list:  
    for year_num in range(num_years):
      change_high_water[region_type][year_num] += (irrdemand[crop_type]*total_acres[region_type][crop_type][year_num] - irrdemand[crop_type]*total_acres[region_type][crop_type][0])/12.0
  for year_num in range(num_years):
    ag_ag_transfers[region_type][year_num] = max(min(change_low_water[region_type][year_num], change_high_water[region_type][year_num]), 0.0)
  if region_type == 'Tulare Lake':
    total_overdraft[region_counter] = 1.73
  elif region_type == 'San Joaquin River':
    total_overdraft[region_counter] = 0.115

fig, ax = plt.subplots()
plt.bar([p + width*0 for p in pos], total_low_water_start, width, alpha=0.8, color=colors_districts[0], edgecolor = 'black', label='Field, Grain, Feed, 2002')     
plt.bar([p + width*1 for p in pos], total_low_water, width, alpha=0.8, color=colors_districts[1], edgecolor = 'black', label='Field, Grain, Feed, 2016') 
plt.bar([p + width*2 for p in pos], total_overdraft, width, alpha=0.8, color=colors_districts[2], edgecolor = 'black', label='Annual Average Overdraft, 1973-2016') 
plt.legend()
ax.set_xticks(pos)
ax.set_ylabel('Total Annual Water Requirements (MAF)')
ax.set_xticklabels(region_list)
  
plt.show()

colors_transfer = pl.cm.gist_rainbow(np.linspace(0,1,len(region_list)))
legend_list_transfers = []
legend_list_transfers.append('Urban-Ag Transfers, Statewide')
for x in region_list:
  legend_list_transfers.append('Ag-Ag Transfers, ' + x)
fig, ax = plt.subplots()
plt.fill_between(np.arange(1997, 2017),np.zeros(num_years), long_termTransfers, color = 'black')
baseline_values = long_termTransfers * 1.0
for region_count, x in enumerate(region_list):
  plt.fill_between(np.arange(1997, 2017),baseline_values, baseline_values + ag_ag_transfers[x], color = colors_transfer[region_count])
  baseline_values += ag_ag_transfers[x]
  print(baseline_values)
plt.legend(legend_list_transfers, loc = 'upper left')
ax.set_xlim((1997, 2016))
ax.set_ylabel('Total Transfers, MAF')
ax.set_xticks(np.arange(1997,2017))
ax.set_xticklabels(np.arange(1997, 2017))
plt.show()
  