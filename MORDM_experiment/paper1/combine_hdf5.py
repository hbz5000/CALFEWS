import h5py
import sys

results = sys.argv[1]

with h5py.File(f'{results}results.hdf5', 'a') as f_new:
    for rank in range(192):
        with h5py.File(f'{results}results_rank{rank}.hdf5', 'r') as f_old:
            keys = f_old.keys()
            for k in keys:
                f_new.create_dataset(k, data=f_old[k])
                for a in f_old[k].attrs.keys():
                    f_new[k].attrs[a] = f_old[k].attrs[a]

