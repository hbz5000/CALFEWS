#!/bin/bash

numNodes=1
numProcs=1
numMC=64
numDU=528
firstDU=1152
t=48:00:00
partition=normal
LHCfile='LHC_DU_2.csv'
MGHMMfile='mghmm_du_2.hdf5'

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
time python3 -W ignore generate_MGHMM_DU.py $dir $numMC $numDU $firstDU $LHCfile $MGHMMfile \n\
\n\ "

echo -e $SLURM | sbatch
