import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize, LogNorm, ListedColormap, rgb2hex
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec
import statsmodels.api as sm
import h5py
import geopandas as gpd
import contextily as cx
from generativepy.color import Color
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from PIL import ImageColor
import json

import sys
sys.path.append('/home/alh/PycharmProjects/CALFEWS/')
from calfews_src.util import district_label_dict

import warnings
warnings.filterwarnings('ignore')

### replace with path of disaggregated results hdf5 dataset on your computer. Download from Zenodo (see link in repo).
results_mhmm_disagg_file = '/home/alh/PycharmProjects/CALFEWS/results/WCU_results_bridges2/results_reevaluation_disagg.hdf5'
baseline_mhmm_dir = f'/home/alh/PycharmProjects/CALFEWS/results/MOO_results_bridges2/baseline/'
results_projections_dir = '/home/alh/PycharmProjects/CALFEWS/results/climate_reeval_bridges2/'
results_projections_disagg_file = f'{results_projections_dir}/results_climate_reeval.hdf5'

### parameters
dpi = 450
fontsize = 14
fig_dir = 'figs/'
kaf_to_gl = 1.23
cmap_vir = cm.get_cmap('viridis')
cols_cbrewer = ['#66c2a5', '#fc8d62', '#8da0cb']

### cost assumptions info that is used in various plots
cap = 1000
FKC_participant_payment = 50e6
CFWB_cost = 50e6
interest_annual = 0.03
time_horizon = 30
projects = {0: 'none', 1: 'FKC', 2: 'CFWB', 3: 'FKC_CFWB'}
principle = {'none': 0., 'FKC': FKC_participant_payment, 'CFWB': CFWB_cost,
             'FKC_CFWB': FKC_participant_payment + CFWB_cost}
payments_per_yr = 1
interest_rt = interest_annual / payments_per_yr
num_payments = time_horizon * payments_per_yr
annual_debt_payment_dict = {k: principle[k] / (((1 + interest_rt) ** num_payments - 1) /
                                                (interest_rt * (1 + interest_rt) ** num_payments)) for k in principle}




### visualize optimal tradeoff set with parallel coordinates plots.
### Note there are several different figures options with different solutions brushed out or highlighted.
# parallel coordinates plot options (fig_stage):
#       0 = axes only,
#       1 = statusquo only,
#       4 = all w/ hilite statusquo
#       6 = (paper Fig. 3) all except statusquo
#       8 = (paper SI Fig. S3) all brushed except satisfice - n_p
#       9 = (paper SI Fig. S5) all brushed except satisfice - cog_wp
#       10 = (paper SI Fig. S6) all brushed except satisfice - cwg_np
#       11 = (paper SI Fig. S4) all brushed except satisfice - cwg_p 
#       13 = (paper SI Fig. S16) all brushed except satisfice - better than or equal to statusquo on all objectives

def plot_parallel_coords(results, columns, column_labels, fig_stage, color_by='n_p', ideal_direction='top', curvy=False):

    ### plot-specific params
    fontsize = 12

    ### split out 3 solutions that didnt come from optimization
    results_opt = results.iloc[:-1,:]
    results_nonopt = results.iloc[-1:,:]
    soln_statusquo = results_nonopt['label'].iloc[0]
    soln_compromise = 'NA' ### this will be set during fig_stage==13 plot. both solns returned from this fn.

    ### get satisficing if brushing
    if fig_stage == 8:
        thres_np = 24
        satisfice = results_opt['n_p'] >= thres_np
    elif fig_stage == 9:
        thres_cog = 250
        satisfice = results_opt['cog_wp_p90'] <= thres_cog
    elif fig_stage == 10:
        thres_cwg_np = 0
        satisfice = results_opt['cwg_np'] >= thres_cwg_np
        print(f"Reduction in max cwg_p if cwg_np>=0: {(1 - results['cwg_p'].loc[results['cwg_np']>=0].max() / results['cwg_p'].max()) * 100}%")
    elif fig_stage == 11:
        thres_cwg_p = 80
        satisfice = results_opt['cwg_p'] >= thres_cwg_p
    elif fig_stage == 13:
        thres_np = results_nonopt['n_p'].loc[results_nonopt['label'] == soln_statusquo].iloc[0]
        thres_cwg_p = results_nonopt['cwg_p'].loc[results_nonopt['label'] == soln_statusquo].iloc[0]
        thres_cwg_np = results_nonopt['cwg_np'].loc[results_nonopt['label'] == soln_statusquo].iloc[0]
        thres_cog = results_nonopt['cog_wp_p90'].loc[results_nonopt['label'] == soln_statusquo].iloc[0]
        satisfice = np.logical_and(
            np.logical_and(np.logical_and(results_opt['n_p'] >= thres_np, results_opt['cwg_p'] >= thres_cwg_p),
                           results_opt['cwg_np'] >= thres_cwg_np),
            results_opt['cog_wp_p90'] <= thres_cog)
        ### define the compromise soln as the one that minimizes worst-partner gain out of the subset that dominate status quo
        soln_compromise = results_opt.loc[satisfice,'label'].iloc[np.argmin(results_opt.loc[satisfice,'cog_wp_p90'])]
        ### print performance of compromise vs status quo solns
        print('Compromise Partnership reevaluation aggregated metrics:')
        print(results.loc[results['label'] == soln_compromise].iloc[0, -4:])
        print('Status Quo Partnership reevaluation aggregated metrics:')
        print(results.loc[results['label'] == soln_statusquo].iloc[0, -4:])

    ressat = results_opt.loc[:, columns]
    ressat = pd.concat([ressat, results_nonopt.loc[:, columns]])


    if ideal_direction == 'bottom':
        tops = ressat.min(axis=0)
        bottoms = ressat.max(axis=0)
        switch = bottoms[-1]
        bottoms[-1] = tops[-1]
        tops[-1] = switch
        ressat.iloc[:, :-1] = (ressat.iloc[:, :-1].max(axis=0) - ressat.iloc[:, :-1]) / (
                    ressat.iloc[:, :-1].max(axis=0) - ressat.iloc[:, :-1].min(axis=0))
        ressat.iloc[:, -1] = (ressat.iloc[:, -1] - ressat.iloc[:, -1].min(axis=0)) / (
                    ressat.iloc[:, -1].max(axis=0) - ressat.iloc[:, -1].min(axis=0))
    elif ideal_direction == 'top':
        tops = ressat.max(axis=0)
        bottoms = ressat.min(axis=0)
        switch = bottoms[-1]
        bottoms[-1] = tops[-1]
        tops[-1] = switch
        ressat.iloc[:, -1] = (ressat.iloc[:, -1].max(axis=0) - ressat.iloc[:, -1]) / (
                    ressat.iloc[:, -1].max(axis=0) - ressat.iloc[:, -1].min(axis=0))
        ressat.iloc[:, :-1] = (ressat.iloc[:, :-1] - ressat.iloc[:, :-1].min(axis=0)) / (
                    ressat.iloc[:, :-1].max(axis=0) - ressat.iloc[:, :-1].min(axis=0))
    else:
        print('ideal_direction should be "top" or "bottom" based on direction of preference')

    ### parallel coord plot
    fig, ax = plt.subplots(1, 1, figsize=(11, 6), gridspec_kw={'hspace': 0.1, 'wspace': 0.1})


    def get_color(color_by, results_opt, results_nonopt, row, cmap):
        start_num = results[color_by].min() if color_by == 'n_p' else 1
        if row < results_opt.shape[0]:
            numnorm = (results_opt[color_by].iloc[row] - start_num) / (results_opt[color_by].max() - start_num)
        else:
            numnorm = (results_nonopt[color_by].iloc[row - results_opt.shape[0]] - start_num) / (
                        results_opt[color_by].max() - start_num)
        return cmap(numnorm), numnorm


    cmap_vir = cm.get_cmap('viridis')

    ### plot all satisficing solns
    for i in range(ressat.shape[0]):
        for j in range(len(columns) - 1):
            c, numnorm = get_color(color_by, results_opt, results_nonopt, i, cmap_vir)
            zorder = 2 + numnorm if color_by == 'n_p' else 2 - numnorm
            y1 = ressat.iloc[i, j]
            y2 = ressat.iloc[i, j + 1]
            if curvy:
                ### add sin shape to help distinguish lines
                t = np.arange(-np.pi / 2, np.pi / 2 + 0.001, 0.01)
                y = y1 + (np.sin(t) + 1) / 2 * (y2 - y1)
                x = j + t / np.pi + 1 / 2
            else:
                y = [y1, y2]
                x = [j, j + 1]
            if fig_stage < 3:
                alpha = 0
            elif fig_stage == 5 or fig_stage >= 7:
                alpha = 0.05
            else:
                alpha = 0.8
            if i < ressat.shape[0] - 1:
                ### plot solns from MOO/WCU
                ax.plot(x, y, c=c, alpha=alpha, zorder=zorder, lw=1.5)
            ### plot extra solns: statusquo
            if fig_stage < 6 or fig_stage == 13:
                if i == ressat.shape[0] - 1:
                    ### statusquo
                    if fig_stage > 0:
                        ax.plot(x, y, c='k', alpha=1, zorder=4, lw=2)
             


    ### highlight satisficing solns
    if fig_stage >= 8:
        for i in range(ressat.shape[0] - 1):
            if satisfice[i]:
                for j in range(len(columns) - 1):
                    c, numnorm = get_color(color_by, results_opt, results_nonopt, i, cmap_vir)
                    y1 = ressat.iloc[i, j]
                    y2 = ressat.iloc[i, j + 1]
                    if curvy:
                        ### add sin shape to help distinguish lines
                        t = np.arange(-np.pi / 2, np.pi / 2 + 0.001, 0.01)
                        y = y1 + (np.sin(t) + 1) / 2 * (y2 - y1)
                        x = j + t / np.pi + 1 / 2
                    else:
                        y = [y1, y2]
                        x = [j, j + 1]
                    alpha = 0.8
                    ax.plot(x, y, c=c, alpha=alpha, zorder=2 + numnorm, lw=1.5)
        thresholds = []
        if ideal_direction == 'bottom':
            if fig_stage == 8:
                thresholds = [(tops[0] - thres_np) / (tops[0] - bottoms[0])]
                xs = [0]
            if fig_stage == 9:
                thresholds = [(tops[3] - thres_cog) / (tops[3] - bottoms[3])]
                xs = [3]
            if fig_stage == 10:
                thresholds = [(tops[2] - thres_cwg_np) / (tops[2] - bottoms[2])]
                xs = [2]
            if fig_stage == 11:
                thresholds = [(tops[1] - thres_cwg_p) / (tops[1] - bottoms[1])]
                xs = [1]
            if fig_stage == 13:
                thresholds = [(tops[0] - thres_np) / (tops[0] - bottoms[0]),
                              (tops[1] - thres_cwg_p) / (tops[1] - bottoms[1]),
                              (tops[3] - thres_cog) / (tops[3] - bottoms[3]),
                              (tops[2] - thres_cwg_np) / (tops[2] - bottoms[2])]
                xs = [0, 1, 3, 2]
        elif ideal_direction == 'top':
            if fig_stage == 8:
                thresholds = [(bottoms[0] - thres_np) / (bottoms[0] - tops[0])]
                xs = [0]
            if fig_stage == 9:
                thresholds = [(bottoms[3] - thres_cog) / (bottoms[3] - tops[3])]
                xs = [3]
            if fig_stage == 10:
                thresholds = [(bottoms[2] - thres_cwg_np) / (bottoms[2] - tops[2])]
                xs = [2]
            if fig_stage == 11:
                thresholds = [(bottoms[1] - thres_cwg_p) / (bottoms[1] - tops[1])]
                xs = [1]
            if fig_stage == 13:
                thresholds = [(bottoms[0] - thres_np) / (bottoms[0] - tops[0]),
                              (bottoms[1] - thres_cwg_p) / (bottoms[1] - tops[1]),
                              (bottoms[3] - thres_cog) / (bottoms[3] - tops[3]),
                              (bottoms[2] - thres_cwg_np) / (bottoms[2] - tops[2])]
                xs = [0, 1, 3, 2]

        pc = PatchCollection([Rectangle([x - 0.05, 0], 0.1, t) for x, t in zip(xs, thresholds)],
                             facecolor='grey', alpha=0.5)
        ax.add_collection(pc)

        if fig_stage == 13:
            ### highlight compromise soln
            ressat_soln = ressat.iloc[:-3,:].loc[results_opt['label'] == soln_compromise, :]
            i = ressat_soln.index[0]
            xx = []
            yy = []
            for j in range(len(columns) - 1):
                c, numnorm = get_color(color_by, results_opt, results_nonopt, i, cmap_vir)
                y1 = ressat_soln.iloc[0, j]
                y2 = ressat_soln.iloc[0, j + 1]
                if curvy:
                    ### add sin shape to help distinguish lines
                    t = np.arange(-np.pi / 2, np.pi / 2 + 0.001, np.pi / 10)
                    y = y1 + (np.sin(t) + 1) / 2 * (y2 - y1)
                    x = j + t / np.pi + 1 / 2
                else:
                    x = np.arange(j, j + 1 + 0.001, 1 / 10)
                    y = y1 + (x - j) * (y2 - y1)
                    xx += list(x)
                    yy += list(y)
            alpha = 1
            ax.plot(xx, yy, c='k', alpha=alpha, zorder=3, lw=4)
            ax.plot(xx, yy, c=c, alpha=alpha, zorder=3, lw=3)

    ### add top/bottom ranges
    for j in range(len(columns)):
        ax.annotate(str(round(tops[j])), [j, 1.02], ha='center', va='bottom', zorder=5, fontsize=fontsize)
        if j == len(columns) - 1:
            ax.annotate(str(round(bottoms[j])) + '+', [j, -0.02], ha='center', va='top', zorder=5, fontsize=fontsize)
        else:
            ax.annotate(str(round(bottoms[j])), [j, -0.02], ha='center', va='top', zorder=5, fontsize=fontsize)

        ax.plot([j, j], [0, 1], c='k', zorder=1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ['top', 'bottom', 'left', 'right']:
        ax.spines[spine].set_visible(False)

    if ideal_direction == 'top':
        ax.arrow(-0.15, 0.1, 0, 0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)
    elif ideal_direction == 'bottom':
        ax.arrow(-0.15, 0.9, 0, -0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)

    ax.annotate('Direction of preference', xy=(-0.3, 0.5), ha='center', va='center', rotation=90, fontsize=fontsize)

    ax.set_xlim(-0.4, 3.2)
    ax.set_ylim(-0.4, 1.1)

    for i, l in enumerate(column_labels):
        ax.annotate(l, xy=(i, -0.12), ha='center', va='top', fontsize=fontsize)
    ax.patch.set_alpha(0)

    ### colorbar
    mappable = cm.ScalarMappable(cmap='viridis')
    if color_by == 'n_p':
        mappable.set_clim(vmin=results[color_by].min(), vmax=results[color_by].max())
        cb = plt.colorbar(mappable, ax=ax, orientation='horizontal', shrink=0.4, label='Number of partners', pad=0.03,
                          alpha=alpha)
        _ = cb.ax.set_xticks(range(results[color_by].min(), results[color_by].max()+1, 2), range(results[color_by].min(), results[color_by].max()+1, 2), fontsize=fontsize)
        _ = cb.ax.set_xlabel(cb.ax.get_xlabel(), fontsize=fontsize)
    elif color_by == 'proj':
        leg = [Line2D([0], [0], color=cmap_vir(0.), lw=3, alpha=alpha, label='Canal expansion'),
               Line2D([0], [0], color=cmap_vir(0.5), lw=3, alpha=alpha, label='Groundwater bank'),
               Line2D([0], [0], color=cmap_vir(1.), lw=3, alpha=alpha, label='Canal + Bank')]
        _ = ax.legend(handles=leg, loc='lower center', ncol=3, bbox_to_anchor=[0.5, -0.07], frameon=False,
                      fontsize=fontsize)

    plt.savefig(f'{fig_dir}paraxis_{fig_stage}_{color_by}.png', bbox_inches='tight', dpi=dpi)
    plt.savefig(f'{fig_dir}paraxis_{fig_stage}_{color_by}.pdf', bbox_inches='tight')


    return soln_statusquo, soln_compromise











### function for preparing geospatial data
def get_geodata():
    # local data folder name
    geo_dir = 'maps/ca_geo'
    point_location_filename = geo_dir + '/CALFEWS_RESERVOIRS.csv'  # coordinates of map 'points'
    shapefile_folder = geo_dir + '/CALFEWS_shapes/'
    districts_folder = geo_dir + '/CALFEWS_shapes/Water_Districts/'
    id4_name = geo_dir + '/ZOB7_ID4_WGS1984/ZOB7_WGS1984.shp'

    water_provider_keys = {
        'BDM': ['berrendamesawaterdistrict'], 'BLR': ['belridgewaterstoragedistrict'],
        'BVA': ['buenavistawaterstoragedistrict'],
        'CWO': ['cawelowaterdistrict'], 'HML': ['henrymillerwaterdistrict'], 'KND': ['kerndeltawaterdistrict'],
        'LHL': ['losthillswaterdistrict'],
        'RRB': ['rosedale-riobravowaterstoragedistrict'], 'SMI': ['semitropicwaterservicedistrict'],
        'THC': ['tehachapi-cummingscountywaterdistrict'],
        'TJC': ['tejon-castacwaterdistrict'], 'WKN': ['westkernwaterdistrict'],
        'WRM': ['wheelerridge-maricopawaterstoragedistrict'],
        'COB': ['bakersfieldcityof'], 'NKN': ['northkernwaterstoragedistrict'],
        'ARV': ['arvin-edisonwaterstoragedistrict'],
        'PIX': ['pixleyirrigationdistrict'], 'DLE': ['delano-earlimartirrigationdistrict'],
        'EXE': ['exeterirrigationdistrict'],
        'KRT': ['kern-tulare'], 'LND': ['lindmore'], 'LDS': ['lindsay-strathmoreirrigationdistric'],
        'LWT': ['lowertule'], 'PRT': ['portervilleirrigationdistrict'], 'SAU': ['saucelito'],
        'SFW': ['shafter-wascoirrigationdistrict'],
        'SSJ': ['southernsanjoaquinmunicipalutilitydistrict'], 'TPD': ['teapot'],
        'TBA': ['terrabellairrigationdistrict'], 'TUL': ['tulareirrigationdistrict'],
        'COF': ['fresnocityof'], 'FRS': ['fresnoirrigation'],
        'DLR': ['dudleyridge'], 'TLB': ['tularelake'], 'KWD': ['kaweahdelta'], 'WSL': ['westlands'],
        'SNL': ['sanluiswater'],
        'PNC': ['panoche'], 'DLP': ['delpuerto'], 'CWC': ['chowchillawaterdistrict'],
        'MAD': ['maderairrigationdistrict'],
        'CNS': ['consolidated'], 'ALT': ['altairrigationdistrict'],
        'KWB': ['kernwaterbank'],
        'KRWA': ['kingsriverwaterdistrict'],

        ### aggregated coastal urban water providers included in experiment but not shown on this map due to geographic distance and because they did not participate in any optimal tradeoff partnerships.
        #     'SOC': 'socal', 'SOB': 'southbay', 'CCA': 'centralcoast',

        ### others not included in this experiment due to minor role in Friant system
        # 'OFK': ['hillsvalley', 'orangecoveirrigationdistrict','lewiscreek','lindsaycityof','stonecorral' ,
        #        'ivanhoeirrigationdistrict', 'orangecovecityof', 'tri-valleywaterdistrict', 'internationalwaterdistrict',
        #       'garfield', 'hiddenlakes', 'fresnocountywaterworksdistrictno18'], #'gravely'
         # , 'kingsriverconservationdistrict'],
        # 'OEX': ['sanluiscanalcompany', 'centralcalifornia', 'firebaughcanalcompany', 'columbiacanalcompany'],
        # 'OCD': ['bantacarbonairrigationdistrict, byronbethanyirrigationdistrict', 'eaglefield', 'mercysprings',
        #       'oralomawaterdistrict', 'pajarovalleywatermanagementagency', 'pattersonwaterdistrict', 'westsidewaterdistrict',
        #      'weststanislaus', 'coelho','fresnoslough', 'jamesirrigationdistrict', 'lagunawaterdistrict',
        #     '1606', 'tranquilityirrigationdistrict', 'avenal', 'coalingacityof', 'huroncityof', 'pacheco',
        #    'tranquilitypublicutilitydistrict']#, 'tracycityof'
        #                   'OXV': ['hillsvalley', 'tri-valleywaterdistrict']
        #     # ,                  'KCWA': 'kerncountywateragency', }
        #     #                   'ID4': '4',
        #     #                   'OKW': 'otherkaweah',
        #     #       'OTL': 'othertule',
        #     #                  'OSW': 'otherswp',

    }

    districts_MOO = ["FRS", "COF", "TUL", "KWD", "EXE", "LDS", "LND", "PRT", "LWT", "TPD", "SAU", "TBA", "PIX", "DLE",
                     "KRT", "SSJ", "SFW", "NKN", "ARV", "DLR", "SMI", "TJC", "BLR", "LHL", "BDM", "WRM", "COB", "BVA",
                     "CWO", "HML", "KND", "RRB", "CNS", "ALT", "CWC", "MAD"]  # "ID4","SOC","SOB","CCA"
    water_provider_keys = {k: water_provider_keys[k] for k in districts_MOO}

    def district_match(shp_names, name):
        shp_names_lc = [k.lower().strip().replace(' ', '') for k in shp_names]
        is_match = [name in k for k in shp_names_lc]
        return [i for i in range(len(is_match)) if is_match[i]], \
               [shp_names_lc[i] for i in range(len(is_match)) if is_match[i]]

    ### read in shapefile of all water districts
    water_providers = gpd.read_file(districts_folder + 'Water_Districts.shp')
    water_providers = water_providers.to_crs(crs=26944)  ### California Zone 4 NAD83 projection

    water_providers.sort_values('AGENCYNAME', inplace=True)

    ### filter to only keep districts in study area
    idxs = []
    names = []
    keys = []
    for k, vs in water_provider_keys.items():
        for v in vs:
            idx, name = district_match(water_providers.AGENCYNAME, v)
            idxs += idx
            names += name
            for i in range(len(idx)):
                keys.append(k)

    water_providers = water_providers.iloc[idxs, :]
    water_providers.reset_index(drop=True, inplace=True)
    water_providers['area'] = water_providers.geometry.area
    water_providers['district'] = keys

    ### get ID4 district from separate shapefile and add to water_providers
    id4 = gpd.read_file(id4_name)
    id4 = id4.to_crs(water_providers.crs)
    id4['district'] = 'ID4'

    water_providers = pd.concat([water_providers, id4], ignore_index=True)

    ### get other shapefiles
    states = gpd.read_file(shapefile_folder + 'states.shp')
    states = states.to_crs(water_providers.crs)

    canals = gpd.read_file(shapefile_folder + 'drawings-line.shp')
    canals = canals.to_crs(water_providers.crs)
    canals_fkc = canals.loc[canals['Name'] == 'fkc']
    canals_other = canals.loc[canals['Name'] != 'fkc']

    tlb = gpd.read_file(shapefile_folder + 'Tulare_Basin-line.shp')
    tlb = tlb.to_crs(water_providers.crs)

    sjr = gpd.read_file(shapefile_folder + 'San_Joaquin-line.shp')
    sjr = sjr.to_crs(water_providers.crs)

    kings = gpd.read_file(shapefile_folder + 'kings_ext.shp')
    kings = kings.to_crs(water_providers.crs)

    res = pd.read_csv(point_location_filename)
    geometry = [Point(xy) for xy in zip(res['LONG'], res['LAT'])]
    res_gdf = gpd.GeoDataFrame(res, crs=4326, geometry=geometry)
    res_gdf = res_gdf.to_crs(water_providers.crs)
    res_gdf = res_gdf.loc[[name in ['MILLERTON', 'PINE FLAT', 'KAWEAH', 'SUCCESS', 'ISABELLA',
                                    'SAN LUIS'] for name in res_gdf['NAME']]]

    return water_providers, states, canals_fkc, canals_other, tlb, sjr, kings, res_gdf


riverblue = 'mediumblue'
reservoirblue = 'darkblue'
canalgrey = '0.2'
def add_tlb_shapes_to_map(ax, canals_fkc, canals_other, tlb, sjr, kings, res_gdf,
                              labels=True, show_fkc=True, show_cfwb=True, cfwb_size=400, show_other=True):
    if show_other:
        canals_fkc.plot(color='firebrick', ax=ax, lw=2, ls='--', zorder=2)
        canals_other.plot(color='0.3', ax=ax, lw=2, ls='-', zorder=2)
        tlb.plot(color=riverblue, ax=ax, lw=2, zorder=2)
        sjr.plot(color=riverblue, ax=ax, lw=2, zorder=2)
        kings.plot(color=riverblue, ax=ax, lw=2, zorder=2)
        res_gdf.plot(color=reservoirblue, ax=ax, markersize=100, zorder=3)
    if show_fkc:
        canals_fkc.plot(color='firebrick', ax=ax, lw=2, ls='--', zorder=2)
    if show_cfwb:
        ax.scatter((1.99e6), (5.78e5), color='firebrick', edgecolor='k', marker='*', s=cfwb_size, alpha=0.7, zorder=3)
    if labels:
        ax.annotate('Millerton Lake', (1.955e6, 6.91e5), ha='center', va='center', fontsize=fontsize, color=reservoirblue)
        ax.annotate('Pine Flat Lake', (1.975e6, 6.72e5), ha='center', va='center', fontsize=fontsize, color=reservoirblue)
        ax.annotate('Lake Kaweah', (2.017e6, 6.27e5), ha='center', va='center', fontsize=fontsize, color=reservoirblue)
        ax.annotate('Lake Success', (2.027e6, 5.88e5), ha='center', va='center', fontsize=fontsize, color=reservoirblue)
        ax.annotate('Lake Isabella', (2.03e6, 5.42e5), ha='center', va='center', fontsize=fontsize, color=reservoirblue)
        ax.annotate('San\nLuis\nReservoir', (1.818e6, 6.82e5), ha='center', va='center', fontsize=fontsize, color=reservoirblue)
        ax.annotate('San Joaquin\nRiver', (1.885e6, 6.5e5), ha='center', va='center', fontsize=fontsize, color=riverblue)
        ax.annotate('Kings\nRiver', (1.925e6, 6.28e5), ha='center', va='center', fontsize=fontsize, color=riverblue)
        ax.annotate('Kaweah River', (1.958e6, 6.085e5), ha='center', va='center', fontsize=fontsize, color=riverblue)
        ax.annotate('Tule River', (1.938e6, 5.8e5), ha='center', va='center', fontsize=fontsize, color=riverblue)
        ax.annotate('Kern River', (2.014e6, 5.27e5), ha='center', va='center', fontsize=fontsize, color=riverblue)
        ax.annotate('Madera\nCanal', (1.918e6, 7.05e5), ha='center', va='center', fontsize=fontsize, color=canalgrey)
        ax.annotate('Friant-Kern\nCanal', (1.995e6, 6.45e5), ha='center', va='center', fontsize=fontsize, color='firebrick')
        ax.annotate('Arvin-\nEdison\nCanal', (2.037e6, 4.85e5), ha='center', va='center', fontsize=fontsize, color=canalgrey)
        ax.annotate('California\nAqueduct', (1.86e6, 6.25e5), ha='center', va='center', fontsize=fontsize, color=canalgrey)
        ax.annotate('Delta-\n     Mendota\n        Canal', (1.84e6, 6.91e5), ha='center', va='center', fontsize=fontsize, color=canalgrey)
        ax.annotate('Cross-\n      Valley\n            Canal', (1.96e6, 5.15e5), ha='center', va='center', fontsize=fontsize, color=canalgrey)

    return ax




def get_bivariate_colorlist(grid_size=4):
    ### function to convert hex color to rgb to Color object (generativepy package)
    def hex_to_Color(hexcode):
        rgb = ImageColor.getcolor(hexcode, 'RGB')
        rgb = [v / 256 for v in rgb]
        rgb = Color(*rgb)
        return rgb

    hex_color_corners = ['#ffffcb', '#a6611a', '#018571', '#2D3033']# '#000000']
    c00 = hex_to_Color(hex_color_corners[0])
    c10 = hex_to_Color(hex_color_corners[1])
    c01 = hex_to_Color(hex_color_corners[2])
    c11 = hex_to_Color(hex_color_corners[3])

    ### now create square grid of colors, using color interpolation from generativepy package
    num_grps = grid_size
    c00_to_c10 = []
    c01_to_c11 = []
    colorlist = []
    for i in range(num_grps):
        c00_to_c10.append(c00.lerp(c10, 1 / (num_grps - 1) * i))
        c01_to_c11.append(c01.lerp(c11, 1 / (num_grps - 1) * i))
    for i in range(num_grps):
        for j in range(num_grps):
            colorlist.append(c00_to_c10[i].lerp(c01_to_c11[i], 1 / (num_grps - 1) * j))
    ### convert back to hex color
    colorlist = [rgb2hex([c.r, c.g, c.b]) for c in colorlist]

    return hex_color_corners, colorlist


### get color based on whether a water provider is a Friant Contractor or not
def get_friant_color(d):
    friant_dict = {'BDM': False, 'BLR': False, 'BVA': False, 'CWO': False, 'HML': False, 'ID4': False, 'KND': False,
                   'LHL': False, 'RRB': False, 'SMI': False, 'THC': False, 'TJC': False, 'WKN': False, 'WRM': False,
                   'KCWA': False, 'COB': False, 'NKN': False, 'ARV': True, 'PIX': False, 'DLE': True, 'EXE': True,
                   'OKW': False, 'KRT': False, 'LND': True, 'LDS': True, 'LWT': True, 'PRT': True, 'SAU': True,
                   'SFW': True, 'SSJ': True, 'TPD': True, 'TBA': True, 'TUL': True, 'COF': True, 'FRS': True,
                   'SOC': False, 'SOB': False, 'CCA': False, 'DLR': False, 'TLB': False, 'KWD': False, 'WSL': False,
                   'SNL': False, 'PNC': False, 'DLP': False, 'CWC': False, 'MAD': False, 'OTL': False, 'OFK': True,
                   'OCD': False, 'OEX': False, 'OXV': False, 'OSW': False, 'CNS': False, 'ALT': False,
                   'KRWA': False, 'KWB': False}
    if d in friant_dict:
        is_friant = friant_dict[d]
    else:
        is_friant = False

    hex_color_corners, colorlist = get_bivariate_colorlist()

    if is_friant:
        return hex_color_corners[2]
    else:
        return hex_color_corners[0]


def plot_regional_map(water_providers, states, canals_fkc, canals_other, tlb, sjr, kings, res_gdf):
    ### base map with labels, etc
    alpha = 0.85
    fontsize = 13
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    ### get color based on whether a water provider is a Friant Contractor or not
    water_providers['color_friant'] = [get_friant_color(d) for d in water_providers['district']]

    ### first plot districts with non-zero participation, except COF & TUL & ID4
    condition = [d not in ('COF', 'TUL', 'ID4') for d in water_providers['district']]
    water_providers.loc[condition, :].plot(ax=ax, color=water_providers.loc[condition, 'color_friant'],
                                           edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1)
    ### now plot COF & TUL, which are overlapping and need to be on top
    condition = [d in ('COF', 'TUL') for d in water_providers['district']]
    water_providers.loc[condition, :].plot(ax=ax, color=water_providers.loc[condition, 'color_friant'],
                                           edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1)

    ### plot other shapefiles, eg rivers & canals
    ax = add_tlb_shapes_to_map(ax, canals_fkc, canals_other, tlb, sjr, kings, res_gdf, labels=True)

    ### axes
    xlim = [1.8e6, 2.06e6]
    xrange = xlim[1] - xlim[0]
    ylim = [4.25e5, 7.25e5]
    yrange = ylim[1] - ylim[0]

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[['top', 'left', 'right', 'bottom']].set_visible(False)
    cx.add_basemap(ax=ax, crs=water_providers.crs, alpha=0.5)  # , source=cx.providers.Stamen.TonerLite)

    ### lastly add separate inset for ID4 due to overlapping. make sure scale is same as original
    xfrac = 0.13
    yfrac = 0.115
    axin = ax.inset_axes([0.45, 0.1, xfrac, yfrac])
    xstart = 1.98e6
    ystart = 4.865e5
    axin.set_xlim([xstart, xstart + xfrac * xrange])
    axin.set_ylim([ystart, ystart + yfrac * yrange])
    water_providers.loc[water_providers['district'] == 'ID4'].plot('color', color=get_friant_color('ID4'),edgecolor='k',
                                                                   lw=0.5, alpha=alpha, legend=True, zorder=1, ax=axin)
    axin.set_xticks([])
    axin.set_yticks([])
    axin.spines[['top', 'left', 'right', 'bottom']].set_edgecolor('0.5')
    # cx.add_basemap(ax = axin, crs=water_providers.crs)#, source=cx.providers.Stamen.TonerLite)

    ### now add rectangle back in original axes with arrow
    box = [Rectangle((xstart, ystart), xfrac * xrange, yfrac * yrange)]
    pc = PatchCollection(box, facecolor='none', edgecolor='0.5')
    ax.add_collection(pc)
    ax.arrow(xlim[0] + (0.45 + xfrac) * xrange, ylim[0] + (0.1 + yfrac * 0.5) * yrange,
             xstart - (xlim[0] + (0.45 + xfrac) * xrange),
             ystart - (ylim[0] + (0.1) * yrange),
             color='0.5', lw=1, head_width=3e3, length_includes_head=True, zorder=5)

    # ### add separate inset with legend
    ax.add_collection(PatchCollection([Rectangle((1.81e6, 4.465e5), 0.1e6, 0.68e5)], facecolor='w', edgecolor='k', alpha=1))
    # ax.annotate('Legend', (1.815e6, 4.89e5), ha='left',va='center', zorder=5, fontsize=fontsize)

    ax.scatter([1.82e6], [5.07e5], color=reservoirblue, s=100, alpha=alpha)
    ax.annotate('Reservoir', (1.83e6, 5.07e5), ha='left', va='center', zorder=5, fontsize=fontsize, color=reservoirblue)

    ax.plot([1.815e6, 1.825e6], [4.98e5, 4.98e5], color=riverblue, lw=2, alpha=alpha)
    ax.annotate('River', (1.83e6, 4.98e5), ha='left', va='center', zorder=5, fontsize=fontsize, color=riverblue)

    ax.plot([1.815e6, 1.825e6], [4.89e5, 4.89e5], color='firebrick', ls='--', lw=2, alpha=alpha)
    ax.annotate('Friant-Kern Canal', (1.83e6, 4.89e5), ha='left', va='center', zorder=5,
                fontsize=fontsize, color='firebrick')

    ax.plot([1.815e6, 1.825e6], [4.8e5, 4.8e5], color='0.2', ls='-', lw=2, alpha=alpha)
    ax.annotate('Other Canal', (1.83e6, 4.8e5), ha='left', va='center', zorder=5, fontsize=fontsize, color='0.2')

    ax.scatter([1.82e6], [4.71e5], color='firebrick', edgecolor='k', marker='*', s=250, alpha=alpha)
    ax.annotate('Groundwater Bank', (1.83e6, 4.71e5), ha='left', va='center', zorder=5, fontsize=fontsize, color='k')

    ax.add_collection(PatchCollection([Rectangle((1.815e6, 4.595e5), 0.01e6, 0.05e5)],
                                      facecolor=get_friant_color('LWT'), edgecolor='k', alpha=alpha))
    ax.annotate('Friant Contractor', (1.83e6, 4.62e5), ha='left', va='center', zorder=5, fontsize=fontsize, color='k')

    ax.add_collection(PatchCollection([Rectangle((1.815e6, 4.505e5), 0.01e6, 0.05e5)],
                                      facecolor=get_friant_color('LHL'), edgecolor='k', alpha=alpha))
    ax.annotate('Non-Friant Contractor', (1.83e6, 4.53e5), ha='left', va='center', zorder=5, fontsize=fontsize, color='k')

    # ### add separate inset with larger area & zoom box
    axin = ax.inset_axes([0.77, 0.78, 0.2, 0.2])
    axin.set_xlim([1.5e6, 2.5e6])
    axin.set_ylim([1e5, 13e5])
    states.plot(facecolor='none', edgecolor='k', ax=axin)
    axin.add_collection(PatchCollection([Rectangle([xlim[0], ylim[0]], xlim[1] - xlim[0], ylim[1] - ylim[0])],
                                        facecolor='0.5', edgecolor='k', alpha=0.5))
    axin.set_xticks([])
    axin.set_yticks([])

    plt.savefig(f'{fig_dir}district_map_friant.png', bbox_inches='tight', dpi=dpi)
    plt.savefig(f'{fig_dir}district_map_friant.pdf', bbox_inches='tight')
    



## get all simulated results for particular partnership in alternative hydrologic scenarios during reevaluation, relative to baseline.
def get_results_disagg_MC(soln_label, reeval_type='mhmm'):
    if reeval_type == 'mhmm':
        results_disagg_file = results_mhmm_disagg_file
        mc_range = list(range(21, 100))
    elif reeval_type == 'projections':
        results_disagg_file = results_projections_disagg_file

    with h5py.File(results_disagg_file, 'r') as open_hdf5:
        dvnames = open_hdf5[soln_label].attrs['dv_names']
        rownames = open_hdf5[soln_label].attrs['rownames']
        colnames = open_hdf5[soln_label].attrs['colnames']
        dvs = open_hdf5[soln_label].attrs['dvs']
        districts = [s.split('_')[0] for s in rownames][::3]

        partners = [dvnames[i].replace('share_', '') for i in range(1, len(dvs)) if (dvs[i]) > 0]
        partner_shares = [dvs[i] for i in range(1, len(dvs)) if (dvs[i]) > 0]
        n_p_soln = len(partners)
        nonpartners = [d for d in districts if d not in partners]
        project = dvs[0]
        annual_debt_payment = annual_debt_payment_dict[projects[int(project + 1e-10)]]

        soln_avg_captured_water = open_hdf5[soln_label][::3,:] * kaf_to_gl           

        ### read in baseline results with no infrastructure investment
        if reeval_type == 'mhmm':
            baseline_avg_captured_water = np.zeros(soln_avg_captured_water.shape)
            for mc in mc_range:
                mc_idx = mc - mc_range[0]
                baseline_dict = json.loads(open(f'{baseline_mhmm_dir}/{mc}_baseline.json', 'r').read())
                for district in baseline_dict.keys():
                    idx = [i for i,d in enumerate(districts) if d == district]
                    baseline_avg_captured_water[idx, mc_idx] = baseline_dict[district]['avg_captured_water'] * kaf_to_gl
        elif reeval_type == 'projections':
            baseline_avg_captured_water = open_hdf5['baseline'][::3,:] * kaf_to_gl           

 
        ### get captured watergains in each mc
        mc_wcu_soln = (soln_avg_captured_water - baseline_avg_captured_water).transpose()
        cwg_soln = pd.DataFrame(mc_wcu_soln,
                                      index=['mc' + mc for mc in colnames],
                                      columns=districts)
        
        cwg_p_soln = cwg_soln[partners].sum(axis=1) 
        cwg_np_soln = cwg_soln[nonpartners].sum(axis=1) 
        
        ### now do cog_wp_p90
        for i, d in enumerate(partners):
            cwg_soln[f'{d}_cog'] = (annual_debt_payment * partner_shares[i]) / cwg_soln[d] / 1000
            cwg_soln[f'{d}_cog'].loc[cwg_soln[f'{d}_cog'] > cap] = cap
            cwg_soln[f'{d}_cog'].loc[cwg_soln[f'{d}_cog'] < 0] = cap
        cog_wp_soln = cwg_soln[[d + '_cog' for d in partners]].max(axis=1)

        df_overall_wcu = pd.DataFrame({'cwg_p': cwg_p_soln,
                                       'cwg_np': cwg_np_soln,
                                       'cog_wp': cog_wp_soln,
                                       'n_p': n_p_soln})
        if reeval_type == 'mhmm':
            df_overall_wcu['mc'] = [int(mc.split('mc')[1]) for mc in cog_wp_soln.index]
        elif reeval_type == 'projections':
            df_overall_wcu['mc'] = [mc for mc in cog_wp_soln.index]


    df_overall_wcu.sort_values(['mc'], inplace=True)
    df_overall_wcu.reset_index(inplace=True, drop=True)

    return df_overall_wcu



### get all simulated results for particular partnership, at level of indiv partners, in alternative hydrologic scenarios during reevaluation, relative to baseline.
def get_results_disagg_MC_district(soln_label, reeval_type='mhmm'):

    if reeval_type == 'mhmm':
        results_disagg_file = results_mhmm_disagg_file
        mc_range = list(range(21, 100))
    elif reeval_type == 'projections':
        results_disagg_file = results_projections_disagg_file

    with h5py.File(results_disagg_file, 'r') as open_hdf5:
        dvnames = open_hdf5[soln_label].attrs['dv_names']
        rownames = open_hdf5[soln_label].attrs['rownames']
        colnames = open_hdf5[soln_label].attrs['colnames']
        dvs = open_hdf5[soln_label].attrs['dvs']
        districts = [s.split('_')[0] for s in rownames][::3]

        partners = [dvnames[i].replace('share_', '') for i in range(1, len(dvs)) if (dvs[i]) > 0]
        partner_shares = [dvs[i] for i in range(1, len(dvs)) if (dvs[i]) > 0]
        n_p_soln = len(partners)
        nonpartners = [d for d in districts if d not in partners]
        project = dvs[0]
        annual_debt_payment = annual_debt_payment_dict[projects[int(project + 1e-10)]]

        soln_avg_captured_water = open_hdf5[soln_label][::3,:] * kaf_to_gl           

        ### read in baseline results with no infrastructure investment 
        if reeval_type == 'mhmm':
            baseline_avg_captured_water = np.zeros(soln_avg_captured_water.shape)
            for mc in mc_range:
                mc_idx = mc - mc_range[0]
                baseline_dict = json.loads(open(f'{baseline_mhmm_dir}/{mc}_baseline.json', 'r').read())
                for district in baseline_dict.keys():
                    idx = [i for i,d in enumerate(districts) if d == district]
                    baseline_avg_captured_water[idx, mc_idx] = baseline_dict[district]['avg_captured_water'] * kaf_to_gl
        elif reeval_type == 'projections':
            baseline_avg_captured_water = open_hdf5['baseline'][::3,:] * kaf_to_gl           


        ### get captured watergains in each mc
        mc_wcu_soln = (soln_avg_captured_water - baseline_avg_captured_water).transpose()
        cwg_soln = pd.DataFrame(mc_wcu_soln,
                                      index=['mc' + mc for mc in colnames],
                                      columns=districts)
        count = 0
        for d in partners:
            if count == 0:
                results_disagg = cwg_soln[[d]]
                results_disagg.columns = [d + '_cwg']
                count = 1
            else:
                results_disagg[d + '_cwg'] = cwg_soln[d]
        results_disagg['overall_cwg_p'] = cwg_soln[[d for d in partners]].sum(axis=1).values 

        ### now do cwg_np
        for d in nonpartners:
            results_disagg[d + '_cwg'] = cwg_soln[d] 
        results_disagg['overall_cwg_np'] = cwg_soln[[d for d in nonpartners]].sum(axis=1).values 

        ### now do cog_wp_p90
        for i, d in enumerate(partners):
            cwg_soln[f'{d}_cog'] = (annual_debt_payment * partner_shares[i]) / (cwg_soln[d]) / 1000
            cwg_soln[f'{d}_cog'].loc[cwg_soln[f'{d}_cog'] > cap] = cap
            cwg_soln[f'{d}_cog'].loc[cwg_soln[f'{d}_cog'] < 0] = cap
            results_disagg[d + '_cog'] = cwg_soln[d + '_cog']
        results_disagg['overall_cog_wp'] = cwg_soln[[d + '_cog' for d in partners]].max(axis=1)

        ### also get cog for partnership overall
        cwg_soln['overall_cog_p'] = (annual_debt_payment) / (sum([cwg_soln[d] for d in partners])) / 1000
        cwg_soln['overall_cog_p'].loc[cwg_soln['overall_cog_p'] > cap] = cap
        cwg_soln['overall_cog_p'].loc[cwg_soln['overall_cog_p'] < 0] = cap
        results_disagg['overall_cog_p'] = cwg_soln['overall_cog_p']

    order = np.argsort(partner_shares)[::-1]
    partner_shares = [partner_shares[o] for o in order]
    partners = [partners[o] for o in order]

    return results_disagg, partners, nonpartners, partner_shares, project



### color palette for ownership share bins
def get_ownership_share_colors():
    ### patches plot, showing shares in different solutions. use custom scale
    nonpartnercolor = 1
    cmap = cm.get_cmap('YlGnBu')
    oldcolors = cmap(np.linspace(0.15, 1, 6))
    newcolors = cmap(np.linspace(0, 1, 2560))
    breaks = [int(2560 * b) for b in [0.001, 0.02, 0.04, 0.08, 0.16, 1]]
    newcolors[:breaks[0]] = [nonpartnercolor, nonpartnercolor, nonpartnercolor, 1]
    for i, b in enumerate(breaks[:-1]):
        newcolors[b:breaks[i + 1]] = oldcolors[i]
    shares_cmap_class = ListedColormap(newcolors)
    shares_cmap_mappable = cm.ScalarMappable(cmap=shares_cmap_class)

    ### separate cmap class with even intervals for colorbar
    breaks_even = [int(2560 * b) for b in [1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6, 1]]
    newcolors_even = cmap(np.linspace(0, 1, 2560))
    newcolors_even[:breaks_even[0]] = [nonpartnercolor, nonpartnercolor, nonpartnercolor, 1]
    for i, b in enumerate(breaks_even[:-1]):
        newcolors_even[b:b + 10] = [0, 0, 0, 1]
        newcolors_even[b + 10:breaks_even[i + 1]] = oldcolors[i]
    shares_cmap_class_even = ListedColormap(newcolors_even)
    shares_cmap_mappable_even = cm.ScalarMappable(cmap=shares_cmap_class_even)

    return (shares_cmap_class, shares_cmap_mappable, shares_cmap_class_even, shares_cmap_mappable_even)




### create 3-part fig for compromise soln with (a) MC paraxis plot, (b) map, & (c) district level COG distributions
def plot_3part_partnership_performance(results_agg, soln_labels, columns, water_providers, states, canals_fkc,
                                      canals_other, tlb, sjr, kings, res_gdf, ideal_direction='top'):
    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(nrows=2, ncols=2, wspace=0.2, hspace=0.2, width_ratios=[1, 1.8])
    fontsize = 12


    ### get disaggregated partnership-level results from individual hydrologic scenarios in reevaluation ensemble
    ### first get results disaggregated by hydrologic scenario MC, but at partnership level
    dict_results_disagg_MC = {}
    for soln_label in soln_labels:
        dict_results_disagg_MC[soln_label] = get_results_disagg_MC(soln_label)
    ### now get results broken down by both MC and water provider level
    dict_results_disagg_MC_district, dict_partners_MC_district, dict_nonpartners_MC_district, \
    dict_shares_MC_district, dict_projects_MC_district = {}, {}, {}, {}, {}
    for soln_label in soln_labels:
        dict_results_disagg_MC_district[soln_label], dict_partners_MC_district[soln_label], dict_nonpartners_MC_district[soln_label], \
            dict_shares_MC_district[soln_label], dict_projects_MC_district[soln_label] = get_results_disagg_MC_district(soln_label)


    #############################################
    ### part 1: shares map. If more than 1 soln in soln_labels, default to showing the last in list.
    #############################################

    ax = fig.add_subplot(gs[:, 0])

    alpha = 1
    nonpartnercolor = 'w'


    ### make map of last partnership in soln_labels
    soln_label = soln_labels[-1]

    partners = dict_partners_MC_district[soln_label]
    shares = dict_shares_MC_district[soln_label]
    project = dict_projects_MC_district[soln_label]

    ### get color of each water provider based on its ownership share in this partnership
    shares_cmap_class, shares_cmap_mappable, shares_cmap_class_even, shares_cmap_mappable_even = get_ownership_share_colors()
    water_providers['color'] = nonpartnercolor
    for d, s in zip(partners, shares):
        water_providers['color'].loc[water_providers['district'] == d] = rgb2hex(shares_cmap_class(s))

    ### first plot districts with zero participation, with no color but outlined in black, except COF & TUL & ID4
    condition = np.logical_and(water_providers['color'] == nonpartnercolor,
                               [d not in ('COF', 'TUL', 'ID4') for d in water_providers['district']])
    water_providers.loc[condition, :].plot('color', ax=ax, color=nonpartnercolor, edgecolor='k', lw=0.5,
                                           legend=True, alpha=alpha, zorder=1)
    ### first plot districts with non-zero participation, except COF & TUL & ID4
    condition = np.logical_and(water_providers['color'] != nonpartnercolor,
                               [d not in ('COF', 'TUL', 'ID4') for d in water_providers['district']])
    water_providers.loc[condition, :].plot('color', ax=ax, color=water_providers.loc[condition, 'color'],
                                           edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1)
    ### now plot COF & TUL, which are overlapping and need to be on top
    condition = [d in ('COF', 'TUL') for d in water_providers['district']]
    water_providers.loc[condition, :].plot('color', ax=ax, color=water_providers.loc[condition, 'color'],
                                           edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1)

    ### axes
    xlim = [1.87e6, 2.03e6]
    xrange = xlim[1] - xlim[0]
    ylim = [4.3e5, 7.22e5]
    yrange = ylim[1] - ylim[0]

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[['top', 'left', 'right', 'bottom']].set_visible(False)

    ### lastly add separate inset for ID4 due to overlapping. make sure scale is same as original
    xfrac = 0.215
    yfrac = 0.115
    axin = ax.inset_axes([0.2, 0.1, xfrac, yfrac])
    xstart = 1.98e6
    ystart = 4.865e5
    axin.set_xlim([xstart, xstart + xfrac * xrange])
    axin.set_ylim([ystart, ystart + yfrac * yrange])
    water_providers.loc[water_providers['district'] == 'ID4'].plot('color', color=water_providers.loc[water_providers['district'] == 'ID4', 'color'],
                                                                   edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1, ax=axin)
    axin.set_xticks([])
    axin.set_yticks([])
    axin.spines[['top', 'left', 'right', 'bottom']].set_edgecolor('0.5')

    ### now add rectangle back in original axes with arrow
    box = [Rectangle((xstart, ystart), xfrac * xrange, yfrac * yrange)]
    pc = PatchCollection(box, facecolor='none', edgecolor='0.5')
    ax.add_collection(pc)
    ax.arrow(xlim[0] + (0.2 + xfrac) * xrange, ylim[0] + (0.1 + yfrac * 0.5) * yrange,
             xstart - (xlim[0] + (0.2 + xfrac) * xrange), ystart - (ylim[0] + (0.1) * yrange),
             color='0.5', lw=1, head_width=3e3, length_includes_head=True, zorder=5)

    ### add infra investment(s) for this partnership
    if project == 1:
        add_tlb_shapes_to_map(ax, canals_fkc, canals_other, tlb, sjr, kings, res_gdf,
                              labels=False, show_fkc=True, show_cfwb=False, show_other=False)
    elif project == 2:
        add_tlb_shapes_to_map(ax, canals_fkc, canals_other, tlb, sjr, kings, res_gdf,
                              labels=False, show_fkc=False, show_cfwb=True, cfwb_size=200, show_other=False)
    elif project == 3:
        add_tlb_shapes_to_map(ax, canals_fkc, canals_other, tlb, sjr, kings, res_gdf,
                              labels=False, show_fkc=True, show_cfwb=True, cfwb_size=200, show_other=False)

    ### colorbar
    cb = plt.colorbar(shares_cmap_mappable_even, ax=ax, ticks=[1 / 12, 3 / 12, 5 / 12, 7 / 12, 9 / 12, 11 / 12],
                      fraction=0.1, orientation='horizontal', pad=0.1)
    _ = cb.ax.set_xticklabels(['0', '1-2', '2-4', '4-8', '8-16', '16+', ], fontsize=fontsize)
    _ = cb.set_label('Ownership share (%)', fontsize=fontsize)  # , labelpad=10)

    ### infra project legend
    if project == 1:
        leg = [Line2D([0], [0], color='firebrick', lw=2, ls='--', label='Canal expansion investment')]
        _ = ax.legend(handles=leg, loc='lower center', bbox_to_anchor=[0.5, -0.12], ncol=1, frameon=False,
                      fontsize=fontsize)
    elif project == 3:
        leg = [Line2D([0], [0], color='firebrick', lw=2, ls='--', label='Canal expansion investment'),
               Line2D([0], [0], color='w', marker='*', markeredgecolor='k', markerfacecolor='firebrick', ms=15,
                      label='Groundwater bank investment')]
        _ = ax.legend(handles=leg, loc='lower center', bbox_to_anchor=[0.5, -0.12], ncol=1, frameon=False,
                      fontsize=fontsize)

    ax.annotate('a)', (0.06, 0.93), xycoords='subfigure fraction', ha='left', va='top', fontsize=fontsize + 2,
                weight='bold')



    ##################################
    ### part 2: paraxis plot with soln_labels highlighted, plus distribution over disaggregated performance in different scenarios
    ################################

    ax = fig.add_subplot(gs[0, 1])

    ### rescale objectives so that parallel axes span 0-1. Note last axis for cog_wp is inverted.
    if len(soln_labels) == 1:
        ### compromise partnership only
        objmins = [11, 35, -100, 100]
        objmaxs = [26, 115, 31, 1000]
    else:
        ### include status quo soln as well, wider margin on 2nd objective
        objmins = [11, 20, -100, 100]
        objmaxs = [26, 115, 31, 1000]

    ressat_wcu = results_agg.loc[:, columns]

    if ideal_direction == 'bottom':
        tops = np.array(objmins)
        bottoms = np.array(objmaxs)
        tops[-1], bottoms[-1] = bottoms[-1], tops[-1]
        ressat_wcu.iloc[:, :-1] = (bottoms[:-1] - ressat_wcu.iloc[:, :-1]) / (bottoms[:-1] - tops[:-1])
        ressat_wcu.iloc[:, -1] = (ressat_wcu.iloc[:, -1] - bottoms[-1]) / (tops[-1] - bottoms[-1])
    elif ideal_direction == 'top':
        tops = np.array(objmaxs)
        bottoms = np.array(objmins)
        tops[-1], bottoms[-1] = bottoms[-1], tops[-1]
        ressat_wcu.iloc[:, -1] = (bottoms[-1] - ressat_wcu.iloc[:, -1]) / (bottoms[-1] - tops[-1])
        ressat_wcu.iloc[:, :-1] = (ressat_wcu.iloc[:, :-1] - bottoms[:-1]) / (tops[:-1] - bottoms[:-1])
    else:
        print('ideal should be "top" or "bottom" based on direction of preference')

    ### plot objs for all partnerships after WCU, brushed. omit statusquo
    for i in range(ressat_wcu.shape[0] - 1):
        for j in range(len(columns) - 1):
            c = '0.8'
            zorder = 1
            y1 = ressat_wcu.iloc[i, j]
            y2 = ressat_wcu.iloc[i, j + 1]
            y = [y1, y2]
            x = [j, j + 1]
            alpha = 0.4
            ax.plot(x, y, c=c, alpha=alpha, zorder=zorder, lw=1)

    ### add top/bottom ranges and ticks at 20% intervals
    for j in range(len(columns)):
        ax.annotate(str(round(tops[j])), [j, 1.02], ha='center', va='bottom', zorder=5, fontsize=fontsize)
        if j == len(columns) - 1:
            ax.annotate(str(round(bottoms[j])) + '+', [j, -0.02], ha='center', va='top', zorder=5, fontsize=fontsize)
        else:
            ax.annotate(str(round(bottoms[j])), [j, -0.02], ha='center', va='top', zorder=5, fontsize=fontsize)

        ax.plot([j, j], [0, 1], c='k', zorder=2)
        for y in np.arange(0, 1.001, 0.2):
            ax.plot([j - 0.03, j + 0.03], [y, y], c='k', zorder=2)

    ### clean up figure
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ['top', 'bottom', 'left', 'right']:
        ax.spines[spine].set_visible(False)

    if ideal_direction == 'top':
        ax.arrow(-0.15, 0.1, 0, 0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)
    elif ideal_direction == 'bottom':
        ax.arrow(-0.15, 0.9, 0, -0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)

    ax.annotate('Direction of preference', xy=(-0.3, 0.5), ha='center', va='center', rotation=90, fontsize=fontsize)

    ax.set_ylim(-0.4, 1.1)
    labels = ['Number\nof\npartners', 'Captured\nwater\ngain\n(GL/yr)', 
              'Captured\nwater\ngain for\nnon-partners\n(GL/yr)', 'Cost of\ngains for\nworst-off\npartner\n($/ML)']
    for i, l in enumerate(labels):
        ax.annotate(l, xy=(i, -0.12), ha='center', va='top', fontsize=fontsize)
    ax.patch.set_alpha(0)

    ### now add detail for particular solns
    colors_brewer = {'s3/soln212': '#1b9e77', 'statusquo/soln0': '#d95f02', 'other': '#7570b3'}

    for sidx, soln_label in enumerate(soln_labels):
        ### highlight soln, wcu agg objectives
        ressat_wcu_soln = ressat_wcu.loc[results_agg['label'] == soln_label, :]
        i = ressat_wcu_soln.index[0]
        xx = []
        yy = []
        for j in range(len(columns) - 1):
            c = colors_brewer[soln_label]
            y1 = ressat_wcu_soln.iloc[0, j]
            y2 = ressat_wcu_soln.iloc[0, j + 1]
            x = np.arange(j, j + 1 + 0.001, 1 / 10)
            y = y1 + (x - j) * (y2 - y1)
            xx += list(x)
            yy += list(y)
        alpha = 1
        ax.plot(xx, yy, c='k', alpha=alpha, zorder=5, lw=3)
        ax.plot(xx, yy, c=c, alpha=alpha, zorder=5, lw=2)

        ### get MC data and plot as distribution
        results_disagg_MC = dict_results_disagg_MC[soln_label]
        columns_MC = ['cog_wp' if c == 'cog_wp_p90' else c for c in columns]
        for o, obj in enumerate(columns_MC):
            if obj == 'cog_wp_p90':
                obj = 'cog_wp'
            results_disagg_MC[f'{obj}_scaled'] = results_disagg_MC[obj].copy()
            if obj not in ['cog_wp']:
                if ideal_direction == 'bottom':
                    results_disagg_MC[f'{obj}_scaled'] = (bottoms[o] - results_disagg_MC[f'{obj}_scaled']) / \
                                                      (bottoms[o] - tops[o])
                elif ideal_direction == 'top':
                    results_disagg_MC[f'{obj}_scaled'] = (results_disagg_MC[f'{obj}_scaled'] - bottoms[o]) / \
                                                      (tops[o] - bottoms[o])
            else:
                if ideal_direction == 'bottom':
                    results_disagg_MC[f'{obj}_scaled'] = (results_disagg_MC[f'{obj}_scaled'] - bottoms[o]) / \
                                                      (tops[o] - bottoms[o])
                elif ideal_direction == 'top':
                    results_disagg_MC[f'{obj}_scaled'] = (bottoms[o] - results_disagg_MC[f'{obj}_scaled']) / \
                                                      (bottoms[o] - tops[o])

        ### add wcu dist
        for o, obj in enumerate(columns_MC[1:]):
            data = results_disagg_MC[f'{obj}_scaled']
            kde = sm.nonparametric.KDEUnivariate(data)
            kde.fit(bw=0.025)

            y = np.arange(0, 1, 0.01)
            x = []
            for yy in y:
                xx = kde.evaluate(yy) * 0.12
                if np.isnan(xx):
                    x.append(0.)
                else:
                    x.append(xx[0])
            x = np.array(x)
            ax.fill_betweenx(y, x + o + 1, o + 1, where=(x > 0.00005), lw=1, alpha=0.6, zorder=4, fc=c, ec='k')

        print(soln_label, 'min, mean, max')
        for o, obj in enumerate(columns_MC[1:]):
            print(obj, results_disagg_MC[f'{obj}'].min(), results_disagg_MC[f'{obj}'].mean(), results_disagg_MC[obj].max())
        print()

    ### add arrow for direction of preference
    if ideal_direction == 'top':
        ax.arrow(-0.15, 0.1, 0, 0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)
    elif ideal_direction == 'bottom':
        ax.arrow(-0.15, 0.9, 0, -0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)
    ax.annotate('Direction of preference', xy=(-0.3, 0.5), ha='center', va='center', rotation=90, fontsize=fontsize)

    plt.xlim([-0.3, 4.3])

    ax.annotate('b)', (0.4, 0.93), xycoords='subfigure fraction', ha='left', va='top', fontsize=fontsize + 2, weight='bold')



    #############################################
    ### part 3: distributions for district level COG
    #############################################
    ax = fig.add_subplot(gs[1, 1])

    soln_label = soln_labels[-1]

    alpha = 1
    bw = 1.0
    bw_scalar = 10
    pdf_scalar = 1.

    ridgesep = 0.1
    xmin = 0
    xmax = 1030

    results_disagg_MC_district = dict_results_disagg_MC_district[soln_label]
    partners = dict_partners_MC_district[soln_label]
    nonpartners = dict_nonpartners_MC_district[soln_label]
    shares = dict_shares_MC_district[soln_label]
    project = dict_projects_MC_district[soln_label]

    ### first do kde for overall partnership
    avg_gap = 2

    ax.axhline(avg_gap * ridgesep, color='0.8', zorder=1, lw=1)
    c = f'overall_cog_p'
    data = results_disagg_MC_district[c]
    kde_district = sm.nonparametric.KDEUnivariate(data)
    kde_district.fit(bw=bw * bw_scalar)

    x = np.arange(xmin, xmax, 0.1 * bw_scalar)
    y = []
    for xx in x:
        yy = kde_district.evaluate(xx) * bw_scalar * pdf_scalar
        if np.isnan(yy):
            y.append(0.)
        else:
            y.append(yy[0])
    y = np.array(y)
    color = '0.2'
    ax.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2,
                    fc=color, ec=color)

    c = f'overall_cog_wp'
    data = results_disagg_MC_district[c]
    kde_district = sm.nonparametric.KDEUnivariate(data)
    # kde_district.fit(kernel='tri', fft=False, bw=bw * bw_scalar)
    kde_district.fit(bw=bw * bw_scalar)
    x = np.arange(xmin, xmax, 0.1 * bw_scalar)
    y = []
    for xx in x:
        yy = kde_district.evaluate(xx) * bw_scalar * pdf_scalar
        if np.isnan(yy):
            y.append(0.)
        else:
            y.append(yy[0])
    y = np.array(y)
    color = 'firebrick'
    ax.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2,
                    fc=color, ec=color)

    for i, d in enumerate(partners):
        ### set bottom of "ridge" in decreasing order (smallest share at bottom)
        bottom = (-i * ridgesep)
        plt.axhline(bottom, color='0.8', zorder=1, lw=1)

        ### evaluate & plot kde
        c = f'{d}_cog'
        data = results_disagg_MC_district[c]
        kde_district = sm.nonparametric.KDEUnivariate(data)
        #     kde_district.fit(kernel='tri', fft=False, bw=bw * bw_scalar)
        kde_district.fit(bw=bw * bw_scalar)

        x = np.arange(xmin, xmax, 0.1 * bw_scalar)
        y = []
        for xx in x:
            yy = kde_district.evaluate(xx) * bw_scalar * pdf_scalar
            if np.isnan(yy):
                y.append(0.)
            else:
                y.append(yy[0])
        y = np.array(y)
        color = shares_cmap_class(shares[i])
        plt.fill_between(x, y + bottom, bottom, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2, fc=color, ec='k')

    ax.set_yticks([avg_gap * ridgesep] + [-i * ridgesep for i in range(len(partners)) if i % avg_gap == 0],
                  ['All'] + [str(i + 1) for i in range(len(partners)) if i % avg_gap == 0])
    plt.xticks([0, 250, 500, 750, 1000], ['0', '250', '500', '750', "1000+"])
    ax.xaxis.set_major_locator(MultipleLocator(250))
    ax.xaxis.set_minor_locator(MultipleLocator(50))

    plt.xlim([xmin, xmax])
    plt.ylabel('Partners\n' + r'(Increasing share $\rightarrow$)', fontsize=fontsize)
    plt.xlabel('Cost of gains ($/ML)', fontsize=fontsize)
    ax.spines[['top', 'left', 'right']].set_visible(False)

    ax.annotate('c)', (0.4, 0.48), xycoords='subfigure fraction', ha='left', va='top',
                fontsize=fontsize + 2, weight='bold')


    if len(soln_labels) == 1:
        plt.savefig(f'{fig_dir}fig_3part_compromise.png', bbox_inches='tight', dpi=dpi, transparent=True)
        plt.savefig(f'{fig_dir}fig_3part_compromise.pdf', bbox_inches='tight')

    else:
        plt.savefig(f'{fig_dir}fig_3part_statusquo.png', bbox_inches='tight', dpi=dpi, transparent=True)
        plt.savefig(f'{fig_dir}fig_3part_statusquo.pdf', bbox_inches='tight')







### create 3-part fig for compromise soln with (a) MC paraxis plot, (b) map, & (c) district level COG distributions
def compare_partnership_performance_climate(results_agg, soln_label, columns, ideal_direction='top'):
    fig = plt.figure(figsize=(12, 12))
    gs = gridspec.GridSpec(nrows=3, ncols=1, wspace=0.2, hspace=0.2)#, width_ratios=[1, 1.8])
    fontsize = 12


    ### first get results disaggregated by hydrologic scenario MC, but at partnership level
    dict_results_disagg_MC = {}
    for reeval_type in ['mhmm', 'projections']:
        dict_results_disagg_MC[reeval_type] = get_results_disagg_MC(soln_label, reeval_type = reeval_type)


    ### now get results broken down by both MC and water provider level
    dict_results_disagg_MC_district, dict_partners_MC_district, dict_nonpartners_MC_district, \
    dict_shares_MC_district, dict_projects_MC_district = {}, {}, {}, {}, {}
    for reeval_type in ['mhmm', 'projections']:
        dict_results_disagg_MC_district[reeval_type], dict_partners_MC_district[reeval_type], \
        dict_nonpartners_MC_district[reeval_type], \
        dict_shares_MC_district[reeval_type], dict_projects_MC_district[reeval_type] = get_results_disagg_MC_district(
            soln_label, reeval_type = reeval_type)



    ##################################
    ### part 1: paraxis plot with soln_labels highlighted, plus distribution over disaggregated performance for MHMM & climate projections
    ################################

    ax = fig.add_subplot(gs[0])

    ### rescale objectives so that parallel axes span 0-1. Note last axis for cog_wp is inverted.
    if soln_label in ['s3/soln212', 'compromise']:
        objmins = [11, 0, -50, 0]
        objmaxs = [26, 175, 50, 1000]
    elif soln_label in ['statusquo/soln0', 'statusquo']:
        objmins = [11, 0, -50, 0]
        objmaxs = [25, 175, 50, 1000]

    ressat_wcu = results_agg.loc[:, columns]

    if ideal_direction == 'bottom':
        tops = np.array(objmins)
        bottoms = np.array(objmaxs)
        tops[-1], bottoms[-1] = bottoms[-1], tops[-1]
        ressat_wcu.iloc[:, :-1] = (bottoms[:-1] - ressat_wcu.iloc[:, :-1]) / (bottoms[:-1] - tops[:-1])
        ressat_wcu.iloc[:, -1] = (ressat_wcu.iloc[:, -1] - bottoms[-1]) / (tops[-1] - bottoms[-1])
    elif ideal_direction == 'top':
        tops = np.array(objmaxs)
        bottoms = np.array(objmins)
        tops[-1], bottoms[-1] = bottoms[-1], tops[-1]
        ressat_wcu.iloc[:, -1] = (bottoms[-1] - ressat_wcu.iloc[:, -1]) / (bottoms[-1] - tops[-1])
        ressat_wcu.iloc[:, :-1] = (ressat_wcu.iloc[:, :-1] - bottoms[:-1]) / (tops[:-1] - bottoms[:-1])
    else:
        print('ideal should be "top" or "bottom" based on direction of preference')

    ### plot objs for all partnerships after WCU, brushed
    for i in range(ressat_wcu.shape[0]):
        for j in range(len(columns) - 1):
            c = '0.8'
            zorder = 1
            y1 = ressat_wcu.iloc[i, j]
            y2 = ressat_wcu.iloc[i, j + 1]
            y = [y1, y2]
            x = [j, j + 1]
            alpha = 0.4
            ax.plot(x, y, c=c, alpha=alpha, zorder=zorder, lw=1)

    ### add top/bottom ranges and ticks at 20% intervals
    for j in range(len(columns)):
        ax.annotate(str(round(tops[j])), [j, 1.02], ha='center', va='bottom', zorder=5, fontsize=fontsize)
        if j == len(columns) - 1:
            ax.annotate(str(round(bottoms[j])) + '+', [j, -0.02], ha='center', va='top', zorder=5, fontsize=fontsize)
        else:
            ax.annotate(str(round(bottoms[j])), [j, -0.02], ha='center', va='top', zorder=5, fontsize=fontsize)

        ax.plot([j, j], [0, 1], c='k', zorder=2)
        for y in np.arange(0, 1.001, 0.2):
            ax.plot([j - 0.03, j + 0.03], [y, y], c='k', zorder=2)

    ### clean up figure
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ['top', 'bottom', 'left', 'right']:
        ax.spines[spine].set_visible(False)

    if ideal_direction == 'top':
        ax.arrow(-0.15, 0.1, 0, 0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)
    elif ideal_direction == 'bottom':
        ax.arrow(-0.15, 0.9, 0, -0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)

    ax.annotate('Direction of preference', xy=(-0.3, 0.5), ha='center', va='center', rotation=90, fontsize=fontsize)

    ax.set_ylim(-0.4, 1.5)
    labels = ['Number\nof\npartners', 'Captured\nwater\ngain\n(GL/yr)', 
              'Captured\nwater\ngain for\nnon-partners\n(GL/yr)', 'Cost of\ngains for\nworst-off\npartner\n($/ML)']
    for i, l in enumerate(labels):
        ax.annotate(l, xy=(i, -0.12), ha='center', va='top', fontsize=fontsize)
    ax.patch.set_alpha(0)

    ### now add detail for particular solns
    colors_brewer = {'s3/soln212': '#1b9e77', 'statusquo/soln0': '#d95f02', 'other': '#7570b3'}

    ### highlight soln, wcu agg objectives
    ressat_wcu_soln = ressat_wcu.loc[results_agg['label'] == soln_label, :]
    i = ressat_wcu_soln.index[0]
    xx = []
    yy = []
    for j in range(len(columns) - 1):
        c = colors_brewer[soln_label]
        y1 = ressat_wcu_soln.iloc[0, j]
        y2 = ressat_wcu_soln.iloc[0, j + 1]
        x = np.arange(j, j + 1 + 0.001, 1 / 10)
        y = y1 + (x - j) * (y2 - y1)
        xx += list(x)
        yy += list(y)
    alpha = 1
    ax.plot(xx, yy, c='k', alpha=alpha, zorder=5, lw=3)
    ax.plot(xx, yy, c=c, alpha=alpha, zorder=5, lw=2)

    ### get MC data and plot as distribution
    for reeval_type in ['mhmm','projections']:
        c = c if reeval_type == 'mhmm' else colors_brewer['other']
        results_disagg_MC = dict_results_disagg_MC[reeval_type]
        columns_MC = ['cog_wp' if c == 'cog_wp_p90' else c for c in columns]
        for o, obj in enumerate(columns_MC):
            if obj == 'cog_wp_p90':
                obj = 'cog_wp'
            results_disagg_MC[f'{obj}_scaled'] = results_disagg_MC[obj].copy()
            if obj not in ['cog_wp']:
                if ideal_direction == 'bottom':
                    results_disagg_MC[f'{obj}_scaled'] = (bottoms[o] - results_disagg_MC[f'{obj}_scaled']) / \
                                                      (bottoms[o] - tops[o])
                elif ideal_direction == 'top':
                    results_disagg_MC[f'{obj}_scaled'] = (results_disagg_MC[f'{obj}_scaled'] - bottoms[o]) / \
                                                      (tops[o] - bottoms[o])
            else:
                if ideal_direction == 'bottom':
                    results_disagg_MC[f'{obj}_scaled'] = (results_disagg_MC[f'{obj}_scaled'] - bottoms[o]) / \
                                                      (tops[o] - bottoms[o])
                elif ideal_direction == 'top':
                    results_disagg_MC[f'{obj}_scaled'] = (bottoms[o] - results_disagg_MC[f'{obj}_scaled']) / \
                                                      (bottoms[o] - tops[o])

        ### add wcu dist
        for o, obj in enumerate(columns_MC[1:]):
            data = results_disagg_MC[f'{obj}_scaled']
            kde = sm.nonparametric.KDEUnivariate(data)
            kde.fit(bw=0.025)

            y = np.arange(0, 1, 0.01)
            x = []
            for yy in y:
                xx = kde.evaluate(yy) * 0.08
                if np.isnan(xx):
                    x.append(0.)
                else:
                    x.append(xx[0])
            x = np.array(x)
            ax.fill_betweenx(y, x + o + 1, o + 1, where=(x > 0.00005), lw=1, alpha=0.6, zorder=4, fc=c, ec='k')

        print(soln_label, 'min, mean, max')
        for o, obj in enumerate(columns_MC[1:]):
            print(obj, results_disagg_MC[f'{obj}'].min(), results_disagg_MC[f'{obj}'].mean(), results_disagg_MC[obj].max())
        print()

    ### add arrow for direction of preference
    if ideal_direction == 'top':
        ax.arrow(-0.15, 0.1, 0, 0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)
    elif ideal_direction == 'bottom':
        ax.arrow(-0.15, 0.9, 0, -0.7, head_width=0.08, head_length=0.05, color='k', lw=1.5)
    ax.annotate('Direction of preference', xy=(-0.3, 0.5), ha='center', va='center', rotation=90, fontsize=fontsize)

    plt.xlim([-0.3, 4])

    ax.annotate('a)', (0.01, 0.92), xycoords='subfigure fraction', ha='left', va='top', fontsize=fontsize + 2, weight='bold')



    #############################################
    ### part 2 & 3: distributions for district level COG for MHMM & climate projections
    #############################################
    for r, reeval_type in enumerate(['mhmm','projections']):

        ax = fig.add_subplot(gs[r+1])


        alpha = 1
        bw = 1.0
        bw_scalar = 10
        pdf_scalar = 1.

        ridgesep = 0.1
        xmin = 0
        xmax = 1030

        results_disagg_MC_district = dict_results_disagg_MC_district[reeval_type]
        partners = dict_partners_MC_district[reeval_type]
        nonpartners = dict_nonpartners_MC_district[reeval_type]
        shares = dict_shares_MC_district[reeval_type]
        project = dict_projects_MC_district[reeval_type]

        ### first do kde for overall partnership
        avg_gap = 2

        ax.axhline(avg_gap * ridgesep, color='0.8', zorder=1, lw=1)
        c = f'overall_cog_p'
        data = results_disagg_MC_district[c]
        kde_district = sm.nonparametric.KDEUnivariate(data)
        kde_district.fit(bw=bw * bw_scalar)

        x = np.arange(xmin, xmax, 0.1 * bw_scalar)
        y = []
        for xx in x:
            yy = kde_district.evaluate(xx) * bw_scalar * pdf_scalar
            if np.isnan(yy):
                y.append(0.)
            else:
                y.append(yy[0])
        y = np.array(y)
        color = '0.2'
        ax.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2,
                        fc=color, ec=color)

        c = f'overall_cog_wp'
        data = results_disagg_MC_district[c]
        kde_district = sm.nonparametric.KDEUnivariate(data)
        # kde_district.fit(kernel='tri', fft=False, bw=bw * bw_scalar)
        kde_district.fit(bw=bw * bw_scalar)
        x = np.arange(xmin, xmax, 0.1 * bw_scalar)
        y = []
        for xx in x:
            yy = kde_district.evaluate(xx) * bw_scalar * pdf_scalar
            if np.isnan(yy):
                y.append(0.)
            else:
                y.append(yy[0])
        y = np.array(y)
        color = 'firebrick'
        ax.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2,
                        fc=color, ec=color)

        shares_cmap_class, shares_cmap_mappable, shares_cmap_class_even, shares_cmap_mappable_even = get_ownership_share_colors()

        for i, d in enumerate(partners):
            ### set bottom of "ridge" in decreasing order (smallest share at bottom)
            bottom = (-i * ridgesep)
            plt.axhline(bottom, color='0.8', zorder=1, lw=1)

            ### evaluate & plot kde
            c = f'{d}_cog'
            data = results_disagg_MC_district[c]
            kde_district = sm.nonparametric.KDEUnivariate(data)
            #     kde_district.fit(kernel='tri', fft=False, bw=bw * bw_scalar)
            kde_district.fit(bw=bw * bw_scalar)

            x = np.arange(xmin, xmax, 0.1 * bw_scalar)
            y = []
            for xx in x:
                yy = kde_district.evaluate(xx) * bw_scalar * pdf_scalar
                if np.isnan(yy):
                    y.append(0.)
                else:
                    y.append(yy[0])
            y = np.array(y)
            color = shares_cmap_class(shares[i])
            plt.fill_between(x, y + bottom, bottom, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2, fc=color, ec='k')

        ax.set_yticks([avg_gap * ridgesep] + [-i * ridgesep for i in range(len(partners)) if i % avg_gap == 0],
                      ['All'] + [str(i + 1) for i in range(len(partners)) if i % avg_gap == 0])
        plt.xticks([0, 250, 500, 750, 1000], ['0', '250', '500', '750', "1000+"])
        ax.xaxis.set_major_locator(MultipleLocator(250))
        ax.xaxis.set_minor_locator(MultipleLocator(50))

        plt.xlim([xmin, xmax])
        plt.ylabel('Partners\n' + r'(Increasing share $\rightarrow$)', fontsize=fontsize)
        plt.xlabel('Cost of gains ($/ML)', fontsize=fontsize)
        ax.spines[['top', 'left', 'right']].set_visible(False)

        axlabel = 'b)' if r==0 else 'c)'
        axheight = 0.62 if r==0 else 0.31
        ax.annotate(axlabel, (0.01, axheight), xycoords='subfigure fraction', ha='left', va='top',
                    fontsize=fontsize + 2, weight='bold')

    soln_figlabel = 'statusquo' if 'statusquo' in soln_label else 'compromise'
    plt.savefig(f"{fig_dir}fig_performance_climate_{soln_figlabel}.png", bbox_inches='tight', dpi=dpi, transparent=True)
    plt.savefig(f"{fig_dir}fig_performance_climate_{soln_figlabel}.pdf", bbox_inches='tight')






# ### function to compare time series of performance in wet vs dry scenarios
# def compare_partnership_performance_timeseries_wetdry(projection_label, soln_label):

#     fig, axs = plt.subplots(4,1,figsize=(10,10), gridspec_kw={'hspace':0.1})

#     results_projections_dir2 = results_projections_dir #+ '../climate_reeval_infra_save/'

#     f_soln = h5py.File(f'{results_projections_dir2}/{soln_label}/{projection_label}/results.hdf5')['s']
#     f_baseline = h5py.File(f'{results_projections_dir2}/baseline/{projection_label}/results.hdf5')['s']

#     ### get full list of column names for each dataset. these may not line up across datasets.
#     cols_soln, cols_baseline = [], []
#     for c in range(100):
#         if f'columns{c}' in f_soln.attrs.keys():
#             cols_soln += [s.decode('utf-8') for s in f_soln.attrs[f'columns{c}']]
#         if f'columns{c}' in f_baseline.attrs.keys():
#             cols_baseline += [s.decode('utf-8') for s in f_baseline.attrs[f'columns{c}']]
#     print(cols_baseline)
#     print([c for c in cols_baseline if 'fresnoid' in c])

#     num_days = f_baseline.shape[0]
#     start_date = f_baseline.attrs['start_date']
#     start_date = datetime.datetime(int(start_date.split('-')[0]), int(start_date.split('-')[1]), int(start_date.split('-')[2]))
#     dates = pd.DatetimeIndex([start_date + datetime.timedelta(days=n) for n in range(num_days)])
#     wy = np.array([y if m < 10 else y+1 for y,m in zip(dates.year, dates.month)])

#     ### get set of partners
#     partnership = json.load(open(f'{results_projections_dir2}/{soln_label}/FKC_scenario.json'))
#     partners = [k for k,v in partnership['ownership_shares'].items() if v>0]
#     partners_labels = [district_label_dict[k] for k in partners]


#     ### undo summation over water year for some timeseries
#     def undo_summation_wy(data, wy):
#         for y in range(wy.min() + 1, wy.max() + 1):
#             maxprevious = data[wy < y][-1]
#             data[wy == y] += maxprevious
#         data[1:] = data[1:] - data[:-1]
#         return data

#     ### moving average of timeseries
#     def moving_average(data, window):
#         if window <= 1:
#             return data
#         else:
#             window_min_1 = window - 1
#         data_ma = np.cumsum(data)
#         data_ma[window_min_1:] = (data_ma[window_min_1:] - data_ma[:-window_min_1]) / window
#         data_ma[:window_min_1] = data[:window_min_1]
#         return data_ma

#     ### get data for particular timeseries
#     def get_timeseries(f_hdf5, cols_hdf5, column, wy, is_summation_wy, smooth_window=0):
#         data = f_hdf5[:, [i for i in range(f_hdf5.shape[1]) if cols_hdf5[i] == column]]
#         if data.shape[1] > 0:
#             data = data[:,0] * kaf_to_gl
#             if is_summation_wy:
#                 data = undo_summation_wy(data, wy)
#             data = moving_average(data, window=smooth_window)
#         else:
#             data = np.zeros(f_hdf5.shape[0])
#         return data


#     color_fill_baseline = '0.7'
#     color_fill_positive = 'navy'
#     color_fill_negative = 'firebrick'

#     #################################################
#     ### part 1: show hydrology by years
#     ##################################################
#     ax = axs[0]
#     smooth_window = 0

#     Q = get_timeseries(f_baseline, cols_baseline,  'millerton_Q', wy, False, smooth_window)
#     ax.plot(dates, Q, color='k')
#     ax.set_ylabel('Millerton\nInflow (GL/day)')
#     ax.set_xticklabels([])

#     #################################################
#     ### part 2: show FKC flow by years
#     ##################################################
#     ax = axs[1]

#     fkc_soln = get_timeseries(f_soln, cols_soln,  'fkc_NFWB_flow', wy, False,smooth_window)
#     fkc_baseline = get_timeseries(f_baseline, cols_baseline,  'fkc_NFWB_flow', wy, False,smooth_window)

#     ax.fill_between(dates, fkc_baseline, color=color_fill_baseline, lw=0)
#     ax.fill_between(dates, fkc_baseline, fkc_soln, where=fkc_baseline<fkc_soln, color=color_fill_positive, lw=0)
#     ax.fill_between(dates, fkc_baseline, fkc_soln, where=fkc_baseline>fkc_soln, color=color_fill_negative, lw=0)
#     ax.set_ylabel('FKC\nFlow (GL/day)')
#     ax.set_xticklabels([])

#     ### now plot cumulative FKC flow gain on 2nd y axis
#     flow_gain_soln = np.cumsum(fkc_soln - fkc_baseline)
#     ax2 = ax.twinx()
#     ax2.plot(dates, flow_gain_soln, color='0.5')
#     ax2.set_ylabel('Cumulative Gain\nin Flow (GL)')

#     #################################################
#     ### part 3: show deliveries by years with timeseries overlaid
#     ##################################################

#     ax = axs[2]

#     ### get deliveries total for partner (following workflow in main_cy.get_district_results())
#     def get_deliveries_partner(partner, f_hdf5, cols_hdf5, wy, is_summation_wy, smooth_window):
#         cols_partner = [c for c in cols_hdf5 if c.split('_')[0] == partner]
#         if partner in ['fresnoid']:
#             print(cols_partner)
#         deliveries = np.zeros(f_hdf5.shape[0])
#         for c in cols_partner:
#             if len(c.split('_')) > 2:
#                 if c.split('_')[2] in ['delivery', 'flood', 'SW']:
#                     if partner == 'fresnoid':
#                         print(c, get_timeseries(f_hdf5, cols_hdf5, c, wy, is_summation_wy, smooth_window).mean()*365)
#                     deliveries += get_timeseries(f_hdf5, cols_hdf5, c, wy, is_summation_wy, smooth_window)
#                 elif c.split('_')[2] == 'GW':
#                     if partner == 'fresnoid':
#                         print(c, get_timeseries(f_hdf5, cols_hdf5, c, wy, is_summation_wy, smooth_window).mean() * 365)
#                     deliveries -= get_timeseries(f_hdf5, cols_hdf5, c, wy, is_summation_wy, smooth_window)
#         print(partner, deliveries.sum()/(f_soln.shape[0]/365))
#         return deliveries

#     def get_deliveries_partnership(partners, f_hdf5, cols_hdf5, wy, is_summation_wy, smooth_window):
#         deliveries = np.zeros(f_hdf5.shape[0])
#         for partner in partners:
#             deliveries += get_deliveries_partner(partner, f_hdf5, cols_hdf5, wy, is_summation_wy, smooth_window)
#         return deliveries

#     deliveries_soln = get_deliveries_partnership(partners_labels, f_soln, cols_soln, wy, True, smooth_window)
#     deliveries_baseline = get_deliveries_partnership(partners_labels, f_baseline, cols_baseline, wy, True, smooth_window)

#     ### plot daily deliveries as areas
#     ax.fill_between(dates, deliveries_baseline, color=color_fill_baseline, lw=0)
#     ax.fill_between(dates, deliveries_baseline, deliveries_soln, where=deliveries_baseline<deliveries_soln, color=color_fill_positive, lw=0)
#     ax.fill_between(dates, deliveries_baseline, deliveries_soln, where=deliveries_baseline>deliveries_soln, color=color_fill_negative, lw=0)
#     ax.set_ylabel('Deliveries\n(GL/day)')
#     ax.set_xticklabels([])

#     ### now plot cumulative captured water gain on 2nd y axis
#     cwg_soln = np.cumsum(deliveries_soln - deliveries_baseline)
#     ax2 = ax.twinx()
#     ax2.plot(dates, cwg_soln, color='0.5')
#     ax2.set_ylabel('Cumulative Gain\nin Deliveries (GL)')


#     ### compare to automated aggregated results
#     agg_results_soln = json.load(open(f'{results_projections_dir2}/{soln_label}/{projection_label}/{soln_label}_mc{projection_label}.json'))
#     agg_results_baseline = json.load(open(f'{results_projections_dir2}/baseline/{projection_label}/{projection_label}_baseline.json'))
#     cwg_soln_agg = 0
#     pump_soln_agg = 0
#     cwg_baseline_agg = 0
#     pump_baseline_agg = 0
#     for p in partners:
#         cwg_soln_agg += agg_results_soln[p]['avg_captured_water']
#         pump_soln_agg += agg_results_soln[p]['avg_pumping']
#         cwg_baseline_agg += agg_results_baseline[p]['avg_captured_water']
#         pump_baseline_agg += agg_results_baseline[p]['avg_pumping']
#     cwg_soln_agg *= kaf_to_gl
#     pump_soln_agg *= kaf_to_gl
#     cwg_baseline_agg *= kaf_to_gl
#     pump_baseline_agg *= kaf_to_gl
#     for p in partners:
#         print(p, (agg_results_soln[p]['avg_captured_water'] - agg_results_baseline[p]['avg_captured_water']) * kaf_to_gl)


#     print(soln_label, projection_label, 'cwg', cwg_soln[-1]/(f_soln.shape[0]/365), cwg_soln_agg - cwg_baseline_agg)

#     #################################################
#     ### part 4: show deliveries & recoveries from CFWB
#     ##################################################

#     ax = axs[3]

#     def get_bank_balance_partnership(partners, f_hdf5, cols_hdf5, wy, is_summation_wy, smooth_window):
#         cols_bank_balances = [f'centralfriantwb_{p}' for p in partners]
#         balances = np.zeros(f_hdf5.shape[0])
#         for c in cols_bank_balances:
#             balances += get_timeseries(f_hdf5, cols_hdf5,  c, wy, is_summation_wy, smooth_window)
#         return balances

#     balances_soln = get_bank_balance_partnership(partners, f_soln, cols_soln, wy, False, smooth_window)
#     balances_soln_diff = balances_soln.copy()
#     balances_soln_diff[1:] -= balances_soln_diff[:-1]

#     ### plot differenced time series similar to above
#     ax.fill_between(dates, balances_soln_diff, 0, where=balances_soln_diff>0, color=color_fill_positive, lw=0)
#     ax.fill_between(dates, balances_soln_diff, 0, where=balances_soln_diff<0, color=color_fill_negative, lw=0)
#     ax.set_ylabel(r'$\Delta$ '+'Groundwater Bank\nBalance (GL/day)')

#     ### now use second y axis to plot the cumulative bank balance
#     ax2 = ax.twinx()
#     ax2.plot(dates, balances_soln, color='0.5')

#     ax2.set_ylabel('Groundwater Bank\nBalance (GL)', color='0.5')




#     ##################################################


#     plt.savefig(f'{fig_dir}fig_partnership_timeseries_{soln_label}_{projection_label}.png',
#                 bbox_inches='tight', dpi=dpi)#, transparent=True)







### 3-part figure showing partner-level disaggregated performance for a partnership
def plot_partner_disagg_performance(results, soln_label):
    fontsize = 10
    labels = ['a)', 'b)', 'c)']
    use_all_nonpartners = True
    bw = 0.5
    alpha = 1

    fig = plt.figure(figsize=(8, 8))
    gs = gridspec.GridSpec(nrows=3, ncols=2, hspace=0.45, wspace=0.3, height_ratios=[6, 6, 1])

    results_soln = results.loc[results['label'] == soln_label]
    shares_cmap_class, shares_cmap_mappable, shares_cmap_class_even, shares_cmap_mappable_even = get_ownership_share_colors()


    ### part 1: distribution of captured water gains by partner
    ax0 = fig.add_subplot(gs[0, 0])

    ### get partners with nonzero shares, ordered by share
    sharecols = [c for c in results_soln.columns if 'share' in c]
    partners = [c.split('_')[1] for c in sharecols if results_soln[c].iloc[0] > 0]
    shares = [results_soln[f'share_{c}'].iloc[0] for c in partners]
    order = np.argsort(shares)[::-1]
    shares = [shares[o] for o in order]
    partners = [partners[o] for o in order]
    project = projects[results_soln['proj'].iloc[0]]
    annual_debt_payment = annual_debt_payment_dict[project]
    nonpartners = [c.split('_')[1] for c in sharecols if results_soln[c].iloc[0] == 0]

    df_mc, partners, nonpartners, partner_shares, project = get_results_disagg_MC_district(soln_label)
    df_mc['overall_cwg'] = df_mc.loc[:, [p + '_cwg' for p in partners]].sum(axis=1) / len(partners)
    df_mc['overall_cwg_np'] = df_mc.loc[:, [p + '_cwg' for p in nonpartners]].sum(axis=1) / len(nonpartners)
    df_mc['overall_cog'] = annual_debt_payment / df_mc['overall_cwg'] / len(partners) / 1000
    df_mc['worst_off_cog'] = df_mc[[f'{d}_cog' for d in partners]].max(axis=1)

    ridgesep = 0.2
    xmin = -100
    xmax = 120

    ### first do kde for overall partnership
    if len(partners) > 30:
        avg_gap = 4
    elif len(partners) > 15:
        avg_gap = 2
    else:
        avg_gap = 1

    ax0.axhline(avg_gap * ridgesep, color='0.8', zorder=1, lw=1)
    c = f'overall_cwg'
    kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
    kde_district.fit(bw=bw)
    x = np.arange(xmin, xmax, 0.1)
    y = []
    for xx in x:
        yy = kde_district.evaluate(xx)
        if np.isnan(yy):
            y.append(0.)
        else:
            y.append(yy[0])
    y = np.array(y)
    color = '0.2'
    ax0.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha,
                     zorder=2, fc=color, ec='k')

    ### now plot kdes for individual partners
    xlim = [0, 0]
    for i, d in enumerate(partners):
        ### set bottom of "ridge" in decreasing order (smallest share at bottom)
        bottom = (-i * ridgesep)
        ax0.axhline(bottom, color='0.8', zorder=1, lw=1)

        ### evaluate & plot kde
        c = f'{d}_cwg'
        kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
        kde_district.fit(bw=bw)
        x = np.arange(xmin, xmax, 0.1)
        y = []
        for xx in x:
            yy = kde_district.evaluate(xx)
            if np.isnan(yy):
                y.append(0.)
            else:
                y.append(yy[0])
        y = np.array(y)
        color = shares_cmap_class(shares[i])
        ax0.fill_between(x, y + bottom, bottom, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2, fc=color,
                         ec='k')
        xlim = [min(xlim[0], x[y > 0.00005][0]), max(xlim[1], x[y > 0.00005][-1])]

    ax0.set_yticks([avg_gap * ridgesep] + [-i * ridgesep for i in range(len(partners)) if i % avg_gap == 0],
                   ['All'] + [str(i + 1) for i in range(len(partners)) if i % avg_gap == 0])
    ax0.set_ylabel('Partners')
    ax0.xaxis.set_major_locator(MultipleLocator(10))
    ax0.xaxis.set_minor_locator(MultipleLocator(2.5))

    xlim = [min(xlim[0] - 2, 0), max(xlim[1] + 2, 30)]
    ax0.set_xlim(xlim)
    ax0.set_xlabel('Captured water gain (GL/year)', fontsize=fontsize)
    ax0.spines[['top', 'left', 'right']].set_visible(False)


    ###############################################
    ### now do cost of gains figures
    ax1 = fig.add_subplot(gs[1, 0])
    ridgesep = 0.2
    xmin = 0
    xmax = 1030

    kde_scaler = 1000/40 ### set so that the smoothness of cog distributions will meet cwg given different x axes

    ### first do kde for overall partnership - avg cost
    ax1.axhline(avg_gap * ridgesep, color='0.8', zorder=1, lw=1)
    c = f'overall_cog'
    kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
    #     kde_district.fit(kernel='tri', fft=False, bw=1.5* kde_scaler)
    kde_district.fit(bw=bw * kde_scaler)
    x = np.arange(xmin, xmax, 0.1)
    y = []
    for xx in x:
        yy = kde_district.evaluate(xx) * kde_scaler
        if np.isnan(yy):
            y.append(0.)
        else:
            y.append(yy[0])
    y = np.array(y)
    color = '0.2'
    ax1.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha,
                     zorder=2, fc=color, ec='k')

    ### now do kde for overall partnership - worst-off cost
    c = f'worst_off_cog'
    kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
    kde_district.fit(bw=bw * kde_scaler)
    x = np.arange(xmin, xmax, 0.1)
    y = []
    for xx in x:
        yy = kde_district.evaluate(xx) * kde_scaler
        if np.isnan(yy):
            y.append(0.)
        else:
            y.append(yy[0])
    y = np.array(y)
    color = 'firebrick'
    ax1.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha,
                     zorder=2, fc=color, ec=color)

    ### now plot kdes for individual partners
    xlim = [0, 0]
    for i, d in enumerate(partners):
        ### set bottom of "ridge" in decreasing order (smallest share at bottom)
        bottom = (-i * ridgesep)
        ax1.axhline(bottom, color='0.8', zorder=1, lw=1)

        ### evaluate & plot kde
        c = f'{d}_cog'
        kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
        kde_district.fit(bw=bw * kde_scaler)
        x = np.arange(xmin, xmax, 0.1)
        y = []
        for xx in x:
            yy = kde_district.evaluate(xx) * kde_scaler
            if np.isnan(yy):
                y.append(0.)
            else:
                y.append(yy[0])
        y = np.array(y)
        color = shares_cmap_class(shares[i])
        ax1.fill_between(x, y + bottom, bottom, where=np.logical_and(y > 0.0001, x >= 0), lw=0.5, alpha=alpha,
                         zorder=2, fc=color, ec='k')
        xlim = [min(xlim[0], x[y > 0.00005][0]), max(xlim[1], x[y > 0.00005][-1])]

    ax1.set_yticks([avg_gap * ridgesep] + [-i * ridgesep for i in range(len(partners)) if i % avg_gap == 0],
                   ['All'] + [str(i + 1) for i in range(len(partners)) if i % avg_gap == 0])
    ax1.set_ylabel('Partners')

    xlim = [0, min(max(xlim[1] + 20, 30), 1030)]
    ax1.set_xlim(xlim)

    ax1.set_xlabel('Cost of gains ($/ML)', fontsize=fontsize)
    ax1.spines[['top', 'left', 'right']].set_visible(False)

    if xlim[1] < 300:
        ax1.xaxis.set_major_locator(MultipleLocator(50))
        ax1.xaxis.set_minor_locator(MultipleLocator(12.5))
    else:
        ax1.xaxis.set_major_locator(MultipleLocator(250))
        ax1.xaxis.set_minor_locator(MultipleLocator(50))
        ax1.set_xticks([0, 250, 500, 750, 1000], ['0', '250', '500', '750', "1000+"])


    ##########################################################
    ### now do captured water gains for nonpartners
    ax3 = fig.add_subplot(gs[:2, 1])

    

    ### get order of nonpartners based on expected value of abs of cwg
    ridgesep = 0.2
    xmin = -100
    xmax = 100

    ### first do kde for overall partnership
    if (use_all_nonpartners and len(nonpartners) > 30) or (not use_all_nonpartners and len(partners) > 30):
        avg_gap = 2#4
    elif (use_all_nonpartners and len(nonpartners) > 15) or (not use_all_nonpartners and len(partners) > 15):
        avg_gap = 2
    else:
        avg_gap = 1

    ax3.axhline(avg_gap * ridgesep, color='0.8', zorder=1, lw=1)
    c = f'overall_cwg_np'
    kde_scaler = 70/40
    kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
    kde_district.fit(bw=bw * kde_scaler)
    x = np.arange(xmin, xmax, 0.1)
    y = []
    for xx in x:
        yy = kde_district.evaluate(xx) * kde_scaler
        if np.isnan(yy):
            y.append(0.)
        else:
            y.append(yy[0])
    y = np.array(y)
    color = '0.2'
    ax3.fill_between(x, y + avg_gap * ridgesep, avg_gap * ridgesep, where=(y > 0.00005), lw=0.5, alpha=alpha,
                     zorder=2, fc=color, ec='k')

    ### now repeat for individual non-partners, ordering by exp val of abs val of cwg
    expvalabs = []
    for i, d in enumerate(nonpartners):
        ### evaluate & plot kde
        c = f'{d}_cwg'
        kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
        kde_district.fit(bw=bw * kde_scaler)
        x = np.arange(xmin, xmax, 0.1)
        y = []
        for xx in x:
            yy = kde_district.evaluate(xx) * kde_scaler
            if np.isnan(yy):
                y.append(0.)
            else:
                y.append(yy[0])
        y = np.array(y)
        expvalabs.append((abs(x) * y).sum() * (x[1] - x[0]))

    ### reorder by expected value of CWG
    expvalabs = np.array(expvalabs)
    order = np.argsort(expvalabs)
    nonpartners = [nonpartners[o] for o in order]
    nonpartners = [nonpartners[-o] for o in range(1, len(nonpartners) + 1)]

    if not use_all_nonpartners:
        nonpartners = nonpartners[:len(partners)]

    ### now create ridgeplot with nonpartners ordered by epected value of abs of cwg, only take first 9 to line up with other plots
    xlim = [0, 0]
    for i, d in enumerate(nonpartners):

        ### set bottom of "ridge" in decreasing order (smallest share at bottom)
        bottom = (-i * ridgesep)
        ax3.axhline(bottom, color='0.8', zorder=1, lw=1)

        ### evaluate & plot kde
        c = f'{d}_cwg'
        kde_district = sm.nonparametric.KDEUnivariate(df_mc[c])
        kde_district.fit(bw=bw * kde_scaler)
        x = np.arange(xmin, xmax, 0.1)
        y = []
        for xx in x:
            yy = kde_district.evaluate(xx) * kde_scaler
            if np.isnan(yy):
                y.append(0.)
            else:
                y.append(yy[0])
        y = np.array(y)
        color = '0.7'
        ax3.fill_between(x, y + bottom, bottom, where=(y > 0.00005), lw=0.5, alpha=alpha, zorder=2, fc=color,
                         ec='k')
        xlim = [min(xlim[0], x[y > 0.00005][0]), max(xlim[1], x[y > 0.00005][-1])]

    ax3.set_yticks([avg_gap * ridgesep] + [-i * ridgesep for i in range(len(nonpartners)) if i % avg_gap == 0],
                   ['All'] + [str(i + 1) for i in range(len(nonpartners)) if i % avg_gap == 0])

    ax3.set_ylabel('Non-Partners')
    ax3.set_xlabel('Captured water gain (GL/year)', fontsize=fontsize)
    ax3.spines[['top', 'left', 'right']].set_visible(False)
    ax3.xaxis.set_major_locator(MultipleLocator(20))
    ax3.xaxis.set_minor_locator(MultipleLocator(5))

    xlim = [min(xlim[0] - 5, -20), max(xlim[1] + 5, 20)]
    ax3.set_xlim(xlim)

    ### adjust ylims so that first 2 have equally spaced lines
    if not use_all_nonpartners:
        ylim0 = ax0.get_ylim()
        ylim1 = ax1.get_ylim()
        ylim3 = ax3.get_ylim()
        ylim0_new = [min(ylim0[0], ylim1[0], ylim3[0]), max(ylim0[1], ylim1[1], ylim3[1])]
        ylim1_new = ylim0_new
        ylim3_new = ylim0_new
        ax0.set_ylim(ylim0_new)
        ax1.set_ylim(ylim1_new)
        ax3.set_ylim(ylim3_new)
    else:
        ylim0 = ax0.get_ylim()
        ylim1 = ax1.get_ylim()
        ylim0_new = [min(ylim0[0], ylim1[0]), max(ylim0[1], ylim1[1])]
        ylim1_new = ylim0_new
        ax0.set_ylim(ylim0_new)
        ax1.set_ylim(ylim1_new)

    # ### label subfigs
    ax0.annotate(labels[0], (0.05, 0.93), xycoords='subfigure fraction', ha='left', va='top', fontsize=fontsize + 2,
                 weight='bold')
    ax1.annotate(labels[1], (0.05, 0.53), xycoords='subfigure fraction', ha='left', va='top', fontsize=fontsize + 2,
                 weight='bold')
    ax3.annotate(labels[2], (0.535, 0.93), xycoords='subfigure fraction', ha='left', va='top',
                 fontsize=fontsize + 2, weight='bold')

    ## add colorbar
    ax4 = fig.add_subplot(gs[2, :])
    ax4.spines[['top', 'left', 'right', 'bottom']].set_visible(False)
    ax4.set_xticks([])
    ax4.set_yticks([])
    cb = plt.colorbar(shares_cmap_mappable_even, ax=ax4, ticks=[1 / 12, 3 / 12, 5 / 12, 7 / 12, 9 / 12, 11 / 12], shrink=0.5,
                      fraction=1,
                      orientation='horizontal', anchor=(0.5, 0.5))
    _ = cb.ax.set_xticklabels(['0', '1-3', '3-7', '7-15', '15-30', '30+', ], fontsize=fontsize)
    _ = cb.set_label('Ownership share (%)', fontsize=fontsize)  # , labelpad=10)

    plt.savefig(f"{fig_dir}partners_{soln_label.replace('/','-')}_disagg_pdfs.png", bbox_inches='tight', dpi=dpi)
    plt.savefig(f"{fig_dir}partners_{soln_label.replace('/','-')}_disagg_pdfs.pdf", bbox_inches='tight')



### get ownership share for a particular district in a particular solution (results_soln should only have one row)
def get_share(d, results_soln):
    try:
        share = results_soln['share_' + d].iloc[0]
    except:
        share = 0
    return share


### five-part figure showing structure of partnerships in optimal tradeoff set
def plot_share_distributions_bivariateChoropleth(results, water_providers, states, canals_fkc, canals_other,
                                                 tlb, sjr, kings, res_gdf):
    ### 5-part figure with bivariate map etc
    fontsize = 10
    labels = ('a)', 'b)', 'c)', 'd)', 'e)')
    nonpartnercolor = 'w'
    alpha = 1


    fig, ax = plt.subplots(1, 1, figsize=(10, 5))  # , gridspec_kw={'width_ratios': [0.75,0.25], 'wspace':0.3})

    ### fraction of optimal tradeoff partnerships that a district is included in
    def get_inclusion_frac(d, df_solutions):
        try:
            frac = np.mean(df_solutions['share_' + d] > 0)
        except:
            frac = 0
        return frac

    water_providers['inclusion_frac'] = [get_inclusion_frac(d, results) for d in water_providers['district']]

    ### median share when included
    def get_median_share(d, df_solutions):
        try:
            share = np.median(df_solutions['share_' + d].loc[df_solutions['share_' + d] > 0])
        except:
            share = 0
        return share

    water_providers['median_share'] = [get_median_share(d, results) for d in water_providers['district']]

    ### bivariate color palette representing the fraction of optimal tradeoff parterships a water provider
    ### participates in, as well as its median share within those partnerships
    share_bounds = [0.02, 0.04, 0.08, 0.16]
    inclusion_bounds = [0.25, 0.5, 0.75, 1]
    hex_color_corners, colorlist = get_bivariate_colorlist(len(share_bounds))
    def get_bivariate_choropleth_color(district, inclusion_frac, median_share):
        d = 'share_' + district
        try:
            count = 0
            for inclusion_bound in inclusion_bounds:
                for share_bound in share_bounds:
                    if inclusion_frac == 0:
                        return nonpartnercolor
                    if inclusion_frac <= inclusion_bound:
                        if median_share <= share_bound:
                            return colorlist[count]
                    count += 1
        except:
            return nonpartnercolor
    water_providers['color_bivariate'] = [get_bivariate_choropleth_color(d,
                                            water_providers['inclusion_frac'].loc[water_providers['district'] == d].values[0],
                                            water_providers['median_share'].loc[water_providers['district'] == d].values[0])
                                          for d in water_providers['district']]

    ### first plot districts with zero participation, with no color but outlined in black, except COF & TUL & ID4
    condition = np.logical_and(water_providers['color_bivariate'] == nonpartnercolor,
                               [d not in ('COF', 'TUL', 'ID4') for d in water_providers['district']])
    water_providers.loc[condition, :].plot('color_bivariate', ax=ax, color=nonpartnercolor, edgecolor='k', lw=0.5,
                                           legend=True, alpha=alpha, zorder=1)
    ### now plot districts with non-zero participation, except COF & TUL & ID4
    condition = np.logical_and(water_providers['color_bivariate'] != nonpartnercolor,
                               [d not in ('COF', 'TUL', 'ID4') for d in water_providers['district']])
    water_providers.loc[condition, :].plot('color_bivariate', ax=ax, color=water_providers.loc[condition, 'color_bivariate'],
                                           edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1)
    ### now plot COF & TUL, which are overlapping and need to be on top
    condition = [d in ('COF', 'TUL') for d in water_providers['district']]
    water_providers.loc[condition, :].plot('color_bivariate', ax=ax, color=water_providers.loc[condition, 'color_bivariate'],
                                           edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1)

    ### axes
    xlim = [1.68e6, 2.21e6]
    xrange = xlim[1] - xlim[0]
    ylim = [4.3e5, 7.22e5]
    yrange = ylim[1] - ylim[0]

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[['top', 'left', 'right', 'bottom']].set_visible(False)

    ### lastly add separate inset for ID4 due to overlapping. make sure scale is same as original
    xfrac = 0.065
    yfrac = 0.115
    axin = ax.inset_axes([0.38, 0.1, xfrac, yfrac])
    xstart = 1.98e6
    ystart = 4.865e5
    axin.set_xlim([xstart, xstart + xfrac * xrange])
    axin.set_ylim([ystart, ystart + yfrac * yrange])
    water_providers.loc[water_providers['district'] == 'ID4'].plot('color_bivariate',
                                           color=water_providers.loc[water_providers['district'] == 'ID4', 'color_bivariate'],
                                           edgecolor='k', lw=0.5, alpha=alpha, legend=True, zorder=1, ax=axin)
    axin.set_xticks([])
    axin.set_yticks([])
    axin.spines[['top', 'left', 'right', 'bottom']].set_edgecolor('0.5')

    ### now add rectangle back in original axes with arrow
    box = [Rectangle((xstart, ystart), xfrac * xrange, yfrac * yrange)]
    pc = PatchCollection(box, facecolor='none', edgecolor='0.5')
    ax.add_collection(pc)
    ax.arrow(xlim[0] + (0.38 + xfrac) * xrange, ylim[0] + (0.1 + yfrac * 0.5) * yrange,
             xstart - (xlim[0] + (0.38 + xfrac) * xrange),
             ystart - (ylim[0] + (0.1) * yrange),
             color='0.5', lw=1, head_width=3e3, length_includes_head=True, zorder=5)

    ### add color grid legend
    # ax = axs[1]
    axin2 = ax.inset_axes([0.76, 0.1, 0.24, 0.34])
    axin2.set_aspect('equal', adjustable='box')
    count = 0
    for i, inclusion_bound in enumerate(inclusion_bounds):
        for j, share_bound in enumerate(share_bounds):
            shareboxes = [Rectangle((i, j), 1, 1)]
            pc = PatchCollection(shareboxes, facecolor=colorlist[count], alpha=alpha)
            count += 1
            axin2.add_collection(pc)
    _ = axin2.set_xlim([0, len(share_bounds)])
    _ = axin2.set_ylim([0, len(inclusion_bounds)])
    _ = axin2.set_xticks(list(np.arange(0, len(inclusion_bounds) + 1)), [0] + [int(b * 100) for b in inclusion_bounds],
                         fontsize=fontsize)
    _ = axin2.set_xlabel('Partnership inclusion (%)', fontsize=fontsize)
    _ = axin2.set_yticks(list(np.arange(0, len(share_bounds) + 1)), [1] + [int(b * 100) for b in share_bounds],
                         fontsize=fontsize)
    _ = axin2.set_ylabel(f'Median ownership\nshare (%)', fontsize=fontsize, labelpad=2)

    ### add exceedance plots for ownership shares
    axin3 = ax.inset_axes([0.7, 0.63, 0.29, 0.36])
    x = np.linspace(0, 100, results.shape[0])
    for d in water_providers['district']:
        try:
            shares_d = results[f'share_{d}'] * 100
            shares_sort = shares_d.sort_values().values
            inclusion_frac = get_inclusion_frac(d, results)
            median_share = get_median_share(d, results)
            bivariate_color = get_bivariate_choropleth_color(d, inclusion_frac, median_share)
            axin3.plot(x, shares_sort, color='k', alpha=alpha, zorder=-int(300 * median_share + 100 * inclusion_frac),
                       lw=2.5)
            axin3.plot(x, shares_sort, color=bivariate_color, alpha=alpha,
                       zorder=-int(300 * median_share + 100 * inclusion_frac), lw=2)
        except:
            pass

    _ = axin3.set_xlim([-2, 102])
    _ = axin3.set_ylim([1, 32])
    _ = axin3.semilogy()
    _ = axin3.set_xticks(range(0, 101, 25), range(0, 101, 25), fontsize=fontsize)
    _ = axin3.set_yticks([1, 2, 4, 8, 16, 32], [1, 2, 4, 8, 16, 32], fontsize=fontsize)
    _ = axin3.set_xlabel('Non-Exceedance (%)', fontsize=fontsize)
    _ = axin3.set_ylabel('Ownership\nshare (%)', fontsize=fontsize)
    _ = axin3.patch.set_alpha(0.)

    ### add distribution of project type by n_p
    axin4 = ax.inset_axes([0.02, 0.65, 0.27, 0.34])
    for proj in range(1,4):
        print(f'Num partnerships with proj={proj}: {(results["proj"]==proj).mean()*100}%')
    for i in range(11, 27):
        subresults = results.loc[results['n_p'] == i]
        print(f'Num partnerships <= {i} partners: {(results["n_p"] <= i).mean()*100}%')
        count = 0
        for proj in range(3, 0, -1):
            newcount = (subresults['proj'] == proj).sum()
            axin4.add_collection(PatchCollection([Rectangle((i - 0.4, count), 0.8, newcount)],
                                                 facecolor=cols_cbrewer[proj - 1]))
            count += newcount
    axin4.set_xlim([10, 27])
    axin4.set_ylim([0, 40])
    _ = axin4.set_xticks(range(11, 27, 3), range(11, 27, 3), fontsize=fontsize)
    _ = axin4.set_xlabel('Number of partners', fontsize=fontsize)
    _ = axin4.set_ylabel('Number of\npartnerships', fontsize=fontsize)
    leg = [Patch(color=cols_cbrewer[0], label='Canal'),
           Patch(color=cols_cbrewer[1], label='Bank'),
           Patch(color=cols_cbrewer[2], label='Both')]
    _ = axin4.legend(handles=leg, loc='center', bbox_to_anchor=[0.8, 0.75], ncol=1, frameon=False, fontsize=fontsize,
                     handlelength=0.8)

    ### gini-type plot of cumulative partners vs partnerships
    axin5 = ax.inset_axes([0.01, 0.1, 0.24, 0.37])
    axin5.set_aspect('equal')
    alpha = 0.7
    for count, soln_label in enumerate(results['label']):
        results_soln = results.loc[results['label'] == soln_label]
        color = cmap_vir((results_soln['n_p'].iloc[0] - 11) / (26-11))
        partner_shares = [0] + [get_share(d, results_soln) for d in water_providers['district']
                                if get_share(d, results_soln) > 0]
        partner_shares = np.sort(partner_shares)
        partners_cum_norm = np.arange(0, len(partner_shares)) / (len(partner_shares) - 1) * 100
        shares_cum_norm = np.cumsum(np.array(partner_shares)) * 100
        axin5.plot(partners_cum_norm, shares_cum_norm, color=color, alpha=alpha, zorder=np.random.choice([1, 2, 3]))
        axin5.set_xlabel('Cumulative partners (%)', fontsize=fontsize)
        axin5.set_ylabel('Cumulative\nownership (%)', fontsize=fontsize)
        axin5.set_xticks(range(0, 101, 25), range(0, 101, 25), fontsize=fontsize)
        axin5.set_yticks(range(0, 101, 25), range(0, 101, 25), fontsize=fontsize)

    ### create colorbar
    axin6 = fig.add_axes([0.295, 0.23, 0.05, 0.22])
    axin6.patch.set_alpha(0)
    axin6.set_xticks([])
    axin6.set_yticks([])
    axin6.spines[['top', 'left', 'right', 'bottom']].set_visible(False)
    mappable = cm.ScalarMappable(cmap='viridis')
    mappable.set_clim(vmin=11, vmax=26)
    cb = plt.colorbar(mappable, ax=axin6, orientation='vertical', shrink=1, label='Number of partners', alpha=0.9,
                      aspect=12)
    _ = cb.ax.set_yticks([11, 16, 21, 26], [11, 16, 21, 26], fontsize=fontsize)

    ### label subplots
    ax.annotate(labels[0], (0.06, 0.8), ha='left', va='top', fontsize=fontsize + 2, weight='bold',
                xycoords='figure fraction')
    ax.annotate(labels[1], (0.06, 0.4), ha='left', va='top', fontsize=fontsize + 2, weight='bold',
                xycoords='figure fraction')
    ax.annotate(labels[2], (0.34, 0.8), ha='left', va='top', fontsize=fontsize + 2, weight='bold',
                xycoords='figure fraction')
    ax.annotate(labels[3], (0.53, 0.8), ha='left', va='top', fontsize=fontsize + 2, weight='bold',
                xycoords='figure fraction')
    ax.annotate(labels[4], (0.57, 0.4), ha='left', va='top', fontsize=fontsize + 2, weight='bold',
                xycoords='figure fraction')

    plt.savefig(f'{fig_dir}share_distributions_bivariateChloropleth.png',
                bbox_inches='tight', dpi=dpi)
    plt.savefig(f'{fig_dir}share_distributions_bivariateChloropleth.pdf',
                bbox_inches='tight')




### plot ownership share concentration, colored by num partners and by project type
def plot_ownership_share_concentrations(results, water_providers):
    ### cumulative ownership plot for groundwater banks vs both projects, then separated by size classes
    fig, axs = plt.subplots(1, 2, figsize=(9, 4))
    alpha = 0.9
    ax = axs[1]
    ax.set_aspect('equal')
    for count, soln_label in enumerate(results['label']):
        results_soln = results.loc[results['label'] == soln_label]
        proj = int(results_soln['proj'].iloc[0])
        color = cols_cbrewer[proj - 1]
        partner_shares = [0] + [get_share(d, results_soln) for d in water_providers['district']
                                if get_share(d, results_soln) > 0]
        partner_shares = np.sort(partner_shares)
        partners_cum_norm = np.arange(0, len(partner_shares)) / (len(partner_shares) - 1) * 100
        shares_cum_norm = np.cumsum(np.array(partner_shares)) * 100
        ax.plot(partners_cum_norm, shares_cum_norm, color=color, alpha=alpha, zorder=np.random.choice([1,2,3]),
                lw=3)
        ax.set_xlabel('Cumulative partners (%)', fontsize=fontsize)
        ax.set_ylabel('Cumulative ownership (%)', fontsize=fontsize)
        ax.set_xticks(range(0, 101, 25), range(0, 101, 25), fontsize=fontsize)
        ax.set_yticks(range(0, 101, 25), range(0, 101, 25), fontsize=fontsize)
    leg = [Line2D([0], [0], color=cols_cbrewer[0], label='Canal', lw=3),
           Line2D([0], [0], color=cols_cbrewer[1], label='Bank', lw=3),
           Line2D([0], [0], color=cols_cbrewer[2], label='Both', lw=3)]
    _ = ax.legend(handles=leg, loc='upper left', bbox_to_anchor=[0.05, 0.95], ncol=1, frameon=False, fontsize=fontsize,
                  handlelength=0.8)

    ax = axs[0]
    ax.set_aspect('equal')
    for count, soln_label in enumerate(results['label']):
        results_soln = results.loc[results['label'] == soln_label]
        c = int(results_soln['n_p'].iloc[0] > 15) + int(results_soln['n_p'].iloc[0] > 20)
        color = cols_cbrewer[c]
        partner_shares = [0] + [get_share(d, results_soln) for d in water_providers['district']
                                if get_share(d, results_soln) > 0]
        partner_shares = np.sort(partner_shares)
        partners_cum_norm = np.arange(0, len(partner_shares)) / (len(partner_shares) - 1) * 100
        shares_cum_norm = np.cumsum(np.array(partner_shares)) * 100
        ax.plot(partners_cum_norm, shares_cum_norm, color=color, alpha=alpha, zorder=np.random.choice([1,2,3]), lw=3)
        ax.set_xlabel('Cumulative partners (%)', fontsize=fontsize)
        ax.set_ylabel('Cumulative ownership (%)', fontsize=fontsize)
        ax.set_xticks(range(0, 101, 25), range(0, 101, 25), fontsize=fontsize)
        ax.set_yticks(range(0, 101, 25), range(0, 101, 25), fontsize=fontsize)
    leg = [Line2D([0], [0], color=cols_cbrewer[0], label='11-15 partners', lw=3),
           Line2D([0], [0], color=cols_cbrewer[1], label='16-20 partners', lw=3),
           Line2D([0], [0], color=cols_cbrewer[2], label='21-26 partners', lw=3)]
    _ = ax.legend(handles=leg, loc='upper left', bbox_to_anchor=[0.05, 0.95], ncol=1, frameon=False, fontsize=fontsize,
                  handlelength=0.8)

    plt.savefig(f'{fig_dir}share_concentration_byNumAndProj.png', bbox_inches='tight', dpi=dpi)
    plt.savefig(f'{fig_dir}share_concentration_byNumAndProj.pdf', bbox_inches='tight')




### figure showing evolution of metrics (e.g., hypervolume) across seeds during multiobjective optimization step
def plot_moo_metrics():
    dvs = [2,2,2,2,2,2,2,2,2]
    seeds = [1,1,2,3,4,1,2,3,4]
    rounds = [1,1,1,1,1,2,2,2,2]
    nfes = [3100,42401,40400,42200,41500,73702, 74001, 75901, 76001]
    results_dir = '../../results/MOO_results_bridges2/'
    subdirs = ['dv2_seed1_round1a', 'dv2_seed1_round1b', 'dv2_seed2_round1', 'dv2_seed3_round1', 'dv2_seed4_round1',
               'dv2_seed1_round2', 'dv2_seed2_round2', 'dv2_seed3_round2', 'dv2_seed4_round2']
    ### read in operators data
    operators = []
    for i in range(len(dvs)):
        dv = dvs[i]
        seed = seeds[i]
        r = rounds[i]
        nfe = nfes[i]
        metrics_dir = f'{results_dir}/{subdirs[i]}/operators/'
        NFE_file = f'{metrics_dir}/dv{dv}_s{seed}_nfe{nfe}.NFE'
        df = pd.read_csv(NFE_file, sep=' ', header=None)
        for o in ['DE', 'PCX', 'SBX', 'SPX', 'UM', 'UNDX']:
            df[o] = pd.read_csv(f'{metrics_dir}/dv{dv}_s{seed}_nfe{nfe}.{o}', sep=' ', header=None)[0].values
        df.index = df[0]
        df = df.iloc[:, 1:]
        ncols = df.shape[1]
        cols = df.columns
        operators.append(df)

    ### read in metrics data
    metrics = []
    for i in range(len(dvs)):
        dv = dvs[i]
        seed = seeds[i]
        r = rounds[i]
        nfe = nfes[i]
        metrics_dir = f'{results_dir}/{subdirs[i]}/metrics/'
        df = pd.read_csv(f'{metrics_dir}/dv{dv}_s{seed}_nfe{nfe}.metrics', sep=' ')
        df.index = operators[i].index[-df.shape[0]:]
        df.columns = ['Hypervolume', 'Generational distance', 'Inverted generational distance', 'Spacing',
                      'Epsilon indicator', 'Maximum Pareto front error']
        ncols = df.shape[1]
        cols = df.columns
        metrics.append(df)

    ### plot runtime metrics
    colors = ['firebrick', 'firebrick', 'cornflowerblue', 'darkgoldenrod', 'indigo', 'firebrick', 'cornflowerblue', 'darkgoldenrod', 'indigo']
    cols = ['Hypervolume', 'Inverted generational distance', 'Epsilon indicator']
    labels = ['Hypervolume', 'Inverted\ngenerational\ndistance', 'Epsilon\nindicator']
    fig, axs = plt.subplots(3, 1, figsize=(8, 6))
    j = 0
    k = 0
    for c, col in enumerate(cols):
        ax = axs[c]
        for i in range(len(dvs)):
            ax.plot(metrics[i][col].index / 1000, metrics[i][col], color=colors[i], 
                    label=f"Seed {seeds[i]}" if rounds[i]==2 else "")
        ax.set_ylabel(labels[c], fontsize=fontsize)
        if c==1:
            ax.legend(frameon=False)
    ax.set_xlabel('Thousand function evaluations', fontsize=fontsize)

    plt.savefig(f'{fig_dir}moo_metrics.png', bbox_inches='tight', dpi=dpi)
    plt.savefig(f'{fig_dir}moo_metrics.pdf', bbox_inches='tight')


    ### plot operators
    cols =  ['DE', 'PCX', 'SBX', 'SPX', 'UM', 'UNDX']
    labels =  ['DE', 'PCX', 'SBX', 'SPX', 'UM', 'UNDX']
    fig, axs = plt.subplots(3, 2, figsize=(8, 6), gridspec_kw={'wspace':0.3})
    for c, col in enumerate(cols):
        j = c%2
        k = int(c/2)
        ax = axs[k,j]
        for i in range(len(dvs)):
            ax.plot(operators[i][col].index / 1000, operators[i][col], color=colors[i])
        ax.set_ylabel(labels[c], fontsize=fontsize)
        if k==2 and j==0:
            ax.set_xlabel('Thousand function evaluations', fontsize=fontsize)

    plt.savefig(f'{fig_dir}moo_operators.png', bbox_inches='tight', dpi=dpi)
    plt.savefig(f'{fig_dir}moo_operators.pdf', bbox_inches='tight')
