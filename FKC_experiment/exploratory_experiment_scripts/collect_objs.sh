#!/bin/bash

dir='/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'

grep scenario $dir/results_other/FKC_experiment_capow_50yr_wet_0_FKC_CFWB/objs.csv > $dir/objs_all.csv

for h in wet dry median
do
  ### collect objectives from all random samples
  for s in {0..3030}
  do
    for p in FKC_CFWB FKC CFWB
    do
      for subdir in $dir/*
      do
        if [ -d $subdir/FKC_experiment_capow_50yr_${h}_${s}_${p} ]
        then
          results=$subdir/FKC_experiment_capow_50yr_${h}_${s}_${p}
        fi
      done
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

  ### do the same thing but for default ownership scenarios
  for own in Equal Historical
  do
    for subdir in $dir/*
    do
      if [ -d $subdir/FKC_experiment_capow_50yr_${h}_friant${own} ]
      then
        results=$subdir/FKC_experiment_capow_50yr_${h}_friant${own} 
      fi
    done
    if [ -f "$results/objs.csv" ]
    then
      objs=$(grep 'FKC_experiment_' $results/objs.csv)
      echo $objs >>$dir/objs_all.csv
    fi
  done

done


