import pandas as pd
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import geopandas as gpd

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

  elif map_type == 'southerncv':
    box_coordinates = [-121.3, -118.3, 34.85, 37.45]#data_figure.format_plot
    calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts-no-banks', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank']
    calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'teal', 'teal', 'teal', 'steelblue']
    calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'SAN JOAQUIN RIVER', 'TULE RIVER', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']
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


  elif map_type == 'FKC_exp':
    if use_type in ['friant', 'alt1', 'intro-tulare', '1827_median_FKC_CFWB', '537_median_FKC_CFWB', '2454_median_FKC_CFWB', '981_median_FKC_CFWB', 'boxplot_combined', 'sagbi']:
      box_coordinates = [-121.3, -118.3, 34.8, 37.35]#data_figure.format_plot
    else:
      box_coordinates = [-122.7, -118.0, 34.85, 41.0]

    if use_type in ['friant', 'alt1', 'intro-tulare', '1827_median_FKC_CFWB', '537_median_FKC_CFWB', '2454_median_FKC_CFWB', '981_median_FKC_CFWB']:
      if use_type == 'friant':
        calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts_FKC_experiment_default_nonpartners', 'districts_FKC_experiment_default_partners']
        calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'color_defa', 'color_defa']
      # elif use_type == 'alt1':
      #   calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'color_alt1', 'color_alt1']
      elif use_type == '1827_median_FKC_CFWB':
        calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts_FKC_experiment_1827_nonpartners', 'districts_FKC_experiment_1827_partners']
        calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'color_1827', 'color_1827']
      elif use_type == '537_median_FKC_CFWB':
        calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts_FKC_experiment_537_nonpartners', 'districts_FKC_experiment_537_partners']
        calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'color_537', 'color_537']
      elif use_type == '2454_median_FKC_CFWB':
        calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts_FKC_experiment_2454_nonpartners', 'districts_FKC_experiment_2454_partners']
        calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'color_2454', 'color_2454']
      elif use_type == '981_median_FKC_CFWB':
        calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts_FKC_experiment_981_partners', 'districts_FKC_experiment_981_nonpartners']
        calfews_attributes['shapefile_color'] = ['black', 'midnightblue', 'midnightblue', 'midnightblue', 'color_981', 'color_981']
    
    elif use_type == 'boxplot_combined':
      calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts_FKC_experiment_topfriant', 		      'districts_FKC_experiment_topnonfriant', 'districts_FKC_experiment_bottomfriant', 'districts_FKC_experiment_bottomnonfriant']
      calfews_attributes['shapefile_color'] = ['black', 'mediumblue', 'mediumblue', 'mediumblue', 'color_boxp', 'color_boxp', 'color_boxp', 'color_boxp']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface reservoir', markerfacecolor='midnightblue', markersize=6, lw=0),
                      Line2D([0], [0], color='mediumblue', lw=2, label='Natural river'),
                      Line2D([0], [0], color='black', lw=2, label='Canal'),
                      Line2D([0], [0], marker='o', color='black', label='Urban turnout', markerfacecolor='dimgrey', markersize=6, lw=0),
                      Patch(facecolor='#7570b3', edgecolor='#7570b3', alpha=0.7, label='Tier 1 district'),
                      Patch(facecolor='#1b9e77', edgecolor='#1b9e77', alpha=0.7, label='Tier 2 district'),
                      Patch(facecolor='#d95f02', edgecolor='#d95f02', alpha=0.7, label='Tier 3 district'),
                      Patch(facecolor='#c1c1c1', edgecolor='#c1c1c1', alpha=0.7, label='Other district'),
                      Patch(facecolor='none', edgecolor='k', alpha=0.7, hatch='////////', label='Friant contractors'),]   

    elif use_type == 'sagbi':
      calfews_attributes['shapefiles'] = ['drawings-line', 'Tulare_Basin-line', 'San_Joaquin-line', 'kings_ext', 'districts_FKC_experiment_sagbi', '../../../../../../Downloads/sagbi_mod/sagbi_mod_clip']
      calfews_attributes['shapefile_color'] = ['black', 'mediumblue', 'mediumblue', 'mediumblue', 'none','color_sagb']

      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface reservoir', markerfacecolor='midnightblue', markersize=6, lw=0),
                      Line2D([0], [0], color='mediumblue', lw=2, label='Natural river'),
                      Line2D([0], [0], color='black', lw=2, label='Canal'),
                      Line2D([0], [0], marker='o', color='black', label='Urban turnout', markerfacecolor='dimgrey', markersize=6, lw=0),
                      Patch(facecolor='darkgreen', alpha=0.7, label='Excellent'),
                      Patch(facecolor='limegreen', alpha=0.7, label='Good'),
                      Patch(facecolor='yellow', alpha=0.7, label='Moderately good'),
                      Patch(facecolor='orange',  alpha=0.7, label='Moderately poor'),
                      Patch(facecolor='red', alpha=0.7, label='Poor'),
                      Patch(facecolor='darkred', alpha=0.7, label='Very poor')]                  

    elif use_type in ['intro-state', 'intro-tulare']:
      calfews_attributes['shapefiles'] = ['drawings-line', 'Canals_and_Aqueducts_local/canals_abbr',  'Canals_and_Aqueducts_local/kern_cal_aq', 'Canals_and_Aqueducts_local/so_cal_aqueduct-line', 'American_River-line', 'Feather_River-line', 'Sacramento_River-line', 'San_Joaquin_Tributaries-line', 'San_Joaquin-line','Yuba_River-line', 'Delta-line', 'Tulare_Basin-line', 'kings_ext', 'creek_add_ons-line', 'Water_Districts/agricultural_districts', 'Water_Districts/urban_districts', 'Water_Districts/recharge_districts', 'kern_water_bank']
      district_colors = ['indianred', 'silver']
      calfews_attributes['shapefile_color'] = ['black', 'black', 'black', 'black', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'midnightblue', 'indianred', 'goldenrod', 'teal', 'darkorchid']
      legend_elements = [Line2D([0], [0], marker='o', color='black', label='Surface Reservoir', markerfacecolor='bisque', markersize=5, linewidth = 0),
                        Line2D([0], [0], color='midnightblue', lw=2, label='Natural Channel'),
                        Line2D([0], [0], color='black', lw=2, label='Canal'),
                        Line2D([0], [0], marker='o', color='black', label='Urban turnout', markerfacecolor='slategray', markersize=5, lw=0),
                        Patch(facecolor='indianred', edgecolor='black', label='Agricultural\nDistricts'),
                        Patch(facecolor='goldenrod', edgecolor='black', label='Urban Districts'), 
                        Patch(facecolor='teal', edgecolor='black', label='Districts with\nRecharge Facilities'), 
                        Patch(facecolor='darkorchid', edgecolor='black', label='Dedicated\nGroundwater Banks')]

    calfews_attributes['csvfiles'] = ['CALIFORNIA AQUEDUCT', 'KAWEAH RIVER', 'KERN RIVER', 'KINGS RIVER', 'SAN JOAQUIN RIVER', 'TULE RIVER', 'SOUTHBAY', 'CENTRALCA', 'SOUTHERNCA']
    
   
  

  return calfews_attributes, box_coordinates, legend_elements

def get_base_order():
  #which shapefiles go on the bottom
  base_list = ['Water_Districts/sacramento_districts', 'Water_Districts/feather_districts', 'Water_Districts/yuba_districts', 'Water_Districts/folsom_districts', 'Water_Districts/eastside_districts', 'Water_Districts/cvp_south_districts', 'Water_Districts/friant_districts', 'Water_Districts/tulare_districts', 'Water_Districts/swp_districts','Water_Districts/urban_districts','Water_Districts/recharge_districts', 'districts-no-banks', 'districts-no-banks_v2', 'arvin_bank', 'semitropic_bank', 'rosedale_bank', 'kern_water_bank', 'westlands', 'kern_delta', 'Water_Districts/exchange_example_ag_districts', 'Water_Districts/exchange_example_urban_districts']
  no_outline_base_list = ['shorebird_priority_habitat/priority_only', 'Water_Districts/agricultural_districts', 
                          'districts_FKC_experiment_default_partners', 'districts_FKC_experiment_default_nonpartners',
                          'districts_FKC_experiment_1827_partners', 'districts_FKC_experiment_1827_nonpartners',
                          'districts_FKC_experiment_537_partners', 'districts_FKC_experiment_537_nonpartners',
                          'districts_FKC_experiment_2454_partners', 'districts_FKC_experiment_2454_nonpartners',
                          'districts_FKC_experiment_981_partners', 'districts_FKC_experiment_981_nonpartners']
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
  reservoir_color_list['AMERICAN RIVER'] = 'midnightblue'
  reservoir_color_list['SACRAMENTO RIVER'] = 'midnightblue'
  reservoir_color_list['NORTH YUBA RIVER'] = 'midnightblue'
  reservoir_color_list['FEATHER RIVER'] = 'midnightblue'
  reservoir_color_list['STANISLAUS RIVER'] = 'midnightblue'
  reservoir_color_list['TUOLUMNE RIVER'] = 'midnightblue'
  reservoir_color_list['MERCED RIVER'] = 'midnightblue'
  reservoir_color_list['MOKELUMNE RIVER'] = 'midnightblue'
  reservoir_color_list['CALAVERAS RIVER'] = 'midnightblue'
  reservoir_color_list['TUOLUMNE RIVER 2'] = 'midnightblue'
  reservoir_color_list['CACHE CREEK'] = 'midnightblue'
  reservoir_color_list['PUTAH CREEK'] = 'midnightblue'
  reservoir_color_list['SACRAMENTO'] = 'midnightblue'
  reservoir_color_list['NORTH YUBA'] = 'midnightblue'
  reservoir_color_list['FEATHER'] = 'midnightblue'
  reservoir_color_list['STANISLAUS'] = 'midnightblue'
  reservoir_color_list['TUOLUMNE'] = 'midnightblue'
  reservoir_color_list['MERCED'] = 'midnightblue'
  reservoir_color_list['SACDELTA'] = 'midnightblue'
  reservoir_color_list['SJDELTA'] = 'midnightblue'
  reservoir_color_list['SAN JOAQUIN RIVER'] = 'midnightblue'
  reservoir_color_list['KINGS RIVER'] = 'midnightblue'
  reservoir_color_list['KAWEAH RIVER'] = 'midnightblue'
  reservoir_color_list['TULE RIVER'] = 'midnightblue'
  reservoir_color_list['KERN RIVER'] = 'midnightblue'
  reservoir_color_list['CALIFORNIA AQUEDUCT'] = 'midnightblue'
  reservoir_color_list['DELTA'] = 'black'
  reservoir_color_list['SOUTHERNCA'] = 'dimgrey'
  reservoir_color_list['CENTRALCA'] = 'dimgrey'
  reservoir_color_list['SOUTHBAY'] = 'dimgrey'
  reservoir_color_list['OUT OF BOX'] = 'dimgrey'
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

  #filter list of southern california canals
  canals_la = gpd.read_file(project_folder + '/CALFEWS_shapes/Streams and Rivers/geo_export_ba240352-6e45-4a4c-a975-fed0666ee0c3.shp')
  canals_la = canals_la[canals_la['hydrograph'].isnull()]
  list_of_canals = ['Canal/Ditch: Canal/Ditch Type = Aqueduct', 'Underground Conduit', 'Pipeline: Pipeline Type = Aqueduct; Relationship to Surface = At or Near', 'Pipeline: Pipeline Type = General Case; Relationship to Surface = Underground', 'Artificial Patch', 'Pipeline: Pipeline Type = Siphon', 'Connector', 'Pipeline: Pipeline Type = General Case', 'Pipeline: Pipeline Type = General Case; Relationship to Surface = Underwater', 'Pipeline: PipelineType = Penstock; Relationship to Surface = Underground', 'Pipeline', 'Pipeline: Pipeline Type = Aqueduct', 'Pipeline: Pipeline Type = Penstock; Relationship to Surface = At or Near', 'Pipeline: Pipeline Type = Aqueduct; Relationship to Surface = Underground', 'Canal/Ditch']
  #generate new canal list only of the above types
  new_list_x = []
  for index, row in canals_la.iterrows():
    for x in list_of_canals:
      if row['descriptio'] == x:
        new_list_x.append(row['comid'])
  new_dict = {}
  new_dict['comid'] = new_list_x
  new_dataFrame = pd.DataFrame(new_dict)
  new_gdf = canals_la.merge(new_dataFrame, on = 'comid')
  new_gdf.to_file(driver = 'ESRI Shapefile', filename = project_folder +  '/CALFEWS_shapes/Canals_and_Aqueducts_local/la_canals.shp')

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
  
  elif figure_type == 'southerncv':
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