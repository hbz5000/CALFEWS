import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from glob import glob



########################################Step 6: Creating FDCs (Figure S7) ########################################################################

#Import LHS Sample
sample=pd.read_csv('./mhmm_data/AboveMIL_TL.csv')


fig, ax = plt.subplots(1,3)

### get random order for visual stacking of lines
zorder = [int(n) for n in np.random.uniform(0,100, size=100)]

### scenarios 0-20 used in optimization step
for i in range(21):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[0].plot(exceedence, sort,color="#21918c",alpha=0.8,label="Optimization" if i == 0 else "", zorder=zorder[i])

### scenarios 21-99 used in reevaluation step
for i in range(21,100):
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

### scenarios 0-20 used in optimization step
for i in range(21):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[1].plot(exceedence, sort,color="#21918c",alpha=0.8,label="Optimization" if i == 0 else "", zorder=zorder[i])

### scenarios 21-99 used in reevaluation step
for i in range(21,100):
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


### scenarios 0-20 used in optimization step
for i in range(21):
    sort = np.sort(sample.iloc[:,i])
    exceedence = np.arange(1.,len(sort)+1) / (len(sort) +1)
    ax[2].plot(exceedence, sort,color="#21918c",alpha=0.8,label="Optimization" if i == 0 else "", zorder=zorder[i])

### scenarios 21-99 used in reevaluation step
for i in range(21,100):
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





########################################Step 6: Creating FDCs with CMIP5 data ######################################################################

fontsize = 10

for figmode in ['past','future']:
    fig, axs = plt.subplots(1, 3, figsize=(8, 3))

    ### first plot historical data for all figs
    ds = '../../calfews_src/data/input/calfews_src-data-sim.csv'
    ### read in data
    df = pd.read_csv(ds)
    df.index = pd.DatetimeIndex(df['datetime'])
    df.drop(['datetime','realization'], axis=1, inplace=True)
    ### convert kAF/day to TL/day
    df *= 1.233e6 * 1e-12
    ### sum across years
    df['year'] = df.index.year
    df_grp = df.groupby('year').sum()
    ### plot historical data
    df_grp = df_grp.loc[1906:2016,:]

    ### plot above MIL first
    ax = axs[0]
    columns = [f'{r}_fnf' for r in ['ORO', 'SHA', 'FOL', 'YRS', 'MHB', 'PAR', 'NHG', 'NML', 'DNP', 'EXC']]
    df_grp_ax = df_grp[columns].sum(axis=1)
    sort = np.sort(df_grp_ax)
    exceedence = np.arange(1., len(sort) + 1) / (len(sort) + 1)
    ax.plot(exceedence, sort, color="0.65", alpha=1, label="", lw=2, zorder=111)

    ### plot MIL
    ax = axs[1]
    columns = [f'{r}_fnf' for r in ['MIL']]
    df_grp_ax = df_grp[columns].sum(axis=1)
    sort = np.sort(df_grp_ax)
    exceedence = np.arange(1., len(sort) + 1) / (len(sort) + 1)
    ax.plot(exceedence, sort, color="0.65", alpha=1, label="Historical (1906-2015)", lw=2, zorder=111)

    ### plot below MIL
    ax = axs[2]
    columns = [f'{r}_fnf' for r in ['PFT', 'KWH', 'SUC', 'ISB']]
    df_grp_ax = df_grp[columns].sum(axis=1)
    sort = np.sort(df_grp_ax)
    exceedence = np.arange(1., len(sort) + 1) / (len(sort) + 1)
    ax.plot(exceedence, sort, color="0.65", alpha=1, label="", lw=2, zorder=111)



    # Import synthetic hydrologic scenarios
    alpha = 1
    for ax, mhmm_datasets in zip(axs, ['./mhmm_data/AboveMIL_TL.csv', './mhmm_data/MIL_TL.csv', './mhmm_data/BelowMIL_TL.csv']):
        sample = pd.read_csv(mhmm_datasets)
        for i in range(100):
            sort = np.sort(sample.iloc[:, i])
            exceedence = np.arange(1., len(sort) + 1) / (len(sort) + 1)
            ax.plot(exceedence, sort, color="navy", alpha=alpha, lw=1,
                    label="Synthetic scenarios" if i == 0 else "", zorder=1)


    ### now loop over downscaled climate scenarios
    datasets = glob('../../calfews_src/data/CA_FNF_climate_change/CA_FNF_*.csv')
    datasets = [s for s in datasets if 'canesm2' not in s]      ### canesm2 dataset is wrong length for some reason - discarded for this study.
    # print(datasets)

    ### dict to hold the wettest & driest scenario - quantified as the largest & smallest mean flow at Millerton
    hydro_extremes = {'wettest_name': '', 'wettest_mean': 0, 'driest_name': '', 'driest_mean': np.inf}
    for i,ds in enumerate(datasets):
        ### read in data
        df = pd.read_csv(ds)
        ### fill in missing leap years & create datetime index
        missing_rows = [r for r in range(df.shape[0]) if np.isnan(df.iloc[r,0])]
        for r in missing_rows:
            df.iloc[r,:] = df.iloc[r-1,:].values
        df.index = pd.DatetimeIndex([datetime.datetime(1950,1,1) + datetime.timedelta(days=1+n) for n in range(df.shape[0])])
        ### convert cfs to TL/day
        df *= 2446575.6 * 1e-12
        ### sum across years
        df['year'] = df.index.year
        df_grp = df.groupby('year').sum()
        ### get data based on figmode
        if figmode == 'past':
            df_grp = df_grp.loc[1950:2016,:]
            axis_label_yrs = '(1950-2015)'
        elif figmode == 'future':
            df_grp = df_grp.loc[2021:2051,:]
            axis_label_yrs = '(2021-2050)'

        ### plot above MIL first
        ax = axs[0]
        columns = [f'{r}_fnf' for r in ['ORO','SHA','FOL','YRS','MHB','PAR','NHG','NML','DNP','EXC']]
        df_grp_ax = df_grp[columns].sum(axis=1)
        sort = np.sort(df_grp_ax)
        exceedence = np.arange(1., len(sort) + 1) / (len(sort) + 1)
        color = 'darkgoldenrod' if '45_' in ds else 'firebrick'
        ax.plot(exceedence, sort, color=color, alpha=alpha, lw=1, label="", zorder=2)#zorder[i])

        ### plot MIL
        ax = axs[1]
        column = f'MIL_fnf'
        df_grp_ax = df_grp[column]
        sort = np.sort(df_grp_ax)
        exceedence = np.arange(1., len(sort) + 1) / (len(sort) + 1)
        label = f'Projections RCP 4.5 {axis_label_yrs}' if i == 0 else f'Projections RCP 8.5 {axis_label_yrs}' if i == 1 else ''
        ax.plot(exceedence, sort, color=color, alpha=alpha, lw=1,
                # label="Downscaled climate projections (1906-2015)" if i == 0 else "", zorder=2)#zorder[i])
                label=label, zorder=2)#zorder[i])
        ### record if this is wettest or driest record
        if df_grp_ax.mean() > hydro_extremes['wettest_mean']:
            hydro_extremes['wettest_mean'] = df_grp_ax.mean()
            hydro_extremes['wettest_name'] = ds.split('/')[-1]
        if  df_grp_ax.mean() < hydro_extremes['driest_mean']:
            hydro_extremes['driest_mean'] = df_grp_ax.mean()
            hydro_extremes['driest_name'] = ds.split('/')[-1]



        ### plot below MIL
        ax = axs[2]
        columns = [f'{r}_fnf' for r in ['PFT','KWH','SUC','ISB']]
        df_grp_ax = df_grp[columns].sum(axis=1)
        sort = np.sort(df_grp_ax)
        exceedence = np.arange(1., len(sort) + 1) / (len(sort) + 1)
        ax.plot(exceedence, sort, color=color, alpha=alpha, lw=1, label="", zorder=2)#zorder[i])



    print(hydro_extremes)
    ### clean up figs
    axs[0].set_ylabel('Annual FNF (TL/yr)',fontsize=fontsize)
    axs[1].set_xlabel("Non-Exceedance Probability", fontsize=fontsize)
    for ax in axs:
        ax.tick_params(axis='both', which='major', labelsize=fontsize)
        ax.set_ylim(ymin=0)

    leg = axs[1].legend(loc='lower center', bbox_to_anchor=(0.5, -0.5), fontsize=fontsize, frameon=False, ncol=2)

    axs[0].text(0.05, 0.90, "a)", fontsize=20, weight="bold", transform=axs[0].transAxes)
    axs[1].text(0.05, 0.90, "b)", fontsize=20, weight="bold",transform=axs[1].transAxes)
    axs[2].text(0.05, 0.90, "c)", fontsize=20, weight="bold", transform=axs[2].transAxes)


    plt.savefig(f"./figs/FDC_climate_scenarios_{figmode}.png", format="png", dpi=300, bbox_inches='tight')




