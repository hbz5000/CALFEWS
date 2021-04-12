#!/bin/bash

#SBATCH -t 24:00:00
#SBATCH --ntasks=250
#SBATCH --job-name=wet
#SBATCH --output=/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/out_wet.txt
#SBATCH --error=/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/err_wet.txt

module load python/3.8.8
source ../.venv_calfews_longleaf/bin/activate

start_samples=0
end_samples=3000
runtime_file='runtime_params_FKC_experiment_wet.ini'

# Print properties of job as submitted
echo "SLURM_JOB_ID = $SLURM_JOB_ID"
echo "SLURM_NTASKS = $SLURM_NTASKS"
echo "SLURM_NTASKS_PER_NODE = $SLURM_NTASKS_PER_NODE"
echo "SLURM_CPUS_PER_TASK = $SLURM_CPUS_PER_TASK"
echo "SLURM_JOB_NUM_NODES = $SLURM_JOB_NUM_NODES"

# Print properties of job as scheduled by Slurm
echo "SLURM_JOB_NODELIST = $SLURM_JOB_NODELIST"
echo "SLURM_TASKS_PER_NODE = $SLURM_TASKS_PER_NODE"
echo "SLURM_JOB_CPUS_PER_NODE = $SLURM_JOB_CPUS_PER_NODE"
echo "SLURM_CPUS_ON_NODE = $SLURM_CPUS_ON_NODE"

#python3 get_FKC_participants.py 0 $end_samples

srun srun_single_FKC.sh 1 $start_samples $end_samples $SLURM_NTASKS $runtime_file


