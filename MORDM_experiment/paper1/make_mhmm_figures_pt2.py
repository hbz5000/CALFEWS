import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt




########################################Step 5: Creating Correlation Plots (Figure S10-S11) ########################################################################


sns.set_style("white")
sns.set(font_scale=1.4)


#Historical Annual 

AnnualQ_h = np.loadtxt('./mhmm_data/historical_annual_streamflow_all_locations.csv',skiprows=1,delimiter=',') 
AnnualQ_h=pd.DataFrame(AnnualQ_h,columns=['ORO', 'SHA', 'FOL','YRS','MHB','PAR','NHG','NML','DNP','EXC','MIL','PFT','KWH','SUC','ISB'])


plt.figure(figsize=(16, 10))
ax=sns.heatmap(AnnualQ_h.corr(), vmin=0.5, vmax=1, annot=True,cmap="viridis",cbar_kws={'label': 'Correlation'})
bottom, top = ax.get_ylim()
ax.set_ylim(bottom, top - 0.5)
ax.set_yticklabels(ax.get_yticklabels(), rotation = 0)
ax.set_title(r'$\bf{a)}$ Historical', fontdict={'fontsize':18}, pad=18);
plt.savefig("./figs/historical_annual_correlation.png", dpi=300)
# plt.savefig("./figs/historical_annual_correlation.pdf")


#Synthetic Annual 
AnnualQ_s = np.loadtxt('./mhmm_data/AnnualQ_s.csv',skiprows=1,delimiter=',') 
AnnualQ_s=pd.DataFrame(AnnualQ_s,columns=['ORO', 'SHA', 'FOL','YRS','MHB','PAR','NHG','NML','DNP','EXC','MIL','PFT','KWH','SUC','ISB'])


plt.figure(figsize=(16, 10))
ax=sns.heatmap(AnnualQ_s.corr(), vmin=0.5, vmax=1, annot=True,cmap="viridis",cbar_kws={'label': 'Correlation'})
bottom, top = ax.get_ylim()
ax.set_ylim(bottom, top - 0.5)
ax.set_yticklabels(ax.get_yticklabels(), rotation = 0)
ax.set_title(r'$\bf{b)}$ Synthetic', fontdict={'fontsize':18}, pad=18);
plt.savefig("./figs/synthetic_annual_correlation.png", dpi=300)
# plt.savefig("./figs/synthetic_annual_correlation.pdf")



#Synthetic Daily

DailyQ_s = np.loadtxt('./mhmm_data/synthetic_daily_streamflow_all_locations.txt') 
DailyQ_s=DailyQ_s[:,0:15]
DailyQ_s=pd.DataFrame(DailyQ_s,columns=['ORO', 'SHA', 'FOL','YRS','MHB','PAR','NHG','NML','DNP','EXC','MIL','PFT','KWH','SUC','ISB',])


plt.figure(figsize=(16, 10))
ax=sns.heatmap(DailyQ_s.corr(), vmin=0, vmax=1, annot=True,cmap="viridis",cbar_kws={'label': 'Correlation'})
bottom, top = ax.get_ylim()
ax.set_ylim(bottom, top - 0.5)
ax.set_yticklabels(ax.get_yticklabels(), rotation = 0)
ax.set_title(r'$\bf{b)}$ Synthetic', fontdict={'fontsize':18}, pad=18);
plt.savefig("./figs/synthetic_daily_correlation.png", dpi=300)
# plt.savefig("./figs/synthetic_daily_correlation.pdf")

#Historic Daily


DailyQ_h = np.loadtxt('./mhmm_data/historical_daily_streamflow_all_locations.csv',skiprows=1,delimiter=',') 
DailyQ_h=DailyQ_h[:,0:15]
DailyQ_h=pd.DataFrame(DailyQ_h,columns=['ORO', 'SHA', 'FOL','YRS','MHB','PAR','NHG','NML','DNP','EXC','MIL','PFT','KWH','SUC','ISB',])

plt.figure(figsize=(16, 10))
ax=sns.heatmap(DailyQ_h.corr(), vmin=0, vmax=1, annot=True,cmap="viridis",cbar_kws={'label': 'Correlation'})
bottom, top = ax.get_ylim()
ax.set_ylim(bottom, top - 0.5)
ax.set_yticklabels(ax.get_yticklabels(), rotation = 0)
ax.set_title(r'$\bf{a)}$ Historical', fontdict={'fontsize':18}, pad=18);
plt.savefig("./figs/historical_daily_correlation.png", dpi=300)
# plt.savefig("./figs/historical_daily_correlation.pdf", dpi=300)
