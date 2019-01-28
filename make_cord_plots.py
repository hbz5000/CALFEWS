import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cord import *

######################################################################################
###Plot Simulation Results
######################################################################################
# res_results_no = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master_01142019/validation/reservoir_results_no_validation.csv', index_col=0, parse_dates=True)
# res_results_so = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master_01142019/validation/reservoir_results_so_validation.csv', index_col=0, parse_dates=True)
# district_results = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master_01142019/validation/master_district_results_validation.csv')
# waterbank_results = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master_01142019/validation/bank_results_validation.csv')
# leiubank_results = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master_01142019/validation/leiu_results_validation.csv')

res_results_no = pd.read_csv('cord/data/results/reservoir_results_no_validation.csv', index_col=0, parse_dates=True)
res_results_so = pd.read_csv('cord/data/results/reservoir_results_so_validation.csv', index_col=0, parse_dates=True)
district_results = pd.read_csv('cord/data/results/district_results_validation.csv')
waterbank_results = pd.read_csv('cord/data/results/bank_results_validation.csv')
leiubank_results = pd.read_csv('cord/data/results/leiu_results_validation.csv')

observations = pd.read_csv('cord/data/input/cord-data.csv', index_col=0, parse_dates=True)

#calibration points (lists of pandas series)
sim = [res_results_no['DEL_HRO_pump'] / cfs_tafd,
       res_results_no['DEL_TRP_pump'] / cfs_tafd,
       res_results_no['SHA_storage'] * 1000.0,
       res_results_no['SHA_out'] / cfs_tafd,
       res_results_no['FOL_storage'] * 1000.0,
       res_results_no['FOL_out'] / cfs_tafd,
       res_results_no['ORO_storage'] * 1000.0,
       res_results_no['ORO_out'] / cfs_tafd,
       res_results_no['YRS_storage'] * 1000.0,
       res_results_no['NML_storage'] * 1000.0,
       res_results_no['DNP_storage'] * 1000.0,
       res_results_no['EXC_storage'] * 1000.0,
       res_results_so['ISB_storage'] * 1000.0,
       res_results_so['SLF_storage'] * 1000.0,
       res_results_so['SLS_storage'] * 1000.0,
       res_results_so['MIL_storage'] * 1000.0]

obs = [observations['HRO_pump'],
       observations['TRP_pump'],
       observations['SHA_storage'],
       observations['SHA_otf'],
       observations['FOL_storage'],
       observations['FOL_otf'],
       observations['ORO_storage'],
       observations['ORO_otf'],
       observations['YRS_storage'],
       observations['NML_storage'],
       observations['DNP_storage'],
       observations['EXC_storage'],
       observations['ISB_storage'],
       observations['SLF_storage'],
       observations['SLS_storage'],
       observations['MIL_storage']]

#for f in ['W','AS-OCT']:
i = 0
for s,o in zip(sim,obs):
  #plotter.compare(s, o, freq=f)
  if i == 0:
    data_name = 'SWP Pumping'
  else:
    data_name = 'CVP Pumping'
  plotter.compare(s, o, 'W', 'AS-OCT', data_name)
  #plt.savefig('cord/figs/%s%d.png' % (f,i), dpi=150)
  i += 1
#
# # results = pd.read_csv('cord/data/reservoir_results_so.csv', index_col=0, parse_dates=True)
# i = 0
# obs = [observations['ISB_storage'],
#        observations['SLF_storage'],
#        observations['SLS_storage'],
#        observations['MIL_storage']]
# res = [res_results_so['ISB_storage']*1000.0,
#        res_results_so['SLF_storage']*1000.0,
#        res_results_so['SLS_storage']*1000.0,
#        res_results_so['MIL_storage']*1000.0]
# for s,o in zip(res,obs):
#   a=1
#   plotter.compare(s, o, 'W', 'M')
#
#
# for x in ['HML', 'SMI', 'BLR', 'DLR', 'SOC']:
#
#   sim = [district_results['%s_recharge_uncontrolled' % x],
#          district_results['%s_recharge_delivery' % x],
#          district_results['%s_leiu_delivered' % x],
#          district_results['%s_pumping' % x],
#          district_results['%s_banked' % x],
#          district_results['%s_leiu_accepted' % x],
#          district_results['%s_delivery' % x],
#          np.zeros(len(district_results['%s_delivery' % x])),
#          district_results['%s_allocation' % x],
#          district_results['%s_carryover' % x],
#          district_results['%s_paper' % x]]
#   plotter.stack(sim, x)
#   plt.savefig('cord/figs/%s_%d.png' % (x,i), dpi=150)
#   i = i + 1
#
# modelplot = Model('cord/data/cord-data.csv', sd='10-01-1996')
# modelplot.initialize_water_districts()
# modelplot.initialize_water_banks()
#
# for x in modelplot.waterbank_list:
#   sim = {}
#   for y in x.participant_list:
#     sim[y] = waterbank_results['%s_%s' %(x.key, y)]
#   plotter.waterbank_storage(sim, x.participant_list, x.key)
# for x in modelplot.leiu_list:
#   sim = {}
#   for y in x.participant_list:
#     sim[y] = leiubank_results['%s_%s_leiu' %(x.key, y)]
#   plotter.waterbank_storage(sim,x.participant_list, x.key)
