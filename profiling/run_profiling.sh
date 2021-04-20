#!/bin/bash

folder=$1
name=$2

cd ../
#python3 -W ignore -m cProfile -o profiling/profile_${name}.stats run_main_cy.py $folder 1 0
#python3 -W ignore run_main_cy.py $folder 1 0
###python3 -W ignore run_main_cy.py $folder 0 1
python3 -W ignore -m cProfile -o profiling/profile_${name}.stats run_main_cy.py $folder 0 1
cd profiling

python3 output_profiling.py $name 'cumulative' > profile_${name}_cumulative.txt
python3 output_profiling.py $name 'caller' > profile_${name}_caller.txt
python3 output_profiling.py $name 'callee' > profile_${name}_callee.txt

