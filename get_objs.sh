#!/bin/bash
SEEDS=$(seq 0 1)
#declare -a NFEs=(5000 6000)
declare -a NFEs=("All")
for SEED in ${SEEDS}
do
	for NFE in ${NFEs[@]}
	do
		awk 'BEGIN {FS=" "}; /^#/ {print $0}; /^[^#/]/ {printf("%s %s %s %s %s\n",$40,$41,$42,$43,$44)}' ./results/infra_borg/runtime/s${SEED}_fe${NFE}.runtime >./results/infra_borg/objs/s${SEED}_fe${NFE}.obj
	done
done
