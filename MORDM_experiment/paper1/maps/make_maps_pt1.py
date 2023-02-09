### First step in making maps from paper
### Andrew Hamilton, 2021-22

import numpy as np
import pandas as pd
import geopandas as gpd


project_folder = 'ca_geo'
projection_string = 'EPSG:4326'#project raster to data projection
projection_num = 4326
point_location_filename = project_folder + '/CALFEWS_RESERVOIRS.csv'#coordinates of map 'points'
shapefile_folder = project_folder + '/CALFEWS_shapes/'
districts_folder = project_folder + '/CALFEWS_shapes/Water_Districts/'
canal_folder = project_folder + '/CALFEWS_shapes/Canals_and_Aqueducts_local/'
raster_folder = project_folder + '/ca_satellite/'
outline_name = project_folder + '/CALFEWS_shapes/states.shp'#state outline

### link from CALFEWS keys (e.g. BDM) to shapefile keys (e.g. berrendamesawaterdistrict)
ag_keys = {
    'BDM': ['berrendamesawaterdistrict'], 'BLR': ['belridgewaterstoragedistrict'],
    'BVA': ['buenavistawaterstoragedistrict'],
    'CWO': ['cawelowaterdistrict'], 'HML': ['henrymillerwaterdistrict'], 'KND': ['kerndeltawaterdistrict'],
    'LHL': ['losthillswaterdistrict'],
    'RRB': ['rosedale-riobravowaterstoragedistrict'], 'SMI': ['semitropicwaterservicedistrict'],
    'THC': ['tehachapi-cummingscountywaterdistrict'],
    'TJC': ['tejon-castacwaterdistrict'], 'WKN': ['westkernwaterdistrict'],
    'WRM': ['wheelerridge-maricopawaterstoragedistrict'],
    'COB': ['bakersfieldcityof'], 'NKN': ['northkernwaterstoragedistrict'], 'ARV': ['arvin-edisonwaterstoragedistrict'],
    'PIX': ['pixleyirrigationdistrict'], 'DLE': ['delano-earlimartirrigationdistrict'],
    'EXE': ['exeterirrigationdistrict'],
    'KRT': ['kern-tulare'], 'LND': ['lindmore'], 'LDS': ['lindsay-strathmoreirrigationdistric'],
    'LWT': ['lowertule'], 'PRT': ['portervilleirrigationdistrict'], 'SAU': ['saucelito'],
    'SFW': ['shafter-wascoirrigationdistrict'],
    'SSJ': ['southernsanjoaquinmunicipalutilitydistrict'], 'TPD': ['teapot'], 'TBA': ['terrabellairrigationdistrict'],
    'TUL': ['tulareirrigationdistrict'],
    'COF': ['fresnocityof'], 'FRS': ['fresnoirrigation'],
    'DLR': ['dudleyridge'], 'TLB': ['tularelake'], 'KWD': ['kaweahdelta'], 'WSL': ['westlands'],
    'SNL': ['sanluiswater'],
    'PNC': ['panoche'], 'DLP': ['delpuerto'], 'CWC': ['chowchillawaterdistrict'], 'MAD': ['maderairrigationdistrict'],
    'CNS': ['consolidated'], 'ALT': ['altairrigationdistrict'],
    'KWB': ['kernwaterbank'],

    'OFK': ['hillsvalley', 'orangecoveirrigationdistrict', 'lewiscreek', 'lindsaycityof', 'stonecorral',
            'ivanhoeirrigationdistrict', 'orangecovecityof', 'tri-valleywaterdistrict', 'internationalwaterdistrict',
            'garfield', 'hiddenlakes', 'fresnocountywaterworksdistrictno18'],  # 'gravely'
    'KRWA': ['kingsriverwaterdistrict'],  # , 'kingsriverconservationdistrict'],
    'OEX': ['sanluiscanalcompany', 'centralcalifornia', 'firebaughcanalcompany', 'columbiacanalcompany'],
    'OCD': ['bantacarbonairrigationdistrict, byronbethanyirrigationdistrict', 'eaglefield', 'mercysprings',
            'oralomawaterdistrict', 'pajarovalleywatermanagementagency', 'pattersonwaterdistrict',
            'westsidewaterdistrict',
            'weststanislaus', 'coelho', 'fresnoslough', 'jamesirrigationdistrict', 'lagunawaterdistrict',
            '1606', 'tranquilityirrigationdistrict', 'avenal', 'coalingacityof', 'huroncityof', 'pacheco',
            'tranquilitypublicutilitydistrict']  # , 'tracycityof'
}
### CALFEWS keys not included in spatial data
#                   'OXV': ['hillsvalley', 'tri-valleywaterdistrict']
# ,                  'KCWA': 'kerncountywateragency', }
#                   'ID4': '4',
#                   'OKW': 'otherkaweah',
#       'OTL': 'othertule',
#                  'OSW': 'otherswp',

#                  'SOC': 'socal', 'SOB': 'southbay', 'CCA': 'centralcoast',


def district_match(shp_names, name):
    shp_names_lc = [k.lower().strip().replace(' ','') for k in shp_names]
    is_match = [name in k for k in shp_names_lc]
    return [i for i in range(len(is_match)) if is_match[i]], [shp_names_lc[i] for i in range(len(is_match)) if is_match[i]]

### get water districts shapefile
ags = gpd.read_file(districts_folder + 'Water_Districts.shp')
ags.sort_values('AGENCYNAME', inplace=True)

### match using dict above
idxs = []
names = []
for k,vs in ag_keys.items():
    for v in vs:
        idx, name = district_match(ags.AGENCYNAME, v)
        idxs += idx
        name += name
ags = ags.iloc[idxs,:]
ags.reset_index(drop=True, inplace=True)

### add key to geodataframe
ags['key'] = ''
for k,vs in ag_keys.items():
    for v in vs:
        idxs, names = district_match(ags.AGENCYNAME, v)
        for idx, name in zip(idxs, names):
            for k, ls in ag_keys.items():
                for l in ls:
                    if l in name:
                        key = k
            ags['key'].iloc[idx] = key

ags['area'] = ags.geometry.area

is_partner = {}
is_partner['friantHistorical'] = {'BDM':False, 'BLR':False, 'BVA':False, 'CWO':False, 'HML':False, 'ID4':False, 'KND':False, 'LHL':False,
                         'RRB':False, 'SMI':False, 'THC':False, 'TJC':False, 'WKN':False, 'WRM':False, 'KCWA':False, 'COB':False,
                         'NKN':False, 'ARV':True, 'PIX':False, 'DLE':True, 'EXE':True, 'OKW':False, 'KRT':False, 'LND':True,
                         'LDS':True, 'LWT':True, 'PRT':True, 'SAU':True, 'SFW':True, 'SSJ':True, 'TPD':True, 'TBA':True,
                         'TUL':True, 'COF':True, 'FRS':True, 'SOC':False, 'SOB':False, 'CCA':False, 'DLR':False, 'TLB':False,
                         'KWD':False, 'WSL':False, 'SNL':False, 'PNC':False, 'DLP':False, 'CWC':False, 'MAD':False, 'OTL':False,
                         'OFK':True, 'OCD':False, 'OEX':False, 'OXV':False, 'OSW':False, 'CNS':False, 'ALT':False, 'KRWA':False, 'KWB':False}

is_partner['boxplot'] = {'BDM':False, 'BLR':False, 'BVA':True, 'CWO':False, 'HML':False, 'ID4':False, 'KND':False, 'LHL':False,
                 'RRB':False, 'SMI':False, 'THC':False, 'TJC':False, 'WKN':False, 'WRM':False, 'KCWA':False, 'COB':False,
                 'NKN':False, 'ARV':False, 'PIX':False, 'DLE':False, 'EXE':False, 'OKW':False, 'KRT':False, 'LND':False,
                 'LDS':False, 'LWT':False, 'PRT':False, 'SAU':False, 'SFW':False, 'SSJ':False, 'TPD':False, 'TBA':False,
                 'TUL':True, 'COF':True, 'FRS':False, 'SOC':False, 'SOB':False, 'CCA':False, 'DLR':False, 'TLB':False,
                 'KWD':False, 'WSL':False, 'SNL':False, 'PNC':False, 'DLP':False, 'CWC':False, 'MAD':False, 'OTL':False,
                 'OFK':False, 'OCD':False, 'OEX':False, 'OXV':False, 'OSW':False, 'CNS':False, 'ALT':False, 'KRWA':False, 'KWB':False}


### read in district level results, get color for map
datasets = ['friantHistorical_median_FKC', 'boxplot_combined']
labels = [s.split('_')[0] for s in datasets]

for l in labels:
    ags['is_' + l] = [is_partner[l][d] for d in ags.key]

### read in results dataset with color codes
cdict = {}
anon_dict = {}
for dataset in datasets[-1:]:
    ds = pd.read_csv('../figures/results_' + dataset + '.csv')
    label = dataset.split('_')[0]

    cdict[label] = {ds.district.iloc[i]: ds.color.iloc[i] for i in range(ds.shape[0])}
    cdict[label]['KWB'] = '#c1c1c1'

    anon_dict[label] = {ds.district.iloc[i]: ds.district_label.iloc[i] for i in range(ds.shape[0])}
    anon_dict[label]['KWB'] = ''

    ags['color_' + label] = [cdict[label][d] if d in cdict[label] else '#c1c1c1' for d in ags.key ]
    ags['anon_' + label] = [anon_dict[label][d] if d in anon_dict[label] else 'other' for d in ags.key ]

### write new polygons. for boxplot_combined need 4 categories to handle zorder: topfriant, topnonfriant, bottomfriant, bottomnonfriant. friant will have black outline, top/bottom is for zorder clarity.
for l in labels[-1:]:
    ags.loc[np.logical_and(ags['is_friantHistorical'], ags['is_boxplot']), :].to_file(shapefile_folder + 'districts_FKC_experiment_topfriant.shp')
    ags.loc[np.logical_and(np.logical_not(ags['is_friantHistorical']), ags['is_boxplot']), :].to_file(shapefile_folder + 'districts_FKC_experiment_topnonfriant.shp')
    ags.loc[np.logical_and(ags['is_friantHistorical'], np.logical_not(ags['is_boxplot'])), :].to_file(shapefile_folder + 'districts_FKC_experiment_bottomfriant.shp')
    ags.loc[np.logical_and(np.logical_not(ags['is_friantHistorical']), np.logical_not(ags['is_boxplot'])), :].to_file(shapefile_folder + 'districts_FKC_experiment_bottomnonfriant.shp')



### now look at groundwater recharge potential using Modified SAGBI data. Y
# You will need to download this data (see citation in paper) and place in "sagbi_mod" folder within "maps" directory.
sagbi = gpd.read_file('.sagbi_mod/sagbi_mod.shp')
sagbi = sagbi.to_crs(ags.crs)

### clip to boundaries of district shapefiles
sagbi_clip = gpd.clip(sagbi, ags)
sagbi = gpd.read_file('sagbi_mod/sagbi_mod_clip.shp')

### set colors
cdict_sagbi = {'Excellent': 'darkgreen',
 'Good': 'limegreen',
 'Moderately Good': 'yellow',
 'Moderately Poor': 'orange',
 None: '0.5',
 'Poor': 'red',
 'Very Poor': 'darkred'}

sagbi['color_sagbi'] = [cdict_sagbi[rating] for rating in sagbi['rat_grp']]
sagbi['color_sagbi']

### save data
sagbi.to_file('sagbi_mod/sagbi_mod_clip.shp')







