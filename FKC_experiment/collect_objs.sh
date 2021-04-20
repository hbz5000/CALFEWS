#!/bin/bash

dir='/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'

#grep scenario $dir/FKC_experiment_capow_50yr_wet_0_FKC_CFWB/objs.csv > $dir/objs_all.csv

for h in wet dry median
do
  for s in {0..3030}
  do
    for p in FKC_CFWB FKC CFWB
    do
      results=$dir/FKC_experiment_capow_50yr_${h}_${s}_${p}
      if [ -f "$results/objs.csv" ]
      then
        objs=$(grep 'FKC_experiment_' $results/objs.csv)
        echo $objs >>$dir/objs_all.csv
      fi
    done
  done
  results=$dir/FKC_experiment_capow_50yr_${h}_all
  if [ -f "$results/objs.csv" ]
  then
    objs=$(grep 'FKC_experiment_' $results/objs.csv)
    echo $objs >>$dir/objs_all.csv
  fi
done


