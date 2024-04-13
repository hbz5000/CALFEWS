#!/bin/bash
numTasks=1
numProcs=1
t=24:00:00
partition=RM-shared

dir=results/climate_reeval_bridges2/
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J clim_reeval \n\
#SBATCH -o ${dir}clim_reeval.out\n\
#SBATCH -e ${dir}clim_reeval.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --ntasks $numTasks\n\
#SBATCH --cpus-per-task $numProcs\n\
#SBATCH --mail-user=andrew.hamilton.water@gmail.com\n\
#SBATCH --mail-type=ALL\n\
\n\
time python3 -W ignore -q -X faulthandler climate_reeval_infra.py \n\
\n\ "

echo -e $SLURM | sbatch
