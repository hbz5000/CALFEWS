#!/bin/bash

numNodes=1
numProcs=1
numMC=64
numDU=64
t=03:00:00
partition=normal

dir=results/infra_mghmm_du/
mkdir $dir

SLURM="#!/bin/bash\n\
#SBATCH -J mghmm \n\
#SBATCH -o ${dir}mghmm.out\n\
#SBATCH -e ${dir}mghmm.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH -c $numProcs\n\
\n\
time python3 -W ignore generate_MGHMM_DU.py $dir $numMC $numDU \n\
\n\ "

echo -e $SLURM | sbatch
