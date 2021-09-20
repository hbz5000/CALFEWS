#!/bin/bash

dir='/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'

#sh collect_objs.sh

#python3 clean_objs.py $dir

grep scenario $dir/objs_clean.csv > $dir/objs_nondom.csv
python3 ../../pareto/pareto.py $dir/objs_clean.csv -o 1 5 7 9 13 185 242 -e 1 0.1 0.1 0.1 0.01 1.0 1.0 -m 1 5 7 9 -d ',' --header 1 >> $dir/objs_nondom.csv

grep scenario $dir/objs_clean.csv > $dir/objs_medHydro_nondom.csv
python3 ../../pareto/pareto.py $dir/objs_medHydro.csv -o 1 5 7 9 13 185 242 -e 1 0.1 0.1 0.1 0.01 1.0 1.0 -m 1 5 7 9 -d ',' --header 1 >> $dir/objs_medHydro_nondom.csv

grep scenario $dir/objs_clean.csv > $dir/objs_FKC_nondom.csv
python3 ../../pareto/pareto.py $dir/objs_FKC.csv -o 1 5 7 9 13 185 242 -e 1 0.1 0.1 0.1 0.01 1.0 1.0 -m 1 5 7 9 -d ',' --header 1 >> $dir/objs_FKC_nondom.csv

grep scenario $dir/objs_clean.csv > $dir/objs_medHydro_FKC_nondom.csv
python3 ../../pareto/pareto.py $dir/objs_medHydro_FKC.csv -o 1 5 7 9 13 185 242 -e 1 0.1 0.1 0.1 0.01 1.0 1.0 -m 1 5 7 9 -d ',' --header 1 >> $dir/objs_medHydro_FKC_nondom.csv

grep num_partners $dir/objs_aggHydro.csv > $dir/objs_aggHydro_nondom.csv
python3 ../../pareto/pareto.py $dir/objs_aggHydro.csv -o 3 7 9 11 15 185 242 -e 1 0.1 0.1 0.1 0.01 1.0 1.0 -m 3 7 9 11 -d ',' --header 1 >> $dir/objs_aggHydro_nondom.csv

