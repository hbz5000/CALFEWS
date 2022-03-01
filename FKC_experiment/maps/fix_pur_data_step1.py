
import numpy as np 
import matplotlib.colors as mplc
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import os 
import pdb
import pandas as pd
import seaborn as sns
import re 
# from mpl_toolkits.basemap import Basemap


# files = 'pur_pre_1990/pur1990'

def replace_bad_characters(year, county):
    directory = 'CA_cropland/pur_data_raw'

    if os.path.isdir(str('CA_cropland/pur_data_cleaned')):
        print('already made folder pur_data_cleaned')
    else:
        os.mkdir('CA_cropland/pur_data_cleaned')  #make cleaned directory 

    new_directory = 'CA_cropland/pur_data_cleaned'
    # 'pur1990/'
    #pdb.set_trace()
    # 'udc90_54.txt'

    # pdb.set_trace()
    final_two_digits = str(year)
    final_two_digits = final_two_digits[-2:]

    # file_to_change = pd.read_csv(os.path.join(directory, ( 'pur' + str(year)), 'udc' + str(final_two_digits) + '_' + str(file) + '.txt')) #, header = True, na_rep = '0', index = False) 
    file_to_change = (os.path.join(directory, ( 'pur' + str(year)), 'udc' + str(final_two_digits) + '_' + str(county).zfill(2) )) #, header = True, na_rep = '0', index = False) 
    new_file_with_location = (os.path.join(new_directory, ( 'pur' + str(year)), 'udc' + str(final_two_digits) + '_' + str(county).zfill(2) ))

    new = open(file_to_change + '.txt').read().replace('?','0')

    if os.path.isdir(str('CA_cropland/pur_data_cleaned/pur' + str(year))):
        a=1
    else:
        os.mkdir(str('CA_cropland/pur_data_cleaned/pur' + str(year)))
            # try:
            # except: 
    open(new_file_with_location + '_fixed.txt', 'w').write(new)

