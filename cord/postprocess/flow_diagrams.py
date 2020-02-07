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
cmap_coolWarm = cm.get_cmap('coolwarm')
cols = [cmap(0.1),cmap(0.3),cmap(0.6),cmap(0.95)]
cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560
eps = 1e-10


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
            load_model_data.load_canal_data('cord/data/results/FKC_capacity_wy2017__LWT_inleiubank_DLESSJSFW_0/canal_results_simulation.csv')
canal4, canal_aggregate_Wateryear4, canal_aggregate_Wateryear_Month4, ind_canal_waterway4, ind_canal_recipient4, ind_canal_flowtype4 = \
            load_model_data.load_canal_data('cord/data/results/FKC_capacity_rehab_full__LWT_inleiubank_DLESSJSFW_0/canal_results_simulation.csv')

# folder_name = 'FKC_capacity_wy2017'
# os.makedirs('cord/figs/flowDiagrams/' + folder_name, exist_ok=True)

# get median, wettest & dryest years
tot_flow = canal_aggregate_Wateryear1.FKC_COF_flow #/ 365*tafd_cfs
flow_order = np.argsort(tot_flow)
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
cols_flow = [cmap_coolWarm(i) for i in np.arange(0.99,0.01,-0.98/flow_aggregate_Wateryear1.shape[0])]
for y in range(flow_aggregate_Wateryear1.shape[0]):
  plt.plot(np.arange(len(ind_flow_recipient1)), flow_aggregate_Wateryear1.iloc[flow_order.iloc[y],:], c=cols_flow[y], alpha=0.8,lw=2)
  plt.xticks(np.arange(len(ind_flow_recipient1)), ind_flow_recipient1, rotation=90)
# plt.xlabel('Inflow node along Friant-Kern Canal')
plt.plot(np.arange(len(ind_flow_recipient1)), flow_aggregate_Wateryear1.mean(axis=0), c='k', alpha=0.7, lw=4)
plt.ylabel('Total flow (tAF/yr)')
plt.ylim([0,1800])

# plot mean flow along canal nodes
plt.plot(np.arange(len(ind_flow_recipient1)), flow_aggregate_Wateryear1.mean(axis=0), c='k', alpha=0.7, lw=4)
plt.xticks(np.arange(len(ind_flow_recipient1)), ind_flow_recipient1, rotation=90)
# plt.xlabel('Inflow node along Friant-Kern Canal')
plt.ylabel('Total flow (tAF/yr)')
plt.ylim([0,1800])




### stacked deliveries
sort_x = False
# screen_districts = ['LWT']#,'DLE','KRT','SFW','SSJ']
screen_districts = False
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
# plt.xlabel('Flow into COF (taf/yr)')
plt.ylabel('Stacked deliveries (tAF/yr)')




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
screen_districts = ['DLE','SSJ','SFW']
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
folders = ['FKC_capacity_wy2017','FKC_capacity_rehab_full']
SW_volume_sales = {folders[0]:{}, folders[1]:{}}
SW_volume_purchases = {folders[0]:{}, folders[1]:{}}
bank_volume = {folders[0]:{}, folders[1]:{}}
SW_cash_sales = {folders[0]:{}, folders[1]:{}}
SW_cash_purchases = {folders[0]:{}, folders[1]:{}}
bank_cash = {folders[0]:{}, folders[1]:{}}
for folder in folders:#,'FKC_capacity_wy2017__LWT_inleiubank_ARV_0','FKC_capacity_rehab_full__LWT_inleiubank_ARV_0','FKC_capacity_wy2017__LWT_inleiubank_ARV_withRecharge_100','FKC_capacity_rehab_full__LWT_inleiubank_withRecharge_100']:
# for folder in ['FKC_capacity_wy2017__LWT_inleiubank_ARV_withRecharge_100']:
# folder = 'FKC_capacity_wy2017__LWT_inleiubank_ARV_0'
  importlib.reload(load_model_data)
  district_modeled_aggregate_Wateryear, district_modeled_aggregate_Wateryear_Month, friant_districts, source_modeled, districts_modeled, WT_modeled = \
    load_model_data.load_district_data('cord/data/results/'+folder+'/district_results_full_simulation.csv')

  leiu_modeled_aggregate_Wateryear, leiu_modeled_aggregate_Wateryear_Month, leiu_banker_modeled, leiu_bankee_modeled = \
    load_model_data.load_leiu_data('cord/data/results/'+folder+'/leiu_results_simulation.csv')

  bank_modeled_aggregate_Wateryear, bank_modeled_aggregate_Wateryear_Month, bank_banker_modeled, bank_bankee_modeled = \
    load_model_data.load_bank_data('cord/data/results/'+folder+'/bank_results_simulation.csv')

  leiu_haircuts = {'ARV':0.9, 'LWT':0.9, 'RRB':0.9}
  bank_haircuts = {'NKB':0.94, 'R21':0.94, 'POSO':0.94}
  df_reorg = pd.DataFrame({'Wateryear':[],'District':[],'Axis':[],'Label':[],'Volume':[],'Obs':[]})
  counter = 0

  # for d in friant_districts:
  #   # get pumping and irrigation demand at district
  #   irrig = district_modeled_aggregate_Wateryear.loc[:, (districts_modeled == d)&(source_modeled == 'irr')].sum(axis=1)
  #   pumping = district_modeled_aggregate_Wateryear.loc[:,(districts_modeled==d)&(source_modeled=='pumping')].sum(axis=1)
  #
  #   # get this district's leiu & banking, as bankee
  #   leiu_bankee = leiu_modeled_aggregate_Wateryear.loc[:,(leiu_bankee_modeled==d)&(leiu_banker_modeled!=d)]
  #   if (leiu_bankee.shape[1] == 0):
  #     leiu_bankee = pd.DataFrame(irrig * 0.0)
  #   else:
  #     # undo haircuts for deposits, so we have full amount recharged
  #     for i,b in enumerate(leiu_banker_modeled[(leiu_bankee_modeled==d)&(leiu_banker_modeled!=d)]):
  #       leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] > 0] = leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] > 0] / leiu_haircuts[b]
  #
  #   bank_bankee = bank_modeled_aggregate_Wateryear_Month.loc[:,(bank_bankee_modeled==d)]
  #   if (bank_bankee.shape[1] == 0):
  #     bank_bankee = pd.DataFrame(irrig * 0.0)
  #   else:
  #     # undo haircuts for deposits, so we have full amount recharged
  #     for i,b in enumerate(bank_banker_modeled[bank_bankee_modeled==d]):
  #       bank_bankee.iloc[:,i].loc[bank_bankee.iloc[:,i] > 0] = bank_bankee.iloc[:,i].loc[bank_bankee.iloc[:,i] > 0] / bank_haircuts[b]
  #   # sum over all banks/leiu to get total recovered & banked
  #   water_banked_bankee = pd.DataFrame(irrig * 0.0)
  #   water_recovered_bankee = pd.DataFrame(irrig * 0.0)
  #   for y in leiu_bankee.index:
  #     water_banked_bankee.loc[y] = leiu_bankee.loc[y, leiu_bankee.loc[y, :] > 0].sum() + bank_bankee.loc[
  #       y, bank_bankee.loc[y, :] > 0].sum()
  #     water_recovered_bankee.loc[y] = -(
  #               leiu_bankee.loc[y, leiu_bankee.loc[y, :] < 0].sum() + bank_bankee.loc[y, bank_bankee.loc[y, :] < 0].sum())
  #   water_banked_bankee = water_banked_bankee.sum(axis=1)
  #   water_recovered_bankee = water_recovered_bankee.sum(axis=1)
  #
  #   # get this district's leiu & banking, as banker. don't count own deliveries (ARV)
  #   leiu_banker = leiu_modeled_aggregate_Wateryear.loc[:,(leiu_banker_modeled==d)&(leiu_bankee_modeled!=d)]
  #   if (leiu_banker.shape[1] == 0):
  #     leiu_banker = pd.DataFrame(irrig * 0.0)
  #   else:
  #     # undo haircuts for deposits, so we have full amount recharged
  #     for i,b in enumerate(leiu_banker_modeled[(leiu_banker_modeled==d)&(leiu_bankee_modeled!=d)]):
  #       leiu_banker.iloc[:,i].loc[leiu_banker.iloc[:,i] > 0] = leiu_banker.iloc[:,i].loc[leiu_banker.iloc[:,i] > 0] / leiu_haircuts[d]
  #   bank_banker = leiu_modeled_aggregate_Wateryear.loc[:,(bank_banker_modeled==d)]
  #   if (bank_banker.shape[1] == 0):
  #     bank_banker = pd.DataFrame(irrig * 0.0)
  #   else:
  #     # undo haircuts for deposits, so we have full amount recharged
  #     for i,b in enumerate(bank_banker_modeled[bank_banker_modeled==d]):
  #       bank_banker.iloc[:,i].loc[bank_banker.iloc[:,i] > 0] = bank_banker.iloc[:,i].loc[bank_banker.iloc[:,i] > 0] / bank_haircuts[d]
  #   # sum over all banks/leiu to get total recovered & banked
  #   water_banked_banker = pd.DataFrame(irrig * 0.0)
  #   water_recovered_banker = pd.DataFrame(irrig * 0.0)
  #   for y in leiu_banker.index:
  #     water_banked_banker.loc[y] = leiu_banker.loc[y, leiu_banker.loc[y, :] > 0].sum() + bank_banker.loc[
  #       y, bank_banker.loc[y, :] > 0].sum()
  #     water_recovered_banker.loc[y] = -(
  #               leiu_banker.loc[y, leiu_banker.loc[y, :] < 0].sum() + bank_banker.loc[y, bank_banker.loc[y, :] < 0].sum())
  #   water_banked_banker = water_banked_banker.sum(axis=1)
  #   water_recovered_banker = water_recovered_banker.sum(axis=1)
  #
  #   # count recovery from own leiu bank as pumping. deposits will be calculated as recharge. assume no haircut.
  #   own_recovery = leiu_modeled_aggregate_Wateryear.loc[:,(leiu_banker_modeled==d)&(leiu_bankee_modeled==d)]
  #   if (own_recovery.shape[1] == 0):
  #     own_recovery = pd.DataFrame(irrig * 0.0)
  #   own_recovery.loc[own_recovery.iloc[:, 0] > -eps, :] = 0
  #   pumping += -(own_recovery.sum(axis=1))
  #
  #   # get exchanged SW and exchanged GW
  #   # exchanged_SW = district_modeled_aggregate_Wateryear.loc[:, (districts_modeled == d)&(WT_modeled == 'SW')].sum(axis=1)
  #   exchanged_GW = district_modeled_aggregate_Wateryear.loc[:, (districts_modeled == d)&(WT_modeled == 'GW')].sum(axis=1)
  #
  #   # now get contract deliveries all non-friant as 'otherSW'
  #   delivery_friant = irrig * 0.0
  #   delivery_otherSW = irrig * 0.0
  #
  #   delivery_friant -= exchanged_GW
  #
  #   for c in ['friant1','friant2']:
  #     delivery_friant += district_modeled_aggregate_Wateryear.loc[:,
  #                       (districts_modeled==d)&((WT_modeled=='flood')|(WT_modeled=='flood_irrigation')|(WT_modeled=='delivery'))&
  #                       (source_modeled==c)].sum(axis=1)
  #
  #   for c in ['cvc', 'kings', 'kaweah', 'tule', 'kern', 'tableA', 'cvpdelta']:
  #     delivery_otherSW += district_modeled_aggregate_Wateryear.loc[:,
  #                        (districts_modeled == d) & ((WT_modeled == 'flood') | (WT_modeled=='flood_irrigation')| (WT_modeled == 'delivery')) &
  #                        (source_modeled == c)].sum(axis=1)
  #
  #   # lastly, recharge = in - (non-recharge-out)
  #   recharged = (delivery_friant + delivery_otherSW + pumping + water_banked_banker + water_recovered_bankee) - \
  #              (irrig + water_banked_bankee + water_recovered_banker)
  #
  #   #TODO figure out why ARV has negative recharge sometimes. for now hack fix by removing pumping, since not large amt water.
  #   error = recharged.copy()
  #   error.loc[error > -eps] = 0
  #   pumping += error
  #   recharged -= error
  #
  #   # now record data. need to fill in sources & uses in equal volumes to have one observation per alluvium for Sankey plot. Doesn't need to correspond to actual relationship between sources and uses.
  #   for y in district_modeled_aggregate_Wateryear.index:
  #     sources = [pumping.loc[y], water_recovered_bankee.loc[y], water_banked_banker.loc[y], delivery_otherSW.loc[y], delivery_friant.loc[y]]
  #     sources_names = ['Pumping', 'Recovery', 'Banked_in', 'OtherSW', 'Friant']
  #     uses = [water_recovered_banker.loc[y], water_banked_bankee.loc[y], recharged.loc[y], irrig.loc[y]]
  #     uses_names = ['Recovered_out', 'Banking', 'Recharge', 'Irrigation']
  #     s = 0
  #     u = 0
  #     while ((s < 5)&(u < 4)):
  #       if (abs(sources[s] - uses[u]) < eps):
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Source',
  #                         'Label': sources_names[s], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'District',
  #                         'Label': d, 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Use',
  #                         'Label': uses_names[u], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         sources[s] -= uses[u]
  #         uses[u] -= uses[u]
  #         s += 1
  #         u += 1
  #         counter += 1
  #       elif (sources[s] > uses[u]):
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Source',
  #                         'Label': sources_names[s], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'District',
  #                         'Label': d, 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Use',
  #                         'Label': uses_names[u], 'Volume': uses[u], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         sources[s] -= uses[u]
  #         uses[u] -= uses[u]
  #         u += 1
  #         counter += 1
  #       else:
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Source',
  #                         'Label': sources_names[s], 'Volume': sources[s], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'District',
  #                         'Label': d, 'Volume': sources[s], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         df_reorg = df_reorg.append(
  #           pd.DataFrame({'Wateryear': y, 'District': d, 'Axis': 'Use',
  #                         'Label': uses_names[u], 'Volume': sources[s], 'Obs': counter}, index=[0])).reset_index(drop=True)
  #         uses[u] -= sources[s]
  #         sources[s] -= sources[s]
  #         s += 1
  #         counter += 1
  #
  # df_reorg.Volume.loc[abs(df_reorg.Volume) < eps] = 0
  # df_reorg.to_csv('cord/data/results/'+folder+'/district_reorg.csv', index=False)



  ### now get monthly delivery types and revenues
  #TODO currently only set up for districts that dont have banking operations
  ID_land_assessment = {'LWT':35*85000, 'DLE':35*85000, 'SSJ':35*85000, 'SFW':35*85000}
  ID_volumetric_charge = {'LWT':65*1000, 'DLE':65*1000, 'SSJ':65*1000, 'SFW':65*1000}
  WB_volumetric_charge = {'ARV':{'banked':50*1000, 'recovered':100*1000}, 'RRB':{'banked':50*1000, 'recovered':100*1000}, 'NKB':{'banked':50*1000, 'recovered':100*1000}, 'POSO':{'banked':50*1000, 'recovered':100*1000},}
  SW_source_charge = {'friant1':{'delivery':28.79*1000, 'flood':0}, 'friant2':{'delivery':11.17*1000, 'flood':0},
                   'cvc':{'delivery':82.32*1000, 'flood':0}, 'cvpdelta':{'delivery':82.32*1000, 'flood':0},
                   'kings': {'delivery': 0, 'flood':0}, 'kaweah': {'delivery':0, 'flood':0},
                   'tule': {'delivery': 0, 'flood': 0}, 'kern': {'delivery': 0, 'flood': 0}}
  SW_sources = ['friant1', 'friant2', 'cvc', 'cvpdelta', 'kings', 'kaweah', 'tule', 'kern']
  banks = ['ARV','RRB','POSO','NKB']
  banks_type = ['leiu','leiu','bank','bank']
  for d in friant_districts:
    SW_volume_purchases[folder][d] = {}
    SW_volume_sales[folder][d] = {}
    bank_volume[folder][d] = {}
    SW_cash_purchases[folder][d] = {}
    SW_cash_sales[folder][d] = {}
    bank_cash[folder][d] = {}

    irrig = district_modeled_aggregate_Wateryear_Month.loc[:, (districts_modeled == d)&(source_modeled == 'irr')].sum(axis=1)
    pumping = district_modeled_aggregate_Wateryear_Month.loc[:,(districts_modeled==d)&(source_modeled=='pumping')].sum(axis=1)

    SW_volume_purchases[folder][d]['total'] = irrig * 0.0
    for s in SW_sources:
      # get SW purchases from each source
      SW_volume_purchases[folder][d][s] = {}
      SW_volume_purchases[folder][d][s]['delivery'] = district_modeled_aggregate_Wateryear_Month.loc[:, (districts_modeled == d)&(source_modeled == s)&(WT_modeled == 'delivery')].sum(axis=1)
      SW_volume_purchases[folder][d][s]['flood'] = district_modeled_aggregate_Wateryear_Month.loc[:, (districts_modeled == d)&(source_modeled == s)&((WT_modeled == 'flood')|(WT_modeled == 'flood_irrigation'))].sum(axis=1)
      SW_volume_purchases[folder][d]['total'] += SW_volume_purchases[folder][d][s]['delivery'] + SW_volume_purchases[folder][d][s]['flood']

    # get exchanged SW and exchanged GW & subtract from contract deliveries. assume comes from friant1, then friant2, cvc, cvpdelta, kern, tule, kaweah, kings. Then flood in same order.
    # exchanged_SW = district_modeled_aggregate_Wateryear.loc[:, (districts_modeled == d)&(WT_modeled == 'SW')].sum(axis=1)
    exchanged_GW = district_modeled_aggregate_Wateryear_Month.loc[:, (districts_modeled == d)&(WT_modeled == 'GW')].sum(axis=1)
    SW_volume_purchases[folder][d]['friant1']['delivery'] -= exchanged_GW
    if ((SW_volume_purchases[folder][d]['friant1']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['friant2']['delivery'].loc[(SW_volume_purchases[folder][d]['friant1']['delivery'] < -eps)] += SW_volume_purchases[folder][d]['friant1']['delivery'].loc[(SW_volume_purchases[folder][d]['friant1']['delivery'] < -eps)]
      SW_volume_purchases[folder][d]['friant1']['delivery'].loc[(SW_volume_purchases[folder][d]['friant1']['delivery'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['friant2']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['cvc']['delivery'].loc[(SW_volume_purchases[folder][d]['friant2']['delivery'] < -eps)] += SW_volume_purchases[folder][d]['friant2']['delivery'].loc[(SW_volume_purchases[folder][d]['friant2']['delivery'] < -eps)]
      SW_volume_purchases[folder][d]['friant2']['delivery'].loc[(SW_volume_purchases[folder][d]['friant2']['delivery'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['cvc']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['cvpdelta']['delivery'].loc[(SW_volume_purchases[folder][d]['cvc']['delivery'] < -eps)] += SW_volume_purchases[folder][d]['cvpdelta']['delivery'].loc[(SW_volume_purchases[folder][d]['cvpdelta']['delivery'] < -eps)]
      SW_volume_purchases[folder][d]['cvpdelta']['delivery'].loc[(SW_volume_purchases[folder][d]['cvpdelta']['delivery'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['cvpdelta']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['kern']['delivery'].loc[(SW_volume_purchases[folder][d]['cvpdelta']['delivery'] < -eps)] += SW_volume_purchases[folder][d]['kern']['delivery'].loc[(SW_volume_purchases[folder][d]['kern']['delivery'] < -eps)]
      SW_volume_purchases[folder][d]['kern']['delivery'].loc[(SW_volume_purchases[folder][d]['kern']['delivery'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['kern']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['tule']['delivery'].loc[(SW_volume_purchases[folder][d]['kern']['delivery'] < -eps)] += SW_volume_purchases[folder][d]['tule']['delivery'].loc[(SW_volume_purchases[folder][d]['tule']['delivery'] < -eps)]
      SW_volume_purchases[folder][d]['tule']['delivery'].loc[(SW_volume_purchases[folder][d]['tule']['delivery'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['tule']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['kaweah']['delivery'].loc[(SW_volume_purchases[folder][d]['tule']['delivery'] < -eps)] += SW_volume_purchases[folder][d]['kaweah']['delivery'].loc[(SW_volume_purchases[folder][d]['kaweah']['delivery'] < -eps)]
      SW_volume_purchases[folder][d]['kaweah']['delivery'].loc[(SW_volume_purchases[folder][d]['kaweah']['delivery'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['kaweah']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['kings']['delivery'].loc[(SW_volume_purchases[folder][d]['kaweah']['delivery'] < -eps)] += SW_volume_purchases[folder][d]['kings']['delivery'].loc[(SW_volume_purchases[folder][d]['kings']['delivery'] < -eps)]
      SW_volume_purchases[folder][d]['kings']['delivery'].loc[(SW_volume_purchases[folder][d]['kings']['delivery'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['kings']['delivery'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['friant1']['flood'].loc[(SW_volume_purchases[folder][d]['kings']['delivery'] < -eps)] += \
      SW_volume_purchases[folder][d]['friant1']['flood'].loc[(SW_volume_purchases[folder][d]['friant1']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['friant1']['flood'].loc[(SW_volume_purchases[folder][d]['friant1']['flood'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['friant1']['flood'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['friant2']['flood'].loc[(SW_volume_purchases[folder][d]['friant1']['flood'] < -eps)] += SW_volume_purchases[folder][d]['friant1']['flood'].loc[(SW_volume_purchases[folder][d]['friant1']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['friant1']['flood'].loc[(SW_volume_purchases[folder][d]['friant1']['flood'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['friant2']['flood'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['cvc']['flood'].loc[(SW_volume_purchases[folder][d]['friant2']['flood'] < -eps)] += SW_volume_purchases[folder][d]['friant2']['flood'].loc[(SW_volume_purchases[folder][d]['friant2']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['friant2']['flood'].loc[(SW_volume_purchases[folder][d]['friant2']['flood'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['cvc']['flood'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['cvpdelta']['flood'].loc[(SW_volume_purchases[folder][d]['cvc']['flood'] < -eps)] += SW_volume_purchases[folder][d]['cvpdelta']['flood'].loc[(SW_volume_purchases[folder][d]['cvpdelta']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['cvpdelta']['flood'].loc[(SW_volume_purchases[folder][d]['cvpdelta']['flood'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['cvpdelta']['flood'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['kern']['flood'].loc[(SW_volume_purchases[folder][d]['cvpdelta']['flood'] < -eps)] += SW_volume_purchases[folder][d]['kern']['flood'].loc[(SW_volume_purchases[folder][d]['kern']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['kern']['flood'].loc[(SW_volume_purchases[folder][d]['kern']['flood'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['kern']['flood'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['tule']['flood'].loc[(SW_volume_purchases[folder][d]['kern']['flood'] < -eps)] += SW_volume_purchases[folder][d]['tule']['flood'].loc[(SW_volume_purchases[folder][d]['tule']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['tule']['flood'].loc[(SW_volume_purchases[folder][d]['tule']['flood'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['tule']['flood'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['kaweah']['flood'].loc[(SW_volume_purchases[folder][d]['tule']['flood'] < -eps)] += SW_volume_purchases[folder][d]['kaweah']['flood'].loc[(SW_volume_purchases[folder][d]['kaweah']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['kaweah']['flood'].loc[(SW_volume_purchases[folder][d]['kaweah']['flood'] < -eps)] = 0.0
    if ((SW_volume_purchases[folder][d]['kaweah']['flood'] < -eps).sum() > 0):
      SW_volume_purchases[folder][d]['kings']['flood'].loc[(SW_volume_purchases[folder][d]['kaweah']['flood'] < -eps)] += SW_volume_purchases[folder][d]['kings']['flood'].loc[(SW_volume_purchases[folder][d]['kings']['flood'] < -eps)]
      SW_volume_purchases[folder][d]['kings']['flood'].loc[(SW_volume_purchases[folder][d]['kings']['flood'] < -eps)] = 0.0

    SW_volume_sales[folder][d] = irrig - pumping

    # get this district's leiu & banking, as bankee
    leiu_bankee = leiu_modeled_aggregate_Wateryear_Month.loc[:,(leiu_bankee_modeled==d)&(leiu_banker_modeled!=d)]
    if (leiu_bankee.shape[1] == 0):
      leiu_bankee = pd.DataFrame(irrig * 0.0)
    else:
      # undo haircuts for deposits, so we have full amount recharged
      for i,b in enumerate(leiu_banker_modeled[(leiu_bankee_modeled==d)&(leiu_banker_modeled!=d)]):
        leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] > 0] = leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] > 0] / leiu_haircuts[b]
    # store
    bank_volume[folder][d]['total'] = {'recovered':irrig*0.0, 'banked':irrig*0.0}
    for i, b in enumerate(leiu_banker_modeled[(leiu_bankee_modeled == d) & (leiu_banker_modeled != d)]):
      bank_volume[folder][d][b] = {}
      bank_volume[folder][d][b]['banked'] = irrig * 0.0
      bank_volume[folder][d][b]['recovered'] = irrig * 0.0
      bank_volume[folder][d][b]['banked'].loc[leiu_bankee.iloc[:,i] > eps] = leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] > eps]
      bank_volume[folder][d][b]['recovered'].loc[leiu_bankee.iloc[:,i] < -eps] = -leiu_bankee.iloc[:,i].loc[leiu_bankee.iloc[:,i] < -eps]
      bank_volume[folder][d]['total']['banked'] += bank_volume[folder][d][b]['banked']
      bank_volume[folder][d]['total']['recovered'] += bank_volume[folder][d][b]['recovered']

    # same for non-leiu banks
    bank_bankee = bank_modeled_aggregate_Wateryear_Month.loc[:, (bank_bankee_modeled == d) & (bank_banker_modeled != d)]
    if (bank_bankee.shape[1] == 0):
      bank_bankee = pd.DataFrame(irrig * 0.0)
    else:
      # undo haircuts for deposits, so we have full amount recharged
      for i, b in enumerate(bank_banker_modeled[(bank_bankee_modeled == d) & (bank_banker_modeled != d)]):
        bank_bankee.iloc[:, i].loc[bank_bankee.iloc[:, i] > 0] = bank_bankee.iloc[:, i].loc[
                                                                   bank_bankee.iloc[:, i] > 0] / bank_haircuts[b]
    # store
    for i, b in enumerate(bank_banker_modeled[(bank_bankee_modeled == d) & (bank_banker_modeled != d)]):
      bank_volume[folder][d][b] = {}
      bank_volume[folder][d][b]['banked'] = irrig * 0.0
      bank_volume[folder][d][b]['recovered'] = irrig * 0.0
      bank_volume[folder][d][b]['banked'].loc[bank_bankee.iloc[:, i] > eps] = bank_bankee.iloc[:, i].loc[
        bank_bankee.iloc[:, i] > eps]
      bank_volume[folder][d][b]['recovered'].loc[bank_bankee.iloc[:, i] < -eps] = -bank_bankee.iloc[:, i].loc[
        bank_bankee.iloc[:, i] < -eps]
      bank_volume[folder][d]['total']['banked'] += bank_volume[folder][d][b]['banked']
      bank_volume[folder][d]['total']['recovered'] += bank_volume[folder][d][b]['recovered']

  # now get revenues
    SW_cash_purchases[folder][d]['total'] = irrig * 0.0
    for s in SW_sources:
      # get SW purchases from each source
      SW_cash_purchases[folder][d][s] = {}
      SW_cash_purchases[folder][d][s]['delivery'] = SW_volume_purchases[folder][d][s]['delivery'] * SW_source_charge[s]['delivery']
      SW_cash_purchases[folder][d][s]['flood'] = SW_volume_purchases[folder][d][s]['flood'] * SW_source_charge[s]['flood']
      SW_cash_purchases[folder][d]['total'] += SW_cash_purchases[folder][d][s]['delivery'] + SW_cash_purchases[folder][d][s]['flood']

    SW_cash_sales[folder][d] = SW_volume_sales[folder][d] * ID_volumetric_charge[d]

    bank_cash[folder][d]['total'] = {'recovered':irrig*0.0, 'banked':irrig*0.0}
    for i, b in enumerate(leiu_banker_modeled[(leiu_bankee_modeled == d) & (leiu_banker_modeled != d)]):
      bank_cash[folder][d][b] = {}
      bank_cash[folder][d][b]['banked'] = bank_volume[folder][d][b]['banked'] * WB_volumetric_charge[b]['banked']
      bank_cash[folder][d][b]['recovered'] = bank_volume[folder][d][b]['recovered'] * WB_volumetric_charge[b][
        'recovered']
      bank_cash[folder][d]['total']['banked'] += bank_cash[folder][d][b]['banked']
      bank_cash[folder][d]['total']['recovered'] += bank_cash[folder][d][b]['recovered']
    for i, b in enumerate(bank_banker_modeled[(bank_bankee_modeled == d) & (bank_banker_modeled != d)]):
      bank_cash[folder][d][b] = {}
      bank_cash[folder][d][b]['banked'] = bank_volume[folder][d][b]['banked'] * WB_volumetric_charge[b]['banked']
      bank_cash[folder][d][b]['recovered'] = bank_volume[folder][d][b]['recovered'] * WB_volumetric_charge[b]['recovered']
      bank_cash[folder][d]['total']['banked'] += bank_cash[folder][d][b]['banked']
      bank_cash[folder][d]['total']['recovered'] += bank_cash[folder][d][b]['recovered']



### now convert these into annual volumes to plot
x = district_modeled_aggregate_Wateryear.Wateryear
x_months = district_modeled_aggregate_Wateryear_Month.Wateryear
ID_volume_purchases = {}
ID_volume_sales = {}
for folder in folders:
  ID_volume_purchases[folder] = {}
  ID_volume_sales[folder] = {}
  for d in friant_districts:
    ID_volume_purchases[folder][d] = SW_volume_purchases[folder][d]['total'].groupby(by=x_months).sum() +\
                                     bank_volume[folder][d]['total']['recovered'].groupby(by=x_months).sum()
    ID_volume_sales[folder][d] = SW_volume_sales[folder][d].groupby(by=x_months).sum()


### assumed costs for FKC rehab
project_cost_per_avg_delivery = [0, 25*1000,50*1000,75*1000,100*1000]
n_cost_scenario = len(project_cost_per_avg_delivery)
project_cost_share = ['friant1_contract','friant12_contract','friant_contract_avg','friant_contract_flood_avg','friant_contract_flood_local_flood_avg','exp_post_benefits']
n_share_scenario = len(project_cost_share)
friant_alloc = {'LWT':{'friant1':61.2,'friant2':238},'DLE':{'friant1':108,'friant2':74.5},'SSJ':{'friant1':97,'friant2':45},'SFW':{'friant1':50,'friant2':39.6}}
project_costs = {}
for share_scenario in range(n_share_scenario):
  project_costs[share_scenario] = {}
  for cost_scenario in range(n_cost_scenario):
    project_costs[share_scenario][cost_scenario] = {folders[0]:{}, folders[1]:{}}
    for folder in folders:
      for d in friant_districts:
        project_costs[share_scenario][cost_scenario][folders[0]][d] = 0
        if (share_scenario == 0):
          project_costs[share_scenario][cost_scenario][folders[1]][d] = friant_alloc[d]['friant1'] * project_cost_per_avg_delivery[cost_scenario]
        elif (share_scenario == 1):
          project_costs[share_scenario][cost_scenario][folders[1]][d] = (friant_alloc[d]['friant1'] + friant_alloc[d]['friant2']) * \
                                                                          project_cost_per_avg_delivery[cost_scenario]
        elif (share_scenario == 2):
          project_costs[share_scenario][cost_scenario][folders[1]][d] = (SW_volume_purchases[folders[0]][d]['friant1']['delivery'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['friant2']['delivery'].groupby(by=x_months).sum()).mean() * \
                                                                        project_cost_per_avg_delivery[cost_scenario]
        elif (share_scenario == 3):
          project_costs[share_scenario][cost_scenario][folders[1]][d] = (SW_volume_purchases[folders[0]][d]['friant1']['delivery'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['friant2']['delivery'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['friant1']['flood'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['friant2']['flood'].groupby(by=x_months).sum()).mean() * \
                                                                        project_cost_per_avg_delivery[cost_scenario]
        elif (share_scenario == 4):
          project_costs[share_scenario][cost_scenario][folders[1]][d] = (SW_volume_purchases[folders[0]][d]['friant1']['delivery'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['friant2']['delivery'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['friant1']['flood'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['friant2']['flood'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['kings']['flood'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['kaweah']['flood'].groupby(by=x_months).sum() +
                                                                         SW_volume_purchases[folders[0]][d]['tule']['flood'].groupby(by=x_months).sum()).mean() * \
                                                                        project_cost_per_avg_delivery[cost_scenario]
        elif (share_scenario == 5):
          project_costs[share_scenario][cost_scenario][folders[1]][d] = (ID_volume_purchases[folders[1]][d] - ID_volume_purchases[folders[0]][d]).mean() * \
                                                                        project_cost_per_avg_delivery[cost_scenario]

# rescale shares based on expected benefits metric, so that unit cost the same but shared differently
for cost_scenario in range(n_cost_scenario):
  folder = folders[1]
  for share_scenario in range(n_share_scenario-1):
    scaler = (project_costs[5][cost_scenario][folder]['LWT'] + project_costs[5][cost_scenario][folder]['DLE'] + \
              project_costs[5][cost_scenario][folder]['SSJ'] + \
              project_costs[5][cost_scenario][folder]['SFW']) / (
                     project_costs[share_scenario][cost_scenario][folder]['LWT'] + \
                     project_costs[share_scenario][cost_scenario][folder]['DLE'] + \
                     project_costs[share_scenario][cost_scenario][folder]['SSJ'] + \
                     project_costs[share_scenario][cost_scenario][folder]['SFW'])
    for d in friant_districts:
      project_costs[share_scenario][cost_scenario][folder][d] *= scaler

### net revenues under each scenario
ID_net_revenues = {}
for share_scenario in range(n_share_scenario):
  ID_net_revenues[share_scenario] = {}
  for cost_scenario in range(n_cost_scenario):
    ID_net_revenues[share_scenario][cost_scenario] = {}
    for folder in folders:
      ID_net_revenues[share_scenario][cost_scenario][folder] = {}
      for d in friant_districts:
        ID_net_revenues[share_scenario][cost_scenario][folder][d] = (ID_land_assessment[d] + SW_cash_sales[folder][d].groupby(by=x_months).sum() - \
                                      SW_cash_purchases[folder][d]['total'].groupby(by=x_months).sum() - \
                                      bank_cash[folder][d]['total']['recovered'].groupby(by=x_months).sum() - \
                                      bank_cash[folder][d]['total']['banked'].groupby(by=x_months).sum() -
                                      project_costs[share_scenario][cost_scenario][folder][d])/1e6


# ### plot stacked deliveries
# d = 'LWT'
# folder=folders[1]
# x = district_modeled_aggregate_Wateryear.Wateryear
# x_months = district_modeled_aggregate_Wateryear_Month.Wateryear
#
# y2 = SW_volume_purchases[folder][d]['total'].groupby(by=x_months).sum()
# plt.fill_between(x, 0, y2, alpha=0.7)
# y1 = y2
# y2 = y1 + bank_volume[folder][d]['total']['recovered'].groupby(by=x_months).sum()
# plt.fill_between(x, y1, y2, alpha=0.7)
# y1 = y2
# y2 = y1 + bank_volume[folder][d]['total']['banked'].groupby(by=x_months).sum()
# plt.fill_between(x, y1, y2, alpha=0.7)
# y1 = SW_volume_sales[folder][d].groupby(by=x_months).sum()
# plt.plot(x, y1, alpha=0.7)
#
# ### stacked revenue plot
# y1 = ID_land_assessment[d]
# plt.fill_between(x, 0, y1, alpha=0.7)
# y2 = y1 + SW_cash_sales[folder][d].groupby(by=x_months).sum()
# plt.fill_between(x, y1, y2, alpha=0.7)
# z1 = SW_cash_purchases[folder][d]['total'].groupby(by=x_months).sum()
# z2 = z1 + bank_cash[folder][d]['total']['recovered'].groupby(by=x_months).sum()
# plt.fill_between(x, 0, -z1, alpha=0.7)
# plt.fill_between(x, -z2, -z1, alpha=0.7)
# z1 = z2
# z2 = z1 + bank_cash[folder][d]['total']['banked'].groupby(by=x_months).sum()
# plt.fill_between(x, -z2, -z1, alpha=0.7)
# y1 = y2 - z2
# plt.plot(x, y1, alpha=0.7)


### plot pdf of total water deliveries vs revenue water
gs1 = gridspec.GridSpec(1,2)
ax = plt.subplot2grid((1,2), (0,0))
share_scenario = 5
cost_scenario = 0
ls = ['-','-']
shade = [True,True]
j = 0
i = 0
d = 'LWT'
y = ID_volume_purchases[folders[i]][d]
sns.kdeplot(y, color='0.3',ls=ls[i],shade=shade[i],kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 0
y = ID_volume_sales[folders[i]][d]
sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,800])
plt.ylim([0,0.0115])
plt.xlabel('Deliveries (tAF/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax = plt.subplot2grid((1,2), (0,1))
j = 2
i = 0
y = 0
for d in friant_districts[1:]:
  y += ID_volume_purchases[folders[i]][d]
sns.kdeplot(y, color='0.3', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 1
y = 0
for d in friant_districts[1:]:
  y += ID_volume_sales[folders[i]][d]
sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,800])
plt.ylim([0,0.0115])
plt.xlabel('Deliveries (tAF/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)




### plot changing pdf of total water deliveries
gs1 = gridspec.GridSpec(1,2)
ax = plt.subplot2grid((1,2), (0,0))
share_scenario = 5
cost_scenario = 0
ls = ['-','-']
shade = [True,True]
j = 0
i = 0
d = 'LWT'
y = ID_volume_purchases[folders[i]][d]
sns.kdeplot(y, color='0.3',ls=ls[i],shade=shade[i],kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 1
y = ID_volume_purchases[folders[i]][d]
# sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
# plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,800])
plt.ylim([0,0.0115])
plt.xlabel('Total deliveries (tAF/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax = plt.subplot2grid((1,2), (0,1))
j = 2
i = 0
y = 0
for d in friant_districts[1:]:
  y += ID_volume_purchases[folders[i]][d]
sns.kdeplot(y, color='0.3', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 1
y = 0
for d in friant_districts[1:]:
  y += ID_volume_purchases[folders[i]][d]
sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,800])
plt.ylim([0,0.0115])
plt.xlabel('Total deliveries (tAF/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)




### plot changing pdf of total water sales (revenue-generating water)
gs1 = gridspec.GridSpec(1,2)
ax = plt.subplot2grid((1,2), (0,0))
share_scenario = 5
cost_scenario = 0
ls = ['-','-']
shade = [True,True]
j = 0
i = 0
d = 'LWT'
y = ID_volume_sales[folders[i]][d]
sns.kdeplot(y, color='0.3',ls=ls[i],shade=shade[i],kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 1
y = ID_volume_sales[folders[i]][d]
sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,350])
plt.ylim([0,0.0105])
plt.xlabel('Revenue-generating deliveries (tAF/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax = plt.subplot2grid((1,2), (0,1))
j = 2
i = 0
y = 0
for d in friant_districts[1:]:
  y += ID_volume_sales[folders[i]][d]
sns.kdeplot(y, color='0.3', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 1
y = 0
for d in friant_districts[1:]:
  y += ID_volume_sales[folders[i]][d]
sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
# plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,350])
plt.ylim([0,0.0105])
plt.xlabel('Revenue-generating deliveries (tAF/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)




### plot changing pdf of total net revenues
# cols_districts = [cmap(i) for i in np.arange(0.1,1,0.9/turnout_aggregate_Wateryear1.shape[1])]
# fig = plt.figure(figsize=(18, 9))
gs1 = gridspec.GridSpec(1,2)
ax = plt.subplot2grid((1,2), (0,0))
share_scenario = 5
cost_scenario = 3
ls = ['-','-']
shade = [True,True]
j = 0
i = 0
d = 'LWT'
y = ID_net_revenues[share_scenario][cost_scenario][folders[i]][d]
sns.kdeplot(y, color='0.3',ls=ls[i],shade=shade[i],kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 1
y = ID_net_revenues[share_scenario][cost_scenario][folders[i]][d]
sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,25])
plt.ylim([0,0.19])
plt.xlabel('Net Revenues ($M/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)
ax = plt.subplot2grid((1,2), (0,1))
j = 2
i = 0
y = 0
for d in friant_districts[1:]:
  y += ID_net_revenues[share_scenario][cost_scenario][folders[i]][d]
sns.kdeplot(y, color='0.3', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='0.3',lw=2)
plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='0.3',lw=2,ls='--')
i = 1
y = 0
for d in friant_districts[1:]:
  y += ID_net_revenues[share_scenario][cost_scenario][folders[i]][d]
sns.kdeplot(y, color='indianred', ls=ls[i],shade=shade[i], kernel='epa',lw=0)
plt.axvline(y.mean(),color='indianred',ls=ls[i],lw=2)
plt.axvline(y.loc[y<y.quantile(0.05)].mean(),color='indianred',lw=2,ls='--')
plt.xlim([0,25])
plt.ylim([0,0.19])
plt.xlabel('Net Revenues ($M/yr)')
plt.ylabel('Density')
plt.tick_params(axis='y', which='both', labelleft=False, labelright=False)




### plot revenue time series
share_scenario = 5
cost_scenario = 0
ls = ['-','-']
shade = [True,True]
j = 0
i = 0
d = 'LWT'
y = ID_net_revenues[share_scenario][cost_scenario][folders[i]][d]
plt.plot(x,y*1000, color=cols[0], lw=3)
plt.axhline(y.mean(), color=cols[0], lw=3, ls='--')
plt.ylim([0,18])
plt.xlabel('Year')
plt.ylabel('Revenue ($M)')



### scatter plot of effect of share_scenario & cost_scenario
rev_diff_stats = {'mean':{}, 'mean_c5':{}}
for d in friant_districts:
  rev_diff_stats['mean'][d] = np.array([])
  rev_diff_stats['mean_c5'][d] = np.array([])
  for share_scenario in range(n_share_scenario):
    for cost_scenario in [3]:
      rev_diff = ID_net_revenues[share_scenario][cost_scenario][folders[1]][d] - ID_net_revenues[share_scenario][cost_scenario][folders[0]][d]
      rev_diff_c5 = rev_diff[rev_diff < np.quantile(rev_diff, 0.05)]
      rev_diff_stats['mean'][d] = np.append(rev_diff.mean(), rev_diff_stats['mean'][d])
      rev_diff_stats['mean_c5'][d] = np.append(rev_diff_c5.mean(), rev_diff_stats['mean_c5'][d])

for i,d in enumerate(friant_districts):
  plt.scatter(rev_diff_stats['mean'][d], rev_diff_stats['mean_c5'][d], color=cols[i], s=80, alpha=0.8)
plt.xlabel('Change in E[revenue] ($M/yr)')
plt.ylabel('Change in E[revenue | revenue < Q5] ($M/yr)')


