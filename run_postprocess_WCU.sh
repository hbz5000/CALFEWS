#!/bin/bash

results='results/WCU_results_bridges2/'

#python3 combine_hdf5.py $results

#python3 find_objs_WCU.py $results

grep label $results/objs_wcu.csv >> $results/objs_wcu_pareto.csv
python3 ../pareto.py $results/objs_wcu.csv -o 43-46 -m 43-44 46 -e 2. 2. 5. 0.999 --output dum.csv --delimiter=", " --comment="#" --header=1
cat dum.csv >> $results/objs_wcu_pareto.csv

cp $results/objs_wcu_pareto.csv $results/objs_wcu_pareto_withStatusQuo.csv
for label in statusquo  
do
	grep $label $results/objs_wcu.csv >> $results/objs_wcu_pareto_withStatusQuo.csv
done

mkdir results_arx/infra_wcu/
cp $results/objs* results_arx/infra_wcu/
