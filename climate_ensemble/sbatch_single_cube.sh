#!/bin/bash

#SBATCH -t 05:00:00
#SBATCH --exclusive
#SBATCH --mem=10000
#SBATCH --ntasks=1
#SBATCH --job-name=namehere
#SBATCH --output=results/climate_ensemble/outhere
#SBATCH --error=results/climate_ensemble/errhere

### longleaf
#module load python/3.8.8
#source ../.venv_calfews_longleaf/bin/activate
#results_base='/pine/scr/a/l/alh91/CALFEWS_results/'

### thecube
module load python/3.9.4
source ~/.venv_calfews/bin/activate
results_base='./results/'


label=$1
results=$2

sed 's/sourcehere/'$label'/' runtime_params_climate_tmp.ini > runtime_params.ini
mkdir -p ${results_base}${results}
cp runtime_params.ini ${results_base}${results}

time python -W ignore run_main_cy.py $label 1 1
