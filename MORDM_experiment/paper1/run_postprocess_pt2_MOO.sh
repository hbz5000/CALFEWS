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

### get overall reference set (only need to do this once in 1st round, since all rounds' ref sets have been copied there in run_postprocess_pt1.sh)
if [ $round -eq 1 ]; then
	python ../pareto.py $results/overall_ref/*.reference -o 0-4 -e 2. 2. 2. 5. 0.999 --output $results/overall_ref/overall.reference --delimiter=" " --comment="#"
	python ../pareto.py $results/overall_ref/*.reference -o 0-4 -e 5. 5. 5. 10. 1.999 --output $results/overall_ref/overall_coarse.reference --delimiter=" " --comment="#"
fi

### find runtime metrics
for (( i=0; i<$num_results; i++ )); do
	dv=${dvs[$i]}
	seed=${seeds[$i]}
	nfe_init=${nfes_init[$i]}
	nfe_final=${nfes_final[$i]}
	subdir=$results/dv${dv}_seed${seed}_round${round}

	### find runtime metrics
	sh find_runtime_metrics.sh $subdir $dv $seed $nfe_init $nfe_final
	### find operator dynamcs
	sh find_operators.sh $subdir $dv $seed $nfe_init $nfe_final
done

### find clean reference set with dvs combined, plus solutions from previous Earth's Future paper (Hamilton et al, 2022).
sh find_clean_refset.sh

