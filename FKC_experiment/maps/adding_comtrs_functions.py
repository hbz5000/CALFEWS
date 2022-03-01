### Compile and read PUR formatted data 

import numpy as np 
import os 
import pandas as pd
import re 

def add_comtrs_pre_1990(year): #adds the comtrs as a column # preliminary processing of 1974 - 1989 data
    final_two_digits = str(year)
    final_two_digits = final_two_digits[-2:]

    overall_data = pd.read_csv(str('pur_data_raw/pur' + str(year) + '/pur'+ str(final_two_digits) + '.txt'), sep = '\t')
    # tlb_overall_data = overall_data[overall_data.county_cd == 54] 16 15 10

    tlb_county_cds = [10, 15, 16, 54]
    tlb_overall_data = overall_data.loc[(overall_data["county_cd"].isin(tlb_county_cds)) ]

    #COMTRS:
    # COunty, Meridian, Township, Range, Section 
    tlb_county = np.int64(tlb_overall_data.county_cd)
    tlb_overall_data.county_cd = tlb_county

    tlb_overall_data = tlb_overall_data[~tlb_overall_data['township'].isnull()]
    tlb_township = np.int64(tlb_overall_data.township)
    tlb_overall_data.township = tlb_township

    try:
        tlb_range = np.int64(tlb_overall_data.range)
        # tlb_range = np.int64(tlb_overall_data.range)
    except:
        
        test = np.array(tlb_overall_data.range)
        test2 = test.tolist()
        where_are_NaNs = np.isnan(test2)
        test3 = tlb_overall_data.range
        test3[where_are_NaNs] = 99
        tlb_range = np.int64(test3)
    tlb_overall_data.range = tlb_range

    tlb_section = np.int64(tlb_overall_data.section)
    tlb_overall_data.section = tlb_section

    len_dataset = len(tlb_overall_data.section)
    COMTRS = pd.DataFrame()
    COMTRS2 = np.zeros(len_dataset)
    COMTRS['comtrs'] = COMTRS2
    tlb_overall_data['comtrs'] = np.zeros((len_dataset))

    array_township = tlb_overall_data.township.values 
    string_list_township = [str(item).zfill(2) for item in array_township]
    tlb_overall_data["township_string"] = string_list_township

    array_range = tlb_overall_data.range.values 
    string_list_range = [str(item).zfill(2) for item in array_range]
    tlb_overall_data["range_string"] = string_list_range

    array_section = tlb_overall_data.section.values
    string_list_section = [str(item).zfill(2) for item in array_section]
    tlb_overall_data["section_string"] = string_list_section

    # print('fix base line meridian here')
    # Replace "H" with "M" since this is clearly not using the Humbolt Meridian, but the Mount Diable meridian 
    # undone since this just exacerbated the problem 
    # tlb_overall_data.base_ln_mer = tlb_overall_data.base_ln_mer.replace('H', 'M')
    tlb_overall_data["base_ln_mer"]
    
    tlb_overall_data["comtrs"] = (tlb_overall_data["county_cd"].map(str) + tlb_overall_data["base_ln_mer"] + tlb_overall_data["township_string"]  + tlb_overall_data["tship_dir"] + tlb_overall_data["range_string"] + tlb_overall_data["range_dir"] + tlb_overall_data["section_string"])

    if os.path.isdir("pur_data_with_comtrs"):
        a=1
    else:
        os.mkdir('pur_data_with_comtrs')
    tlb_overall_data.to_csv(str('pur_data_with_comtrs/comtrs_pur_vals_year' + str(year) + '.csv'), index = False )
    


def add_comtrs_1990_2004(year, county): #adds the comtrs as a column # preliminary processing of 1990 - 2004 data
    final_two_digits = str(year)
    final_two_digits = final_two_digits[-2:]
    # Extract data from counties 10, 15, 16, 54
    county_string = '_' + str(county).zfill(2) + '_fixed.txt'
    overall_data_fresno = pd.read_csv(str('CA_cropland/pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + county_string), sep = ',', error_bad_lines = False, warn_bad_lines = True)
    #overall_data_kern = pd.read_csv(str('pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + '_15_fixed.txt'), sep = ',', error_bad_lines = False, warn_bad_lines = True)
    #overall_data_kings = pd.read_csv(str('pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + '_16_fixed.txt'), sep = ',', error_bad_lines = False, warn_bad_lines = True)
    #overall_data_tulare = pd.read_csv(str('pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + '_54_fixed.txt'), sep = ',', error_bad_lines = False, warn_bad_lines = True)

    full_dataset = [overall_data_fresno]

    for dataset_num, dataset in enumerate(full_dataset):
        
        tlb_county = np.int64(dataset.county_cd)
        dataset.county_cd = tlb_county

        dataset = dataset[~dataset['township'].isnull()]
        try: # fix township
            tlb_township = np.int64(dataset.township)
        except:
            
            number_exceptions = 0 
            tlb_township = np.zeros(len(dataset.township))
            for township_num, township in enumerate(dataset.township):
                try:
                    township = np.int64(township)
                    tlb_township[township_num] = township
                except:
                    number_exceptions = number_exceptions + 1
                    print(township)
                    print(number_exceptions)
                    tlb_township[township_num] = 99
        dataset.township = np.int64(tlb_township)    # added this in to round the numbers and remove decimals 
        try: # fix range
            tlb_range = np.int64(dataset.range)
                # tlb_range = np.int64(tlb_overall_data.range)
        except:   
            number_exceptions = 0 
            tlb_range = np.zeros(len(dataset.range))
            for range_num, range_val in enumerate(dataset.range):
                try:
                    range_val = np.int64(range_val)
                    tlb_range[range_num] = range_val
                except:
                    number_exceptions = number_exceptions + 1
                    print(range_val)
                    print(number_exceptions)
                    tlb_range[range_num] = 99

        dataset.range = np.int64(tlb_range)

        try:  # Fix sections
            tlb_section = np.int64(dataset.section)
                # tlb_range = np.int64(tlb_overall_data.range)
        except:
            number_exceptions = 0 
            tlb_section = np.zeros(len(dataset.section))
            for section_num, section_val in enumerate(dataset.section):
                try:
                    section_val = np.int64(section_val)
                    tlb_section[section_num] = section_val
                except:
                    number_exceptions = number_exceptions + 1
                    print(section_val)
                    print(number_exceptions)
                    tlb_section[section_num] = 99


            # tlb_section = np.int64(dataset.section)
        dataset.section = np.int64(tlb_section)


        len_dataset = len(dataset.section)
        COMTRS = pd.DataFrame()
        COMTRS2 = np.zeros(len_dataset)
        COMTRS['comtrs'] = COMTRS2
        dataset['comtrs'] = np.zeros((len_dataset))        

        try:
            array_township = dataset.township.values 
            string_list_township = [str(item).zfill(2) for item in array_township]
            dataset["township_string"] = string_list_township

            array_range = dataset.range.values 
            string_list_range = [str(item).zfill(2) for item in array_range]
            dataset["range_string"] = string_list_range

            array_section = dataset.section.values
            string_list_section = [str(item).zfill(2) for item in array_section]
            dataset["section_string"] = string_list_section

            dataset["base_ln_mer"] = dataset["base_ln_mer"].apply(str)
            dataset["tship_dir"] = dataset["tship_dir"].apply(str)
            dataset["range_dir"] = dataset["range_dir"].apply(str)

        except Exception as e: print(e)

        
        dataset["comtrs"] = (dataset["county_cd"].map(str) + dataset["base_ln_mer"] + dataset["township_string"]  + dataset["tship_dir"] + dataset["range_string"] + dataset["range_dir"] + dataset["section_string"])
        dataset = dataset.set_index(['comtrs'])
        if dataset_num == 0:
            tlb_overall_data = dataset
        else:
                # merge these 4 datasets together, run a function similar to calculate_acres_pre_1990(), output should be acres in each comtrs for each crop type (site_code)
            tlb_overall_data = pd.concat([tlb_overall_data, dataset])
        
    if os.path.isdir("CA_cropland/pur_data_with_comtrs"):
        a=1
    else:
        os.mkdir('CA_cropland/pur_data_with_comtrs')
    tlb_overall_data.to_csv(str('CA_cropland/pur_data_with_comtrs/comtrs_pur_vals_year' + str(year) + '.csv'), index = True )
    
    # tlb_overall_data.to_csv(str('comtrs_pur_vals_year' + str(year) + '.csv'), index = True )

def add_comtrs_2005_2016(year, county): #adds the comtrs as a column # preliminary processing of 2004 - 2016 data
    '''relatively simple since this dataset already includes the comtrs'''
    final_two_digits = str(year)
    final_two_digits = final_two_digits[-2:]
    
    # Extract data from counties 10, 15, 16, 54
    county_string = '_' + str(county).zfill(2) + '_fixed.txt'    
    overall_data_fresno = pd.read_csv(str('CA_cropland/pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + county_string), sep = ',', error_bad_lines = False, warn_bad_lines = True)
    #overall_data_kern = pd.read_csv(str('pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + '_15_fixed.txt'), sep = ',', error_bad_lines = False, warn_bad_lines = True)
    #overall_data_kings = pd.read_csv(str('pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + '_16_fixed.txt'), sep = ',', error_bad_lines = False, warn_bad_lines = True)
    #overall_data_tulare = pd.read_csv(str('pur_data_cleaned/pur' + str(year) +'/udc' + final_two_digits + '_54_fixed.txt'), sep = ',', error_bad_lines = False, warn_bad_lines = True)
    full_dataset = [overall_data_fresno,]

    for dataset_num, dataset in enumerate(full_dataset):
        if dataset_num == 0:
            tlb_overall_data = dataset
        else:
            tlb_overall_data = pd.concat([tlb_overall_data, dataset])

    if os.path.isdir("CA_cropland/pur_data_with_comtrs"):
        a=1
    else:
        os.mkdir('CA_cropland/pur_data_with_comtrs')
        
    tlb_overall_data.to_csv(str('CA_cropland/pur_data_with_comtrs/comtrs_pur_vals_year' + str(year) + '.csv'), index = True )
    


