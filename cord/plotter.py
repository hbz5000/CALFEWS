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

def compare(res,obs,freq,freq2, data_name):
  # input two series and a frequency
  init_plotting()
  
  res1 = res.resample(freq).mean()*7*1.98/1000.0
  obs1 = obs.resample(freq).mean()*7*1.98/1000.0

  sns.set()
  fig = plt.figure(figsize=(16, 4)) 
  gs = gridspec.GridSpec(2, 2, width_ratios=[3, 1]) 

  ax0 = plt.subplot(gs[0, 0])
  obs1.plot(ax=ax0, color='k', use_index=True, alpha = 0.7, linewidth = 3)
  res1.plot(ax=ax0, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)
  #ax0.set_xlim([datetime.date(2004,10,1), datetime.date(2006,9,30)])
  #ax0.set_title('%s, %s' % (res.name, obs.name), family='OfficinaSanITCMedium', loc='left')
  ax0.set_title('Weekly '+ data_name + ' WY 2005-2006')
  ax0.legend(['Observed', 'Simulated'], ncol=1)
  ax0.set_ylabel('Pumping (tAF)')
  ax0.set_xlabel('')
  ax11 = plt.subplot(gs[1, 0])
  obs1.plot(ax=ax11, color='k', use_index=True, alpha = 0.7, linewidth = 3)
  res1.plot(ax=ax11, color='indianred', use_index=True, alpha = 0.7, linewidth = 3)
  #ax11.set_xlim([datetime.date(2013,10,1), datetime.date(2015,9,30)])
  ax11.set_title('Weekly '+ data_name + ' WY 2014-2015')
  #ax0.set_title('%s, %s' % (res.name, obs.name), family='OfficinaSanITCMedium', loc='left')
  ax11.set_ylabel('Pumping (tAF)')
  ax11.set_xlabel('')
  
  res2 = res.resample(freq2).mean()*365*1.98/1000
  obs2 = obs.resample(freq2).mean()*365*1.98/1000
  
  ax22 = plt.subplot(gs[:,1])
  r = np.corrcoef(obs2.values,res2.values)[0,1]  
  ax22.scatter(obs2.values, res2.values, s=75, c='steelblue', edgecolor='none', alpha=0.8)
  ax22.plot([0.0, max([max(obs2.values), max(res2.values)])], [0.0, max([max(obs2.values), max(res2.values)])], linestyle = 'dashed', color = 'black', linewidth = 3)    
  ax22.set_ylabel('Simulated (tAF/yr)')
  ax22.set_xlabel('Observed (tAF/yr)')
  ax22.set_title('Annual '+ data_name + ' vs. Simulated')
  ax22.annotate('$R^2 = %f$' % r**2, xy=(0,0), color='0.3')
  ax22.set_xlim([0.0, ax22.get_xlim()[1]])
  ax22.set_ylim([0.0, ax22.get_ylim()[1]])
  for item in [ax0.xaxis.label, ax0.yaxis.label, ax11.xaxis.label, ax11.yaxis.label,ax22.xaxis.label, ax22.yaxis.label, ax0.title, ax11.title, ax22.title]:
    item.set_fontsize(14)  
  for item in (ax0.get_xticklabels() + ax11.get_xticklabels() + ax22.get_xticklabels() + ax0.get_yticklabels() + ax11.get_yticklabels() + ax22.get_yticklabels()):
    item.set_fontsize(14)  
  plt.tight_layout()
  plt.show()
  
def compare_contracts():
  contract_values = pd.read_csv('cord/data/swp_contract_results.csv', index_col = 0)
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
    print(y, end = " ")
    print(period_revenue[y], end = " ")
    print(total_average, end = " ")
    print(budget_gap[y-1])
	
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
  for x in range(0, len(revenues_swp)):
    print(x, end = " ")
    print(revenues_cvp[x], end = " ")
    print(averages_cvp)
	  
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

def show_pumping_pdf(annual_pumping, project, max_pumping):
  sorted_pumping = np.sort(annual_pumping)
  five_percent = sorted_pumping[int(np.ceil(.05*len(annual_pumping)))]
  one_percent = sorted_pumping[0]
  #sns.set()
  #ax0 = sns.kdeplot(annual_pumping, shade = True).set(xlim=(0))
  #line = ax0.get_lines()[-1]
  #x, y = line.get_data()
  plt.style.use("seaborn-darkgrid")
  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  kde = stats.gaussian_kde(annual_pumping)
  pos = np.linspace(0.0, max_pumping, 101)
  ax1 = plt.fill_between(pos, kde(pos), alpha = 0.25, facecolor = 'blue')
  plt.xlabel('Annual ' + project +' (tAF)')
  plt.ylabel('Probability')
  plt.xlim([0.0, max_pumping])
  plt.yticks([])
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels()):
    item.set_fontsize(16)  

  plt.show()
  
  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  plt.style.use("seaborn-darkgrid")
  kde = stats.gaussian_kde(annual_pumping)
  pos = np.linspace(five_percent, max_pumping, 101)
  ax1 = plt.fill_between(pos, kde(pos), alpha = 0.25, facecolor = 'blue')
  pos2 = np.linspace(0.0, five_percent, 101)
  ax2 = plt.fill_between(pos2, kde(pos2), alpha = 0.5, facecolor = 'red')
  plt.xlabel('Annual ' + project +' (tAF)')
  plt.ylabel('Probability')
  plt.legend('Annual Pumping', '5% Risk')
  plt.xlim([0.0, max_pumping])
  plt.yticks([])
  plt.legend((ax1, ax2), ('Annual Pumping', '5% Risk'),bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels()):
    item.set_fontsize(16)  
  plt.show()

  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  plt.style.use("seaborn-darkgrid")
  kde = stats.gaussian_kde(annual_pumping)
  pos = np.linspace(five_percent, max_pumping, 101)
  ax1 = plt.fill_between(pos, kde(pos), alpha = 0.25, facecolor = 'blue')
  pos2 = np.linspace(one_percent, five_percent, 101)
  ax2 = plt.fill_between(pos2, kde(pos2), alpha = 0.5, facecolor = 'red')
  pos3 = np.linspace(0.0, one_percent, 101)
  ax3 = plt.fill_between(pos3, kde(pos3), alpha = 0.75, facecolor = 'red')
  plt.xlabel('Annual ' + project +' (tAF)')
  plt.ylabel('Probability')
  plt.legend('Annual Pumping', '5% Risk')
  plt.xlim([0.0, max_pumping])
  plt.legend((ax1, ax2, ax3), ('Annual Pumping', '5% Risk', '1% Risk'),bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)
  plt.yticks([])
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels()):
    item.set_fontsize(16)  
  plt.show()
  
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
    print(y, end = " ")
    print(total_deliveries[y], end = " ")
    print(total_revenue[y])


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
      print(y, end = " ")
      print(xx, end = " ")
      print(deposits[y][xx], end = " ")
      print(total_revenue['deposit'][y][xx])
  for y in withdrawals:
    total_revenue['withdrawal'][y] = np.zeros(len(withdrawals[y]))
    for xx in range(0, len(withdrawals[y])):
      total_revenue['withdrawal'][y][xx] = withdrawals[y][xx]*give_fee/1000.0
      print(y, end = " ")
      print(xx, end = " ")
      print(withdrawals[y][xx], end = " ")
      print(total_revenue['withdrawal'][y][xx])

 	  
  average_revenue = {}
  average_revenue['deposit'] = {}
  average_revenue['withdrawal'] = {}
  for y in deposits:
    average_revenue['deposit'][y] = np.mean(total_revenue['deposit'][y])
  for y in withdrawals:
    average_revenue['withdrawal'][y] = np.mean(total_revenue['withdrawal'][y])
	
  return total_revenue, average_revenue

def show_district_revenues(timeseries_revenues, min_rev, max_rev):
  plt.style.use("seaborn-darkgrid")  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  kde = stats.gaussian_kde(timeseries_revenues['delivery'])
  kde2 = stats.gaussian_kde(timeseries_revenues['recovery'])

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
  kde2 = stats.gaussian_kde(timeseries_revenues['recovery'])
  sorted_recovery = np.sort(timeseries_revenues['recovery'])
  five_percent = sorted_recovery[int(np.ceil(.05*len(timeseries_revenues['recovery'])))]
  one_percent = sorted_recovery[0]
  mean_value = np.mean(sorted_recovery)
  pos = np.linspace(min_rev, max_rev, 101)
  ax1 = plt.fill_between(pos, kde(pos), alpha = 0.25, facecolor = 'blue')
  pos1 = np.linspace(five_percent, max_rev, 101)
  ax11 = plt.fill_between(pos1, kde2(pos1), alpha = 0.25, facecolor = 'green')
  pos2 = np.linspace(one_percent, five_percent, 101)
  ax2 = plt.fill_between(pos2, kde2(pos2), alpha = 0.5, facecolor = 'red')
  pos3 = np.linspace(min_rev, one_percent, 101)
  ax3 = plt.fill_between(pos3, kde2(pos3), alpha = 0.75, facecolor = 'red')
  p = ax0.plot([mean_value, mean_value], [0.0, max_height], linestyle = 'dashed', color = 'black', linewidth = 3)
  ax4 = plt.plot([mean_value, mean_value], [0.0, max_height], linestyle = 'dashed', color = 'black', linewidth = 3)
    	
  plt.xlabel('Annual Water Sales ($MM)')
  plt.ylabel('Probability')
  plt.xlim([min_rev, max_rev])
  plt.ylim([0.0, max_height])
  plt.legend((ax1, ax11, ax2, ax3, p[0]), ('Annual Water Sales, ($80/AF)', 'Annual Water Sales, with Take Fees', '5% Risk', '1% Risk', 'Average Revenue'),bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)

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

def find_insurance_mitigation(annual_pumping, district_revenues, target_revenue, evaluation_length, insurance_cost, insurance_strike, insurance_payout, contingency_fund_start, min_loss):
  total_revenue = np.zeros(len(district_revenues)*evaluation_length)
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
        total_revenue[(yy-y)+y*evaluation_length] = district_revenues[yy-y_adjust] - annual_contribution - insurance_cost
        contingency_fund += insurance_payment
      else:
        contingency_fund += (district_revenues[yy-y_adjust] - target_revenue + insurance_payment)
        total_revenue[(yy-y)+y*evaluation_length] = target_revenue - annual_contribution - insurance_cost
      if contingency_fund < 0.0:
        total_revenue[(yy-y)+y*evaluation_length] += contingency_fund
        contingency_fund = 0.0

  average_revenue = np.mean(total_revenue)
  
  return total_revenue, average_revenue
  
def show_insurance_payouts(annual_pumping, revenues_delivery, revenues_banking, strike, strike2, contract_type):
  payout_years = annual_pumping < strike
  payout_pumping = annual_pumping[payout_years]
  payout_revenues = revenues_delivery[payout_years]
  if len(payout_pumping > 1):
    insurance_payout = np.polyfit(payout_pumping, payout_revenues, 1)	
  else:
    insurance_payout = np.zeros(2)

  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  ax1 = plt.scatter(annual_pumping, revenues_delivery, s=75, c='black', edgecolor='none', alpha=0.7)
  plt.xlim((np.min(annual_pumping)-25.0, np.max(annual_pumping)+25.0))
  plt.ylim((0,np.ceil(revenues_banking.max())))  
  plt.xlabel('Total ' + contract_type +' (tAF)')
  plt.ylabel('Annual District Sales ($MM)')
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()

  
  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  ax1 = plt.scatter(annual_pumping, revenues_delivery, s=75, c='black', edgecolor='none', alpha=0.7)
  ax2 = plt.scatter(annual_pumping, revenues_banking, s=75, c='red', edgecolor='none', alpha=0.7)
  plt.xlim((np.min(annual_pumping)-25.0, np.max(annual_pumping)+25.0))
  plt.ylim((0,np.ceil(revenues_banking.max())))  
  plt.xlabel('Total ' + contract_type +' (tAF)')
  plt.ylabel('Annual District Sales ($MM)')
  plt.legend((ax1, ax2), ('Contract Deliveries', 'Deliveries + Recharge Take Fees'),bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()
  
	
  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  ax1 = plt.scatter(annual_pumping, revenues_delivery, s=75, c='black', edgecolor='none', alpha=0.7)
  strike_years = annual_pumping < strike
  expected_revenue = np.max(revenues_delivery[strike_years])
  min_revenue = np.min(revenues_delivery)
  insurance_range = np.arange(int(strike))
  ax2 = plt.plot(insurance_range, min_revenue*np.ones(len(insurance_range)), color = 'black', linewidth = 3)
  ax3 = plt.plot(insurance_range, expected_revenue*np.ones(len(insurance_range)), color = 'black', linewidth = 3)
  ax4 = plt.plot(np.zeros(2), [min_revenue, expected_revenue], color = 'black', linewidth = 3)
  ax5 = plt.plot(strike*np.ones(2), [min_revenue, expected_revenue], color = 'black', linewidth = 3)
  ax6 = plt.fill_between(insurance_range,min_revenue*np.ones(len(insurance_range)),expected_revenue*np.ones(len(insurance_range)), color = 'black', alpha = 0.25)
  
  non_risk = annual_pumping > strike
  mean_non_risk = np.mean(revenues_delivery[non_risk])
  p = ax0.plot([0.0, np.max(annual_pumping)],[mean_non_risk, mean_non_risk], linestyle = 'dashed', color = 'black', linewidth = 3)
  ax7 = plt.plot([0.0, np.max(annual_pumping)],[mean_non_risk, mean_non_risk], linestyle = 'dashed', color = 'black', linewidth = 3)

  plt.xlim((np.min(annual_pumping)-25.0, np.max(annual_pumping)+25.0))
  plt.ylim((0,np.ceil(revenues_banking.max())))  
  plt.xlabel('Total ' + contract_type +' (tAF)')
  plt.ylabel('Annual District Sales ($MM)')
  plt.legend((ax1, ax6, p[0]), ('Contract Deliveries', 'At-Risk Years', 'Mean Revenue, Non-Risk Years'),bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()
  
  payout_revenues = revenues_banking[payout_years]
  if len(payout_pumping > 1):
    insurance_payout = np.polyfit(payout_pumping, payout_revenues, 1)	
  else:
    insurance_payout = np.zeros(2)
  
  fig1 = plt.figure()
  ax0 = fig1.add_subplot(111)
  ax1 = plt.scatter(annual_pumping, revenues_delivery, s=75, c='black', edgecolor='none', alpha=0.7)  
  ax2 = plt.scatter(annual_pumping, revenues_banking, s=75, c='red', edgecolor='none', alpha=0.7)
  strike_years = annual_pumping < strike2
  min_revenue = np.min(revenues_banking)
  expected_revenue = np.max(revenues_banking[strike_years])
  insurance_range = np.arange(int(strike2))
  ax3 = plt.plot(insurance_range, min_revenue*np.ones(len(insurance_range)), color = 'red', linewidth = 3)
  ax4 = plt.plot(insurance_range, expected_revenue*np.ones(len(insurance_range)), color = 'red', linewidth = 3)
  ax5 = plt.plot(np.zeros(2), [min_revenue, expected_revenue], color = 'red', linewidth = 3)
  ax6 = plt.plot(strike2*np.ones(2), [min_revenue, expected_revenue], color = 'red', linewidth = 3)
  ax7 = plt.fill_between(insurance_range,min_revenue*np.ones(len(insurance_range)),expected_revenue*np.ones(len(insurance_range)), color = 'red', alpha = 0.25)
  
  non_risk = annual_pumping > strike2
  mean_non_risk = np.mean(revenues_banking[non_risk])
  p = ax0.plot([0.0, np.max(annual_pumping)],[mean_non_risk, mean_non_risk], linestyle = 'dashed', color = 'red', linewidth = 3)
  ax8 = plt.plot([0.0, np.max(annual_pumping)],[mean_non_risk, mean_non_risk], linestyle = 'dashed', color = 'red', linewidth = 3)

  plt.xlim((np.min(annual_pumping)-25.0, np.max(annual_pumping)+25.0))
  plt.ylim((0,np.ceil(revenues_banking.max())))  
  plt.xlabel('Total ' + contract_type +' (tAF)')
  plt.ylabel('Annual District Sales ($MM)')
  plt.legend((ax1, ax2, ax7, p[0]), ('Contract Deliveries', 'Deliveries + Recharge Take Fees', 'At-Risk Years', 'Mean Revenue, Non-Risk Years'),bbox_to_anchor = (0.005, .995), loc = 'upper left', fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()
  
  
  #fig1 = plt.figure()
  #ax0 = fig1.add_subplot(111)  
  #ax2 = plt.scatter(annual_pumping, revenues_banking, s=75, c='red', edgecolor='none', alpha=0.7)
  #insurance_range = np.arange(int(strike))
  #expected_revenue = insurance_payout[0]*np.arange(int(strike)) + insurance_payout[1]*np.ones(int(strike))
  #insurance_range_tot = np.arange(4000)
  #target_revenue_tot = (insurance_payout[0]*2000.0 + insurance_payout[1])*np.ones(int(4000))
  
  #target_revenue = (insurance_payout[0]*strike + insurance_payout[1])*np.ones(int(strike))
  #ax3 = plt.plot(insurance_range, expected_revenue, linestyle = 'dashed', color = 'black', linewidth = 3)
  #ax4 = plt.plot(insurance_range_tot, target_revenue_tot, linestyle = 'dashed', color = 'black', linewidth = 3)
  #ax5 = plt.fill_between(np.arange(int(strike)),target_revenue,expected_revenue, color = 'blue', alpha = 0.25)
  #plt.xlim((0, 4000))
  #plt.ylim((0,45))  
  #plt.xlabel('Total SWP Pumping (tAF)')
  #plt.ylabel('Annual Water Sales ($MM)')
  #plt.legend((ax2, ax5), ('San Luis + Recovery Deliveries', 'Insurance Coverage'),bbox_to_anchor = (0.005, .995), loc = 'upper left')
  #for item in [ax0.xaxis.label, ax0.yaxis.label]:
    #item.set_fontsize(20)  
  #for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    #item.set_fontsize(14)  

  #plt.show()
 
def show_value_at_risk(district_revenue, average_revenue, percentile):
  numYears = len(district_revenue)
  risk = np.zeros(numYears)
  for y in range(0, len(district_revenue)):
    risk[y] = max(average_revenue - district_revenue[y], 0.0)
  contingent_risk = np.sort(risk)
  percentile_index = int(np.ceil(percentile*numYears))
  value_at_risk = contingent_risk[percentile_index]
  
  return value_at_risk
  
def find_index(values, averages, max_value):
  print(values)
  sorted_values = np.sort(values)
  sorted_index = np.argsort(values)
  for x in range(0,len(values)):
    check_value = sorted_values[x]
    print(x, end = " ")
    print(check_value)
    if check_value > max_value:
      break
  max_rev = 0.0
  max_rev_spot = x
  sorted_averages = averages[sorted_index]
  if x > 0:
    end_loc = x-1
  else:
    end_loc = x

  for y in range(0,end_loc):
    print(y, end = " ")
    print(sorted_averages[y], end = " ")
    print(max_rev)
    if sorted_averages[y] > max_rev:
      max_rev_spot = y
      max_rev = sorted_averages[y]
	  
  return sorted_index[max_rev_spot]

	
def find_revenue_buckets(revenues, contingency_index, insurance_index, start_type):
  bar_shapes = {}
  percentile_groups = ['1_loss', '5_loss', '20_loss', '20_gain', '5_gain', '1_gain']
  percentile_values = [.01, .05, .2, .8 , .95, .99]
  for percentile in percentile_groups:
    bar_shapes[percentile] = np.zeros(3)
	
  for i,v in enumerate([start_type, 'CF', 'insurance']):
    if v == 'CF':
      sorted_values = np.sort(revenues[v][start_type][contingency_index])
    elif v == 'insurance':
      sorted_values = np.sort(revenues[v][start_type][insurance_index])
    else:
      sorted_values = np.sort(revenues[start_type])
    numYears = len(sorted_values)
    for ii,vv in enumerate(percentile_groups):
      percentile_index = int(np.ceil(percentile_values[ii]*numYears))
      bar_shapes[vv][i] = sorted_values[percentile_index]
	  
  return bar_shapes
    
def show_revenue_variability(bar_shapes, averages, contingency_index, insurance_index, initial_type, annual_cost, max_revenue):	
  
  cost_shapes_cont = np.zeros(3)
  cost_shapes_cont[1] = annual_cost['CF']['contribution'][contingency_index]
  cost_shapes_cont[2] = annual_cost['insurance']['contribution'][insurance_index]
  cost_shapes_prem = np.zeros(3)
  cost_shapes_prem[1] = annual_cost['CF']['premium'][contingency_index]
  cost_shapes_prem[2] = annual_cost['insurance']['premium'][insurance_index]
  bar_locations = np.arange(3)
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  average_locations = np.zeros(3)
  for i,v in enumerate([initial_type, 'CF', 'insurance']):
    if v == 'CF':
      average_locations[i] = averages[v][initial_type][contingency_index]
    elif v == 'insurance':
      average_locations[i] = averages[v][initial_type][insurance_index]
    else:
      average_locations[i] = averages[initial_type]
  p2 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], color = 'red', alpha = 0.75)
  p22 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p3 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], color = 'red', alpha = 0.5)
  p33 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p4 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], color = 'red', alpha = 0.25)
  p44 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p5 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, color = 'blue', alpha = 0.75)
  p55 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, edgecolor = ['blue']*len(bar_locations), linewidth = 1, color = 'None')
  p6 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'],  color = 'blue', alpha = 0.5)
  p66 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p7 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'],  color = 'blue', alpha = 0.25)
  p77 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p8 = plt.bar(bar_locations, cost_shapes_cont, 0.5,  bottom = np.zeros(3), color = 'green', alpha = 0.75)
  p88 = plt.bar(bar_locations, cost_shapes_cont, 0.5,  bottom = np.zeros(3), edgecolor = ['green']*len(bar_locations), linewidth = 1,  color = 'None')
  p9 = plt.bar(bar_locations, cost_shapes_prem, 0.5,  bottom = cost_shapes_cont, color = 'green', alpha = 0.25)
  p99 = plt.bar(bar_locations, cost_shapes_prem, 0.5,  bottom = cost_shapes_cont, edgecolor = ['green']*len(bar_locations), linewidth = 1,  color = 'None')

  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")

  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  plt.legend((p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p8[0], p9[0], p1[0]), ('20% Chance of Lower Revenue', '5% Chance', '1% Chance', '20% Chance of Greater Revenue', '5% Chance', '1% Chance', 'Annual Contingency Fund Contribution', 'Annual Insurance Premium', 'Expected Revenue'), ncol = 3, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  

  plt.show()

  
  
  
  
  bar_locations = np.arange(3)
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  average_locations = np.zeros(3)
  for i,v in enumerate([initial_type, 'CF', 'insurance']):
    if v == 'CF':
      average_locations[i] = averages[v][initial_type][contingency_index]
    elif v == 'insurance':
      average_locations[i] = averages[v][initial_type][insurance_index]
    else:
      average_locations[i] = averages[initial_type]
  p2 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], color = 'red', alpha = 0.75)
  p22 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p3 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], color = 'red', alpha = 0.5)
  p33 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p4 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], color = 'red', alpha = 0.25)
  p44 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p5 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, color = 'blue', alpha = 0.75)
  p55 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, edgecolor = ['blue']*len(bar_locations), linewidth = 1, color = 'None')
  p6 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'],  color = 'blue', alpha = 0.5)
  p66 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p7 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'],  color = 'blue', alpha = 0.25)
  p77 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")

  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  plt.legend((p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p1[0]), ('20% Chance of Lower Revenue', '5% Chance', '1% Chance', '20% Chance of Greater Revenue', '5% Chance', '1% Chance','Expected Revenue'), ncol = 3, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  

  plt.show()
  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  average_locations[2] = 0.0
  bar_shapes['20_loss'][2] = 0.0
  bar_shapes['5_loss'][2] = 0.0
  bar_shapes['1_loss'][2] = 0.0  
  bar_shapes['20_gain'][2] = 0.0
  bar_shapes['5_gain'][2] = 0.0
  bar_shapes['1_gain'][2] = 0.0

  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  p2 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], color = 'red', alpha = 0.75)
  p22 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p3 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], color = 'red', alpha = 0.5)  
  p33 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p4 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], color = 'red', alpha = 0.25)  
  p44 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p5 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, color = 'blue', alpha = 0.75)
  p55 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, edgecolor = ['blue']*len(bar_locations), linewidth = 1, color = 'None')
  p6 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'],  color = 'blue', alpha = 0.5)
  p66 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p7 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'],  color = 'blue', alpha = 0.25)
  p77 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")

  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  plt.legend((p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p1[0]), ('20% Chance of Lower Revenue', '5% Chance', '1% Chance', '20% Chance of Greater Revenue', '5% Chance', '1% Chance','Expected Revenue'), ncol = 3, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  

  plt.show()
  

  fig = plt.figure()
  ax0 = fig.add_subplot(111)  	  
  average_locations[1] = 0.0
  average_locations[2] = 0.0  
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()
	  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  average_locations[1] = 0.0
  average_locations[2] = 0.0
  bar_shapes['20_loss'][1] = 0.0
  bar_shapes['20_loss'][2] = 0.0
  
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  p2 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], color = 'red', alpha = 0.75)
  p22 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  plt.legend((p2[0], p1[0]),('20% Chance of Lower Revenue', 'Expected Revenue'), ncol = 1, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()
	  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  average_locations[1] = 0.0
  average_locations[2] = 0.0
  bar_shapes['20_loss'][1] = 0.0
  bar_shapes['20_loss'][2] = 0.0
  bar_shapes['5_loss'][1] = 0.0
  bar_shapes['5_loss'][2] = 0.0
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  p2 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], color = 'red', alpha = 0.75)
  p22 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p3 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], color = 'red', alpha = 0.5)  
  p33 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  plt.legend((p2[0], p3[0], p1[0]),('20% Chance of Lower Revenue', '5% Chance', 'Expected Revenue'), ncol = 1, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()
	  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  average_locations[1] = 0.0
  average_locations[2] = 0.0
  bar_shapes['20_loss'][1] = 0.0
  bar_shapes['20_loss'][2] = 0.0
  bar_shapes['5_loss'][1] = 0.0
  bar_shapes['5_loss'][2] = 0.0
  bar_shapes['1_loss'][1] = 0.0
  bar_shapes['1_loss'][2] = 0.0
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  p2 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], color = 'red', alpha = 0.75)
  p22 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p3 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], color = 'red', alpha = 0.5)  
  p33 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p4 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], color = 'red', alpha = 0.25)  
  p44 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  plt.legend((p2[0], p3[0], p4[0], p1[0]),('20% Chance of Lower Revenue', '5% Chance', '1% Chance', 'Expected Revenue'), ncol = 2, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  
  plt.show()
	  
  fig = plt.figure()
  ax0 = fig.add_subplot(111)  
  average_locations[1] = 0.0
  average_locations[2] = 0.0
  bar_shapes['20_loss'][1] = 0.0
  bar_shapes['20_loss'][2] = 0.0
  bar_shapes['5_loss'][1] = 0.0
  bar_shapes['5_loss'][2] = 0.0
  bar_shapes['1_loss'][1] = 0.0
  bar_shapes['1_loss'][2] = 0.0  
  bar_shapes['20_gain'][1] = 0.0
  bar_shapes['20_gain'][2] = 0.0
  bar_shapes['5_gain'][1] = 0.0
  bar_shapes['5_gain'][2] = 0.0
  bar_shapes['1_gain'][1] = 0.0
  bar_shapes['1_gain'][2] = 0.0

  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")
  p2 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], color = 'red', alpha = 0.75)
  p22 = plt.bar(bar_locations, average_locations - bar_shapes['20_loss'], 0.5, bottom = bar_shapes['20_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p3 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], color = 'red', alpha = 0.5)  
  p33 = plt.bar(bar_locations, bar_shapes['20_loss'] - bar_shapes['5_loss'], 0.5, bottom = bar_shapes['5_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p4 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], color = 'red', alpha = 0.25)  
  p44 = plt.bar(bar_locations, bar_shapes['5_loss'] - bar_shapes['1_loss'], 0.5, bottom = bar_shapes['1_loss'], edgecolor = ['red']*len(bar_locations), linewidth = 1, color = 'None')
  p5 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, color = 'blue', alpha = 0.75)
  p55 = plt.bar(bar_locations, bar_shapes['20_gain'] - average_locations, 0.5, bottom = average_locations, edgecolor = ['blue']*len(bar_locations), linewidth = 1, color = 'None')
  p6 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'],  color = 'blue', alpha = 0.5)
  p66 = plt.bar(bar_locations, bar_shapes['5_gain'] - bar_shapes['20_gain'], 0.5, bottom = bar_shapes['20_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p7 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'],  color = 'blue', alpha = 0.25)
  p77 = plt.bar(bar_locations, bar_shapes['1_gain'] - bar_shapes['5_gain'], 0.5, bottom = bar_shapes['5_gain'], edgecolor = ['blue']*len(bar_locations), linewidth = 1,  color = 'None')
  p1 = plt.bar(bar_locations, average_locations, 0.5, edgecolor = ['black']*len(bar_locations), linewidth = 5, color = "None")

  plt.ylabel('Annual Revenue ($MM)')
  plt.ylim([0.0, max_revenue])
  plt.xticks(bar_locations,('No Mitigation', 'Contingency Fund', 'Contingency Fund\n with Index Insurance'))
  plt.legend((p2[0], p3[0], p4[0], p5[0], p6[0], p7[0], p1[0]), ('20% Chance of Lower Revenue', '5% Chance', '1% Chance', '20% Chance of Greater Revenue', '5% Chance', '1% Chance','Expected Revenue'), ncol = 3, bbox_to_anchor = (0.0, 1.005, 1.0, .4), loc = 3, borderaxespad = 0.0, fontsize = 14)
  for item in [ax0.xaxis.label, ax0.yaxis.label]:
    item.set_fontsize(20)  
  for item in (ax0.get_xticklabels() + ax0.get_yticklabels()):
    item.set_fontsize(14)  

  plt.show()
	    