### Compile and read PUR formatted data 

import numpy as np 
import matplotlib.colors as mplc
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import os 
import pdb
import pandas as pd
import re 

# pdb.set_trace()
def read_data(year):

    directory='CA_cropland/pur_data_with_comtrs'
    tlb_overall_data = pd.read_csv(os.path.join(directory, str('comtrs_pur_vals_year' + str(year) + '.csv') ) )

    if year < 1990:
        tlb_overall_data.acre_unit_treated = tlb_overall_data.acre_unit_treated.values / 100 # divide by 100 since original database does not include decimal point
        crop_list = np.int64(tlb_overall_data.commodity_code.unique())

    if year > 1989:
        crop_list = np.int64(tlb_overall_data.site_code.unique())

    return crop_list, tlb_overall_data

def make_dataframe(year, tlb_overall_data, crop_list): # Build empty dataframe for the crop acreage summations 
    
    all_COMTRS = tlb_overall_data.comtrs.unique()
    array_zeros1 = np.full((len(all_COMTRS), len(crop_list)), 0) #array of zeros for dataset
    crop4_df = pd.DataFrame(array_zeros1, index = [all_COMTRS], columns = [ str(crop_type) for crop_type in crop_list ] )   # makes overall dataframe for all crop types 
    array_tulare = np.full((1, 1), 0)
    tulare_overall_by_crop = pd.DataFrame(array_tulare, columns = ['year'])
    # pdb.set_trace()
    tulare_overall_by_crop['year'] = year 
    # pdb.set_trace()
    return crop4_df, tulare_overall_by_crop  #returns framework for the compiled crop types by comtrs, and tulare_overall_by_crop (to be used later)


def calculate_acres_pre_1990(year, crop_type, crop_iter, crop_list, tlb_overall_data): # for a given set of comtrs, calculate total tree crop acreage 
    
    crop_type_vals = tlb_overall_data.loc[lambda df: tlb_overall_data.commodity_code == crop_type, : ]  # pulls permits for each of the crop types (filters for only this crop)

    COMTRS_list = crop_type_vals.comtrs.unique()
    no_COMTRS = len(crop_type_vals.comtrs.unique())   # number of unique COMTRS that grow specific crop 
    
    crop_column = crop_list[crop_iter]
    crop_iter = crop_iter + 1
    crop_acres_tulare = 0 # reset crop acreage to zero 

    save_crop_file = 1 
    if save_crop_file == 1:
        # path='/Users/nataliemall/Box Sync/herman_research_box/calPIP_crop_acreages'
        # directory_overall_folder 
        if not os.path.isdir("CA_cropland/calPIP_PUR_crop_acreages"):
            os.mkdir('CA_cropland/calPIP_PUR_crop_acreages')

    array_zeros = np.zeros([no_COMTRS, 1])  # array of the length of COMTRS for alfalfa
    crop2_df = pd.DataFrame(array_zeros, index = [COMTRS_list], columns = [str(crop_column)] )   # change column label to each type of crop 
    # COMTRS_iter = 0 
    crop_acres_list = np.zeros([no_COMTRS, 1])
    # pdb.set_trace()

    for COMTRS_iter, COMTRS_value in enumerate(COMTRS_list): 
        # pdb.set_trace()
        everything_in_this_comtrs = crop_type_vals.loc[crop_type_vals['comtrs'] == COMTRS_value, :]  # filters by fields in this specific COMTRS section 

        batch_IDs = everything_in_this_comtrs.batch_no.unique()  # array of unique batch registration values in section
        num_batches = len(batch_IDs)   # number of parcels within the COMTRS

        acreages_for_each_batch = np.zeros([num_batches, 1])  # empty array for the summed acreage for each parcel (site location)
        # pdb.set_trace()

        try:
            for batch_num, individual_batch in enumerate(batch_IDs): #goes through the individual sites in the secition 
                # pdb.set_trace()
                # print('I think here is where the problem is')
                specific_registrant = everything_in_this_comtrs.loc[everything_in_this_comtrs.batch_no == individual_batch] # locates all permits a specific site
                # pdb.set_trace()
                # if specific_parcel.acre_unit_treated
                try:
                    total_at_this_batch = max(specific_registrant.acre_unit_treated)  # maximum acreage reported for that SITE_LOCATION_ID 
                except: 
                    # pdb.set_trace()
                    print('test this exception')
                    total_at_this_batch = 0 
                    print(f'No value for amount planted at COMTRS {COMTRS_value} at registrant {individual_batch}')

                # commented these back in
                # if pd.isnull(individual_site) == True or individual_site == np.nan:   # If site_ID is not labelled
                #     total_at_site_loc = sum(specific_parcel.AMOUNT_PLANTED.unique()) # sum up all unique area values
                acreages_for_each_batch[batch_num] = total_at_this_batch
                total_in_COMTRS = sum(acreages_for_each_batch)
        except:
            total_in_COMTRS = O 

        try:
            crop_acres_list[COMTRS_iter] = total_in_COMTRS  #puts all of this crop for this comtrs in the crop_acres_list
        except:
            crop_acres_list[COMTRS_iter] = 0 

    try:
        # crop2_df[lambda crop2_df: crop2_df.columns[0]] = crop_acres_list  # crop acreage list for this specific crop # risk of misassigning
        crop_type_string = str(crop_type)
        crop2_df[crop_type_string] = crop_acres_list   #tried this method instead so nothing gets misassigned 
        # crop_test = crop4_df.loc[crop4_df.index == '10M10S13E34']
        # pdb.set_trace()

        save_acres = 1     # Saves each crop's data for each COMTRS 
        if save_acres == 1:
            crop3_df = crop2_df.reset_index()
            crop3_df.columns = ['COMTRS', str(crop_column)]
            year_string = str(year) 
            year_two_digits = year_string[-2:]
            # directory=os.path.join('/Users/nataliemall/Box Sync/herman_research_box/calPIP_PUR_crop_acreages', str(year) + 'files' )
            directory=os.path.join('CA_cropland', 'calPIP_PUR_crop_acreages', year_two_digits + 'files' )
            # try: 
            #     crop3_df.to_csv(os.path.join(directory, (year_two_digits + 'crop' + str(crop_column) + '_by_COMTRS'+ '.csv' ) ), header = True, na_rep = '0', index = False)   
            #     # pdb.set_trace()
            # except: 
            #     os.mkdir(directory) 
            #     crop3_df.to_csv(os.path.join(directory, (year_two_digits + 'crop' + str(crop_column) + '_by_COMTRS' + '.csv' ) ), header = True, na_rep = '0', index = False)

            # comtrs_with_crop
    except:
        print('crop2_df make have been empty for this crop type')

    # if crop_type == 3101:
    #     pdb.set_trace()
    return crop2_df, directory, crop_column, crop_iter, crop_acres_tulare

def calculate_acres_1990_2016(year, crop_type, tlb_overall_data): # for a given set of comtrs, calculate total tree crop acreage
    # overall_data = pd.read_csv('/Users/nataliemall/Box Sync/herman_research_box/calPIP_crop_acreages/overall_results.csv', sep = '\t', index_col =0) 

    # total_skipped = 0 
    # calPIP_data
    crop_type_vals = tlb_overall_data.loc[lambda df: tlb_overall_data.site_code == crop_type, : ]  # pulls permits for each of the crop types (filters for only this crop)
    # pdb.set_trace()
    # no_reg_firm_IDs = len(crop_type_vals.reg_firm_no.unique()) # number of registration firms for a specific crop 
    ## ^ Edit location ID search - test for different SITE_LOCATION_ID
    # number_of_null_site_location_ids = sum(pd.isnull(crop_type_vals.reg_firm_no))

    COMTRS_list = crop_type_vals.comtrs.unique()
    no_COMTRS = len(crop_type_vals.comtrs.unique())   # number of unique COMTRS that grow specific crop 
    
    crop_acres_tulare = 0 # reset crop acreage to zero 
    # pdb.set_trace()

    save_crop_file = 1 
    if save_crop_file == 1:
        # path='/Users/nataliemall/Box Sync/herman_research_box/calPIP_crop_acreages'
        # directory_overall_folder 
        if not os.path.isdir("CA_cropland/calPIP_PUR_crop_acreages"): 
            os.mkdir('CA_cropland/calPIP_PUR_crop_acreages')

    array_zeros = np.zeros([no_COMTRS, 1])  # array of the length of COMTRS for alfalfa
    crop2_df = pd.DataFrame(array_zeros, index = [COMTRS_list], columns = [str(crop_type)] )   # change column label to each type of crop 
    # COMTRS_iter = 0 
    crop_acres_list = np.zeros([no_COMTRS, 1])
    # pdb.set_trace()

    for COMTRS_iter, COMTRS_value in enumerate(COMTRS_list): 
        # pdb.set_trace()
        everything_in_this_comtrs = crop_type_vals.loc[crop_type_vals['comtrs'] == COMTRS_value, :]  # filters by fields in this specific COMTRS section 

        site_loc_IDs = everything_in_this_comtrs.site_loc_id.unique()  # array of unique batch registration values in section
        num_site_loc_IDs = len(site_loc_IDs)   # number of parcels within the COMTRS

        acreages_for_each_site_loc_id = np.zeros([num_site_loc_IDs, 1])  # empty array for the summed acreage for each parcel (site location)
        try: 
            if len(everything_in_this_comtrs) > 0: 
                for loc_id_num, individual_batch in enumerate(site_loc_IDs): #goes through the individual sites in the secition 
                    specific_registrant = everything_in_this_comtrs.loc[everything_in_this_comtrs.site_loc_id == individual_batch] # locates all permits a specific site
                    # pdb.set_trace()
                    # if specific_parcel.acre_planted
                    try:
                        total_at_this_site_loc = max(specific_registrant.acre_planted)  # maximum acreage reported for that SITE_LOCATION_ID 
                    except: 
                        total_at_this_site_loc = 0 
                        print(f'No value for amount planted at COMTRS {COMTRS_value} at registrant {individual_batch}')

                    # commented these back in
                    # if pd.isnull(individual_site) == True or individual_site == np.nan:   # If site_ID is not labelled
                    #     total_at_site_loc = sum(specific_parcel.AMOUNT_PLANTED.unique()) # sum up all unique area values
                    acreages_for_each_site_loc_id[loc_id_num] = total_at_this_site_loc
                    total_in_COMTRS = sum(acreages_for_each_site_loc_id)
                    
            else: 
                total_in_COMTRS = 0 

        except:
            print('THIS is throwhing an exeption')

        crop_acres_list[COMTRS_iter] = total_in_COMTRS  #puts all of this crop for this comtrs in the crop_acres_list
    
    # pdb.set_trace()

    try:
        # crop2_df[lambda crop2_df: crop2_df.columns[0]] = crop_acres_list  # crop acreage list for this specific crop # risk of misassignment 
        crop_type_string = str(crop_type)
        crop2_df[crop_type_string] = crop_acres_list   #tried this method instead so nothing gets misassigned 
        # crop_test = crop4_df.loc[crop4_df.index == '10M10S13E34']
        # pdb.set_trace()
        #if save_crop_file == 1:  # Saves each crop's data for each COMTRS 
            #crop3_df = crop2_df.reset_index()
            #print(crop3_df)
            #print(crop_column)
            #crop3_df.columns = ['COMTRS', str(crop_column)]
            #print(crop3_df.columns)
            #year_string = str(year)
            #print(year_string)			
            #year_two_digits = year_string[-2:]
            #print(year_two_digits)
            # directory=os.path.join('/Users/nataliemall/Box Sync/herman_research_box/calPIP_PUR_crop_acreages', str(year) + 'files' )
            # directory=os.path.join('/Users/nataliemall/Box Sync/herman_research_box/calPIP_PUR_crop_acreages', year_two_digits + 'files' )
            # try: 
            #     crop3_df.to_csv(os.path.join(directory, (year_two_digits + 'crop' + str(crop_column) + '_by_COMTRS'+ '.csv' ) ), header = True, na_rep = '0', index = False)   
            #     # pdb.set_trace()
            # except: 
            #     os.mkdir(directory) 
            #     crop3_df.to_csv(os.path.join(directory, (year_two_digits + 'crop' + str(crop_column) + '_by_COMTRS' + '.csv' ) ), header = True, na_rep = '0', index = False)

            # comtrs_with_crop
    except:
        print('crop2_df may have been empty for this crop type')

    # pdb.set_trace()
    return crop2_df, crop_acres_tulare


def compile_data_by_comtrs(year): 
    '''Compiles 1974 - 2016 data by comtrs'''
    crop_list, tlb_overall_data = read_data(year)
    # pdb.set_trace()
    # print('check tlb_overall_data here')
    crop4_df, tulare_overall_by_crop = make_dataframe(year, tlb_overall_data, crop_list)    # make dataframe for the crop acreage summations     
    # pdb.set_trace()
    crop_iter = 0 
    if year < 1990:
        for crop_type in crop_list:  # Runs for each crop type in calPIP database, then connects to larger calPIP array using COMTRS index 
            try:
                # deleted variable directory - hopefully this solves it!!! 
                crop2_df, directory, crop_column, crop_iter, crop_acres_tulare = calculate_acres_pre_1990(year, crop_type, crop_iter, crop_list, tlb_overall_data)  # sum up acreages for each crop type 
                # pdb.set_trace()
                crop4_df[crop_column] = crop2_df[str(crop_column)].loc[crop2_df.index]  # Puts the individual crop acreage list into the overall dataframe crop4_df 
                # tulare_overall_by_crop[crop_column] = crop_acres_tulare
            except:
                crop_iter = crop_iter + 1 
                print(f'crop2 dataframe may have been empty for this crop type number {crop_type}')
                # pdb.set_trace()
    if year > 1989:
        for crop_type in crop_list:  # Runs for each crop type in calPIP database, then connects to larger calPIP array using COMTRS index 
            try:
                # pdb.set_trace()
                # print('run this by hand')
                crop2_df, crop_acres_tulare = calculate_acres_1990_2016(year, crop_type, tlb_overall_data)  # sum up acreages for each crop type 
                # pdb.set_trace()
                crop4_df.loc[crop2_df.index, str(crop_type)] = crop2_df[str(crop_type)]
                # Puts the individual crop acreage list into the overall dataframe crop4_df 
                # tulare_overall_by_crop[crop_column] = crop_acres_tulare
            except:
                print(f'crop2 dataframe may have been empty for this crop type number {crop_type}')    
    
    crop5_df = crop4_df.reset_index()
    # crop6_df = crop5_df.rename(columns={"level_0": "comtrs"})
    # crop7_df = crop5_df.set_index("comtrs")
    year_string = str(year) 
    year_two_digits = year_string[-2:]
    directory=os.path.join('CA_cropland', 'calPIP_PUR_crop_acreages', year_two_digits + 'files' )

    if not os.path.isdir(directory):  # creates this folder 
        os.mkdir(directory)
    # try:
    crop5_df.to_csv(os.path.join(directory, ('all_data_year' + year_two_digits + '_by_COMTRS' + '.csv' ) ), header = True, na_rep = '0', index = False, sep = '\t')

    # pdb.set_trace()
    # for this year, extract a subset of columns whose crop_ID is either a tree crop or annual crop

    codes_pre_1990 = pd.read_csv('CA_cropland/site_codes_with_crop_types.csv', usecols = ['site_code_pre_1990', 'site_name_pre_1990', 'is_orchard_crop_pre_1990', 'is_annual_crop_pre_1990', 'is_forage_pre_1990', 'applied_water_category_pre_1990']) # , index_col = 0)
    codes_1990_2016 = pd.read_csv('CA_cropland/site_codes_with_crop_types.csv', usecols = ['site_code_1990_2016', 'site_name_1990_2016', 'is_orchard_crop_1990_2016', 'is_annual_crop_1990_2016', 'is_forage_1990_2016', 'applied_water_category_1990_2016']) #, index_col = 0)

    # codes_useful_ones = codes_pre_1990.iloc[codes_pre_1990.is_orchard_crop_pre_1990 == 1]

    tree_crops_pre_1990 = codes_pre_1990.site_code_pre_1990.loc[codes_pre_1990.is_orchard_crop_pre_1990 == 1]
    tree_crops_pre_1990 = [str(round(i)) for i in tree_crops_pre_1990]

    tree_crops_1990_2016 = codes_1990_2016.site_code_1990_2016.loc[codes_1990_2016.is_orchard_crop_1990_2016 == 1]
    tree_crops_1990_2016_list = tree_crops_1990_2016.values.tolist()  # why necessary?  
    tree_crops_1990_2016 = [str(round(i)) for i in tree_crops_1990_2016_list]

    forage_crops_pre_1990 = codes_pre_1990.site_code_pre_1990.loc[codes_pre_1990.is_forage_pre_1990 == 1]
    forage_crops_pre_1990 = [str(round(i)) for i in forage_crops_pre_1990]

    forage_crops_1990_2016 = codes_1990_2016.site_code_1990_2016.loc[codes_1990_2016.is_forage_1990_2016 == 1]
    forage_crops_1990_2016_list = forage_crops_1990_2016.values.tolist()
    forage_crops_1990_2016 = [str(round(i)) for i in forage_crops_1990_2016_list]

    annual_crops_pre_1990 = codes_pre_1990.site_code_pre_1990.loc[codes_pre_1990.is_annual_crop_pre_1990 == 1]
    annual_crops_pre_1990 = [str(round(i)) for i in annual_crops_pre_1990]

    annual_crops_1990_2016 = codes_1990_2016.site_code_1990_2016.loc[codes_1990_2016.is_annual_crop_1990_2016 == 1]
    annual_crops_1990_2016_list = annual_crops_1990_2016.values.tolist()
    annual_crops_1990_2016 = [str(round(i)) for i in annual_crops_1990_2016_list]

    concatted_1990_2016 = [tree_crops_1990_2016_list + annual_crops_1990_2016_list + forage_crops_1990_2016_list]
    concatted_1990_2016_formatted = concatted_1990_2016[0]
    all_crops_1990_2016 = [str(round(i)) for i in concatted_1990_2016_formatted]


    concatted_pre_1990 = [tree_crops_pre_1990 + annual_crops_pre_1990 + forage_crops_pre_1990]
    all_crops_pre_1990 = concatted_pre_1990[0]

    # pdb.set_trace()

    if year < 1990: 
        integer_columns = np.int64(all_crops_pre_1990)

    if year > 1989:
        integer_columns = np.int64(all_crops_1990_2016)


    try:
        valid_crop_dataset = crop4_df.loc[:, all_crops_1990_2016] 
        valid_crop_dataset2 = valid_crop_dataset.reset_index()
        valid_crop_dataset3 = valid_crop_dataset2.rename(columns={"level_0": "comtrs"})
        valid_crop_dataset3.to_csv(os.path.join(directory, ('annual_perennial_data_year' + year_two_digits + '_by_COMTRS' + '.csv' ) ), header = True, na_rep = '0', index = False, sep = '\t')
    except:
      print('No crop types in county')
    # pdb.set_trace()



def normalize_data(year, county):
    '''normalize data '''
    # sum the total along the y-axis 
    # if >640, divide each by value 
    year_string = str(year) 
    year_two_digits = year_string[-2:]    
    directory=os.path.join('CA_cropland', 'calPIP_PUR_crop_acreages', year_two_digits + 'files' )
    if not os.path.isdir(directory):  # creates this folder 
        os.mkdir(directory)

    crop_df = pd.read_csv(os.path.join(directory, ('annual_perennial_data_year' + year_two_digits + '_by_COMTRS' + '.csv' ) ), sep = '\t')
    crop5_df = crop_df.rename(columns = { "index" : "comtrs"})
    # pdb.set_trace()
    valid_crop_dataset = crop5_df.set_index("comtrs")
    # valid_crop_dataset = crop_df

    total_acreage_each_comtrs = valid_crop_dataset.sum(axis = 1)

    valid_crop_dataset_normalized = valid_crop_dataset
    # pdb.set_trace()
    for num, comtrs in enumerate(valid_crop_dataset.index) :
        try:
          if total_acreage_each_comtrs.loc[comtrs] > 640:
            valid_crop_dataset_normalized.loc[comtrs] = valid_crop_dataset.loc[comtrs] * 640 / total_acreage_each_comtrs.loc[comtrs]
        except ValueError:
          if total_acreage_each_comtrs.loc[comtrs].iat[0] > 640:
            valid_crop_dataset_normalized.loc[comtrs] = valid_crop_dataset.loc[comtrs] * 640 / total_acreage_each_comtrs.loc[comtrs].iat[0]

        # total_acreage_each_comtrs.hist(bins = 100)
    
    valid_crop_dataset_normalized2 = valid_crop_dataset_normalized.reset_index()
    valid_crop_dataset_normalized3 = valid_crop_dataset_normalized2.rename(columns={"level_0": "comtrs"})
    valid_crop_dataset_normalized3.to_csv(os.path.join(directory, ('all_data_normalized_year' + year_two_digits + '_by_COMTRS_'+ str(county).zfill(2) + '.csv' ) ), header = True, na_rep = '0', index = False, sep = '\t')
    # valid_crop_dataset_normalized3.to_csv(os.path.join('calPIP_PUR_crop_acreages', ('all_data_normalized_year' + year_two_digits + '_by_COMTRS' + '.csv' ) ), header = True, na_rep = '0', index = False, sep = '\t')




 


    