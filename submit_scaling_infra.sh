#!/bin/bash

dependency=0
numNodes=2
numProcsPerNode=48
numTasksPerNode=12
numProcsPerTask=4
numMCPerFE=32
numFE=100000
numFEPrevious=0
numSeedsPerTrial=1
numTrials=1
t=1:00:00
partition=skx-normal

subdir=${numProcsPerTask}ppt_${numNodes}node/
dir=results/infra_moo/$subdir 
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J ${numNodes}n\n\
#SBATCH -o ${dir}infra.out\n\
#SBATCH -e ${dir}infra.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
#SBATCH --exclusive\n\
\n\
mkdir $dir/sets \n\
mkdir $dir/runtime \n\
mkdir $dir/checkpts \n\
\n\
sed -i \"s:num_MC = .*:num_MC = $numMCPerFE:g\" problem_infra.py \n\
sed -i \"s:num_procs = .*:num_procs = $numProcsPerTask:g\" problem_infra.py \n\
sed -i \"s:sub_folder = .*:sub_folder = '$subdir':g\" problem_infra.py \n\
\n\
cp submit_scaling_infra.sh $dir \n\
cp problem_infra.py $dir \n\
\n\
for trial in $(seq 1 $numTrials) \n\
do \n\
	echo 'Begin trial '${trial}\n\
	time ibrun python3 -W ignore wrapborg_infra.py $dir $numFE $numFEPrevious $numSeedsPerTrial\n\
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
