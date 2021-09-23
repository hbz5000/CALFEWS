#!/bin/bash
#SBATCH -t 12:00:00
#SBATCH --ntasks=1

### get objs for baseline cases
if [ $1 -eq 0 ]
then
  for h in wet dry median
  do
    time python3 get_objectives.py $h 0  0
    time python3 get_objectives.py $h 0  1
  done
fi

for s in $(seq $1 $2)
do
  for h in wet dry median
  do
    for p in FKC_CFWB FKC CFWB
    do
      echo $h $s $p
      time python3 get_objectives.py $h $s $p
    done
  done
done
