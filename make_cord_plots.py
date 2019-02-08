import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cord import *

######################################################################################
###Plot Simulation Results
######################################################################################
# plot validation mode (1) or simulation mode (0)
validation_plots = 1

# set plot number to number from results lists below, or -1 to plot all
plot_number = -1

observations = pd.read_csv('cord/data/input/cord-data.csv', index_col=0, parse_dates=True)

# Note: change file paths to local storage. 'old' should be a previous run of results with an old branch of code, and 'new' is the results from the new code being tested.
if validation_plots:
       res_results_no_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/validation_01142019/reservoir_results_no_validation.csv', index_col=0, parse_dates=True)
       res_results_so_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/validation_01142019/reservoir_results_so_validation.csv', index_col=0, parse_dates=True)
       # district_results_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/validation_01292019/master_district_results_validation.csv')
       # waterbank_results_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/validation_01292019/bank_results_validation.csv')
       # leiubank_results_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/validation_01292019/leiu_results_validation.csv')

       res_results_no_new = pd.read_csv('cord/data/results/reservoir_results_no_validation.csv', index_col=0, parse_dates=True)
       res_results_so_new = pd.read_csv('cord/data/results/reservoir_results_so_validation.csv', index_col=0, parse_dates=True)
       # district_results_new = pd.read_csv('cord/data/results/district_results_validation.csv')
       # waterbank_results_new = pd.read_csv('cord/data/results/bank_results_validation.csv')
       # leiubank_results_new = pd.read_csv('cord/data/results/leiu_results_validation.csv')

else:
       # res_results_no_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/simulation/reservoir_results_no_simulation.csv', index_col=0, parse_dates=True)
       # res_results_so_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/simulation/reservoir_results_so_simulation.csv', index_col=0, parse_dates=True)
       # district_results_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/simulation/district_results_simulation.csv')
       # waterbank_results_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/simulation/bank_results_simulation.csv')
       # leiubank_results_old = pd.read_csv('../../Documents/DataFilesNonGit/ORCA_master/simulation/leiu_results_simulation.csv')

       res_results_no_old = pd.read_csv('cord/data/results/reservoir_results_no_simulation_validation.csv', index_col=0,
                                        parse_dates=True)
       res_results_so_old = pd.read_csv('cord/data/results/reservoir_results_so_simulation_validation.csv', index_col=0,
                                        parse_dates=True)
       res_results_no_new = pd.read_csv('cord/data/results/reservoir_results_no_simulation.csv', index_col=0, parse_dates=True)
       res_results_so_new = pd.read_csv('cord/data/results/reservoir_results_so_simulation.csv', index_col=0, parse_dates=True)
       # district_results_new = pd.read_csv('cord/data/results/district_results_simulation.csv')
       # waterbank_results_new = pd.read_csv('cord/data/results/bank_results_simulation.csv')
       # leiubank_results_new = pd.read_csv('cord/data/results/leiu_results_simulation.csv')

# columns for results files ***make sure these match the corresponding columns in observations***
columns = ['DEL_HRO_pump',
           'DEL_TRP_pump',
           'SHA_storage',
           'SHA_out',
           'FOL_storage',
           'FOL_out',
           'ORO_storage',
           'ORO_out',
           'YRS_storage',
           'NML_storage',
           'DNP_storage',
           'EXC_storage',
           'ISB_storage',
           'MIL_storage',
           'SLF_storage',
           'SLS_storage']

#calibration points (lists of pandas series)
sim_old = [
       res_results_no_old[columns[0]] / cfs_tafd,
       res_results_no_old[columns[1]] / cfs_tafd,
       res_results_no_old[columns[2]] * 1000.0,
       res_results_no_old[columns[3]] / cfs_tafd,
       res_results_no_old[columns[4]] * 1000.0,
       res_results_no_old[columns[5]] / cfs_tafd,
       res_results_no_old[columns[6]] * 1000.0,
       res_results_no_old[columns[7]] / cfs_tafd,
       res_results_no_old[columns[8]] * 1000.0,
       res_results_no_old[columns[9]] * 1000.0,
       res_results_no_old[columns[10]] * 1000.0,
       res_results_no_old[columns[11]] * 1000.0,
       res_results_so_old[columns[12]] * 1000.0,
       res_results_so_old[columns[13]] * 1000.0,
       res_results_so_old[columns[14]] * 1000.0,
       res_results_so_old[columns[15]] * 1000.0
       ]

sim_new = [
       res_results_no_new[columns[0]] / cfs_tafd,
       res_results_no_new[columns[1]] / cfs_tafd,
       res_results_no_new[columns[2]] * 1000.0,
       res_results_no_new[columns[3]] / cfs_tafd,
       res_results_no_new[columns[4]] * 1000.0,
       res_results_no_new[columns[5]] / cfs_tafd,
       res_results_no_new[columns[6]] * 1000.0,
       res_results_no_new[columns[7]] / cfs_tafd,
       res_results_no_new[columns[8]] * 1000.0,
       res_results_no_new[columns[9]] * 1000.0,
       res_results_no_new[columns[10]] * 1000.0,
       res_results_no_new[columns[11]] * 1000.0,
       res_results_so_new[columns[12]] * 1000.0,
       res_results_so_new[columns[13]] * 1000.0,
       res_results_so_new[columns[14]] * 1000.0,
       res_results_so_new[columns[15]] * 1000.0
       ]

obs = [
       observations['HRO_pump'],
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
       observations['MIL_storage'],
       observations['SLF_storage'],
       observations['SLS_storage'],
       ]


if validation_plots:
       if plot_number > 0:
              for s_old, s_new, o, name in zip([sim_old[plot_number]], [sim_new[plot_number]], [obs[plot_number]], [columns[plot_number]]):
                     plotter.compare_validation(s_old, s_new, o, name, 'D', 'AS-OCT', 'level')
                     plt.savefig('cord/figs/validation_%s.png' % (name), dpi=150)

       else:
              for s_old, s_new, o, name in zip(sim_old,sim_new,obs, columns):
                     plotter.compare_validation(s_old, s_new, o, name, 'D', 'AS-OCT', 'level')
                     plt.savefig('cord/figs/validation_%s.png' % (name), dpi=150)
else:
       if plot_number > 0:
              for s_old, s_new, o, name in zip([sim_old[plot_number]], [sim_new[plot_number]], [obs[plot_number]], [columns[plot_number]]):
                     plotter.compare_simulation(s_old, s_new, o, name, 'D', 'AS-OCT', 'level')
                     plt.savefig('cord/figs/simulation_%s.png' % (name), dpi=150)

       else:
              for s_old, s_new, o, name in zip(sim_old, sim_new, obs, columns):
                     plotter.compare_simulation(s_old, s_new, o, name, 'D', 'AS-OCT', 'level')
                     plt.savefig('cord/figs/simulation_%s.png' % (name), dpi=150)

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
