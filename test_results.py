import numpy as np
import pandas as pd
import h5py
import sys

### Test function to check if two results files are equivalent (to make sure no errors have been introduced)
# To run: python3 -W ignore test_results.py <path_to_new_results> <path_to_old_results>

# results hdf5 file location
new_data = sys.argv[1]
old_data = sys.argv[2]
labelnum = sys.argv[3]
#output_file = "C:/Users/km663/Documents/Papers/ErrorPropagation/CALFEWS__Feb2020/ORCA_COMBINED-master/ORCA_COMBINED-master/cord/data/results/baseline_wy2017/p0"

# given a particular sensitivity factor sample number, get entire model output and output as dataframe
def get_results_sensitivity_number(results_file, labelnum):
  with h5py.File(results_file, 'r') as f:
    data = f['s' + str(labelnum)]
    print(data)
    names = data.attrs['columns']
    names = list(map(lambda x: str(x).split("'")[1], names))
    df_data = pd.DataFrame(data[:,0], columns=[names[0]])
    end = False
    col = 1
    while end==False:
      try:
        if sum(data[:,col]) > 1e-8:
          print(col)
          df_data[names[col]] = data[:,col]
          col += 1
        else:
          col += 1
      except:
        end = True
    print(df_data.head())
    #df_data = df_data.loc[df_data.sum(axis=0)>1e-8]
    return df_data

def test_results_same(new_data, old_data, labelnum):
  new_df = get_results_sensitivity_number(new_data, labelnum)
  old_df = get_results_sensitivity_number(old_data, labelnum)
  a = new_df - old_df
  print(np.abs(new_df.sum(axis=0)).min())
  print(np.abs(old_df.sum(axis=0)).min())
  print(a.sum(axis=1).max())
  pd.testing.assert_frame_equal(new_df, old_df)

if __name__ == '__main__':
  test_results_same(new_data, old_data, labelnum)
  print('TEST PASSED: RESULTS EQUAL')
