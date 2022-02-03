#!/bin/bash

#SBATCH -J b_infra
#SBATCH -o results/infra_borg/infra.out
#SBATCH -e results/infra_borg/infra.err
#SBATCH -p skx-dev
#SBATCH -t 2:00:00
#SBATCH --nodes 2
#SBATCH --ntasks-per-node 4
#SBATCH --exclusive

time ibrun python -W ignore wrapborg_infra.py 
