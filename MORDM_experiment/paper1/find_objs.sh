#!/bin/bash

results=$1
dv=$2
seed=$3
nfe_init=$4
nfe_final=$5

mkdir $results/objs
if [ $dv -eq 1 ]; then
	awk 'BEGIN {FS=" "}; /^#/ {print $0}; /^[^#/]/ {printf("%s %s %s %s %s\n",$43,$44,$45,$46,$47)}' $results/runtime/s${seed}_nfe${nfe_init}.runtime > $results/objs/dv${dv}_s${seed}_nfe${nfe_final}.obj
else
	awk 'BEGIN {FS=" "}; /^#/ {print $0}; /^[^#/]/ {printf("%s %s %s %s %s\n",$82,$83,$84,$85,$86)}' $results/runtime/s${seed}_nfe${nfe_init}.runtime > $results/objs/dv${dv}_s${seed}_nfe${nfe_final}.obj
fi
