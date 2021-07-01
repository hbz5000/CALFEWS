#!/bin/bash

name='med_nowrite'
nodes=$1
tasks_per_node=$2
trials_per_task=5
last_jobid=$3 ## enter 0 otherwise
tot_tasks=$(( nodes * tasks_per_node ))
tot_trials=$(( nodes * tasks_per_node * trials_per_task ))
dir=$WORK/frontera_scaling/${name}_${tot_tasks}/
t="01:00:00"
partition=normal

sed "s+name_here+${name}_${tot_tasks}+g" sbatch_scaling_experiment.sh > sbatch_scaling_experiment_${tot_tasks}.sh
sed -i "s+dir_here+$dir+g" sbatch_scaling_experiment_${tot_tasks}.sh
sed -i "s+nodes_here+$nodes+g" sbatch_scaling_experiment_${tot_tasks}.sh
sed -i "s+tot_tasks_here+$tot_tasks+g" sbatch_scaling_experiment_${tot_tasks}.sh
sed -i "s+tot_trials_here+$tot_trials+g" sbatch_scaling_experiment_${tot_tasks}.sh
sed -i "s+time_here+$t+g" sbatch_scaling_experiment_${tot_tasks}.sh
sed -i "s+partition_here+$partition+g" sbatch_scaling_experiment_${tot_tasks}.sh

mkdir $dir
#cp runtime_params.ini $dir
cp sbatch_scaling_experiment_${tot_tasks}.sh $dir

if [ $last_jobid -eq 0 ]
then
  sbatch sbatch_scaling_experiment_${tot_tasks}.sh
else
  sbatch --dependency=afterany:$last_jobid sbatch_scaling_experiment_${tot_tasks}.sh
fi

sleep 3






