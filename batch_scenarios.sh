#!/bin/bash

for d in none grp1 #grp2 grp3 grp12 grp13 grp23 grp123 
#for s in FKC_capacity_rehab_full baseline_wy2017
do
	s=FKC_rehab_ownership_$d
	cp runtime_params_wet_dry.ini runtime_params.ini
	sed -i 's:baseline_wy2017:'$s':' runtime_params.ini
	sed -i 's:\"CDEC_wet_dry\":\"CDEC\":' runtime_params.ini
	python3 -W ignore run_main_cy.py results/$s 1 1
done
