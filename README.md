# California Food-Energy-Water System (CALFEWS)
This repository contains all code and data for the California Food-Energy-Water System (CALFEWS), an open-sourced, Python-based model for simulating the integrated, multi-sector dynamics of water supply in the Central Valley of California.  CALFEWS captures system dynamics across multiple scales, from coordinated management of inter-basin water supply projects at the state and regional scale, to agent-based representation of conjunctive surface water and groundwater supplies at the scale of irrigation and water storage districts. Its flexible, adaptive, rules-based representation allows CALFEWS to explore alternative climate, infrastructure, and regulation scenarios, and it is also interoperable with power dispatch and agricultural production models. This tool can provide decision-makers and analysts with a platform to generate a wide range of internally consistent scenarios for the integrated management of water supply, energy generation, and food production.

More information on the CALFEWS model, and comparison of model output to historical data, can be found in the following manuscript:

Zeff, H.B., Herman, J.D., Hamilton, A.L., Malek, K., Cohen, J.S., Medellin-Azuara, J., Reed, P.M., and G.W. Characklis. (2020). "Paper title." *Journal Name*. (In preparation). **TODO-update paper details**

Licensed under the MIT License, 2017.

## Installation and setup
1. Clone this repository to your local machine.
1. If you use Anaconda:
    1. Create a new environment using the yml file: ``conda env create -f environment.yml``
    1. Activate environment: ``conda activate .venv_conda_calfews``
1. If you don't use Anaconda:
    1. Manually install the packages listed in ``environment.yml``
1. Run model with ``python -W ignore run_main_cy.py``, or run ``run_main_cy.py`` from your favorite IDE. (Note: the command for Python 3 may be python3, not python, depending on your machine).
1. If this doesn't work (or you want to make any changes to source files), you will need to recompile the model, which includes C binaries from Cython. 
    1. If you are running on Linux or MacOS, you should already have gcc installed. If you are running on Windows, you will need to install Visual Studio 2019 Community Edition. When it asks which programs to install, choose "Desktop development with C++".
    1. Cythonize and recompile with the command: ``python setup_cy.py build_ext --inplace``.
1. For more details on model parameters, input files, and output files, run the Jupyter Notebook ``CALFEWS_intro_tutorial.ipynb``.
1. To run all simulations and reproduce all figures from Zeff et al. 2020 (in preparation), run the Jupyter Notebook ``modeling_paper_notebook.ipynb``.
