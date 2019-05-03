import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import cm


def load_canal_data(datafile):
  ### read in results from different scenarios
  # canal & turnout flows
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

  # # get aggregated deliveries - aggregate months across years
  # canal_aggregate_Month = canal.groupby(by = 'Month').sum()
  # canal_aggregate_Month['Wateryear'] = canal.groupby(by = 'Month')['Wateryear'].first()
  # canal_aggregate_Month['Month'] = canal.groupby(by = 'Month')['Month'].first()
  # canal_aggregate_Month['Date'] = canal.groupby(by = 'Month')['Date'].first()
  # canal_aggregate_Month = canal_aggregate_Month.sort_values('Date')

  return (canal, canal_aggregate_Wateryear, canal_aggregate_Wateryear_Month, ind_canal_waterway, ind_canal_recipient, ind_canal_flowtype)






