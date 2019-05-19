import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import cm
import importlib
import cord.postprocess.load_model_data as load_model_data


sns.set()
sns.set_context('paper', font_scale=3)

cmap = cm.get_cmap('viridis')
cols = [cmap(0.1),cmap(0.3),cmap(0.6),cmap(0.95)]
cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560



# ### plot synthetic vs observed environmental data
# observations = pd.read_csv('cord/data/input/cord-data.csv', index_col=0, parse_dates=True)
# simulated_cord_data = pd.read_csv('cord/data/input/cord-data-sim.csv', index_col=0, parse_dates=True)
#
# plt.plot(np.log(observations.MIL_inf), color='k', lw=3)
# plt.plot(np.log(simulated_cord_data.MIL_inf), color = 'indianred', alpha=0.7, lw=3)
# plt.ylabel('Daily flow, ln(cfs)')
# plt.title('MIL-inflow')
#
# plt.plot(np.log(observations.PFT_inf), color='k', lw=3)
# plt.plot(np.log(simulated_cord_data.PFT_inf), color = 'indianred', alpha=0.7, lw=3)
# plt.ylabel('Daily flow, ln(cfs)')
# plt.title('PFT-inflow')
#
# plt.plot(np.log(observations.KWH_inf), color='k', lw=3)
# plt.plot(np.log(simulated_cord_data.KWH_inf), color = 'indianred', alpha=0.7, lw=3)
# plt.ylabel('Daily flow, ln(cfs)')
# plt.title('KWH-inflow')
#
# plt.plot(np.log(observations.SUC_inf), color='k', lw=3)
# plt.plot(np.log(simulated_cord_data.SUC_inf), color = 'indianred', alpha=0.7, lw=3)
# plt.ylabel('Daily flow, ln(cfs)')
# plt.title('SUC-inflow')
#
# plt.plot(np.log(observations.ISB_inf), color='k', lw=3)
# plt.plot(np.log(simulated_cord_data.ISB_inf), color = 'indianred', alpha=0.7, lw=3)
# plt.ylabel('Daily flow, ln(cfs)')
# plt.title('ISB-inflow')



### load canal data
importlib.reload(load_model_data)
canal1, canal_aggregate_Wateryear1, canal_aggregate_Wateryear_Month1, ind_canal_waterway1, ind_canal_recipient1, ind_canal_flowtype1 = \
            load_model_data.load_canal_data('cord/data/results/FKC_capacity_wy2017/canal_results_simulation.csv')
canal2, canal_aggregate_Wateryear2, canal_aggregate_Wateryear_Month2, ind_canal_waterway2, ind_canal_recipient2, ind_canal_flowtype2 = \
            load_model_data.load_canal_data('cord/data/results/FKC_capacity_rehab_full/canal_results_simulation.csv')
canal3, canal_aggregate_Wateryear3, canal_aggregate_Wateryear_Month3, ind_canal_waterway3, ind_canal_recipient3, ind_canal_flowtype3 = \
            load_model_data.load_canal_data('cord/data/results/FKC_capacity_wy2017__LWT_inleiubank/canal_results_simulation.csv')
canal4, canal_aggregate_Wateryear4, canal_aggregate_Wateryear_Month4, ind_canal_waterway4, ind_canal_recipient4, ind_canal_flowtype4 = \
            load_model_data.load_canal_data('cord/data/results/FKC_capacity_rehab_full__LWT_inleiubank/canal_results_simulation.csv')

# folder_name = 'FKC_capacity_wy2017'
# os.makedirs('cord/figs/flowDiagrams/' + folder_name, exist_ok=True)

# get median, wettest & dryest years
tot_flow = canal_aggregate_Wateryear1.FKC_COF_flow #/ 365*tafd_cfs
flow_order = np.argsort(canal_aggregate_Wateryear1.FKC_COF_flow)
# plt.hist(tot_flow.iloc[:,0])
wyMedian = np.where(tot_flow == np.median(tot_flow))[0]
wyMax = np.where(tot_flow == np.max(tot_flow))[0]
wyMin = np.where(tot_flow == np.min(tot_flow))[0]

# only keep FKC, turnout. remove rivers, MIL
turnout_aggregate_Wateryear1 = canal_aggregate_Wateryear1.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'turnout')) & ~((ind_canal_recipient1 == 'MIL') | (ind_canal_recipient1 == 'KGR') | (ind_canal_recipient1 == 'KWR') | (ind_canal_recipient1 == 'TLR'))]
turnout_aggregate_Wateryear2 = canal_aggregate_Wateryear2.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'turnout')) & ~((ind_canal_recipient1 == 'MIL') | (ind_canal_recipient1 == 'KGR') | (ind_canal_recipient1 == 'KWR') | (ind_canal_recipient1 == 'TLR'))]
turnout_aggregate_Wateryear3 = canal_aggregate_Wateryear3.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'turnout')) & ~((ind_canal_recipient1 == 'MIL') | (ind_canal_recipient1 == 'KGR') | (ind_canal_recipient1 == 'KWR') | (ind_canal_recipient1 == 'TLR'))]
turnout_aggregate_Wateryear4 = canal_aggregate_Wateryear4.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'turnout')) & ~((ind_canal_recipient1 == 'MIL') | (ind_canal_recipient1 == 'KGR') | (ind_canal_recipient1 == 'KWR') | (ind_canal_recipient1 == 'TLR'))]
ind_turnout_flowtype1 = turnout_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[2])
ind_turnout_waterway1 = turnout_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[0])
ind_turnout_recipient1 = turnout_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[1])
# only keep FKC, flow. remove MIL
flow_aggregate_Wateryear1 = canal_aggregate_Wateryear1.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'flow')) & ~(ind_canal_recipient1 == 'MIL') ]
flow_aggregate_Wateryear2 = canal_aggregate_Wateryear2.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'flow')) & ~(ind_canal_recipient1 == 'MIL') ]
flow_aggregate_Wateryear3 = canal_aggregate_Wateryear3.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'flow')) & ~(ind_canal_recipient1 == 'MIL') ]
flow_aggregate_Wateryear4 = canal_aggregate_Wateryear4.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'flow')) & ~(ind_canal_recipient1 == 'MIL') ]
ind_flow_flowtype1 = flow_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[2])
ind_flow_waterway1 = flow_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[0])
ind_flow_recipient1 = flow_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[1])
del canal1, canal_aggregate_Wateryear1,ind_canal_recipient1,ind_canal_flowtype1,ind_canal_waterway1



# plot flow along canal nodes
cols_flow = [cmap(i) for i in np.arange(0.1,0.9,0.8/flow_aggregate_Wateryear1.shape[0])]
for y in range(flow_aggregate_Wateryear1.shape[0]):
  plt.plot(np.arange(len(ind_flow_recipient1)), flow_aggregate_Wateryear1.iloc[y,:], c=cols_flow[y], alpha=0.7)
  plt.xticks(np.arange(len(ind_flow_recipient1)), ind_flow_recipient1, rotation=90)
# plt.xlabel('Inflow node along Friant-Kern Canal')
plt.plot(np.arange(len(ind_flow_recipient1)), flow_aggregate_Wateryear1.mean(axis=0), c='k', alpha=0.7, lw=4)
plt.ylabel('Wateryear flow (taf)')
plt.ylim([0,2000])

# plot mean flow along canal nodes
plt.plot(np.arange(len(ind_flow_recipient1)), flow_aggregate_Wateryear1.mean(axis=0), c='k', alpha=0.7, lw=4)
plt.xticks(np.arange(len(ind_flow_recipient1)), ind_flow_recipient1, rotation=90)
# plt.xlabel('Inflow node along Friant-Kern Canal')
plt.ylabel('Wateryear flow (taf)')
plt.ylim([0,2000])




### stacked deliveries
sort_x = False
screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
# screen_districts = False
order_by_diversion = False
cols_districts = [cmap(i) for i in np.arange(0.1,1,0.9/turnout_aggregate_Wateryear1.shape[1])]
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# get x-axis
if (sort_x):
  x = tot_flow.iloc[flow_order]
  sort = flow_order
else:
  x = turnout_aggregate_Wateryear1.index
  sort = range(turnout_aggregate_Wateryear1.shape[0])
# order stack by north-south or by max diversion level
if (order_by_diversion):
  max_div = turnout_aggregate_Wateryear1.max(axis=0)
  turnout_aggregate_Wateryear1_stacked = turnout_aggregate_Wateryear1.iloc[:,np.argsort(max_div)]
  # turnout_aggregate_Wateryear1_stacked = turnout_aggregate_Wateryear1_stacked[turnout_aggregate_Wateryear1_stacked.columns[::-1]]
  if (screen_districts):
    ind_district = [d in screen_districts for d in ind_turnout_recipient1[np.argsort(max_div)][::-1]]
else:
  turnout_aggregate_Wateryear1_stacked = turnout_aggregate_Wateryear1[turnout_aggregate_Wateryear1.columns[::-1]]
if (ind_district[-1]):
  plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[sort, 0], color=cols_districts[0], alpha=0.7)
else:
  plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[sort, 0], color='0.8', alpha=0.7)
for i in range(1, turnout_aggregate_Wateryear1.shape[1]):
  turnout_aggregate_Wateryear1_stacked.iloc[:,i] = turnout_aggregate_Wateryear1_stacked.iloc[:,i] + turnout_aggregate_Wateryear1_stacked.iloc[:,i-1]
  if (ind_district[-(i+1)]):
    plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[sort,i],
                     turnout_aggregate_Wateryear1_stacked.iloc[sort,i-1], color=cols_districts[i], alpha=0.7)
  else:
    plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[sort, i],
                     turnout_aggregate_Wateryear1_stacked.iloc[sort, i - 1], color='0.8', alpha=0.7)
# plt.legend(ind_turnout_recipient1[::-1])
plt.xlabel('Flow into COF (taf/yr)')
plt.ylabel('Cumulative turnout flow (taf/yr)')




### delivery pdf
# cols_districts = [cmap(i) for i in np.arange(0.1,1,0.9/turnout_aggregate_Wateryear1.shape[1])]
fig = plt.figure(figsize=(18, 9))
gs1 = gridspec.GridSpec(1,3)
ax = plt.subplot2grid((1,3), (0,0))
# screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# ax.hist(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color=cols_districts[-1], alpha=0.6, normed=True)
sns.kdeplot(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color='k', kernel='epa')
# sns.kdeplot(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1), color=cols[1], kernel='epa', label='Friant rehab')
# sns.kdeplot(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1), color=cols[2], kernel='epa', label='LWT bank')
# sns.kdeplot(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1), color=cols[3], kernel='epa', label='Friant rehab + LWT bank')
# ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Diversions (tAF/yr)')
ax.set_ylabel('Density')
ax.set_title('Friant-Kern Canal')
ax.set_xlim([0,3500])
ax.axvline(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1).mean(), color='k', lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1).mean(), color=cols[1], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1).mean(), color=cols[2], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1).mean(), color=cols[3], lw=2, ls='--')
ax = plt.subplot2grid((1,3), (0,1))
screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
# screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# ax.hist(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
#         color=cols_districts[-(int(np.median(np.arange(0, ind_turnout_recipient1.shape[0])[ind_district]))+1)], alpha=0.6, normed=True)
sns.kdeplot(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color='k', kernel='epa')
# sns.kdeplot(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1), color=cols[1], kernel='epa', label='Friant rehab')
# sns.kdeplot(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1), color=cols[2], kernel='epa', label='LWT bank')
# sns.kdeplot(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1), color=cols[3], kernel='epa', label='Friant rehab + LWT bank')
ax.set_xlim([0,800])
ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Diversions (tAF/yr)')
ax.set_title('Lower Tule River ID')
ax.axvline(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1).mean(), color='k', lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1).mean(), color=cols[1], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1).mean(), color=cols[2], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1).mean(), color=cols[3], lw=2, ls='--')
ax = plt.subplot2grid((1,3), (0,2))
screen_districts = ['DLE','KRT','SSJ','SFW']
# screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# ax.hist(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
#         color=cols_districts[-(int(np.median(np.arange(0, ind_turnout_recipient1.shape[0])[ind_district]))+1)], alpha=0.6, normed=True)
sns.kdeplot(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color='k', kernel='epa')
# sns.kdeplot(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1), color=cols[1], kernel='epa', label='Friant rehab')
# sns.kdeplot(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1), color=cols[2], kernel='epa', label='LWT bank')
# sns.kdeplot(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1), color=cols[3], kernel='epa', label='Friant rehab + LWT bank')
ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Diversions (tAF/yr)')
ax.set_title('Southern Friant IDs')
ax.axvline(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1).mean(), color='k', lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1).mean(), color=cols[1], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1).mean(), color=cols[2], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1).mean(), color=cols[3], lw=2, ls='--')



### delivery differences scatter
# cols_districts = [cmap(i) for i in np.arange(0.1,1,0.9/turnout_aggregate_Wateryear1.shape[1])]
fig = plt.figure(figsize=(18, 9))
gs1 = gridspec.GridSpec(1,3)
ax = plt.subplot2grid((1,3), (0,0))
# screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
ax.axhline(0, color='0.4', zorder=1)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[0], alpha=0.7, zorder=2, s=50)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[2], alpha=0.7, zorder=2, s=50)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[3], alpha=0.7, zorder=2, s=50)
# ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Baseline deliveries (tAF/yr)')
ax.set_ylabel('Scenario increase (tAF/yr)')
# ax.set_xlim([0,3500])
ax.axhline((turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[0], lw=2, ls='--', zorder=1)
ax.axhline((turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[2], lw=2, ls='--', zorder=1)
ax.axhline((turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[3], lw=2, ls='--', zorder=1)
ax = plt.subplot2grid((1,3), (0,1))
screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
# screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
ax.axhline(0, color='0.4', zorder=1)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[0], alpha=0.7, zorder=2, s=50)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[2], alpha=0.7, zorder=2, s=50)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[3], alpha=0.7, zorder=2, s=50)
# ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Baseline deliveries (tAF/yr)')
# ax.set_ylabel('Scenario increase (tAF/yr)')
# ax.set_xlim([0,3500])
ax.axhline((turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[0], lw=2, ls='--', zorder=1)
ax.axhline((turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[2], lw=2, ls='--', zorder=1)
ax.axhline((turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[3], lw=2, ls='--', zorder=1)
ax = plt.subplot2grid((1,3), (0,2))
screen_districts = ['DLE','KRT','SSJ','SFW']
# screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
ax.axhline(0, color='0.4', zorder=1)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[0], alpha=0.7, zorder=2, s=50)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[2], alpha=0.7, zorder=2, s=50)
ax.scatter(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1)- \
           turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
           color=cols[3], alpha=0.7, zorder=2, s=50)
# ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Baseline deliveries (tAF/yr)')
# ax.set_ylabel('Scenario increase (tAF/yr)')
# ax.set_xlim([0,3500])
ax.axhline((turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[0], lw=2, ls='--', zorder=1)
ax.axhline((turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[2], lw=2, ls='--', zorder=1)
ax.axhline((turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1)-\
            turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1)).mean(), color=cols[3], lw=2, ls='--', zorder=1)





# ### sankey diagram for wet/dry years
# df = pd.DataFrame({'name': ind_turnout_recipient1, 'median': turnout_aggregate_Wateryear1.iloc[wyMedian,:].values[0],
#                    'dryest': turnout_aggregate_Wateryear1.iloc[wyMin,:].values[0],
#                    'wettest': turnout_aggregate_Wateryear1.iloc[wyMax,:].values[0]})
# df = df.reindex(index=df.index[::-1]).reset_index(drop=True)
# df['label'] = ''
# df.label.loc[df.name == 'LWT'] = 'LWT'
#
# sankey(left=df['name'], right=df['name'],leftWeight=df['median'], rightWeight=df['wettest'],leftLabels=df['name'], rightLabels=df['name'],aspect=20, fontsize=12, figureName="flow")
#




### get district data
folder = 'FKC_capacity_wy2017'
importlib.reload(load_model_data)
district_modeled_aggregate_Wateryear, friant_districts, source_modeled, districts_modeled, WT_modeled = \
  load_model_data.load_district_data('cord/data/results/'+folder+'/district_results_full_simulation.csv')

leiu_modeled_aggregate_wateryear, leiu_banker_modeled, leiu_bankee_modeled = \
  load_model_data.load_leiu_data('cord/data/results/'+folder+'/leiu_results_simulation.csv')

bank_modeled_aggregate_wateryear, bank_banker_modeled, bank_bankee_modeled = \
  load_model_data.load_bank_data('cord/data/results/'+folder+'/bank_results_simulation.csv')

leiu_haircuts = {'ARV':0.9}
bank_haircuts = {'NKB':0.94, 'R21':0.94}
df_reorg = pd.DataFrame({'Wateryear':[],'District':[],'Axis':[],'Label':[],'Volume':[],'Obs':[]})
counter = 0
for d in friant_districts:
  # get pumping and irrigation demand at district
  irrig = district_modeled_aggregate_Wateryear.loc[:, (districts_modeled == d)&(source_modeled == 'irr')].sum(axis=1)
  pumping = district_modeled_aggregate_Wateryear.loc[:,(districts_modeled==d)&(source_modeled=='pumping')].sum(axis=1)

  # get this district's leiu & banking, as bankee
  leiu_bankee = leiu_modeled_aggregate_wateryear.loc[:,(leiu_banker_modeled==d)&(leiu_bankee_modeled!=d)]
  if (leiu_bankee.shape[1] == 0):
    leiu_bankee = pd.DataFrame(irrig * 0.0)
  else:
    # undo haircuts for deposits, so we have full amount recharged
    for i,b in enumerate(leiu_banker_modeled[(leiu_banker_modeled==d)&(leiu_bankee_modeled!=d)]):
      leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] > 0] = leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] > 0] / leiu_haircuts[b]

  bank_bankee = bank_modeled_aggregate_wateryear.loc[:,(bank_bankee_modeled==d)]
  if (bank_bankee.shape[1] == 0):
    bank_bankee = pd.DataFrame(irrig * 0.0)
  else:
    # undo haircuts for deposits, so we have full amount recharged
    for i,b in enumerate(bank_banker_modeled[bank_bankee_modeled==d]):
      bank_bankee.iloc[:,i].loc[bank_bankee.iloc[:,i] > 0] = bank_bankee.iloc[:,i].loc[bank_bankee.iloc[:,i] > 0] / bank_haircuts[b]
  # sum over all banks/leiu to get total recovered & banked
  water_banked_bankee = pd.DataFrame(irrig * 0.0)
  water_recovered_bankee = pd.DataFrame(irrig * 0.0)
  for y in leiu_bankee.index:
    water_banked_bankee.loc[y] = leiu_bankee.loc[y, leiu_bankee.loc[y, :] > 0].sum() + bank_bankee.loc[
      y, bank_bankee.loc[y, :] > 0].sum()
    water_recovered_bankee.loc[y] = -(
              leiu_bankee.loc[y, leiu_bankee.loc[y, :] < 0].sum() + bank_bankee.loc[y, bank_bankee.loc[y, :] < 0].sum())
  water_banked_bankee = water_banked_bankee.sum(axis=1)
  water_recovered_bankee = water_recovered_bankee.sum(axis=1)

  # get this district's leiu & banking, as banker. don't count own deliveries (ARV)
  leiu_banker = leiu_modeled_aggregate_wateryear.loc[:,(leiu_banker_modeled==d)&(leiu_bankee_modeled!=d)]
  if (leiu_banker.shape[1] == 0):
    leiu_banker = pd.DataFrame(irrig * 0.0)
  else:
    # undo haircuts for deposits, so we have full amount recharged
    for i,b in enumerate(leiu_banker_modeled[(leiu_banker_modeled==d)&(leiu_bankee_modeled!=d)]):
      leiu_banker.iloc[:,i].loc[leiu_banker.iloc[:,i] > 0] = leiu_banker.iloc[:,i].loc[leiu_banker.iloc[:,i] > 0] / leiu_haircuts[d]
  bank_banker = leiu_modeled_aggregate_wateryear.loc[:,(bank_banker_modeled==d)]
  if (bank_banker.shape[1] == 0):
    bank_banker = pd.DataFrame(irrig * 0.0)
  else:
    # undo haircuts for deposits, so we have full amount recharged
    for i,b in enumerate(bank_banker_modeled[bank_banker_modeled==d]):
      bank_banker.iloc[:,i].loc[bank_banker.iloc[:,i] > 0] = bank_banker.iloc[:,i].loc[bank_banker.iloc[:,i] > 0] / bank_haircuts[d]
  # sum over all banks/leiu to get total recovered & banked
  water_banked_banker = pd.DataFrame(irrig * 0.0)
  water_recovered_banker = pd.DataFrame(irrig * 0.0)
  for y in leiu_banker.index:
    water_banked_banker.loc[y] = leiu_banker.loc[y, leiu_banker.loc[y, :] > 0].sum() + bank_banker.loc[
      y, bank_banker.loc[y, :] > 0].sum()
    water_recovered_banker.loc[y] = -(
              leiu_banker.loc[y, leiu_banker.loc[y, :] < 0].sum() + bank_banker.loc[y, bank_banker.loc[y, :] < 0].sum())
  water_banked_banker = water_banked_banker.sum(axis=1)
  water_recovered_banker = water_recovered_banker.sum(axis=1)

  # get exchanged SW and exchanged GW
  # exchanged_SW = district_modeled_aggregate_Wateryear.loc[:, (districts_modeled == d)&(WT_modeled == 'SW')].sum(axis=1)
  exchanged_GW = district_modeled_aggregate_Wateryear.loc[:, (districts_modeled == d)&(WT_modeled == 'GW')].sum(axis=1)

  # now get contract deliveries all non-friant as 'otherSW'
  delivery_friant = irrig * 0.0
  delivery_otherSW = irrig * 0.0

  delivery_friant -= exchanged_GW

  for c in ['friant1','friant2']:
    delivery_friant += district_modeled_aggregate_Wateryear.loc[:,
                      (districts_modeled==d)&((WT_modeled=='flood')|(WT_modeled=='delivery'))&
                      (source_modeled==c)].sum(axis=1)

  for c in ['cvc', 'kings', 'kaweah', 'tule', 'kern', 'tableA', 'cvpdelta']:
    delivery_otherSW += district_modeled_aggregate_Wateryear.loc[:,
                       (districts_modeled == d) & ((WT_modeled == 'flood') | (WT_modeled == 'delivery')) &
                       (source_modeled == c)].sum(axis=1)

  # lastly, recharge = in - (non-recharge-out)
  recharged = (delivery_friant + delivery_otherSW + pumping + water_banked_banker + water_recovered_bankee) - \
             (irrig + water_banked_bankee + water_recovered_banker)
  #
  # df_wy1$District < - factor(df_wy1$District, levels = c('LWT', 'DLE', 'KRT', 'SSJ', 'SFW'))
  # df_wy1$Label < - factor(df_wy1$Label, levels = c('Pumping', 'Recovered_in', 'Banked_in', 'OtherSW', 'Friant', 'LWT',
  #                                                  'DLE', 'KRT', 'SSJ', 'SFW', 'Recovered_out', 'Banked_out',
  #                                                  'Recharged', 'Irrigation'))
  # df_wy1$Axis < - factor(df_wy1$Axis, levels = c('Source', 'District', 'Use'))

  # now record data. need to fill in sources & uses in equal volumes to have one observation per alluvium for Sankey plot. Doesn't need to correspond to actual relationship between sources and uses.
  for y in district_modeled_aggregate_Wateryear.index:
    sources = [pumping.loc[y], water_recovered_bankee.loc[y], water_banked_banker.loc[y], delivery_otherSW.loc[y], delivery_friant.loc[y]]
    sources_names = ['Pumping', 'Recovered_in', 'Banked_in', 'OtherSW', 'Friant']
    uses = [water_recovered_banker.loc[y], water_banked_bankee.loc[y], recharged.loc[y], irrig.loc[y]]
    uses_names = ['Recovered_out', 'Banked_out', 'Recharged', 'Irrigation']
    s = 0
    u = 0
    while ((s < 5)&(u < 4)):
      if (sources[s] > uses[u]):
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Source',
                        'Label': sources_names[s], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'District',
                        'Label': d, 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Use',
                        'Label': uses_names[u], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
        sources[s] -= uses[u]
        uses[u] -= uses[u]
        u += 1
        counter += 1
      elif (sources[s] < uses[u]):
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Source',
                        'Label': sources_names[s], 'Volume': sources[s], 'Obs': counter}, index=[0])).reset_index(drop=True)
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'District',
                        'Label': d, 'Volume': sources[s], 'Obs': counter}, index=[0])).reset_index(drop=True)
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Use',
                        'Label': uses_names[u], 'Volume': sources[s], 'Obs': counter}, index=[0])).reset_index(drop=True)
        uses[u] -= sources[s]
        sources[s] -= sources[s]
        s += 1
        counter += 1
      else:
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Source',
                        'Label': sources_names[s], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'District',
                        'Label': d, 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
        df_reorg = df_reorg.append(
          pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Use',
                        'Label': uses_names[u], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
        sources[s] -= uses[u]
        uses[u] -= uses[u]
        s += 1
        u += 1
        counter += 1


df_reorg.to_csv('cord/data/results/'+folder+'/district_reorg.csv', index=False)







### delivery pdf
fig = plt.figure(figsize=(18, 9))
gs1 = gridspec.GridSpec(1,3)
ax = plt.subplot2grid((1,3), (0,0))
# screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# ax.hist(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color=cols_districts[-1], alpha=0.6, normed=True)
sns.kdeplot(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color='k', kernel='epa')
# sns.kdeplot(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1), color=cols[1], kernel='epa', label='Friant rehab')
# sns.kdeplot(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1), color=cols[2], kernel='epa', label='LWT bank')
# sns.kdeplot(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1), color=cols[3], kernel='epa', label='Friant rehab + LWT bank')
# ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Diversions (tAF/yr)')
ax.set_ylabel('Density')
ax.set_title('Friant-Kern Canal')
ax.set_xlim([0,3500])
ax.axvline(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1).mean(), color='k', lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1).mean(), color=cols[1], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1).mean(), color=cols[2], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1).mean(), color=cols[3], lw=2, ls='--')
ax = plt.subplot2grid((1,3), (0,1))
screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
# screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# ax.hist(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
#         color=cols_districts[-(int(np.median(np.arange(0, ind_turnout_recipient1.shape[0])[ind_district]))+1)], alpha=0.6, normed=True)
sns.kdeplot(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color='k', kernel='epa')
# sns.kdeplot(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1), color=cols[1], kernel='epa', label='Friant rehab')
# sns.kdeplot(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1), color=cols[2], kernel='epa', label='LWT bank')
# sns.kdeplot(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1), color=cols[3], kernel='epa', label='Friant rehab + LWT bank')
ax.set_xlim([0,800])
ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Diversions (tAF/yr)')
ax.set_title('Lower Tule River ID')
ax.axvline(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1).mean(), color='k', lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1).mean(), color=cols[1], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1).mean(), color=cols[2], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1).mean(), color=cols[3], lw=2, ls='--')
ax = plt.subplot2grid((1,3), (0,2))
screen_districts = ['DLE','KRT','SSJ','SFW']
# screen_districts = False
# screen for particular districts
if (screen_districts):
  ind_district = [d in screen_districts for d in ind_turnout_recipient1]
else:
  ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# ax.hist(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1),
#         color=cols_districts[-(int(np.median(np.arange(0, ind_turnout_recipient1.shape[0])[ind_district]))+1)], alpha=0.6, normed=True)
sns.kdeplot(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1), color='k', kernel='epa')
# sns.kdeplot(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1), color=cols[1], kernel='epa', label='Friant rehab')
# sns.kdeplot(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1), color=cols[2], kernel='epa', label='LWT bank')
# sns.kdeplot(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1), color=cols[3], kernel='epa', label='Friant rehab + LWT bank')
ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax.set_xlabel('Diversions (tAF/yr)')
ax.set_title('Southern Friant IDs')
ax.axvline(turnout_aggregate_Wateryear1.loc[:,ind_district].sum(axis=1).mean(), color='k', lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear2.loc[:,ind_district].sum(axis=1).mean(), color=cols[1], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear3.loc[:,ind_district].sum(axis=1).mean(), color=cols[2], lw=2, ls='--')
# ax.axvline(turnout_aggregate_Wateryear4.loc[:,ind_district].sum(axis=1).mean(), color=cols[3], lw=2, ls='--')
