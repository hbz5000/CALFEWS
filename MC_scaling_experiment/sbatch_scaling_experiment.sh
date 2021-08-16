#!/bin/bash

#SBATCH -J name_here           # Job name
#SBATCH -o dir_here/slurm.o%j       # Name of stdout output file
#SBATCH -e dir_here/slurm.e%j       # Name of stderr error file
#SBATCH -p partition_here          # Queue (partition) name
#SBATCH -N nodes_here               # Total # of nodes (must be 1 for serial)
#SBATCH -n tot_tasks_here               # Total # of mpi tasks (should be 1 for serial)
#SBATCH -t time_here        # Run time (hh:mm:ss)

#time ibrun python -W ignore run_scaling_experiment.py name_here 0 tot_tasks_here
time ibrun python -W ignore run_scaling_experiment.py name_here 0 tot_trials_here  
