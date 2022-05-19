# -*- coding: utf-8 -*-
"""
Created on Wed May 11 14:29:08 2022

@author: Rohini Gupta, Andrew Hamilton
"""
import numpy as np
from random import random
import pandas as pd
import sys

#Import LHS Sample - input line of LHS sample to use as command line arg, zero - indexed
LHS_sample_num = int(sys.argv[1])    
LHS = np.loadtxt('LHsamples_broad_64.txt', skiprows = LHS_sample_num, max_rows = 1)

#Static Parameters
nYears = 30
nSites = 15


#Import stationary parameters
dry_state_means = np.loadtxt('dry_state_means.txt')
wet_state_means = np.loadtxt('wet_state_means.txt')
covariance_matrix_dry = np.loadtxt('covariance_matrix_dry.txt')
covariance_matrix_wet = np.loadtxt('covariance_matrix_wet.txt')
transition_matrix = np.loadtxt('transition_matrix.txt')


#Apply mean multipliers
dry_state_means_sampled = dry_state_means * LHS[0]
wet_state_means_sampled = wet_state_means * LHS[2]

#Apply covariance multipliers
covariance_matrix_dry_sampled = covariance_matrix_dry * LHS[1]

for j in range(nSites):
    covariance_matrix_dry_sampled[j, j] = covariance_matrix_dry_sampled[j, j] * LHS[1]

covariance_matrix_wet_sampled = covariance_matrix_wet * LHS[3]

for j in range(nSites):
    covariance_matrix_wet_sampled[j, j] = covariance_matrix_wet_sampled[j, j] * LHS[3]

#Apply transition matrix multipliers
transition_matrix_sampled = transition_matrix
transition_matrix_sampled[0, 0] = transition_matrix[0, 0] + LHS[4]
transition_matrix_sampled[1, 1] = transition_matrix[1, 1] + LHS[5]
transition_matrix_sampled[0, 1] = 1 - transition_matrix_sampled[0, 0]
transition_matrix_sampled[1, 0] = 1 - transition_matrix_sampled[1, 1]

# calculate stationary distribution to determine unconditional probabilities
eigenvals, eigenvecs = np.linalg.eig(np.transpose(transition_matrix_sampled))
one_eigval = np.argmin(np.abs(eigenvals - 1))
pi = eigenvecs[:, one_eigval] / np.sum(eigenvecs[:, one_eigval])
unconditional_dry = pi[0]
unconditional_wet = pi[1]

logAnnualQ_s = np.zeros([nYears, nSites])

states = np.empty([np.shape(logAnnualQ_s)[0]])
if random() <=  unconditional_dry:
    states[0] = 0
    logAnnualQ_s[0, :] = np.random.multivariate_normal(np.reshape(dry_state_means_sampled, -1), covariance_matrix_dry_sampled)
else:
    states[0] = 1
    logAnnualQ_s[0, :] = np.random.multivariate_normal(np.reshape(wet_state_means_sampled, -1), covariance_matrix_wet_sampled)

# generate remaining state trajectory and log space flows
for j in range(1, np.shape(logAnnualQ_s)[0]):
    if random() <=  transition_matrix_sampled[int(states[j - 1]), int(states[j - 1])]:
        states[j] = states[j - 1]
    else:
        states[j] = 1 - states[j - 1]

    if states[j] ==  0:
        logAnnualQ_s[j, :] = np.random.multivariate_normal(np.reshape(dry_state_means_sampled, -1), covariance_matrix_dry_sampled)
    else:
        logAnnualQ_s[j, :] = np.random.multivariate_normal(np.reshape(wet_state_means_sampled, -1), covariance_matrix_wet_sampled)

AnnualQ_s = np.exp(logAnnualQ_s)

#############################################Daily Disaggregation######################

### read in pre - normalized data
calfews_data = pd.read_csv("calfews_src-data-sim-agg_norm.csv")

yearly_sum = calfews_data.groupby(['Year']).sum()
yearly_sum = yearly_sum.reset_index()

#Import historic annual flows
AnnualQ_h = pd.read_csv("AnnualQ_h.csv", header = None)

#Identify number of years in synthetic & historical sample
N_s = len(AnnualQ_s)
N_h = len(AnnualQ_h)

#Find closest year for each synthetic sample
index = np.zeros(N_s)

for j in range(0, N_s):
    distance = np.zeros(N_h)
    for i in range(0, N_h):
       distance[i] = (AnnualQ_s[j, 0] - AnnualQ_h.iloc[i, 0]) ** 2
    index[j] = np.argmin(distance)

#Assign year to the index
closest_year = yearly_sum.Year[index]
closest_year = closest_year.reset_index()
closest_year = closest_year.iloc[:, 1]

#Disaggregate to a daily value
DailyQ_s = calfews_data
DailyQ_s = DailyQ_s[DailyQ_s.Year < DailyQ_s.Year[0] + N_s]

count = 0
for i in range(0, N_s):
  y = np.unique(DailyQ_s.Year)[i]
  index_array = np.where(DailyQ_s.Year == np.unique(DailyQ_s.Year)[i])[0]
  newdata = DailyQ_s[DailyQ_s.index.isin(index_array)]
  newdatasize = np.shape(newdata)[0]
  olddata_array = np.where(calfews_data.Year == closest_year[i])[0]
  olddata = calfews_data[calfews_data.index.isin(olddata_array)]
  olddata = olddata.reset_index()
  olddata = olddata.iloc[:, 1:20]
  for z in range(4, 19):
    olddata.iloc[:, z] = AnnualQ_s[i, z - 4] * olddata.iloc[:, z].values
  ## fill in data, accounting for leap years. assume leap year duplicates feb 29
  if newdatasize ==  365:
    if np.shape(olddata)[0] ==  365:
      DailyQ_s.iloc[count:(count + 365), 4:19] = olddata.iloc[:, 4:19].values
    elif np.shape(olddata)[0] ==  366:
      # if generated data has 365 days, and disaggregating 366 - day series, skip feb 29 (60th day of leap year)
      DailyQ_s.iloc[count:(count + 59), 4:19] = olddata.iloc[0:59, 4:19].values
      DailyQ_s.iloc[(count + 60 - 1):(count + 365), 4:19] = olddata.iloc[60:366, 4:19].values

  elif newdatasize ==  366:
    if np.shape(olddata)[0] ==  366:
      DailyQ_s.iloc[count:(count + 366), 4:19] = olddata.iloc[:, 4:19].values
    elif np.shape(olddata)[0] ==  365:
      # if generated data has 366 days, and disaggregating 365 - day series, repeat feb 28 (59rd day of leap year)
      DailyQ_s.iloc[count:(count + 59), 4:19] = olddata.iloc[0:59, 4:19].values
      DailyQ_s.iloc[count + 60 - 1, 4:19] = olddata.iloc[58, 4:19].values
      DailyQ_s.iloc[(count + 61 - 1):(count + 366 - 1), 4:19] = olddata.iloc[59:364, 4:19].values
  count = count + len(olddata)

DailyQ_s.to_csv('DailyQ_s.csv', index = False)


