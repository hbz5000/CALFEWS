import numpy as np
import pandas as pd
# import h5py
import json
import sys
import matplotlib.pyplot as plt
from calfews_src.util import get_results_sensitivity_number_outside_model

hydrology = sys.argv[1] #wet,dry, or median
sample = sys.argv[2]  #0-2999
project = sys.argv[3] #FKC_CFWB, FKC, CFWB

scenario = 'FKC_experiment_capow_50yr_'+ hydrology + '_' + sample + '_' + project
baseline = 'FKC_experiment_capow_50yr_' + hydrology + '_none'

### get ownership shares for each scenario
base_dir = '/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'
shares = {}
shares['ownership'] = json.load(open(base_dir + scenario + '/FKC_scenario.json'))['ownership_shares']
shares_CFWB = json.load(open(base_dir + scenario + '/CFWB_scenario.json'))

for k in shares['ownership']:
  try:
    shares['ownership'][k] = max(shares['ownership'][k], shares_CFWB['ownership'][k])
  except:
    pass
shares['initial_recharge'] = shares_CFWB['initial_recharge']
shares['tot_storage'] = shares_CFWB['tot_storage']
shares['recovery'] = shares_CFWB['recovery']

district_lookup = { 'BDM': 'berrenda', 'BLR': 'belridge', 'BVA': 'buenavista', 'CWO': 'cawelo', 'HML': 'henrymiller', 'ID4': 'ID4', 'KND': 'kerndelta', 
                    'LHL': 'losthills', 'RRB': 'rosedale', 'SMI': 'semitropic', 'THC': 'tehachapi', 'TJC': 'tejon', 'WKN': 'westkern', 'WRM': 'wheeler', 
                    'KCWA': 'kcwa', 'COB': 'bakersfield', 'NKN': 'northkern', 'ARV': 'arvin', 'PIX': 'pixley', 'DLE': 'delano', 'EXE': 'exeter', 
                    'KRT': 'kerntulare', 'LND': 'lindmore', 'LDS': 'lindsay', 'LWT': 'lowertule', 'PRT': 'porterville', 'SAU': 'saucelito', 'SFW': 'shaffer',
                     'SSJ': 'sosanjoaquin', 'TPD': 'teapot', 'TBA': 'terra', 'TUL': 'tulare', 'COF': 'fresno', 'FRS': 'fresnoid', 'SOC': 'socal', 
                     'SOB': 'southbay', 'CCA': 'centralcoast', 'DLR': 'dudleyridge', 'TLB': 'tularelake', 'KWD': 'kaweahdelta', 'WSL': 'westlands', 
                     'SNL': 'sanluiswater', 'PNC': 'panoche', 'DLP': 'delpuerto', 'CWC': 'chowchilla', 'MAD': 'madera', 'OTL': 'othertule', 'OFK': 'otherfriant', 
                     'OCD': 'othercvp', 'OEX': 'otherexchange', 'OXV': 'othercrossvalley', 'OSW': 'otherswp', 'CNS': 'consolidated', 'ALT': 'alta', 'KRWA': 'krwa'}


### read in data & organize datetimes
def get_district_data(datafile):
  dat = get_results_sensitivity_number_outside_model(datafile, '')
  keys = list(dat.keys())
  index = dat.index
  year = index.year
  month = index.month
  # dom = index.day
  # doy = index.dayofyear
  # dowy = (doy + (365-274)) % 365
  wy = np.array([year[i] if month[i] < 10 else year[i] + 1 for i in range(len(year))])
  ### get relevant results for each district
  districts = {}
  for d, v in district_lookup.items():
    b = [k for k in keys if (((d in k.split('_')) or (v in k.split('_'))) and (('delivery' in k.split('_')) or ('flood' in k.split('_')) or ('recharged' in k.split('_')) or \
                                                                                ('exchanged' in k.split('_')) or ('inleiu' in k.split('_')) or ('peiupumping' in k.split('_')) or \
                                                                                  ('banked' in k.split('_'))))]
    df = dat.loc[:, b]
    ## undo summation over years
    for y in range(df.index.year.min() + 2, df.index.year.max() + 1):
      maxprevious = df.loc[wy < y, :].iloc[-1, :]
      df.loc[wy == y, :] += maxprevious
    df.iloc[1:, :] = df.diff().iloc[1:, :]
    ## get total water deliveries across categories
    df['total_deliveries'] = 0.0
    for (wtype, position) in [('delivery', 2), ('flood', 2), ('recover', 1)]:
      for c in df.columns:
        try:
          if c.split('_')[position] == wtype:
            df['total_deliveries'] += df[c]
        except:
          pass    
    districts[d] = df

  return districts, wy

districts_scenario, wy = get_district_data(base_dir + scenario + '/results.hdf5')
districts_baseline, wy = get_district_data(base_dir + baseline + '/results.hdf5')

### aggregate over time for each district
districts_scenario_wy = {}
districts_baseline_wy = {}
for d in districts_scenario:
  districts_scenario_wy[d] = districts_scenario[d].groupby(wy).sum()
for d in districts_baseline:
  districts_baseline_wy[d] = districts_baseline[d].groupby(wy).sum()

### get district-level objectives (gain vs baseline case)
objs_districts = {}
for d in districts_scenario_wy:
  objs_districts[d] = {}
  objs_districts[d]['exp_del'] = districts_scenario_wy[d]['total_deliveries'].mean()
  objs_districts[d]['std_del'] = districts_scenario_wy[d]['total_deliveries'].std()       
  objs_districts[d]['w5yr_del'] = districts_scenario_wy[d]['total_deliveries'].rolling(5).mean().min()
  objs_districts[d]['exp_gain'] = (districts_scenario_wy[d]['total_deliveries'] - districts_baseline_wy[d]['total_deliveries']).mean()
  objs_districts[d]['std_gain'] = (districts_scenario_wy[d]['total_deliveries'] - districts_baseline_wy[d]['total_deliveries']).std()    
  objs_districts[d]['w5yr_gain'] = districts_scenario_wy[d]['total_deliveries'].rolling(5).mean().min() - districts_baseline_wy[d]['total_deliveries'].rolling(5).mean().min()
### now aggregate across districts to get system-wide benefits
partners = []
others = []
num_partners = 0
for k in objs_districts:
  try:
    if shares['ownership'][k] > 0.0:
      partners.append(objs_districts[k]['exp_gain'])
      num_partners += 1
    else:
      others.append(objs_districts[k]['exp_gain'])
  except:
    others.append(objs_districts[k]['exp_gain'])
avg_partner_avg_gain = sum(partners)/num_partners
min_partner_avg_gain = min(partners)
avg_other_avg_gain = sum(others)/len(others)
min_other_avg_gain = min(others)

partners = []
for k in objs_districts:
  try:
    if shares['ownership'][k] > 0.0:
      partners.append(objs_districts[k]['w5yr_gain'])
  except:
    pass  
avg_partner_w5yr_gain = sum(partners)/num_partners
min_partner_w5yr_gain = min(partners)

### gini coef
total_gain = avg_partner_avg_gain * num_partners
gains = []
ds = []
owns = []
for k in districts_scenario:
  try:
    if shares['ownership'][k] > 0.0:
      gains.append(objs_districts[k]['exp_gain'])
      ds.append(k)
      owns.append(shares['ownership'][k])
  except:
    pass
ginidf = pd.DataFrame({'district': ds, 'share': owns, 'gain': gains})
ginidf['sharegain'] = total_gain * ginidf['share']
ginidf['gain/sharegain'] = ginidf['gain'] / ginidf['sharegain']
ginidf.sort_values('gain/sharegain', inplace=True)
ginidf['cumsharegain'] = ginidf['sharegain'].cumsum()
ginidf['cumgain'] = ginidf['gain'].cumsum()
ginidf['fraccumsharegain'] = ginidf['cumsharegain'] / ginidf['cumsharegain'].max()
ginidf['fraccumgain'] = ginidf['cumgain'] / ginidf['cumgain'].max()
ginidf = pd.concat([pd.DataFrame({'fraccumsharegain':[0], 'fraccumgain':[0]}), ginidf]).reset_index(drop=True)

# plt.figure()
# plt.plot(ginidf['fraccumsharegain'], ginidf['fraccumgain'], alpha=0.6, marker='o')
# plt.plot([0,1],[0,1],c='k',ls=':')
# plt.savefig('test1d.png')

### trapezoid rule for integrating area between gini curve and 45deg line
def trap_rule(x, y):
  integ = 0
  for n in range(1, len(x)):
    integ += (x[n] - x[n-1]) * (x[n] + x[n-1] - y[n] - y[n-1])
  integ /= 2
  return integ

ginicoef = 2 * trap_rule(ginidf['fraccumsharegain'].values, ginidf['fraccumgain'].values)

with open(base_dir + scenario + '/objs.csv', 'w') as f:
  f.write('scenario, avg_partner_avg_gain, min_partner_avg_gain, avg_other_avg_gain, min_other_avg_gain, avg_partner_w5yr_gain, min_partner_w5yr_gain, ginicoef\n')
  f.write(f'{scenario}, {avg_partner_avg_gain}, {min_partner_avg_gain}, {avg_other_avg_gain}, {min_other_avg_gain}, {avg_partner_w5yr_gain}, {min_partner_w5yr_gain},  {ginicoef}\n')
