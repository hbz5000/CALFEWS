#!/bin/bash

dir='/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'

#sh collect_objs.sh

python3 clean_objs.py $dir

grep scenario $dir/objs_clean.csv > $dir/objs_nondom.csv
python3 ../../pareto/pareto.py $dir/objs_clean.csv -o 5 6 7 9 11 183 -e 0.1 0.01 0.1 0.1 0.01 1.0 -m 5 6 7 9 -d ',' --header 1 >> $dir/objs_nondom.csv

grep num_partners $dir/objs_aggHydro.csv > $dir/objs_aggHydro_nondom.csv
python3 ../../pareto/pareto.py $dir/objs_aggHydro.csv -o 7 8 9 11 13 183 -e 0.1 0.01 0.1 0.1 0.01 1.0 -m 7 8 9 11 -d ',' --header 1 >> $dir/objs_aggHydro_nondom.csv

