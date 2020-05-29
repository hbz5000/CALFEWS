
import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import math 

class Sanker():

  def __init__(self, nr = 1, nc = 0):
    self.sub_rows = nr
    self.sub_cols = nc
    if self.sub_cols == 0:
      self.fig, self.ax = plt.subplots(self.sub_rows, figsize=(20, 10))
      if self.sub_rows == 1:
        self.type = 'single'
        self.ax.grid(False)
      else:
        self.type = '1d'
    else: 
      self.fig, self.ax = plt.subplots(self.sub_rows, self.sub_cols, figsize=(25, 10))
      self.type = '2d'
    self.band_min = np.ones(3)*(-1.0)
    self.band_max = np.ones(3)*(-1.0)
    self.brightness_adj = 2.0



  def add_sankey(self, loc1, loc2, scale_src, scale_dest, plot_position, color, alpha):
    x = np.linspace(-10, 10, 100)
    x_plot = np.linspace(plot_position, plot_position + 1.0, 100)
    bottom_sig_height = (loc2[0]/scale_dest) - (loc1[0]/scale_src)
    top_sig_height = (loc2[1]/scale_dest) - (loc1[1]/scale_src)
    z_bottom = bottom_sig_height/(1 + np.exp(-1 * x)) + (loc1[0]/scale_src)
    z_top = top_sig_height/(1 + np.exp(-1 * x)) + (loc1[1]/scale_src)
    self.ax.fill_between(x_plot, z_bottom, z_top, color= color, alpha = alpha, edgecolor = 'b', linewidth = 0.0, zorder = 10) 

  def add_sankey2(self, loc1, loc2, scale_src, scale_away, plot_position, color, alpha, zorder_num = 2):
    x = np.linspace(0, scale_away, 100)
    bottom_multiplier = (1.1 - loc1[0]/scale_src)/pow(loc2[1], 2.0)
    top_multiplier = (1.1 - loc1[1]/scale_src)/pow(loc2[0], 2.0)

    x_plot = np.linspace(plot_position, plot_position + 1.0, 100)
    z_bottom = bottom_multiplier * pow(x, 2.0) + loc1[0]/scale_src
    z_top = top_multiplier * pow(x, 2.0) + loc1[1]/scale_src
    z_top[z_top > 1.1] = 1.1
    z_bottom[z_bottom > 1.1] = 1.1
    self.ax.fill_between(x_plot, z_bottom, z_top, color= color, alpha = alpha, edgecolor = 'b', linewidth = 0.0, zorder = zorder_num) 

  def add_sankey3(self, loc1, loc2, scale_away, scale_dest, plot_position, color, alpha, zorder_num = 2):
    x = np.linspace(0, 1, 100)
    bottom_multiplier = (1.1 - loc2[0]/scale_dest)/pow((loc1[0]/scale_away)-1.0, 2.0)
    top_multiplier = (1.1 - loc2[1]/scale_dest)/pow((loc1[1]/scale_away)-1.0, 2.0)

    x_plot = np.linspace(plot_position, plot_position + 1.0, 100)
    z_bottom = bottom_multiplier * pow(x - 1, 2.0) + loc2[0]/scale_dest
    z_top = top_multiplier * pow(x - 1, 2.0) + loc2[1]/scale_dest
    z_top[z_top > 1.1] = 1.1
    z_bottom[z_bottom > 1.1] = 1.1
    self.ax.fill_between(x_plot, z_bottom, z_top, color= color, alpha = alpha, edgecolor = 'b', linewidth = 0.0, zorder = zorder_num) 



  def add_sankey_label(self, block_height, loc_scale, block_width, block_position, open_space, label_groups, min_height, prev_values, block_label, unit_label = 'tAF'):

    if len(label_groups) < 2:
      numspaces = 1
    else:
      numspaces = len(label_groups) - 1

    min_width = max(len(block_label),8) * .025

    open_space = max( len(label_groups) * min_height, open_space)
    top = (prev_values + block_height)/loc_scale + block_position[0] * open_space/numspaces
    bottom = prev_values/loc_scale + block_position[0] * open_space/numspaces
    total_height = top - bottom
    if total_height < min_height:
      top += (min_height - total_height)*0.5
      bottom -= (min_height - total_height)*0.5

    left = block_position[1] - block_width
    right = block_position[1] + block_width
    total_width = right - left
    if total_width < min_width:
      left -= (min_width - total_width)/2
      right +=(min_width - total_width)/2
    self.ax.fill_between([left, right], [bottom, bottom], [top, top], facecolor= 'lightgray', alpha = 1.0, edgecolor = 'black', linewidth = 2.0, zorder = 20)
    if unit_label == 'tAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height)) + ' tAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == 'mAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height/100)/10) + ' mAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == '%':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height*100)/100) + ' %', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)

  def add_sankey_label_horizontal(self, block_height, loc_scale, block_width, block_position, open_space, prev_values, block_label, unit_label = 'tAF'):
    min_width = max(len(block_label), 8) * .025
    right = (prev_values + block_height)/loc_scale + block_position[0] * open_space/loc_scale
    left = prev_values/loc_scale + block_position[0] * open_space/loc_scale
    tot_width = right - left
    if tot_width < min_width:
      right += (min_width - tot_width)/2
      left -= (min_width - tot_width)/2

    bottom = block_position[1] - block_width
    top = block_position[1] + block_width

    self.ax.fill_between([left, right], [bottom, bottom], [top, top], facecolor= 'lightgray', alpha = 1.0, edgecolor = 'black', linewidth = 2.0, zorder = 20)
    if unit_label == 'tAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height)) + ' tAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == 'mAF':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height/100)/10) + ' mAF', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)
    elif unit_label == '%':
      self.ax.text((left + right)/2.0, (bottom + top)/2, block_label + '\n ' + str(round(block_height*100)/100) + ' %', fontsize = 10, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center',
        horizontalalignment='center', zorder = 20)


  def add_sankey_title(self, column, title, height):
    self.ax.text(column, height, title, fontsize = 20, weight = 'bold', fontname = 'Gill Sans MT',verticalalignment='center', horizontalalignment='center') 

  def format_sankey(self, xlim, ylim, fig_name):
    self.ax.set_xlim(xlim)
    self.ax.set_ylim(ylim)
    self.ax.axis('off')
    x_extent = int(np.floor(xlim[1]))
    self.ax.plot([0, x_extent], [0, 0], color = 'black',  zorder = 1)
    self.ax.plot([0, x_extent], [1.1, 1.1], color = 'black',  zorder = 1)
    self.ax.plot([0, 0], [0, 1.1], color = 'black',  zorder = 1)
    self.ax.plot([x_extent, x_extent], [0, 1.1], color = 'black',  zorder = 1)

    plt.savefig(fig_name + '.png', dpi = 150, bbox_inches = 'tight', pad_inches = 0.0)



