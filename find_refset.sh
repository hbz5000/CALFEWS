#/bin/bash

results=$1

### for each directory, get ref sets from checkpoint file. Manually add correct checkpoint file for each directory.
dv=$2
seed=$3
nfe_init=$4
nfe_final=$5

setfile=$results/sets/s${seed}_nfe${nfe_final}.set
checkptfile=$results/checkpts/s${seed}_nfe${nfe_final}.checkpt
### get lines bracketing archive
line1=$(grep -n "Archive:" $checkptfile | tr ":" " ")
line1=($line1)
line1=${line1[0]}
let line1++
line2=$(grep -n "Number of Improvements:" $checkptfile | tr ":" " ")
line2=($line2)
line2=${line2[0]}
let line2--
### print archive to set file
sed -n ${line1},${line2}p $checkptfile > $setfile
sed "s/^[ \t]*//" -i $setfile
### remove solution 0 0 0 0 if exists, this is error (we know because 0-partners is impossible)
grep -v "0 0 0 0" $setfile > tmpfile && mv tmpfile $setfile

###get reference sets
python ../pareto.py $results/sets/*.set -o 81-84 -e 2. 2. 5. 0.999 --output $results/s${seed}_nfe${nfe_final}.resultfile --delimiter=" " --comment="#"
cut -d ' ' -f 82-85 $results/s${seed}_nfe${nfe_final}.resultfile > $results/s${seed}_nfe${nfe_final}.reference

