import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import cm
import importlib
import calfews_src.postprocess.load_model_data as load_model_data

cmap = cm.get_cmap('viridis')
cols = [cmap(0.1),cmap(0.3),cmap(0.6),cmap(0.8)]
cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560

### load canal data for 2 scenarios
importlib.reload(load_model_data)
canal1, canal_aggregate_Wateryear1, canal_aggregate_Wateryear_Month1, ind_canal_waterway1, ind_canal_recipient1, ind_canal_flowtype1 = \
            load_model_data.load_canal_data('calfews_src/data/results/old_ewri2019/FKC_capacity_wy2017/canal_results_simulation.csv')

canal2, canal_aggregate_Wateryear2, canal_aggregate_Wateryear_Month2, ind_canal_waterway2, ind_canal_recipient2, ind_canal_flowtype2 = \
            load_model_data.load_canal_data('calfews_src/data/results/old_ewri2019/FKC_capacity_rehab_full/canal_results_simulation.csv')
folder_name = 'FKC_capacity_rehab_full'
os.makedirs('calfews_src/figs/compareScenarios/' + folder_name, exist_ok=True)


### organize data for alluvial plots in R




####### plots
### plot historical & modeled deliveries (based on turnouts) - FKC & MDC, contractors & non-contractors
flow_type = 'turnout'   # 'flow' or 'turnout'

fig = plt.figure(figsize=(18, 9))
ax = plt.subplot2grid((2,2), (0,0))
ind = (ind_canal_flowtype1 == flow_type) & ((ind_canal_waterway1 == 'FKC'))
ax.plot_date(canal_aggregate_Wateryear1.Date,
                       np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1), fmt='-', c=cols[0])
ax.plot_date(canal_aggregate_Wateryear2.Date,
                       np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1), fmt='--', c=cols[3])
ax.legend(['Scenario 1', 'Scenario 2'])
ax.set_ylabel(flow_type + ' (taf/wy)')
ax.set_xlabel('Date')
ax = plt.subplot2grid((2,2), (0,1))
ax.scatter(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1),
           np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1), c=cols[0])
ax.plot(ax.get_xlim(), ax.get_xlim(), ls="--", c=".7")
ax.annotate('FKC/MDC all', xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0])*0.94,
                          ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0])*0.95))
ax.annotate(round(np.corrcoef(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1),
                              np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1))[1][0], 2),
            xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0])*0.94 ,
                ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0])*0.9))
ax.set_xlabel('Scenario 1 ' + flow_type + ' (taf/wy)')
ax.set_ylabel('Scenario 2 ' + flow_type + ' (taf/wy)')
ax = plt.subplot2grid((2,2), (1,0))
ax.plot_date(canal_aggregate_Wateryear_Month1.Date,
                       np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1), fmt='-', c=cols[0])
ax.plot_date(canal_aggregate_Wateryear_Month2.Date,
                      np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1), fmt='--', c=cols[3])
ax.legend(['Scenario 1', 'Scenario 2'])
ax.set_xlabel('Date')
ax.set_ylabel(flow_type + ' (taf/month)')
ax = plt.subplot2grid((2,2), (1,1))
ax.scatter(np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1),
           np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1), c=cols[0])
ax.plot(ax.get_xlim(), ax.get_xlim(), ls="--", c=".7")
ax.annotate('FKC/MDC all', xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0])*0.94,
                          ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0])*0.95))
ax.annotate(round(np.corrcoef(np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1),
                              np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1))[1][0], 2),
            xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0])*0.94 ,
                ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0])*0.9))
ax.set_xlabel('Scenario 1 ' + flow_type + ' (taf/month)')
ax.set_ylabel('Scenario 2 ' + flow_type + ' (taf/month)')
plt.savefig('calfews_src/figs/compareScenarios/%s/compare_%s_all.png' % (folder_name,flow_type), dpi=150)


### plot annual deliveries for different districts - time series
flow_type = 'turnout'   # 'flow' or 'turnout'
aggregation = 'wy' # 'month' or 'wy'
plot_type = 'scatter'  # 'timeseries' or 'scatter'

d_list = [[['MIL','MAD','CWC'],
           ['COF','FRS','KGR']],
          [['OFK','TUL','OKW'],
           ['KWR','EXE','LDS']],
          [['LND','PRT','LWT'],
           ['OTL','TLR','TPD']],
          [['SAU','TBA','OXV'],
           ['DLE','KRT','SSJ']],
          [['SFW','NKN','NKB'],
           ['XVC','KNR','AEC']]]
name_list = ['1','2','3','4','5']
for k in range(len(d_list)):
  d = d_list[k]
  name = name_list[k]
  fig = plt.figure(figsize=(18,9))
  gs1 = gridspec.GridSpec(2,3)
  # gs1.update(wspace=0.3,hspace=0.3)
  for i in range(2):
    for j in range(3):
      ax = plt.subplot(gs1[i,j])
      ax.tick_params(axis='y', which='both', labelleft=True, labelright=False)
      ax.tick_params(axis='x', which='both', labelbottom=True, labeltop=False)
      ind = (ind_canal_recipient1 == d[i][j]) & (ind_canal_flowtype1 == flow_type) & ((ind_canal_waterway1 == 'FKC') | (ind_canal_waterway1 == 'MDC'))
      if (plot_type == 'timeseries'):
        if (aggregation == 'wy'):
          ax.plot_date(canal_aggregate_Wateryear1.Date,
                       np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1), fmt='-', c=cols[0])
          ax.plot_date(canal_aggregate_Wateryear2.Date,
                      np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1), fmt='--', c=cols[3])
          ax.legend(['Scenario 1', 'Scenario 2'])
          ax.set_ylabel(flow_type + ' (taf/wy)')
          ax.set_xlabel('Date')
        elif (aggregation == 'month'):
          ax.plot_date(canal_aggregate_Wateryear_Month1.Date,
                       np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1), fmt='-', c=cols[0])
          ax.plot_date(canal_aggregate_Wateryear_Month2.Date,
                       np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1), fmt='--', c=cols[3])
          ax.legend(['Scenario 1', 'Scenario 2'])
          ax.set_xlabel('Date')
          ax.set_ylabel(flow_type + ' (taf/month)')
      elif (plot_type == 'scatter'):
        if (aggregation == 'wy'):
          ax.scatter(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1),
                     np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1), c=cols[0])
          ax.plot(ax.get_xlim(), ax.get_xlim(), ls="--", c=".7")
          ax.annotate(d[i][j], xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.94,
                                         ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.95))
          ax.annotate(round(np.corrcoef(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1),
                                        np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1))[1][0], 2),
                      xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.94,
                          ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.9))
          ax.set_xlabel('Scenario 1 ' + flow_type + ' (taf/wy)')
          ax.set_ylabel('Scenario 2 ' + flow_type + ' (taf/wy)')
        elif (aggregation == 'month'):
          ax.scatter(np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1),
                     np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1), c=cols[0])
          ax.plot(ax.get_xlim(), ax.get_xlim(), ls="--", c=".7")
          ax.annotate(d[i][j], xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.94,
                                         ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.95))
          ax.annotate(round(np.corrcoef(np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1),
                                        np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1))[1][0], 2),
                      xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.94,
                          ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.9))
          ax.set_xlabel('Scenario 1 ' + flow_type + ' (taf/month)')
          ax.set_ylabel('Scenario 2 ' + flow_type + ' (taf/month)')
  plt.savefig('calfews_src/figs/compareScenarios/%s/compareFriant_%s_%s_%s_%s.png' % (folder_name, flow_type, plot_type, aggregation, name), dpi=150)



### plot annual deliveries for different districts - time series
flow_type = 'turnout'   # 'flow' or 'turnout'
aggregation = 'wy' # 'month' or 'wy'
plot_type = 'scatter'  # 'timeseries' or 'scatter'

d_list = [[['CAA','BVA','KWB'],
           ['IVR', 'PIO', 'B2800']],
          [['BRM', 'GSL', 'FKC'],
           ['BRM', 'GSL', 'FKC']]]
          # [['LND','PRT','LWT'],
          #  ['OTL','TLR','TPD']],
          # [['SAU','TBA','OXV'],
          #  ['DLE','KRT','SSJ']],
          # [['SFW','NKN','NKB'],
          #  ['XVC','KNR','AEC']]]
name_list = ['1','2']
for k in range(len(d_list)):
  d = d_list[k]
  name = name_list[k]
  fig = plt.figure(figsize=(18,9))
  gs1 = gridspec.GridSpec(2,3)
  # gs1.update(wspace=0.3,hspace=0.3)
  for i in range(2):
    for j in range(3):
      ax = plt.subplot(gs1[i,j])
      ax.tick_params(axis='y', which='both', labelleft=True, labelright=False)
      ax.tick_params(axis='x', which='both', labelbottom=True, labeltop=False)
      ind = (ind_canal_recipient1 == d[i][j]) & (ind_canal_flowtype1 == flow_type) & (ind_canal_waterway1 == 'KNR')
      if (plot_type == 'timeseries'):
        if (aggregation == 'wy'):
          ax.plot_date(canal_aggregate_Wateryear1.Date,
                       np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1), fmt='-', c=cols[0])
          ax.plot_date(canal_aggregate_Wateryear2.Date,
                      np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1), fmt='--', c=cols[3])
          ax.set_ylabel('Deliveries (taf/wy)')
        elif (aggregation == 'month'):
          ax.plot_date(canal_aggregate_Wateryear_Month1.Date,
                       np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1), fmt='-', c=cols[0])
          ax.plot_date(canal_aggregate_Wateryear_Month2.Date,
                       np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1), fmt='--', c=cols[3])
          ax.set_ylabel('Deliveries (taf/month)')
        if ((i == 0) & (j == 2)):
          ax.legend(['Historical', 'Modeled'])
        ax.set_xlabel('Date')
      elif (plot_type == 'scatter'):
        if (aggregation == 'wy'):
          ax.scatter(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1),
                     np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1), c=cols[0])
          ax.plot(ax.get_xlim(), ax.get_xlim(), ls="--", c=".7")
          ax.set_xlabel('Scenario 1 Deliveries (taf/wy)')
          ax.set_ylabel('Scenario 2 Deliveries (taf/wy)')
        elif (aggregation == 'month'):
          ax.scatter(np.sum(canal_aggregate_Wateryear_Month1.loc[:, ind], axis=1),
                     np.sum(canal_aggregate_Wateryear_Month2.loc[:, ind], axis=1), c=cols[0])
          ax.plot(ax.get_xlim(), ax.get_xlim(), ls="--", c=".7")
          ax.set_xlabel('Scenario 1 Deliveries (taf/month)')
          ax.set_ylabel('Scenario 2 Deliveries (taf/month)')
      ax.annotate(d[i][j], xy=(ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.91,
                               ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.95))
  plt.savefig('calfews_src/figs/compareScenarios/%s/compareKNR_%s_%s_%s_%s.png' % (folder_name, flow_type, plot_type, aggregation, name), dpi=150)




### plot pdfs of deliveries, FKC
flow_type = 'turnout'   # 'flow' or 'turnout'
d_list = [[['all','LWT','DLE'],
          ['XVC','KNR','AEC']]]      # 'all' or pick a district key
fig = plt.figure(figsize=(18, 9))
for k in range(len(d_list)):
  d = d_list[k]
  gs1 = gridspec.GridSpec(2,3)
  for i in range(2):
    for j in range(3):
      ax = plt.subplot(gs1[i,j])
      ax.tick_params(axis='y', which='both', labelleft=True, labelright=False)
      ax.tick_params(axis='x', which='both', labelbottom=True, labeltop=False)
      if (d[i][j] == 'all'):
        ind = (ind_canal_flowtype1 == flow_type) & (ind_canal_waterway1 == 'FKC')
      else:
        ind = (ind_canal_flowtype1 == flow_type) & (ind_canal_waterway1 == 'FKC') & (ind_canal_recipient1 == d[i][j])
      maxbin = max(np.max(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1)), np.max(np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1)))
      ax.hist(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1), alpha=0.6, color=cols[0], normed=True, bins=np.arange(0,maxbin+2,step=(maxbin+1)/11))
      ax.hist(np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1), alpha=0.6, color=cols[3], normed=True, bins=np.arange(0,maxbin+2,step=(maxbin+1)/11))
      ax.legend(['Scenario 1', 'Scenario 2'])
      ax.axvline(np.sum(canal_aggregate_Wateryear1.loc[:, ind], axis=1).mean(), c=cols[0])
      ax.axvline(np.sum(canal_aggregate_Wateryear2.loc[:, ind], axis=1).mean(), c=cols[3], ls='--')
      ax.set_xlabel('Total turnout (taf/wy)')
      ax.set_title(d[i][j])
plt.savefig('calfews_src/figs/compareScenarios/%s/pdf_%s.png' % (folder_name,flow_type), dpi=150)


