#!/bin/bash

numNodes=2
numProcsPerNode=128
numProcsPerTask=16
numTasksPerNode=$(expr $numProcsPerNode / $numProcsPerTask)
numTasks=$(expr $numTasksPerNode \* $numNodes)
dv_formulation=2
seed=4
numSolnsTotal=269
startSolnsTotal=0
numMC=79
startMC=21
t=28:00:00
partition=RM

dir=results/infra_wcu/dv${dv_formulation}_seed${seed}/
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J wcu_s${seed} \n\
#SBATCH -o ${dir}wcu.out\n\
#SBATCH -e ${dir}wcu.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
#SBATCH --exclusive\n\
#SBATCH --mail-user=andrew.hamilton.water@gmail.com\n\
#SBATCH --mail-type=ALL\n\
\n\
time mpirun -np $numTasks python3 -W ignore -q -X faulthandler wcu_reeval_infra.py $dir $numTasks $numProcsPerTask $dv_formulation $seed $numSolnsTotal $startSolnsTotal $numMC $startMC \n\
\n\ "

echo -e $SLURM | sbatch
