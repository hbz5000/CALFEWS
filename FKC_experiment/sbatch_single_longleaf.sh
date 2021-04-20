#!/bin/bash

#SBATCH -t 04:00:00
#SBATCH --ntasks=1
#SBATCH --job-name=namehere
#SBATCH --output=/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/outhere
#SBATCH --error=/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/errhere

module load python/3.8.8
source ../.venv_calfews_longleaf/bin/activate

run_baseline=$1
start_samples=$2
end_samples=$3
runtime_file=$4 #'runtime_params_FKC_experiment_wet.ini'

time python3 -W ignore run_FKC_experiment.py $run_baseline $start_samples $end_samples $runtime_file


