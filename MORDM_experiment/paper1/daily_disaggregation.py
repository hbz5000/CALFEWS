# -*- coding: utf-8 -*-
"""
Created on Sat Jan  8 11:23:00 2022

@author: Rohini
"""

#Import Libraries 

import pandas as pd
import numpy as np
import os
from pandas.testing import assert_frame_equal


### read in pre-normalized data
calfews_data=pd.read_csv("./mhmm_data/calfews_src-data-sim-agg_norm.csv")

yearly_sum=calfews_data.groupby(['Year']).sum()
yearly_sum=yearly_sum.reset_index()

#Import synthetic and historic annual flows

AnnualQ_s=pd.read_csv("./mhmm_data/AnnualQ_s.csv",header=None)
AnnualQ_h=pd.read_csv("./mhmm_data/AnnualQ_h.csv",header=None)

#Identify number of years in synthetic & historical sample
N_s=len(AnnualQ_s)
N_h=len(AnnualQ_h)

#Find closest year for each synthetic sample
index=np.zeros(N_s)

for j in range(0, N_s):
    distance=np.zeros(N_h)
    for i in range(0,N_h):
       distance[i]=(AnnualQ_s.iloc[j,0]-AnnualQ_h.iloc[i,0])**2 
    index[j]=np.argmin(distance)  

#Assign year to the index
closest_year=yearly_sum.Year[index]
closest_year=closest_year.reset_index()
closest_year=closest_year.iloc[:,1]

#Disaggregate to a daily value 
DailyQ_s=calfews_data
DailyQ_s=DailyQ_s[DailyQ_s.Year < DailyQ_s.Year[0] + N_s]



count=0

for i in range(0,N_s):
  y=np.unique(DailyQ_s.Year)[i]
  index_array=np.where(DailyQ_s.Year==np.unique(DailyQ_s.Year)[i])[0]
  newdata=DailyQ_s[DailyQ_s.index.isin(index_array)]
  newdatasize=np.shape(newdata)[0]
  olddata_array=np.where(calfews_data.Year==closest_year[i])[0]
  olddata=calfews_data[calfews_data.index.isin(olddata_array)]
  olddata=olddata.reset_index()
  olddata=olddata.iloc[:,1:20]
  for z in range(4,19):
    olddata.iloc[:,z]=AnnualQ_s.iloc[i,z-4]*olddata.iloc[:,z].values
  ## fill in data, accounting for leap years. assume leap year duplicates feb 29
  if newdatasize == 365:
    if np.shape(olddata)[0] == 365:
      DailyQ_s.iloc[count:(count+365),4:19]=olddata.iloc[:,4:19].values
    elif np.shape(olddata)[0] == 366:
      # if generated data has 365 days, and disaggregating 366-day series, skip feb 29 (60th day of leap year)
      DailyQ_s.iloc[count:(count+59),4:19]=olddata.iloc[0:59,4:19].values
      DailyQ_s.iloc[(count+60-1):(count+365),4:19]=olddata.iloc[60:366,4:19].values
    
  elif newdatasize == 366:
    if np.shape(olddata)[0] == 366:
      DailyQ_s.iloc[count:(count+366),4:19]=olddata.iloc[:,4:19].values
    elif np.shape(olddata)[0] == 365:
      # if generated data has 366 days, and disaggregating 365-day series, repeat feb 28 (59rd day of leap year)
      DailyQ_s.iloc[count:(count+59),4:19]=olddata.iloc[0:59,4:19].values
      DailyQ_s.iloc[count+60-1,4:19]=olddata.iloc[58,4:19].values
      DailyQ_s.iloc[(count+61-1):(count+366-1),4:19]=olddata.iloc[59:364,4:19].values
  count=count+len(olddata)


DailyQ_s.to_csv('./mhmm_data/DailyQ_s.csv', index=False)













