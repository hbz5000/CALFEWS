#!/bin/bash

NFE=All #5000
SEEDS=$(seq 0 1)
JAVA_ARGS="-cp MOEAFramework-2.12-Demo.jar"

for SEED in ${SEEDS}
do
	NAME=s${SEED}_fe${NFE}
	slurmscript="\
	#!/bin/bash\n\
	#SBATCH -J ${NAME}\n\
        #SBATCH -N 1\n\
	#SBATCH -n 1\n\
	#SBATCH -p normal\n\
	#SBATCH -t 1:00:00\n\
	#SBATCH -o results/infra_borg/${NAME}.metricsout\n\
	#SBATCH -e results/infra_borg/${NAME}.metricserr\n\
	java ${JAVA_ARGS} org.moeaframework.analysis.sensitivity.ResultFileEvaluator \
		-d 5 -i ./results/infra_borg/objs/s${SEED}_fe${NFE}.obj -r ./results/infra_borg/infra.reference \
		-o ./results/infra_borg/metrics/s${SEED}_fe${NFE}.metrics"
	echo -e $slurmscript | sbatch

done
