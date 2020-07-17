### When using parallel_mode, main.py will generate results spread across multiple folders, one for each processor.
# This file will combine the output from many hdf5 files into a single file.
# Program arguments are the base output folder, and the number of processors.
# e.g. run with:  "python consolidate_hdf5_climate_ensemble.py 'calfews_src/data/results/baseline_wy2019' 2"

import numpy as np
import sys
import os
import shutil
import h5py

output_directory = sys.argv[1]
num_processors = int(sys.argv[2])

with h5py.File(output_directory + '/results.hdf5', 'w') as f:
  for p in range(num_processors):
    file = output_directory + '/p' + str(p) + '/results_p' + str(p) + '.hdf5'
    with h5py.File(file, 'r') as g:
      datasets = list(g.keys())
      for dataset in datasets:
        if ((dataset in f.keys()) == False):
          d = f.create_dataset(dataset, g[dataset].shape, dtype='float', compression='gzip')
          d.attrs['columns'] = g[dataset].attrs['columns']
          if (g[dataset].attrs.__contains__('sensitivity_factors') == True):
            d.attrs['sensitivity_factors'] = g[dataset].attrs['sensitivity_factors']
            d.attrs['sensitivity_factor_values'] = g[dataset].attrs['sensitivity_factor_values']
          d[:] = g[dataset][:]
    os.remove(file)