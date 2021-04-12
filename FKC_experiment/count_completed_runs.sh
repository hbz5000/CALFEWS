#!/bin/bash

rm -f 'complete.txt' 'incomplete.txt'
dir='/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'
#for f in `ls ${dir}`
#do
#  if grep -q 'Data output complete' $dir/$f/log.txt 
#  if grep -q 'Year  50.0 ,' $dir/$f/log.txt
#  then
#    echo $f >> 'completed.txt' 
#  else
#    echo $f
#    rm -r $dir/$f
#  fi
#done

for i in {0..3029}
do
y=0
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_wet_${i}_FKC_CFWB/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_wet_${i}_FKC/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_wet_${i}_CFWB/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_dry_${i}_FKC_CFWB/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_dry_${i}_FKC/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_dry_${i}_CFWB/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_median_${i}_FKC_CFWB/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_median_${i}_FKC/log.txt
then
dum=0
else
y=1
fi
if grep -q 'Data output complete' $dir/FKC_experiment_capow_50yr_median_${i}_CFWB/log.txt
then
dum=0
else
y=1
fi

if [ $y = 1 ]
then
echo $i >> incomplete.txt
rm -rf $dir/FKC_experiment_capow_50yr_dry_${i}_*
rm -rf $dir/FKC_experiment_capow_50yr_wet_${i}_*
rm -rf $dir/FKC_experiment_capow_50yr_median_${i}_*
else
echo $i >> complete.txt
fi
done


