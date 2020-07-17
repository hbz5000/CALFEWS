import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
sns.set_style('whitegrid')

df = pd.read_csv('flows.csv', index_col=0, parse_dates=True).resample('M').mean()

# in winter, assume gains into delta are equal to SHA/ORO/FOL inflows
# because all the basins inflows are correlated 
# winter = (df.index.month >= 11) | (df.index.month <= 3)
# dfw = df[winter]
# resin = dfw[['SHA_in','ORO_in','FOL_in']].sum(axis=1)
# resout = dfw[['SHA_out','ORO_out','FOL_out']].sum(axis=1)
# plt.scatter(resin.values, (dfw.DeltaIn - resout).values)
# plt.xlabel('Sum of SHA/ORO/FOL Inflows')
# plt.ylabel('Delta Gains')

# in summer, use the outflows instead
# and consider diversions along the channel
summer = (df.index.month >= 4) & (df.index.month <= 10)
# dfs = df[summer]
# resout = dfs[['SHA_out','ORO_out','FOL_out']].sum(axis=1)
# gains = dfs[['SHA_in','ORO_in','FOL_in']].sum(axis=1)
# plt.scatter(resout.values, (dfs.DeltaIn-gains).values)
# plt.xlabel('Sum of SHA/ORO/FOL Outflows')
# plt.ylabel('Delta Inflows')

# resout = df[['SHA_out','ORO_out','FOL_out']].sum(axis=1)
# h = resout.plot(color='r')
# df.DeltaIn.plot(color='k', linewidth=2, ax=h)

pred = df[['SHA_in','ORO_in','FOL_in']].sum(axis=1) * 2
pred[summer] = df[['SHA_out','ORO_out','FOL_out']].sum(axis=1) * 0.5
h = pred.plot(color='r')
df.DeltaIn.plot(color='k', linewidth=2, ax=h)

plt.show()