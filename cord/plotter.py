import numpy as np
import pandas as pd
import toyplot as tp
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import gridspec
from matplotlib.lines import Line2D
from .util import *
import seaborn as sns
sns.set_style('whitegrid')

def init_plotting():
    sns.set_style('whitegrid')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 13
    plt.rcParams['font.family'] = 'OfficinaSanITCBoo'
    plt.rcParams['axes.labelsize'] = 1.1*plt.rcParams['font.size']
    plt.rcParams['axes.titlesize'] = 1.1*plt.rcParams['font.size']
    plt.rcParams['legend.fontsize'] = plt.rcParams['font.size']
    plt.rcParams['xtick.labelsize'] = plt.rcParams['font.size']
    plt.rcParams['ytick.labelsize'] = plt.rcParams['font.size']

def compare(res,obs,freq='D'):
  # input two series and a frequency
  init_plotting()
  res = res.resample(freq).mean()
  obs = obs.resample(freq).mean()

  fig = plt.figure(figsize=(12, 3)) 
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 

  ax0 = plt.subplot(gs[0])
  res.plot(ax=ax0, color='indianred')
  obs.plot(ax=ax0, color='k')
  ax0.set_title('%s, %s' % (res.name, obs.name), family='OfficinaSanITCMedium', loc='left')
  ax0.legend(['Simulated', 'Observed'], ncol=3)

  ax1 = plt.subplot(gs[1])
  r = np.corrcoef(obs.values,res.values)[0,1]
  ax1.scatter(obs.values, res.values, s=3, c='steelblue', edgecolor='none', alpha=0.7)
  ax1.set_ylabel('Simulated')
  ax1.set_xlabel('Observed')
  ax1.annotate('$R^2 = %f$' % r**2, xy=(0,0), color='0.3')
  ax1.set_xlim([0.0, ax1.get_xlim()[1]])
  ax1.set_ylim([0.0, ax1.get_ylim()[1]])

  plt.tight_layout()
  plt.show()

def stack(data, district_name):
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  x = np.arange(len(data[0]))
  #ax1.fill_between(x,data[0],data[1], color = 'xkcd:cornflower')
  #ax1.fill_between(x,data[1],data[2], color = 'xkcd:denim blue')
  ax1.fill_between(x,data[2],data[3], color = 'xkcd:light rose')
  ax1.fill_between(x,data[3],data[4], color = 'xkcd:neon red')
  ax1.fill_between(x,data[4],data[5], color = 'xkcd:olive')
  ax1.fill_between(x,data[5],data[6], color = 'xkcd:turquoise')
  ax1.fill_between(x,data[6],data[7], color = 'xkcd:lime')
  ax1.fill_between(x,data[7],data[8], color = 'xkcd:cream')
  ax1.fill_between(x,data[8],data[9], color = 'xkcd:bright yellow')
  ax1.fill_between(x,data[9],data[10], color = 'xkcd:golden yellow')
  ax1.set_ylabel('District Deliveries (tAF)          District Supplies (tAF)  ')
  ax1.set_xlabel('Days from 10/1/1996')
  ax1.set_xlim([0.0, ax1.get_xlim()[1]])
  sq1 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:cornflower')
  sq2 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:denim blue')
  sq3 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:light rose')
  sq4 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:neon red')
  sq5 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:olive')
  sq6 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:turquoise')
  sq7 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:lime')
  sq8 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:cream')
  sq9 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:bright yellow')
  sq10 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'xkcd:golden yellow')

  plt.legend((sq10, sq9, sq8, sq7, sq6, sq5, sq4, sq3), ("Paper Trade Balance", "Carryover Surface Storage", "Annual Contract Allocation", "District SW Deliveries", "Deliveries from In-Leiu Partner", "Deliveries from District Banked Storage", "Private Pumping", "Pumping to In-Leiu Partner"), ncol = 3, mode = 'expand', bbox_to_anchor = (0.0, 1.025, 1.0, .4), loc = 3, borderaxespad = 0.0)
  plt.title(district_name + " Water Accounting")
  plt.show()

def waterbank_storage(data,member_list,bank_name):
  colorlist = ['xkcd:purple', 'xkcd:green', 'xkcd:blue', 'xkcd:pink', 'xkcd:brown', 'xkcd:red', 'xkcd:light blue', 'xkcd:teal', 'xkcd:orange', 'xkcd:light green', 'xkcd:magenta', 'xkcd:yellow', 'xkcd:sky blue', 'xkcd:grey', 'xkcd:lime green', 'xkcd:light purple', 'xkcd:barbie pink', 'xkcd:turquoise', 'xkcd:lavender', 'xkcd:tan', 'xkcd:cyan', 'xkcd:aqua', 'xkcd:forest green', 'xkcd:mauve', 'xkcd:dark purple', 'xkcd:bright green', 'xkcd:maroon', 'xkcd:olive']

  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  i = 0
  legend_list = []
  for member in member_list:
    thismember = member
    x = np.arange(len(data[thismember]))

    if i > 0:
      ax1.fill_between(x,data[lastmember],data[thismember], color = colorlist[i])
      sq1 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = colorlist[i])
      legend_list.append(sq1)
    else:
      lastmember_data = np.zeros(len(data[thismember]))
      ax1.fill_between(x,lastmember_data,data[thismember], color = colorlist[i])
      sq1 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = colorlist[i])
      legend_list.append(sq1)


    lastmember = thismember
    i += 1

  plt.legend(legend_list, member_list,ncol = math.ceil(len(member_list)/3),  bbox_to_anchor = (0.0, 1.025, 1.0,  .4), loc = 3, borderaxespad = 0.0)
  plt.title(bank_name + " bank")
  plt.show()
  
def exposure(data,var_ind,num_ind):
  colors = ("yellow", "green", "blue", "red")
  groups = ("Total Deliveries, In-District + Banking Partners", "In-District Deliveries, Banked + Contract + In-leiu", "In-District Deliveries, Banked + Contract", "In-District Deliveries, Contract")
  fig = plt.figure()
  ax1 = fig.add_subplot(1,1,1, axisbg = "1.0")
  i = num_ind
  for color, group in zip(colors, groups):
    x = data[var_ind]
    y = data[i]
    ax1.scatter(x,y, alpha = 0.8, c = color, edgecolors = 'none', s = 30, label = group)
    i = i + 1
  ax1.set_ylabel('Annual District Sales (tAF)')
  ax1.set_xlabel('Annual SWP Pumping (tAF) minus Pumping at Edmonston')
  ax1.set_xlim([0.0, ax1.get_xlim()[1]])
  ax1.set_ylim([0.0, ax1.get_ylim()[1]])
  plt.legend(loc = 2, fancybox = True, shadow = True)
  plt.show()

def financial(data,var_ind,num_ind):
  colors = ("yellow", "green", "blue", "red")
  groups = ("Banking Recovery", "Banking Recharge", "In-District Deliveries, Variable", "In-District Deliveries, Contract")
  fig = plt.figure()
  ax1 = fig.add_subplot(1,1,1, axisbg = "1.0")
  i = num_ind
  y = np.zeros((5,len(data[var_ind])))
  costs = np.zeros(4)
  costs[0] = .08633 - .01
  costs[1] = .01233 + .044
  costs[2] = .118
  costs[3] = .056
  i = num_ind + len(costs) - 1
  x = data[var_ind]
  index_values = np.argsort(x)
  for color, group in zip(colors, groups):
    for spot in range(0,len(data[var_ind])):
      ordered_index = index_values[spot]
      if i == num_ind + len(costs) - 1:
        data_prev = 0.0
        value_prev = 0.0
      else:
        data_prev = data[i+1][ordered_index]
        value_prev = y[i+1-num_ind][spot]
      y[i-num_ind][spot] += (data[i][ordered_index] - data_prev)*costs[i-num_ind] + value_prev
      print(i, end = " ")
      print(ordered_index, end = " ")
      print(value_prev, end = " ")
      print(data_prev, end = " ")
      print(data[i][ordered_index], end = " ")
      print(x[ordered_index])
      y[num_ind + 1][spot] = x[ordered_index]
      	  
    i = i - 1
  print(y)
  print(data[num_ind])
  print(data[num_ind+1])
  print(data[num_ind+2])
  print(data[num_ind+3])

  ax1.fill_between(y[4],np.zeros(len(y[0])), y[3], color = "yellow")
  ax1.fill_between(y[4],y[3],y[2], color = 'green')
  ax1.fill_between(y[4],y[2],y[1], color = 'blue')
  ax1.fill_between(y[4],y[1],y[0], color = 'red')
  sq1 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'yellow')
  sq2 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'green')
  sq3 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'blue')
  sq4 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.4, markersize = 10, markerfacecolor = 'red')
  plt.legend((sq4, sq3, sq2, sq1), groups, ncol = 2, mode = 'expand', bbox_to_anchor = (0.0, 1.025, 1.0, .4), loc = 3, borderaxespad = 0.0)
  ax1.set_ylabel('Annual Revenue ($MM)')
  ax1.set_xlabel('Pumping difference between Banks and Edmonston, minus Article 21 Flows (tAF)')
  plt.show()

  fig2, ax2 = plt.subplots()
  ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer = True))
  plt.plot(range(1997,2017),y[0])
  plt.ylabel('Total Revenue ($MM)')
  ax2.axis('tight')
  fig2.tight_layout()
  plt.xlabel('WY (OCT-SEPT)')

  #ax1.scatter(x,y, alpha = 0.8, c = 'red', edgecolors = 'black', s = 30)
  #ax1.set_ylabel('Annual District Sales ($)')
  #ax1.set_xlabel('Annual SWP Pumping minus Edmonston Pumping (tAF)')
  #ax1.set_xlim([0.0, ax1.get_xlim()[1]])
  #ax1.set_ylim([0.0, ax1.get_ylim()[1]])
  #plt.legend(loc = 2, fancybox = True, shadow = True)
  #plt.show()
