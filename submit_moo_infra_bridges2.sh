#!/bin/bash

dependency=0
numNodes=2
numProcsPerNode=128
numTasksPerNode=16
numProcsPerTask=8
numMCPerFE=16
numTasks=$(($numNodes * $numTasksPerNode))
numFE=1000000
numFEPrevious=0
runtimeFrequency=2
seed=0
dv_formulation=2
t=01:00:00
partition=RM

subdir=dv${dv_formulation}_seed${seed}/
dir=results/infra_moo/$subdir 
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J d${dv_formulation}s${seed}e${numFEPrevious}\n\
#SBATCH -o ${dir}s${seed}_nfe${numFEPrevious}.out\n\
#SBATCH -e ${dir}s${seed}_nfe${numFEPrevious}.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH --nodes $numNodes\n\
#SBATCH --ntasks-per-node $numTasksPerNode\n\
#SBATCH --cpus-per-task $numProcsPerTask\n\
###SBATCH --exclusive\n\
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
sed -i \"s:dv_formulation = .*:dv_formulation = ${dv_formulation}:g\" problem_infra.py \n\
\n\
cp submit_moo_infra_anvil.sh $dir \n\
cp problem_infra.py $dir \n\
\n\
time mpirun -np $numTasks python3 -W ignore -q -X faulthandler wrapborg_infra.py $dir $numFE $numFEPrevious $seed $runtimeFrequency $dv_formulation \n\
\n\ "

if [ $dependency -eq 0 ]
then
	echo no dependency
	echo -e $SLURM | sbatch
else
	echo dependency: $dependency
	echo -e $SLURM | sbatch --dependency=afterany:$dependency
fi
sleep 0.5
