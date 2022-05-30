import numpy as np
import pandas as pd
import h5py
from calfews_src.util import MGHMM_generate_trace 
import sys
from datetime import datetime

start_time = datetime.now()

### results folder and number of MC samples & DU samples from command line
results = sys.argv[1]
numMC = int(sys.argv[2])
numDU = int(sys.argv[3])

### uncertainties
dunames = ['dry_state_mean_multiplier', 'wet_state_mean_multiplier', 'covariance_matrix_dry_multiplier',
           'covariance_matrix_wet_multiplier', 'transition_drydry_addition', 'transition_wetwet_addition']
### number of years for synthetic generation. Note this is one more than we will simulate, since this does calendar year but calfews cuts to water year.
nYears = 31

### load DU samples from LHC
LHC = pd.read_csv('calfews_src/data/LHC_DU/LHC_DU.csv')

### loop over DU samples & MC samples, store each hierarchically
with h5py.File(f'{results}/mghmm_du.hdf5', 'a') as hf:

  for ui in range(numDU):
    udict = {c: LHC[c].iloc[ui] for c in dunames}

    g = hf.create_group(f'du{ui}')

    for mc in range(numMC):
      udict['synth_gen_seed'] = mc
      df = MGHMM_generate_trace(nYears, udict)
      d = hf.create_dataset(f'du{ui}/mc{mc}', data=df, dtype='float', compression='gzip')
      seed = udict.pop('synth_gen_seed')
    g.attrs['dusamps'] = list(udict.values())
    print('finished du ', ui, datetime.now() - start_time)
    sys.stdout.flush()

  hf.attrs['colnames'] = list(df.columns)
  hf.attrs['dunames'] = dunames
