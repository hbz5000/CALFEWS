#!/bin/bash

numNodes=32
numProcsPerNode=48
numProcsPerTask=8
numTasksPerNode=$(expr $numProcsPerNode / $numProcsPerTask)
numTasks=$(expr $numTasksPerNode \* $numNodes)
numSolnsTotal=1295
startSolnsTotal=0
numMC=64
startMC=33
t=48:00:00
partition=skx-normal

dir=results/infra_wcu/
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J wcu \n\
#SBATCH -o ${dir}wcu.out\n\
#SBATCH -e ${dir}wcu.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
#SBATCH --exclusive\n\
\n\
time ibrun python3 -W ignore wcu_reeval_infra.py $dir $numTasks $numProcsPerTask $numSolnsTotal $startSolnsTotal $numMC $startMC \n\
\n\ "

echo -e $SLURM | sbatch
