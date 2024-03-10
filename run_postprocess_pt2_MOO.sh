#!/bin/bash

results=results/MOO_results_bridges2/

### provide all combinations of decision variable formulation (dv) and seed, along with the final number of function evals from the last runtime file (nfes_final) and the NFE at the beginning of the simulation

#### round 1
dvs=(2 2 2 2 2)
seeds=(1 1 2 3 4)
round=1
nfes_init=(0 3100 0 0 0)
nfes_final=(3100 42401 40400 42200 41500)
dir_names=('dv2_seed1_round1a' 'dv2_seed1_round1b' 'dv2_seed2_round1' 'dv2_seed3_round1' 'dv2_seed4_round1')

### round 2
#dvs=(2 2 2 2)
#seeds=(1 2 3 4)
#round=2
#nfes_init=(42401 40400 42200 41500)
#nfes_final=(73702 74001 75901 76001)
#dir_names=('dv2_seed1_round2' 'dv2_seed2_round2' 'dv2_seed3_round2' 'dv2_seed4_round2')


### run postprocessing for this round
num_results=${#dvs[@]}

### get overall reference set (only need to do this once in 1st round, since all rounds' ref sets have been copied there in run_postprocess_pt1.sh)
if [ $round -eq 1 ]; then
	python3 ../pareto.py $results/overall_ref/*.reference -o 0-3 -e 2. 2. 5. 0.999 --output $results/overall_ref/overall.reference --delimiter=" " --comment="#"
#	python ../pareto.py $results/overall_ref/*.reference -o 0-3 -e 5. 5. 10. 1.999 --output $results/overall_ref/overall_coarse.reference --delimiter=" " --comment="#"
fi

### find runtime metrics
for (( i=0; i<$num_results; i++ )); do
	dv=${dvs[$i]}
	seed=${seeds[$i]}
	nfe_init=${nfes_init[$i]}
	nfe_final=${nfes_final[$i]}
	subdir=$results/${dir_names[$i]}

	### find runtime metrics
	bash find_runtime_metrics_local.sh $subdir $dv $seed $nfe_init $nfe_final
	### find operator dynamcs
	bash find_operators.sh $subdir $dv $seed $nfe_init $nfe_final
done

### find clean reference set with dvs combined, plus solutions from previous Earth's Future paper (Hamilton et al, 2022).
#sh find_clean_refset.sh

