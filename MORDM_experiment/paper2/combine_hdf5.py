import h5py
import sys

results = sys.argv[1]
solns = [96]#[50,95,96] #range(99)

with h5py.File(f'{results}results.hdf5', 'a') as f_new:
    for soln in solns:
        for total_rank, sample_set in zip((288, 132), ('du_1', 'du_2')):
            for rank in range(total_rank):
                with h5py.File(f'{results}/infra_{sample_set}/soln{soln}/results_rank{rank}.hdf5', 'r') as f_old:
                    keys = f_old.keys()
                    for k in keys:
                        k_new = f'soln{soln}/{sample_set}/{k}'
                        f_new.create_dataset(k_new, data=f_old[k])
                        for a in f_old[k].attrs.keys():
                            f_new[k_new].attrs[a] = f_old[k].attrs[a]

