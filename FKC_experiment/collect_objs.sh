#!/bin/bash

rm -f 'complete.txt' 'incomplete.txt'
dir='/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'

rm -f objs_all.txt

for h in wet dry median
do
  for s in {0..3029}
  do
    for p in FKC_CFWB FKC CFWB
    do
      echo $h $s $p
      grep 'FKC_experiment_' $dir/FKC_experiment_capow_50yr_${h}_${s}_${p}/objs.csv >> objs_all.txt
    done
  done
done




