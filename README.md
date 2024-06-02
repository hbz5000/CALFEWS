# Designing resilient water infrastructure partnerships with multiobjective intelligent search

This "MORDM_experiment_paper1" branch of the repository contains code and data for the following paper:

Hamilton, A.L., Reed, P.M., Gupta, R.S., Zeff, H.B., & G.W. Characklis. (2023). Resilient water infrastructure
partnerships in institutionally complex systems face challenging supply and financial risk tradeoffs. *In Review*.

## California Food-Energy-Water System (CALFEWS)

For general information on the California Food-Energy-Water System (CALFEWS) simulation model, please switch to the "
main" branch of this repository, where you will find information on installing, compiling, running, and analyzing the
base model. Interested readers can also refer to the following paper to learn more about the performance and conceptual
underpinnings of the model:

Zeff, H.B., Hamilton, A.L., Malek, K., Herman, J.D., Cohen, J.S., Medellin-Azuara, J., Reed, P.M., and G.W.
Characklis. (2021). California's Food-Energy-Water System: An Open Source Simulation Model of Adaptive Surface and
Groundwater Management in the Central Valley. *Environmental Modelling & Software, 141*: 105052. [https://doi.org/10.1016/j.envsoft.2021.105052](https://doi.org/10.1016/j.envsoft.2021.105052)

Licensed under the MIT License, 2017-.

## Installation and setup

1. First, switch to the "main" branch of this repository and follow instructions to clone, compile, and run the base CALFEWS model. If you only want to recreate the data analysis and figures (step 5), you can just setup CALFEWS on a local desktop/laptop. If you also want to recreate the full multiobjective intelligent search experiment, then you will need to access to a large computing cluster, and should set up CALFEWS there as well. The submission scripts are set up to run largescale analysis on Bridges-2 at the Pittsburgh Supercomputing Center (PSC), and smaller postprocessing jobs on Cornell Center for Advanced Computing (CAC) TheCube cluster. If you want to replicate this analysis on different machines, you will need to alter the SLURM submission scripts to match your machine(s).
2. Then switch back to this "MORDM_experiment_paper1" branch and copy all `*.sh` and `*.py` files from the `MORDM_experiment/paper1/` directory into the main directory of this repository.
3. Run the cythonization command, `python3 setup_cy.py build_ext --inplace`, on all machines. This step converts Cython   files (`*.pyx`, `*.pxd`) into C analogues (`*.c`) and then compiles them into dynamic libraries (`*.so` for Linux/Unix, `*.pyd` for Windows). These dynamic libraries can be called as fast C code from within a Python script.
4. Obtain additional software for the computer cluster where you will run the multi-objective optimization and large-scale resampling experiments.
    - Download the [Borg MOEA](http://borgmoea.org/) source code, using the `alh_python_checkpointing` branch of the Master-Worker repository, as demonstrated in [this blog post](https://waterprogramming.wordpress.com/2022/04/13/checkpointing-and-restoring-runs-with-the-borg-moea/). Compile the source code in 2 steps (borg.c with gcc, borgms.c with mpicc) in a separate directory as described in post above, then copy the compiled binaries `libborg.so` and `libborgms.so` , as well as the Python wrapper `borg.py` from the `Python/` directory, to the base directory of the current repo.
    - Download the "Compiled Binaries" from the [MOEAFramework](http://www.moeaframework.org/) website and copy the `moeaframework.c` & `moeaframework.h` files (from the `MOEAFramework-*/examples` directory of the package) to the base directory of this repo.
    - Download the "Demo Application" from the [MOEAFramework](http://www.moeaframework.org/) website and copy `MOEAFramework-*-Demo.jar` to the base directory of this repo.
    - Download `pareto.py` from [Github](https://github.com/matthewjwoodruff/pareto.py) and copy it to the base directory of this repo.

## Running the Multi-site Hidden Markov Model (MHMM) synthetic generator

1. 100 synthetic timeseries of inflows from the MHMM generator are stored at `calfews_src/data/MGHMM_synthetic/DailyQ_s{n}.csv`, where n is the sample 0-99. If you want to recreate these you can run `submmit_MGHMM_MOOWCU.sh` to the SLURM scheduler (set up for TheCube), or just run `generate_MGHMM_MOOWCU.py` on your local machine. Samples 0-21 are used for the multi-objective optimization, and samples 22-99 are used for the reevaluation step.

## Running the multi-objective optimization

1. First run the baseline simulations with no new infrastructure by submitting `submit_baselines_bridges2.sh` to the SLURM scheduler via sbatch. I ran all 100 simulations at once using a single job with 1 task of 50 cores on Bridgees-2 on the RM-shared partition. This took ~13 minutes.
2. Run `submit_moo_infra_bridges2.sh` for multiple seeds. Each submisssion uses 32 nodes on the RM partition on Bridges-2. I ran 3 seeds. For each, begin with numFEPrevious=0 (a fresh start for MOEA), and run for 48 hours.
3. Once each of these has finished, it will store results in `results/infra_moo/dv{dv_formulation}_seed{seed}/` -> move this to `results/MOO_results_bridges2/dv{dv_formulation}_seed{seed}_round1/` for storage.
4. Now create a new directory `results/infra_moo/dv{dv_formulation}_seed{seed}/` for the round 2 results to be written to. Within it, create a directory `checkpts/`. Within that, copy the file `results/MOO_results_s2/dv{dv_formulation}_seed{seed}_round1/checkpts/s{seed}_nfe{NFE_last}.checkpt` from the previous round's results, where NFE_last is the largest number file listed in this directory. This file represents a snapshot of the Borg MOEA's state after a particular number of function evaluations - snapshots are made every 100 evaluations. We want to use the most recent snapshot before the job ran out of time and exited. This will be used for a starting point for the second round.
5. Now within `submit_moo_infra.sh`, change `numFEPrevious` to this same value as the checkpoint file in the last step for each dv_formulation/seed combo, and rerun each seed for a second round.
6. Once these are complete, repeat steps 3-5 again in order to run a third round based on the checkpoint from the second round. Based on my available computing budget, I ran round 3 for 24 hours, for a total of 5 days computing across the 3 rounds for each seed.

## Postprocessing from the multi-objective optimization

1. Run `run_postprocess_pt1_MOO.sh` three times, one for each round's results. For each, uncomment the three lines related to that round's initial and final NFEs for each dv_formulation/seed combination. If you reran the MOO experiment yourself, replace the NFE values with those from your own, similar to the checkpoint files used for each round. This script will calculate the reference set for each seed and the objective values evolution throughout the run.
2. After running pt1 for all three rounds, run `run_postprocess_pt2_MOO.sh` for each round by uncommenting the appropriate lines for each. The rounds should be run in the proper order, beginning with round 1. This script will calculate the overall Pareto set across all dv_formulations/seeds (using `pareto.py`). The objective values for each solution in the Pareto set are stored as `results/MOO_results_bridges2/overall_ref/overall.reference`. Then the `find_runtime_metrics.sh` script calculates the performance metrics (e.g., Hypervolume) evolution throughout each run. Note this step is somewhat slow, so it will submmit jobs to the scheduler rather than running on the login node. Next, `find_operators.sh` collects the dynamics of the Borg MOEA's internal combination operator weights. 

## Running & postprocessing the reevaluation

1. Next, each solution from each of the four approximate Pareto sets from different random seed replicates (1146 in total) is reevaluated across 79 new hydrologic states-of-the-world (SOWs). `submit_wcu_infra.sh` should be submitted to the SLURM scheduler four times, with the `seed` variable set for 1-4 and the `numSolnsTotal` variable set to the number of solutions in that seed's Pareto set. Each submission will run `wcu_reeval_infra.py`, which loops over all solutions in that seed's Pareto set, for each SOW. I ran this on Bridges-2 with 2 RM nodes, 128 processors/mode, 6 processors/task. 
    - Results from the step above are stored in a separate hdf5 file for each MPI task, at `results/WCU_results_bridges2/results_rank{task}.hdf5`.
2. Run `submit_wcu_infra_statusquo.sh`, which will run the Status Quo Partnership on the same set of 79 scenarios.
3. Now run `run_postprocess_WCU.sh`, which runs several postprocessing steps.
    - First, `combine_hdf5.py` combines all of the separate results files from the previous steps into a single file, `results/WCU_results_bridges2/results.hdf5`. Note that I renamed this file `results_reevaluation_disagg.hdf5` for clarity in further analysis. This file contains 1147 datasets, one for each of the partnerships from the four seeds, plus the Status Quo Partnership. Each dataset dataset contains an array of results (e.g., if f is the open hdf5 file, `f['seed1/soln0'][...]` is the numeric results for the first partnership from seed 1). Rows are different metrics aggregated across time (e.g., PRT_avg_captured_water gives the average captured water gain for Porterville Irrigation District), with metric names given in `f['seed1/soln0'].attrs['rownames']`. Columns represent different SOWs, as labeled in `f['seed1/soln0'].attrs['colnames']`. The decision variable names and their values for each partnership are given in `f['seed1/soln0'].attrs['dv_names']` and `f['seed1/soln0'].attrs['dvs']`, respectively.
    - Next, `find_objs_WCU.py` loops over solutions in the results file and calculates the reevaluated objectives for each partnership, consistent with their definitions in the multi-objective optimization step. These are stored in `results/WCU_results_bridges2/objs_wcu.csv`.
    - Some of the partnerships from the Pareto set will have degraded upon reevaluation and are no longer non-dominated. The next step is to recalculate the Pareto set using `pareto.py`, with the same epsilon dominance parameters used in the optimization (`objs_wcu_pareto.csv`). The Status Quo solution is added back into a third file (`objs_wcu_pareto_withStatusQuo.csv`) since it is a dominated solution. 
    - Note that the `results/` directory is ignored by the Git repository, to avoid storing large files. The `results_arx/` directory is where smaller processed results files can be stored and backed up. Do not put any files >100 MB in here (or elsewhere in repository) or you will have to set up Git Large File Storage. All three of the `objs_wcu*.csv` files were copied to `results_arx/infra_wcu/` for longer term storage in the Git repository.
4. Run `submit_climate_reeval_bridges2.sh`, which submits `climate_reeval_infra.py` to the SLURM scheduler. This will run 20 different downscaled CMIP5 streamflow scenarios for the baseline no-infrastructure case, the Compromise Partnership from the final Pareto set (see next step for how this was selected), and the Status Quo partnership.

## Analyzing the results & creating figures

1. Once the optimization and reevaluation steps have been completed, the remaining analysis and figure generation can be done on a local computer after results have been copied there. Three basic dataset are needed from the optimization and reevaluation steps:
    - The full set of results from this work are too large to be included in the GitHub repository, but are packaged separately within the GitHub release associated with this branch.
2. Navigate to the `MORDM_experiment/paper1/` directory.
3. After downloading the `results_reevaluation_disagg.hdf5` file (either from the GitHub release or from your own reevaluation) and placing it in any location on your computer outside of the CALFEWS repository, update the `results_disagg_file` variable at the top of `fig_functions.py` with the correct absolute file path. Similarly, update the paths for the baseline no-infrastructure scenario results and the climate projection scenario results.
4. Run `make_figs.py`, which will run the analysis and create all figures from the paper (except those in the next step) in the `figs/` directory.
5. To generate the figures related to the MHMM synthetic hydrologic generator, run the following steps. You will need an R installation as well as Python.
    - Run `make_mhmm_figures_pt1.py`. This code fits the multi-site hidden Markov model, creates Figure S12-14 which assess goodness of fit of the model, and creates an example 110-year synthetic streamflow sample (`AnnualQ_s.csv`).
    - Run `daily_disaggregation.py` to disaggregate `AnnualQ_csv` to a daily timescale (`DailyQ_s.csv`).
    - Run `make_mhmm_figures_pt2.py`. This code creates Figures S10-11 which are correlation heat map plots that assess how well the model is maintaining spatial correlation in the synthetic traces. 
    - Run `aggregate_synthetic_traces.R` to aggregate the ensemble of synthetic traces (in `./calfews_src/data/MGHMM_synthetic/`) across locations. 
    - Run `make_mhmm_figures_pt3.py` to create Figure S7 which creates synthetic and historical flow duration curves at specific locations.



