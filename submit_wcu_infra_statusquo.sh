#!/bin/bash
numTasks=1
numProcs=16
dv_formulation=0
seed=-1
numSolnsTotal=1
startSolnsTotal=0
numMC=79
startMC=21
t=2:00:00
partition=RM-shared

dir=results/infra_wcu/statusquo/
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J wcu_s${seed} \n\
#SBATCH -o ${dir}wcu.out\n\
#SBATCH -e ${dir}wcu.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --ntasks $numTasks\n\
#SBATCH --cpus-per-task $numProcs\n\
#SBATCH --mail-user=andrew.hamilton.water@gmail.com\n\
#SBATCH --mail-type=ALL\n\
\n\
time python3 -W ignore -q -X faulthandler wcu_reeval_infra.py $dir $numTasks $numProcs $dv_formulation $seed $numSolnsTotal $startSolnsTotal $numMC $startMC \n\
\n\ "

echo -e $SLURM | sbatch
