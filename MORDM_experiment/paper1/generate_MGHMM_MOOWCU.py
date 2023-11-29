import numpy as np
import pandas as pd
import h5py
from calfews_src.util import MGHMM_generate_trace 
import sys
from datetime import datetime

start_time = datetime.now()

### results folder and number of MC samples & DU samples from command line
MGHMMdir = 'calfews_src/data/MGHMM_synthetic/'
filestart = 'DailyQ_s'
fileend = '.csv'
numMC = 100

### uncertainties. these are all set to baseline value for MOO/WCU experiment (as opposed to DU experiment to come in next paper)
udict = {'dry_state_mean_multiplier': 1, 'wet_state_mean_multiplier': 1,\
         'covariance_matrix_dry_multiplier': 1, 'covariance_matrix_wet_multiplier': 1, \
         'transition_drydry_addition': 0, 'transition_wetwet_addition': 0}
#### number of years for synthetic generation. Note this is one more than we will simulate, since this does calendar year but calfews cuts to water year.
nYears = 31

### loop over MC samples & create a new synthetic trace for each, using MC number as seed
for mc in range(numMC):
  udict['synth_gen_seed'] = mc
  df = MGHMM_generate_trace(nYears, udict, drop_date=False)
  df.to_csv(MGHMMdir + filestart + str(mc) + fileend, index=False)

