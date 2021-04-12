#!/bin/bash

#for d in LWT00_PIX00 LWT10_PIX90 LWT90_PIX10
for s in NFWB_large_ownership_LWT90_PIX10 NFWB_small_ownership_LWT90_PIX10 NFWB_zero_ownership_LWT90_PIX10
do
#	s=FKC_rehab_ownership_$d
	cp runtime_params_wet_dry.ini runtime_params.ini
	sed -i 's:FKC_experiment:'$s':' runtime_params.ini
	sed -i 's:baseline_wy2017:'$s':' runtime_params.ini
#	sed -i 's:\"CDEC_wet_dry\":\"CDEC\":' runtime_params.ini
	python3 -W ignore run_main_cy.py results/$s 1 1
done
