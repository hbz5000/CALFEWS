#!/bin/bash

NFE=All #5000
SEEDS=$(seq 0 1)
results_folder=./results/infra_borg/

for SEED in ${SEEDS}
do
	runtimefile=${results_folder}/runtime/s${SEED}_fe${NFE}.runtime
	for operator in SBX DE PCX SPX UNDX UM NFE
	do
		operatorfile=${results_folder}/operators/s${SEED}_fe${NFE}.${operator}
		grep $operator $runtimefile | grep -Eo '[+-]?[0-9]+([.][0-9]+)?' | tee $operatorfile >/dev/null
	done
done
