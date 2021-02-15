import sys
import os

results_folder = sys.argv[1]

os.mkdir(results_folder)  

import main_cy
main_cy_obj = main_cy.main_cy()
main_cy_obj.run_py(results_folder)
