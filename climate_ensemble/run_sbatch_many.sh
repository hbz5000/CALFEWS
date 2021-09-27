#!/bin/bash

### longleaf
#sbatch_file=sbatch_single_longleaf.sh

### thecube
sbatch_file=sbatch_single_cube

count=0
for model in 'hadgem2-es' 'cnrm-cm5' 'canesm2' 'miroc5' 'ccsm4' 'csiro-mk3-6-0' 'gfdl-cm3' 'gfdl-esm2m' 'hadgem2-cc' 'inmcm4' 'ipsl-cm5a-mr' 
do
  for rcp in '45' '85' 
  do
    label=${model}_rcp${rcp}
    results='climate_ensemble/'${label}'/'
    sed 's/namehere/'$label'/' ${sbatch_file}.sh > ${sbatch_file}_${label}.sh
    sed -i 's/outhere/out_'$label'.txt/' ${sbatch_file}_${label}.sh
    sed -i 's/errhere/err_'$label'.txt/' ${sbatch_file}_${label}.sh

    if [ $count -eq 0 ]
#    ### set up dependency so each job will wait a few minutes after previous job starts, to make sure we finish initialization and dont overwrite any input files.
#    then
#      jobid=$(sbatch --parsable ${sbatch_file}_${label}.sh $label $results)
#    else
#      jobid=$(sbatch --parsable --dependency=after:${jobid}+4 ${sbatch_file}_${label}.sh $label $results)
#    fi
#    echo 'Submitting job '$jobid
#    count=$(( $count + 1 ))

    ### +time dependency not working on cube (too old of slurm version i think), so just run in serial (afterany waits until previous job exits)
    then
      jobid=$(sbatch --parsable ${sbatch_file}_${label}.sh $label $results)
    else
      jobid=$(sbatch --parsable --dependency=afterany:${jobid} ${sbatch_file}_${label}.sh $label $results)
    fi
    echo 'Submitting job '$jobid
    count=$(( $count + 1 ))

  done
done
