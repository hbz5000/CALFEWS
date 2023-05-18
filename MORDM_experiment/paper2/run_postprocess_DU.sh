#!/bin/bash

results='../../results/DU_results_s2/'

python3 combine_hdf5.py $results

#python3 find_objs_DU.py $results

#grep label $results/objs_wcu.csv >> $results/objs_wcu_pareto_5objs.csv
#python3 ../pareto.py $results/objs_wcu.csv -o 44-48 -m 44-46 48 -e 2. 2. 2. 5. 0.999 --output dum.csv --delimiter=", " --comment="#" --header=1
#cat dum.csv >> $results/objs_wcu_pareto_5objs.csv

#grep label $results/objs_wcu.csv >> $results/objs_wcu_pareto_5objs_coarse.csv
#python3 ../pareto.py $results/objs_wcu.csv -o 44-48 -m 44-46 48 -e 6. 6. 6. 15. 2.999 --output dum.csv --delimiter=", " --comment="#" --header=1
#cat dum.csv >> $results/objs_wcu_pareto_5objs_coarse.csv

#rm dum.csv

#cp $results/objs_wcu_pareto_5objs_coarse.csv $results/objs_wcu_pareto_5objs_coarse_withBaselines.csv
#for label in baseline friant16 alt3 alt8
#do
#	grep $label $results/objs_wcu.csv >> $results/objs_wcu_pareto_5objs_coarse_withBaselines.csv
#done

#mkdir results_arx/infra_wcu/
#cp $results/objs* results_arx/infra_wcu/
