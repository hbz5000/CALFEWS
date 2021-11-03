import numpy as np
import problem_infra


### execution params
#num_MC = 101
#num_procs = 16
#model_modes = ['simulation'] * num_MC
#flow_input_types = ['synthetic'] * num_MC
#flow_input_sources = ['capow_50yr_generic'] * num_MC
#MC_labels = [str(i) for i in range(num_MC)]     #['wet','dry']


### uncertainties
#uncertainty_dict = {}
# uncertainty_dict['MDD_multiplier'] = 1.1
# uncertainty_dict['ag_demand_multiplier'] = {'crop': {'maj_orchardvineyard':1.1, 'maj_other':0.8}, 'friant': {'friant': 0.9, 'non_friant': 1.0}}

# uncertainty_dict['env_min_flow_base'] = {'MIL': 150., 'PFT': 150., 'KWH': 35., 'SUC': 15., 'ISB':75, 'SHA': 3000, 'ORO':1500}
# uncertainty_dict['env_min_flow_peak_multiplier'] = {'MIL': 1.1, 'PFT': 1.1, 'KWH': 1.1, 'SUC': 1.1, 'ISB': 1.1, 'SHA': 2, 'ORO':1.5}
# uncertainty_dict['delta_min_outflow_base'] = 3500
# uncertainty_dict['delta_min_outflow_peak_multiplier'] = 1.2



### first run baseline version
### decision variables for problem
#dvs = np.zeros(42)
#problem_infra.problem_infra(*dvs, is_baseline=True)





# ### now run for each of 3 infrastructure scenarios from exploratory study
###27283 :  ['ARV', 'LWT', 'DLE', 'SSJ', 'OFK', 'TUL', 'SFW', 'COF', 'LND', 'SAU', 'TBA', 'LDS', 'PRT', 'FRS', 'EXE', 'TPD'] :  [0.136207165, 0.135494501, 0.134481079, 0.11488389800000001, 0.075812672, 0.073845762, 0.063438028, 0.06162258599999999, 0.040607704, 0.031784396, 0.029784795, 0.028243958, 0.025589446000000002, 0.022890257, 0.017610656000000002, 0.0077030959999999996]
###14983 :  ['LHL', 'KRT', 'OTL', 'KND', 'SOC', 'NKN', 'ARV', 'TUL'] :  [0.2042886185766813, 0.1794291485898997, 0.1492737685922382, 0.1427780807519122, 0.1230885688261011, 0.0897598541362769, 0.0890444390183038, 0.0223375215085865]
###8071 :  ['ID4', 'LWT', 'PIX'] :  [0.3632764114896976, 0.3381612256546455, 0.2985623628556568]

### ownership shares dict   "ownership_shares":           {
#    "FRS": 1.0,
#    "COF": 1.0,
#    "OFK": 1.0,
#    "TUL": 1.0,   4
#    "KWD": 1.0,
#    "OKW": 1.0,
#    "EXE": 1.0,
#    "LDS": 1.0,
#    "LND": 1.0,
#    "PRT": 1.0,
#    "LWT": 1.0,   11
#    "OTL": 1.0,   12
#    "TPD": 1.0,
#    "SAU": 1.0,
#    "TBA": 1.0,
#    "OXV": 1.0,
#    "PIX": 1.0,   17
#    "DLE": 1.0,
#    "KRT": 1.0,   19
#    "SSJ": 1.0,
#    "SFW": 1.0,
#    "NKN": 1.0,   22
#    "ARV": 1.0,   23
#    "DLR": 1.0,
#    "KCWA": 1.0,
#    "ID4": 1.0,    26
#    "SMI": 1.0,
#    "TJC": 1.0,
#    "BLR": 1.0,
#    "LHL": 1.0,    30
#    "BDM": 1.0,
#    "WRM": 1.0,
#    "SOC": 1.0,   33
#    "COB": 1.0,
#    "BVA": 1.0,
#    "CWO": 1.0,
#    "HML": 1.0,
#    "KND": 1.0,   38
#    "RRB": 1.0,
#    "SOB": 1.0,
#    "CCA": 1.0
#  }




### decision variables for problem - alt3
dvs = np.zeros(42)
dvs[0] = 3
dvs[11] = 0.3381612256546455
dvs[17] = 0.2985623628556568
dvs[26] = 0.3632764114896976
objs_MCagg, constrs_MCagg = problem_infra.problem_infra(*dvs, is_baseline=False)
print(objs_MCagg, constrs_MCagg)


### decision variables for problem - alt8
###14983 :  ['LHL', 'KRT', 'OTL', 'KND', 'SOC', 'NKN', 'ARV', 'TUL'] :  [0.2042886185766813, 0.1794291485898997, 0.1492737685922382, 0.1427780807519122, 0.1230885688261011, 0.0897598541362769, 0.0890444390183038, 0.0223375215085865]
#dvs = np.zeros(42)
#dvs[0] = 3
#dvs[30] = 0.2042886185766813
#dvs[19] = 0.1794291485898997
#dvs[12] = 0.1492737685922382
#dvs[38] = 0.1427780807519122
#dvs[33] = 0.1230885688261011
#dvs[22] = 0.0897598541362769
#dvs[23] = 0.0890444390183038
#dvs[4] = 0.0223375215085865
#objs_MCagg, constrs_MCagg = problem_infra.problem_infra(*dvs, is_baseline=False)
#print(objs_MCagg, constrs_MCagg)



### decision variables for problem - friant16
###27283 :  ['ARV', 'LWT', 'DLE', 'SSJ', 'OFK', 'TUL', 'SFW', 'COF', 'LND', 'SAU', 'TBA', 'LDS', 'PRT', 'FRS', 'EXE', 'TPD'] :  [0.136207165, 0.135494501, 0.134481079, 0.11488389800000001, 0.075812672, 0.073845762, 0.063438028, 0.06162258599999999, 0.040607704, 0.031784396, 0.029784795, 0.028243958, 0.025589446000000002, 0.022890257, 0.017610656000000002, 0.0077030959999999996]
#dvs = np.zeros(42)
#dvs[0] = 1
#dvs[23] = 0.136207165
#dvs[11] = 0.135494501
#dvs[18] = 0.134481079
#dvs[20] = 0.11488389800000001
#dvs[3] = 0.075812672
#dvs[4] = 0.073845762
#dvs[21] = 0.063438028
#dvs[2] = 0.06162258599999999
#dvs[9] = 0.040607704
#dvs[14] = 0.031784396
#dvs[15] = 0.029784795
#dvs[8] =  0.028243958
#dvs[10] =  0.025589446000000002
#dvs[1] = 0.022890257
#dvs[7] =  0.017610656000000002
#dvs[13] = 0.0077030959999999996
#objs_MCagg, constrs_MCagg = problem_infra.problem_infra(*dvs, is_baseline=False)
#print(objs_MCagg, constrs_MCagg)





