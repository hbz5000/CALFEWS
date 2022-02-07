#!/bin/bash

dependency=0
numNodes=1
numProcsPerNode=48
numTasksPerNode=$numProcsPerNode
numConcurrentFE=9
numProcsBorg=10
numProcsPerFE=5
numMCPerFE=10
numFE=18
numFEPrevious=0
numSeedsPerTrial=1
numTrials=1
t=02:00:00
partition=skx-dev

subdir=${numTasksPerNode}task_${numNodes}node/
dir=results/infra_scaling/$subdir 

SLURM="#!/bin/bash\n\
#SBATCH -J ${numNodes}node\n\
#SBATCH -o results/infra_scaling/infra.out\n\
#SBATCH -e results/infra_scaling/infra.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task 1\n\
#SBATCH --exclusive\n\
#SBATCH --hint=nomultithread\n\
\n\
mkdir $dir \n\
mkdir $dir/sets \n\
mkdir $dir/runtime \n\
mkdir $dir/checkpts \n\
\n\
sed -i \"s:num_MC = .*:num_MC = $numMCPerFE:g\" problem_infra.py \n\
sed -i \"s:num_procs_FE = .*:num_procs_FE = $numProcsPerFE:g\" problem_infra.py \n\
sed -i \"s:sub_folder = .*:sub_folder = '$subdir':g\" problem_infra.py \n\
\n\
cp submit_scaling_infra.sh $dir \n\
cp problem_infra.py $dir \n\
\n\

export FI_MLX_ENABLE_SPAWN=yes \n\
for trial in $(seq 1 $numTrials) \n\
do \n\
	echo 'Begin trial '${trial}\n\
	MY_MPIRUN_OPTIONS=\"-usize ${numProcsPerNode}\"
	ibrun -np ${numProcsBorg} python3 -W ignore -m mpi4py wrapborg_infra.py $dir $numFE $numFEPrevious $numSeedsPerTrial\n\
	cp results/infra_scaling/infra.* $dir \n\
done \n\ "

if [ $dependency -eq 0 ]
then
	echo eq0
	echo -e $SLURM | sbatch
else
	echo noteq0
	echo -e $SLURM | sbatch --dependency=afterany:$dependency
fi
sleep 0.5
