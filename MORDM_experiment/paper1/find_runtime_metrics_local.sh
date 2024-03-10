#!/bin/bash

results=$1
dv=$2
seed=$3
nfe_init=$4
nfe_final=$5

JAVA_ARGS="-cp ../MOEAFramework-2.12-Demo.jar"

name=dv${dv}_s${seed}_nfe${nfe_final}
mkdir $results/metrics

java ${JAVA_ARGS} org.moeaframework.analysis.sensitivity.ResultFileEvaluator \
	-d 4 -i $results/objs/dv${dv}_s${seed}_nfe${nfe_final}.obj -r $results/../overall_ref/overall.reference \
	-o $results/metrics/${name}.metrics

