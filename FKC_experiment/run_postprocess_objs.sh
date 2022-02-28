#!/bin/bash

dir='/pine/scr/a/l/alh91/CALFEWS_results/FKC_experiment/'

### collect objectives from all simulations into a single file, objs_all.csv
sh collect_objs.sh

### calculate additional post-processed objectives & store in objs_clean.csv
python3 clean_objs.py $dir
