# California Food-Energy-Water System (CALFEWS)
For general information on the California Food-Energy-Water System (CALFEWS) simulation model, please switch to the "main" branch of this repository, where you will find information on installing, compiling, running, and analyzing the base model. Interested readers can also refer to the following paper to learn more about the performance and conceptual underpinnings of the model:

Zeff, H.B., Hamilton, A.L., Malek, K., Herman, J.D., Cohen, J.S., Medellin-Azuara, J., Reed, P.M., and G.W. Characklis. (2021). California's Food-Energy-Water System: An Open Source Simulation Model of Adaptive Surface and Groundwater Management in the Central Valley. *Environmental Modelling & Software, 141*: 105052. [https://doi.org/10.1016/j.envsoft.2021.105052](https://doi.org/10.1016/j.envsoft.2021.105052) 

Licensed under the MIT License, 2017-2022.

# Multi-Objective Robust Decision Making (MORDM) for infrastructure partnership design; Part 1
This "MORDM_experiment_paper1" branch of the repository contains code and data for the first in a two-part series on using MORDM to design water supply infrastructure partnerships that provide robust benefits to all partners under uncertainty. This first paper focuses on the Multi-Objective Optimization, using the Borg MOEA, to discover partnerships that perform well across multiple objectives. This first step only uses "well characterized" uncertainty in future streamflows. A follow on study will reevaluate high-performing solutions across a range of deeply uncertain factors related to hydrology, demand, regulation, and cost.

## Installation and setup
1. First, switch to the "main" branch of this repository and follow instructions to clone, compile, and run the base CALFEWS model. If you only want to recreate the data analysis and figures (step 5), you can just setup CALFEWS on a local desktop/laptop. If you also want to recreate the full MORDM experiment, then you will need to access to a larger computing cluster, and should set up CALFEWS there as well.
2. Then switch back to this "MORDM_experiment_paper1" branch and run the cythonization command, `python3 setup_cy.py build_ext --inplace`, on all machines. 
3. Obtain additional software for the computer cluster where you will run the multi-objective optimization and large-scale resampling experiments.
  * Download the [Borg MOEA](http://borgmoea.org/) source code, using the `alh_python_checkpointing` branch of the Master-Worker algorithm, as demonstrated in [this blog post](https://waterprogramming.wordpress.com/2022/04/13/checkpointing-and-restoring-runs-with-the-borg-moea/). Compile the source code in a separate directory, then copy the compiled binaries `libborg.so` and `libborgms.so`, as well as the Python wrapper `borg.py`, to the base directory of the current repo.
  * Download the "Compiled Binaries" from the [MOEAFramework](http://www.moeaframework.org/) website and copy the `moeaframework.c` &amp `moeaframework.h` files (from the `MOEAFramework-*/examples` directory of the package) to the base directory of this repo. 
  * Download the "Demo Application" from the [MOEAFramework](http://www.moeaframework.org/) website and copy `MOEAFramework-*-Demo.jar` to the base directory of this repo.
  * Download `pareto.py` from [Github](https://github.com/matthewjwoodruff/pareto.py) and copy it to the base directory of this repo.
3. Instructions TBD
