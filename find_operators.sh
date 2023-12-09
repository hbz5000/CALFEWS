#!/bin/bash

results=$1
dv=$2
seed=$3
nfe_init=$4
nfe_final=$5

runtimefile=$results/runtime/s${seed}_nfe${nfe_init}.runtime

mkdir $results/operators

for operator in SBX DE PCX SPX UNDX UM NFE
do
	operatorfile=$results/operators/dv${dv}_s${seed}_nfe${nfe_final}.${operator}
	grep $operator $runtimefile | grep -Eo '[+-]?[0-9]+([.][0-9]+)?' | tee $operatorfile >/dev/null
done
