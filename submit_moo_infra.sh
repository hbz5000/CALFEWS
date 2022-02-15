#!/bin/bash

dependency=0
numNodes=128
numProcsPerNode=48
numTasksPerNode=6
numProcsPerTask=8
numMCPerFE=32
numFE=1000000
numFEPrevious=0
runtimeFrequency=100
seed=0
t=48:00:00
partition=skx-normal

subdir=seed${seed}/
dir=results/infra_moo/$subdir 
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J s${seed}_e${numFEPrevious}\n\
#SBATCH -o ${dir}s${seed}_nfe${numFEPrevious}.out\n\
#SBATCH -e ${dir}s${seed}_nfe${numFEPrevious}.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
#SBATCH --exclusive\n\
#SBATCH --mail-user=andrew.hamilton@cornell.edu\n\
#SBATCH --mail-type=ALL\n\
\n\
mkdir $dir/sets \n\
mkdir $dir/runtime \n\
mkdir $dir/checkpts \n\
mkdir $dir/evaluations \n\
\n\
sed -i \"s:num_MC = .*:num_MC = $numMCPerFE:g\" problem_infra.py \n\
sed -i \"s:num_procs = .*:num_procs = $numProcsPerTask:g\" problem_infra.py \n\
sed -i \"s:sub_folder = .*:sub_folder = '$subdir':g\" problem_infra.py \n\
sed -i \"s:seed = .*:seed = ${seed}:g\" problem_infra.py \n\
\n\
cp submit_moo_infra.sh $dir \n\
cp problem_infra.py $dir \n\
\n\
time ibrun python3 -W ignore wrapborg_infra.py $dir $numFE $numFEPrevious $seed $runtimeFrequency \n\
\n\ "

if [ $dependency -eq 0 ]
then
	echo eq0
	echo -e $SLURM | sbatch
else
	echo noteq0
	echo -e $SLURM | sbatch --dependency=afterany:$dependency
fi
sleep 0.5
