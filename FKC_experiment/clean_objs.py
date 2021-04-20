import numpy as np
import pandas as pd
import sys

results = sys.argv[1]

## get data & organize diff experiments
objs = pd.read_csv(results + 'objs_all.csv')
print(objs.shape)
objs = objs.loc[objs['scenario'].notnull(), :]
objs.columns = [s.strip() for s in objs.columns]
print(objs.shape)
objs['hydro'] = [s.split('_')[4] for s in objs.scenario]
objs['samp'] = '' #[s.split('_')[5] for s in objs.scenario]
objs['project'] = '' #[s.split('_', 6)[6] for s in objs.scenario]
for i in range(objs.shape[0]):
  try:
    objs['samp'].iloc[i] = objs.scenario.iloc[i].split('_')[5]
  except:
    objs['samp'].iloc[i] = '-1'
  try:
    objs['project'].iloc[i] = objs.scenario.iloc[i].split('_', 6)[6]
  except:
    objs['project'].iloc[i] = 'FKC'



objs.sort_values(['samp','project','hydro'], inplace=True)
objs.reset_index(inplace=True, drop=True)
print(objs.shape)
print(objs.head())
### FKC-only experiments don't have correct ownership shares in objs_all.csv
#objs_FKC = objs.loc[objs.project == 'FKC']
#for i in range(objs_FKC.shape[0]):
#    samp = objs_FKC.iloc[i].samp
#    hydro = objs_FKC.iloc[i].hydro
#    b1 = np.logical_and(np.logical_and(objs.samp == samp, objs.hydro == hydro), objs.project == 'FKC')
#    b2 = np.logical_and(np.logical_and(objs.samp == samp, objs.hydro == hydro), objs.project == 'FKC_CFWB')
#    objs.loc[b1, objs.columns[12:-3]] = objs.loc[b2, objs.columns[12:-3]].values

### if gini coef >1 or <0, indicates weirdness with negative returns. set to 1.
#objs.ginicoef = np.minimum(objs.ginicoef, 1.0)
#objs.ginicoef = [1.0 if g < 0.0 else g for g in objs.ginicoef]

### get avg price of water gains per year
principle = {'FKC': 300e6, 'CFWB': 50e6, 'FKC_CFWB': 350e6}
payments_per_yr = 1
interest_rt = 0.05 / payments_per_yr
num_payments = 50 * payments_per_yr
annual_payment = {k: principle[k] / (((1 + interest_rt) ** num_payments - 1) / (interest_rt * (1 + interest_rt) ** num_payments)) for k in principle}
#objs['total_partner_avg_gain'] = objs['avg_partner_avg_gain'] * objs['num_partners']
#objs['total_other_avg_gain'] = objs['avg_other_avg_gain'] * (41 - objs['num_partners'])
#objs['total_total_avg_gain'] = objs['total_partner_avg_gain'] + objs['total_other_avg_gain']
objs['avg_price_gain_dolAF'] = [annual_payment[objs.project.iloc[i]] / objs['total_partner_avg_gain'].iloc[i] / 1000 for i in range(objs.shape[0])]

# negative prices indicate negative benefits. set these, plus those over $3000/AF, to $3000/AF
objs.avg_price_gain_dolAF.loc[objs.avg_price_gain_dolAF < 0.0] = 3000.
objs.avg_price_gain_dolAF.loc[objs.avg_price_gain_dolAF > 3000.0] = 3000.

## output
objs.to_csv(results + 'objs_clean.csv', index=False)

## aggregate across hydrology, taking worst case for each project/sample combo
objs_aggHydro = objs.groupby(['samp','project']).min().reset_index()
for o in ['ginicoef', 'avg_price_gain_dolAF']:
    objs_aggHydro.loc[:, o] = objs.groupby(['samp','project']).max().reset_index().loc[:, o]

## output
objs_aggHydro.to_csv(results + 'objs_aggHydro.csv', index=False)

