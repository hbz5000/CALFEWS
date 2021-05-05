#!/bin/bash

count=0
for model in 'hadgem2-es' 'cnrm-cm5' 'canesm2' 'miroc5'
do
  for rcp in '45' '85' 
  do
    label=${model}_rcp${rcp}
    results='climate_ensemble/'${label}'/'
    sed 's/namehere/'$label'/' sbatch_single_longleaf.sh > sbatch_single_longleaf_${label}.sh
    sed -i 's/outhere/out_'$label'.txt/' sbatch_single_longleaf_${label}.sh
    sed -i 's/errhere/err_'$label'.txt/' sbatch_single_longleaf_${label}.sh

    if [ $count -eq 0 ]
    then
      jobid=$(sbatch --parsable sbatch_single_longleaf_${label}.sh $label $results)
    else
      jobid=$(sbatch --parsable --dependency=after:$jobid+3 sbatch_single_longleaf_${label}.sh $label $results)
    fi

    count=$(( $count + 1 ))
  done
done
