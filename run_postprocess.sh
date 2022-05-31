#!/bin/bash

results=results/MOO_results_s2/

### provide all combinations of decision variable formulation (dv) and seed, along with the final number of function evals from the last runtime file (nfes_final) and the NFE at the beginning of the simulation
dvs=(1 1 1 2 2 2)
seeds=(0 1 2 0 1 2)
nfes_init=(0 0 0 0 0 0)
nfes_final=(21500 21600 21300 20300 20300 19800)
num_results=${#dvs[@]}

mkdir $results/overall_ref

### find objectives & ref sets for each seed
for (( i=0; i<$num_results; i++ )); do
	dv=${dvs[$i]}
	seed=${seeds[$i]}
	nfe_init=${nfes_init[$i]}
	nfe_final=${nfes_final[$i]}

	### find reference set for this seed
	sh find_refset.sh $results/dv${dv}_seed${seed} $dv $seed $nfe_init $nfe_final
	### get objective values at each runtime write
	sh find_objs.sh $results/dv${dv}_seed${seed} $dv $seed $nfe_init $nfe_final
	### copy to overall ref set directory
	cp $results/dv${dv}_seed${seed}/*.reference $results/overall_ref
done

### get overall reference set 
python ../pareto.py $results/overall_ref/*.reference -o 0-4 -e 2. 2. 2. 5. 0.999 --output $results/overall_ref/overall.reference --delimiter=" " --comment="#"

### find runtime metrics
for (( i=0; i<$num_results; i++ )); do
	dv=${dvs[$i]}
	seed=${seeds[$i]}
	nfe_init=${nfes_init[$i]}
	nfe_final=${nfes_final[$i]}

	### find runtime metrics
	sh find_runtime_metrics.sh $results/dv${dv}_seed${seed} $dv $seed $nfe_init $nfe_final
	### find operator dynamcs
	sh find_operators.sh $results/dv${dv}_seed${seed} $dv $seed $nfe_init $nfe_final
done
