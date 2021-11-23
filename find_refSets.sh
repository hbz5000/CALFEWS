#/bin/bash

python pareto.py ./results/infra_borg/sets/*.set -o 39-43 -e 2. 2. 2. 5. 0.999 --output ./results/infra_borg/infra.resultfile --delimiter=" " --comment="#"
cut -d ' ' -f 40-44 ./results/infra_borg/infra.resultfile >./results/infra_borg/infra.reference

