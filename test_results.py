import numpy as np
import pandas as pd
import h5py
import sys

### Test function to check if two results files are equivalent (to make sure no errors have been introduced)
# To run: python3 -W ignore test_results.py <path_to_new_results> <path_to_old_results>

# results hdf5 file location
new_data = sys.argv[1]
old_data = sys.argv[2]
#output_file = "C:/Users/km663/Documents/Papers/ErrorPropagation/CALFEWS__Feb2020/ORCA_COMBINED-master/ORCA_COMBINED-master/cord/data/results/baseline_wy2017/p0"

# given a particular sensitivity factor sample number, get entire model output and output as dataframe
def get_results_sensitivity_number(results_file, sensitivity_number):
  with h5py.File(results_file, 'r') as f:
    data = f['s0']# + str(sensitivity_number)]
    names = data.attrs['columns']
    names = list(map(lambda x: str(x).split("'")[1], names))
    df_data = pd.DataFrame(data[:], columns=names)
    return df_data

def test_results_same(new_data, old_data):
  new_df = get_results_sensitivity_number(new_data, 0)
  old_df = get_results_sensitivity_number(old_data, 0)
  a = new_df - old_df
  print(a.sum(axis=0).max())
  print(a.sum(axis=1).max())
  pd.testing.assert_frame_equal(new_df, old_df)

if __name__ == '__main__':
  test_results_same(new_data, old_data)
  print('TEST PASSED: RESULTS EQUAL')
