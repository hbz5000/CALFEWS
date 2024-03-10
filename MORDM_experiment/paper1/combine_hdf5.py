import h5py
import sys

results = sys.argv[1]

with h5py.File(f'{results}results.hdf5', 'a') as f_new:
    for seed in range(1, 5):
        for rank in range(16):
            with h5py.File(f'{results}/dv2_seed{seed}/results_rank{rank}.hdf5', 'r') as f_old:
                # indiv datasets have 2x as many rows as they should, with second half all zeros
                keys = f_old.keys()
                for k in keys:
                    num_rows = len(f_old[k].attrs['rownames'])
                    f_new.create_dataset(f's{seed}/{k}', data=f_old[k][:num_rows,:])
                    for a in f_old[k].attrs.keys():
                        f_new[f's{seed}/{k}'].attrs[a] = f_old[k].attrs[a]
    with h5py.File(f'{results}/statusquo/results_rank0.hdf5', 'r') as f_old:
        keys = f_old.keys()
        for k in keys:
            num_rows = len(f_old[k].attrs['rownames'])
            f_new.create_dataset(f'statusquo/{k}', data=f_old[k][:num_rows,:])
            for a in f_old[k].attrs.keys():
                f_new[f'statusquo/{k}'].attrs[a] = f_old[k].attrs[a]

