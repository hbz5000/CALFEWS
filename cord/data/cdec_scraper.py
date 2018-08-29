import numpy as np
import pandas as pd 
from ulmo.cdec import historical as cd

# first get daily FNF
# first 8 are the 8-river index
# first 4 are the SRI and SR WYT
# http://cdec.water.ca.gov/cgi-progs/staSearch?sta=&sensor_chk=on&sensor=8
cfs_tafd = 2.29568411*10**-5 * 86400 / 1000

df = pd.DataFrame()
sd = '10-01-1999' # reliable start for CDEC daily data
ids = ['BND', 'ORO', 'YRS', 'FOL', 'NML', 'TLG', 'MRC', 'MIL']
       # 'GDW', 'MHB', 'MKM', 'NHG', 'SHA']
data = cd.get_data(station_ids=ids, sensor_ids=[8], 
                   resolutions=['daily'], start=sd)

for k in ids:
  df[k + '_fnf'] = data[k]['FULL NATURAL FLOW daily']['value']

# flowrates: inflow / outflow / evap / pumping
ids = ['SHA', 'ORO', 'FOL']#, 'CLE', 'NML', 'DNP', 'EXC', 'MIL', 'SNL']

data = cd.get_data(station_ids=ids, sensor_ids=[15,23,74,76,94,45], 
                   resolutions=['daily'], start=sd)

for k in ids:
  df[k + '_in'] = data[k]['RESERVOIR INFLOW daily']['value']
  df[k + '_out'] = data[k]['RESERVOIR OUTFLOW daily']['value']
  df[k + '_storage'] = data[k]['RESERVOIR STORAGE daily']['value'] / 1000 # TAF
  df[k + '_evap'] = data[k]['EVAPORATION, LAKE COMPUTED CFS daily']['value']
  df[k + '_tocs_obs'] = data[k]['RESERVOIR, TOP CONSERV STORAGE daily']['value'] / 1000
  df[k + '_precip'] = data[k]['PRECIPITATION, INCREMENTAL daily']['value']
  # fix mass balance problems in inflow
  df[k + '_in_fix'] = df[k+'_storage'].diff()/cfs_tafd + df[k+'_out'] + df[k+'_evap']

# observed delta outflow
data = cd.get_data(['DTO'], [23], ['daily'], start=sd)
df['DeltaOut'] = data['DTO']['RESERVOIR OUTFLOW daily']['value']

# banks & tracy pumping
ids = ['HRO', 'TRP']
data = cd.get_data(ids, [70], ['daily'], start=sd)
for k in ids:
  df[k + '_pump'] = data[k]['DISCHARGE, PUMPING daily']['value']

# estimate delta inflow from this (ignores GCD and direct precip)
df['DeltaIn'] = df['DeltaOut'] + df['HRO_pump'] + df['TRP_pump']

# other reservoirs for folsom flood control index
ids = ['FMD','UNV','HHL']

data = cd.get_data(station_ids=ids, sensor_ids=[15], 
                   resolutions=['daily'], start=sd)

for k in ids:
  df[k + '_storage'] = data[k]['RESERVOIR STORAGE daily']['value'] / 1000 # TAF

# oroville release from thermalito instead?
# no -- there is a canal diversion that isn't accounted for.
# data = cd.get_data(['THA'], [85], ['daily'], start=sd)
# df['THA_out'] = data['THA']['DISCHARGE,CONTROL REGULATING daily']['value']

# cleanup
df[df < 0] = np.nan
df.interpolate(inplace=True)
df.to_csv('cord-data.csv')
