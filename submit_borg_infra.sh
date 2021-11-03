#!/bin/bash

#SBATCH -J b_infra
#SBATCH -o results/infra_borg/infra.out
#SBATCH -e results/infra_borg/infra.err
#SBATCH -t 05:00:00
#SBATCH --nodes 2
#SBATCH --ntasks-per-node 4
#SBATCH --exclusive

time mpirun python3 -W ignore wrapborg_infra.py
