import numpy as np
import pandas as pd
# import h5py
import json
import sys
import matplotlib.pyplot as plt
from calfews_src.util import get_results_sensitivity_number_outside_model

model = sys.argv[1] 
rcp = sys.argv[2]  

scenario = model + '_rcp' + rcp 

### get ownership shares for each scenario
base_dir = '/pine/scr/a/l/alh91/CALFEWS_results/climate_ensemble/'


### read in data & organize datetimes
def get_reservoir_data(datafile):
  dat = get_results_sensitivity_number_outside_model(datafile, '')
  keys = list(dat.keys())
  l1 = []
  for obj in ['shasta','oroville','yuba','folsom','newmelones','donpedro','exchequer','sanluisstate','sanluisfederal',\
                'millerton','pineflat','kaweah','success','isabella','delta']:
    l1 += [k for k in keys if obj in k.split('_')]
  l2 = []
  for att in ['S','R','Q','SNPK','downstream','fnf','outflow','pump','eastside','gains','depletions','OMR','uncontrolled','x2']:
    l2 += [k for k in l1 if att in k.split('_')]

  df = dat.loc[:, l2]

  return df



df = get_reservoir_data(base_dir + scenario + '/results.hdf5')

df.to_csv(base_dir + scenario + '/' + scenario + '_results.csv')

