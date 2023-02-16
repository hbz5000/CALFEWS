#!/bin/bash

soln1=$1
let soln2=$soln1+1
let soln3=$soln1+2
echo $soln1 $soln2 $soln3

numNodes=48
numProcsPerNode=48
numProcsPerTask=8
numTasksPerNode=$(expr $numProcsPerNode / $numProcsPerTask)
numTasks=$(expr $numTasksPerNode \* $numNodes)
numDU=1152
round=1
startDU=0
numMC=64
startMC=0
t=28:00:00
partition=skx-normal

dir=results/infra_du_${round}/
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J du_${soln1}_${soln3} \n\
#SBATCH -o ${dir}du_${soln1}_${soln3}.out\n\
#SBATCH -e ${dir}du_${soln1}_${soln3}.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
#SBATCH --exclusive\n\
#SBATCH --mail-user=andrew.hamilton@cornell.edu\n\
#SBATCH --mail-type=ALL\n\
\n\
time ibrun python3 -W ignore du_reeval_infra.py $dir $numTasks $numProcsPerTask $soln1 $numDU $startDU $numMC $startMC \n\
time ibrun python3 -W ignore du_reeval_infra.py $dir $numTasks $numProcsPerTask $soln2 $numDU $startDU $numMC $startMC \n\
time ibrun python3 -W ignore du_reeval_infra.py $dir $numTasks $numProcsPerTask $soln3 $numDU $startDU $numMC $startMC \n\
\n\ "

echo -e $SLURM | sbatch 
