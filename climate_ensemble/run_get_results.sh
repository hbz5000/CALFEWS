#!/bin/bash

for model in 'canesm2' #'hadgem2-es' 'cnrm-cm5' 'miroc5'
do
  for rcp in '45' #'85'
  do
    python get_results.py $model $rcp
  done
done
