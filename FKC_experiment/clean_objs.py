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

### get avg price of water gains per year
FKC_cost = 500e6
FKC_fed_payment = 200e6
FKC_east_tule_payment = 125e6
FKC_participant_payment = FKC_cost - FKC_fed_payment - FKC_east_tule_payment
CFWB_cost = 100e6
interest_annual = 0.03
time_horizon = 50

principle = {'FKC': FKC_participant_payment, 'CFWB': CFWB_cost, 'FKC_CFWB': FKC_participant_payment + CFWB_cost}
payments_per_yr = 1
interest_rt = interest_annual / payments_per_yr
num_payments = time_horizon * payments_per_yr
annual_payment = {k: principle[k] / (((1 + interest_rt) ** num_payments - 1) / (interest_rt * (1 + interest_rt) ** num_payments)) for k in principle}
objs['avg_price_gain_dolAF'] = [annual_payment[objs.project.iloc[i]] / objs['total_partner_avg_gain'].iloc[i] / 1000 for i in range(objs.shape[0])]

# negative prices indicate negative benefits. set these, plus those over $3000/AF, to $3000/AF
objs.avg_price_gain_dolAF.loc[objs.avg_price_gain_dolAF < 0.0] = 3000.
objs.avg_price_gain_dolAF.loc[objs.avg_price_gain_dolAF > 3000.0] = 3000.

## output
objs.to_csv(results + 'objs_clean.csv', index=False)


### get median-hydrology only set
objs_medHydro = objs.loc[objs.hydro == 'median', :]
## output
objs_medHydro.to_csv(results + 'objs_medHydro.csv', index=False)

### aggregate across hydrology, taking worst case for each project/sample combo
objs_aggHydro = objs.groupby(['samp','project']).min().reset_index()
for o in ['ginicoef', 'avg_price_gain_dolAF']:
    objs_aggHydro.loc[:, o] = objs.groupby(['samp','project']).max().reset_index().loc[:, o]

## output
objs_aggHydro.to_csv(results + 'objs_aggHydro.csv', index=False)

