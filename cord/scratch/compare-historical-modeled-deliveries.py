import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


### read in & aggregate SWP historical data
swp_historical = pd.read_csv('cord/data/input/SWP_delivery_cleaned.csv')

# aggregate by Year-Month-Agency_Group-WT_model
swp_historical['Year__Month__Agency_Group__WT_model'] = swp_historical.Year.map(str) + '__' + swp_historical.Month.map(str) + '__' + swp_historical.Agency_Group + '__' + swp_historical.WT_model
swp_historical_aggregate = swp_historical.groupby(by = ['Year__Month__Agency_Group__WT_model']).sum()
swp_historical_aggregate['Year'] = swp_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Year'].first()
swp_historical_aggregate['Month'] = swp_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Month'].first()
swp_historical_aggregate['Day'] = 1
swp_historical_aggregate['Wateryear'] = swp_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Wateryear'].first()
swp_historical_aggregate['Agency_Group'] = swp_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['Agency_Group'].first()
swp_historical_aggregate['WT_model'] = swp_historical.groupby(by = ['Year__Month__Agency_Group__WT_model'])['WT_model'].first()
swp_historical_aggregate['Date'] = pd.to_datetime(swp_historical_aggregate[['Year','Month','Day']])
swp_historical_aggregate = swp_historical_aggregate.sort_values(by=['Date'])

# aggregate by Year-Month-Agency_Group, only for is_delivery==1 (should be approximately total deliveries, but not sure about 'other' water types)
swp_historical_deliveries = swp_historical.loc[swp_historical.is_delivery == 1]
swp_historical_deliveries['Year__Month__Agency_Group'] = swp_historical_deliveries.Year.map(str) + '__' + swp_historical_deliveries.Month.map(str) + '__' + swp_historical_deliveries.Agency_Group
swp_historical_deliveries_aggregate = swp_historical_deliveries.groupby(by = ['Year__Month__Agency_Group']).sum()
swp_historical_deliveries_aggregate['Year'] = swp_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Year'].first()
swp_historical_deliveries_aggregate['Month'] = swp_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Month'].first()
swp_historical_deliveries_aggregate['Day'] = 1
swp_historical_deliveries_aggregate['Wateryear'] = swp_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Wateryear'].first()
swp_historical_deliveries_aggregate['Agency_Group'] = swp_historical_deliveries.groupby(by = ['Year__Month__Agency_Group'])['Agency_Group'].first()
swp_historical_deliveries_aggregate['Date'] = pd.to_datetime(swp_historical_deliveries_aggregate[['Year','Month','Day']])
swp_historical_deliveries_aggregate = swp_historical_deliveries_aggregate.sort_values(by=['Date'])


### plot historical aggregate deliveries
dum =  (swp_historical_aggregate.Agency_Group == 'DLR')
dum2 = dum & (swp_historical_aggregate.WT_model == 'tableA_delivery')
# dum3 = dum & (swp_historical.WT_model == 'tableA_flood')
# dum4 = dum & (swp_historical.WT_model == 'tableA_turnback')
# dum5 = dum & (swp_historical.WT_model == 'tableA_carryover')
# dum6 = dum & (swp_historical.WT_model == 'recover_banked')
# dum7 = dum & (swp_historical.WT_model == 'exchange_SW')
# dum8 = dum & (swp_historical.WT_model == 'other')

plt.plot_date(swp_historical_aggregate['Date'].loc[dum2], swp_historical_aggregate['delivery_taf'].loc[dum2],fmt='-')
# plt.plot_date(swp_historical['Date'].loc[dum3], swp_historical['delivery_taf'].loc[dum3], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum4], swp_historical['delivery_taf'].loc[dum4], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum5], swp_historical['delivery_taf'].loc[dum5], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum6], swp_historical['delivery_taf'].loc[dum6], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum7], swp_historical['delivery_taf'].loc[dum7], marker='o', alpha=0.3)
# plt.plot_date(swp_historical['Date'].loc[dum8], swp_historical['delivery_taf'].loc[dum8], marker='o', alpha=0.3)
# plt.legend(['delivery','flood','turnback','carryover','recovery','exchange_SW', 'other'])






### read in and aggregate historical CVP deliveries
cvp_historical = pd.read_csv('cord/data/input/CVP_delivery_cleaned.csv')
cvp_historical_pumpin = cvp_historical.loc[cvp_historical.pumpin==True,:]
cvp_historical = cvp_historical.loc[cvp_historical.pumpin==False,:]
#
# aggregate by Canal__Date
cvp_historical['Canal__Date'] = cvp_historical.Canal + '__' + cvp_historical.Date.map(str)
cvp_historical_aggregate_canal = cvp_historical.groupby(by = ['Canal__Date']).sum()
cvp_historical_aggregate_canal['Year'] = cvp_historical.groupby(by = ['Canal__Date'])['Year'].first()
cvp_historical_aggregate_canal['Month'] = cvp_historical.groupby(by = ['Canal__Date'])['Month'].first()
cvp_historical_aggregate_canal['Wateryear'] = cvp_historical.groupby(by = ['Canal__Date'])['Wateryear'].first()
cvp_historical_aggregate_canal['Date'] = cvp_historical.groupby(by = ['Canal__Date'])['Date'].first()
cvp_historical_aggregate_canal['Canal'] = cvp_historical.groupby(by = ['Canal__Date'])['Canal'].first()
cvp_historical_aggregate_canal['Project'] = 'CVP'
cvp_historical_aggregate_canal = cvp_historical_aggregate_canal.reset_index(drop=True)

# cvp_historical_pumpin['Canal__Date'] = cvp_historical_pumpin.Canal + '__' + cvp_historical_pumpin.Date.map(str)
# cvp_historical_pumpin_aggregate = cvp_historical_pumpin.groupby(by = ['Canal__Date']).sum()
# cvp_historical_pumpin_aggregate['Year'] = cvp_historical_pumpin.groupby(by = ['Canal__Date'])['Year'].first()
# cvp_historical_pumpin_aggregate['Month'] = cvp_historical_pumpin.groupby(by = ['Canal__Date'])['Month'].first()
# cvp_historical_pumpin_aggregate['Wateryear'] = cvp_historical_pumpin.groupby(by = ['Canal__Date'])['Wateryear'].first()
# cvp_historical_pumpin_aggregate['Date'] = cvp_historical_pumpin.groupby(by = ['Canal__Date'])['Date'].first()
# cvp_historical_pumpin_aggregate['Canal'] = cvp_historical_pumpin.groupby(by = ['Canal__Date'])['Canal'].first()
# cvp_historical_pumpin_aggregate['Project'] = 'CVP'
# cvp_historical_pumpin_aggregate = cvp_historical_pumpin_aggregate.reset_index(drop=True)

# aggregate by Contractor_Date
cvp_historical['Contractor__Date'] = cvp_historical.contractor + '__' + cvp_historical.Date.map(str)
cvp_historical_aggregate_contractor = cvp_historical.groupby(by = ['Contractor__Date']).sum()
cvp_historical_aggregate_contractor['Year'] = cvp_historical.groupby(by = ['Contractor__Date'])['Year'].first()
cvp_historical_aggregate_contractor['Month'] = cvp_historical.groupby(by = ['Contractor__Date'])['Month'].first()
cvp_historical_aggregate_contractor['Wateryear'] = cvp_historical.groupby(by = ['Contractor__Date'])['Wateryear'].first()
cvp_historical_aggregate_contractor['Date'] = cvp_historical.groupby(by = ['Contractor__Date'])['Date'].first()
cvp_historical_aggregate_contractor['Canal'] = cvp_historical.groupby(by = ['Contractor__Date'])['Canal'].first()
cvp_historical_aggregate_contractor['contractor'] = cvp_historical.groupby(by = ['Contractor__Date'])['contractor'].first()
cvp_historical_aggregate_contractor['Project'] = 'CVP'
cvp_historical_aggregate_contractor = cvp_historical_aggregate_contractor.reset_index(drop=True)


#
# ### plot historical aggregate deliveries
# for canal in cvp_historical_aggregate.Canal.unique():
#   plt.plot_date(cvp_historical_aggregate['Date'].loc[cvp_historical_aggregate.Canal == canal],
#                 cvp_historical_aggregate['delivery_taf'].loc[cvp_historical_aggregate.Canal == canal],fmt='-')
# plt.legend(cvp_historical_aggregate.Canal.unique())
#
# ### plot historical aggregate pumpin
# for canal in cvp_historical_pumpin_aggregate.Canal.unique():
#   plt.plot_date(cvp_historical_pumpin_aggregate['Date'].loc[cvp_historical_pumpin_aggregate.Canal == canal],
#                 cvp_historical_pumpin_aggregate['delivery_taf'].loc[cvp_historical_pumpin_aggregate.Canal == canal],fmt='-')
# plt.legend(cvp_historical_pumpin_aggregate.Canal.unique())

### plot historical aggregate deliveries
# for contractor in cvp_historical_aggregate.contractor.unique():
#   plt.plot_date(cvp_historical_aggregate['Date'].loc[cvp_historical_aggregate.contractor == contractor],
#                 cvp_historical_aggregate['delivery_taf'].loc[cvp_historical_aggregate.contractor == contractor],fmt='-')
# plt.legend(cvp_historical_aggregate.contractor.unique())


### Now read in modeled daily district delivery data
df_modeled = pd.read_csv('cord/data/results/district_results_full_validation.csv', index_col=0, parse_dates=True)

# aggregate monthly sum
df_modeled = df_modeled.resample('M').last()
df_modeled['Year__'] = df_modeled.index.year
df_modeled['Month__'] = df_modeled.index.month
df_modeled['Wateryear__'] = df_modeled.Year__
df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] = df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] + 1

# get district and water delivery type
districts_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
WT_modeled = df_modeled.columns.map(lambda x: x.split('_',1)[1])
# source_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])
# source_modeled[source_modeled in ['recharged', 'GW', 'banked', 'SW', 'inleiu', 'leiupumping', 'trades']] = 'none'
# source_modeled[tuple(x in ['Year', 'Month', 'Wateryear'] for x in source_modeled)] = 'NA'
df_modeled['Year'] = df_modeled['Year__']
df_modeled['Month'] = df_modeled['Month__']
df_modeled['Wateryear'] = df_modeled['Wateryear__']
del df_modeled['Year__'], df_modeled['Month__'], df_modeled['Wateryear__']

# deliveries are cumulative over water year, so difference to get monthly deliveries
# df_modeled['Date'] = df_modeled.index
# df_modeled.index = range(df_modeled.shape[0])
ind = np.where(WT_modeled == 'tableA_delivery')[0]
for i in ind:
  for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
    startDay = np.where(df_modeled.Wateryear == wy)[0][0]
    df_modeled.iloc[(startDay+1):(startDay+12), i] = np.diff(df_modeled.iloc[(startDay):(startDay+12), i])
ind = np.where(WT_modeled == 'tableA_flood')[0]
for i in ind:
  for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
    startDay = np.where(df_modeled.Wateryear == wy)[0][0]
    df_modeled.iloc[(startDay+1):(startDay+12), i] = np.diff(df_modeled.iloc[(startDay):(startDay+12), i])
ind = np.where(WT_modeled == 'friant1_delivery')[0]
for i in ind:
  for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
    startDay = np.where(df_modeled.Wateryear == wy)[0][0]
    df_modeled.iloc[(startDay+1):(startDay+12), i] = np.diff(df_modeled.iloc[(startDay):(startDay+12), i])
ind = np.where(WT_modeled == 'friant1_flood')[0]
for i in ind:
  for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
    startDay = np.where(df_modeled.Wateryear == wy)[0][0]
    df_modeled.iloc[(startDay+1):(startDay+12), i] = np.diff(df_modeled.iloc[(startDay):(startDay+12), i])
ind = np.where(WT_modeled == 'friant2_flood')[0]
for i in ind:
  for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
    startDay = np.where(df_modeled.Wateryear == wy)[0][0]
    df_modeled.iloc[(startDay+1):(startDay+12), i] = np.diff(df_modeled.iloc[(startDay):(startDay+12), i])
ind = np.where(WT_modeled == 'friant2_delivery')[0]
for i in ind:
  for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
    startDay = np.where(df_modeled.Wateryear == wy)[0][0]
    df_modeled.iloc[(startDay+1):(startDay+12), i] = np.diff(df_modeled.iloc[(startDay):(startDay+12), i])



### get water-year deliveries
cvp_historical['WaterUserCode__Wateryear'] = cvp_historical.WaterUserCode + '__' + cvp_historical.Wateryear.map(int).map(str)
cvp_historical_aggregate_WaterUserCode_Wateryear =  cvp_historical.groupby(by = ['WaterUserCode__Wateryear']).sum()
cvp_historical_aggregate_WaterUserCode_Wateryear['WaterUserCode'] = cvp_historical.groupby(by = ['WaterUserCode__Wateryear'])['WaterUserCode'].first()
cvp_historical_aggregate_WaterUserCode_Wateryear['Wateryear'] = cvp_historical.groupby(by = ['WaterUserCode__Wateryear'])['Wateryear'].first()
cvp_historical_aggregate_WaterUserCode_Wateryear['Canal'] = cvp_historical.groupby(by = ['WaterUserCode__Wateryear'])['Canal'].first()

df_modeled_aggregate_Wateryear = df_modeled.groupby(by = 'Wateryear').sum()
df_modeled_aggregate_Wateryear['Wateryear'] = df_modeled.groupby(by = 'Wateryear')['Wateryear'].first()

plt.plot_date(cvp_historical_aggregate_WaterUserCode_Wateryear['Wateryear'].loc[cvp_historical_aggregate_WaterUserCode_Wateryear.WaterUserCode == 'LWT'],
                cvp_historical_aggregate_WaterUserCode_Wateryear['delivery_taf'].loc[cvp_historical_aggregate_WaterUserCode_Wateryear.WaterUserCode == 'LWT'],fmt='-')
ind = ((districts_modeled == 'LWT') & ((WT_modeled == 'friant1_delivery')|(WT_modeled == 'friant1_flood')|(WT_modeled == 'friant2_delivery')|(WT_modeled == 'friant2_flood')))
plt.plot(np.sum(df_modeled_aggregate_Wateryear.loc[:, ind],axis=1))
plt.legend(['LWT historical','LWT modeled'])


### plot historical & modeled deliveries - CVP

# ### plot historical & modeled deliveries - FKC
# plt.plot_date(cvp_historical_aggregate['Date'].loc[cvp_historical_aggregate.Canal == 'FRIANT-KERNCANAL'],
#                 cvp_historical_aggregate['delivery_taf'].loc[cvp_historical_aggregate.Canal == 'FRIANT-KERNCANAL'],fmt='-')
# ind = (WT_modeled == 'friant1_delivery')|(WT_modeled == 'friant1_flood')|(WT_modeled == 'friant2_delivery')|(WT_modeled == 'friant2_flood')
# plt.plot(np.sum(df_modeled.loc[:, ind],axis=1))

### plot historical & modeled deliveries - FKC
plt.plot_date(cvp_historical_aggregate_canal['Date'].loc[cvp_historical_aggregate_canal.Canal == 'FRIANT-KERNCANAL'],
                cvp_historical_aggregate_canal['delivery_taf'].loc[cvp_historical_aggregate_canal.Canal == 'FRIANT-KERNCANAL'],fmt='-')
plt.plot_date(cvp_historical_aggregate_contractor['Date'].loc[(cvp_historical_aggregate_contractor.contractor == 'friant')&(cvp_historical_aggregate_contractor.Canal == 'FRIANT-KERNCANAL')],
                cvp_historical_aggregate_contractor['delivery_taf'].loc[(cvp_historical_aggregate_contractor.contractor == 'friant')&(cvp_historical_aggregate_contractor.Canal == 'FRIANT-KERNCANAL')],fmt='-')
ind = (WT_modeled == 'friant1_delivery')|(WT_modeled == 'friant1_flood')|(WT_modeled == 'friant2_delivery')|(WT_modeled == 'friant2_flood')
plt.plot(np.sum(df_modeled.loc[:, ind],axis=1))
plt.legend(['FKC total','FKC contractors','Modeled friant'])

### plot historical & modeled deliveries - Lower Tule
plt.plot_date(cvp_historical['Date'].loc[(cvp_historical.WaterUserCode == 'LWT')&(cvp_historical.Canal == 'FRIANT-KERNCANAL')],
                cvp_historical['delivery_taf'].loc[(cvp_historical.WaterUserCode == 'LWT')&(cvp_historical.Canal == 'FRIANT-KERNCANAL')], fmt='-')
# plt.plot_date(cvp_historical_aggregate_contractor['Date'].loc[(cvp_historical_aggregate_contractor.contractor == 'friant')&(cvp_historical_aggregate_contractor.Canal == 'FRIANT-KERNCANAL')],
#                 cvp_historical_aggregate_contractor['delivery_taf'].loc[(cvp_historical_aggregate_contractor.contractor == 'friant')&(cvp_historical_aggregate_contractor.Canal == 'FRIANT-KERNCANAL')],fmt='-')
ind = ((districts_modeled == 'LWT') & ((WT_modeled == 'friant1_delivery')|(WT_modeled == 'friant1_flood')|(WT_modeled == 'friant2_delivery')|(WT_modeled == 'friant2_flood')))
plt.plot(np.sum(df_modeled.loc[:, ind],axis=1))
plt.legend(['LWT historical','LWT modeled'])

plt.scatter(np.arange(19))

#
# ### plot historical & modeled deliveries - Losts Hills
# dum =  (swp_historical_deliveries_aggregate.Agency_Group == 'LHL')
# plt.plot_date(swp_historical_deliveries_aggregate['Date'].loc[dum], swp_historical_deliveries_aggregate['delivery_taf'].loc[dum],fmt='-')
#
# ind = (districts_modeled == 'LHL')&((WT_modeled == 'tableA_delivery') | (WT_modeled == 'tableA_flood'))
# plt.plot(df_modeled.loc[:, ind])
#
