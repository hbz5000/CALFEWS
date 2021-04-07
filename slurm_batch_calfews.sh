#!/bin/bash

#SBATCH -t 02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --job-name=FKC_wet
#SBATCH -p normal
#SBATCH --export=ALL
#SBATCH --output=out_wet.txt
#SBATCH --exclusive

module load python/3.9.4
source ../.venv_calfews_cube/bin/activate

time mpirun python3 -W ignore run_FKC_experiment.py 1 0 15 
