#!/bin/bash

#SBATCH -t 10:00:00
#SBATCH --nodes=12
#SBATCH --ntasks=192
#SBATCH --job-name=FKC_CFWB
#SBATCH -p normal
#SBATCH --export=ALL
#SBATCH --output=/scratch/spec823/CALFEWS_results/FKC_experiment/out_FKC_CFWB.txt
#SBATCH --error=/scratch/spec823/CALFEWS_results/FKC_experiment/err_FKC_CFWB.txt
#SBATCH --exclusive

module load python/3.9.4
source ../.venv_calfews/bin/activate

start_samples=0
end_samples=191


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

#python3 get_FKC_participants.py 0 3000

echo '##########################################################'
echo '### START WET TIME SERIES' "ended at `date` on `hostname`"
echo '##########################################################'

sed -i 's/capow_50yr_dry/capow_50yr_wet/' runtime_params.ini
sed -i 's/capow_50yr_median/capow_50yr_wet/' runtime_params.ini

srun srun_single_FKC.sh 1 $start_samples $end_samples $SLURM_NTASKS
#time mpirun python3 -W ignore run_FKC_experiment.py 1 0 3000

echo '##########################################################'
echo '### FINISH WET TIME SERIES' "ended at `date` on `hostname`"
echo '##########################################################'

sed -i 's/capow_50yr_wet/capow_50yr_dry/' runtime_params.ini

srun srun_single_FKC.sh 1 $start_samples $end_samples $SLURM_NTASKS
#time mpirun python3 -W ignore run_FKC_experiment.py 1 0 3000

echo '##########################################################'
echo '### FINISH DRY TIME SERIES' "ended at `date` on `hostname`"
echo '##########################################################'

sed -i 's/capow_50yr_dry/capow_50yr_median/' runtime_params.ini

srun srun_single_FKC.sh 1 $start_samples $end_samples $SLURM_NTASKS
#time mpirun python3 -W ignore run_FKC_experiment.py 1 0 3000

echo '##########################################################'
echo '### FINISH MEDIAN TIME SERIES' "ended at `date` on `hostname`"
echo '##########################################################'

