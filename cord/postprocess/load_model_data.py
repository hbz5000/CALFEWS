import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import cm

def load_canal_data(datafile):
  ### read in canal results
  canal = pd.read_csv(datafile, index_col=0, parse_dates=True)

  canal['Date__'] = canal.index
  canal['Year__'] = canal.index.year
  canal['Month__'] = canal.index.month
  canal['Wateryear__'] = canal.Year__
  canal.Wateryear__.loc[canal.Month__ > 9] = canal.Wateryear__.loc[canal.Month__ > 9] + 1

  # only keep FKC & MDC & KNR & XVC
  ind_canal_flowtype = canal.columns.map(lambda x: x.split('_')[2])
  ind_canal_waterway = canal.columns.map(lambda x: x.split('_')[0])
  ind_canal_recipient = canal.columns.map(lambda x: x.split('_')[1])
  canal = canal.loc[:, ((ind_canal_waterway == 'FKC') | (ind_canal_waterway == 'MDC') | (ind_canal_waterway == 'KNR') | (ind_canal_waterway == 'XVC') | (ind_canal_flowtype == ''))]

  ind_canal_flowtype = canal.columns.map(lambda x: x.split('_')[2])
  ind_canal_waterway = canal.columns.map(lambda x: x.split('_')[0])
  ind_canal_recipient = canal.columns.map(lambda x: x.split('_')[1])


  # clean dates
  canal['Date'] = canal['Date__']
  canal['Year'] = canal['Year__']
  canal['Month'] = canal['Month__']
  canal['Wateryear'] = canal['Wateryear__']
  del canal['Date__'], canal['Year__'], canal['Month__'], canal['Wateryear__']

  # get aggregated deliveries - annual
  canal_aggregate_Wateryear = canal.groupby(by = 'Wateryear').sum()
  canal_aggregate_Wateryear['Wateryear'] = canal.groupby(by = 'Wateryear')['Wateryear'].first()
  canal_aggregate_Wateryear['Date'] = canal.groupby(by = 'Wateryear')['Date'].first()
  canal_aggregate_Wateryear = canal_aggregate_Wateryear.sort_values('Date')

  # get aggregated deliveries - annual/monthly
  canal['Wateryear__Month'] = canal.Wateryear.map(int).map(str) + '__' + canal.Month.map(int).map(str)
  canal_aggregate_Wateryear_Month = canal.groupby(by = 'Wateryear__Month').sum()
  canal_aggregate_Wateryear_Month['Wateryear'] = canal.groupby(by = 'Wateryear__Month')['Wateryear'].first()
  canal_aggregate_Wateryear_Month['Month'] = canal.groupby(by = 'Wateryear__Month')['Month'].first()
  canal_aggregate_Wateryear_Month['Date'] = canal.groupby(by = 'Wateryear__Month')['Date'].first()
  canal_aggregate_Wateryear_Month = canal_aggregate_Wateryear_Month.sort_values('Date')


  return (canal, canal_aggregate_Wateryear, canal_aggregate_Wateryear_Month, ind_canal_waterway, ind_canal_recipient, ind_canal_flowtype)





def load_district_data(datafile):

  ### Read in modeled daily district delivery data
  df_modeled = pd.read_csv(datafile, index_col=0, parse_dates=True)

  df_modeled['Date__'] = df_modeled.index
  df_modeled['Year__'] = df_modeled.index.year
  df_modeled['Month__'] = df_modeled.index.month
  df_modeled['Wateryear__'] = df_modeled.Year__
  df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] = df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] + 1


  ### get district and water delivery type
  districts_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_',1)[1])
  source_modeled = WT_modeled.map(lambda x: x.split('_',1)[0])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])

  # only keep friant contractors
  # friant_districts = ['COF', 'FRS', 'OFK', 'TUL', 'KWD', 'OKW', 'EXE', 'LDS', 'LND', 'PRT', 'LWT',
  #      'OTL', 'TPD', 'SAU', 'TBA', 'OXV', 'PIX', 'DLE', 'KRT', 'SSJ', 'SFW', 'NKN',
  #      'NKB', 'ARV','Date','Year','Month','Wateryear']
  friant_districts = ['LWT', 'DLE','SSJ','SFW', 'Date', 'Year', 'Month', 'Wateryear']
  df_modeled = df_modeled.loc[:, [d in friant_districts for d in districts_modeled]]
  friant_districts = friant_districts[:-4]

  districts_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_',1)[1])
  source_modeled = WT_modeled.map(lambda x: x.split('_',1)[0])
  WT_modeled = WT_modeled.map(lambda x: x.split('_',1)[-1])


  # binary variables for differnt types of deliveries
  friantDelivery_modeled = df_modeled.columns.map(lambda x: False)
  cvcDelivery_modeled = df_modeled.columns.map(lambda x: False)
  swpDelivery_modeled = df_modeled.columns.map(lambda x: False)
  cvpdeltaDelivery_modeled = df_modeled.columns.map(lambda x: False)
  localDelivery_modeled = df_modeled.columns.map(lambda x: False)
  otherDelivery_modeled = df_modeled.columns.map(lambda x: False)
  recharged_modeled = df_modeled.columns.map(lambda x: False)
  pumping_modeled = df_modeled.columns.map(lambda x: False)
  irr_demand_modeled = df_modeled.columns.map(lambda x: False)
  exchanged_SW = df_modeled.columns.map(lambda x: False)
  exchanged_GW = df_modeled.columns.map(lambda x: False)
  friantDelivery_modeled.values[((source_modeled == 'friant1')|(source_modeled=='friant2')) & ((WT_modeled == 'delivery')|(WT_modeled == 'flood')|(WT_modeled == 'flood_irrigation'))] = True
  cvcDelivery_modeled.values[((source_modeled=='cvc')) & ((WT_modeled == 'delivery')|(WT_modeled == 'flood'))] = True
  swpDelivery_modeled.values[((source_modeled == 'tableA')) & ((WT_modeled == 'delivery')|(WT_modeled == 'flood'))] = True
  cvpdeltaDelivery_modeled.values[((source_modeled == 'cvpdelta')) & ((WT_modeled == 'delivery')|(WT_modeled == 'flood'))] = True
  localDelivery_modeled.values[((source_modeled == 'kings') | (source_modeled == 'kaweah') | (source_modeled == 'tule') | (source_modeled == 'kern')) & ((WT_modeled == 'delivery')|(WT_modeled == 'flood')|(WT_modeled == 'flood_irrigation'))] = True
  otherDelivery_modeled.values[[i for i,v in enumerate(WT_modeled) if v in ['banked','SW','GW']]] = True
  otherDelivery_modeled.values[[i for i,v in enumerate(source_modeled) if v in ['recover','inleiu']]] = True
  recharged_modeled.values[[i for i,v in enumerate(WT_modeled) if v in ['recharged']]] = True
  pumping_modeled.values[[i for i,v in enumerate(source_modeled) if v in ['pumping']]] = True
  irr_demand_modeled.values[[i for i,v in enumerate(source_modeled) if v in ['irr']]] = True


  df_modeled['Date'] = df_modeled['Date__']
  df_modeled['Year'] = df_modeled['Year__']
  df_modeled['Month'] = df_modeled['Month__']
  df_modeled['Wateryear'] = df_modeled['Wateryear__']
  del df_modeled['Date__'], df_modeled['Year__'], df_modeled['Month__'], df_modeled['Wateryear__']

  # deliveries are cumulative over water year, so difference to get monthly deliveries
  ind = np.where((friantDelivery_modeled == True) | (cvcDelivery_modeled == True) | (swpDelivery_modeled == True) |
                 (cvpdeltaDelivery_modeled == True) | (localDelivery_modeled == True) | (otherDelivery_modeled == True) |
                 (recharged_modeled == True) | (pumping_modeled == True)| (exchanged_GW == True)| (exchanged_SW == True))[0]
  for i in ind:
    for wy in range(min(df_modeled.Wateryear), max(df_modeled.Wateryear)+1):
      startDay = np.where(df_modeled.Wateryear == wy)[0][0]
      endDay = np.where(df_modeled.Wateryear == wy)[0][-1]
      df_modeled.iloc[(startDay+1):(endDay+1), i] = np.diff(df_modeled.iloc[(startDay):(endDay+1), i])


  # get aggregated deliveries - annual
  df_modeled_aggregate_Wateryear = df_modeled.groupby(by = 'Wateryear').sum()
  df_modeled_aggregate_Wateryear['Wateryear'] = df_modeled.groupby(by = 'Wateryear')['Wateryear'].first()
  df_modeled_aggregate_Wateryear['Date'] = df_modeled.groupby(by = 'Wateryear')['Date'].first()
  df_modeled_aggregate_Wateryear.index = df_modeled_aggregate_Wateryear['Date']

  # get aggregated deliveries - monthly
  df_modeled['Wateryear__Month'] = df_modeled.Wateryear.map(int).map(str) + '__' + df_modeled.Month.map(int).map(str)
  df_modeled_aggregate_Wateryear_Month = df_modeled.groupby(by = 'Wateryear__Month').sum()
  df_modeled_aggregate_Wateryear_Month['Wateryear'] = df_modeled.groupby(by = 'Wateryear__Month')['Wateryear'].first()
  df_modeled_aggregate_Wateryear_Month['Month'] = df_modeled.groupby(by = 'Wateryear__Month')['Month'].first()
  df_modeled_aggregate_Wateryear_Month['Date'] = df_modeled.groupby(by = 'Wateryear__Month')['Date'].first()
  df_modeled_aggregate_Wateryear_Month = df_modeled_aggregate_Wateryear_Month.sort_values('Date')
  df_modeled_aggregate_Wateryear_Month.index = df_modeled_aggregate_Wateryear_Month['Date']


  return (df_modeled_aggregate_Wateryear, df_modeled_aggregate_Wateryear_Month, friant_districts, source_modeled, districts_modeled, WT_modeled)






def load_leiu_data(datafile):

  ### Read in modeled daily district delivery data
  df_modeled = pd.read_csv(datafile, index_col=0, parse_dates=True)

  df_modeled['Date__'] = df_modeled.index
  df_modeled['Year__'] = df_modeled.index.year
  df_modeled['Month__'] = df_modeled.index.month
  df_modeled['Wateryear__'] = df_modeled.Year__
  df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] = df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] + 1

  ### get banker & bankee
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])

  ### entries are stacked for each banker - difference across bankees to get individual balances
  for b in banker_modeled.unique()[:-4]:
    ind = np.where(banker_modeled == b)[0]
    if (len(ind) > 1):
      for i in np.arange(len(ind)-1, 0, -1):
        df_modeled.iloc[:,ind[i]] = df_modeled.iloc[:,ind[i]] - df_modeled.iloc[:,ind[i-1]]


  # only keep if actually used over simulation
  df_modeled.iloc[:,:-4] = df_modeled.iloc[:,:-4].loc[:, (df_modeled.iloc[:,:-4].max(axis=0)>0)]
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])

  # remove 'rate' columns
  df_modeled = df_modeled.loc[:, bankee_modeled != 'rate']
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])

  ### only keep friant bankees, and bankers w/ friant bankees
  # friant_districts = ['COF', 'FRS', 'OFK', 'TUL','KWD', 'OKW', 'EXE', 'LDS', 'LND', 'PRT', 'LWT',
  #      'OTL', 'TPD', 'SAU', 'TBA', 'OXV', 'PIX','DLE', 'KRT', 'SSJ', 'SFW', 'NKN',
  #      'NKB', 'ARV','']
  friant_banks = ['LWT', 'ARV', 'RRB', '']
  df_modeled = df_modeled.loc[:, ((banker_modeled=='RRB')|(banker_modeled=='ARV')|(banker_modeled=='LWT')|(bankee_modeled==''))]
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])

  # bank balances are cumulative across water years, so difference to get change in balances
  ind = np.where(WT_modeled == 'leiu')[0]
  for i in ind:
    df_modeled.iloc[1:, i] = np.diff(df_modeled.iloc[:, i])

  df_modeled['Date'] = df_modeled['Date__']
  df_modeled['Month'] = df_modeled['Month__']
  df_modeled['Wateryear'] = df_modeled['Wateryear__']
  del df_modeled['Date__'], df_modeled['Year__'], df_modeled['Month__'], df_modeled['Wateryear__']



  # get aggregated deliveries - annual
  df_modeled_aggregate_Wateryear = df_modeled.groupby(by = 'Wateryear').sum()
  df_modeled_aggregate_Wateryear['Wateryear'] = df_modeled.groupby(by = 'Wateryear')['Wateryear'].first()
  df_modeled_aggregate_Wateryear['Date'] = df_modeled.groupby(by = 'Wateryear')['Date'].first()
  df_modeled_aggregate_Wateryear.index = df_modeled_aggregate_Wateryear['Date']

  # get aggregated deliveries - monthly
  df_modeled['Wateryear__Month'] = df_modeled.Wateryear.map(int).map(str) + '__' + df_modeled.Month.map(int).map(str)
  df_modeled_aggregate_Wateryear_Month = df_modeled.groupby(by = 'Wateryear__Month').sum()
  df_modeled_aggregate_Wateryear_Month['Wateryear'] = df_modeled.groupby(by = 'Wateryear__Month')['Wateryear'].first()
  df_modeled_aggregate_Wateryear_Month['Month'] = df_modeled.groupby(by = 'Wateryear__Month')['Month'].first()
  df_modeled_aggregate_Wateryear_Month['Date'] = df_modeled.groupby(by = 'Wateryear__Month')['Date'].first()
  df_modeled_aggregate_Wateryear_Month = df_modeled_aggregate_Wateryear_Month.sort_values('Date')
  df_modeled_aggregate_Wateryear_Month.index = df_modeled_aggregate_Wateryear_Month['Date']

  return (df_modeled_aggregate_Wateryear, df_modeled_aggregate_Wateryear_Month, banker_modeled, bankee_modeled)




def load_bank_data(datafile):

  ### Read in modeled daily district delivery data
  df_modeled = pd.read_csv(datafile, index_col=0, parse_dates=True)

  df_modeled['Date__'] = df_modeled.index
  df_modeled['Year__'] = df_modeled.index.year
  df_modeled['Month__'] = df_modeled.index.month
  df_modeled['Wateryear__'] = df_modeled.Year__
  df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] = df_modeled.Wateryear__.loc[df_modeled.Month__ > 9] + 1


  ### get banker & bankee
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])


  ### entries are stacked for each banker - difference across bankees to get individual balances
  for b in banker_modeled.unique()[:-4]:
    ind = np.where(banker_modeled == b)[0]
    if (len(ind) > 1):
      for i in np.arange(len(ind)-1, 0, -1):
        df_modeled.iloc[:,ind[i]] = df_modeled.iloc[:,ind[i]] - df_modeled.iloc[:,ind[i-1]]


  # only keep if actually used over simulation
  df_modeled.iloc[:,:-4] = df_modeled.iloc[:,:-4].loc[:, (df_modeled.iloc[:,:-4].max(axis=0)>0)]
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])

  # remove 'rate' columns
  df_modeled = df_modeled.loc[:, bankee_modeled!='rate']
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])

  ### only keep bankers w/ friant bankees
  # friant_districts = ['COF', 'FRS', 'OFK', 'TUL','KWD', 'OKW', 'EXE', 'LDS', 'LND', 'PRT', 'LWT',
  #      'OTL', 'TPD', 'SAU', 'TBA', 'OXV','PIX', 'DLE', 'KRT', 'SSJ', 'SFW', 'NKN',
  #      'NKB', 'ARV','']
  df_modeled = df_modeled.loc[:, ((banker_modeled=='POSO')|(banker_modeled=='NKB')|(banker_modeled=='R21')|(bankee_modeled==''))]
  banker_modeled = df_modeled.columns.map(lambda x: x.split('_')[0])
  bankee_modeled = df_modeled.columns.map(lambda x: x.split('_')[1])
  WT_modeled = df_modeled.columns.map(lambda x: x.split('_')[-1])


  # bank balances are cumulative across water years, so difference to get change in balances
  ind = np.where(WT_modeled != '')[0]
  for i in ind:
    df_modeled.iloc[1:, i] = np.diff(df_modeled.iloc[:, i])

  df_modeled['Date'] = df_modeled['Date__']
  df_modeled['Month'] = df_modeled['Month__']
  df_modeled['Wateryear'] = df_modeled['Wateryear__']
  del df_modeled['Year__'], df_modeled['Month__'], df_modeled['Wateryear__']

  # get aggregated deliveries - annual
  df_modeled_aggregate_Wateryear = df_modeled.groupby(by = 'Wateryear').sum()
  df_modeled_aggregate_Wateryear['Wateryear'] = df_modeled.groupby(by = 'Wateryear')['Wateryear'].first()
  df_modeled_aggregate_Wateryear['Date'] = df_modeled.groupby(by = 'Wateryear')['Date'].first()
  df_modeled_aggregate_Wateryear.index = df_modeled_aggregate_Wateryear['Date']

  # get aggregated deliveries - monthly
  df_modeled['Wateryear__Month'] = df_modeled.Wateryear.map(int).map(str) + '__' + df_modeled.Month.map(int).map(str)
  df_modeled_aggregate_Wateryear_Month = df_modeled.groupby(by = 'Wateryear__Month').sum()
  df_modeled_aggregate_Wateryear_Month['Wateryear'] = df_modeled.groupby(by = 'Wateryear__Month')['Wateryear'].first()
  df_modeled_aggregate_Wateryear_Month['Month'] = df_modeled.groupby(by = 'Wateryear__Month')['Month'].first()
  df_modeled_aggregate_Wateryear_Month['Date'] = df_modeled.groupby(by = 'Wateryear__Month')['Date'].first()
  df_modeled_aggregate_Wateryear_Month = df_modeled_aggregate_Wateryear_Month.sort_values('Date')
  df_modeled_aggregate_Wateryear_Month.index = df_modeled_aggregate_Wateryear_Month.Date


  return (df_modeled_aggregate_Wateryear, df_modeled_aggregate_Wateryear_Month, banker_modeled, bankee_modeled)


