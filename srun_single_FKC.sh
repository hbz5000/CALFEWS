#!/bin/bash

echo 'Proc '$SLURM_PROCID $nsamples
time python3 -W ignore run_FKC_experiment.py $1 $2 $3 $SLURM_PROCID $4
