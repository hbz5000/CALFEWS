import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import os

def make_district_data_shapefiles(original_filename):
  all_districts = gpd.read_file(original_filename)
  sellers_key = pd.read_csv(os.path.join('CALFEWS_Shapes', 'sellers_key.csv'))
  buyers_key = pd.read_csv(os.path.join('CALFEWS_Shapes', 'buyers_key.csv'))
  seller_data = pd.read_csv(os.path.join('CALFEWS_Shapes', 'transfers_by_seller.csv'))
  buyer_data = pd.read_csv(os.path.join('CALFEWS_Shapes', 'transfers_by_buyer.csv'))
  shapefile_data = pd.DataFrame()
  column_list = ['AGENCYNAME', 'geometry']
  for year in range(2010, 2021):
    column_list.append('NetTra' + str(year))
  for index, row in buyers_key.iterrows():
    this_shape = all_districts[all_districts['AGENCYNAME'] == row['Shapefile Name']]  
    this_shape_transaction = buyer_data[buyer_data['Buyer'] == row['Transfer Name']]
    shapefile_data.at[row['Shapefile Name'], 'AGENCYNAME'] = row['Shapefile Name']
    shapefile_data.at[row['Shapefile Name'], 'geometry'] = this_shape.loc[this_shape.index[0], 'geometry']    
    for year in range(2010, 2021):
      net_transfers = this_shape_transaction[this_shape_transaction['Year'] == year]
      shapefile_data.at[row['Shapefile Name'], 'NetTra'+str(year)] = np.sum(net_transfers['Delivered'])
  for index, row in sellers_key.iterrows():
    this_shape = all_districts[all_districts['AGENCYNAME'] == row['Shapefile Name']]  
    this_shape_transaction = seller_data[seller_data['Seller'] == row['Transfer Name']]
    if row['Shapefile Name'] not in shapefile_data.index:
      shapefile_data.at[row['Shapefile Name'], 'AGENCYNAME'] = row['Shapefile Name']
      shapefile_data.at[row['Shapefile Name'], 'geometry'] = this_shape.loc[this_shape.index[0], 'geometry']    
      for year in range(2010, 2021):
        net_transfers = this_shape_transaction[this_shape_transaction['Year'] == year]
        if len(net_transfers.index) > 0:
          shapefile_data.at[row['Shapefile Name'], 'NetTra'+str(year)] = (-1.0) * np.sum(net_transfers['Volume'])
        else:
          shapefile_data.at[row['Shapefile Name'], 'NetTra'+str(year)] = 0.0
    else:
      for year in range(2010, 2021):
        net_transfers = this_shape_transaction[this_shape_transaction['Year'] == year]
        if len(net_transfers.index) > 0:
          shapefile_data.at[row['Shapefile Name'], 'NetTra'+str(year)] -= np.sum(net_transfers['Volume']) - np.sum(net_transfers['Additional Loss'])
  
  shapefile_gdf = gpd.GeoDataFrame(shapefile_data, crs = all_districts.crs, geometry = shapefile_data['geometry'])
  return shapefile_gdf  
def make_point_shapes(point_filename):
  points = pd.read_csv(point_filename)
  points_gdf = pd.DataFrame()
  x_loc = 'LONG'
  y_loc = 'LAT'
  crs = {'init': 'epsg:4326'}
  for index, row in points.iterrows():
    points_gdf = pd.concat([points_gdf, points[points.NAME == row.NAME]], axis = 0)
  if x_loc in points_gdf and y_loc in points_gdf:
    geometry = [Point(xy) for xy in zip(points_gdf[x_loc], points_gdf[y_loc])]
    new_geo_df = gpd.GeoDataFrame(points_gdf, crs = crs, geometry = geometry)
    
  return new_geo_df

def create_shape_lists(map_type, use_type):
  #enables multiple figure types to be generated from maps_main.py script
  #calfews_attributes - list of shapefile names, point locations, and colors to plot
  #box_coordinates - coordinate frame to plot  

  #map_type: total = full state, subgroup options:
  #############################contracts: districts grouped by contract types
  #############################land_use: districts grouped by water use (i.e., urban, ag, recharge)
  #############################exchange_example: select districts that illustrate a potential 'paper' exchange
  #############################wetlands: show wetlands/migratory bird areas
  #############################crop_groups: crop types on a 1km x 1km grid (no shapefiles used)
  #############################groundwater: SAGBI index (no shapefiles used)

  #map_type: statewide = full state (no SoCal), subgroup options:
  #############################paper: full figure shown in CALFEWS intro paper
  #############################projects1 - projects10: various combinations of districts/infrastructure w/different stuff highlighted

  #map_type: cv = central valley only
  #map_type: northerncv = central valley excluding Tulare Basin
  #map_type: southerncv = central valley excluding Sacramento
  #map_type: sacramento = only sacramento valley
  #map_type: sanjoaquin = only san joaquin valley
  #map_type: tulare = only Tulare Basin

  #set attributes - 'shapefiles' = shapefile names, 'shapefile_color' = colors of shapefiles, 'csvfiles' = point location names
  #colors for point locations (listed in 'csvfiles') set in function create_reservoir_file()
  calfews_attributes = {}  
  if map_type == 'total':
    if use_type == 'contracts':
      calfews_attributes['shapefiles'] = ['drawings-line', 'Canals_and_Aqueducts_local/canals_abbr', 'Canals_and_Aqueducts_local/kern_cal_aq', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Yuba_River-line', 'Delta-line', 'Tulare_Basin-line', 'kings_ext', 'Water_Districts/sacramento_districts', 'Water_Districts/feather_districts', 'Water_Districts/yuba_districts', 'Water_Districts/folsom_districts', 'Water_Districts/eastside_districts', 'Water_Districts/cvp_south_districts', 'Water_Districts/friant_districts', 'Water_Districts/tulare_districts', 'Water_Districts/swp_districts']
      district_colors = ['beige', 'khaki', 'gold', 'darkgoldenrod', 'sienna', 'firebrick', 'indianred', 'lightcoral', 'mistyrose']
      calfews_attributes['shapefile_color'] = ['black', 'black', 'black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue']
      for x in range(0, len(district_colors)):
        calfews_attributes['shapefile_color'].append(district_colors[x])

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                   Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                   Line2D([0], [0], color='black', lw=2, label='Canal'),
                   Patch(facecolor=district_colors[0], edgecolor=district_colors[0], label='Sacramento River Districts'),
                   Patch(facecolor=district_colors[1], edgecolor=district_colors[1], label='Feather River Districts'),
                   Patch(facecolor=district_colors[2], edgecolor=district_colors[2], label='Yuba River Districts'),
                   Patch(facecolor=district_colors[3], edgecolor=district_colors[3], label='American River Districts'),
                   Patch(facecolor=district_colors[4], edgecolor=district_colors[4], label='Eastside Districts'),
                   Patch(facecolor=district_colors[5], edgecolor=district_colors[5], label='CVP SOD Districts'),
                   Patch(facecolor=district_colors[6], edgecolor=district_colors[6], label='Friant-Kern Districts'),
                   Patch(facecolor=district_colors[7], edgecolor=district_colors[7], label='Tulare Basin Districts'),
                   Patch(facecolor=district_colors[8], edgecolor=district_colors[8], label='SWP Districts')]

    elif use_type == 'land_use':
      calfews_attributes['shapefiles'] = ['drawings-line', 'Canals_and_Aqueducts_local/canals_abbr',  'Canals_and_Aqueducts_local/kern_cal_aq', 'Canals_and_Aqueducts_local/so_cal_aqueduct-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Yuba_River-line', 'Delta-line', 'Tulare_Basin-line', 'kings_ext', 'creek_add_ons-line', 'Water_Districts/agricultural_districts', 'Water_Districts/urban_districts', 'Water_Districts/recharge_districts', 'kern_water_bank']
      district_colors = ['indianred', 'silver']
      calfews_attributes['shapefile_color'] = ['black', 'black', 'black', 'black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'goldenrod', 'teal', 'darkorchid']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface Reservoir', markerfacecolor='bisque', markersize=5, linewidth = 0),
                   Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                   Line2D([0], [0], color='black', lw=2, label='Canal'),
                   Patch(facecolor='indianred', edgecolor='black', label='Agricultural\nDistricts'),
                   Patch(facecolor='goldenrod', edgecolor='black', label='Urban Districts'), 
                   Patch(facecolor='teal', edgecolor='black', label='Districts with\nRecharge Facilities'), 
                   Patch(facecolor='darkorchid', edgecolor='black', label='Dedicated\nGroundwater Banks')]

    elif use_type == 'exchange_example':
      calfews_attributes['shapefiles'] = ['drawings-line',  'Canals_and_Aqueducts_local/kern_cal_aq', 'Canals_and_Aqueducts_local/so_cal_aqueduct-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Yuba_River-line', 'Delta-line', 'Water_Districts/exchange_example_ag_districts', 'Water_Districts/exchange_example_urban_districts']
      district_colors = ['indianred', 'silver']
      calfews_attributes['shapefile_color'] = ['black', 'black', 'black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'goldenrod']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface Reservoir', markerfacecolor='bisque', markersize=5, linewidth = 0),
                   Line2D([0], [0], marker='o', color='black', label='Fish Spawning/Migration Site', markerfacecolor='midnightblue', markersize=5, linewidth = 0),
                   Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                   Line2D([0], [0], color='black', lw=2, label='Canal'),
                   Patch(facecolor='indianred', edgecolor='black', label='Agricultural Recharge Sites'),
                   Patch(facecolor='goldenrod', edgecolor='black', label='Urban Exchange Partners')]

    elif use_type == 'wetlands':
      calfews_attributes['shapefiles'] = ['wetlands/wetlands/i02_NCCAG_Vegetation', 'wetlands/wetlands/i02_NCCAG_Wetlands', 'shorebird_priority_habitat/priority_only']
      district_colors = ['indianred', 'silver']
      calfews_attributes['shapefile_color'] = ['lime', 'lime', 'teal']

      legend_elements = [Patch(facecolor='lime', edgecolor='black', label='Wetlands'), Patch(facecolor='teal', edgecolor='black', label='Shorebird Habitat')]

    elif use_type == 'crop_groups':
      calfews_attributes['shapefiles'] = []
      district_colors = ['indianred', 'silver']
      calfews_attributes['shapefile_color'] = ['yellow', 'darkgreen', 'darkorchid', 'coral']

      legend_elements = [Patch(facecolor=calfews_attributes['shapefile_color'][0], edgecolor='black', label='Forage/Staple Crops'),
                   Patch(facecolor=calfews_attributes['shapefile_color'][1], edgecolor='black', label='Other Annual Crops'),
                   Patch(facecolor=calfews_attributes['shapefile_color'][2], edgecolor='black', label='Grapes'),
                   Patch(facecolor=calfews_attributes['shapefile_color'][3], edgecolor='black', label='Orchards')]

    elif use_type == 'groundwater':
      calfews_attributes['shapefiles'] = []
      district_colors = ['indianred', 'silver']
      calfews_attributes['shapefile_color'] = []

      legend_elements = [Patch(facecolor='steelblue', edgecolor='black', label='Excellent SAGBI Rating'),
                   Patch(facecolor='lightskyblue', edgecolor='black', label='Good SAGBI Rating'),
                   Patch(facecolor='lightgoldenrodyellow', edgecolor='black', label='Moderate SAGBI Rating'),
                   Patch(facecolor='salmon', edgecolor='black', label='Poor SAGBI Rating'),
                   Patch(facecolor='firebrick', edgecolor='black', label='Very Poor SAGBI Rating')]
    
    if use_type == 'wetlands' or use_type == 'crop_groups' or use_type == 'groundwater':
      calfews_attributes['csvfiles'] = ['OUT OF BOX']
      box_coordinates = [-122.7, -118.0, 34.85, 41.0]
    elif use_type == 'exchange_example':
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT','SAN JOAQUIN RIVER', 'FISH']
      box_coordinates = [-123.0, -116, 32.25, 38.0]
    else:
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'MERCED RIVER', 'NORTH YUBA RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'TULE RIVER', 'MOKELUMNE RIVER', 'CALAVERAS RIVER', 'TUOLUMNE RIVER 2', 'CACHE CREEK', 'PUTAH CREEK']
      box_coordinates = [-123.0, -116, 32.75, 41.0]
  
  elif map_type == 'statewide':
    box_coordinates = [-122.7, -118.0, 34.85, 41.0]
    if use_type == 'blank':
      calfews_attributes['shapefiles'] = []
      calfews_attributes['shapefile_color'] = []
      calfews_attributes['csvfiles'] = []

      legend_elements = []
    if use_type == 'paper':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Yuba_River-line', 'Delta-line', 'Tulare_Basin-line', 'kings_ext', 'districts-no-banks', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'teal', 'teal', 'teal', 'steelblue']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'MERCED RIVER', 'NORTH YUBA RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'DELTA', 'FEATHER', 'MERCED', 'NORTH YUBA', 'SACRAMENTO', 'STANISLAUS', 'TUOLUMNE', 'SACDELTA', 'SJDELTA', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'TULE RIVER', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                   Line2D([0], [0], marker='o', color='black', label='Downstream Gauge', markerfacecolor='midnightblue', markersize=5, linewidth = 0),
                   Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                   Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                   Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                   Line2D([0], [0], color='black', lw=2, label='Canal'),
                   Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'),
                   Patch(facecolor='teal', edgecolor='teal', label='In-lieu GW Bank'),
                   Patch(facecolor='steelblue', edgecolor='steelblue', label='Direct GW Bank')]

    elif use_type == 'projects1':
      calfews_attributes['shapefiles'] = ['arvin_bank',]
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'teal', 'teal', 'teal', 'steelblue']
      calfews_attributes['csvfiles'] = ['KERN RIVER']
  
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='S', markerfacecolor='bisque', markersize=5, linewidth = 0),
                   Line2D([0], [0], color='midnightblue', lw=2, label='N')]

    elif use_type == 'projects2':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line', 'districts-no-banks', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'indianred', 'indianred', 'indianred', 'indianred']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'DELTA', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'),
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District')]

    elif use_type == 'projects3':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line', 'districts-no-banks_v2', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'kern_delta', 'westlands']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'teal', 'teal', 'teal', 'teal','teal', 'indianred']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'DELTA', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']
      
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'),
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'), Patch(facecolor='teal', edgecolor='teal', label='Groundwater Banks')]

    elif use_type == 'projects4':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line','Yuba_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line','Tulare_Basin-line', 'kings_ext', 'districts-no-banks_v2', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'kern_delta', 'westlands']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'teal', 'teal', 'teal', 'teal','teal', 'indianred']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER','NORTH YUBA RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'TULE RIVER', 'DELTA', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'),
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'), Patch(facecolor='teal', edgecolor='teal', label='Groundwater Banks')]

    elif use_type == 'projects5':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line','Yuba_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line','Tulare_Basin-line', 'kings_ext', 'districts-no-banks_v2', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'kern_delta', 'westlands']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'indianred', 'teal', 'indianred', 'indianred','indianred', 'indianred']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER','NORTH YUBA RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'TULE RIVER', 'DELTA', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'),
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'), Patch(facecolor='teal', edgecolor='teal', label='Groundwater Banks')]

    elif use_type == 'projects6':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line', 'districts-no-banks_v2', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'kern_delta', 'westlands']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'indianred', 'indianred', 'indianred', 'indianred','indianred', 'teal']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'DELTA', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'),
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District')]

    elif use_type == 'projects7':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line','Yuba_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER','NORTH YUBA RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER', 'DELTA', 'FEATHER', 'MERCED', 'NORTH YUBA', 'SACRAMENTO', 'STANISLAUS', 'TUOLUMNE', 'SACDELTA', 'SJDELTA']
      
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface Reservoir', markerfacecolor='bisque', markersize=5, linewidth = 0),Line2D([0], [0], marker='o', color='black', label='Downstream Gauge', markerfacecolor='midnightblue', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal')]

    elif use_type == 'projects8':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line','Yuba_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line','Tulare_Basin-line', 'kings_ext', 'districts-no-banks_v2', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'kern_delta', 'westlands']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'indianred', 'indianred', 'indianred', 'indianred','indianred', 'indianred']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER','NORTH YUBA RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER', 'DELTA', 'FEATHER', 'MERCED', 'NORTH YUBA', 'SACRAMENTO', 'STANISLAUS', 'TUOLUMNE', 'SACDELTA', 'SJDELTA', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'TULE RIVER', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']
      
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface Reservoir', markerfacecolor='bisque', markersize=5, linewidth = 0),Line2D([0], [0], marker='o', color='black', label='Downstream Gauge', markerfacecolor='midnightblue', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'), 
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District')]

    elif use_type == 'projects9':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line','Yuba_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line','Tulare_Basin-line', 'kings_ext', 'districts-no-banks_v2', 'Water_Districts/recharge_districts', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'kern_delta', 'westlands']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'teal', 'steelblue', 'steelblue', 'steelblue','steelblue', 'steelblue', 'indianred']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER','NORTH YUBA RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER', 'DELTA', 'FEATHER', 'MERCED', 'NORTH YUBA', 'SACRAMENTO', 'STANISLAUS', 'TUOLUMNE', 'SACDELTA', 'SJDELTA', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'TULE RIVER', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface Reservoir', markerfacecolor='bisque', markersize=5, linewidth = 0),Line2D([0], [0], marker='o', color='black', label='Downstream Gauge', markerfacecolor='midnightblue', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'), 
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'), Patch(facecolor='teal', edgecolor='teal', label='Recharge Basins'), Patch(facecolor='steelblue', edgecolor='steelblue', label='Groundwater Banks')]

    elif use_type == 'projects10':
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line','Yuba_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Delta-line','Tulare_Basin-line', 'kings_ext', 'districts-no-banks_v2', 'Water_Districts/recharge_districts', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'kern_delta', 'westlands']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'indianred', 'indianred', 'indianred', 'indianred','indianred', 'indianred', 'teal']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'SACRAMENTO RIVER','NORTH YUBA RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER', 'DELTA', 'FEATHER', 'MERCED', 'NORTH YUBA', 'SACRAMENTO', 'STANISLAUS', 'TUOLUMNE', 'SACDELTA', 'SJDELTA', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'TULE RIVER', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']
      
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface Reservoir', markerfacecolor='bisque', markersize=5, linewidth = 0),Line2D([0], [0], marker='o', color='black', label='Downstream Gauge', markerfacecolor='midnightblue', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5, linewidth = 0),
                       Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5, linewidth = 0),
                       Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                       Line2D([0], [0], color='black', lw=2, label='Canal'), 
                       Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District')]

  elif map_type == 'cv':
    calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line', 'Tulare_Basin-line', 'Yuba_River-line',  'Delta-line', 'districts-polygon']
    calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred']
    calfews_attributes['csvfiles'] = ['AMERICAN RIVER', 'CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'MERCED RIVER', 'NORTH YUBA RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TULE RIVER', 'TUOLUMNE RIVER']
    box_coordinates = [-123.0, -118.0, 34.5, 41.0]

    legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5),
                   Line2D([0], [0], marker='o', color='black', label='$\it{Downstream}$ $\it{Gauge}$', markerfacecolor='midnightblue', markersize=5),
                   Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5),
                   Patch(facecolor='steelblue', edgecolor='steelblue', alpha = 0.6, label='Sacramento Controlled Flows'),
                   Patch(facecolor='teal', edgecolor='teal', alpha = 0.6, label='Sacramento Uncontrolled Flows'),
                   Patch(facecolor='forestgreen', edgecolor='forestgreen', alpha = 0.6, label='Delta Uncontrolled Flows'),
                   Patch(facecolor='coral', edgecolor='coral', alpha = 0.6, label='San Joaquin Controlled Flows'),
                   Patch(facecolor='indianred', edgecolor='indianred', alpha = 0.6, label='San Joaquin Uncontrolled Flows'),
                   Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                   Line2D([0], [0], color='black', lw=2, label='Canal')]


  elif map_type == 'northerncv':
    box_coordinates = [-122.7, -119.8, 37.2, 41.0]


    if use_type == 'YCWA':
      calfews_attributes['shapefiles'] = ['drawings-line', 'Canals_and_Aqueducts_local/canals_abbr', 'Canals_and_Aqueducts_local/kern_cal_aq', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Yuba_River-line', 'Delta-line', 'Tulare_Basin-line', 'kings_ext', 'Water_Districts/sacramento_districts', 'Water_Districts/feather_districts', 'Water_Districts/yuba_districts']
      district_colors = ['beige', 'khaki', 'gold', 'darkgoldenrod', 'sienna', 'firebrick', 'indianred', 'lightcoral', 'mistyrose']
      calfews_attributes['shapefile_color'] = ['black', 'black', 'black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'teal', 'teal', 'teal']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'MERCED RIVER', 'NORTH YUBA RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'DELTA', 'FEATHER', 'MERCED', 'NORTH YUBA', 'SACRAMENTO', 'STANISLAUS', 'TUOLUMNE', 'SACDELTA', 'SJDELTA']

      for x in range(0, len(district_colors)):
        calfews_attributes['shapefile_color'].append(district_colors[x])

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5, linewidth = 0),
                   Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                   Line2D([0], [0], color='black', lw=2, label='Canal'),
                   Patch(facecolor=district_colors[0], edgecolor=district_colors[0], label='Districts'),
                   Patch(facecolor='steelblue', edgecolor='black', label='Excellent SAGBI Rating'),
                   Patch(facecolor='lightskyblue', edgecolor='black', label='Good SAGBI Rating'),
                   Patch(facecolor='lightgoldenrodyellow', edgecolor='black', label='Moderate SAGBI Rating'),
                   Patch(facecolor='salmon', edgecolor='black', label='Poor SAGBI Rating'),
                   Patch(facecolor='firebrick', edgecolor='black', label='Very Poor SAGBI Rating')]
    else:
      calfews_attributes['shapefiles'] = ['drawings-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Yuba_River-line', 'Delta-line']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue']
      calfews_attributes['csvfiles'] = ['AMERICAN RIVER','CALIFORNIA AQUEDUCT', 'FEATHER RIVER', 'MERCED RIVER', 'NORTH YUBA RIVER', 'SACRAMENTO RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER', 'DELTA', 'FEATHER', 'MERCED', 'NORTH YUBA', 'SACRAMENTO', 'STANISLAUS', 'TUOLUMNE', 'SACDELTA', 'SJDELTA']
    
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5),
                     Line2D([0], [0], marker='o', color='black', label='$\it{Downstream}$ $\it{Gauge}$', markerfacecolor='midnightblue', markersize=5),
                     Line2D([0], [0], marker='o', color='black', label= 'Delta Pumps', markerfacecolor='black', markersize=5),
                     Patch(facecolor='steelblue', edgecolor='steelblue', alpha = 0.6, label='Sacramento Controlled Flows'),
                     Patch(facecolor='teal', edgecolor='teal', alpha = 0.6, label='Sacramento Uncontrolled Flows'),
                     Patch(facecolor='forestgreen', edgecolor='forestgreen', alpha = 0.6, label='Delta Uncontrolled Flows'),
                     Patch(facecolor='coral', edgecolor='coral', alpha = 0.6, label='San Joaquin Controlled Flows'),
                     Patch(facecolor='indianred', edgecolor='indianred', alpha = 0.6, label='San Joaquin Uncontrolled Flows'),
                     Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                     Line2D([0], [0], color='black', lw=2, label='Canal')]

  elif map_type == 'climate change':
    box_coordinates = [-121.8, -118.0, 34.85, 37.95]#data_figure.format_plot
    if use_type[:len('district_highlight')] == 'district_highlight':
      calfews_attributes['shapefiles'] = ['drawings-line',]
      calfews_attributes['shapefile_color'] = ['black',]
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT',]
    elif use_type == 'blank':
      calfews_attributes['shapefiles'] = []
      calfews_attributes['shapefile_color'] = []
      calfews_attributes['csvfiles'] = []    
    else:
      calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', ]
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue',]
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'SAN JOAQUIN RIVER', 'TULE RIVER']
    legend_elements = 'None'
    if use_type == 'contracts1':
      calfews_attributes['shapefiles'] = ['drawings-line',]
      calfews_attributes['shapefile_color'] = ['black',]
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT',]
      legend_elements = [Patch(facecolor='indianred', edgecolor='crimson', alpha = 0.6, label='CVP - South of Delta')]
    if use_type == 'contracts2':
      calfews_attributes['shapefiles'] = ['drawings-line',]
      calfews_attributes['shapefile_color'] = ['black',]
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT',]
      legend_elements = [Patch(facecolor='indianred', edgecolor='black', alpha = 0.6, label='CVP - South of Delta'),
                         Patch(facecolor='goldenrod', edgecolor='crimson', alpha = 0.6, label='State Water Project')]
    if use_type == 'contracts3':
      calfews_attributes['shapefiles'] = ['drawings-line','San_Joaquin-line',]
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue',]
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT','SAN JOAQUIN RIVER',]
      legend_elements = [Patch(facecolor='indianred', edgecolor='black', alpha = 0.6, label='CVP - South of Delta'),
                         Patch(facecolor='goldenrod', edgecolor='black', alpha = 0.6, label='State Water Project'),
                         Patch(facecolor='moccasin', edgecolor='crimson', alpha = 0.6, label='CVP - Friant')]
    if use_type == 'contracts4':
      calfews_attributes['shapefiles'] = ['drawings-line','San_Joaquin-line',]
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue',]
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT','SAN JOAQUIN RIVER','STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER']
      legend_elements = [Patch(facecolor='indianred', edgecolor='black', alpha = 0.6, label='CVP - South of Delta'),
                         Patch(facecolor='goldenrod', edgecolor='black', alpha = 0.6, label='State Water Project'),
                         Patch(facecolor='moccasin', edgecolor='black', alpha = 0.6, label='CVP - Friant'),
                         Patch(facecolor='olivedrab', edgecolor='crimson', alpha = 0.6, label='Local San Joaquin')]
    if use_type == 'contracts5':
      calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', ]
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue',]
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'SAN JOAQUIN RIVER', 'TULE RIVER','STANISLAUS RIVER', 'TUOLUMNE RIVER', 'MERCED RIVER']
      legend_elements = [Patch(facecolor='indianred', edgecolor='black', alpha = 0.6, label='CVP - South of Delta'),
                         Patch(facecolor='goldenrod', edgecolor='black', alpha = 0.6, label='State Water Project'),
                         Patch(facecolor='moccasin', edgecolor='black', alpha = 0.6, label='CVP - Friant'),
                         Patch(facecolor='olivedrab', edgecolor='black', alpha = 0.6, label='Local San Joaquin'),
                         Patch(facecolor='steelblue', edgecolor='crimson', alpha = 0.6, label='Local Tulare')]


  elif map_type == 'southerncv':
    box_coordinates = [-121.3, -118.3, 34.85, 37.45]#data_figure.format_plot
    calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext']
    calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue']
    calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'SAN JOAQUIN RIVER', 'TULE RIVER', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA', 'MERCED RIVER', 'STANISLAUS RIVER',  'TUOLUMNE RIVER']
    legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5),
                     Line2D([0], [0], color='midnightblue', lw=2, label='$\it{Natural}$ $\it{Channel}$'),
                     Line2D([0], [0], color='black', lw=2, label='$\it{Canal}$'),
                     Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5),
                     Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'),
                     Patch(facecolor='teal', edgecolor='teal', label='Irrigation District w/ Banking Program'),
                     Patch(facecolor='steelblue', edgecolor='steelblue', label='Dedicated Groundwater Bank')]

  elif map_type == 'sacramento':
    calfews_attributes['shapefiles'] = ['American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'Yuba_River-line']
    calfews_attributes['shapefile_color'] = ['midnightblue', 'midnightblue', 'midnightblue', 'midnightblue']
    calfews_attributes['csvfiles'] = ['AMERICAN RIVER', 'FEATHER RIVER', 'NORTH YUBA RIVER', 'SACRAMENTO RIVER']
    box_coordinates = [-123.0, -120.5, 38.0, 41.0]
    legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5),
                     Line2D([0], [0], color='midnightblue', lw=2, label='$\it{Natural}$ $\it{Channel}$'),
                     Line2D([0], [0], color='black', lw=2, label='$\it{Canal}$'),
                     Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5),
                     Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'),
                     Patch(facecolor='teal', edgecolor='teal', label='Irrigation District w/ Banking Program'),
                     Patch(facecolor='steelblue', edgecolor='steelblue', label='Dedicated Groundwater Bank')]

  elif map_type == 'sanjoaquin':
    calfews_attributes['shapefiles'] = ['San_Joaquin_Tributaries-line', 'San_Joaquin-line']
    calfews_attributes['shapefile_color'] = ['midnightblue', 'midnightblue']
    calfews_attributes['csvfiles'] = ['MERCED RIVER', 'SAN JOAQUIN RIVER', 'STANISLAUS RIVER', 'TUOLUMNE RIVER']
    box_coordinates = [-123.0, -119.5, 36.5, 38.0]
    legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5),
                     Line2D([0], [0], color='midnightblue', lw=2, label='$\it{Natural}$ $\it{Channel}$'),
                     Line2D([0], [0], color='black', lw=2, label='$\it{Canal}$'),
                     Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5),
                     Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'),
                     Patch(facecolor='teal', edgecolor='teal', label='Irrigation District w/ Banking Program'),
                     Patch(facecolor='steelblue', edgecolor='steelblue', label='Dedicated Groundwater Bank')]
  elif map_type == 'tulare':
    if use_type == 'Wonderful':
      calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'districts-polygon-no-won', 'districts-polygon-wonderful', 'kern_water_bank']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'forestgreen', 'indianred', 'steelblue']
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'SAN JOAQUIN RIVER', 'TULE RIVER']
      box_coordinates = [-121.2, -118.0, 34.8, 37.2]
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5),
                     Line2D([0], [0], color='midnightblue', lw=2, label='$\it{Natural}$ $\it{Channel}$'),
                     Line2D([0], [0], color='black', lw=2, label='$\it{Canal}$'),
                     Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5),
                     Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'),
                     Patch(facecolor='teal', edgecolor='teal', label='Irrigation District w/ Banking Program'),
                     Patch(facecolor='steelblue', edgecolor='steelblue', label='Dedicated Groundwater Bank')]
    
    else:
      calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'districts-polygon']
      calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'indianred']
      calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'SAN JOAQUIN RIVER', 'TULE RIVER']
      box_coordinates = [-121.2, -118.0, 34.8, 37.2]
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='SURFACE RESERVOIR', markerfacecolor='bisque', markersize=5),
                     Line2D([0], [0], color='midnightblue', lw=2, label='$\it{Natural}$ $\it{Channel}$'),
                     Line2D([0], [0], color='black', lw=2, label='$\it{Canal}$'),
                     Line2D([0], [0], marker='o', color='black', label='Urban Turnout', markerfacecolor='slategray', markersize=5),
                     Patch(facecolor='indianred', edgecolor='indianred', label='Irrigation District'),
                     Patch(facecolor='teal', edgecolor='teal', label='Irrigation District w/ Banking Program'),
                     Patch(facecolor='steelblue', edgecolor='steelblue', label='Dedicated Groundwater Bank')]

  return calfews_attributes, box_coordinates, legend_elements

def get_base_order():
  #which shapefiles go on the bottom
  base_list = ['Water_Districts/sacramento_districts', 'Water_Districts/feather_districts', 'Water_Districts/yuba_districts', 'Water_Districts/folsom_districts', 'Water_Districts/eastside_districts', 'Water_Districts/cvp_south_districts', 'Water_Districts/friant_districts', 'Water_Districts/tulare_districts', 'Water_Districts/swp_districts','Water_Districts/urban_districts','Water_Districts/recharge_districts', 'districts-no-banks', 'districts-no-banks_v2', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'westlands', 'kern_delta', 'Water_Districts/exchange_example_ag_districts', 'Water_Districts/exchange_example_urban_districts']
  no_outline_base_list = ['shorebird_priority_habitat/priority_only', 'Water_Districts/agricultural_districts']
  no_outline_list = ['wetlands/wetlands/i02_NCCAG_Vegetation', 'wetlands/wetlands/i02_NCCAG_Wetlands']


  return base_list, no_outline_base_list, no_outline_list

      
def create_reservoir_file(reservoir_watersheds, reservoir_filename):
  #set colors of point locations
  #note: when label says 'NAME RIVER' (i.e., SACRAMENTO RIVER) it refers to
  #the location of the reservoir, if it just says 'NAME' (i.e., SACRAMENTO) it
  #refers to a downstream location on the river, like a flow gauge
  reservoir = pd.read_csv(reservoir_filename)
  new_reservoir = pd.DataFrame()
  new_color_list = []
  x_loc = 'LONG'
  y_loc = 'LAT'
  crs = {'init': 'epsg:4326'}
  reservoir_color_list = {}
  reservoir_color_list['AMERICAN RIVER'] = 'bisque'
  reservoir_color_list['SACRAMENTO RIVER'] = 'bisque'
  reservoir_color_list['NORTH YUBA RIVER'] = 'bisque'
  reservoir_color_list['FEATHER RIVER'] = 'bisque'
  reservoir_color_list['STANISLAUS RIVER'] = 'bisque'
  reservoir_color_list['TUOLUMNE RIVER'] = 'bisque'
  reservoir_color_list['MERCED RIVER'] = 'bisque'
  reservoir_color_list['MOKELUMNE RIVER'] = 'bisque'
  reservoir_color_list['CALAVERAS RIVER'] = 'bisque'
  reservoir_color_list['TUOLUMNE RIVER 2'] = 'bisque'
  reservoir_color_list['CACHE CREEK'] = 'bisque'
  reservoir_color_list['PUTAH CREEK'] = 'bisque'
  reservoir_color_list['SACRAMENTO'] = 'midnightblue'
  reservoir_color_list['NORTH YUBA'] = 'midnightblue'
  reservoir_color_list['FEATHER'] = 'midnightblue'
  reservoir_color_list['STANISLAUS'] = 'midnightblue'
  reservoir_color_list['TUOLUMNE'] = 'midnightblue'
  reservoir_color_list['MERCED'] = 'midnightblue'
  reservoir_color_list['SACDELTA'] = 'midnightblue'
  reservoir_color_list['SJDELTA'] = 'midnightblue'
  reservoir_color_list['SAN JOAQUIN RIVER'] = 'bisque'
  reservoir_color_list['KINGS RIVER'] = 'bisque'
  reservoir_color_list['KAWEAH RIVER'] = 'bisque'
  reservoir_color_list['TULE RIVER'] = 'bisque'
  reservoir_color_list['KERN RIVER'] = 'bisque'
  reservoir_color_list['CALIFORNIA AQUEDUCT'] = 'bisque'
  reservoir_color_list['DELTA'] = 'black'
  reservoir_color_list['SOUTHERNCA'] = 'slategray'
  reservoir_color_list['CENTRALCA'] = 'slategray'
  reservoir_color_list['SOUTHBAY'] = 'slategray'
  reservoir_color_list['OUT OF BOX'] = 'slategray'
  reservoir_color_list['FISH'] = 'midnightblue'

  for plotted_res in reservoir_watersheds:
    new_reservoir = pd.concat([new_reservoir, reservoir[reservoir.BASIN == plotted_res]], axis = 0)
    new_color_list.append(reservoir_color_list[plotted_res])
  if x_loc in new_reservoir and y_loc in new_reservoir:
    geometry = [Point(xy) for xy in zip(new_reservoir[x_loc], new_reservoir[y_loc])]
    new_geo_df = gpd.GeoDataFrame(new_reservoir, crs = crs, geometry = geometry)
    
  return new_geo_df, new_color_list

def divide_districts(filename_folder, filename_folder2, project_folder):
  

  ##subdivide individual districts from Water_Districts shapefile into relevant groups
  districts = gpd.read_file(project_folder + '/CALFEWS_shapes/Water_Districts/Water_Districts.shp')
  districts = districts.to_crs(epsg = 4326)
  districts_v1 = gpd.read_file(project_folder + '/CALFEWS_shapes/districts-no-banks.shp')
      
  list_2 = ['Tulare Lake Basin',]
  for index, row in districts.iterrows():
    for list_value in list_2:
      if list_value in row['AGENCYNAME']:
        print(row['AGENCYNAME'])
  list_1 = ['Dudley Ridge',]
  list_2 = ['Tulare Lake Basin',]
  list_3 = ['Corcoran Irrigation', 'Riverdale Irrigation', 'Laguna Irrigation', 'Stratford Irrigation', 'Empire West Side', 'John Heinlen', 'Lemoore Canal']
  list_4 = ['Kaweah Delta',]
  list_5 = ['Central California', 'San Luis Canal', 'Firebaugh Canal', 'Columbia Canal']
  list_6 = ['Banta Carbona', 'Byron Bethany', 'Eagle Field', 'Mercy Springs', 'Oro Loma Water District', 'Patterson Irrigation', 'West Side Irrigation', 'West Stanilaus', 'Coelho Family', 'Fresno Slough', 'James Irrigation', 'Laguna Water District', '1606', 'Tranquility', 'Avenal', 'Huron', 'Meyers Farms', 'Lempesis']
  list_7 = ['Gravelly Ford', 'Hills Valley', 'Garfield', 'International Water District', 'Lewis Creek', 'Orange Cove', 'Stone Corral']
  list_8 = ['Ducor Irrigation District', 'Pixely', 'Terra Bella', 'Rancho Terra Bella', 'Vandalia', 'Porterville Irrigation District', 'Angolia', 'Alpaugh Irrigation District', 'Teapot Dome']
  list_9 = ['Lakeside Irrigation', 'Visalia  City', 'Lindsay  City', 'Farmersville  City', 'Tulare  City']
  list_10 = ['Hills Valley', 'Pixely', 'Tri-Valley']

  cvp_delta = ['Central California Irrigation District', 'Columbia Canal Company', 'Firebaugh Canal Company', 'San Luis Canal Company', 'Banta Carbona Irrigation District', 'Byron Bethany Irrigation District', 'Del Puerto Water District', 'Eagle Field Water District', 'Mercy Springs Water District', 'Ora Loma Water District', 'Pajaro Valley Water Management Agency', 'Santa Clara Valley Water District', 'Patterson Water District', 'West Side Irrigation District', 'Tracy', 'West Stanislaus Irrigation District', 'San Benito County Water District Zone 3', 'San Benito County Water District Zone 6', 'Avenal', 'Coalinga', 'Huron', 'Pacheco Water District', 'Panoche Water District', 'San Luis Water District', 'Westlands Water District']
  friant = ['Gravely Ford Water District', 'Arvin - Edison Water Storage District', 'Delano - Earlimart Irrigation District', 'Exeter Irrigation District', 'Fresno Irrigation District', 'Hills Valley Irrigation District', 'Garfield Water District', 'International Water District', 'Ivanhoe Irrigation District', 'Kern - Tulare Water District', 'Lewis Creek Water District', 'Lindmore Irrigation District', 'Lindsay - Strathmore Irrigation District', 'Lower Tule River Irrigation District', 'Orange Cove Irrigation District', 'Saucelito Irrigation District', 'Shafter - Wasco Irrigation District', 'Southern San Joaquin Municipal Utility District', 'Stone Corral Irrigation District', 'Tea Pot Dome Water District', 'Terra Bella Irrigation District', 'Tri-Valley Water District', 'Tulare Irrigation District', 'Chowchilla Water District', 'Madera Irrigation District']
  sj_local = ['Central San Joaquin Water Conservation District', 'Oakdale Irrigation District', 'South San Joaquin Irrigation District', 'Modesto Irrigation District', 'Turlock Irrigation District', 'San Francisco Public Utilities Comission', 'Merced Irrigation District', 'Merquin County Water District', 'Stevinson Water District']
  tulare_local = ['North Kern Water Storage District', 'Kern Delta Water District', 'Bakersfield  City Of', 'Kaweah Delta Water Conservation District', 'Porterville Irrigation District', 'Vandalia Irrigation District', 'Pixley Irrigation District', 'Fresno  City Of', 'Alta Irrigation District', 'Consolidated Irrigation District', 'Kings River Water District', 'Corcoran Irrigation District', 'Laguna Irrigation District', 'Reed Ditch Company', 'Riverdale Irrigation District', 'Liberty Mill Race Company', 'Burrel Ditch Company', 'Liberty Canal Company', 'Lemoore Canal & Irrigation Company', 'John Heinlen Mutual Water Company', 'Reclamation District No 2069', 'Empire West Side Irrigation District',  'Stratford Irrigation District', 'Tulare Lake Basin Water Storage District', 'Reclamation District No 761', 'Crescent Canal Company', 'Stinson Water District', 'James Irrigation District', 'Tranquility Irrigation District']
  swp = ['Dudley Ridge Water District', 'Belridge Water Storage District', 'Berrenda Mesa Water District', 'Buena Vista Water Storage District', 'Cawelo Water District', 'Henry Miller Water District', 'Lost Hills Water District', 'Rosedale - Rio Bravo Water Storage District', 'Semitropic Water Service District', 'Tehachapi - Cummings County Water District', 'Tejon - Castac Water District', 'West Kern Water District', 'Wheeler Ridge - Maricopa Water Storage District']


  key_CALFEWS = {}
  key_CALFEWS['Central California Irrigation District'] = 'San Joaquin River Exchange Contractors'
  key_CALFEWS['Columbia Canal Company'] = 'San Joaquin River Exchange Contractors'
  key_CALFEWS['Firebaugh Canal Company'] = 'San Joaquin River Exchange Contractors'
  key_CALFEWS['San Luis Canal Company'] = 'San Joaquin River Exchange Contractors'
  key_CALFEWS['Banta Carbona Irrigation District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Byron Bethany Irrigation District'] = 'Small CVP-SOD Contractors'
  #key_CALFEWS['Del Puerto Water District'] = 
  key_CALFEWS['Eagle Field Water District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Mercy Springs Water District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Ora Loma Water District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Pajaro Valley Water Management Agency'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Santa Clara Valley Water District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Patterson Water District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS[ 'West Side Irrigation District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Tracy'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['West Stanislaus Irrigation District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['San Benito County Water District Zone 3'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['San Benito County Water District Zone 6'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Avenal'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Coalinga'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Huron'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Pacheco Water District'] = 'Small CVP-SOD Contractors'
  key_CALFEWS['Gravely Ford Water District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Hills Valley Irrigation District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Garfield Water District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['International Water District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Ivanhoe Irrigation District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Lewis Creek Water District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Orange Cove Irrigation District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Stone Corral Irrigation District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Tri-Valley Water District'] = 'Small CVP-Friant Contractors'
  key_CALFEWS['Bakersfield  City Of'] = 'City of Bakersfield'
  key_CALFEWS['Vandalia Irrigation District'] = 'Small Tule River Rightsholders'
  key_CALFEWS['Fresno  City Of'] = 'City of Fresno'
  key_CALFEWS['Kings River Water District'] = 'Kings River Water Association'
  key_CALFEWS['Corcoran Irrigation District'] = 'Kings River Water Association'
  key_CALFEWS['Laguna Irrigation District'] = 'Kings River Water Association'
  key_CALFEWS['Reed Ditch Company'] = 'Kings River Water Association'
  key_CALFEWS['Riverdale Irrigation District'] = 'Kings River Water Association'
  key_CALFEWS['Liberty Mill Race Company'] = 'Kings River Water Association'
  key_CALFEWS['Burrel Ditch Company'] = 'Kings River Water Association'
  key_CALFEWS['Liberty Canal Company'] = 'Kings River Water Association'
  key_CALFEWS['Lemoore Canal & Irrigation Company'] = 'Kings River Water Association'
  key_CALFEWS['John Heinlen Mutual Water Company'] = 'Kings River Water Association'
  key_CALFEWS['Reclamation District No 2069'] = 'Kings River Water Association'
  key_CALFEWS['Empire West Side Irrigation District'] = 'Kings River Water Association'
  key_CALFEWS['Stratford Irrigation District'] = 'Kings River Water Association'
  key_CALFEWS['Reclamation District No 761'] = 'Kings River Water Association'
  key_CALFEWS['Crescent Canal Company'] = 'Kings River Water Association'
  key_CALFEWS['Stinson Water District'] = 'Kings River Water Association'
  key_CALFEWS['James Irrigation District'] = 'Kings River Water Association'
  key_CALFEWS['Tranquility Irrigation District'] = 'Kings River Water Association'
  key_CALFEWS['Semitropic Water Service District'] = 'Semitropic Water Storage District'
  key_CALFEWS['Dudley Ridge Water District'] = 'Dudley Ridge Irigation District'
  key_CALFEWS['Central San Joaquin Water Conservation District'] = 'newmelones'
  key_CALFEWS['Oakdale Irrigation District'] = 'newmelones'
  key_CALFEWS['South San Joaquin Irrigation District'] = 'newmelones'
  key_CALFEWS['Modesto Irrigation District'] = 'donpedro'
  key_CALFEWS['Turlock Irrigation District'] = 'donpedro'
  key_CALFEWS['San Francisco Public Utilities Comission'] = 'donpedro'
  key_CALFEWS['Merced Irrigation District'] = 'exchequer'
  key_CALFEWS['Merquin County Water District'] = 'exchequer'
  key_CALFEWS['Stevinson Water District']  = 'exchequer'
  
  aggregated_names = ['Dudley Ridge Irigation District','Tulare Lake Basin Water Storage District','San Joaquin River Exchange Contractors', 'Small CVP-SOD Contractors', 'Small CVP-Friant Contractors', 'Small Tule River Rightsholders', 'Small Kaweah River Rightsholders', 'Small Cross-Valley Contractors', 'Kings River Water Association', 'Kaweah Delta Water Conservation District']
  list_objects = [list_1, list_2, list_5, list_6, list_7, list_8, list_9, list_10, list_3, list_4]
  list_objects = [cvp_delta, friant, swp, sj_local, tulare_local]
  aggregated_names = ['CVP Delta', 'CVP Friant', 'State Water Project', 'SJ Local', 'Tulare Local']
  output_key = {}
  output_key['CVP Delta'] = ['cvpdelta','cvpexchange']
  output_key['CVP Friant'] = ['friant1', 'friant2']
  output_key['State Water Project'] = ['swpdelta',]
  output_key['SJ Local'] = ['newmelones','donpedro','exchequer']
  output_key['Tulare Local'] = ['kingsriver','kaweahriver','tuleriver', 'kernriver']
  all_shapes = pd.DataFrame()
  counter =0
  gcm_list = ['miroc5', 'inmcm4', 'ipsl-cm5a-mr', 'hadgem2-cc', 'hadgem2-es', 'gfdl-cm3', 'gfdl-esm2m', 'cnrm-cm5', 'csiro-mk3-6-0', 'canesm2', 'ccsm4']
  gcm_unique_list = ['miroc5', 'inmcm4', 'ipsl-cm5a-mr', 'gem2-cc', 'gem2-es', 'gfdl-cm3', 'gfdl-esm2m', 'cnrm-cm5', 'csiro-mk3-6-0', 'canesm2', 'ccsm4']
  rcp_list = ['45', '85']
  min_change = 0.0
  max_change = 0.0
  for list_use, agg_name in zip(list_objects, aggregated_names):
    aggregated_shape = gpd.GeoDataFrame()
    for index, row in districts.iterrows():
      for list_value in list_use:
        if list_value in row['AGENCYNAME']:
          this_district = districts[districts.index == index]
          aggregated_shape = pd.concat([aggregated_shape, this_district])
    if len(aggregated_shape) > 1:
      aggregated_shape = gpd.GeoDataFrame(aggregated_shape, crs = districts.crs, geometry = aggregated_shape['geometry'])
      aggregated_shape = aggregated_shape.dissolve()
    else:
      aggregated_shape = gpd.GeoDataFrame(aggregated_shape, crs = districts.crs, geometry = aggregated_shape['geometry'])
      aggregated_shape = aggregated_shape.dissolve()
    scenario_list = []
    climate_values = []
    climate_values_by_rcp = {}
    for rcp in rcp_list:
      climate_values_by_rcp[rcp] = []
    for gcm, gcm_unique in zip(gcm_list, gcm_unique_list):
      for rcp in rcp_list:
        contract_values = pd.read_csv('CALFEWS-main/results/climate_change_files_expanded/results_' + gcm + '_rcp' + rcp + '/contract_deliveries_annual_' + gcm + '_rcp' + rcp + '.csv', index_col = 0)
        reservoir_values = pd.read_csv('CALFEWS-main/results/climate_change_files_expanded/results_' + gcm + '_rcp' + rcp + '/reservoir_releases_annual_' + gcm + '_rcp' + rcp + '.csv', index_col = 0)
        contract_values.index = pd.to_datetime(contract_values.index)
        reservoir_values.index = pd.to_datetime(reservoir_values.index)
        total_hist = 0.0
        total_climate_change = 0.0
        scenario_list.append(gcm_unique[:7] + '_' + rcp)
        for column_name in output_key[agg_name]:
          if column_name + 'non_flood_release' in reservoir_values:
            total_hist += np.mean(reservoir_values.loc['1950':'2020', column_name + 'non_flood_release'])
            total_climate_change += np.mean(reservoir_values.loc['2048':'2098', column_name + 'non_flood_release'])
          elif column_name + '_contract_deliveries' in contract_values:
            total_hist += np.mean(contract_values.loc['1950':'2020', column_name + '_contract_deliveries'])
            total_climate_change += np.mean(contract_values.loc['2048':'2098', column_name + '_contract_deliveries'])
        climate_values.append((1.0 - total_climate_change / total_hist))
        climate_values_by_rcp[rcp].append((1.0 - total_climate_change / total_hist))
    contract_changes = pd.DataFrame(columns = scenario_list)
    for gcm, climate in zip(scenario_list, climate_values):
      contract_changes.loc[0, gcm] = float(climate)
      min_change = min(min_change, float(climate))
      max_change = max(max_change, float(climate))
    contract_changes.loc[0, 'name'] = agg_name
    for rcp in rcp_list:
      contract_changes.loc[0, rcp] = np.mean(climate_values_by_rcp[rcp])
    labeled_shape = gpd.GeoDataFrame(contract_changes, crs = districts.crs, geometry = aggregated_shape['geometry'])
    counter += 1
    all_shapes = pd.concat([all_shapes, labeled_shape])
  all_shapes = all_shapes.reset_index()
  all_shapes = gpd.GeoDataFrame(all_shapes, crs = districts.crs, geometry = all_shapes['geometry'])
  all_shapes.to_file(driver = 'ESRI Shapefile', filename = filename_folder + 'CALFEWS_contracts.shp')
    
  counter = 0 
  district_changes = pd.DataFrame()  
  geometry_list = []
  duplicate_check = []
  district_changes_irr = pd.DataFrame()
  district_changes_rech = pd.DataFrame()
  for list_use, agg_name in zip(list_objects, aggregated_names):
    for index, row in districts.iterrows():
      for list_value in list_use:
        if list_value in row['AGENCYNAME']:
          this_district = districts[districts.index == index]
          if list_value in key_CALFEWS:
            calfews_id = key_CALFEWS[list_value]
          elif list_value[:9] == 'Tehachapi':
            calfews_id = list_value
          else:
            calfews_id = list_value.replace(' - ', '-')
            
          if list_value not in duplicate_check:
            geometry_list.append(row['geometry'])
            duplicate_check.append(list_value)
          
          change_by_rcp = {}
          for rcp in rcp_list:
            change_by_rcp[rcp + '_irr'] = []
            change_by_rcp[rcp + '_rech'] = []
          district_changes_irr.loc[list_value, 'name'] = list_value
          district_changes_rech.loc[list_value, 'name'] = list_value
          for gcm, gcm_unique in zip(gcm_list, gcm_unique_list):
            for rcp in rcp_list:
              if agg_name == 'SJ Local':
                reservoir_values = pd.read_csv('CALFEWS-main/results/climate_change_files_expanded/results_' + gcm + '_rcp' + rcp + '/reservoir_releases_annual_' + gcm + '_rcp' + rcp + '.csv', index_col = 0)
                reservoir_values.index = pd.to_datetime(reservoir_values.index)
                if calfews_id + 'non_flood_release' in reservoir_values:
                  total_hist = np.mean(reservoir_values.loc['1950':'2020', calfews_id + 'non_flood_release'])
                  total_climate_change = np.mean(reservoir_values.loc['2048':'2098', calfews_id + 'non_flood_release'])
                  district_changes_irr.loc[list_value, gcm_unique + '_' + rcp] = 1.0 - total_climate_change / total_hist
                  district_changes_rech.loc[list_value, gcm_unique + '_' + rcp] = 1.0 - total_climate_change / total_hist
                  change_by_rcp[rcp + '_irr'].append(1.0 - total_climate_change / total_hist)
                  change_by_rcp[rcp + '_rech'].append(1.0 - total_climate_change / total_hist)
                  
              else:
                irrigation_values = pd.read_csv('CALFEWS-main/results/climate_change_files_expanded/results_' + gcm + '_rcp' + rcp + '/irrigation_annual_' + gcm + '_rcp' + rcp + '.csv', index_col = 0)
                recharge_values = pd.read_csv('CALFEWS-main/results/climate_change_files_expanded/results_' + gcm + '_rcp' + rcp + '/recharge_annual_' + gcm + '_rcp' + rcp + '.csv', index_col = 0)
                if calfews_id in irrigation_values:
                  total_hist_i = np.mean(irrigation_values.loc[np.logical_and(recharge_values.index > 1950, recharge_values.index < 2021), calfews_id])
                  total_climate_change_i = np.mean(irrigation_values.loc[np.logical_and(irrigation_values.index > 2049, irrigation_values.index < 2100), calfews_id])
                  if total_hist_i > 0.0:
                    district_changes_irr.loc[list_value, gcm_unique + '_' + rcp] = 1.0 - total_climate_change_i / total_hist_i
                    change_by_rcp[rcp + '_irr'].append(1.0 - total_climate_change_i / total_hist_i)
                  else:
                    district_changes_irr.loc[list_value, gcm_unique + '_' + rcp] = 0.0
                    change_by_rcp[rcp + '_irr'].append(0.0)
                  
                if calfews_id in recharge_values:
                  total_hist_r = np.mean(recharge_values.loc[np.logical_and(recharge_values.index > 1950, recharge_values.index < 2021), calfews_id])
                  total_climate_change_r = np.mean(recharge_values.loc[np.logical_and(recharge_values.index > 2049, recharge_values.index < 2100), calfews_id])
                  if total_hist_i + total_hist_r > 0.0:
                    district_changes_rech.loc[list_value, gcm_unique + '_' + rcp] = 1.0 - (total_climate_change_i + total_climate_change_r) / (total_hist_i + total_hist_r)
                    change_by_rcp[rcp + '_rech'].append(1.0 - (total_climate_change_i + total_climate_change_r) / (total_hist_i + total_hist_r))
                  else:
                    district_changes_rech.loc[list_value, gcm_unique + '_' + rcp] = 0.0
                    change_by_rcp[rcp + '_rech'].append(0.0)
                  
          for rcp in rcp_list:
            district_changes_irr.loc[list_value, rcp] = np.mean(np.asarray(change_by_rcp[rcp + '_irr']))
            district_changes_rech.loc[list_value, rcp] = np.mean(np.asarray(change_by_rcp[rcp + '_rech']))
  kern_water_bank = gpd.read_file(project_folder + '/CALFEWS_Shapes/kern_water_bank.shp')
  print(kern_water_bank)
  kern_water_bank = kern_water_bank.to_crs(epsg = 4326)
  print(kern_water_bank)
  change_by_rcp = {}
  for rcp in rcp_list:
    change_by_rcp[rcp] = []
  for gcm, gcm_unique in zip(gcm_list, gcm_unique_list):
    for rcp in rcp_list:
      recharge_values = pd.read_csv('CALFEWS-main/results/climate_change_files_expanded/results_' + gcm + '_rcp' + rcp + '/recharge_annual_' + gcm + '_rcp' + rcp + '.csv', index_col = 0)
      total_hist_r = np.mean(recharge_values.loc[np.logical_and(recharge_values.index > 1950, recharge_values.index < 2021), 'Kern Fan Groundwater Banking'])
      total_climate_change_r = np.mean(recharge_values.loc[np.logical_and(recharge_values.index > 2049, recharge_values.index < 2100), 'Kern Fan Groundwater Banking'])
      district_changes_rech.loc['Kern Fan Groundwater Banking', gcm_unique + '_' + rcp] = 1.0 - total_climate_change_r / total_hist_r
      district_changes_irr.loc['Kern Fan Groundwater Banking', gcm_unique + '_' + rcp] = 0.0
      change_by_rcp[rcp].append(1.0 - total_climate_change_r / total_hist_r)
  district_changes_rech.loc['Kern Fan Groundwater Banking', 'name'] = 'Kern Fan Groundwater Banking'
  district_changes_irr.loc['Kern Fan Groundwater Banking', 'name'] = 'Kern Fan Groundwater Banking'
  for rcp in rcp_list:
    district_changes_irr.loc['Kern Fan Groundwater Banking', rcp] = 0.0
    district_changes_rech.loc['Kern Fan Groundwater Banking', rcp] = np.mean(np.asarray(change_by_rcp[rcp]))
    print(district_changes_irr)
    print(district_changes_rech)
  for index, row in kern_water_bank.iterrows():
    print(len(geometry_list))
    geometry_list.append(row['geometry'])
    print(len(geometry_list))
    break
  district_shapes_irr = gpd.GeoDataFrame(district_changes_irr, crs = districts.crs, geometry = geometry_list)
  district_shapes_rech = gpd.GeoDataFrame(district_changes_rech, crs = districts.crs, geometry = geometry_list)
  print(district_shapes_rech)
  print(district_shapes_irr)
  district_shapes_irr.to_file(driver = 'ESRI Shapefile', filename = filename_folder + 'CALFEWS_districts_irr.shp')
  district_shapes_rech.to_file(driver = 'ESRI Shapefile', filename = filename_folder + 'CALFEWS_districts_rech.shp')
  
  #set up individual district shapefiles
  westlands_district = districts_v1[districts_v1['AGENCYNAME'] == 'Westlands Water District']
  kern_delta_district = districts_v1[districts_v1['AGENCYNAME'] == 'Kern Delta Water District']
  districts_v1_1 = districts_v1[districts_v1['AGENCYNAME'] != 'Westlands Water District']
  districts_v2 = districts_v1_1[districts_v1_1['AGENCYNAME'] != 'Westlands Water District']
  westlands_district.to_file(driver = 'ESRI Shapefile', filename = project_folder +'/CALFEWS_shapes/westlands.shp')
  kern_delta_district.to_file(driver = 'ESRI Shapefile', filename = project_folder +'/CALFEWS_shapes/kern_delta.shp')
  districts_v2.to_file(driver = 'ESRI Shapefile', filename = project_folder +'/CALFEWS_shapes/districts-no-banks_v2.shp')

  #filter out main canals from statewide canal shapefile
  canals = gpd.read_file(project_folder + '/CALFEWS_shapes/Canals_and_Aqueducts_local/Canals_and_Aqueducts_local.shp')
  canals = canals.to_crs(epsg = 4326)
  canals_to_use = ['Tehama-Colusa Canal', 'Glenn Colusa Canal', 'Mokelumne Aqueduct', 'Chowchilla Canal', 'San Luis Canal', 'Hetch Hetchy Aqueduct', 'San Francisco Public Utility Commission', 'Semitropic Canal', 'Arvin Edison Canal', 'Alta Main Canal', 'Consolidated Canal', 'South Bay Aqueduct', 'Cross Valley Canal', 'Los Angeles Aqueduct']
  new_dict = {}
  new_dict['Name'] = canals_to_use
  new_dataFrame = pd.DataFrame(new_dict)
  new_gdf = canals.merge(new_dataFrame, on = 'Name')
  new_gdf.to_file(driver = 'ESRI Shapefile', filename = filename_folder2 +  'canals_abbr.shp')

  #get a shapefile of only the california aqueduct
  kern_canals = gpd.read_file(project_folder + '/CALFEWS_shapes/Kern_Watercourse_2014/Kern_Watercourse_2014.shp')
  cal_aq = kern_canals[kern_canals['NAME'] == 'California Aqueduct']
  cal_aq = cal_aq.to_crs(epsg = 4326)
  cal_aq.to_file(driver = 'ESRI Shapefile', filename = project_folder +  '/CALFEWS_shapes/Canals_and_Aqueducts_local/kern_cal_aq.shp')

  #find priority shorebird habitats
  shorebird = gpd.read_file(project_folder + '/CALFEWS_shapes/shorebird_priority_habitat/shorebird_priority_habitat.shp')
  shorebird = shorebird.to_crs(epsg = 4326)
  shorebird_priority = shorebird[shorebird['PriHabitat'] == 1]
  shorebird_priority.to_file(driver = 'ESRI Shapefile', filename = project_folder + '/CALFEWS_shapes/shorebird_priority_habitat/priority_only.shp')

  #water district categories(by contract type):
  #urban districts
  #agricultural districts
  #recharge districts: districts w/ direct GW recharge
  #black butte
  #colusa basin - colusa basin, not on the tehama-colusa canal
  #corning_canal
  #tehama_colusa
  #trinity
  #folsom_dam - take directly from folsum dam
  #folsom_south - use the folsom south canal
  #sac_settlement - large districts in the sacramento that get water from CVP through 'settlement contracts' (i.e., they were there before the SWP
  #sac_settlement_small - small districts and individual users w/ CVP settlement contracts
  #solano_project
  #cache_creek
  #delta_mendota
  #mendota_pool
  #cross_valley - cross valley canal contractors w/ cvp
  #san_felipe - cvp contractor subgroup
  #san_luis - cvp contractor subgroup
  #exchange - cvp exchange contractors in the San Joaquin (i.e., original San Joaquin River users that get delta water in exchange for their water going to the FKC)
  #friant - friant-kern canal contractors
  #delta
  #feather_river
  #yuba_river
  #mokelumne_calaveras
  #eastside
  #tuolumne
  #merced
  #kings
  #kaweah
  #tule
  #kern
  #swp - state water project
  #kcwa - kern county water authority
  #water_exchange_example_ag - subset to illustrate exchanges
  #water_exchange_example_urban - subset to illustrate exchanges
  
  ##these categories are grouped into the following shapefiles (can be rearranged however):
  #'sacramento_districts' - black butte, colusa, corning, tehama colusa, trinity, sac settlement, sac settlemnt small, 
  #'sac_west_districts' - solano project, cache creek
  #'feather_districts' - feather 
  #'yuba_districts' - yuba
  #'folsom_districts' - folsom_south, folsom dam
  #'eastside_districts' - eastside, tuolumne, merced, mokelumne_calaveras, 
  #'cvp_south_districts' - delta mendota, mendota pool, cross valley, san felipe, san luis, exchange, delta
  #'friant_districts' - friant
  #'tulare_districts' - kings, kaweah, tule, kern
  #'swp_districts' - swp, kcwa, 
  #'agricultural_districts'
  #'urban_districts'
  #'recharge_districts'
  #'exchange_example_ag_districts'
  #'exchange_example_urban_districts'

  urban_districts = ['Davis Water District (from USBR)', 'City of Redding', 'City of Shasta Lake', 'Roseville', 'Sacramento County Water Agency', 'East Bay Municipal Utility District', 'Sacramento Municipal Utility District', 'City of Redding',  'West Sacramento', 'Santa Clara Valley Water District', 'Tracy', 'San Benito County Water District Zone 3', 'San Benito County Water District Zone 6', 'Avenal', 'Coalinga', 'Huron', 'Contra Costa Water District', 'Marysville', 'Wheatland City', 'Olivehurst Public Utilities District', 'Yuba City', 'East Bay Municipal Utility District', 'Calaveras Public Utilities District', 'San Francisco Public Utilities Comission', 'Alameda County Flood Control District', 'Alameda County Water District', 'Metropolitan Water District Of Southern California', 'Napa County Flood Control and Water Conservation District', 'Oak Flat Water District', 'Palmdale Water District', 'Plumas County Flood Control and Water Conservation District', 'San Bernardino Valley Municipal Water District', 'San Gabriel Valley Municipal Water District', 'San Gorgonio Pass Water Agency', 'San Luis Obispo County Flood Control And Water Conservation District', 'Ventura County Watershed Protection District', 'Antelope Valley - East Kern Water Agency', 'Coachella Valley Water District', 'Crestline - Lake Arrowhead Water Agency', 'Desert Water Agency', 'Mojave Water Agency', 'Winters  City Of', 'Davis  City Of', 'Woodland  City Of', 'Vacaville  City Of' , 'Fairfield  City Of', 'Suisun City', 'Vallejo  City Of'] 
  agricultural_districts = ['4-E Water District', 'Stony Creek Water District', 'Colusa Drain Mutual Water Company', 'Corning Water District', 'Proberta Water District', 'Thomes Creek Water District', 'Colusa County Water District', '4-M Water District', 'Cortina Water District', 'Glenn Valley Water District', 'Holthouse Water District', 'La Grande Water District', 'Myers-marsh Mutual Water Company', 'Centerville Community Services District', 'Mountain Gate Community Services District', 'Dunnigan Water Works', 'Glide Water District', 'Kanawha Water District', 'Kirkwood Water District', 'Orland - Artois Water District', 'Westside Water District', 'Feather Water District', 'Bella Vista Water District', 'Clear Creek Community Services District', 'Shasta Community Services District', 'El Dorado Irrigation District', 'San Juan Water District', 'Placer County Water Agency', 'Anderson - Cottonwood Irrigation District', 'Conaway Preservation Group', 'Cranmore Farms', 'Eastside Mutual Water Company', 'Glenn - Colusa Irrigation District', 'Maxwell Irrigation District', 'Meridian Farms Water Company', 'Natomas Central Mutual Water Company', 'Pelger Mutual Water Company', 'Pleasant Grove Verona Municipal Water District', 'Princeton - Codora - Glenn Irrigation District', 'Provident Irrigation District', 'Reclamation District No 1000', 'Reclamation District No 900', 'Reclamation District No 1004', 'Reclamation District No. 108', 'Sutter Mutual Water Company', 'Sycamore Family Trust', 'Tisdale Irrigation And Drainage Company', 'Alexander  Thomas And Karen',  'Anderson, Arthur Et Al (formerly Westfall, Mary)', 'Anderson, Arthur et al', 'Andreotti, Beverly F., Et Al','Baber, Jack Et Al','Beckley, Ralph And Ophelia', 'Butler, Dianne E.', 'Butte Creek Farms (a)', 'Butte Creek Farms (m)', 'Butte Creek Farms (p)', 'Butte Creek Farms (y)', 'Byrd, Anna C. And Osborne, Jane', 'Cachil Dehe Band Of Wintun Indians', 'Carter Mutual Water Company', 'Chesney, Adona', 'Churkin, Michael And Carol', 'Cummings, William S.', 'Driscoll Strawberry Associates, Inc.', 'Driver, Gary, Et Al', 'Driver, Gregory E.', 'Driver, John A. And Clare M. (1314)', 'Driver, John A. And Clare M. (2398)', 'Driver, William A. Et Al', 'Dyer, Jeffrey E. And Wing-dyer, Jan', 'E. L. H. Sutter Properties',  'Eggleston, Ronald H. And Susan I.', 'Ehrke,  Allen A. And Bonnie E.', 'Exchange Bank (c/o Nature Conservancy)', 'Fedora, Sibley G. And Margaret L.', 'Forry, Laurie E.', 'Furlan, Emile And Simone', 'Gillaspy, William F.', 'Giovannetti', 'Giusti, Richard J. And Sandra A.', 'Gjermann, Hal', 'Gomes, Judith', 'Green Valley Corporation (5210)', 'Green Valley Corporation (5211)', 'Griffin, Joseph, And Prater, Sharon', 'Hale, Judith And Marks, Alice (1638)', 'Hale, Judith And Marks, Alice (7572)', 'Hatfield, R & B', 'Heidrick, Joe Jr.', 'Heidrick, Mildred (1616)', 'Heidrick, Mildred (8322)', 'Henle, Thomas N.', 'Hiatt, Thomas (Haitt Family Trust)', 'Hiatt, Thomas And Illerich, Phillip', 'Howald Farms', 'Howard, Theodore W. And Linda M', 'J.B. Unlimited', 'Jaeger, William L. And Patricia A.', 'Jansen, Peter And Sandy', 'Kary, Carol', 'King, Benjamin And Laura', 'Klsy LLC', 'Knaggs Walnut Ranches', 'Knights Landing Investors', 'Lauppe, Burton And Kathryn (1289)', 'Lauppe, Burton And Kathryn (1364)', 'Leiser, Dorothy L.', 'Leviathan, Inc.', 'Lockett, William And Jean', 'Lomo Cold Storage And Michelli, Justin', 'Lonon, Michael E.', 'MCM Properties', 'Mehrhof, Susan And Montgomery, John', 'Mesquite Investors, LLC And Family Real Property Limited Partnership', 'Meyer Crest', 'Micke, Daniel And Nina', 'Morehead, Joseph A. And Brenda', 'Munson, James T. And Dalmira', 'Natomas Basin Conservancy', 'Nelson, Thomas L. And Hazel M.', 'Nene Ranch', 'Obrien, Frank And Janice', 'Odysseus Farms Partnership', 'Oji Brothers Farm, Inc.', 'Oji, Mitsue, Family Partnership', 'Otterson, Mike (Wells, Joyce)', 'Pacific Realty Associates', 'Penner, Roger And Leona', 'Quad-H Ranches', 'Rauf, Abdul And Tahmina (formerly Forster, R. And J.)', 'Reische, Eric', 'Reische, Laverne', 'Richter, Henry D. Et Al', 'River Garden Farms Company', 'Roberts Ditch Irrigation Company', 'Rubio, Exequiel And Elsa', 'Sacramento River Ranch', 'Seaver, Charles W. And Barbara J.', 'Tarke, Stephen E. And Debra F.', 'Tuttle, Charles W. And Noack, Sue T.', 'Wakida, Tomio (1415)', 'Wakida, Tomio (5200)', 'Wallace, Kenneth L. Living Trust', 'Willey, Edwin A. And Marjorie E.', 'Wilson Ranch Partnership', 'Windswept Land And Livestock Company', 'Wisler, John W. Jr', 'Young, Russel L., Et Al', 'Zelmar Ranch', 'Banta Carbona Irrigation District', 'Byron Bethany Irrigation District', 'Del Puerto Water District', 'Eagle Field Water District', 'Mercy Springs Water District', 'Ora Loma Water District', 'Pajaro Valley Water Management Agency', 'Westlands Water District', 'Patterson Water District', 'West Side Irrigation District', 'West Stanislaus Irrigation District', 'Fresno Slough Water District', 'James Irrigation District', 'Laguna Water District', 'Reclamation District No 1606', 'Tranquility Irrigation District', 'Hills Valley Irrigation District', 'Kern - Tulare Water District', 'Tri-Valley Water District', 'Pacheco Water District', 'Panoche Water District', 'San Luis Water District', 'Westlands Water District', 'Central California Irrigation District', 'Columbia Canal Company', 'Firebaugh Canal Company', 'San Luis Canal Company', 'Gravely Ford Water District', 'Delano - Earlimart Irrigation District', 'Exeter Irrigation District',  'Hills Valley Irrigation District', 'Garfield Water District', 'International Water District', 'Ivanhoe Irrigation District', 'Kern - Tulare Water District', 'Lewis Creek Water District', 'Lindmore Irrigation District', 'Lindsay - Strathmore Irrigation District', 'Orange Cove Irrigation District', 'Porterville Irrigation District', 'Saucelito Irrigation District', 'Shafter - Wasco Irrigation District', 'Southern San Joaquin Municipal Utility District', 'Stone Corral Irrigation District', 'Tea Pot Dome Water District', 'Terra Bella Irrigation District', 'Tri-Valley Water District', 'Western Canal Water District', 'Richvale Irrigation District', 'Biggs - West Gridley Water District', 'Butte Water District', 'Sutter Extension Water District', 'Oswald WD', 'Feather Water District', 'Tudor Mutual Water Company', 'Garden Highway Mutual Water Company', 'Plumas Mutual Water Company', 'Browns Valley Irrigation District', 'Ramirez Water District', 'Cordua Irrigation District', 'Hallwood Irrigation District', 'Brophy Water District', 'South Yuba Water District', 'Dry Creek Mutual Water Company', 'Wheatland Water District', 'Linda County Water District', 'North Yuba Water District', 'Camp Far West Irrigation District', 'Plumas Mutual Water Company', 'Reclamation District No 784', 'Reclamation District No 10', 'Reclamation District No 2103', 'Reclamation District No 817', 'Nevada Irrigation District', 'South Sutter Water District', 'Jackson Valley Irrigation District', 'Stockton East Water District', 'Central San Joaquin Water Conservation District', 'Oakdale Irrigation District', 'South San Joaquin Irrigation District', 'Modesto Irrigation District', 'Turlock Irrigation District', 'Merced Irrigation District', 'Merquin County Water District', 'Stevinson Water District', 'Kings River Water District', 'Corcoran Irrigation District', 'Laguna Irrigation District', 'Reed Ditch Company', 'Riverdale Irrigation District', 'Liberty Mill Race Company', 'Burrel Ditch Company', 'Liberty Canal Company', 'Last Chance Creek Water District', 'Lemoore Canal & Irrigation Company', 'John Heinlen Mutual Water Company', 'Reclamation District No 2069', 'Empire West Side Irrigation District',  'Stratford Irrigation District', 'Tulare Lake Basin Water Storage District', 'Reclamation District No 761', 'Crescent Canal Company', 'Stinson Water District', 'James Irrigation District', 'Tranquility Irrigation District', 'Porterville Irrigation District', 'Vandalia Irrigation District', 'Pixley Irrigation District', 'Dudley Ridge Water District', 'Empire West Side Irrigation District', 'Littlerock Creek Irrigation District', 'Belridge Water Storage District', 'Berrenda Mesa Water District', 'Henry Miller Water District', 'Lost Hills Water District', 'Semitropic Water Service District', 'Tehachapi - Cummings County Water District', 'Tejon - Castac Water District', 'Wheeler Ridge - Maricopa Water Storage District', 'Solano Irrigation District', 'Maine Prairie Water District', 'Yolo County Flood Control And Water Conservation District']
  recharge_districts = ['Alta Irrigation District', 'Arvin - Edison Water Storage District', 'Buena Vista Water Storage District', 'Cawelo Water District','Consolidated Irrigation District', 'Fresno Irrigation District', 'Kaweah Delta Water Conservation District', 'Kern Delta Water District', 'North Kern Water Storage District', 'Rosedale - Rio Bravo Water Storage District', 'Tulare Irrigation District', 'Lower Tule River Irrigation District', 'West Kern Water District', 'Bakersfield  City Of','Fresno  City Of', 'Chowchilla Water District', 'Madera Irrigation District'] 
  black_butte = ['4-E Water District', 'Stony Creek Water District']
  colusa_basin = ['Colusa Drain Mutual Water Company']
  corning_canal = ['Corning Water District', 'Proberta Water District', 'Thomes Creek Water District']
  tehama_colusa = ['Colusa County Water District', '4-M Water District', 'Cortina Water District', 'Glenn Valley Water District', 'Holthouse Water District', 'La Grande Water District', 'Myers-marsh Mutual Water Company', 'Davis Water District (from USBR)', 'Dunnigan Water Works', 'Glide Water District', 'Kanawha Water District', 'Kirkwood Water District', 'Orland - Artois Water District', 'Westside Water District', 'Feather Water District']
  trinity = ['Centerville Community Services District', 'Mountain Gate Community Services District', 'City of Redding', 'City of Shasta Lake', 'Bella Vista Water District', 'Clear Creek Community Services District', 'Shasta Community Services District']
  folsom_dam = ['El Dorado Irrigation District', 'Roseville', 'Sacramento County Water Agency', 'San Juan Water District', 'Placer County Water Agency']
  folsom_south =  ['East Bay Municipal Utility District', 'Sacramento Municipal Utility District']
  sac_settlement = ['Anderson - Cottonwood Irrigation District', 'Conaway Preservation Group', 'Cranmore Farms', 'Eastside Mutual Water Company', 'Glenn - Colusa Irrigation District', 'Maxwell Irrigation District', 'Meridian Farms Water Company', 'Natomas Central Mutual Water Company', 'Pelger Mutual Water Company', 'Pleasant Grove Verona Municipal Water District', 'Princeton - Codora - Glenn Irrigation District', 'Provident Irrigation District', 'Reclamation District No 1000', 'Reclamation District No 900', 'Reclamation District No 1004', 'Reclamation District No. 108', 'City of Redding', 'Sutter Mutual Water Company', 'Sycamore Family Trust', 'Tisdale Irrigation And Drainage Company', 'West Sacramento']
  sac_settlement_small = ['Alexander  Thomas And Karen',  'Anderson, Arthur Et Al (formerly Westfall, Mary)', 'Anderson, Arthur et al', 'Andreotti, Beverly F., Et Al','Baber, Jack Et Al','Beckley, Ralph And Ophelia', 'Butler, Dianne E.', 'Butte Creek Farms (a)', 'Butte Creek Farms (m)', 'Butte Creek Farms (p)', 'Butte Creek Farms (y)', 'Byrd, Anna C. And Osborne, Jane', 'Cachil Dehe Band Of Wintun Indians', 'Carter Mutual Water Company', 'Chesney, Adona', 'Churkin, Michael And Carol', 'Cummings, William S.', 'Driscoll Strawberry Associates, Inc.', 'Driver, Gary, Et Al', 'Driver, Gregory E.', 'Driver, John A. And Clare M. (1314)', 'Driver, John A. And Clare M. (2398)', 'Driver, William A. Et Al', 'Dyer, Jeffrey E. And Wing-dyer, Jan', 'E. L. H. Sutter Properties',  'Eggleston, Ronald H. And Susan I.', 'Ehrke,  Allen A. And Bonnie E.', 'Exchange Bank (c/o Nature Conservancy)', 'Fedora, Sibley G. And Margaret L.', 'Forry, Laurie E.', 'Furlan, Emile And Simone', 'Gillaspy, William F.', 'Giovannetti', 'Giusti, Richard J. And Sandra A.', 'Gjermann, Hal', 'Gomes, Judith', 'Green Valley Corporation (5210)', 'Green Valley Corporation (5211)', 'Griffin, Joseph, And Prater, Sharon', 'Hale, Judith And Marks, Alice (1638)', 'Hale, Judith And Marks, Alice (7572)', 'Hatfield, R & B', 'Heidrick, Joe Jr.', 'Heidrick, Mildred (1616)', 'Heidrick, Mildred (8322)', 'Henle, Thomas N.', 'Hiatt, Thomas (Haitt Family Trust)', 'Hiatt, Thomas And Illerich, Phillip', 'Howald Farms', 'Howard, Theodore W. And Linda M', 'J.B. Unlimited', 'Jaeger, William L. And Patricia A.', 'Jansen, Peter And Sandy', 'Kary, Carol', 'King, Benjamin And Laura', 'Klsy LLC', 'Knaggs Walnut Ranches', 'Knights Landing Investors', 'Lauppe, Burton And Kathryn (1289)', 'Lauppe, Burton And Kathryn (1364)', 'Leiser, Dorothy L.', 'Leviathan, Inc.', 'Lockett, William And Jean', 'Lomo Cold Storage And Michelli, Justin', 'Lonon, Michael E.', 'MCM Properties', 'Mehrhof, Susan And Montgomery, John', 'Mesquite Investors, LLC And Family Real Property Limited Partnership', 'Meyer Crest', 'Micke, Daniel And Nina', 'Morehead, Joseph A. And Brenda', 'Munson, James T. And Dalmira', 'Natomas Basin Conservancy', 'Nelson, Thomas L. And Hazel M.', 'Nene Ranch', 'Obrien, Frank And Janice', 'Odysseus Farms Partnership', 'Oji Brothers Farm, Inc.', 'Oji, Mitsue, Family Partnership', 'Otterson, Mike (Wells, Joyce)', 'Pacific Realty Associates', 'Penner, Roger And Leona', 'Quad-H Ranches', 'Rauf, Abdul And Tahmina (formerly Forster, R. And J.)', 'Reische, Eric', 'Reische, Laverne', 'Richter, Henry D. Et Al', 'River Garden Farms Company', 'Roberts Ditch Irrigation Company', 'Rubio, Exequiel And Elsa', 'Sacramento River Ranch', 'Seaver, Charles W. And Barbara J.', 'Tarke, Stephen E. And Debra F.', 'Tuttle, Charles W. And Noack, Sue T.', 'Wakida, Tomio (1415)', 'Wakida, Tomio (5200)', 'Wallace, Kenneth L. Living Trust', 'Willey, Edwin A. And Marjorie E.', 'Wilson Ranch Partnership', 'Windswept Land And Livestock Company', 'Wisler, John W. Jr', 'Young, Russel L., Et Al', 'Zelmar Ranch']
  solano_project = ['Solano Irrigation District', 'Maine Prairie Water District', 'Vacaville  City Of' , 'Fairfield  City Of', 'City of Suisun City', 'Vallejo  City Of']
  cache_creek = ['Yolo County Flood Control And Water Conservation District', 'Winters  City Of', 'Davis  City Of', 'Woodland  City Of']
  delta_mendota = ['Banta Carbona Irrigation District', 'Byron Bethany Irrigation District', 'Del Puerto Water District', 'Eagle Field Water District', 'Mercy Springs Water District', 'Ora Loma Water District', 'Pajaro Valley Water Management Agency', 'Santa Clara Valley Water District', 'Westlands Water District', 'Patterson Water District', 'West Side Irrigation District', 'Tracy', 'West Stanislaus Irrigation District']
  mendota_pool = ['Fresno Slough Water District', 'James Irrigation District', 'Laguna Water District', 'Reclamation District No 1606', 'Tranquility Irrigation District']
  cross_valley = ['Hills Valley Irrigation District', 'Kern - Tulare Water District', 'Tri-Valley Water District']
  san_felipe = ['San Benito County Water District Zone 3', 'San Benito County Water District Zone 6', 'Santa Clara Valley Water District']
  san_luis = ['Avenal', 'Coalinga', 'Huron', 'Pacheco Water District', 'Panoche Water District', 'San Luis Water District', 'Westlands Water District']
  exchange = ['Central California Irrigation District', 'Columbia Canal Company', 'Firebaugh Canal Company', 'San Luis Canal Company']
  friant = ['Gravely Ford Water District', 'Arvin - Edison Water Storage District', 'Delano - Earlimart Irrigation District', 'Exeter Irrigation District', 'Fresno Irrigation District', 'Hills Valley Irrigation District', 'Garfield Water District', 'International Water District', 'Ivanhoe Irrigation District', 'Kaweah Delta Water Conservation District', 'Kern - Tulare Water District', 'Lewis Creek Water District', 'Lindmore Irrigation District', 'Lindsay - Strathmore Irrigation District', 'Lower Tule River Irrigation District', 'Orange Cove Irrigation District', 'Porterville Irrigation District', 'Saucelito Irrigation District', 'Shafter - Wasco Irrigation District', 'Southern San Joaquin Municipal Utility District', 'Stone Corral Irrigation District', 'Tea Pot Dome Water District', 'Terra Bella Irrigation District', 'Tri-Valley Water District', 'Tulare Irrigation District', 'Chowchilla Water District', 'Madera Irrigation District']
  delta = ['Contra Costa Water District']
  feather_river = ['Western Canal Water District', 'Richvale Irrigation District', 'Biggs - West Gridley Water District', 'Butte Water District', 'Sutter Extension Water District', 'Oswald WD', 'Feather Water District', 'Tudor Mutual Water Company', 'Garden Highway Mutual Water Company', 'Plumas Mutual Water Company']
  yuba_river = ['Browns Valley Irrigation District', 'Ramirez Water District', 'Cordua Irrigation District', 'Hallwood Irrigation District', 'Brophy Water District', 'South Yuba Water District', 'Dry Creek Mutual Water Company', 'Wheatland Water District', 'Marysville', 'Wheatland City', 'Linda County Water District', 'Olivehurst Public Utilities District', 'North Yuba Water District', 'Camp Far West Irrigation District', 'Plumas Mutual Water Company', 'Reclamation District No 784', 'Reclamation District No 10', 'Reclamation District No 2103', 'Reclamation District No 817', 'Yuba City', 'Nevada Irrigation District', 'South Sutter Water District']
  mokelumne_calaveras = ['Amador Water Agency', 'Calaveras County Water District', 'East Bay Municipal Utility District', 'Calaveras Public Utilities District', 'Jackson Valley Irrigation District', 'Stockton East Water District']
  eastside = ['Central San Joaquin Water Conservation District', 'Oakdale Irrigation District', 'South San Joaquin Irrigation District']
  tuolumne = ['Modesto Irrigation District', 'Turlock Irrigation District', 'San Francisco Public Utilities Comission']
  merced = ['Merced Irrigation District', 'Merquin County Water District', 'Stevinson Water District']
  kings = ['Fresno  City Of', 'Alta Irrigation District', 'Fresno Irrigation District', 'Consolidated Irrigation District', 'Kings River Water District', 'Corcoran Irrigation District', 'Laguna Irrigation District', 'Reed Ditch Company', 'Riverdale Irrigation District', 'Liberty Mill Race Company', 'Burrel Ditch Company', 'Liberty Canal Company', 'Last Chance Creek Water District', 'Lemoore Canal & Irrigation Company', 'John Heinlen Mutual Water Company', 'Reclamation District No 2069', 'Empire West Side Irrigation District',  'Stratford Irrigation District', 'Tulare Lake Basin Water Storage District', 'Reclamation District No 761', 'Crescent Canal Company', 'Stinson Water District', 'James Irrigation District', 'Tranquility Irrigation District']
  kaweah = ['Kaweah Delta Water Conservation District']
  tule = ['Porterville Irrigation District', 'Vandalia Irrigation District', 'Pixley Irrigation District']
  kern = ['North Kern Water Storage District', 'Kern Delta Water District', 'Bakersfield  City Of']
  swp = ['Alameda County Flood Control District', 'Alameda County Water District', 'Antelope Valley - East Kern Water Agency', 'Coachella Valley Water District', 'Crestline - Lake Arrowhead Water Agency', 'Desert Water Agency', 'Dudley Ridge Water District', 'Empire West Side Irrigation District', 'Littlerock Creek Irrigation District', 'Metropolitan Water District Of Southern California', 'Mojave Water Agency', 'Napa County Flood Control and Water Conservation District', 'Oak Flat Water District', 'Palmdale Water District', 'Plumas County Flood Control and Water Conservation District', 'San Bernardino Valley Municipal Water District', 'San Gabriel Valley Municipal Water District', 'San Gorgonio Pass Water Agency', 'San Luis Obispo County Flood Control And Water Conservation District', 'Santa Clarita Valley Water Agency', 'Ventura County Watershed Protection District']
  kcwa = ['Belridge Water Storage District', 'Berrenda Mesa Water District', 'Buena Vista Water Storage District', 'Cawelo Water District', 'Henry Miller Water District', 'Lost Hills Water District', 'Rosedale - Rio Bravo Water Storage District', 'Semitropic Water Service District', 'Tehachapi - Cummings County Water District', 'Tejon - Castac Water District', 'West Kern Water District', 'Wheeler Ridge - Maricopa Water Storage District']
  water_exchange_example_ag = ['Pacheco Water District', 'Panoche Water District', 'San Luis Water District', 'Arvin - Edison Water Storage District']
  water_exchange_example_urban = ['Metropolitan Water District Of Southern California']

  sacramento = []
  for x in black_butte:
    sacramento.append(x)
  for x in colusa_basin:
    sacramento.append(x)
  for x in corning_canal:
    sacramento.append(x)
  for x in tehama_colusa:
    sacramento.append(x)
  for x in trinity:
    sacramento.append(x)
  folsom_tot = []
  for x in folsom_south:
    folsom_tot.append(x)
  for x in folsom_dam:
    folsom_tot.append(x)
  for x in sac_settlement:
    sacramento.append(x)
  for x in sac_settlement_small:
    sacramento.append(x)
  cvp_south = []
  for x in delta_mendota:
    cvp_south.append(x)
  for x in mendota_pool:
    cvp_south.append(x)
  for x in cross_valley:
    cvp_south.append(x)
  for x in san_felipe:
    cvp_south.append(x)
  for x in san_luis:
    cvp_south.append(x)
  for x in exchange:
    cvp_south.append(x)
  for x in delta:
    cvp_south.append(x)
  sj_tribs = []
  for x in eastside:
    sj_tribs.append(x)
  for x in tuolumne:
    sj_tribs.append(x)
  for x in merced:
    sj_tribs.append(x)
  for x in mokelumne_calaveras:
    sj_tribs.append(x)
  tulare_basin = []
  for x in kings:
    tulare_basin.append(x)
  for x in kaweah:
    tulare_basin.append(x)
  for x in tule:
    tulare_basin.append(x)
  for x in kern:
    tulare_basin.append(x)
  swp_tot = []
  for x in swp:
    swp_tot.append(x)
  for x in kcwa:
    swp_tot.append(x)
  sac_tribs_west = []
  for x in solano_project:
    sac_tribs_west.append(x)
  for x in cache_creek:
    sac_tribs_west.append(x)
  cvp_contract_list = [sacramento, feather_river, yuba_river, folsom_tot, sj_tribs, cvp_south, friant, tulare_basin, swp_tot, sac_tribs_west, agricultural_districts, urban_districts, recharge_districts, water_exchange_example_ag, water_exchange_example_urban]
  cvp_contract_names = ['sacramento_districts', 'feather_districts', 'yuba_districts', 'folsom_districts', 'eastside_districts', 'cvp_south_districts', 'friant_districts', 'tulare_districts', 'swp_districts', 'sac_west_districts', 'agricultural_districts', 'urban_districts', 'recharge_districts', 'exchange_example_ag_districts', 'exchange_example_urban_districts']
  district_names = districts['AGENCYNAME']
  sorted_district = sorted(district_names)
  for x, xname in zip(cvp_contract_list, cvp_contract_names):
    new_list_x = []
    for y in x:
      for index, row in districts.iterrows():
        row_name = row['AGENCYNAME']
        if y == row['AGENCYNAME']:
          new_list_x.append(row_name)
        elif y == row_name[0:len(y)]:
          new_list_x.append(row_name)

    new_dict = {}
    new_dict['AGENCYNAME'] = new_list_x
    new_dataFrame = pd.DataFrame(new_dict)
    new_gdf = districts.merge(new_dataFrame, on = 'AGENCYNAME')
    new_gdf.to_file(driver = 'ESRI Shapefile', filename = filename_folder +  xname + '.shp')
    #new_gdf.plot(ax = ax, color = colors_use[color_counter])
    #color_counter += 1

def get_raster_list(figure_type):
  if figure_type == 'total':

    raster_list = {}
    raster_list['001007'] = ['20191102_20191116',]
    raster_list['001008'] = ['20191102_20191116','20191010_20191020']
    raster_list['001009'] = ['20191026_20191101',]
    raster_list['001010'] = ['20191026_20191101',]
  #  raster_list['001011'] = ['20191104_20191117',]
    raster_list['002006'] = ['20190915_20191001','20201003_20201017']
    raster_list['002007'] = ['20191026_20191101','20191102_20191116']
    raster_list['002008'] = ['20191010_20191020','20191104_20191117', '20201003_20201017']
    raster_list['002009'] = ['20191104_20191117','20191026_20191101']
    raster_list['002010'] = ['20191104_20191117','20191028_20191116']
    raster_list['002011'] = ['20191104_20191117','20191012_20191022']
    raster_list['002012'] = ['20200608_20200627','20191113_20191204']
    raster_list['003006'] = ['20190823_20190905',]
    raster_list['003007'] = ['20191104_20191117','20191026_20191101']
    raster_list['003008'] = ['20191111_20191117','20191104_20191117', '20200827_20200907']
    raster_list['003009'] = ['20191028_20191116','20191104_20191117']
    raster_list['003010'] = ['20191028_20191116','20191021_20191101']
    raster_list['003011'] = ['20191106_20191117','20191028_20191116']
    raster_list['003012'] = ['20201007_20201017','20200930_20201016']
    raster_list['004007'] = ['20191104_20191117','20200827_20200907']
    raster_list['004008'] = ['20200912_20200922','20201007_20201017']
    raster_list['004009'] = ['20191028_20191116','20200905_20200921']
    raster_list['004010'] = ['20191106_20191117','20200930_20201016']
    raster_list['004011'] = ['20191106_20191117','20200930_20201016']
    raster_list['004012'] = ['20200930_20201016','20201009_20201017']
    raster_list['004013'] = ['20200930_20201016','20201009_20201017']
    raster_list['005007'] = ['20200921_20201022','20200928_20201016']
    raster_list['005008'] = ['20200921_20201022','20200930_20201016']
    raster_list['005009'] = ['20200921_20201022','20200930_20201016']
    raster_list['005010'] = ['20200930_20201016']
    raster_list['005011'] = ['20200923_20201016', '20200930_20201016']
    raster_list['005012'] = ['20201009_20201017']
    raster_list['005013'] = ['20201009_20201017']

  elif figure_type == 'northerncv':

    raster_list = {}
    raster_list['001007'] = ['20191102_20191116',]
    raster_list['001008'] = ['20191102_20191116','20191010_20191020']
    raster_list['001009'] = ['20191026_20191101',]
  #  raster_list['001010'] = ['20191026_20191101',]
    raster_list['002006'] = ['20190915_20191001',]
    raster_list['002007'] = ['20191026_20191101','20191102_20191116']
    raster_list['002008'] = ['20191010_20191020','20191104_20191117']
    raster_list['002009'] = ['20191104_20191117','20191026_20191101']
  #  raster_list['002010'] = ['20191104_20191117',]
    raster_list['003006'] = ['20190823_20190905',]
    raster_list['003007'] = ['20191104_20191117','20191026_20191101']
    raster_list['003008'] = ['20191111_20191117','20191104_20191117']
    raster_list['003009'] = ['20191028_20191116','20191104_20191117']
  #  raster_list['003010'] = ['20191028_20191116']
    raster_list['004007'] = ['20191104_20191117']
  
  elif figure_type == 'southerncv' or figure_type == 'tulare' or figure_type == 'climate change':
    raster_list = {}
    raster_list['002009'] = ['20191104_20191117','20191026_20191101']
    raster_list['002010'] = ['20191104_20191117','20191028_20191116']
    raster_list['002011'] = ['20191104_20191117','20191012_20191022']
    raster_list['003009'] = ['20191028_20191116','20191104_20191117']
    raster_list['003010'] = ['20191028_20191116','20191021_20191101']
    raster_list['003011'] = ['20191106_20191117','20191028_20191116']
    raster_list['004009'] = ['20191028_20191116']
    raster_list['004010'] = ['20191106_20191117']
    raster_list['004011'] = ['20191106_20191117']

  elif figure_type == 'statewide':

    raster_list = {}
    raster_list['001007'] = ['20191102_20191116',]
    raster_list['001008'] = ['20191102_20191116','20191010_20191020']
    raster_list['001009'] = ['20191026_20191101',]
    raster_list['001010'] = ['20191026_20191101',]
    raster_list['002006'] = ['20190915_20191001','20201003_20201017']
    raster_list['002007'] = ['20191026_20191101','20191102_20191116']
    raster_list['002008'] = ['20191010_20191020','20191104_20191117', '20201003_20201017']
    raster_list['002009'] = ['20191104_20191117','20191026_20191101']
    raster_list['002010'] = ['20191104_20191117','20191028_20191116']
    raster_list['002011'] = ['20191104_20191117','20191012_20191022']
    raster_list['002012'] = ['20200608_20200627','20191113_20191204']
    raster_list['003006'] = ['20190823_20190905',]
    raster_list['003007'] = ['20191104_20191117','20191026_20191101']
    raster_list['003008'] = ['20191111_20191117','20191104_20191117', '20200827_20200907']
    raster_list['003009'] = ['20191028_20191116','20191104_20191117']
    raster_list['003010'] = ['20191028_20191116','20191021_20191101']
    raster_list['003011'] = ['20191106_20191117','20191028_20191116']
    raster_list['004007'] = ['20191104_20191117','20200827_20200907']
    raster_list['004008'] = ['20200912_20200922','20201007_20201017']
    raster_list['004009'] = ['20191028_20191116','20200905_20200921']
    raster_list['004010'] = ['20191106_20191117','20200930_20201016']
    raster_list['004011'] = ['20191106_20191117','20200930_20201016']

  return raster_list

def get_watershed_list():

  watershed_list = {}
  watershed_list['feather'] = ['18020121', '18020122', '18020123', '18020106', '18020159']
  watershed_list['yuba'] = ['18020124', '18020125', '18020107']
  watershed_list['sacramento'] = ['18020101','18020102','18020103','18020104','18020105','18020112','18020113','18020114','18020115','18020118','18020119','18020120', '18020151', '18020152', '18020153','18020154', '18020155', '18020156', '18020157', '18020158', '18020005', '18020002', '18020003', '18020004', '18020001']
  watershed_list['american'] = ['18020128','18020129','18020111']
  watershed_list['sac_delta'] = ['18020126', '18020161','18020162', '18020163', '18020116']
  watershed_list['tuolumne'] = ['18040009',]
  watershed_list['stanislaus'] = ['18040010',]
  watershed_list['merced'] = ['18040008',]
  watershed_list['eastside'] = ['18040011','18040012','18040013','18040003','18040004','18040004','18040051',]
  watershed_list['san_joaquin'] = ['18040006','18040007','18040001','18040002']

  basin_list = ['feather', 'yuba', 'sacramento', 'american', 'sac_delta', 'tuolumne', 'san_joaquin', 'eastside', 'stanislaus', 'merced']
  basin_list_clip = ['feather', 'yuba', 'sacramento', 'american', 'tuolumne', 'stanislaus', 'merced']
  basin_list_clip = ['feather', 'yuba', 'sacramento', 'american', 'sac_delta', 'tuolumne', 'san_joaquin', 'eastside', 'stanislaus', 'merced']
  basin_colors = ['steelblue', 'steelblue', 'steelblue', 'steelblue', 'teal', 'coral', 'indianred', 'forestgreen', 'coral', 'coral']

  return watershed_list, basin_list, basin_list_clip, basin_colors