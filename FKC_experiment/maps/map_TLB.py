import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
# from shapely.geometry import Point, Polygon, LineString, MultiLineString
# from shapely.ops import split, linemerge
import geopandas as gpd
# import fiona
from matplotlib.colors import ListedColormap
from matplotlib.colors import Normalize
import matplotlib.pylab as pl
from matplotlib import cm, rcParams
# import rasterio
# import rasterio.plot
# from osgeo import gdal, osr, ogr, gdalnumeric
from mapper import Mapper
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
# import seaborn as sns
import cropping_main
from preprocessor import create_shape_lists, create_reservoir_file, divide_districts, get_raster_list, get_watershed_list, get_base_order
from platform import uname
import contextily as cx

### check if in WSL (for Andrew) and if so, add font location
if 'Microsoft' in uname().release:
  import matplotlib.font_manager as font_manager
  font_dirs = ['/mnt/c/Windows/Fonts/', ]
  font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
  font_list = font_manager.createFontList(font_files)
  font_manager.fontManager.ttflist.extend(font_list)

## set default font type/size
rcParams['font.family'] = 'Arial'
rcParams.update({'font.size': 8})
rcParams['hatch.linewidth'] = 0.5

#figure 'style' (figure type and use type) - see preprocessor.py for details
#figure_type list: [total, statewide, cv, northerncv, southerncv, sacramento, sanjoaquin, tulare]
figure_type = 'FKC_exp'
use_type = 'sagbi'  ### FKC_exp use_types- intro-tulare, friant, alt1, 1827_median_FKC_CFWB, 2454_median_FKC_CFWB, 537_median_FKC_CFWB, 981_median_FKC_CFWB, boxplot_combined, sagbi
#local data folder name
project_folder = 'ca_geo'
projection_string = 'EPSG:4326'#project raster to data projection
projection_num = 4326
point_location_filename = project_folder + '/CALFEWS_RESERVOIRS.csv'#coordinates of map 'points'
shapefile_folder = project_folder + '/CALFEWS_shapes/'
districts_folder = project_folder + '/CALFEWS_shapes/Water_Districts/'
canal_folder = project_folder + '/CALFEWS_shapes/Canals_and_Aqueducts_local/'
raster_folder = project_folder + '/ca_satellite/'
outline_name = project_folder + '/CALFEWS_shapes/states.shp'#state outline

#create shapefiles from the aggregated districts & canals shapefiles from the State of California (these are already created so its commented out)
#divide_districts(districts_folder, canal_folder, project_folder)


#set up info to load satellite backgrounds
raster_name_pt1 = 'LC08_CU_'
raster_name_pt2 = '_C01_V01_SR'
raster_band_list = ['B4', 'B3', 'B2']
projection_string = 'EPSG:4326'#project raster to data projection
watershed_list, basin_list, basin_list_clip, basin_colors = get_watershed_list()
# raster_list = get_raster_list(figure_type)

#initialize map figure
data_figure = Mapper()
#plot satellite raster layers (photos + layer for the ocean) - comment this out if using alternative background
#data_figure.load_batch_raster(raster_folder, raster_list, raster_name_pt1, raster_name_pt2, raster_band_list, projection_string, upscale_factor = 0.5)
#data_figure.load_single_bands(project_folder, '/CALFEWS_shapes/bathymetry/bathymetry', projection_string)

#Plot state outline
outline_shape = gpd.read_file(outline_name)
data_figure.plot_scale(outline_shape, 'none', type = 'polygons', solid_color = 'none', linewidth_size = 1.0, zorder = 1, outline_color = 'silver')

#get shapefiles & points to plot
figure_attributes, box_coordinates, legend_elements = create_shape_lists(figure_type, use_type)

#get map point locations (i.e., reservoirs, flow gauges)
reservoir_shapefile, reservoir_colors = create_reservoir_file(figure_attributes['csvfiles'], point_location_filename)


#set bounding coordiates from map
lx = box_coordinates[0]
rx = box_coordinates[1]
by = box_coordinates[2]
ty = box_coordinates[3]

#plot point locations
counter = 0
for index, row in reservoir_shapefile.iterrows():
  current_watershed = reservoir_shapefile.loc[[index]] 
  data_figure.plot_scale(current_watershed, 'none', type = 'points', solid_color = reservoir_colors[counter], markersize_use = 40.0, solid_alpha = 1.0, zorder = 6)
  counter += 1

#plot shapefiles
base_list, no_outline_base_list, no_outline_list = get_base_order()
for shapefile_name, shapefile_color in zip(figure_attributes['shapefiles'], figure_attributes['shapefile_color']):
  shape_filename = shapefile_folder + shapefile_name + '.shp'
  shapes = gpd.read_file(shape_filename)
  #shapes.fillna(0.0, inplace = True)
  shapes['geometry'] = shapes['geometry'].to_crs(epsg = projection_num)

  if shapefile_name in base_list:
    zorder_int = 2
    lw = 0.5
    outline_color = 'slategray'
    solid_alpha = 1.0
    hatch = ''
  elif shapefile_name in no_outline_base_list:
    zorder_int = 2
    lw = 1
    outline_color = shapefile_color
    solid_alpha = 0.7
    hatch = ''
  elif shapefile_name in no_outline_list:
    zorder_int = 5
    lw = 0.075
    outline_color = shapefile_color
    solid_alpha = 1.0
    hatch = ''
  elif shapefile_name == 'districts_FKC_experiment_topfriant':
    zorder_int = 4
    lw = 0.5
    outline_color = shapefile_color
    solid_alpha = 0.7
    hatch = '////////'
  elif shapefile_name == 'districts_FKC_experiment_topnonfriant':
    zorder_int = 3
    lw = 0.5
    outline_color = shapefile_color
    solid_alpha = 0.7
    hatch = ''
  elif shapefile_name == 'districts_FKC_experiment_bottomfriant':
    zorder_int = 2
    lw = 0.5
    outline_color = shapefile_color
    solid_alpha = 0.7
    hatch = '////////'
  elif shapefile_name == 'districts_FKC_experiment_bottomnonfriant':
    zorder_int = 1
    lw = 0.5
    outline_color = shapefile_color
    solid_alpha = 0.7	
    hatch = ''
  elif shapefile_name == 'districts_FKC_experiment_sagbi':
    zorder_int = 2
    lw = 0.5
    outline_color = 'k'
    solid_alpha = 0.7	
    hatch = ''
  elif shapefile_name == '../../../../../../Downloads/sagbi_mod/sagbi_mod_clip':
    zorder_int = 1
    lw = 0.
    outline_color = 'none'
    solid_alpha = 0.6
    hatch = ''    
  else:
    zorder_int  = 5
    lw = 1
    outline_color = shapefile_color
    solid_alpha = 1.0
    hatch = ''
  data_figure.plot_scale(shapes, 'none', type = 'polygons', solid_color = shapefile_color, outline_color = outline_color, linewidth_size = lw, zorder = zorder_int, solid_alpha = solid_alpha, hatch = hatch)

if figure_type == 'total' and use_type == 'crop_groups':
  shapefile_name = project_folder + '/CALFEWS_shapes/plsnet/plsnet.shp'
  acreage_files = project_folder + '/CALFEWS_shapes/calPIP_PUR_crop_acreages'
  ag_groups = cropping_main.find_cropping(2012, shapefile_name, acreage_files)
  for x in range(1, 5):
    sub_group = ag_groups[ag_groups['CROPGROUP'] == x]
    data_figure.plot_scale(sub_group, 'none', type = 'polygons', solid_color = calfews_attributes['shapefile_color'][x-1], outline_color = calfews_attributes['shapefile_color'][x-1], linewidth_size = 0, zorder = 1, solid_alpha = 0.6) 

if figure_type == 'total' and use_type == 'groundwater':
    sagbi = gpd.read_file(project_folder + '/CALFEWS_shapes/sagbi_unmod/sagbi_unmod.shp')
    sagbi = sagbi.to_crs(epsg = 4326)
    data_figure.plot_scale(sagbi, 'sagbi', type = 'polygons', solid_color = 'scaled', log_toggle = 2, alpha_scaled = 0.6)


###LABEL PLOT#####
##For each plot type, there are legend elements and also free-floating labels
##legend elements are set in preprocessor.py
##free-floating labels are set here

reservoir_labels = pd.read_csv(point_location_filename)
longitude = 'LONG'
latitude = 'LAT'
label = 'STATION'
name = 'NAME'

if figure_type == 'total':
  leg_loc = 'upper right'

elif figure_type == 'statewide':
  if use_type == 'paper':
    leg_loc = 'upper right'
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML', 'DNP', 'EXC', 'RIO', 'VER']
    offset_x_list = [0.1, -0.75, 0.1, 0.1, 0.1, 0.1, -0.7, -0.6]
    offset_y_list = [0.0, 0.12, 0.0, 0.0, 0.0, -0.05, 0.05, -0.25]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL', 'MIL', 'PFT', 'KWH', 'TLR', 'ISB', 'PCH', 'LAP', 'EDM', 'CAA', 'FKC', 'YRS','HRO/TRP']
    label_name_big = ['SAN LUIS', 'MILLERTON', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston Pumping Plant', 'California\nAqueduct', 'Friant-Kern\nCanal', 'NEW\nBULLARDS\nBAR', 'Delta\nPumps']
    offset_x_list = [0.1, 0.025, 0.1, 0.1, 0.1, -0.4, -0.75, -1.2, -2.2, -0.725, -0.8, 0.0, -0.55]
    offset_y_list = [0.0, 0.09, 0.0, 0.0, 0.0, 0.1, -0.175, -0.1, -0.05, -0.025, 0.45, 0.15, -0.15]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)


  elif use_type == 'projects1':
    leg_loc = 'upper right'

  elif use_type == 'projects2' or use_type == 'projects6':
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML']
    offset_x_list = [0.1, 0.1, 0.1, 0.1, 0.1]
    offset_y_list = [0.0, 0.0, 0.0, 0.0, 0.0]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL', 'MIL', 'PCH', 'LAP', 'EDM', 'CAA', 'FKC', 'HRO/TRP']
    label_name_big = ['SAN LUIS', 'MILLERTON', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston Pumping Plant', 'California\nAqueduct', 'Friant-Kern\nCanal', 'Delta\nPumps']
    offset_x_list = [0.1, 0.025,  -0.75, -1.2, -2.2, -0.725, 0.15, -0.55]
    offset_y_list = [0.0, 0.09,  -0.175, -0.1, -0.05, -0.025, 0.45, -0.15]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'upper right'

  elif use_type == 'projects3':
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML']
    offset_x_list = [0.1, 0.1, 0.1, 0.1, 0.1]
    offset_y_list = [0.0, 0.0, 0.0, 0.0, 0.0]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL', 'MIL', 'PCH', 'LAP', 'EDM', 'CAA', 'FKC', 'HRO/TRP']
    label_name_big = ['SAN LUIS', 'MILLERTON', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston Pumping Plant', 'California\nAqueduct', 'Friant-Kern\nCanal', 'Delta\nPumps']
    offset_x_list = [0.1, 0.025,  -0.75, -1.2, -2.2, -0.725, 0.15, -0.55]
    offset_y_list = [0.0, 0.09,  -0.175, -0.1, -0.05, -0.025, 0.45, -0.15]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'upper right'

  elif use_type == 'projects4' or use_type == 'projects5':
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML', 'DNP', 'EXC']
    offset_x_list = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    offset_y_list = [0.0, 0.0, 0.0, 0.0, 0.0, -0.1]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL', 'MIL', 'PCH', 'LAP', 'EDM', 'CAA', 'HRO/TRP', 'PFT', 'KWH', 'TLR', 'ISB', 'YRS']
    label_name_big = ['SAN LUIS', 'MILLERTON', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston Pumping Plant', 'California\nAqueduct', 'Delta\nPumps', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA', 'NEW\nBULLARDS\nBAR']
    offset_x_list = [0.1, 0.025,  -0.75, -1.2, -2.2, -0.725, -0.55, 0.1, 0.1, 0.1, -0.4, 0.1]
    offset_y_list = [0.0, 0.09,  -0.175, -0.1, -0.05, -0.025, -0.15, 0.0, 0.0, 0.0, 0.1, -0.4]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'upper right'
    
  elif use_type == 'projects7':
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML', 'DNP', 'EXC']
    offset_x_list = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    offset_y_list = [0.0, 0.0, 0.0, 0.0, 0.0, -0.1]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL', 'HRO/TRP', 'YRS']
    label_name_big = ['SAN LUIS', 'Delta\nPumps', 'NEW\nBULLARDS\nBAR']
    offset_x_list = [-0.9, -0.55, 0.1]
    offset_y_list = [0.075, -0.15, -0.4]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'upper right'

  elif use_type == 'projects8':
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML', 'DNP', 'EXC']
    offset_x_list = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    offset_y_list = [0.0, 0.0, 0.0, 0.0, 0.0, -0.1]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL','MIL', 'PCH', 'LAP', 'EDM', 'CAA', 'HRO/TRP', 'PFT', 'KWH', 'TLR', 'ISB', 'YRS']
    label_name_big = ['SAN LUIS',  'MILLERTON', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston Pumping Plant', 'California\nAqueduct', 'Delta\nPumps', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA', 'NEW\nBULLARDS\nBAR']
    offset_x_list = [-0.9, 0.025,  -0.75, -1.2, -2.2, -0.725, -0.55,  0.1, 0.1, 0.1, -0.4, 0.1]
    offset_y_list = [0.075, 0.09,  -0.25, -0.1, -0.05, -0.025, -0.15,  0.0, 0.0, 0.0, 0.1, -0.4]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'upper right'

  elif use_type == 'projects9':
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML', 'DNP', 'EXC']
    offset_x_list = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    offset_y_list = [0.0, 0.0, 0.0, 0.0, 0.0, -0.1]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL','MIL', 'PCH', 'LAP', 'EDM', 'CAA', 'HRO/TRP', 'PFT', 'KWH', 'TLR', 'ISB', 'YRS']
    label_name_big = ['SAN LUIS',  'MILLERTON', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston Pumping Plant', 'California\nAqueduct', 'Delta\nPumps', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA', 'NEW\nBULLARDS\nBAR']
    offset_x_list = [-0.9, 0.025,  -0.75, -1.2, -2.2, -0.725, -0.55,  0.1, 0.1, 0.1, -0.4, 0.1]
    offset_y_list = [0.075, 0.09,  -0.25, -0.1, -0.05, -0.025, -0.15,  0.0, 0.0, 0.0, 0.1, -0.4]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'upper right'

  elif use_type == 'projects10':
    label_list_big = ['SHA', 'ORO', 'FOL', 'NML', 'DNP', 'EXC']
    offset_x_list = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    offset_y_list = [0.0, 0.0, 0.0, 0.0, 0.0, -0.1]
    for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
    label_list_big = ['SNL','MIL', 'PCH', 'LAP', 'EDM', 'CAA', 'HRO/TRP', 'PFT', 'KWH', 'TLR', 'ISB', 'YRS']
    label_name_big = ['SAN LUIS',  'MILLERTON', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston Pumping Plant', 'California\nAqueduct', 'Delta\nPumps', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA', 'NEW\nBULLARDS\nBAR']
    offset_x_list = [-0.9, 0.025,  -0.75, -1.2, -2.2, -0.725, -0.55,  0.1, 0.1, 0.1, -0.4, 0.1]
    offset_y_list = [0.075, 0.09,  -0.25, -0.1, -0.05, -0.025, -0.15,  0.0, 0.0, 0.0, 0.1, -0.4]
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'upper right'


if figure_type == 'northerncv':
  watershed_file = '/CALFEWS_shapes/CA_HUC08/wbdhu8_a_ca.shp'
  clipper_file = '/CALFEWS_shapes/pp1766_cvhm_texture_regions/cvhm_texture_regions.shp'
  data_figure.load_watersheds(project_folder + watershed_file, project_folder + clipper_file, watershed_list, basin_list, basin_colors, basin_list_clip, 1) 
  label_list_big = ['SHA', 'ORO', 'FOL', 'YRS', 'NML', 'DNP', 'EXC', 'RIO', 'VER', 'HRO/TRP', 'CRS', 'GRL', 'LGN', 'OBB', 'MRY', 'WLK']
  offset_x_list = [0.0, 0.0, 0.0, 0.0, -0.275, -0.23, -0.25, -0.45, -0.3, -0.65, -0.325, -0.35, -0.55, -0.65, 0.075, -0.7]
  offset_y_list = [0.075, 0.05, 0.075, 0.05, 0.075, 0.075, -0.125, 0.05, -0.125, 0.05, 0.05, 0.05, -0.015, 0.075, -0.05, 0.05]
  for label_name, offset_x, offset_y in zip(label_list_big, offset_x_list, offset_y_list):
    label_list = []
    label_list.append(label_name)
    data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y)
  leg_loc = 'upper right'

elif figure_type == 'southerncv':
  label_list_big = ['SNL', 'MIL', 'PFT', 'KWH', 'TLR', 'ISB', 'PCH', 'LAP', 'EDM', 'SMI', 'RRB', 'KWB', 'AWD', 'CAA', 'FKC', 'SJR', 'KIN', 'KAW', 'TUL', 'KER']
  label_name_big = ['SAN LUIS', 'MILLERTON', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA', 'Pacheco\nTunnel', 'Las Perillas\nPumping Plant', 'Edmonston\nPumping Plant', 'Semitropic\nWSD', 'Rosedale-Rio\nBravo WSD', 'Kern Water\nBank', 'Arvin-Edison\nWSD', 'California\nAqueduct', 'Friant-Kern\nCanal', 'San Joaquin\nRiver', 'Kings\nRiver', 'Kaweah\nRiver', 'Tule\nRiver', 'Kern\nRiver']
  offset_x_list = [0.025, 0.025, 0.025, 0.025, 0.025, -0.25, -0.09, -0.525, 0.05, -0.125, -0.24, 0.05, 0.0, -0.2, -0.05, -0.2, -0.15, -0.15, -0.05, -0.15]
  offset_y_list = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, -0.175, 0.0, -0.05, -0.025, -0.025, -0.035, 0.05, 0.0, 0.15, 0.025, 0.0, -0.05, 0.07, -0.025]
  for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
    label_list = []
    label_list.append(label_name)
    data_figure.label_plot(figure_type, use_type, figure_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
  leg_loc = 'lower left'


elif figure_type == 'FKC_exp':
  if use_type in ['friant', 'alt1', 'intro-tulare', '1827_median_FKC_CFWB', '537_median_FKC_CFWB', '2454_median_FKC_CFWB', '981_median_FKC_CFWB', 'boxplot_combined', 'sagbi']:
    label_list_big = ['SNL', 'MIL', 'PFT', 'KWH', 'TLR', 'ISB', 'PCH', 'LAP', 'EDM', 'SJR', 'KIN', 'KAW', 'TUL', 'KER']
    label_name_big = ['San Luis Reservoir', 'Millerton\nLake', 'Pine Flat\nLake', 'Lake\nKaweah', 'Lake\nSuccess', 'Lake\nIsabella', 'Pacheco\nTunnel', 'Las\nPerillas\nPumping\nPlant', 
                      'Edmonston\nPumping\nPlant', 'San Joaquin\nRiver', 'Kings\nRiver', 
                      'Kaweah River', 'Tule River', 'Kern\nRiver']
    offset_x_list = [0.055, 0.025, 0.025, 0.05, 0.05, -0.15, -0.09, -0.38, 
                    0.01, -0.32, -0.24, 
                    -0.33, -0.58, -0.2]
    offset_y_list = [-0.0, -0.03, -0.04, -0.05, -0.05, 0.05, -0.19, -0.09,
                    -0.06,  0.03, -0.02, 
                    -0.12, -0.00, -0.02]    
    for label_name, offset_x, offset_y, label_writing in zip(label_list_big, offset_x_list, offset_y_list, label_name_big):
      label_list = []
      label_list.append(label_name)
      data_figure.label_plot(figure_type, use_type, reservoir_labels, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = label_writing)
    leg_loc = 'lower left'
  else:
    leg_loc = 'upper right'


if use_type == 'land_use':
  legend_text_size = 7.5
elif use_type == 'groundwater' or use_type == 'crop_groups' or use_type == 'wetlands':
  legend_text_size = 8.5
elif figure_type == 'FKC_exp':
  legend_text_size = 8
else:
  legend_text_size = 6
  

data_figure.format_plot(xlim = (lx, rx), ylim = (by, ty), legend_description = legend_elements, legend_location = leg_loc, legend_text_size = legend_text_size)
box_lim_x = (lx, rx)
box_lim_y = (by, ty)
inset_lim_x = (-125, -117)
inset_lim_y = (31, 44)
shapefile_name = project_folder + '/CALFEWS_shapes/states.shp'
#if use_type == 'land_use' or use_type == 'groundwater':
data_figure.add_inset_figure(shapefile_name, box_lim_x, box_lim_y, inset_lim_x, inset_lim_y, figure_type, use_type)

if figure_type == 'FKC_exp' or use_type=='land_use':
  ## add basemap
  cx.add_basemap(ax = data_figure.ax, crs=shapes['geometry'].crs)

#plt.savefig(project_folder + '/finished_maps/' + figure_type + '_' + use_type + '_1800.png', dpi = 1800, bbox_inches = 'tight', pad_inches = 0.0)
plt.savefig('finished_maps/' + figure_type + '_' + use_type + '_300.png', dpi = 300, bbox_inches = 'tight', pad_inches = 0.0)
plt.show()
