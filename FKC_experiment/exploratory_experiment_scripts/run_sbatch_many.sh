#!/bin/bash

start_samples=0
end_samples=3034
runtime_base='runtime_params_FKC_experiment_'

### run script to get sampled infrastructure configurations
python3 get_FKC_participants.py 0 3035

for s in 'dry' 'median' 'wet'
do
  ### run baseline with no new infrastructure, for each hydro scenario
  runtime_file=${runtime_base}${s}.ini

  sed 's/namehere/'$s'_none/' sbatch_single_longleaf.sh > sbatch_single_longleaf_tmp.sh
  sed -i 's/outhere/out_'$s'_none.txt/' sbatch_single_longleaf_tmp.sh
  sed -i 's/errhere/err_'$s'_none.txt/' sbatch_single_longleaf_tmp.sh
  sbatch sbatch_single_longleaf_tmp.sh 1 0 0 $runtime_file

  ### now run infrastructure scenarios, each as its own process
  for i in $(seq $start_samples $end_samples )
  do
    i2=$(expr $i + 1)
    sed 's/namehere/'$s'_'$i'/' sbatch_single_longleaf.sh > sbatch_single_longleaf_tmp.sh
    sed -i 's/outhere/out_'$s'_'$i'.txt/' sbatch_single_longleaf_tmp.sh
    sed -i 's/errhere/err_'$s'_'$i'.txt/' sbatch_single_longleaf_tmp.sh
    sbatch sbatch_single_longleaf_tmp.sh 0 $i $i2 $runtime_file
  done
done
