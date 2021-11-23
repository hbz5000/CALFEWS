#!/bin/bash

runtime_dir=results/infra_borg/runtime/
SEEDS=$(seq 0 1)
declare -a NFEs=(5000 6000)

for seed in $seeds
do
	for NFE in ${FEs[@]}
	do
		cat $runtime_dir/s${seed}_fe${NFE}.runtime >> $runtime_dir/s${seed}_feAll.runtime
	done
done
