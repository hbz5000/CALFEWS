#!/bin/bash

############################
## Enter location of working directory and runtime_params.ini, both relative to C:/
############################

working_directory_relative_C="Users/Andrew/PycharmProjects/ORCA_COMBINED"
project_directory_relative_C="Users/Andrew/PycharmProjects/ORCA_COMBINED"

############################
working_directory_C='C:/'$working_directory_relative_C
working_directory_cygwin='/cygdrive/c/'$working_directory_relative_C

project_directory_cygwin='/cygdrive/c/'$project_directory_relative_C
project_directory_C='C:/'$project_directory_relative_C

param_file_cygwin=$project_directory_cygwin'/cord/data/input/runtime_params.ini'
main_file_C=$project_directory_C'/main.py'
consolidate_hdf5_file_C=$project_directory_C'/cord/postprocess/consolidate_hdf5.py'

base_output_directory_relative_wd=$(grep -Po 'output_directory = "\K[^"]*' $param_file_cygwin)
scenario_name=$(grep -Po 'scenario_name = "\K[^"]*' $param_file_cygwin)

output_directory_relative_wd=$base_output_directory_relative_wd'/'$scenario_name
output_directory_cygwin=$working_directory_cygwin'/'$output_directory_relative_wd
output_directory_C=$working_directory_C'/'$output_directory_relative_wd

parallel_mode=$(grep -Po 'parallel_mode = "\K[^"]*' $param_file_cygwin)

num_processors=$(grep -Po 'num_processors = "\K[^"]*' $param_file_cygwin)

if test -d "$output_directory_cygwin"; then
	echo "ERROR: Output directory already exists. Move or delete prior to running."
	echo "Directory: $output_directory_cygwin"
else
	echo "Working directory: "$working_directory_cygwin
	echo "Output directory: "$output_directory_cygwin
	echo "Parallel mode: "$parallel_mode
	echo "Processors (if parallel mode True): "$num_processors
	if [ $parallel_mode = 'True' ]; then
		echo $main_file_cygwin
		mpiexec -n $num_processors python $main_file_C $working_directory_C 
		python $consolidate_hdf5_file_C $output_directory_C $num_processors
	else
		python $main_file_C $working_directory_C 
		python $consolidate_hdf5_file_C $output_directory_C 1
	fi
fi


