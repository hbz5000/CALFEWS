import numpy as np
import pandas as pd
import collections as cl
import toyplot as tp
import scipy.stats as stats
import math
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import gridspec
from matplotlib.lines import Line2D
from .util import *
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter

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

def compare_validation(res_old,res_new,obs,name,freq,freq2, data_name):
  # input two series and a frequency
  init_plotting()

  res_old1 = res_old.resample(freq).mean()*7*1.98/1000.0
  res_new1 = res_new.resample(freq).mean()*7*1.98/1000.0
  obs1 = obs.resample(freq).mean()*7*1.98/1000.0

  sns.set()
  fig = plt.figure(figsize=(16, 4))
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])

  ax0 = plt.subplot(gs[0, 0])
  obs1.plot(ax=ax0, color='k', use_index=True, alpha = 0.7, linewidth = 3)
  res_old1.plot(ax=ax0, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)
  res_new1.plot(ax=ax0, color='steelblue', use_index=True, alpha = 0.7, linewidth = 3, linestyle = '--')
  #ax0.set_xlim([datetime.date(2004,10,1), datetime.date(2006,9,30)])
  #ax0.set_title('%s, %s' % (res.name, obs.name), family='OfficinaSanITCMedium', loc='left')
  ax0.set_title(name)
  ax0.legend(['Observed', 'Old', 'New'], ncol=1)
  ax0.set_ylabel('Pumping (tAF)')
  ax0.set_xlabel('')
  # ax11 = plt.subplot(gs[1, 0])
  # obs1.plot(ax=ax11, color='k', use_index=True, alpha = 0.7, linewidth = 3)
  # res_new1.plot(ax=ax11, color='steelblue', use_index=True, alpha = 0.7, linewidth = 3)
  #ax11.set_xlim([datetime.date(2013,10,1), datetime.date(2015,9,30)])
  # ax11.set_title('Weekly '+ data_name + ' WY 2014-2015')
  #ax0.set_title('%s, %s' % (res.name, obs.name), family='OfficinaSanITCMedium', loc='left')
  # ax11.set_ylabel('Pumping (tAF)')
  # ax11.set_xlabel('')

  res_old2 = res_old.resample(freq2).mean()*365*1.98/1000
  res_new2 = res_new.resample(freq2).mean()*365*1.98/1000
  obs2 = obs.resample(freq2).mean()*365*1.98/1000

  ax22 = plt.subplot(gs[0,1])
  r_old = np.corrcoef(obs2.values,res_old2.values)[0,1]
  r_new = np.corrcoef(obs2.values,res_new2.values)[0,1]
  ax22.scatter(obs2.values, res_old2.values, s=75, c='indianred', edgecolor='none', alpha=0.8)
  ax22.scatter(obs2.values, res_new2.values, s=75, c='steelblue', edgecolor='none', alpha=0.8)
  ax22.plot([0.0, max([max(obs2.values), max(res_old2.values)])], [0.0, max([max(obs2.values), max(res_old2.values)])], linestyle = 'dashed', color = 'black', linewidth = 3)
  ax22.set_ylabel('Simulated (tAF/yr)')
  ax22.set_xlabel('Observed (tAF/yr)')
  ax22.set_title('Annual '+ data_name + ' vs. Simulated')
  ax22.annotate('$R^2 = %f$' % r_old**2, xy=(0,0), color='indianred')
  ax22.annotate('$R^2 = %f$' % r_new**2, xy=(max(obs2.values)*0.6,0), color='steelblue')
  ax22.set_xlim([0.0, ax22.get_xlim()[1]])
  ax22.set_ylim([0.0, ax22.get_ylim()[1]])
  # for item in [ax0.xaxis.label, ax0.yaxis.label, ax11.xaxis.label, ax11.yaxis.label,ax22.xaxis.label, ax22.yaxis.label, ax0.title, ax11.title, ax22.title]:
  #   item.set_fontsize(14)
  # for item in (ax0.get_xticklabels() + ax11.get_xticklabels() + ax22.get_xticklabels() + ax0.get_yticklabels() + ax11.get_yticklabels() + ax22.get_yticklabels()):
  #   item.set_fontsize(14)
  plt.tight_layout()
  plt.show()



def compare_simulation(res_old,res_new,obs,name,freq,freq2, data_name):
  # input two series and a frequency
  init_plotting()

  # res_new = res_new.loc[res_new.index.year > 1995]
  res_old1 = res_old.resample(freq).mean()*7*1.98/1000.0
  res_new1 = res_new.resample(freq).mean()*7*1.98/1000.0
  obs1 = obs.resample(freq).mean()*7*1.98/1000.0

  sns.set()
  fig = plt.figure(figsize=(16, 4))
  gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])

  ax0 = plt.subplot(gs[0, 0])
  obs1.plot(ax=ax0, color='k', use_index=True, alpha = 0.7, linewidth = 3)
  res_old1.plot(ax=ax0, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)
  res_new1.plot(ax=ax0, color='steelblue', use_index=True, alpha = 0.7, linewidth = 3, linestyle = '--')
  #ax0.set_xlim([datetime.date(2004,10,1), datetime.date(2006,9,30)])
  #ax0.set_title('%s, %s' % (res.name, obs.name), family='OfficinaSanITCMedium', loc='left')
  ax0.set_title(name)
  ax0.legend(['Observed', 'Old', 'New'], ncol=1)
  ax0.set_ylabel('Pumping (tAF)')
  ax0.set_xlabel('')
  # ax11 = plt.subplot(gs[1, 0])
  # obs1.plot(ax=ax11, color='k', use_index=True, alpha = 0.7, linewidth = 3)
  # res_new1.plot(ax=ax11, color='steelblue', use_index=True, alpha = 0.7, linewidth = 3)
  #ax11.set_xlim([datetime.date(2013,10,1), datetime.date(2015,9,30)])
  # ax11.set_title('Weekly '+ data_name + ' WY 2014-2015')
  #ax0.set_title('%s, %s' % (res.name, obs.name), family='OfficinaSanITCMedium', loc='left')
  # ax11.set_ylabel('Pumping (tAF)')
  # ax11.set_xlabel('')

  res_old2 = res_old.resample(freq2).mean()*365*1.98/1000
  res_new2 = res_new.resample(freq2).mean()*365*1.98/1000

  # ax22 = plt.subplot(gs[0,1])
  # r = np.corrcoef(res_new2.values,res_old2.values)[0,1]
  # ax22.scatter(res_old2.values, res_new2.values, s=75, c='steelblue', edgecolor='none', alpha=0.8)
  # ax22.plot([0.0, max([max(res_old2.values), max(res_new2.values)])], [0.0, max([max(res_old2.values), max(res_new2.values)])], linestyle = 'dashed', color = 'black', linewidth = 3)
  # ax22.set_ylabel('Simulated (tAF/yr)')
  # ax22.set_xlabel('Observed (tAF/yr)')
  # ax22.set_title('Annual '+ data_name + ' vs. Simulated')
  # ax22.annotate('$R^2 = %f$' % r**2, xy=(max(res_old2.values)*0.6,0), color='steelblue')
  # ax22.set_xlim([0.0, ax22.get_xlim()[1]])
  # ax22.set_ylim([0.0, ax22.get_ylim()[1]])
  # for item in [ax0.xaxis.label, ax0.yaxis.label, ax11.xaxis.label, ax11.yaxis.label,ax22.xaxis.label, ax22.yaxis.label, ax0.title, ax11.title, ax22.title]:
  #   item.set_fontsize(14)
  # for item in (ax0.get_xticklabels() + ax11.get_xticklabels() + ax22.get_xticklabels() + ax0.get_yticklabels() + ax11.get_yticklabels() + ax22.get_yticklabels()):
  #   item.set_fontsize(14)
  plt.tight_layout()
  plt.show()






def compare_contracts():
  contract_values = pd.read_csv('cord/data/results/contract_results_annual_simulation.csv', index_col = 0)
  sns.set()
  fig = plt.figure()
  gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1]) 

  ax0 = plt.subplot(gs[0])
  obs = contract_values['tableA real']
  res = contract_values['SLS_contract']
  obs.plot(ax=ax0, color='k', alpha = 0.7, linewidth = 3)
  res.plot(ax=ax0, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)  
  ax0.set_ylabel('Table A Deliveries (tAF)')
  ax0.set_xlim([0, 19])
  plt.xticks(range(3,23,4), range(2000,2020,4))

  ax1 = plt.subplot(gs[1])
  obs = contract_values['article21 real']
  res = contract_values['SLS_flood']
  obs.plot(ax=ax1, color='k', alpha = 0.7, linewidth = 3)
  res.plot(ax=ax1, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)  
  ax1.set_ylabel('Article 21 Deliveries (tAF)')
  ax1.set_xlim([0, 19])
  plt.xticks(range(3,23,4), range(2000,2020,4))

  ax2 = plt.subplot(gs[2])
  obs = contract_values['carryover real']
  res = contract_values['SLS_carryover']
  obs.plot(ax=ax2, color='k', alpha = 0.7, linewidth = 3)
  res.plot(ax=ax2, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)  
  ax2.set_ylabel('Carryover Deliveries (tAF)')
  ax2.set_xlim([0, 19])
  plt.xticks(range(3,23,4), range(2000,2020,4))

  ax3 = plt.subplot(gs[3])
  obs = contract_values['turnback real']
  res = contract_values['SLS_turnback']
  obs.plot(ax=ax3, color='k', alpha = 0.7, linewidth = 3)
  res.plot(ax=ax3, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)  
  ax3.set_ylabel('Turnback Pool Deliveries (tAF)')
  ax3.set_xlim([0, 19])
  plt.xticks(range(3,23,4), range(2000,2020,4))
  
  for item in [ax0.xaxis.label, ax0.yaxis.label, ax1.xaxis.label, ax1.yaxis.label, ax2.xaxis.label, ax2.yaxis.label, ax3.xaxis.label, ax3.yaxis.label]:
    item.set_fontsize(14)  
  for item in (ax0.get_xticklabels() + ax1.get_xticklabels() + ax0.get_yticklabels() + ax1.get_yticklabels()+ax2.get_xticklabels() + ax3.get_xticklabels() + ax2.get_yticklabels() + ax3.get_yticklabels()):
    item.set_fontsize(14)  

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
#################################################################
def show_recovery(district_results, key_list, delivery_type):
  total_delivery = 0.0
  total_banked = 0.0
  for x in key_list:
    deliveries = district_results[x + '_delivery']
    banking = district_results[x + '_banked_accepted']
    total_delivery += deliveries
    total_banked += banking
	
  sns.set()
  plt.plot(total_delivery, linewidth = 3, color = 'black')
  plt.plot(total_banked, linewidth = 3, color = 'red')
  plt.xlabel('Historical Sample Year')
  plt.ylabel('Total Irrigation Deliveries (kAF)')
  plt.legend((delivery_type +' Deliveries', 'With Banking Recovery'))
  plt.tight_layout()
  plt.show()
  
def show_recovery_historic(district_results, timeseries_revenues, average_revenues, key_list, year_start, year_end, min_rev, max_rev, rev_int, min_del, max_del, del_int, legend_loc):
  record_start = 1905
  index_start = int(year_start - record_start - 1)
  index_end = int(year_end - record_start - 1)
  total_delivery = np.zeros(len(district_results))
  total_banked = np.zeros(len(district_results))
  total_revenue = np.zeros(len(district_results))
  total_average = 0.0
  if isinstance(key_list, cl.Iterable):
    for x in key_list:
      deliveries = district_results[x + '_delivery']
      banking = district_results[x + '_banked_accepted']
      revenue = timeseries_revenues[x]['recovery']
      averev = average_revenues[x]['recovery']
      total_delivery += deliveries
      total_banked += banking
      total_revenue += revenue
      total_average += averev
  else:
    deliveries = district_results[x + '_delivery']
    banking = district_results[x + '_banked_accepted']
    revenue = timeseries_revenues['recovery']
    averev = average_revenues['recovery']
    total_delivery += deliveries
    total_banked += banking
    total_revenue += revenue
    total_average += averev
  
  period_revenue = total_revenue[index_start:index_end]
  budget_gap = np.zeros(len(period_revenue))
  budget_gap[0] = period_revenue[0] - total_average
  for y in range(1,len(period_revenue)):
    budget_gap[y] = period_revenue[y] - total_average + budget_gap[y-1]
	
  period_delivery = total_delivery[index_start:index_end]
  period_banked = total_banked[index_start:index_end]
  period_length = len(period_delivery)
  sns.set()
  fig = plt.figure()
  ax1 = fig.add_subplot(1,1,1)
  ax1.fill_between(np.arange(period_length),np.zeros(period_length),period_delivery, color = 'blue', alpha = 0.25)
  ax1.fill_between(np.arange(period_length),period_delivery,period_banked, color = 'blue', alpha = 0.75)
  ax1.set_xlabel('Historical Sample Year')
  ax1.set_xlim([0.0, period_length - 1])
  plt.xticks(np.arange(period_length), range(year_start,(year_end+1)))
  ax1.set_ylabel('Annual District Deliveries (tAF)', color = 'blue')
  ax1.set_ylim([min_del, max_del])
  plt.yticks(range(int(min_del),int(max_del+del_int),int(del_int)))
  ax2 = ax1.twinx()
  ax2.plot(budget_gap, linewidth = 5, color = 'red')
  ax2.set_ylabel('Cumulative Revenue Shortfall ($MM)', color = 'red')
  ax2.set_ylim([min_rev,max_rev])
  plt.yticks(range(int(min_rev),int(max_rev+rev_int),int(rev_int)))
  if legend_loc == 1:
    ax1.legend(('Contract Deliveries', 'Recharge at Bank'), bbox_to_anchor = (0.005, .995), loc = 'upper left',  fontsize = 18)
  else:
    ax1.legend(('Contract Deliveries', 'Recharge at Bank'),  fontsize = 18)

  plt.tight_layout()
  for item in [ax1.xaxis.label, ax1.yaxis.label, ax2.yaxis.label]:
    item.set_fontsize(22)  
  for item in (ax1.get_xticklabels() + ax1.get_yticklabels() + ax2.get_yticklabels()):
    item.set_fontsize(20)  
  plt.tight_layout()
  plt.show()

def show_banking_historic(deliveries, deposits, revenues, average_revenues, key_list, year_start, year_end, min_rev, max_rev, rev_int, min_del, max_del, del_int, legend_loc):
  record_start = 1905
  index_start = int(year_start - record_start - 1)
  index_end = int(year_end - record_start - 1)
  period_revenue = revenues[index_start:index_end]
  period_delivery = deliveries[index_start:index_end]
  period_deposit = deposits[index_start:index_end]

  budget_gap = np.zeros(len(period_revenue_swp))

  budget_gap_swp[0] = period_revenue_swp[0] - averages_swp
  budget_gap_cvp[0] = period_revenue_cvp[0] - averages_cvp

  for y in range(1,len(period_revenue_swp)):
    budget_gap_swp[y] = period_revenue_swp[y] - averages_swp + budget_gap_swp[y-1]
  for y in range(1,len(period_revenue_cvp)):
    budget_gap_cvp[y] = period_revenue_cvp[y] - averages_cvp + budget_gap_cvp[y-1]

  period_length = len(period_delivery_swp)
	  
  sns.set()
  fig = plt.figure()
  ax1 = fig.add_subplot(1,1,1)
  ax1.fill_between(np.arange(period_length),np.zeros(period_length),period_delivery_cvp, color = 'blue', alpha = 0.25)
  ax1.fill_between(np.arange(period_length),period_delivery,period_deposit + period_delivery, color = 'blue', alpha = 0.75)
  sq1 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.25, markersize = 25, markerfacecolor = 'blue')
  sq2 = Line2D([0], [0], linestyle = "none", marker = "s", alpha = 0.75, markersize = 25, markerfacecolor = 'blue')
  ax1.set_xlabel('Historical Sample Year')
  ax1.set_xlim([0.0, period_length - 1])
  plt.xticks(np.arange(period_length), range(year_start,(year_end+1)))
  ax1.set_ylabel('Annual Banking Use (tAF)', color = 'blue')
  ax1.set_ylim([min_del, max_del])
  plt.yticks(range(int(min_del),int(max_del+del_int),int(del_int)))
  ax2 = ax1.twinx()
  p1 = ax2.plot(period_revenue_cvp, linewidth = 5, color = 'red')
  ax2.plot(np.ones(len(revenues_cvp))*averages_cvp, linewidth = 5, linestyle = 'dashed', color = 'black')
  p2 = ax2.plot(np.ones(len(revenues_cvp))*averages_cvp, linewidth = 5, linestyle = 'dashed', color = 'black')
  ax2.set_ylabel('Annual Revenues ($MM)', color = 'red')
  ax2.set_ylim([min_rev,max_rev])
  plt.yticks(range(int(min_rev),int(max_rev+rev_int),int(rev_int)))
  if legend_loc == 1:
    ax1.legend((sq1, sq2, p1[0], p2[0]), ('Deliveries', 'Withdrawals', 'Annual Banking Reveue', 'Average Banking Revenue'), bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 18)
  else:
    ax1.legend((sq1, sq2, p1[0], p2[0]), ('Deliveries', 'Withdrawals', 'Annual Banking Reveue', 'Average Banking Revenue'), fontsize = 18)

  plt.tight_layout()
  for item in [ax1.xaxis.label, ax1.yaxis.label, ax2.yaxis.label]:
    item.set_fontsize(22)  
  for item in (ax1.get_xticklabels() + ax1.get_yticklabels() + ax2.get_yticklabels()):
    item.set_fontsize(20)  
  plt.tight_layout()
  plt.show()
  
  fig = plt.figure()
  ax1 = fig.add_subplot(1,1,1)
  sns.set()
  ax1.fill_between(np.arange(period_length),np.zeros(period_length),period_delivery_swp, color = 'blue', alpha = 0.25)
  ax1.fill_between(np.arange(period_length),period_delivery_swp,period_delivery_swp + period_withdrawal_swp, color = 'blue', alpha = 0.75)
  
  ax1.fill_between(np.arange(period_length),period_delivery_swp +  + period_withdrawal_swp,period_delivery_swp + period_delivery_cvp + period_withdrawal_swp, color = 'red', alpha = 0.25)
  ax1.fill_between(np.arange(period_length),period_delivery_swp + period_delivery_cvp + period_withdrawal_swp,period_delivery_swp + period_delivery_cvp + period_withdrawal_swp+period_withdrawal_cvp, color = 'red', alpha = 0.75)

  ax1.set_xlabel('Historical Sample Year')
  ax1.set_xlim([0.0, period_length - 1])
  plt.xticks(np.arange(period_length), range(year_start,(year_end+1)))
  ax1.set_ylabel('Annual Banking Use (tAF)')
  ax1.set_ylim([min_del, max_del])
  plt.yticks(range(int(min_del),int(max_del+del_int),int(del_int)))
  #ax2 = ax1.twinx()
  #ax2.plot(budget_gap_swp, linewidth = 5, color = 'red')
  #ax2.set_ylabel('Cumulative Revenue Shortfall ($MM)', color = 'red')
  #ax2.set_ylim([min_rev,max_rev])
  #plt.yticks(range(int(min_rev),int(max_rev+rev_int),int(rev_int)))
  ax1.legend(('Metropolitan Deliveries','Metropolitan Withdrawals', 'Cross Valley Deliveries', 'Cross Valley Withdrawals'), fontsize = 18)
  plt.tight_layout()
  for item in [ax1.xaxis.label, ax1.yaxis.label]:
    item.set_fontsize(22)  
  for item in (ax1.get_xticklabels() + ax1.get_yticklabels()):
    item.set_fontsize(20)  
  plt.tight_layout()
  plt.show()

  
  
def show_contract_types(contract_results, contract_key):
  contract_deliveries = contract_results[contract_key + '_contract']
  flood_deliveries = contract_results[contract_key + '_flood']
  carryover_deliveries = contract_results[contract_key + '_carryover']
  turnback_deliveries = contract_results[contract_key + '_turnback']
  
  fig = plt.figure()
  ax1 = fig.add_subplot(221)
  sns.set()
  sns.distplot(contract_deliveries, hist=False, kde = True, kde_kws = {'shade' : True, 'linewidth' : 3}).set(xlim=(0))
  ax1.set_xlabel('Table A Deliveries (tAF)')
  ax1.set_ylabel('Probability')
  plt.yticks([])

  ax2 = fig.add_subplot(222)
  sns.set()
  sns.distplot(flood_deliveries, hist=False, kde = True, kde_kws = {'shade' : True, 'linewidth' : 3}).set(xlim=(0))
  ax2.set_xlabel('Article 21 Deliveries (tAF)')
  ax2.set_ylabel('Probability')
  plt.yticks([])

  ax3 = fig.add_subplot(223)
  sns.set()
  sns.distplot(carryover_deliveries, hist=False, kde = True, kde_kws = {'shade' : True, 'linewidth' : 3}).set(xlim=(0))
  ax3.set_xlabel('SWP Carryover Storage Deliveries (tAF)')
  ax3.set_ylabel('Probability')
  plt.yticks([])

  ax4 = fig.add_subplot(224)
  sns.set()
  sns.distplot(turnback_deliveries, hist=False, kde = True, kde_kws = {'shade' : True, 'linewidth' : 3}).set(xlim=(0))
  ax4.set_xlabel('SWP Turnback Pool Deliveries (tAF)')
  ax4.set_ylabel('Probability')
  plt.yticks([])

  for item in [ax4.xaxis.label, ax4.yaxis.label, ax1.xaxis.label, ax1.yaxis.label, ax2.xaxis.label, ax2.yaxis.label, ax3.xaxis.label, ax3.yaxis.label]:
    item.set_fontsize(14)  
  for item in (ax4.get_xticklabels() + ax4.get_yticklabels() + ax1.get_xticklabels() + ax1.get_yticklabels() + ax2.get_xticklabels() + ax2.get_yticklabels() + ax3.get_xticklabels() + ax3.get_yticklabels()):
    item.set_fontsize(14)  

  plt.tight_layout()
  plt.show()

def show_pumping_pdf(annual_pumping, project, max_pumping, thresholds, threshold_list):
  init_plotting()
  sns.set()
  
  sorted_pumping = np.sort(annual_pumping)
  percentages = {}
  for x,y in zip(thresholds, threshold_list):
    percentages[y] = sorted_pumping[int(np.floor(x*len(annual_pumping))-1)]
  
  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  kde = stats.gaussian_kde(annual_pumping)
  first_endpoint = 0.0
  total_divisions = len(percentages) - 1
  counter = total_divisions 
  legend_dict = {}
  plot_color = 'red'
  for z in percentages:
    if counter == 0:
      plot_color = 'blue'
      counter = 1
    pos = np.linspace(first_endpoint, percentages[z], 101)
    legend_dict[z] = plt.fill_between(pos, kde(pos), alpha = counter/total_divisions, facecolor = plot_color)
    plt.xlabel('Annual ' + project +' (tAF)')
    plt.ylabel('Probability')
    plt.xlim([0.0, max_pumping])
    plt.yticks([])
    for item in [ax0.xaxis.label, ax0.yaxis.label]:
      item.set_fontsize(20)  
    for item in (ax0.get_xticklabels()):
      item.set_fontsize(16) 
    first_endpoint = percentages[z]
    counter -= 1
  legend_obj = tuple([legend_dict[e] for e in legend_dict])
  legend_names = tuple(threshold_list)
  plt.legend(legend_obj, legend_names, bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)
  plt.show()
  
def find_insurance_mitigation(annual_pumping, district_revenues, target_revenue, evaluation_length, insurance_cost, insurance_strike, insurance_payout, contingency_fund_start, min_loss):
  total_revenue = np.zeros((evaluation_length, len(district_revenues)))
  annual_contribution = contingency_fund_start*1.96/evaluation_length
  for y in range(0, len(district_revenues)):
    contingency_fund = contingency_fund_start
    for yy in range(y, y+evaluation_length):
      if yy > (len(district_revenues)-1):
        y_adjust = len(district_revenues)
      else:
        y_adjust = 0
   
      insurance_payment = insurance_payout[0]*max(insurance_strike - annual_pumping[yy - y_adjust], 0.0)
      if insurance_strike > annual_pumping[yy-y_adjust]:
        insurance_payment += insurance_payout[1]
      if district_revenues[yy-y_adjust] > target_revenue:
        total_revenue[yy-y][y] = target_revenue - annual_contribution - insurance_cost
        contingency_fund += insurance_payment + district_revenues[yy-y_adjust] - target_revenue
      else:
        contingency_fund += (district_revenues[yy-y_adjust] - target_revenue + insurance_payment)
        total_revenue[yy-y][y] = target_revenue - annual_contribution - insurance_cost + min(contingency_fund,0.0)
      if contingency_fund < 0.0:
        contingency_fund = 0.0

  average_revenue = target_revenue - annual_contribution - insurance_cost
  
  return total_revenue, average_revenue
  
def show_insurance_payouts(annual_pumping, revenue_dict, color_dict, alpha_dict, strike, contract_type, name, plot_max, animate):
  max_revenue = 0.0
  for x in revenue_dict:
    max_revenue = np.max([max_revenue, np.max(revenue_dict[x])])
  counter = 0
  legend_dict = {}
  strike_years = annual_pumping < strike
  non_risk = annual_pumping > strike
  insurance_range = np.arange(int(strike))
  
  init_plotting()
  sns.set()
  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  for x in revenue_dict:
    current_revenues = revenue_dict[x]
    legend_dict[x] = plt.scatter(annual_pumping, current_revenues, s=75, c=color_dict[x], edgecolor='none', alpha=alpha_dict[x])
    expected_revenue = np.max(current_revenues[strike_years])
    min_revenue = np.min(current_revenues)
    mean_non_risk = np.mean(current_revenues[non_risk])
    mean_risk = np.mean(current_revenues[strike_years])

    if counter == len(revenue_dict) -1 :
      print(mean_non_risk, end = " ")
      print(mean_risk)
      ax2 = plt.plot(insurance_range, min_revenue*np.ones(len(insurance_range)), color = 'red', linewidth = 3)
      ax3 = plt.plot(insurance_range, expected_revenue*np.ones(len(insurance_range)), color = 'red', linewidth = 3)
      ax4 = plt.plot(np.zeros(2), [min_revenue, expected_revenue], color = 'red', linewidth = 3)
      ax5 = plt.plot(strike*np.ones(2), [min_revenue, expected_revenue], color = 'red', linewidth = 3)
      legend_dict['At Risk Years'] = plt.fill_between(insurance_range,min_revenue*np.ones(len(insurance_range)),expected_revenue*np.ones(len(insurance_range)), color = 'red', alpha = 0.25)
      p = ax0.plot([0.0, np.max(annual_pumping)],[mean_non_risk, mean_non_risk], linestyle = 'dashed', color = 'black', linewidth = 3)
      legend_dict['Mean Revenue, Normal'] = p[0]
      ax7 = plt.plot([0.0, np.max(annual_pumping)],[mean_non_risk, mean_non_risk], linestyle = 'dashed', color = 'black', linewidth = 3)
      p2 = ax0.plot([0.0, np.max(annual_pumping)],[mean_risk, mean_risk], linestyle = 'dashed', color = 'red', linewidth = 3)
      legend_dict['Mean Revenue, At-Risk'] = p2[0]
      ax8 = plt.plot([0.0, np.max(annual_pumping)],[mean_risk, mean_risk], linestyle = 'dashed', color = 'red', linewidth = 3)
	
    plt.xlim((np.min(annual_pumping)-25.0, np.max(annual_pumping)+25.0))
    plt.ylim((0,plot_max))  
    plt.xlabel('Total ' + contract_type +' (tAF)')
    plt.ylabel(name + ' Annual Revenue ($MM)')
    counter += 1
	
  legend_obj = tuple([legend_dict[e] for e in legend_dict])
  legend_names = tuple(legend_dict)
  plt.legend(legend_obj, legend_names, bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)	  
  plt.show()
  
  
def make_revenue_cumulative(revenue_series, insurance_series, control_level):
  numYears = len(revenue_series)
  cumulative_revenue = np.zeros(numYears)
  c_counter = 0.0
  target_revenue = np.mean(revenue_series)
  for x in range(0,numYears):
    c_counter += revenue_series[x] + insurance_series[x] - target_revenue
    if revenue_series[x]  + insurance_series[x]- target_revenue > 0.0:
      if c_counter > 0.0:
        cumulative_revenue[x] = revenue_series[x] +insurance_series[x] - target_revenue
      else:
        cumulative_revenue[x] = 0.0
    else:
      cumulative_revenue[x] = c_counter
    if c_counter > 0.0:
      c_counter = 0.0

	  
  sorted_cumulative = np.sort(cumulative_revenue)
  cumulative_index = np.argsort(cumulative_revenue)

  fund_size = {}
  value_at_risk = {}
  percentiles = {}
  var = {}
  percentiles['100'] = 0.99
  percentiles['10'] = 0.1
  percentiles['5'] = 0.05
  value_risk_list = ['99', '95', '80', '20', '5', '1']
  var['99'] = 0.99
  var['95'] = 0.95
  var['80'] = 0.8
  var['20'] = 0.2
  var['5'] = 0.05
  var['1'] = 0.01
  index_value = np.floor(len(sorted_cumulative)*percentiles[control_level])
  if control_level == '100':
    fund_size = 0.0
  else:
    fund_size = sorted_cumulative[int(index_value)]*-1.0
  annual_losses = np.zeros(len(revenue_series))
  for y in range(0,len(revenue_series)):
    this_year_losses = revenue_series[cumulative_index[y]] + insurance_series[cumulative_index[y]] - target_revenue
    accounting_losses = min(sorted_cumulative[y] + fund_size, 0.0)
    if this_year_losses > 0.0:
      annual_losses[y] = min(this_year_losses, sorted_cumulative[y])
    else:
      annual_losses[y] = max(this_year_losses, accounting_losses)
  for v in value_risk_list:
    index_value = np.floor(len(revenue_series)*var[v])
    sorted_losses = np.sort(annual_losses)
    value_at_risk[v] = sorted_losses[int(index_value)]
	  
  return value_at_risk, fund_size, target_revenue  
	  
def find_bar_shapes(value_at_risk, target_revenue, annual_cost):
  bar_shapes = {}
  percentile_groups = ['1_loss', '5_loss', '20_loss', '20_gain', '5_gain', '1_gain']
  value_risk_list = ['1', '5', '20', '80', '95', '99']
  percentile_values = [.01, .05, .2, .8 , .95, .99]
  for percentile in percentile_groups:
    bar_shapes[percentile] = np.zeros(5)
  for i,v in enumerate(['none', 'CF', 'CF2','insurance','insurance2']):
    counter = 0
    for x,y in zip(percentile_groups, value_risk_list):
      bar_shapes[x][i] = value_at_risk[v][y] + target_revenue[v] - annual_cost[v]['contribution'] - annual_cost[v]['premium']
      #if counter < 3:
        #bar_shapes[x][i] = value_at_risk[v][y] + target_revenue[v] - annual_cost[v]['contribution'] - annual_cost[v]['premium']
      #elif v == 'none':
        #bar_shapes[x][i] = value_at_risk[v][y] + target_revenue[v]
      #else:
        #bar_shapes[x][i] = target_revenue[v] - annual_cost[v]['contribution'] - annual_cost[v]['premium']

      counter += 1		
		
  return bar_shapes

def show_mitigation_plots(revenue_series, annual_pumping, insurance_cutoff, control_risk, contingency_increments, insurance_increments, evaluation_length, interest_rate, insurance_premium, name):
  mitigation_dict = {}
  mitigation_dict['none'] = np.zeros((evaluation_length, len(revenue_series)))
  for x in range(0,evaluation_length):
    mitigation_dict['none'][x] = revenue_series
  average_revenue = {}
  average_revenue['none'] = np.mean(revenue_series)
  average_revenue['CF'] = {}
  average_revenue['insurance'] = {}
  value_at_risk = {}
  mitigation_dict['CF'] = np.zeros((contingency_increments, evaluation_length, len(annual_pumping)))
  mitigation_dict['insurance'] = np.zeros((contingency_increments*insurance_increments, evaluation_length, len(annual_pumping)))
  average_revenue['CF'] = np.zeros(contingency_increments)
  average_revenue['insurance'] = np.zeros(contingency_increments*insurance_increments)

  annual_cost = {}
  annual_cost['CF'] = {}
  annual_cost['CF']['contribution'] = np.zeros(contingency_increments)
  annual_cost['CF']['premium'] = np.zeros(contingency_increments)
  annual_cost['insurance'] = {}
  annual_cost['insurance']['contribution'] = np.zeros(contingency_increments*insurance_increments)
  annual_cost['insurance']['premium'] = np.zeros(contingency_increments*insurance_increments)

  for contingency_index in range(0,contingency_increments):
    contingency_fund_start = 2.0*contingency_index*average_revenue['none']/contingency_increments
    insurance_strike = 0.0
    insurance_cost = 0.0
    insurance_payout = np.zeros(2)
    mitigation_dict['CF'][contingency_index][:][:], average_revenue['CF'][contingency_index] = find_insurance_mitigation(annual_pumping, revenue_series, average_revenue['none'], int(evaluation_length), insurance_cost, insurance_strike, insurance_payout, contingency_fund_start, insurance_cutoff)
    annual_cost['CF']['contribution'][contingency_index] = contingency_fund_start*interest_rate*((1.0+interest_rate)**evaluation_length)/(((1.0+interest_rate)**evaluation_length)-1) 
    
  for contingency_index in range(0,contingency_increments):
    contingency_fund_start = 0.5*contingency_index*average_revenue['none']/contingency_increments
    for insurance_index in range(0, insurance_increments):
      insurance_strike = insurance_index*50.0 + 1000.0
      insurance_payout = find_insurance_payment_constant(annual_pumping, revenue_series, insurance_strike)
      insurance_cost = price_insurance(annual_pumping, insurance_strike, insurance_payout, 1.0+insurance_premium)
      insurance_payment = insurance_payout[0]*max(insurance_strike - annual_pumping[yy - y_adjust], 0.0)
      if insurance_strike > annual_pumping[yy-y_adjust]:
        insurance_payment += insurance_payout[1]


      mitigation_dict['insurance'][contingency_index*insurance_increments + insurance_index][:][:], average_revenue['insurance'][contingency_index*insurance_increments + insurance_index] = find_insurance_mitigation(annual_pumping, revenue_series, average_revenue['none'], int(evaluation_length), insurance_cost, insurance_strike, insurance_payout, contingency_fund_start, insurance_cutoff) 
      annual_cost['insurance']['contribution'][contingency_index*insurance_increments + insurance_index] = contingency_fund_start*interest_rate*((1.0+interest_rate)**evaluation_length)/(((1.0+interest_rate)**evaluation_length)-1) 
      annual_cost['insurance']['premium'][contingency_index*insurance_increments + insurance_index] = insurance_cost
   
  for type in ['none', 'CF', 'insurance']:
    if type == 'CF':
      value_at_risk[type] = np.zeros(contingency_increments)
      for contingency_index in range(0,contingency_increments):
        value_at_risk[type][contingency_index] = show_value_at_risk(mitigation_dict[type][contingency_index], average_revenue[type][contingency_index], control_risk)
    elif type == 'insurance':
      value_at_risk[type] = np.zeros(contingency_increments*insurance_increments)
      for insurance_index in range(0,contingency_increments*insurance_increments):
        value_at_risk[type][insurance_index] = show_value_at_risk(mitigation_dict[type][insurance_index], average_revenue[type][insurance_index], control_risk)
    else:
      value_at_risk[type] = 0.0
      value_at_risk[type] = show_value_at_risk(mitigation_dict[type], average_revenue[type], control_risk)

	
  contingency_figure_index = find_index(value_at_risk['CF'], average_revenue['CF'], insurance_cutoff)
  insurance_figure_index = find_index(value_at_risk['insurance'], average_revenue['insurance'], value_at_risk['CF'][contingency_figure_index])
 
  bar_shapes = find_revenue_buckets(mitigation_dict, contingency_figure_index, insurance_figure_index,evaluation_length, contingency_increments, insurance_increments)
  show_revenue_variability(bar_shapes, average_revenue, contingency_figure_index, insurance_figure_index, annual_cost, max(mitigation_dict['none'][0]), name)
 
def find_insurance_payment(annual_pumping, district_revenues, strike):
  payout_years = annual_pumping < strike
  payout_pumping = annual_pumping[payout_years]
  payout_revenues = district_revenues[payout_years]
  if len(payout_pumping > 1):
    insurance_payout = np.polyfit(payout_pumping, payout_revenues, 1)	
  else:
    insurance_payout = np.zeros(2)
  insurance_payout[1] = 0.0
	
  return insurance_payout
  
def make_insurance_series(annual_pumping, insurance_strike, revenue_series, pay_frac):
  insurance_payout = find_insurance_payment_constant(annual_pumping, revenue_series, insurance_strike)
  insurance_revenues = np.zeros(len(annual_pumping))
  for x in range(0, len(annual_pumping)):
    if insurance_strike > annual_pumping[x]:
        insurance_revenues[x] = insurance_payout[1]*pay_frac

  return insurance_revenues
  
def find_insurance_payment_constant(annual_pumping, district_revenues, strike):
  payout_years = annual_pumping < strike
  non_payout_years = annual_pumping > strike
  mean_payout = np.mean(district_revenues[payout_years])
  mean_non_payout = np.mean(district_revenues[non_payout_years])
  insurance_payout = np.zeros(2)
  insurance_payout[1] = mean_non_payout - mean_payout  
	
  return insurance_payout

	
def price_insurance(annual_pumping, insurance_strike, insurance_payout, insurance_premium):
  insurance_cost = 0.0
  for y in range(0, len(annual_pumping)):
    revenue_shortfall = insurance_payout[0]*max(insurance_strike - annual_pumping[y], 0.0)
    if insurance_strike > annual_pumping[y]:
      revenue_shortfall += insurance_payout[1]
	  
    insurance_cost += revenue_shortfall*insurance_premium/len(annual_pumping)

  return insurance_cost	  
  
def show_value_at_risk(district_revenue, average_revenue, percentile):
  a = district_revenue.shape
  numYears = a[1]
  numEval = a[0]
  value_at_risk = 0.0
  for x in range(0, numEval):
    risk = np.zeros(numYears)
    for y in range(0,numYears):
      risk[y] = max(average_revenue - district_revenue[x][y], 0.0)
    contingent_risk = np.sort(risk)
    percentile_index = int(np.ceil(percentile*numYears))
    value_at_risk = max(contingent_risk[percentile_index], value_at_risk)
  
  return value_at_risk
  
def find_index(values, averages, max_value):
  sorted_values = np.sort(values)
  sorted_index = np.argsort(values)
  for x in range(0,len(values)):
    check_value = sorted_values[x]
    if check_value > max_value:
      break
  max_rev = 0.0
  max_rev_spot = x
  sorted_averages = averages[sorted_index]
  end_loc = x

  for y in range(0,end_loc):
    if sorted_averages[y] > max_rev:
      max_rev_spot = y
      max_rev = sorted_averages[y]
	
  return sorted_index[max_rev_spot]

	
def find_revenue_buckets(revenues, contingency_index, insurance_index, numEval, contInc, insInc):
  bar_shapes = {}
  percentile_groups = ['1_loss', '5_loss', '20_loss', '20_gain', '5_gain', '1_gain']
  percentile_values = [.01, .05, .2, .8 , .95, .99]
  for percentile in percentile_groups:
    bar_shapes[percentile] = np.ones(3)*999999
	
  for i,v in enumerate(['none', 'CF', 'insurance']):
    for xx in range(0, numEval):
      if v == 'CF':
        sorted_values = np.sort(revenues[v][contingency_index][xx])

      elif v == 'insurance':
        sorted_values = np.sort(revenues[v][insurance_index][xx])

      else:
        sorted_values = np.sort(revenues[v][xx])

      numYears = len(sorted_values)
      for ii,vv in enumerate(percentile_groups):
        percentile_index = int(np.ceil(percentile_values[ii]*numYears))
        bar_shapes[vv][i] = min(sorted_values[percentile_index],bar_shapes[vv][i])
		
  return bar_shapes
  
def compare_mitigation_performance(revenue_series, annual_pumping, premium_rate, control_level, insurance_strike, insurance_payment, name):
  value_at_risk = {}
  value_at_risk['none'] = {}
  value_at_risk['CF'] = {}
  value_at_risk['insurance'] = {}
  value_at_risk['CF2'] = {}
  value_at_risk['insurance2'] = {}
  fund_size = {}

  annual_cost = {}
  annual_cost['none'] = {}
  annual_cost['CF'] = {}
  annual_cost['insurance'] = {}
  annual_cost['CF2'] = {}
  annual_cost['insurance2'] = {}

  average_revenue = {}
  value_at_int0, fund_size['none'], average_revenue['none'] = make_revenue_cumulative(revenue_series, np.zeros(len(revenue_series)), '100')
  for x in value_at_int0:
    value_at_risk['none'][x] = value_at_int0[x]

  value_at_int, fund_size['CF'], average_revenue['CF'] = make_revenue_cumulative(revenue_series, np.zeros(len(revenue_series)), control_level[0])
  for x in value_at_int:
      value_at_risk['CF'][x] = value_at_int[x]
  value_at_int, fund_size['CF2'], average_revenue['CF2'] = make_revenue_cumulative(revenue_series, np.zeros(len(revenue_series)), control_level[1])
  for x in value_at_int:
      value_at_risk['CF2'][x] = value_at_int[x]


  insurance_revenues = make_insurance_series(annual_pumping, insurance_strike, revenue_series, insurance_payment[0])
  value_at_int2, fund_size['insurance'], average_revenue['insurance'] = make_revenue_cumulative(revenue_series, insurance_revenues, control_level[0])
  for x in value_at_int2:
    value_at_risk['insurance'][x] = value_at_int2[x]
  insurance_revenues2 = make_insurance_series(annual_pumping, insurance_strike, revenue_series, insurance_payment[1])
  value_at_int2, fund_size['insurance2'], average_revenue['insurance2'] = make_revenue_cumulative(revenue_series, insurance_revenues2, control_level[1])
  for x in value_at_int2:
    value_at_risk['insurance2'][x] = value_at_int2[x]


  annual_cost['none']['contribution'] = 0.0
  annual_cost['none']['premium'] = 0.0
  annual_cost['CF']['contribution'] = fund_size['CF']*1.96/30
  annual_cost['CF2']['contribution'] = fund_size['CF2']*1.96/30

  annual_cost['insurance']['contribution'] = fund_size['insurance']*1.96/30
  annual_cost['insurance2']['contribution'] = fund_size['insurance2']*1.96/30

  annual_cost['CF']['premium'] = 0.0
  annual_cost['insurance']['premium'] = np.mean(insurance_revenues)*(1.0+premium_rate)
  annual_cost['CF2']['premium'] = 0.0
  annual_cost['insurance2']['premium'] = np.mean(insurance_revenues2)*(1.0+premium_rate)
  print(value_at_risk)
  print(average_revenue)
  print(annual_cost)
  bar_shapes = find_bar_shapes(value_at_risk, average_revenue, annual_cost)
  plot_bar_shapes(bar_shapes, average_revenue, annual_cost, np.ceil(bar_shapes['1_gain'][0]), name)
  
def plot_almond_costs():

  init_plotting()
  sns.set()

  bar_shapes = np.zeros(25)
  cost_shapes = np.zeros(25)
  bar_locations = np.arange(25)
  fig = plt.figure()
  ax0 = fig.add_subplot(111)
  bar_shapes[0] = 0.0
  bar_shapes[1] = 0.0
  bar_shapes[2] = 1.35
  bar_shapes[3] = 2.7
  bar_shapes[4] = 5.4
  bar_shapes[5] = 11.1
  cost_shapes[0] = -5.8
  cost_shapes[1] = -3.0
  cost_shapes[2] = -4.0
  cost_shapes[3] = -5.5
  cost_shapes[4] = -6.0
  cost_shapes[5] = -6.2

  for x in range(6, 25):
    bar_shapes[x] = 11.1
    cost_shapes[x] = -6.2
	
  ax1 = plt.bar(bar_locations, bar_shapes, 0.8, bottom = np.zeros(25), color = 'blue', alpha = 0.25)
  p0 =  plt.bar(bar_locations, bar_shapes, 0.8, bottom = np.zeros(25), edgecolor = ['blue']*len(bar_locations), linewidth = 1, color = 'None')
  ax2 = plt.bar(bar_locations, np.zeros(25) - cost_shapes, 0.8, bottom = cost_shapes, color = 'red', alpha = 0.25)
  p0 =  plt.bar(bar_locations, np.zeros(25) - cost_shapes, 0.8, bottom = cost_shapes, edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  
  plt.ylabel('Annual Costs and Revenues ($1000/acre)')
  plt.xlabel('Almond Life')
  plt.ylim([-10, 15])
  plt.legend((ax1, ax2), ('Revenue', 'Cost'), fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  

  
  plt.show()
  
def plot_bar_shapes(bar_shapes, averages, annual_cost, max_revenue, name):	
  
  bar_shapes['cont'] = np.zeros(5)
  bar_shapes['premium'] = np.zeros(5)
  bar_shapes['average'] = np.zeros(5)
  bar_shapes['zero'] = np.zeros(5)
  bar_locations = np.arange(5)  
  legend_dict = {}
  legend_list = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue', 'Annual Contingency Fund Contribution', 'Annual Insurance Premium', 'Expected Revenue']
  top_threshold_list = ['average', '20_loss', '5_loss', '20_gain', '5_gain', '1_gain', 'zero', 'cont']
  bottom_threshold_list = ['20_loss', '5_loss', '1_loss', 'average', '20_gain', '5_gain', 'cont', 'premium']
  color_shade = [0.75, 0.5, 0.25, 0.75, 0.5, 0.25, 0.75, 0.25]
  color_list = ['red', 'red', 'red', 'blue', 'blue', 'blue', 'green', 'green']
  for i,v in enumerate(['none', 'CF', 'CF2','insurance','insurance2']):
    if v == 'CF':
      bar_shapes['average'][i] = averages[v] - (annual_cost[v]['premium']+ annual_cost[v]['contribution'])
      bar_shapes['cont'][1] = annual_cost[v]['contribution']*-1
      bar_shapes['premium'][1] = (annual_cost[v]['premium']+ annual_cost[v]['contribution'])*-1
    elif v == 'CF2':
      bar_shapes['average'][i] = averages[v] - (annual_cost[v]['premium']+ annual_cost[v]['contribution'])
      bar_shapes['cont'][2] = annual_cost[v]['contribution']*-1
      bar_shapes['premium'][2] = (annual_cost[v]['premium']+ annual_cost[v]['contribution'])*-1
    elif v == 'insurance':
      bar_shapes['average'][i] = averages[v] - (annual_cost[v]['premium']+ annual_cost[v]['contribution'])
      bar_shapes['cont'][3] = annual_cost[v]['contribution']*-1
      bar_shapes['premium'][3] = (annual_cost[v]['premium']+ annual_cost[v]['contribution'])*-1
    elif v == 'insurance2':
      bar_shapes['average'][i] = averages[v] - (annual_cost[v]['premium']+ annual_cost[v]['contribution'])
      bar_shapes['cont'][4] = annual_cost[v]['contribution']*-1
      bar_shapes['premium'][4] = (annual_cost[v]['premium']+ annual_cost[v]['contribution'])*-1

    else:
      bar_shapes['average'][i] = averages[v]
	  
  max_cost = np.floor(min(bar_shapes['premium'])-0.5)
  print(max_cost)
  print(min(bar_shapes['premium']))
  animation_loop = {}
  location_loop = {}
  set_to_loop = {}
  animation_loop['1'] = ['Expected Revenue']
  animation_loop['2'] = ['20% Chance of Lower Revenue','Expected Revenue']
  animation_loop['3'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue','Expected Revenue']
  animation_loop['4'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue','Expected Revenue']
  animation_loop['5'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['6'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['7'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['8'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['9'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['10'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue', 'Annual Contingency Fund Contribution', 'Annual Insurance Premium','Expected Revenue']

  location_loop['1'] = [0,]
  location_loop['2'] = [0,]
  location_loop['3'] = [0,]
  location_loop['4'] = [0,]
  location_loop['5'] = [0,]
  location_loop['6'] = [0,1]
  location_loop['7'] = [0,1,2]
  location_loop['8'] = [0,1,2,3]
  location_loop['9'] = [0,1,2,3,4]
  location_loop['10'] = [0,1,2,3,4]
  for animation in animation_loop:
    current_block = animation_loop[animation]
    current_space = location_loop[animation]
    new_bar_shapes = {}
    for aa in bar_shapes:
      new_bar_shapes[aa] = np.zeros(5)
    for yy in range(0,len(bar_shapes['average'])):
      counter = 0
      for zz in current_space:
        if zz == yy:
          counter = 1
      if counter == 1:
        for aa in bar_shapes:
          new_bar_shapes[aa][yy] = bar_shapes[aa][yy]
      else:
        for aa in bar_shapes:
          new_bar_shapes[aa][yy] = 0.0
    fig = plt.figure()
    ax0 = fig.add_subplot(111) 
    for x,y,z,shade,color_fill in zip(legend_list, top_threshold_list, bottom_threshold_list, color_shade, color_list):
      counter = 0
      for aa in animation_loop[animation]:
        if aa == x:
          legend_dict[x] = plt.bar(bar_locations, new_bar_shapes[y] - new_bar_shapes[z], 0.5, bottom = new_bar_shapes[z], color = color_fill, alpha = shade)
          p0 =  plt.bar(bar_locations, new_bar_shapes[y] - new_bar_shapes[z], 0.5, bottom = new_bar_shapes[z], edgecolor = [color_fill]*len(bar_locations), linewidth = 1, color = 'None')
          counter = 1
      if counter == 0:
        legend_dict[x] = plt.bar(bar_locations, new_bar_shapes[z] - new_bar_shapes[z], 0.5, bottom = new_bar_shapes[z], color = 'None', alpha = 0.1)
    legend_dict['Expected Revenue'] = plt.bar(bar_locations, new_bar_shapes['average'], 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")

    plt.ylabel(name + ' Annual Revenue ($MM)')
    plt.ylim([max_cost, max_revenue])
    legend_names = tuple(legend_list)
    legend_object = tuple(legend_dict[e] for e in legend_dict)
    plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund (A)','Contingency Fund (B)', 'Hybrid Insurance Fund (A)', 'Hybrid Insurance Fund (B)'))
    columns = int(np.ceil(len(legend_object)/3))
    plt.legend(legend_object, legend_names, ncol = columns, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
    for item in [ax0.xaxis.label, ax0.yaxis.label]:
      item.set_fontsize(20)  
    for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
      item.set_fontsize(14)  

    plt.show()
    del new_bar_shapes

  
def show_revenue_variability(bar_shapes, averages, contingency_index, insurance_index, annual_cost, max_revenue, name):	
  
  bar_shapes['cont'] = np.zeros(3)
  bar_shapes['premium'] = np.zeros(3)
  bar_shapes['average'] = np.zeros(3)
  bar_shapes['zero'] = np.zeros(3)
  bar_locations = np.arange(3)  
  legend_dict = {}
  legend_list = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue', 'Annual Contingency Fund Contribution', 'Annual Insurance Premium', 'Expected Revenue']
  top_threshold_list = ['average', '20_loss', '5_loss', '20_gain', '5_gain', '1_gain', 'zero', 'cont']
  bottom_threshold_list = ['20_loss', '5_loss', '1_loss', 'average', '20_gain', '5_gain', 'cont', 'premium']
  color_shade = [0.75, 0.5, 0.25, 0.75, 0.5, 0.25, 0.75, 0.25]
  color_list = ['red', 'red', 'red', 'blue', 'blue', 'blue', 'green', 'green']
  for i,v in enumerate(['none', 'CF', 'insurance']):
    if v == 'CF':
      bar_shapes['average'][i] = averages[v][contingency_index]
      bar_shapes['cont'][1] = annual_cost[v]['contribution'][contingency_index]*-1
      bar_shapes['premium'][1] = (annual_cost[v]['premium'][contingency_index]+ annual_cost[v]['contribution'][contingency_index])*-1
    elif v == 'insurance':
      bar_shapes['average'][i] = averages[v][insurance_index]
      bar_shapes['cont'][2] = annual_cost[v]['contribution'][insurance_index]*-1
      bar_shapes['premium'][2] = (annual_cost[v]['premium'][insurance_index]+ annual_cost[v]['contribution'][insurance_index])*-1
    else:
      bar_shapes['average'][i] = averages[v]
	  
  max_cost = np.floor(min(bar_shapes['premium']))
  animation_loop = {}
  location_loop = {}
  set_to_loop = {}
  animation_loop['1'] = ['Expected Revenue']
  animation_loop['2'] = ['20% Chance of Lower Revenue','Expected Revenue']
  animation_loop['3'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue','Expected Revenue']
  animation_loop['4'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue','Expected Revenue']
  animation_loop['5'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['6'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['7'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue','Expected Revenue']
  animation_loop['8'] = ['20% Chance of Lower Revenue', '5% Chance of Lower Revenue', '1% Chance of Lower Revenue', '20% Chance of Greater Revenue', '5% Chance of Greater Revenue', '1% Chance of Greater Revenue', 'Annual Contingency Fund Contribution', 'Annual Insurance Premium','Expected Revenue']

  location_loop['1'] = [0,]
  location_loop['2'] = [0,]
  location_loop['3'] = [0,]
  location_loop['4'] = [0,]
  location_loop['5'] = [0,]
  location_loop['6'] = [0,1]
  location_loop['7'] = [0,1,2]
  location_loop['8'] = [0,1,2]
  for animation in animation_loop:
    current_block = animation_loop[animation]
    current_space = location_loop[animation]
    new_bar_shapes = {}
    for aa in bar_shapes:
      new_bar_shapes[aa] = np.zeros(3)
    for yy in range(0,len(bar_shapes['average'])):
      counter = 0
      for zz in current_space:
        if zz == yy:
          counter = 1
      if counter == 1:
        for aa in bar_shapes:
          new_bar_shapes[aa][yy] = bar_shapes[aa][yy]
      else:
        for aa in bar_shapes:
          new_bar_shapes[aa][yy] = 0.0
    fig = plt.figure()
    ax0 = fig.add_subplot(111) 
    for x,y,z,shade,color_fill in zip(legend_list, top_threshold_list, bottom_threshold_list, color_shade, color_list):
      counter = 0
      for aa in animation_loop[animation]:
        if aa == x:
          legend_dict[x] = plt.bar(bar_locations, new_bar_shapes[y] - new_bar_shapes[z], 0.5, bottom = new_bar_shapes[z], color = color_fill, alpha = shade)
          p0 =  plt.bar(bar_locations, new_bar_shapes[y] - new_bar_shapes[z], 0.5, bottom = new_bar_shapes[z], edgecolor = [color_fill]*len(bar_locations), linewidth = 1, color = 'None')
          counter = 1
      if counter == 0:
        legend_dict[x] = plt.bar(bar_locations, new_bar_shapes[z] - new_bar_shapes[z], 0.5, bottom = new_bar_shapes[z], color = 'None', alpha = 0.1)
    legend_dict['Expected Revenue'] = plt.bar(bar_locations, new_bar_shapes['average'], 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")

    plt.ylabel(name + ' Annual Revenue ($MM)')
    plt.ylim([max_cost, max_revenue])
    legend_names = tuple(legend_list)
    legend_object = tuple(legend_dict[e] for e in legend_dict)
    plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
    columns = int(np.ceil(len(legend_object)/3))
    plt.legend(legend_object, legend_names, ncol = columns, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
    for item in [ax0.xaxis.label, ax0.yaxis.label]:
      item.set_fontsize(20)  
    for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
      item.set_fontsize(14)  

    plt.show()
    del new_bar_shapes
	      
def make_pumping_plots(simulated_results, observed_results, simulated_unit, observed_unit, object_list, title_list, label_loc, freq, freq2):
  init_plotting()
  sns.set()
  fig = plt.figure(figsize=(16, 6)) 
  gs = gridspec.GridSpec(2, 2, width_ratios=[3, 1]) 
  counter = 0
  for x,y  in zip(object_list, title_list):
    sim_values = simulated_results['DEL_' + x]*simulated_unit
    simulated_week = sim_values.resample(freq).mean() * 7.0
    simulated_year = sim_values.resample(freq2).mean() * 365.0
    obs_values = observed_results[x]*observed_unit
    observed_week = obs_values.resample(freq).mean() * 7.0
    observed_year = obs_values.resample(freq2).mean() * 365.0
	
    ax0 = plt.subplot(gs[counter, 0])
    r = np.corrcoef(observed_week.values,simulated_week.values)[0,1]  
    observed_week.plot(ax=ax0, color='k', use_index=True, alpha = 0.7, linewidth = 3)
    simulated_week.plot(ax=ax0, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)
    ax0.set_title('Weekly ' + y + ' Pumping')
    ax0.legend(['Observed', 'Simulated'], ncol=1)
    ax0.set_xlim([datetime.date(1996,10,1), datetime.date(2016,9,30)])
    ax0.set_ylabel('Pumping (tAF)')
    ax0.set_xlabel('')
    ax0.annotate('$R^2 = %.2f$' % r**2, xy=(1400, label_loc[counter]), color='0.1')

    ax22 = plt.subplot(gs[counter,1])
    r = np.corrcoef(observed_year.values,simulated_year.values)[0,1]  
    ax22.scatter(observed_year.values, simulated_year.values, s=75, c='steelblue', edgecolor='none', alpha=0.8)
    ax22.plot([0.0, max([max(observed_year.values), max(simulated_year.values)])], [0.0, max([max(observed_year.values), max(simulated_year.values)])], linestyle = 'dashed', color = 'black', linewidth = 3)    
    ax22.set_ylabel('Simulated (tAF/yr)')
    ax22.set_xlabel('Observed (tAF/yr)')
    ax22.set_title('Annual ' + y + ' Pumping vs. Simulated')
    ax22.annotate('$R^2 = %.2f$' % r**2, xy=(0,max(simulated_year.values) - 300), color='0.1')
    ax22.set_xlim([0.0, ax22.get_xlim()[1]])
    ax22.set_ylim([0.0, ax22.get_ylim()[1]])
     
  
    for item in [ax0.xaxis.label, ax0.yaxis.label, ax22.yaxis.label, ax0.title, ax22.title]:
      item.set_fontsize(14)  
    for item in (ax0.get_xticklabels() + ax22.get_xticklabels() + ax0.get_yticklabels() + ax22.get_yticklabels()):
      item.set_fontsize(14)

    counter += 1	  
  plt.tight_layout()
  plt.show()
  
  
def make_reservoir_plots(simulated_results, observed_results, simulated_unit, observed_unit, object_list, title_list, data_type, dim_1, dim_2, freq):
  init_plotting()
  sns.set()
  fig = plt.figure() 
  gs = gridspec.GridSpec(dim_1, dim_2) 
  counter = 0
  counter2 = 0
  for x,y  in zip(object_list, title_list):
    sim_values = simulated_results[x + data_type]*simulated_unit
    simulated_week = sim_values.resample(freq).mean()
    obs_values = observed_results[x + data_type]*observed_unit
    observed_week = obs_values.resample(freq).mean()
	
    ax0 = plt.subplot(gs[counter,counter2])
    r = np.corrcoef(simulated_week.values, observed_week.values)[0,1]
    observed_week.plot(ax = ax0, color = 'k', use_index = True, alpha = 0.7, linewidth = 3)
    simulated_week.plot(ax = ax0, color = 'indianred', use_index = True, alpha = 0.7, linewidth = 3)
    ax0.set_title(y)
    ax0.set_xlim([datetime.date(1996,10,1), datetime.date(2016,9,30)])
    ax0.set_xlabel('')
    ax0.set_xticklabels('')
    ax0.annotate('$R^2 = %.2f$' % r**2, xy=(1400,min(observed_week)), color='0.1')
	
    for item in [ax0.xaxis.label, ax0.yaxis.label, ax0.title]:
      item.set_fontsize(14)
    for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
      item.set_fontsize(14)
	  
    ax0.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
	
    counter += 1
    if counter == 4:
      counter = 0
      counter2 += 1

	  
  fig.add_subplot(111, frameon=False)
  plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
  plt.grid(False)
  plt.ylabel("Storage (mAF)", fontsize = 14, position = (-0.1, 0.5))

  plt.tight_layout()
  plt.show()

def make_san_luis_plots(simulated_results, observed_results, simulated_unit, observed_unit, object_list, title_list, data_type, freq):
  init_plotting()
  sns.set()
  plot_counter = 0
  fig = plt.figure(figsize=(16, 6)) 
  gs = gridspec.GridSpec(2, 2, width_ratios=[3, 1]) 
  end_of_month = [30, 60, 91, 122, 150, 181, 211, 242, 272, 303, 334, 364]
  
  for x,y  in zip(object_list, title_list):
    counter = 0
    counter_m = 0
    monthly_values_sim = np.zeros(240)
    monthly_values_obs = np.zeros(240)
    leap_year_counter = 3
    total_counter = 0
    sim_values = simulated_results[x + data_type]*simulated_unit
    obs_values = observed_results[x + data_type]*observed_unit
    for x in range(0,len(obs_values)):
      if counter == end_of_month[counter_m]:
        monthly_values_sim[total_counter] = sim_values[x]
        monthly_values_obs[total_counter] = obs_values[x]
        if counter_m !=1 and leap_year_counter != 3:
          counter += 1	  
        counter_m += 1
        total_counter += 1
        if counter_m == 12:
          counter_m = 0
          leap_year_counter += 1
          if leap_year_counter == 4:
            leap_year_counter = 0
      else:
        counter += 1
      if counter == 365:
        counter = 0
	  
    ax0 = plt.subplot(gs[plot_counter, 0])
    obs_values.plot(ax=ax0, color='k', use_index=True, alpha = 0.7, linewidth = 3)
    sim_values.plot(ax=ax0, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)
    ax0.set_title('San Luis Reservoir, ' + y + ' Portion')
    ax0.set_xlim([datetime.date(1996,10,1), datetime.date(2016,9,30)])
    ax0.set_xlabel('')
    ax0.set_xticklabels('')
    for item in [ax0.xaxis.label, ax0.yaxis.label, ax0.title]:
      item.set_fontsize(14)  
    for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
      item.set_fontsize(14)  

  
    ax22 = plt.subplot(gs[plot_counter,1])
    r = np.corrcoef(monthly_values_obs,monthly_values_sim)[0,1]     
    ax22.scatter(monthly_values_obs, monthly_values_sim, s=75, c='steelblue', edgecolor='none', alpha=0.8)
    ax22.plot([0.0, max([max(monthly_values_obs), max(monthly_values_sim)])], [0.0, max([max(monthly_values_obs), max(monthly_values_sim)])], linestyle = 'dashed', color = 'black', linewidth = 3)    
    ax22.set_ylabel('Simulated (mAF)')
    ax22.set_xlabel('Observed (mAF)')
    ax22.set_title('Monthly San Luis Storage ' + y + ' vs. Simulated')
    ax22.annotate('$R^2 = %.2f$' % r**2, xy=(0.8,0), color='0.1')
    ax22.set_xlim([0.0, ax22.get_xlim()[1]])
    ax22.set_ylim([0.0, ax22.get_ylim()[1]])
	
    plot_counter += 1
  
  
  fig.add_subplot(111, frameon=False)
  plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
  plt.grid(False)
  plt.ylabel("Storage (mAF)", fontsize = 14, position = (-0.1, 0.5))
  
  ax0.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))  
  plt.tight_layout()
  plt.show()

  
  
  
  
###################GRAVEYARD############################################ 
  
def find_district_revenues(district_results, district_key, acreage, price, assessment, take_fee, give_fee, type):
  if type == 'delivery':
    total_deliveries = district_results[district_key + '_delivery']
    bank_withdrawals = np.zeros(len(total_deliveries))
    bank_deliveries = np.zeros(len(total_deliveries))
  elif type == 'recovery':
    total_deliveries = district_results[district_key + '_banked_accepted']
    bank_withdrawals = np.zeros(len(total_deliveries))
    bank_deliveries = np.zeros(len(total_deliveries))
  elif type == 'banking':
    total_deliveries = district_results[district_key + '_banked_accepted']
    bank_withdrawals = district_results[district_key + '_leiu_delivered']
    bank_deliveries = district_results[district_key + '_leiu_accepted']
	
  total_acreage = 0.0
  total_revenue = np.zeros(len(total_deliveries))
  for a in range(0, len(acreage)):
    total_acreage += acreage[a]	
  for y in range(0, len(total_deliveries)):
    total_revenue[y] = (total_deliveries[y]*price + total_acreage*assessment + max(bank_deliveries[y] - total_deliveries[y], 0.0)*take_fee + max(bank_withdrawals[y] - bank_deliveries[y], 0.0)*give_fee)/1000.0


  average_revenue = np.mean(total_revenue)
  
  return total_revenue, average_revenue
  
def find_banking_revenues(deposits, withdrawals, take_fee, give_fee):
  total_revenue = {}
  total_revenue['deposit'] = {}
  total_revenue['withdrawal'] = {}
  for y in deposits:
    total_revenue['deposit'][y] = np.zeros(len(deposits[y]))
    for xx in range(0, len(deposits[y])):
      total_revenue['deposit'][y][xx] = deposits[y][xx]*take_fee/1000.0
  for y in withdrawals:
    total_revenue['withdrawal'][y] = np.zeros(len(withdrawals[y]))
    for xx in range(0, len(withdrawals[y])):
      total_revenue['withdrawal'][y][xx] = withdrawals[y][xx]*give_fee/1000.0

 	  
  average_revenue = {}
  average_revenue['deposit'] = {}
  average_revenue['withdrawal'] = {}
  for y in deposits:
    average_revenue['deposit'][y] = np.mean(total_revenue['deposit'][y])
  for y in withdrawals:
    average_revenue['withdrawal'][y] = np.mean(total_revenue['withdrawal'][y])
	
  return total_revenue, average_revenue
  

def show_district_revenues(timeseries_revenues, min_rev, max_rev, second_type):
  plt.style.use("seaborn-darkgrid")  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  kde = stats.gaussian_kde(timeseries_revenues['delivery'])
  kde2 = stats.gaussian_kde(timeseries_revenues[second_type])

  sorted_delivery = np.sort(timeseries_revenues['delivery'])
  five_percent = sorted_delivery[int(np.ceil(.05*len(timeseries_revenues['delivery'])))]
  one_percent = sorted_delivery[0]
  mean_value = np.mean(sorted_delivery)
  pos = np.linspace(five_percent, max_rev, 101)
  max_height = np.max([np.max(kde(pos)), np.max(kde2(pos))])
  ax1 = plt.fill_between(pos, kde(pos), alpha = 0.25, facecolor = 'blue')
  pos2 = np.linspace(one_percent, five_percent, 101)
  ax2 = plt.fill_between(pos2, kde(pos2), alpha = 0.5, facecolor = 'red')
  pos3 = np.linspace(min_rev, one_percent, 101)
  ax3 = plt.fill_between(pos3, kde(pos3), alpha = 0.75, facecolor = 'red')
  p = ax0.plot([mean_value, mean_value], [0.0, max_height], linestyle = 'dashed', color = 'black', linewidth = 3)
  ax4 = plt.plot([mean_value, mean_value], [0.0, max_height], linestyle = 'dashed', color = 'black', linewidth = 3)
    	
  plt.xlabel('Annual Water Sales ($MM)', fontsize = 20)
  plt.ylabel('Probability', fontsize = 20)
  plt.xlim([min_rev, max_rev])
  plt.ylim([0.0, max_height])
  plt.legend((ax1, ax2, ax3,p[0]), ('Annual Water Sales ($80/AF)', '5% Risk', '1% Risk', 'Average Revenue'),bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)

  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(16)  
  plt.yticks([])
  plt.show()
  
  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)
  
  plt.style.use("seaborn-darkgrid")
  sorted_recovery = np.sort(timeseries_revenues[second_type])
  five_percent_new = sorted_recovery[int(np.ceil(.05*len(timeseries_revenues[second_type])))]
  one_percent_new = sorted_recovery[0]
  mean_value_new = np.mean(sorted_recovery)
  pos = np.linspace(five_percent, max_rev, 101)
  ax1 = plt.fill_between(pos, kde(pos), alpha = 0.25, facecolor = 'blue')
  pos2 = np.linspace(one_percent, five_percent, 101)
  ax22 = plt.fill_between(pos2, kde(pos2), alpha = 0.5, facecolor = 'red')
  pos3 = np.linspace(min_rev, one_percent, 101)
  ax33 = plt.fill_between(pos3, kde(pos3), alpha = 0.75, facecolor = 'red')
  p = ax0.plot([mean_value, mean_value], [0.0, max_height], linestyle = 'dashed', color = 'blue', linewidth = 3)
  ax4 = plt.plot([mean_value, mean_value], [0.0, max_height], linestyle = 'dashed', color = 'blue', linewidth = 3)
  
  
  pos1 = np.linspace(five_percent_new, max_rev, 101)
  ax11 = plt.fill_between(pos1, kde2(pos1), alpha = 0.25, facecolor = 'green')
  pos2 = np.linspace(one_percent_new, five_percent_new, 101)
  ax2 = plt.fill_between(pos2, kde2(pos2), alpha = 0.5, facecolor = 'red')
  pos3 = np.linspace(min_rev, one_percent_new, 101)
  ax3 = plt.fill_between(pos3, kde2(pos3), alpha = 0.75, facecolor = 'red')
  p = ax0.plot([mean_value_new, mean_value_new], [0.0, max_height], linestyle = 'dashed', color = 'green', linewidth = 3)
  pp = ax0.plot([mean_value_new, mean_value_new], [0.0, max_height], linestyle = 'dashed', color = 'black', linewidth = 3)
  ax4 = plt.plot([mean_value_new, mean_value_new], [0.0, max_height], linestyle = 'dashed', color = 'green', linewidth = 3)
  plt.xlabel('Annual Revenues ($MM)')
  plt.ylabel('Probability')
  plt.xlim([min_rev, max_rev])
  plt.ylim([0.0, max_height])
  plt.legend((ax1, ax11, ax2, ax3, pp[0]), ('Annual "Table A" Revenues', 'Annual Revenues w/Banking Ops', '5% Risk', '1% Risk', 'Average Revenue'), loc = 'upper right', fontsize = 14)

  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(16)  
  plt.yticks([])
  plt.show()
  
def find_pricing_mitigation(district_deliveries, acreage, average_revenue, max_volumetric, max_total, price, assessment):
  total_acreage = 0.0
  total_revenue = np.zeros(len(district_deliveries))
  for a in range(0, len(acreage)):
    total_acreage += acreage[a]	
  for y in range(0, len(district_deliveries)):
    average_per_af = assessment*total_acreage/district_deliveries[y]
    pricing_for_average = (average_revenue*1000.0 - total_acreage*assessment)/district_deliveries[y]
    new_price = max(min(pricing_for_average, max_volumetric, max_total - average_per_af), price)
    total_revenue[y] = (district_deliveries[y]*new_price + total_acreage*assessment)/1000.0

  average_revenue = np.mean(total_revenue)
  
  return total_revenue, average_revenue

	    