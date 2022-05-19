#!/bin/bash

results='results/WCU_results_s2/'

#python3 combine_hdf5.py $results

#python3 find_objs_WCU.py $results

python3 ../pareto.py $results/objs_wcu.csv -o 44-48 -m 44-46 48 -e 2. 2. 2. 5. 0.999 --output $results/objs_wcu_pareto_5objs.csv --delimiter=", " --comment="#" --header=1

python3 ../pareto.py $results/objs_wcu.csv -o 44-51 -m 44-46 48 -e 2. 2. 2. 5. 0.999 5. 5. 5. --output $results/objs_wcu_pareto_8objs.csv --delimiter=", " --comment="#" --header=1

python3 ../pareto.py $results/objs_wcu.csv -o 44-48 -m 44-46 48 -e 6. 6. 6. 15. 2.999 --output $results/objs_wcu_pareto_5objs_coarse.csv --delimiter=", " --comment="#" --header=1
