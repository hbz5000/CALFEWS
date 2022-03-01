import numpy as np 
import matplotlib.pyplot as plt
from osgeo import gdal
import rasterio
from shapely.geometry import Point, Polygon, LineString
import geopandas as gpd
from matplotlib.colors import ListedColormap
import matplotlib.pylab as pl
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

class Mapper():

  def __init__(self, nr = 1, nc = 0):
    self.sub_rows = nr
    self.sub_cols = nc
    if self.sub_cols == 0:
      self.fig, self.ax = plt.subplots(self.sub_rows)
      if self.sub_rows == 1:
        self.type = 'single'
        self.ax.grid(False)
      else:
        self.type = '1d'
    else:
      self.fig, self.ax = plt.subplots(self.sub_rows, self.sub_cols, figsize=(3,3)) #, figsize=(8,8))
      self.type = '2d'
    self.band_min = np.ones(3)*(-1.0)
    self.band_max = np.ones(3)*(-1.0)
    self.brightness_adj = 2.0

  def load_sat(self, raster_name, pixel_bounds, projection_string, upscale_factor = 'none', nr = 1, nc = 0):
    ds = gdal.Open(raster_name + '.tif')
    #geotransform - tells you where pixel 0 (x,y) is in the coordinate system and the scale of pixels to coordinates
    geotransform = ds.GetGeoTransform()
    ##clip the raster - note: this is done in UTM coordinates before projection
    ##so that you don't need to re-project entire contiguous US
    clip_name = raster_name + '_clipped.tif'
    ds = gdal.Translate(clip_name, ds, projWin = [geotransform[0] + 400*geotransform[1], geotransform[3] + 200*geotransform[5], geotransform[0] + 2500*geotransform[1], geotransform[3] +1200*geotransform[5]])
    output_name = raster_name + '_projected.tif'
    ##re-project raster from UTM to LAT/LONG
    gdal.Warp(output_name, ds, dstSRS = 'EPSG:4326')
    raster = rasterio.open(output_name)
    ###read RGB bands of raster

    # resample data to target shape
    # scale image transform
    b = raster.read()

    ##put bands into RGB order
    image = rasterio.plot.reshape_as_image(b)
    ##give coordinates of image bands
    spatial_extent = rasterio.plot.plotting_extent(raster)
    ##plot image
    if self.type == 'single':
      self.ax.imshow(image, extent = spatial_extent)
    elif self.type == '1d':
      self.ax[nr].imshow(image, extent = spatial_extent)
    elif self.type == '2d':
      self.ax[nr][nc].imshow(image, extent = spatial_extent)
	  
  def load_shapefile_solid(self, shapefile_name, alpha_shp, color_shp, clip_list, nr = 1, nc = 0):
    map_shape = gpd.read_file(shapefile_name)
    map_shape['geometry'] = map_shape['geometry'].to_crs(epsg = 4326)
    if clip_list != 'None':
      map_shape = map_shape[map_shape[clip_list[0]] == clip_list[1]]	  
    
    if self.type == 'single':
      map_shape.plot(ax=self.ax, color = color_shp, alpha = alpha_shp)
    elif self.type == '1d':
      map_shape.plot(ax=self.ax[nr], color = color_shp, alpha = alpha_shp)
    elif self.type == '2d':
      map_shape.plot(ax=self.ax[nr][nc], color = color_shp, alpha = alpha_shp)

  def load_watersheds(self, shapefile_name, clipper_name, watershed_list, basin_lists, basin_colors, basin_list_clip, zorder):
    map_shape = gpd.read_file(shapefile_name)
    map_shape_base = gpd.read_file(clipper_name)
    map_shape['geometry'] = map_shape['geometry'].to_crs(epsg = 4326)
    map_shape_base['geometry'] = map_shape_base['geometry'].to_crs(epsg = 4326)

    for index2, row2 in map_shape.iterrows():
      for x, y in zip(basin_lists, basin_colors):
        for xx in watershed_list[x]:
          if row2.HUC8 == xx:
            map_shape_clip = map_shape[map_shape['HUC8'] == row2.HUC8]
            if x in basin_list_clip:
              map_shape_union = gpd.overlay(map_shape_clip, map_shape_base, how='intersection')
              map_shape_union.plot(ax = self.ax, facecolor = y,  alpha = 0.6, edgecolor = 'none', zorder = zorder)
            else:
              map_shape_clip.plot(ax = self.ax, facecolor = y,  alpha = 0.6, edgecolor = 'none', zorder = zorder)

  def plot_scale(self, values, key, type = 'points', value_lim = 'None', solid_color = 'scaled', outline_color = 'black', solid_alpha = 0.8, linewidth_size = 0.2, nr = 0, nc = 0, log_toggle = 0, markersize_use = 2.0, zorder = 1, alpha_scaled = 0.9, hatch=''):
    if solid_color == 'none':
      if type == 'points':
        if self.type == 'single':
          values.plot(ax = self.ax, facecolor = 'none', edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder, alpha = solid_alpha)
        elif self.type == '1d':      
          values.plot(ax = self.ax[nr], facecolor = 'none', edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder, alpha = solid_alpha)
        elif self.type == '2d':      
          values.plot(ax = self.ax[nr][nc], facecolor = 'none', edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder, alpha = solid_alpha)
      elif type == 'polygons':
        if self.type == 'single':
          values.plot(ax = self.ax, facecolor = 'none', edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder, alpha = solid_alpha)
        elif self.type == '1d':      
          values.plot(ax = self.ax[nr], facecolor = 'none', edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder, alpha = solid_alpha)
        elif self.type == '2d':      
          values.plot(ax = self.ax[nr][nc], facecolor = 'none', edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder, alpha = solid_alpha)
    elif solid_color == 'scaled':
      float_num = values[key].notnull()
      all_val = values[key]
      print(np.min(all_val[float_num]))
      print(np.max(all_val[float_num]))
      if value_lim == 'None':
        value_lim = (min(values[key]), max(values[key]))
    
      if np.min(all_val[float_num]) < 0.0 and np.max(all_val[float_num]) > 0.0:
        if log_toggle == 1:
          cmap = pl.cm.Reds
        else:
          cmap = pl.cm.spring
      elif log_toggle == 2:
        cmap = pl.cm.RdYlBu
      else:
        cmap = pl.cm.Reds
      my_cmap = cmap(np.arange(cmap.N))
      my_cmap[:,-1] = np.linspace(alpha_scaled, 1, cmap.N)
      my_cmap = ListedColormap(my_cmap)

      if type == 'points':
        if self.type == 'single':
          values.plot(ax = self.ax, column = key, cmap = my_cmap, marker = 'o', markersize = 2.5, vmin = value_lim[0], vmax = value_lim[1])
        elif self.type == '1d':      
          values.plot(ax = self.ax[nr], column = key, cmap = my_cmap, marker = 'o', markersize = 0.5, vmin = value_lim[0], vmax = value_lim[1])
        elif self.type == '2d':      
          values.plot(ax = self.ax[nr][nc], column = key, cmap = my_cmap, marker = 'o', markersize = 0.5, vmin = value_lim[0], vmax = value_lim[1])
      elif type == 'polygons':
        if self.type == 'single':
          values.plot(ax = self.ax, column = key, cmap = my_cmap, vmin = value_lim[0], vmax = value_lim[1], edgecolor = 'none', linewidth = 0.0)
        elif self.type == '1d':      
          values.plot(ax = self.ax[nr], column = key, cmap = my_cmap, vmin = value_lim[0], vmax = value_lim[1])
        elif self.type == '2d':      
          values.plot(ax = self.ax[nr][nc], column = key, cmap = my_cmap, vmin = value_lim[0], vmax = value_lim[1])
    elif solid_color in ['color_fria', 'color_alt1', 'color_1827', 'color_537', 'color_2454', 'color_981', 'color_defa', 'color_boxp', 'color_sagb']:
      try:
        ### have to plot twice to get black hatch then override edge color
        values.plot(ax = self.ax, color = values[solid_color], alpha = solid_alpha, edgecolor = 'k', linewidth = linewidth_size, zorder = zorder, hatch=hatch)
        values.plot(ax = self.ax, color = 'none', alpha = solid_alpha, edgecolor = values[outline_color], linewidth = linewidth_size, zorder = zorder)
      except:
        values.plot(ax = self.ax, color = values[solid_color], alpha = solid_alpha, edgecolor = 'k', linewidth = linewidth_size, zorder = zorder, hatch=hatch)
        values.plot(ax = self.ax, color = 'none', alpha = solid_alpha, edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder)

    
    
    else:
      if type == 'points':
        if self.type == 'single':
          values.plot(ax = self.ax, color = solid_color, edgecolor = 'black', alpha = solid_alpha, marker = 'o', markersize = markersize_use, zorder = zorder)
        elif self.type == '1d':      
          values.plot(ax = self.ax[nr], color = solid_color, edgecolor = 'black', alpha = solid_alpha, marker = 'o', markersize = markersize_use)
        elif self.type == '2d':      
          values.plot(ax = self.ax[nr][nc], color = solid_color, edgecolor = 'black', alpha = solid_alpha, marker = 'o', markersize = markersize_use)
      elif type == 'polygons':
        if self.type == 'single':
          if solid_color == 'default':
            values.plot(ax = self.ax)
          else:
            values.plot(ax = self.ax, color = solid_color, alpha = solid_alpha, edgecolor = outline_color, linewidth = linewidth_size, zorder = zorder)
        elif self.type == '1d':      
          values.plot(ax = self.ax[nr], color = solid_color, alpha = solid_alpha)
        elif self.type == '2d':      
          values.plot(ax = self.ax[nr][nc], color = solid_color, alpha = solid_alpha)
    
  def format_plot(self, xlim = 'None', ylim = 'None', title = '', legend_description= 'None', legend_location = 'upper right', legend_text_size = 6):
    self.ax.axis('off')
    if legend_description != 'None':
      leg = self.ax.legend(handles=legend_description, loc=legend_location, bbox_to_anchor=(0,0.1), framealpha = 1, shadow = False, prop={'family':'Arial','weight':'bold','size':legend_text_size})
      leg.set_zorder(6)
      ## set color white and manually add text over it with correct colors/italics/etc
      for text in leg.get_texts():
        text.set_color("w")
    if xlim == 'None' and ylim == 'None':
      do_nothing = True
    elif ylim == 'None':
      if self.type == 'single':
        self.ax.set_xlim(xlim)
        self.ax.set_xticklabels('')
        self.ax.set_yticklabels('')
        self.ax.set_title(title)    
      elif self.type == '1d':
        for nr in range(0, self.sub_rows):
          self.ax[nr].set_xlim(xlim)
          self.ax[nr].set_xticklabels('')
          self.ax[nr].set_yticklabels('')
          self.ax[nr].set_title(title)    
      elif self.type == '2d':
        for nr in range(0, self.sub_rows):
          for nc in range(0, self.sub_cols):
            self.ax[nr][nc].set_xlim(xlim)
            self.ax[nr][nc].set_xticklabels('')
            self.ax[nr][nc].set_yticklabels('')
            self.ax[nr][nc].set_title(title)			
    else:
      if self.type == 'single':
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        self.ax.set_xticklabels('')
        self.ax.set_yticklabels('')
        self.ax.set_title(title)
      elif self.type == '1d':
        for nr in range(0, self.sub_rows):
          self.ax[nr].set_xlim(xlim)
          self.ax[nr].set_ylim(ylim)
          self.ax[nr].set_xticklabels('')
          self.ax[nr].set_yticklabels('')
          self.ax[nr].set_title(title)        
      elif self.type == '2d':
        for nr in range(0, self.sub_rows):
          for nc in range(0, self.sub_cols):
            self.ax[nr][nc].set_xlim(xlim)
            self.ax[nr][nc].set_ylim(ylim)
            self.ax[nr][nc].set_xticklabels('')
            self.ax[nr][nc].set_yticklabels('') 
            self.ax[nr][nc].set_title(title)

  def label_plot(self, figure_type, use_type, label_file, longitude, latitude, label, name, label_list, offset_x, offset_y, map_text_alt = 'none'):
    if figure_type == 'FKC_exp':
      for x, y, map_label, map_text in zip(label_file[longitude], label_file[latitude], label_file[label], label_file[name]):
        if map_label in label_list:
          if map_label == 'RIO' or map_label == 'VER' or map_label == 'CRS' or map_label == 'GRL' or map_label == 'LGN' or map_label == 'OBB' or map_label == 'MRY' or map_label == 'WLK':
            self.ax.text(x+offset_x, y+offset_y, map_text, weight = 'bold', style = 'italic', ma='center', zorder=7)
          elif map_text_alt == 'none':
            self.ax.text(x+offset_x, y+offset_y, map_text, ma='center', zorder=7)
          elif  map_label == 'CAA' or map_label == 'FKC':
            self.ax.text(x+offset_x, y+offset_y, map_text_alt, weight = 'bold', style = 'italic', ma='center', zorder=7)
          elif map_label == 'SJR' or map_label == 'KIN' or map_label == 'KAW' or map_label == 'TUL' or map_label == 'KER':
            self.ax.text(x+offset_x, y+offset_y, map_text_alt, weight = 'bold', color='mediumblue', style = 'italic', ma='center', zorder=7)
          elif map_label in ['PCH', 'LAP', 'EDM']:
            self.ax.text(x+offset_x, y+offset_y, map_text_alt, weight = 'bold', color='dimgrey', ma='center', zorder=7)            
          elif map_label in ['SNL', 'MIL', 'PFT', 'KWH', 'TLR', 'ISB']:
            self.ax.text(x+offset_x, y+offset_y, map_text_alt, weight = 'bold', color='midnightblue', ma='center', zorder=7)            
          else:	
            self.ax.text(x+offset_x, y+offset_y, map_text_alt, weight = 'bold', ma='center', zorder=7)
      ## add additional canal labels manually
      self.ax.text(-120.03, 37.1, 'Madera\nCanal', weight='bold', style = 'italic', ma='center', zorder=7)
      self.ax.text(-118.81, 35.18, 'Arvin-Edison\nCanal', weight='bold', style = 'italic', ma='center', zorder=7)
      self.ax.text(-119.55, 35.55, 'Cross', weight='bold', style = 'italic', ma='center', zorder=7)
      self.ax.text(-119.47, 35.46, 'Valley', weight='bold', style = 'italic', ma='center', zorder=7)
      self.ax.text(-119.39, 35.37, 'Canal', weight='bold', style = 'italic', ma='center', zorder=7)
      self.ax.text(-119.26, 36.56, 'Friant-Kern\nCanal', weight='bold', style = 'italic', ma='center', zorder=7)
      self.ax.text(-120.72, 36.38, 'California\nAqueduct', weight='bold', style = 'italic', ma='center', zorder=7)
      ## override legend labels with correct colors/italics/etc
      if use_type != 'sagbi':
        self.ax.text(-121.03, 36.02, 'Surface reservoir', color='midnightblue', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 35.91, 'Natural river', color='mediumblue', style='italic', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 35.8, 'Canal', style='italic', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 35.69, 'Urban turnout', color='dimgrey', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 35.58, 'Tier 1 district', ma='left', zorder=7)
        self.ax.text(-121.03, 35.47, 'Tier 2 district', ma='left', zorder=7)
        self.ax.text(-121.03, 35.36, 'Tier 3 district', ma='left', zorder=7)
        self.ax.text(-121.03, 35.25, 'Other district', ma='left', zorder=7)
        self.ax.text(-121.03, 35.14, 'Friant contractors', ma='left', zorder=7)
      else:
        self.ax.text(-121.03, 36.13, 'Surface reservoir', color='midnightblue', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 36.02, 'Natural river', color='mediumblue', style='italic', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 35.91, 'Canal', style='italic', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 35.8, 'Urban turnout', color='dimgrey', weight='bold', ma='left', zorder=7)
        self.ax.text(-121.03, 35.69, 'Excellent', ma='left', zorder=7)
        self.ax.text(-121.03, 35.58, 'Good', ma='left', zorder=7)
        self.ax.text(-121.03, 35.47, 'Moderately good', ma='left', zorder=7)
        self.ax.text(-121.03, 35.36, 'Moderately poor', ma='left', zorder=7)
        self.ax.text(-121.03, 35.25, 'Poor', ma='left', zorder=7)
        self.ax.text(-121.03, 35.14, 'Very poor', ma='left', zorder=7)
      ## annotate subfig number for paper
      # self.ax.text(-121.27, 37.25, 'a)', ma='left', zorder=7, weight='bold')




    else:
      for x, y, map_label, map_text in zip(label_file[longitude], label_file[latitude], label_file[label], label_file[name]):
        if map_label in label_list:
          if map_label == 'RIO' or map_label == 'VER' or map_label == 'CRS' or map_label == 'GRL' or map_label == 'LGN' or map_label == 'OBB' or map_label == 'MRY' or map_label == 'WLK':
            self.ax.text(x+offset_x, y+offset_y, map_text, weight = 'bold', style = 'italic')
          elif map_text_alt == 'none':
            self.ax.text(x+offset_x, y+offset_y, map_text)
          elif  map_label == 'CAA' or map_label == 'FKC':
            self.ax.text(x+offset_x, y+offset_y, map_text_alt, weight = 'bold', style = 'italic')
          elif map_label == 'SJR' or map_label == 'KIN' or map_label == 'KAW' or map_label == 'TUL' or map_label == 'KER':
            self.ax.text(x+offset_x, y+offset_y, map_text_alt,weight = 'bold', color='midnightblue', style = 'italic')
          else:	
            self.ax.text(x+offset_x, y+offset_y, map_text_alt)


  def load_batch_raster(self, project_folder, raster_id_list, raster_name_pt1, raster_name_pt2, raster_band_list, projection_string, upscale_factor = 'none'):
    for grid_cell in raster_id_list:
      for date_range in raster_id_list[grid_cell]:
        file_folder = project_folder + raster_name_pt1 + grid_cell + '_' + date_range + raster_name_pt2 + '/'
        rgb_list = []
        for band_name in raster_band_list:
          rgb_list.append(raster_name_pt1 + grid_cell + '_' + date_range + raster_name_pt2 + band_name) 
        self.load_sat_bands(file_folder, rgb_list, projection_string, upscale_factor)
  
  def find_plotting_data(self, plot_name):
    vmin = 0
    vmax = 0
    markersize = 2.5
    use_log = False
    if plot_name == 'land use':
      folder_name = '/180115_NeuseHydrology_Draft2/Shapefiles/'
      data_shapefile = 'Soil_Landuse_raw.shp'
      data_layer = 'Land_Use'
      data_type = 'polygons'
      data_labels = 'features'
      xkcd_color_list = ['xkcd:beige', 'xkcd:goldenrod', 'xkcd:moss green', 'xkcd:scarlet', 'xkcd:rose pink','xkcd:reddish pink', 'xkcd:pale rose', 'xkcd:navy green', 'xkcd:light green', 'xkcd:nice blue', 'xkcd:jungle green', 'xkcd:deep sky blue', 'xkcd:canary yellow', 'xkcd:pale', 'xkcd:ocean'] 
	  
    elif plot_name == 'road closure incident type':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Road_Impacts/'
      data_shapefile = 'NCDOT_Incidents_Counties.shp'
      data_layer = 'Incident_T'
      data_type = 'points'
      data_labels = 'features'
      xkcd_color_list = ['xkcd:beige', 'xkcd:goldenrod', 'xkcd:moss green', 'xkcd:scarlet', 'xkcd:rose pink','xkcd:reddish pink', 'xkcd:pale rose', 'xkcd:navy green', 'xkcd:light green', 'xkcd:nice blue', 'xkcd:jungle green', 'xkcd:deep sky blue', 'xkcd:canary yellow', 'xkcd:pale', 'xkcd:ocean'] 

    elif plot_name == 'road closure condition':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Road_Impacts/'
      data_shapefile = 'NCDOT_Incidents_Counties.shp'
      data_layer = 'ConditionN'
      data_type = 'points'
      data_labels = 'features'
      xkcd_color_list = ['white', 'xkcd:pale rose', 'xkcd:pale rose', 'indianred', 'indianred', 'indianred'] 

    elif plot_name == 'road closure duration':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Road_Impacts/'
      data_shapefile = 'NCDOT_Incidents_Counties.shp'
      data_layer = 'Duration'
      data_type = 'points'
      data_labels = 'scaled'
      xkcd_color_list = ['white', 'xkcd:pale rose', 'xkcd:pale rose', 'indianred', 'indianred', 'indianred'] 
      use_log = False
      markersize = 25
      vmin = 0
      vmax = 30
	  
    elif plot_name == 'dam status':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Infrastructure/'
      data_shapefile = 'NCDAMS_20130923.shp'
      data_layer = 'DAM_STATUS'
      data_type = 'points'
      data_labels = 'features'
      xkcd_color_list = ['indianred', 'indianred', 'xkcd:goldenrod', 'xkcd:beige', 'xkcd:beige','xkcd:beige', 'xkcd:beige', 'xkcd:beige', 'xkcd:beige', 'xkcd:beige', 'steelblue', 'xkcd:canary yellow', 'xkcd:rose pink'] 

    elif plot_name == 'dam hazard':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Infrastructure/'
      data_shapefile = 'NCDAMS_20130923.shp'
      data_layer = 'DAM_HAZARD'
      data_type = 'points'
      data_labels = 'features'
      xkcd_color_list = ['indianred', 'xkcd:goldenrod', 'xkcd:beige'] 
      markersize = 25
	  
    elif plot_name == 'dam condition':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Infrastructure/'
      data_shapefile = 'NCDAMS_20130923.shp'
      data_layer = 'CONDITION'
      data_type = 'points'
      data_labels = 'features'
      xkcd_color_list = ['xkcd:beige', 'xkcd:goldenrod', 'xkcd:moss green', 'xkcd:scarlet', 'xkcd:rose pink','xkcd:reddish pink', 'xkcd:pale rose', 'xkcd:navy green', 'xkcd:light green', 'xkcd:nice blue', 'xkcd:jungle green', 'xkcd:deep sky blue', 'xkcd:canary yellow', 'xkcd:pale', 'xkcd:ocean'] 

    elif plot_name == 'dam impoundment':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Infrastructure/'
      data_shapefile = 'NCDAMS_20130923.shp'
      data_layer = 'MAX_IMPOUN'
      data_type = 'points'
      data_labels = 'scaled'
      xkcd_color_list = ['xkcd:beige', 'xkcd:goldenrod', 'xkcd:moss green', 'xkcd:scarlet', 'xkcd:rose pink','xkcd:reddish pink', 'xkcd:pale rose', 'xkcd:navy green', 'xkcd:light green', 'xkcd:nice blue', 'xkcd:jungle green', 'xkcd:deep sky blue', 'xkcd:canary yellow', 'xkcd:pale', 'xkcd:ocean'] 
      vmin = 0
      vmax = 6
      use_log = True
      markersize = 25
    elif plot_name == 'dam discharge':
      folder_name = '/NCState/20180412_RoadImpacts_Infrastructure_data/20180412_RoadImpacts_Infrastructure_data/Infrastructure/'
      data_shapefile = 'NCDAMS_20130923.shp'
      data_layer = 'MAX_DISCHA'
      data_type = 'points'
      data_labels = 'scaled'
      xkcd_color_list = ['xkcd:beige', 'xkcd:goldenrod', 'xkcd:moss green', 'xkcd:scarlet', 'xkcd:rose pink','xkcd:reddish pink', 'xkcd:pale rose', 'xkcd:navy green', 'xkcd:light green', 'xkcd:nice blue', 'xkcd:jungle green', 'xkcd:deep sky blue', 'xkcd:canary yellow', 'xkcd:pale', 'xkcd:ocean'] 
      vmin = 0
      vmax = 5
      use_log = True
      markersize = 25
    
    return folder_name, data_shapefile, data_layer, data_type, data_labels, xkcd_color_list, vmin, vmax, use_log, markersize

  def load_single_bands(self, file_folder, raster_name, projection_string, upscale_factor = 'none'):
      ds = gdal.Open(file_folder + raster_name + '.tif')
      print(file_folder + raster_name)
      #geotransform - tells you where pixel 0 (x,y) is in the coordinate system and the scale of pixels to coordinates
      geotransform = ds.GetGeoTransform()
      print(geotransform)
      ##clip the raster - note: this is done in UTM coordinates before projection
      ##so that you don't need to re-project entire contiguous US
      clip_name = raster_name + '_clipped.tif'
      #ds = gdal.Translate(clip_name, ds, projWin = [geotransform[0] + x_bound[0]*geotransform[1], geotransform[3] + y_bound[0]*geotransform[5], geotransform[0] + x_bound[1]*geotransform[1], geotransform[3] +y_bound[1]*geotransform[5]])
      output_name = file_folder + raster_name + '_projected.tif'
      ##re-project raster from UTM to LAT/LONG
      gdal.Warp(output_name, ds, dstSRS = projection_string)
      raster = rasterio.open(output_name)

      if upscale_factor == 'none':
        ind_rgb = raster.read()
      else:
        ind_rgb = raster.read(out_shape=(raster.count, int(raster.height * upscale_factor), int(raster.width * upscale_factor)), resampling=rasterio.enums.Resampling.bilinear)
      zero_mask = np.zeros(ind_rgb.shape)
      ones_mask = np.ones(ind_rgb.shape)
      ind_rgb[ind_rgb > 0.0] = zero_mask[ind_rgb > 0.0]
      ind_rgb = ind_rgb * -1.0
      spatial_extent = rasterio.plot.plotting_extent(raster)
      image = rasterio.plot.reshape_as_image(ind_rgb)
      image_2d = image.squeeze()
      masked_image = np.ma.masked_where(image_2d == 0.0, image_2d)
      self.ax.imshow(masked_image, extent = spatial_extent, cmap = 'Blues', vmin = -2000.0, vmax = 2000.0)
      print(raster_name)

  def load_sat_bands(self, file_folder, rgb_list, projection_string, upscale_factor, nr = 1, nc = 0):
    
    counter = 0
    for raster_name in rgb_list:
#      print(file_folder + raster_name + '.tif')
      ds = gdal.Open(file_folder + raster_name + '.tif')
#      print(file_folder + raster_name)
      #geotransform - tells you where pixel 0 (x,y) is in the coordinate system and the scale of pixels to coordinates
      geotransform = ds.GetGeoTransform()
      ##clip the raster - note: this is done in UTM coordinates before projection
      ##so that you don't need to re-project entire contiguous US
      clip_name = raster_name + '_clipped.tif'
      #ds = gdal.Translate(clip_name, ds, projWin = [geotransform[0] + x_bound[0]*geotransform[1], geotransform[3] + y_bound[0]*geotransform[5], geotransform[0] + x_bound[1]*geotransform[1], geotransform[3] +y_bound[1]*geotransform[5]])
      output_name = file_folder + raster_name + '_projected.tif'
      ##re-project raster from UTM to LAT/LONG
      gdal.Warp(output_name, ds, dstSRS = projection_string)
      raster = rasterio.open(output_name)

      if upscale_factor == 'none':
        ind_rgb = raster.read()
      else:
        ind_rgb = raster.read(out_shape=(raster.count, int(raster.height * upscale_factor), int(raster.width * upscale_factor)), resampling=rasterio.enums.Resampling.bilinear)
      zero_mask = np.zeros(ind_rgb.shape)
      ones_mask = np.ones(ind_rgb.shape)
      ind_rgb[ind_rgb <= 1.0] = ones_mask[ind_rgb <= 1.0]
      band_mean, band_std = np.mean(ind_rgb), np.std(ind_rgb)
      ind_rgb = np.log(ind_rgb)
      ind_rgb = np.power(ind_rgb, self.brightness_adj*np.ones(ind_rgb.shape))
      if self.band_min[counter] == -1.0:
        self.band_min[counter], self.band_max[counter] = np.min(ind_rgb), np.max(ind_rgb)
      ind_rgb = (ind_rgb - self.band_min[counter])/(self.band_max[counter] - self.band_min[counter])
      if counter == 0:
        rgb_bands = np.zeros((4, ind_rgb.shape[1], ind_rgb.shape[2]))
      rgb_bands[counter,:,:] = ind_rgb
      
      counter = counter + 1
      
    ###read RGB bands of raster
    #b = raster.read()
    #file_folder = 'Neuse/LC08_CU_026011_20190920_20190927_C01_V01_SR/'
    #rgb_list = ['LC08_CU_026011_20190920_20190927_C01_V01_SRB4.tif','LC08_CU_026011_20190920_20190927_C01_V01_SRB3.tif','LC08_CU_026011_20190920_20190927_C01_V01_SRB2.tif']
    #file_folder = 'Neuse/LC08_CU_028011_20190922_20191001_C01_V01_SR/'
    #rgb_list = ['LC08_CU_028011_20190922_20191001_C01_V01_SRB4.tif','LC08_CU_028011_20190922_20191001_C01_V01_SRB3.tif','LC08_CU_028011_20190922_20191001_C01_V01_SRB2.tif']
    
    
    true_value_mask = np.ones((1,ind_rgb.shape[1], ind_rgb.shape[2]))
    false_value_overlay = np.zeros((1, ind_rgb.shape[1], ind_rgb.shape[2]))
    false_value_mask = ind_rgb == 0.0
    true_value_mask[false_value_mask] = false_value_overlay[false_value_mask]
    rgb_bands[3,:,:] = true_value_mask
    #rgb_bands = rgb_bands.transpose([1,2,0])
    image = rasterio.plot.reshape_as_image(rgb_bands)
    del rgb_bands
    del ind_rgb
    del true_value_mask
    del false_value_overlay
    del false_value_mask

    ##put bands into RGB order
    #image = rasterio.plot.reshape_as_image(b)
    ##give coordinates of image bands
    spatial_extent = rasterio.plot.plotting_extent(raster)
    ##plot image
    print(spatial_extent)
    if self.type == 'single':
      self.ax.imshow(image, extent = spatial_extent)
    elif self.type == '1d':
      self.ax[nr].imshow(image, extent = spatial_extent)
    elif self.type == '2d':
      self.ax[nr][nc].imshow(image, extent = spatial_extent)

  def add_inset_figure(self, shapefile_name, box_lim_x, box_lim_y, inset_lim_x, inset_lim_y, figure_type, use_type):
    map_shape = gpd.read_file(shapefile_name)
    map_shape['geometry'] = map_shape['geometry'].to_crs(epsg = 4326)
    p2 = Polygon([(box_lim_x[0], box_lim_y[0]), (box_lim_x[1], box_lim_y[0]), (box_lim_x[1], box_lim_y[1]), (box_lim_x[0], box_lim_y[1])])
    df1 = gpd.GeoDataFrame({'geometry': p2, 'df1':[1,1]})
    df1.crs = {'init' :'epsg:4326'}
    if figure_type == 'FKC_exp':
      if use_type in ['friant', 'alt1', 'intro-tulare', '1827_median_FKC_CFWB', '537_median_FKC_CFWB', '2454_median_FKC_CFWB', '981_median_FKC_CFWB', 'boxplot_combined', 'sagbi']:
        loc = 'upper right'
      else:
        loc = 'lower left'

    else:
      loc = 3
    axins = inset_axes(self.ax, width = '25%', height = '25%', loc = loc, bbox_to_anchor=(0.06, 0, 1,1), bbox_transform=self.ax.transAxes)
    map_shape.plot(ax = axins, facecolor = 'none', edgecolor = 'k', linewidth = 1)
    df1.plot(ax = axins, facecolor = '0.5', alpha = 0.5)
    axins.set_xlim(inset_lim_x[0], inset_lim_x[1])
    axins.set_ylim(inset_lim_y[0], inset_lim_y[1])
    axins.set_xticks([])
    axins.set_yticks([])

    
  def add_ocean(self, filename, x_left):
    coastline = gpd.read_file(filename)
    geo_list = []
    counter = 0
    polygon_list = []
    for x in coastline['geometry']:
      newcords = list(x.coords)
      if counter == 0:
        start_loc = newcords[0]
        polygon_list.append(LineString([[x_left, start_loc[1]]]))
        counter += 1
      for y in newcords:
        if y[0] < -122.917 and y[1] < 37.8744:
          skip = 1
        elif y[0] < -119.309 and y[1] < 34.153:
          skip = 1
        elif y[0] < -18.258 and y[1] < 33.6132:
          skip = 1
        else:                 
          polygon_list.append((y[0], y[1]))
    #polygon_list.append(LineString([[x_left, y[1]]]))
    #polygon_list.append(LineString([[x_left, start_loc[1]]]))
    multi_line = MultiLineString(polygon_list)
    print(multi_line)
    merged_line = linemerge(multiline)
    print(merged_line) 
    p2 = Polygon(polygon_list)
    geo_list.append(p2)
    values = range(len(geo_list))
    df1 = gpd.GeoDataFrame(values, geometry = geo_list)
    df1.crs = {'init' :'epsg:4326'}
    df1.plot(ax = self.ax)
    plt.show()



# def finalize_FKC_exp(self):
#     ## add basemap
#   # cx.add_basemap(ax = data_figure.ax, crs=shapes['geometry'].crs)
#   ## add district labels
#   data_figure.values['coords'] = data_figure.values['geometry'].apply(lambda x: x.representative_point().coords[:])
#   data_figure.values['coords'] = [coords[0] for coords in data_figure.values['coords']]
#   for idx, row in data_figure.values.iterrows():
#     data_figure.annotate(row['anon'], xy=row['coords'], horizontalalignment='center', color='k')

