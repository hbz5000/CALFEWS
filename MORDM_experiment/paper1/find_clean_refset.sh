#!/bin/bash

results=results/MOO_results_s2/overall_ref/

slurmscript="\
#!/bin/bash\n\
#SBATCH -J clean_refset\n\
#SBATCH -N 1\n\
#SBATCH -n 1\n\
#SBATCH -p normal\n\
#SBATCH -t 2:00:00\n\
#SBATCH -o $results/clean_refset.out\n\
#SBATCH -e $results/clean_refset.err\n\
python3 clean_refset_forReeval.py"
echo -e $slurmscript | sbatch

