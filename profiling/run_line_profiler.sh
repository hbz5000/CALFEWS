#!/bin/bash

name=$1

cd ../
rm -r results/baseline_wy2017
kernprof -l -v main_profile.py		# run once for initialization
kernprof -l -v main_profile.py   # now run again for profiling
cd profiling
mv ../main_profile.py.lprof .
python3 -m line_profiler main_profile.py.lprof > lprofile_${name}.txt
