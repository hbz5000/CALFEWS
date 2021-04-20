#!/bin/bash
#SBATCH -t 02:00:00
#SBATCH --ntasks=1

for s in $(seq $1 $2)
do
  s=0
  for h in wet dry median
  do
    for p in FKC_CFWB FKC CFWB
    do
      echo $h $s $p
      time python3 get_objectives.py $h $s $p
    done
  done
#done
