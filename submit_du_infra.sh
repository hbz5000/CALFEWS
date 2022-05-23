#!/bin/bash

numNodes=2
numProcsPerNode=16
numProcsPerTask=4
numTasksPerNode=$(expr $numProcsPerNode / $numProcsPerTask)
numTasks=$(expr $numTasksPerNode \* $numNodes)
soln=0
numDU=16
startDU=0
numMC=8
startMC=0
t=24:00:00
partition=normal

dir=results/infra_du/
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J du \n\
#SBATCH -o ${dir}du.out\n\
#SBATCH -e ${dir}du.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
#SBATCH --exclusive\n\
\n\
time mpirun python3 -W ignore du_reeval_infra.py $dir $numTasks $numProcsPerTask $soln $numDU $startDU $numMC $startMC \n\
\n\ "

echo -e $SLURM | sbatch --dependency=afterany:123554
