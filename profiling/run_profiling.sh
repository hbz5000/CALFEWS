#!/bin/bash

name=$1

cd ../
rm -r cord/data/results/baseline_wy2017
python3 -W ignore main_profile.py
#python3 -W ignore main_profile.py
python3 -W ignore -m cProfile -o profiling/profile_${name}.stats main_profile.py
cd profiling
python3 output_profiling.py $name 'cumulative' > profile_${name}_cumulative.txt
python3 output_profiling.py $name 'caller' > profile_${name}_caller.txt
python3 output_profiling.py $name 'callee' > profile_${name}_callee.txt

