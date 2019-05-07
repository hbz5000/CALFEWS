import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import cm
import importlib
import cord.postprocess.load_model_data as load_model_data
from pysankey import sankey

cmap = cm.get_cmap('viridis')
cols = [cmap(0.1),cmap(0.3),cmap(0.6),cmap(0.8)]
cfs_tafd = 2.29568411*10**-5 * 86400 / 1000
tafd_cfs = 1000 / 86400 * 43560

### load canal data
importlib.reload(load_model_data)
canal1, canal_aggregate_Wateryear1, canal_aggregate_Wateryear_Month1, ind_canal_waterway1, ind_canal_recipient1, ind_canal_flowtype1 = \
            load_model_data.load_canal_data('cord/data/results/FKC_capacity_wy2017_new/canal_results_simulation.csv')

folder_name = 'FKC_capacity_wy2017'
os.makedirs('cord/figs/flowDiagrams/' + folder_name, exist_ok=True)

# get median, wettest & dryest years
tot_flow = canal_aggregate_Wateryear1.FKC_COF_flow #/ 365*tafd_cfs
flow_order = np.argsort(canal_aggregate_Wateryear1.FKC_COF_flow)
# plt.hist(tot_flow.iloc[:,0])
wyMedian = np.where(tot_flow == np.median(tot_flow))[0]
wyMax = np.where(tot_flow == np.max(tot_flow))[0]
wyMin = np.where(tot_flow == np.min(tot_flow))[0]

# only keep FKC, turnout. remove rivers, MIL
turnout_aggregate_Wateryear1 = canal_aggregate_Wateryear1.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'turnout')) & ~((ind_canal_recipient1 == 'MIL') | (ind_canal_recipient1 == 'KGR') | (ind_canal_recipient1 == 'KWR') | (ind_canal_recipient1 == 'TLR'))]
ind_turnout_flowtype1 = turnout_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[2])
ind_turnout_waterway1 = turnout_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[0])
ind_turnout_recipient1 = turnout_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[1])
# only keep FKC, flow. remove MIL
flow_aggregate_Wateryear1 = canal_aggregate_Wateryear1.loc[:, ((ind_canal_waterway1 == 'FKC') & (ind_canal_flowtype1 == 'flow')) & ~(ind_canal_recipient1 == 'MIL') ]
ind_flow_flowtype1 = flow_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[2])
ind_flow_waterway1 = flow_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[0])
ind_flow_recipient1 = flow_aggregate_Wateryear1.columns.map(lambda x: x.split('_')[1])
del canal1, canal_aggregate_Wateryear1,ind_canal_recipient1,ind_canal_flowtype1,ind_canal_waterway1



# # plot flow along canal nodes
# cols_flow = [cmap(i) for i in np.arange(0.1,0.9,0.8/flow_aggregate_Wateryear1.shape[0])]
# for y in range(flow_aggregate_Wateryear1.shape[0]):
#   plt.plot(np.arange(len(ind_flow_recipient1)), flow_aggregate_Wateryear1.iloc[y,:], c=cols_flow[y], alpha=0.7)
#   plt.xticks(np.arange(len(ind_flow_recipient1)), ind_flow_recipient1, rotation=90)
# plt.xlabel('Node for FKC inflow')
# plt.ylabel('Wateryear flow (taf)')




# ### stacked deliveries
# sort_x = True
# # screen_districts = ['LWT','KRT']
# screen_districts = False
# order_by_diversion = False
# cols_districts = [cmap(i) for i in np.arange(0.1,1,0.9/turnout_aggregate_Wateryear1.shape[1])]
# # screen for particular districts
# if (screen_districts):
#   ind_district = [d in screen_districts for d in ind_turnout_recipient1]
# else:
#   ind_district = [d in ind_turnout_recipient1 for d in ind_turnout_recipient1]
# # get x-axis
# if (sort_x):
#   x = tot_flow.iloc[flow_order]
# else:
#   x = turnout_aggregate_Wateryear1.index
# # order stack by north-south or by max diversion level
# if (order_by_diversion):
#   max_div = turnout_aggregate_Wateryear1.max(axis=0)
#   turnout_aggregate_Wateryear1_stacked = turnout_aggregate_Wateryear1.iloc[:,np.argsort(max_div)]
#   # turnout_aggregate_Wateryear1_stacked = turnout_aggregate_Wateryear1_stacked[turnout_aggregate_Wateryear1_stacked.columns[::-1]]
#   if (screen_districts):
#     ind_district = [d in screen_districts for d in ind_turnout_recipient1[np.argsort(max_div)][::-1]]
# else:
#   turnout_aggregate_Wateryear1_stacked = turnout_aggregate_Wateryear1[turnout_aggregate_Wateryear1.columns[::-1]]
# if (ind_district[-1]):
#   plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[flow_order, 0], color=cols_districts[0], alpha=0.7)
# else:
#   plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[flow_order, 0], color='0.8', alpha=0.7)
# for i in range(1, turnout_aggregate_Wateryear1.shape[1]):
#   turnout_aggregate_Wateryear1_stacked.iloc[:,i] = turnout_aggregate_Wateryear1_stacked.iloc[:,i] + turnout_aggregate_Wateryear1_stacked.iloc[:,i-1]
#   if (ind_district[-(i+1)]):
#     plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[flow_order,i],
#                      turnout_aggregate_Wateryear1_stacked.iloc[flow_order,i-1], color=cols_districts[i], alpha=0.7)
#   else:
#     plt.fill_between(x, turnout_aggregate_Wateryear1_stacked.iloc[flow_order, i],
#                      turnout_aggregate_Wateryear1_stacked.iloc[flow_order, i - 1], color='0.8', alpha=0.7)
# plt.legend(ind_turnout_recipient1[::-1])
# plt.xlabel('Flow into COF (taf/yr)')
# plt.ylabel('Cumulative turnout flow (taf/yr)')

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
importlib.reload(load_model_data)
district_modeled_aggregate_Wateryear, friant_districts, source_modeled, districts_modeled, WT_modeled = \
  load_model_data.load_district_data('cord/data/results/FKC_capacity_wy2017_new/district_results_full_simulation.csv')

leiu_modeled_aggregate_wateryear, leiu_banker_modeled, leiu_bankee_modeled = \
  load_model_data.load_leiu_data('cord/data/results/FKC_capacity_wy2017_new/leiu_results_simulation.csv')

bank_modeled_aggregate_wateryear, bank_banker_modeled, bank_bankee_modeled = \
  load_model_data.load_bank_data('cord/data/results/FKC_capacity_wy2017_new/bank_results_simulation.csv')


df_reorg = pd.DataFrame({'Wateryear':[],'district':[],'source':[],'destination':[],'volume':[]})
for d in friant_districts:
  leiu = leiu_modeled_aggregate_wateryear.loc[:,(leiu_bankee_modeled==d)]
  bank = bank_modeled_aggregate_wateryear.loc[:,(bank_bankee_modeled==d)]
  if ((leiu.shape[1] > 0) & (bank.shape[1] > 0)):
    recharge_offDistrict = leiu.iloc[:,0] * 0.0
    recovery = leiu.iloc[:,0] * 0.0
    for y in leiu.index:
      recharge_offDistrict.loc[y] = leiu.loc[y, leiu.loc[y,:] > 0].sum() + bank.loc[y, bank.loc[y,:] > 0].sum()
      recovery.loc[y] = -(leiu.loc[y, leiu.loc[y,:] < 0].sum() + bank.loc[y, bank.loc[y,:] < 0].sum())
  elif ((leiu.shape[1] > 0)):
    recharge_offDistrict = leiu.iloc[:,0] * 0.0
    recovery = leiu.iloc[:,0] * 0.0
    for y in leiu.index:
      recharge_offDistrict.loc[y] = leiu.loc[y, leiu.loc[y,:] > 0].sum()
      recovery.loc[y] = -(leiu.loc[y, leiu.loc[y,:] < 0].sum())
  elif ((bank.shape[1] > 0)):
    recharge_offDistrict = bank.iloc[:,0] * 0.0
    recovery = bank.iloc[:,0] * 0.0
    for y in bank.index:
      recharge_offDistrict.loc[y] = bank.loc[y, bank.loc[y,:] > 0].sum()
      recovery.loc[y] = -(bank.loc[y, bank.loc[y,:] < 0].sum())
  else:
    recharge_offDistrict = leiu_modeled_aggregate_wateryear.iloc[:,0] * 0.0
    recovery = leiu_modeled_aggregate_wateryear.iloc[:,0] * 0.0
  if (recovery.sum() > 1e-13):
    df_reorg = df_reorg.append(
      pd.DataFrame({'Wateryear': district_modeled_aggregate_Wateryear.index, 'district': d, 'source': 'recovery',
                    'volume': recovery, 'destination': 'irrigation'}))
  else:
    df_reorg = df_reorg.append(
      pd.DataFrame({'Wateryear': district_modeled_aggregate_Wateryear.index, 'district': d, 'source': 'recovery',
                    'volume': 0, 'destination': 'irrigation'}))
  pumping = district_modeled_aggregate_Wateryear.loc[:,(districts_modeled==d)&(source_modeled=='pumping')].sum(axis=1)
  if (pumping.sum() > 1e-13):
    df_reorg = df_reorg.append(
      pd.DataFrame({'Wateryear': district_modeled_aggregate_Wateryear.index, 'district': d, 'source': 'pumping',
                    'volume': pumping, 'destination': 'irrigation'}))
  else:
    df_reorg = df_reorg.append(
      pd.DataFrame({'Wateryear': district_modeled_aggregate_Wateryear.index, 'district': d, 'source': 'pumping',
                    'volume': 0, 'destination': 'irrigation'}))
  for c in ['cvc','friant1','friant2','kings','kaweah','tule','kern','tableA','cvpdelta']:
    delivery = district_modeled_aggregate_Wateryear.loc[:,(districts_modeled==d)&((WT_modeled=='delivery'))&(source_modeled==c)].sum(axis=1)
    recharge = district_modeled_aggregate_Wateryear.loc[:,(districts_modeled==d)&((WT_modeled=='flood')|((WT_modeled=='recharged')&(source_modeled!='recharged')))&(source_modeled==c)].sum(axis=1)
    if (recharge.sum() > 1e-13):
      recharge_offDistrict_c = np.minimum(recharge_offDistrict, recharge)
      delivery = delivery - recharge
      recharge_offDistrict -= recharge_offDistrict_c
      recharge_onDistrict_c = recharge - recharge_offDistrict_c
    if (delivery.sum() > 1e-13):
      df_reorg = df_reorg.append(pd.DataFrame({'Wateryear':district_modeled_aggregate_Wateryear.index, 'district':d, 'source':c,
                                               'volume':delivery, 'destination':'irrigation'}))
    else:
      df_reorg = df_reorg.append(pd.DataFrame({'Wateryear':district_modeled_aggregate_Wateryear.index, 'district':d, 'source':c,
                                               'volume':0, 'destination':'irrigation'}))
    if (recharge.sum() > 1e-13):
      df_reorg = df_reorg.append(pd.DataFrame({'Wateryear':district_modeled_aggregate_Wateryear.index, 'district':d, 'source':c,
                                               'volume':recharge_onDistrict_c, 'destination':'recharge'}))
    else:
      df_reorg = df_reorg.append(pd.DataFrame({'Wateryear':district_modeled_aggregate_Wateryear.index, 'district':d, 'source':c,
                                               'volume':0, 'destination':'recharge'}))
    if (recharge.sum() > 1e-13):
      df_reorg = df_reorg.append(pd.DataFrame({'Wateryear':district_modeled_aggregate_Wateryear.index, 'district':d, 'source':c,
                                               'volume':recharge_offDistrict_c, 'destination':'bank'}))
    else:
      df_reorg = df_reorg.append(pd.DataFrame({'Wateryear':district_modeled_aggregate_Wateryear.index, 'district':d, 'source':c,
                                               'volume':0, 'destination':'bank'}))
df_reorg.to_csv('C:/Users/Andrew/Desktop/district_reorg.csv', index=False)
