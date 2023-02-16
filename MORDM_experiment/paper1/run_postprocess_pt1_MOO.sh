#!/bin/bash

results=results/MOO_results_s2/

### provide all combinations of decision variable formulation (dv) and seed, along with the final number of function evals from the last runtime file (nfes_final) and the NFE at the beginning of the simulation
dvs=(1 1 1 2 2 2)
seeds=(0 1 2 0 1 2)

#### round 1
#round=1
#nfes_init=(0 0 0 0 0 0)
#nfes_final=(21500 21600 21300 20300 20300 19800)

### round 2
#round=2
#nfes_init=(21500 21600 21300 20300 20300 19800)
#nfes_final=(63801 67801 63601 58301 59601 58601)

### round 3
round=3
nfes_init=(63801 67801 63601 58301 59601 58601)
nfes_final=(106202 108502 104702 96902 98802 114202)

### run postprocessing for this round
num_results=${#dvs[@]}

mkdir $results/overall_ref

### find objectives & ref sets for each seed
for (( i=0; i<$num_results; i++ )); do
	dv=${dvs[$i]}
	seed=${seeds[$i]}
	nfe_init=${nfes_init[$i]}
	nfe_final=${nfes_final[$i]}
	subdir=$results/dv${dv}_seed${seed}_round${round}

	### find reference set for this seed
	sh find_refset.sh $subdir $dv $seed $nfe_init $nfe_final
	### get objective values at each runtime write
	sh find_objs.sh $subdir $dv $seed $nfe_init $nfe_final
	### copy to overall ref set directory
	cp $subdir/*.reference $results/overall_ref
done

