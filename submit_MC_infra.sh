#!/bin/bash

#SBATCH -J b_infra
#SBATCH -o results/infra_MC/infra.out
#SBATCH -e results/infra_MC/infra.err
#SBATCH -p skx-dev
#SBATCH -t 2:00:00
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 1
#SBATCH --exclusive

time python -W ignore run_problem_infra.py
