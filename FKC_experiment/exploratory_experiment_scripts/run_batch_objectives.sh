#!/bin/bash

for s in {0..800}
do
  let sample_start=s*4 sample_end=s*4+3
  if [ $sample_start -lt 3030 ]
  then
    if [ $sample_end -lt 3030 ]
    then
      echo $sample_start $sample_end
      sbatch batch_objectives.sh $sample_start $sample_end
    else
      sample_end=3029
      echo $sample_start $sample_end
      sbatch batch_objectives.sh $sample_start $sample_end
    fi
  fi

done
