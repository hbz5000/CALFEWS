#!/bin/bash

soln1=0
solns_per_task=3
num_tasks=33

for (( task=0; task<$num_tasks; task++ ))
do
	echo $soln1
	sh submit_du_infra_innerloop.sh $soln1
	let soln1=$soln1+$solns_per_task	
done
