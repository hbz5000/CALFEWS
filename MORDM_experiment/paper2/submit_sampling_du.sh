#!/bin/bash

numNodes=1
numProcs=1
numMC=64
numDU=1152
firstDU=0
round=1
t=48:00:00
partition=normal

file_lhc='LHC_DU_'$round'.csv'
file_mghmm='mghmm_du_'$round'.hdf5'

dir_lhc=calfews_src/data/LHC_DU/
dir_mghmm=results/infra_mghmm_du/
mkdir $dir_mghmm

SLURM="#!/bin/bash\n\
#SBATCH -J mghmm \n\
#SBATCH -o ${dir_lhc}mghmm_${round}.out\n\
#SBATCH -e ${dir_lhc}mghmm_${round}.err\n\
#SBATCH -p ${partition}\n\
#SBATCH -t ${t}\n\
#SBATCH -c $numProcs\n\
\n\
time python3 -W ignore generate_LHC_DU.py $dir_lhc $file_lhc $numDU $round \n\
time python3 -W ignore generate_MGHMM_DU.py $dir_mghmm $numMC $numDU $firstDU $file_lhc $file_mghmm \n\
\n\ "

echo -e $SLURM | sbatch
