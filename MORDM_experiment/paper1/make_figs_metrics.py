import pandas as pd
import time
import fig_functions

import warnings
warnings.filterwarnings('ignore')

fontsize = 14
fig_dir = 'figs/'

### function for printing fig completion with time
t0 = time.time()
def print_completion(fig_label):
    print(f'Finished {fig_label}, {round((time.time() - t0)/60, 2)} minutes')
    print()


fig_functions.plot_moo_metrics()
print_completion(f'optimization metrics figure')


