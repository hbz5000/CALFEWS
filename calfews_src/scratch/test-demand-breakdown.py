import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
import seaborn as sns
sns.set_style('whitegrid')

cfs_tafd = 2.29568411*10**-5 * 86400 / 1000

def water_day(d):
  return d - 274 if d >= 274 else d + 91

df = pd.read_csv('../data/calfews_src-data.csv', index_col=0, parse_dates=True)
print df.keys()
# # north of delta demand, in TAFD (CVP only)
nodd = np.array([2,2,3,5,8,11,12,8,6,5,4,2]) #/ cfs_tafd
print nodd*0.82 # shasta
print nodd*0.18 # folsom
df['nodd'] = pd.Series([nodd[m-1] for m in df.index.month], index=df.index)

sodd_cvp = np.array([8,8,6,2,3.5,6.5,8,8,8,8,8,8]) / cfs_tafd
print sodd_cvp*0.82 # shasta 
print sodd_cvp*0.18 # folsom

# then do HRO/ ORO

# (df.ORO_out * cfs_tafd).resample('AS-OCT').sum().plot()
# plt.show()
# df = (df).resample('M').sum() * cfs_tafd
# df['dowy'] = pd.Series([water_day(d) for d in df.index.dayofyear], index=df.index)
# sns.lmplot('dowy', 'SHA_out', data=df, hue='SR_WYT', fit_reg=False)
# df['month'] = df.index.month

# Hydrologic gains between reservoirs and delta
# assume equal to 1.0*reservoir INFLOWS (not outflows)
# does not apply in the summer? or should it?
df['gains'] = df[['SHA_in', 'ORO_in', 'FOL_in']].sum(axis=1)
# df.loc[(df.index.month >= 6) & (df.index.month <= 10), 'gains'] = 0.0

# df['resout'] = df[['SHA_out','ORO_out','FOL_out']].sum(axis=1)

# (df.HRO_pump.resample('M').sum()*cfs_tafd).plot()
# h = df.filter(like='_out').plot(kind='area')

# # df['delta_inflow_predicted'] = df.resout + df.gains - df.nodd
# df['thing'] = df.SHA_out + df.FOL_out - df.nodd
# df = (df).resample('M').mean()
# df.thing.plot(color='r')
# df.TRP_pump.plot(color='k')

def plotyear(x):
  print x
  x.plot()

df.TRP_pump.resample('M').mean().plot()
# df[['TRP_pump', 'HRO_pump', 'SNL_storage']].plot()
# h = df[['ORO_out']].plot(kind='area', linewidth=0)
# # df.plot(kind='scatter', x='month', y='SHA_out')
# # h = df.filter(like='fnf').plot(kind='area', linewidth=0)
# h = df.delta_inflow_predicted.plot(color='r', linewidth=2)
# df.nodd.plot(color='k', linewidth=2, ax=h)
# # df.plot(kind='scatter', x='DeltaIn', y='delta_inflow_predicted')
plt.show()
