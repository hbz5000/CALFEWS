#!/bin/bash

numNodes=48
numProcsPerNode=48
numProcsPerTask=8
numTasksPerNode=$(expr $numProcsPerNode / $numProcsPerTask)
numTasks=$(expr $numTasksPerNode \* $numNodes)
numDU=1152
startDU=0
numMC=64
startMC=0
t=48:00:00
partition=skx-normal

soln1=0
soln2=1
soln3=2
dir=results/infra_du/
mkdir $dir
dir1=$dir/soln1/
dir2=$dir/soln2/
dir3=$dir/soln3/
mkdir $dir1
mkdir $dir2
mkdir $dir3

SLURM="#!/bin/bash\n\
#SBATCH -J du \n\
#SBATCH -o ${dir}du_${soln1}_${soln3}.out\n\
#SBATCH -e ${dir}du_${soln1}_${soln3}.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
#SBATCH --exclusive\n\
\n\
time ibrun python3 -W ignore du_reeval_infra.py $dir1 $numTasks $numProcsPerTask $soln1 $numDU $startDU $numMC $startMC \n\
time ibrun python3 -W ignore du_reeval_infra.py $dir2 $numTasks $numProcsPerTask $soln2 $numDU $startDU $numMC $startMC \n\
time ibrun python3 -W ignore du_reeval_infra.py $dir3 $numTasks $numProcsPerTask $soln3 $numDU $startDU $numMC $startMC \n\
\n\ "

echo -e $SLURM | sbatch 
