#!/bin/bash

#SBATCH -J b_infra
#SBATCH -o results/infra_borg/infra6000.out
#SBATCH -e results/infra_borg/infra6000.err
#SBATCH -t 30:00:00
#SBATCH --nodes 12
#SBATCH --ntasks-per-node 8
#SBATCH --exclusive

time mpirun python3 -W ignore wrapborg_infra.py
