#!/bin/bash

numNodes=1
numProcs=1
numMC=100
t=00:30:00
partition=normal

SLURM="#!/bin/bash\n\
#SBATCH -J mghmm \n\
#SBATCH -o ${dir}mghmm.out\n\
#SBATCH -e ${dir}mghmm.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH -c $numProcs\n\
\n\
time python3 -W ignore generate_MGHMM_MOOWCU.py \n\
\n\ "

echo -e $SLURM | sbatch
