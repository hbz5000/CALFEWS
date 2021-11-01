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
#    "TUL": 1.0,
#    "KWD": 1.0,
#    "OKW": 1.0,
#    "EXE": 1.0,
#    "LDS": 1.0,
#    "LND": 1.0,
#    "PRT": 1.0,
#    "LWT": 1.0,   11
#    "OTL": 1.0,
#    "TPD": 1.0,
#    "SAU": 1.0,
#    "TBA": 1.0,
#    "OXV": 1.0,
#    "PIX": 1.0,   17
#    "DLE": 1.0,
#    "KRT": 1.0,
#    "SSJ": 1.0,
#    "SFW": 1.0,
#    "NKN": 1.0,
#    "ARV": 1.0,
#    "DLR": 1.0,
#    "KCWA": 1.0,
#    "ID4": 1.0,    26
#    "SMI": 1.0,
#    "TJC": 1.0,
#    "BLR": 1.0,
#    "LHL": 1.0,
#    "BDM": 1.0,
#    "WRM": 1.0,
#    "SOC": 1.0,
#    "COB": 1.0,
#    "BVA": 1.0,
#    "CWO": 1.0,
#    "HML": 1.0,
#    "KND": 1.0,
#    "RRB": 1.0,
#    "SOB": 1.0,
#    "CCA": 1.0
#  }




### decision variables for problem
dvs = np.zeros(42)
dvs[0] = 3
dvs[11] = 0.3381612256546455
dvs[17] = 0.2985623628556568
dvs[26] = 0.3632764114896976
objs_MCagg, constrs_MCagg = problem_infra.problem_infra(*dvs, is_baseline=False)
print(objs_MCagg, constrs_MCagg)






#dvs = [2.6955096003821275, 0.3371666270161901, 0.45447130535134844, 0.29919481028318284, 0.91667768869471677, 0.81156352646918117, 0.8675874983583548, 0.012139991859938016, 0.55081417331258165, 0.41680343645084728, 0.53431275150140578, 0.66165148668495277, 0.030222980545419963, 0.38764613084207433, 0.92401153639052336, 0.27272881713526531, 0.12836770576619722, 0.7356453327777901, 0.44719054327513802, 0.5848228248266556, 0.64942030134830164, 0.36727552217600762, 0.14625586083770167, 0.37128944400960801, 0.51722718251804523, 0.15829590176192482, 0.39702464393270775, 0.62755667060323916, 0.1006579573966232, 0.98760692472281097, 0.63005402419484546, 0.9499417091603255, 0.86439296809593047, 0.28555082885677713, 0.58218198469425131, 0.10341694953465297, 0.1984988577194742, 0.85569922808923271, 0.3652270919096719, 0.76784888905655801, 0.99979852256360424, 0.50673547934431939 ]
#objs_MCagg, constrs_MCagg = problem_infra.problem_infra(*dvs, is_baseline=False)
