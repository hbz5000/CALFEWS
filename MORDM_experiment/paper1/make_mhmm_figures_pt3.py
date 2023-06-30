import numpy as np
import pandas as pd
from matplotlib import pyplot as plt




########################################Step 6: Creating FDCs (Figure S7) ########################################################################

#Import LHS Sample
sample=pd.read_csv('./mhmm_data/AboveMIL_TL.csv')


fig, ax = plt.subplots(1,3)

### get random order for visual stacking of lines
zorder = [int(n) for n in np.random.uniform(0,100, size=100)]

### scenarios 0-31 used in optimization step
for i in range(32):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[0].plot(exceedence, sort,color="#21918c",alpha=0.8,label="Optimization" if i == 0 else "", zorder=zorder[i])

### scenarios 33-96 used in reevaluation step
for i in range(33,97):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[0].plot(exceedence, sort,color="#3b528b",alpha=0.8,label="Reevaluation" if i == 33 else "", zorder=zorder[i])



AnnualQ_h = np.array(pd.read_csv('./mhmm_data/AnnualQ_h.csv',header=None))
AnnualQ_h = AnnualQ_h*1.233e6*1e-12
sort = np.sort(np.sum(AnnualQ_h[:,0:9],axis=1))
exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)

ax[0].plot(exceedence, sort,color="#FFD700",label='Historical',linewidth=3, zorder=111)
ax[0].set_xlabel("Non-Exceedance\nProbability",fontsize=20)
ax[0].set_ylabel('Annual FNF (TL/yr)',fontsize=20)
#ax[0].set_title("North of Millerton",fontsize=22,y=1.08)
ax[0].tick_params(axis='both', which='major', labelsize=22)
ax[0].set_ylim(ymin=0)




#Millerton 


#Import LHS Sample
sample=pd.read_csv('./mhmm_data/MIL_TL.csv')

### scenarios 0-31 used in optimization step
for i in range(32):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[1].plot(exceedence, sort,color="#21918c",alpha=0.8,label="Optimization" if i == 0 else "", zorder=zorder[i])

### scenarios 33-96 used in reevaluation step
for i in range(33,97):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[1].plot(exceedence, sort,color="#3b528b",alpha=0.8,label="Reevaluation" if i == 33 else "", zorder=zorder[i])





AnnualQ_h = np.array(pd.read_csv('./mhmm_data/AnnualQ_h.csv',header=None))
AnnualQ_h = AnnualQ_h*1.233e6*1e-12
sort = np.sort(AnnualQ_h[:,10])
exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)

ax[1].plot(exceedence, sort,color="#FFD700",label='Historical',linewidth=3, zorder=111)
#ax[1].set_ylabel('Annual FNF (TL/yr)',fontsize=20)
ax[1].set_xlabel("Non-Exceedance\nProbability",fontsize=20)
#ax[1].set_title("Millerton",fontsize=22,y=1.08)
ax[1].tick_params(axis='both', which='major', labelsize=22)
ax[1].set_ylim(ymin=0)

#ax[1].legend(loc='lower center', bbox_to_anchor=(0.5, -0.5), fontsize = 20,frameon=False,ncol=3)
 
leg = ax[1].legend(loc='lower center', bbox_to_anchor=(0.5, -0.5), fontsize = 20,frameon=False,ncol=3)
leg.get_lines()[0].set_linewidth(5)
leg.get_lines()[1].set_linewidth(5)
leg.get_lines()[2].set_linewidth(5)


#Below Millerton


#Import LHS Sample
sample=pd.read_csv('./mhmm_data/BelowMIL_TL.csv')


### scenarios 0-31 used in optimization step
for i in range(32):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[2].plot(exceedence, sort,color="#21918c",alpha=0.8,label="Optimization" if i == 0 else "", zorder=zorder[i])

### scenarios 33-96 used in reevaluation step
for i in range(33,97):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[2].plot(exceedence, sort,color="#3b528b",alpha=0.8,label="Reevaluation" if i == 33 else "", zorder=zorder[i])



AnnualQ_h = np.array(pd.read_csv('./mhmm_data/AnnualQ_h.csv',header=None))
AnnualQ_h = AnnualQ_h*1.233e6*1e-12
sort = np.sort(np.sum(AnnualQ_h[:,11:15],axis=1))
exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)

ax[2].plot(exceedence, sort,color="#FFD700",label='Historical',linewidth=3, zorder=111)
ax[2].set_xlabel("Non-Exceedance\nProbability",fontsize=20)
#ax[2].set_ylabel('Annual FNF (TL/yr)',fontsize=20)
#ax[2].set_title("South of Millerton",fontsize=22,y=1.08)
ax[2].tick_params(axis='both', which='major', labelsize=22)
ax[2].set_ylim(ymin=0)

ax[0].text(0.05, 0.90, "a)", fontsize=20, weight="bold", transform=ax[0].transAxes)
ax[1].text(0.05, 0.90, "b)", fontsize=20, weight="bold",transform=ax[1].transAxes)
ax[2].text(0.05, 0.90, "c)", fontsize=20, weight="bold", transform=ax[2].transAxes)


fig.set_size_inches(17,6)
plt.savefig("./figs/FDC.png", format="png", dpi=300,bbox_inches='tight')

