from __future__ import division
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns 
sns.set_style('whitegrid')

# historical data from DWR Dayflow
taf_cfs = 1000 / 86400 * 43560
df = pd.read_csv('data-clean.csv', index_col=0, parse_dates=True)#.resample('AS-OCT', how='sum')

# salinity requirements

# this isn't perfect, see other file for model
def salinity_flow_requirement(site, St, t):
  if St is not None:
    params = salinity_params_weekly[site]
    So = 10**params[0]
    Sb = 10**params[1]
    alpha = 10**params[2]
    w = int(params[3])
    Qt = (w/alpha) * np.log((So-Sb)/(St*1000-Sb)) - df.outflow.values[(t-w+1):t].sum()
    Qt /= 4 # target to fix within a month (don't pulse in a single week)
    if Qt < 0: 
      Qt = None # not binding
  else:
    Qt = None # not binding
  return Qt


# Physical Capacity Constraints
# https://www.usbr.gov/mp/nepa/documentShow.cfm?Doc_ID=19490
# banks + tracy (mean daily cfs)
# plus extra 500 cfs july-sept. from EWA (only when habitat outflow constraint is binding)
# banks = [8500, 8500, 7590, 6680, 6680, 6680, 7180, 7180, 7180, 6680, 6680, 7590]
# capacity = np.array(banks) + 4600 # add tracy

# df['pump_capacity'] = pd.Series([capacity[m-1] for m in df.index.month], index=df.index)

# legally Banks+Tracy cannot exceed 1500 cfs from Apr 15 - May 15
ix = ((df.index.month==4) & (df.index.day >= 15)) | ((df.index.month==5) & (df.index.day <= 15))
df.pump_capacity[ix] = 1500

# Export-inflow ratio constraints
# pct = [0.65, 0.35, 0.35, 0.35, 0.35, 0.35, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65]
# df['export_ratio_constraint'] = df.inflow * np.array([pct[m-1] for m in df.index.month])
# df['outflow_ratio_constraint'] = df.inflow * (1 - np.array([pct[m-1] for m in df.index.month]))

# January 8RI changes February export ratio constraint
# DONE (sorta)
# ix = (df.index.month==2) & (df.jan8RI < 1)
# df[ix].export_ratio_constraint = df.inflow[ix] * 0.45
# df[ix].outflow_ratio_constraint = df.inflow[ix] * 0.55

# ix = (df.index.month==2) & (df.jan8RI > 1) & (df.jan8RI < 1.5)
# df[ix].export_ratio_constraint = df.inflow[ix] * 0.40
# df[ix].outflow_ratio_constraint = df.inflow[ix] * 0.60

# find required flow Qt to meet salinity targets St
for k in St.keys():
  df['St_' + k] = pd.Series([St[k][df.wyt[i]][i.month-1] for i in df.index], index=df.index)
  Qt = [salinity_flow_requirement(k, St[k][df.wyt[i]][i.month-1], t) for t,i in enumerate(df.index)]
  df['Qt_' + k] = pd.Series(Qt, index=df.index)

# Minimum Delta outflow requirements (depends on water year and month)
df['min_delta_outflow'] = pd.Series()

# Jan: if 8RI < 800 TAF in previous December: 4500 cfs, else 6000 cfs
# DONE (sorta)
# df[df.index.month==1].min_delta_outflow = 6000
# df[(df.index.month==1) & (df.dec8RI < 0.8)].min_delta_outflow = 4500

# Feb: 7100 cfs or EC_collins < 2.64
# Mar: same
# Apr: same
# May: same (unless SRI forecast < 8.1 MAF at 90% exceedance, then 4000 cfs)
# June: same (unless SRI forecast < 8.1 MAF at 90% exceedance, then 4000 cfs)
# DONE (sorta, not including salinity)
# df[df.Qt_collinsville > 7100].Qt_collinsville = 7100
# ix = ((df.index.month==5) | (df.index.month==6)) & (df.maySRI < 8.1) & (df.Qt_collinsville > 4000)
# df[ix].Qt_collinsville = 4000

# July: 8000 cfs in a 'W' or 'AN' year; 6500 in 'BN'; 5000 in 'D'; 4000 in 'C'
# August: 4000 in W/AN/BN; 3500 in D, 3000 in C
# Sept: 3000 cfs 
# Oct: 4000 in W/AN/BN/D; 3000 in C
# Nov: 4500 in W/AN/BN/D; 3500 in C
# Dec: same as Nov
# DONE
# temp = {7: {'W': 8000, 'AN': 8000, 'BN': 6500, 'D': 5000, 'C': 4000},
#         8: {'W': 4000, 'AN': 4000, 'BN': 4000, 'D': 3500, 'C': 3000},
#         9: {'W': 3000, 'AN': 3000, 'BN': 3000, 'D': 3000, 'C': 3000},
#         10: {'W': 4000, 'AN': 4000, 'BN': 4000, 'D': 4000, 'C': 3000},
#         11: {'W': 4500, 'AN': 4500, 'BN': 4500, 'D': 4500, 'C': 4500},
#         12: {'W': 4500, 'AN': 4500, 'BN': 4500, 'D': 4500, 'C': 4500}}

# ix = (df.index.month >= 7) & (df.index.month <= 12)
# df.ix[ix, 'min_delta_outflow'] = [temp[i.month][df.wyt[i]] for i in df[ix].index]

# plot export requirements
export_constraints = ['pump_capacity', 'export_ratio_constraint']
df['export_constraint'] = df[export_constraints].min(axis=1)

outflow_constraints = ['outflow_ratio_constraint',
                       'Qt_collinsville',
                       'Qt_jerseypoint',
                       'Qt_emmaton',
                       'min_delta_outflow']

df['outflow_constraint'] = df[outflow_constraints].max(axis=1)

df['available_water'] = df.inflow - df.gcd - df.outflow_constraint
df['available_outflows'] = df.inflow - df.gcd - df.export_constraint

df['export_pred'] = df[['available_water', 'export_constraint']].min(axis=1)
df.export_pred[df.export_pred < 0] = 0

df['outflow_pred'] = df[['available_outflows', 'outflow_constraint']].max(axis=1)


# df = df.resample('A').mean()
# df[['outflow', 'outflow_constraint', 'outflow_pred', 
#     'exports', 'export_constraint', 'export_pred', 'inflow']].to_csv('data-for-HB-monthly.csv')

df = df['2000':]
# how good is the prediction?
# df.plot(kind='scatter', x='export_pred', y='exports', s=50)
# plt.show()

# other stuff..........

# plt.subplot(4,1,1)
# df.exports.plot(color='indianred')
# df.export_pred.plot(color='blue')
# plt.ylabel('Exports (Mean Daily cfs)')
# plt.legend(['Actual', 'Predicted'])

# plt.subplot(4,1,2)
# df.exports.plot(color='indianred')
# df.export_constraint.plot(color='k')
# plt.ylabel('Exports (Mean Daily cfs)')
# plt.legend(['Actual', 'Maximum Allowed'])

# plt.subplot(4,1,3)
# df.outflow.plot(color='indianred')
# df.outflow_pred.plot(color='blue')
# plt.ylabel('Outflows (Mean Daily cfs)')
# plt.legend(['Actual', 'Predicted'])

# plt.subplot(4,1,4)
# df.outflow.plot(color='indianred')
# df.outflow_constraint.plot(color='k')
# plt.ylabel('Exports (Mean Daily cfs)')
# plt.legend(['Actual', 'Maximum Allowed'])


# # other stuff................

# plot outflow requirements
# plt.subplot(5,1,2)
# df.outflow.plot(color='indianred')
# df.outflow_constraint.plot(color='k')
# plt.ylabel('Outflow (Mean Daily cfs)')
# plt.legend(['Actual', 'Minimum Allowed'])

# for i,k in enumerate(St.keys()):
#   plt.subplot(5,1,i+3)
#   df['EC_%s' % k].plot(color='indianred')
#   df['St_%s' % k].plot(color='k')
#   plt.ylabel('Salinity @ %s (mS/cm)' % k)
#   plt.legend(['Actual', 'Maximum Allowed'])


# other stuff...................
plt.subplot(2,1,1)
ax = df.outflow.plot(color='k')
df[outflow_constraints].plot(ax=ax)

plt.subplot(2,1,2)
ax = df.exports.plot(color='k')
df[export_constraints].plot(ax=ax)




plt.show()



