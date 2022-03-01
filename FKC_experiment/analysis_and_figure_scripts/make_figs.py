### Analyze data on objectives from exploratory experiment, create figures from paper

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm, rcParams
from matplotlib.patches import Patch
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import json
import seaborn as sns
import math

fig_dir = '../figures/'
results_dir = '../output_data/'

print('Begin analyzing output data')

### I am running from WSL (Ubuntu within WIndows), and need to add font location. If not WSL, this should get ignored
from platform import uname
if 'Microsoft' in uname().release:
  import matplotlib.font_manager as font_manager
  font_dirs = ['/mnt/c/Windows/Fonts/', ]
  font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
  for font_file in font_files:
    font_list = font_manager.fontManager.addfont(font_file)

### set default font type/size
rcParams['font.family'] = 'Arial'
rcParams.update({'font.size': 8})

### get results from exploratory experiment
results = pd.read_csv(results_dir + 'objs_clean.csv')
### remove extra samples
results['samp_num'] = -1
results.samp_num[:-6] = pd.to_numeric(results.samp[:-6])
results = results.loc[results.samp_num < 3000]
results.reset_index(inplace=True, drop=True)

### get subsets of columns
districts = [d.split('_')[0] for d in results.columns if 'w5yr_gain' in d.split('_',1)]
share_keys = [d + '_share' for d in districts]
exp_gain_keys = [d + '_exp_gain' for d in districts]
w5yr_gain_keys = [d + '_w5yr_gain' for d in districts]
avg_price_keys = [d + '_avg_price' for d in districts]
objs_keys = ['total_partner_avg_gain', 'min_partner_avg_gain','total_other_avg_gain', 'min_other_avg_gain', 'total_partner_w5yr_gain', \
             'min_partner_w5yr_gain', 'ginicoef', 'avg_price_gain_dolAF']

### convert results to SI units 
gain_conversion = 0.00123*1000  ## convert kAF to million cubic meters (GL)

results['total_partner_avg_gain'] *= gain_conversion
results['min_partner_avg_gain'] *= gain_conversion
results['total_other_avg_gain'] *= gain_conversion
results['min_other_avg_gain'] *= gain_conversion
results['total_partner_w5yr_gain'] *= gain_conversion
results['min_partner_w5yr_gain'] *= gain_conversion
for d in districts:
    results[d + '_exp_gain'] *= gain_conversion

### recalculate costs based on new Friant-Kern Canal agreement 
### this reduced the cost share by partners, relative to numbers in original objective calculation script. 
### Also reduce estimated CFWB cost for simpler comparison.
FKC_participant_payment = 50e6
CFWB_cost = 50e6
interest_annual = 0.03
time_horizon = 50
cap = 1000

principle = {'FKC': FKC_participant_payment, 'CFWB': CFWB_cost, 'FKC_CFWB': FKC_participant_payment + CFWB_cost}
payments_per_yr = 1
interest_rt = interest_annual / payments_per_yr
num_payments = time_horizon * payments_per_yr
annual_payment = {k: principle[k] / (((1 + interest_rt) ** num_payments - 1) / (interest_rt * (1 + interest_rt) ** num_payments)) for k in principle}

results['annual_payment'] = [annual_payment[p] for p in results['project']]
results['avg_price_gain_dolAF'] = results['annual_payment'] / results['total_partner_avg_gain'] / 1000
results['avg_price_gain_dolAF'].loc[np.logical_or(results['avg_price_gain_dolAF'] < 0, results['avg_price_gain_dolAF'] > cap)] = cap
for d in districts:
    results[d + '_avg_price'] = results['annual_payment'] * results[d + '_share'] / results[d + '_exp_gain'] / 1000
    results[d + '_avg_price'].loc[np.logical_or(results[d + '_avg_price'] < 0, results[d + '_avg_price'] > cap)] = cap
results['worst_price_avg_gain'] = np.max(results.loc[:,avg_price_keys], axis=1)


## color & marker by hydro/project
pal_zissou1_5 = ["#3B9AB2", "#78B7C5", "#EBCC2A", "#E1AF00", "#F21A00"]
pal_cb = ['#7570b3', '#1b9e77', '#d95f02']

projects = ['FKC','CFWB','FKC_CFWB']
hydros = ['dry','median','wet']
cdict_hydro = {'wet': pal_zissou1_5[0], 'median': pal_zissou1_5[2], 'dry': pal_zissou1_5[4]}
mdict_project = {'FKC': 's', 'FKC_CFWB':'v', 'CFWB': 'o'}
ldict_project = {'FKC': 'Canal', 'FKC_CFWB':'Both', 'CFWB': 'Bank'}
ldict_hydro = {'wet': 'Wet', 'median': 'Avg', 'dry': 'Dry'}
results['c_hydro'] = [cdict_hydro[i] for i in results.hydro]
results['m_project'] = [mdict_project[i] for i in results.project]

varnames = ['total_partner_avg_gain', 'total_partner_w5yr_gain', 'total_other_avg_gain',
        'avg_price_gain_dolAF', 'worst_price_avg_gain', 'ginicoef', 'num_partners','initial_recharge', 'tot_storage',
       'recovery']

print()


# ######################################################
# ### figures 6, S3, S4
# ######################################################

def make_satisfice_fig(figname, ylabel, row, col, maximizing, inset_lims_1, leg_proj_anchor, leg_hydro_anchor, y, y_base):
  fig,ax = plt.subplots(1,1,figsize=(7.45,3.25))

  x = results[varnames[col]]
  c = results['c_hydro']
  m = results['m_project']

  x_base = 200

  if maximizing:
      satisfice = np.logical_and(x <= x_base, y >= y_base)
  else:
      satisfice = np.logical_and(x <= x_base, y <= y_base)
      
  ## trick for separate markers from https://stackoverflow.com/questions/52303660/iterating-markers-in-plots/52303895#52303895
  def mscatter(x,y,ax=None, m=None, **kw):
      import matplotlib.markers as mmarkers
      if not ax: ax=plt.gca()
      sc = ax.scatter(x,y,**kw)
      if (m is not None) and (len(m)==len(x)):
          paths = []
          for marker in m:
              if isinstance(marker, mmarkers.MarkerStyle):
                  marker_obj = marker
              else:
                  marker_obj = mmarkers.MarkerStyle(marker)
              path = marker_obj.get_path().transformed(
                          marker_obj.get_transform())
              paths.append(path)
          sc.set_paths(paths)
      return sc

  mscatter(x.loc[np.logical_not(satisfice)], y.loc[np.logical_not(satisfice)], ax=ax, c=c.loc[np.logical_not(satisfice)], 
          m=m.loc[np.logical_not(satisfice)], alpha=0.3, edgecolor='w', zorder=2)
  mscatter(x.loc[satisfice], y.loc[satisfice], ax=ax, c=c.loc[satisfice], m=m.loc[satisfice], alpha=0.8, edgecolor='k', zorder=2)

  ylim = ax.get_ylim()
  xlim = ax.get_xlim()


  # ax.set_xlim([xlim[0], xlim[1] + (xlim[1] - xlim[0]) * 0.1])
  ax.set_xlim([0,1021])
  ax.set_xticks(np.arange(0,1001,200))
  ax.set_xticklabels(['0','200','400','600','800','1000+'])
  if figname == 'wpcost_pcost':
      ax.set_ylim([0,1061])
      ax.set_yticks(np.arange(0,1001,200))
      ax.set_yticklabels(['0','200','400','600','800','1000+'])
  elif figname == 'wpcost_pcwg':
      ax.set_ylim(ylim)
  elif figname in ['wpcost_pddg']:
      ax.set_ylim([-300,175])
  elif figname in ['wpcost_npcwg']:
      ax.set_ylim([-300,175])
  elif figname == 'wpcost_pnum':
      ax.set_ylim([-30,22])
  else:
      ax.set_ylim(ylim)    

      
  if maximizing:
      ax.plot([x_base, x_base], [y_base, ax.get_ylim()[1]],lw=2,c='k', zorder=1)
  else:
      ax.plot([x_base, x_base], [ax.get_ylim()[0], y_base],lw=2,c='k',zorder=1)
  ax.plot([ax.get_xlim()[0], x_base], [y_base, y_base],lw=2, c='k', zorder=1) 
  ax.set_xlabel('Cost of gains for worst-off partner ($/ML)')
  ax.set_ylabel(ylabel)

  ### inset with satisficing color table
  axins1 = ax.inset_axes(inset_lims_1)
  axins1.patch.set_alpha(0)

  def get_satisfice_perc(is_subset):
          if maximizing:
              satisfice = np.logical_and(x.loc[is_subset] <= x_base, y.loc[is_subset] >= y_base)
          else:
              satisfice = np.logical_and(x.loc[is_subset] <= x_base, y.loc[is_subset] <= y_base)
          return satisfice.mean()*100
      
  percs = []
  colors = []
  pos = []
  for pi,p in enumerate([projects[i] for i in [2,1,0]]):
      for hi,h in enumerate([hydros[i] for i in [2,1,0]]):
          percs.append(get_satisfice_perc(np.logical_and(results['hydro'] == h, results['project'] == p)))
      percs.append(get_satisfice_perc(results['project'] == p))
  for hi,h in enumerate([hydros[i] for i in [2,1,0]]):
      percs.append(get_satisfice_perc(results['hydro'] == h))
  percs.append(get_satisfice_perc(np.logical_or(results['project'] == p, results['project'] != p)))

  ### now plot patches with percentages
  offset = 0.5
  cmap_satisfice = cm.get_cmap('PiYG')
  rownames = ['Both', 'Bank', 'Canal','All\nprojects']
  colnames = ['Wet', 'Avg.', 'Dry', 'All\nhydrology']

  def get_color_satisfice(cmap, sat_perc, max_sat, min_sat):
      sat_norm = (sat_perc - min_sat) / (max_sat - min_sat)
      return cmap(sat_norm)

  for r in range(4):
      if r == 3:
          row_offset = offset
      else:
          row_offset = 0
      for c in range(4):
          if c == 3:
              col_offset = offset
          else:
              col_offset = 0
          xy = np.zeros((5,2))
          xy[0,] = (row_offset + r, col_offset + c)
          xy[1,] = (row_offset + r, col_offset + c+1)
          xy[2,] = (row_offset + r+1, col_offset + c+1)
          xy[3,] = (row_offset + r+1, col_offset + c)
          xy[4,] = (row_offset + r, col_offset + c)

          path = mpath.Path(xy)
          color = get_color_satisfice(cmap_satisfice, percs[r + c*4], 21, 0)
          patch = mpatches.PathPatch(path, facecolor=color, edgecolor='k', alpha=0.7)
          axins1.add_patch(patch)
          axins1.annotate(str(round(percs[r + c*4],1)) + '%', (xy[:-1,0].mean(), xy[:-1,1].mean()), va='center', ha='center', fontsize=6)
          
          if r == 0:
              axins1.annotate(colnames[c], (c+0.5 + col_offset, -0.8), va='center', ha='center', ma='center', zorder=2)
      
      axins1.annotate(rownames[r], (-1, r+0.5 + row_offset), va='center', ha='center', ma='center', zorder=2)


  axins1.set_xlim([-1., 4.5])
  axins1.set_ylim([-2.7, 4.5])

  cb = plt.colorbar(mappable = cm.ScalarMappable(cmap = cmap_satisfice, norm = Normalize(vmin=0, vmax=21)), 
                      ax=axins1, shrink=0.7, orientation='horizontal')
  cb.ax.tick_params(pad=1)
  cb.set_label('Percent viable', labelpad=0)


  axins1.set_xticks([])
  axins1.set_yticks([])
  for spine in ['top','right','left','bottom']:
      axins1.spines[spine].set_visible(False)

  leg_hydro = [Patch(facecolor=cdict_hydro['dry'], label='Dry'),
              Patch(facecolor=cdict_hydro['median'], label='Avg.'),
              Patch(facecolor=cdict_hydro['wet'], label='Wet')]
  leg1 = axins1.legend(handles=leg_hydro, loc='center', bbox_to_anchor=leg_hydro_anchor, title='Hydrology', frameon=False)
  leg1.get_title().set_ma('center')

  leg_proj = [Line2D([0],[0], color='0.5', lw=0, marker=mdict_project['FKC'], label='Canal'),
              Line2D([0],[0], color='0.5', lw=0, marker=mdict_project['CFWB'], label='Bank'),
              Line2D([0],[0], color='0.5', lw=0, marker=mdict_project['FKC_CFWB'], label='Both'),]
  leg1 = ax.legend(handles=leg_proj, loc='center', bbox_to_anchor=leg_proj_anchor, title='Project type', frameon=False)
  leg1.get_title().set_ma('center')

  plt.savefig(fig_dir + 'satisfice_' + figname + '.png', bbox_inches='tight', dpi=300)



### fig 6: WP_cost vs P_cost
print('Making Figure 6')
figname = 'wpcost_pcost'
ylabel = 'Cost of gains for partnership ($/ML)'
row = 3
col = 4
maximizing = False
inset_lims_1 = [0.06,0.43, 0.25, 0.54]
leg_proj_anchor = (0.62,0.837)
leg_hydro_anchor = (1.65,0.75)
y = results[varnames[row]] 
y_base = 200
# make_satisfice_fig(figname, ylabel, row, col, maximizing, inset_lims_1, leg_proj_anchor, leg_hydro_anchor, y, y_base)
### print fraction of solutions meeting project-level viability 
print('Fraction of sims meeting project-level viability:', np.mean(y <= y_base))
print()

### fig S3: WP_cost vs P_CWG
print('Making Figure S3')
figname = 'wpcost_pcwg'
ylabel = 'Captured water gains for partnership (GL/yr)'
row = 0
col = 4
maximizing = True
inset_lims_1 = [0.05,0.07, 0.25, 0.45]
leg_proj_anchor = (0.6,0.356)
leg_hydro_anchor = (1.6,0.63)
y = results[varnames[row]]
y_base = 55 
# make_satisfice_fig(figname, ylabel, row, col, maximizing, inset_lims_1, leg_proj_anchor, leg_hydro_anchor, y, y_base)
print()

### fig S4: WP_cost vs NP_CWG
print('Making Figure S4')
figname = 'wpcost_npcwg'
ylabel = 'Captured water gains for non-partners (GL/yr)'
row = 2
col = 4
maximizing = True
data_scaler = 1
inset_lims_1 = [0.25,0.07, 0.25, 0.45]
leg_proj_anchor = (0.8,0.356)
leg_hydro_anchor = (1.6,0.63)
y = results[varnames[row]]
y_base = 0 
# make_satisfice_fig(figname, ylabel, row, col, maximizing, inset_lims_1, leg_proj_anchor, leg_hydro_anchor, y, y_base)
print()



# ######################################################
# ### figure S5
# ######################################################
print('Making Figure S5')
# ### get subset of results meeting more strict satisficing criteria
# satisfice = np.logical_and(np.logical_and(np.logical_and(results['worst_price_avg_gain'] <= 200,
#                                                          results['total_partner_avg_gain'] >= 55),
#                                            results['total_other_avg_gain'] >= 0),
#                             results['avg_price_gain_dolAF'] <= 200)

# ### reorganize for parallel coordinate plot
# cols = ['num_partners', 'total_partner_avg_gain', 'total_other_avg_gain', 'avg_price_gain_dolAF', 'worst_price_avg_gain', 'project', 'hydro']
# ressat = results.loc[satisfice, cols]
# tops = ressat.iloc[:, :-2].min(axis=0)
# bottoms = ressat.iloc[:, :-2].max(axis=0)
# switch = bottoms[-2:].copy()
# bottoms[-2:] = tops[-2:]
# tops[-2:] = switch
# ressat.iloc[:, :3] = (ressat.iloc[:, :3].max(axis=0) - ressat.iloc[:, :3]) / (ressat.iloc[:, :3].max(axis=0) - ressat.iloc[:, :3].min(axis=0))
# ressat.iloc[:, 3:5] = (ressat.iloc[:, 3:5] - ressat.iloc[:, 3:5].min(axis=0)) / (ressat.iloc[:, 3:5].max(axis=0) - ressat.iloc[:, 3:5].min(axis=0))

# ### print number of satisficing solutions from different scenarios
# print('Satisficing solutions from dry scenario:', sum(ressat['hydro'] == 'dry'))
# print('Satisficing solutions from median scenario:', sum(ressat['hydro'] == 'median'))
# print('Satisficing solutions from wet scenario:', sum(ressat['hydro'] == 'wet'))
# print('Satisficing solutions from canal project:', sum(ressat['project'] == 'FKC'))
# print('Satisficing solutions from bank project:', sum(ressat['project'] == 'CFWB'))
# print('Satisficing solutions from both projects:', sum(ressat['project'] == 'FKC_CFWB'))

# ### parallel coord plot
# fig,ax = plt.subplots(1,1,figsize=(8.9,4), gridspec_kw={'hspace':0.1, 'wspace':0.1})

# ### pick particular soln to highlight
# idxs = [14983,8071]#[13525,5560] #14983 #8071

# colnorm = 0
# lsdict_hydro = {'wet': '-', 'median': '--', 'dry': ':'}
# cmdict_hydro = {'wet': 'Blues_r', 'median': 'Oranges_r', 'dry': 'Purples_r'}
# zdict_hydro = {'wet': 2, 'median': 3}
# ### plot all satisficing solns
# for i in range(ressat.shape[0]):
#     if ressat.index[i] not in idxs and ressat.iloc[i,]['hydro'] != 'dry':
#         for j in range(len(cols) - 3):
#             numnorm = ressat.iloc[i,colnorm]  / ressat.iloc[:,colnorm].max() *0.75
#             c = cm.get_cmap(cmdict_hydro[ressat.iloc[i,:]['hydro']])(numnorm)
#             ### add sin shape to help distinguish lines
#             y1 = ressat.iloc[i, j]
#             y2 = ressat.iloc[i, j+1]
#             t = np.arange(-np.pi/2, np.pi/2+0.001, 0.01)
#             y = y1 + (np.sin(t) + 1) / 2 * (y2 - y1)
#             x = j + t / np.pi + 1/2
#             ax.plot(x, y, c=c, alpha=0.75, zorder=zdict_hydro[ressat.iloc[i,:]['hydro']], lw=1.5)

# ### highlight chosen solns
# lss = ['--',':']
# for i, idx in enumerate(idxs):
#     if ressat.loc[idx,'hydro'] != 'dry':
#         numnorm = ressat.iloc[:,colnorm].loc[idx] / ressat.iloc[:,colnorm].max() *0.8
#         c = cm.get_cmap(cmdict_hydro[ressat.loc[idx,'hydro']])(numnorm)
#         for j in range(len(cols) - 3): 
#             ### add sin shape to help distinguish lines
#             y1 = ressat.iloc[:, j].loc[idx]
#             y2 = ressat.iloc[:, j+1].loc[idx]
#             t = np.arange(-np.pi/2, np.pi/2+0.001, 0.01)
#             y = y1 + (np.sin(t) + 1) / 2 * (y2 - y1)
#             x = j + t / np.pi + 1/2
#             ax.plot(x, y, c=c, alpha=1, zorder=4, lw=4)
#             ax.plot(x, y, c='k', alpha=1, zorder=5, lw=1.5, ls=lss[i])
    

# ### add top/bottom ranges
# for j in range(len(cols)-2):
#     ax.annotate(str(round(tops[j],2)), [j, 1.02], ha='center', va='bottom', zorder=5)
#     ax.annotate(str(round(bottoms[j],2)), [j, -0.02], ha='center', va='top', zorder=5)    
#     ax.plot([j,j], [0,1], c='k', zorder=1)
# ax.set_xticks([])
# ax.set_yticks([])
# for spine in ['top','bottom','left','right']:
#     ax.spines[spine].set_visible(False)
# ax.arrow(-0.2,0.9,0,-0.7, head_width=0.1, head_length=0.065, color='k', lw=1.5)
# ax.annotate('Direction of preference', xy=(-0.4,0.5), ha='center', va='center', rotation=90)

# ax.set_xlim(-0.4, 4.2)
# ax.set_ylim(-0.4,1.1)
# labels = ['Number of\npartners','Captured\nwater gains,\npartnership\n(GL/yr)','Captured\nwater gains,\nnon-partners\n(GL/yr)','Cost of gains,\npartnership\n($/ML)','Cost of gains,\nworst-off\npartner\n($/ML)']
# for i,l in enumerate(labels):
#     ax.annotate(l, xy=(i,-0.12), ha='center', va='top')

# ## legend
# cb2 = fig.colorbar(cm.ScalarMappable(cmap=cm.get_cmap('Oranges_r'), 
#                    norm=Normalize(vmin=0, vmax=bottoms[colnorm])), ax=ax, fraction=0.15, shrink=0.5, pad=-0.04, alpha=0.7)
# cb2.ax.set_title('Avg.', fontsize=8)
# cb2.set_ticks(np.arange(0,13,2))
# cb2.set_ticklabels(np.arange(12,-1,-2))

# cb1 = fig.colorbar(cm.ScalarMappable(cmap=cm.get_cmap('Blues_r'), 
#                     norm=Normalize(vmin=0, vmax=bottoms[colnorm])), ax=ax, fraction=0.15, shrink=0.5, pad=0.01, alpha=0.7)
# cb1.ax.set_title('Wet', fontsize=8)
# cb1.set_ticks(np.arange(0,13,2))
# cb1.set_ticklabels(np.arange(12,-1,-2))
# ax.annotate('Number of\npartners', [4.35,0.88], ma='center', annotation_clip=False)

# figname = 'parallel_' + str(idxs)
# plt.savefig(fig_dir + figname + '.png', bbox_inches='tight', dpi=300)
# print()






# ######################################################
# ### figure 3
# ######################################################
print('Making Figure 3')

# ### gains & prices for each district in scenarios for which they are participants
# fig,axs = plt.subplots(2,2,figsize=(6.2, 4), sharex='col', sharey='row', gridspec_kw={'hspace':0.08, 'wspace':0.15, 'height_ratios':[1,5]}) 

### break points for tiers
breaks = [0, 13, 27, 41]
barht = 0.2

# ### first do hist of distribution of outcomes for whole partnership - cwg
# ax = axs[0,0]
# dat = results['total_partner_avg_gain']

# binsize = 5.0001
# binmin = -30
# binmax = 70
# bins = np.arange(binmin-binsize/2, binmax+2.5*binsize+0.001, binsize)

# hist_y, hist_x = np.histogram(dat, bins=bins)
# kde_x = [hist_x[0]]
# kde_y = [hist_y[0]]
# for i in range(len(hist_y)-1):
#     kde_x.append(hist_x[i+1])
#     kde_y.append(hist_y[i])
#     kde_x.append(hist_x[i+1])
#     kde_y.append(hist_y[i+1])
# ax.fill_between(kde_x, kde_y, color='cornflowerblue', edgecolor='none', alpha=0.7)
# # print('a)', dat.min(), dat.max(), dat.median(), (dat < 0).mean())
        
        
# ### now hist of distribution of outcomes for whole partnership - cost
# ax = axs[0,1]
# dat = results['avg_price_gain_dolAF'] 

# binsize = 40.0001
# binmin = 0
# binmax = 1000
# bins = np.arange(binmin-binsize/2, binmax+2.5*binsize+0.001, binsize)

# hist_y, hist_x = np.histogram(dat, bins=bins)
# kde_x = [hist_x[0]]
# kde_y = [hist_y[0]]
# for i in range(len(hist_y)-1):
#     kde_x.append(hist_x[i+1])
#     kde_y.append(hist_y[i])
#     kde_x.append(hist_x[i+1])
#     kde_y.append(hist_y[i+1])

# ax.fill_between(kde_x, kde_y, color='cornflowerblue', edgecolor='none', alpha=0.7)
# barht = barht * (ax.get_ylim()[1] - ax.get_ylim()[0])
# # print('b)', dat.min(), dat.max(), dat.median(), (dat >999.99999).mean())


# ### now plot boxplots for cwg & cost
# ax = axs[0,0]
# dat = results['total_partner_avg_gain']

# ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.625) - np.quantile(dat, 0.375)],
#             left = [np.quantile(dat, 0.375)],
#             height = barht, align = 'edge', color='0.5', alpha=1, zorder=2)
# ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.75) - np.quantile(dat, 0.25)],
#             left = [np.quantile(dat, 0.25)],
#             height = barht, align = 'edge', color='0.5', alpha=0.5, zorder=2)
# ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.95) - np.quantile(dat, 0.05)],
#             left = [np.quantile(dat, 0.05)],
#             height = barht, align = 'edge', color='0.5', alpha=0.3, zorder=2)
# ax.plot([np.median(dat)]*2, [-barht*0.4-barht*0.9,-barht*0.4-barht*0.1], color='k', lw=1.5, zorder=3)
# ax.plot([np.quantile(dat, 0.0), np.quantile(dat, 0.05)], [-barht*0.4-barht/2]*2, color='k', lw=0.5, zorder=1)
# ax.plot([np.quantile(dat, 0.95), np.quantile(dat, 1)], [-barht*0.4-barht/2]*2, color='k', lw=0.5, zorder=1)
# ax.annotate('a)', xy=(-28,ax.get_ylim()[1]*0.7), ma='center', xycoords='data', weight='bold', annotation_clip=False)
# ax.set_yticks([])
# # print('overall cwg')
# # print('min: ', np.quantile(dat, 0.0), '5: ', np.quantile(dat, 0.05),'25: ', np.quantile(dat, 0.25), '50: ', np.quantile(dat, 0.5),
# #      '75: ', np.quantile(dat, 0.75), '95: ', np.quantile(dat, 0.95), 'max: ', np.quantile(dat, 1))

# ax = axs[0,1]
# dat = results['avg_price_gain_dolAF']
# ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.625) - np.quantile(dat, 0.375)],
#             left = [np.quantile(dat, 0.375)],
#             height = barht, align = 'edge', color='0.5', alpha=1, zorder=2)
# ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.75) - np.quantile(dat, 0.25)],
#             left = [np.quantile(dat, 0.25)],
#             height = barht, align = 'edge', color='0.5', alpha=0.5, zorder=2)
# ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.95) - np.quantile(dat, 0.05)],
#             left = [np.quantile(dat, 0.05)],
#             height = barht, align = 'edge', color='0.5', alpha=0.3, zorder=2)
# ax.plot([np.median(dat)]*2, [-barht*0.4-barht*0.9,-barht*0.4-barht*0.1], color='k', lw=1.5, zorder=3)
# ax.plot([np.quantile(dat, 0.0), np.quantile(dat, 0.05)], [-barht*0.4-barht/2]*2, color='k', lw=0.5, zorder=1)
# ax.plot([np.quantile(dat, 0.95), np.quantile(dat, 1)], [-barht*0.4-barht/2]*2, color='k', lw=0.5, zorder=1)
# ax.annotate('b)', xy=(-51,ax.get_ylim()[1]*0.7), ma='center', xycoords='data', weight='bold', annotation_clip=False)
# # print('overall price')
# # print('min: ', np.quantile(dat, 0.0), '5: ', np.quantile(dat, 0.05),'25: ', np.quantile(dat, 0.25), '50: ', np.quantile(dat, 0.5),
# #      '75: ', np.quantile(dat, 0.75), '95: ', np.quantile(dat, 0.95), 'max: ', np.quantile(dat, 1))

# ### get gains & prices individual districts, sort based on prices

# districts_samp = districts.copy()
# for d in districts:
#     try:
#         if results[d + '_share'].sum() == 0.0:
#             districts_samp.remove(d)
#     except:
#         districts_samp.remove(d)


# prices = []
# for j,d in enumerate(districts_samp):
#     prices.append(results.loc[results[d+'_share'] > 0, d+'_avg_price'])
    
# medians = [np.median(a) for a in prices]
# sort = np.argsort(medians)
# districts_samp = [districts_samp[s] for s in sort]
# prices = [prices[s] for s in sort]

# nresort = sum([m > 999.999 for m in medians])
# q25s = [np.quantile(a, 0.25) for a in prices[-nresort:]]
# sort = np.argsort(q25s)
# districts_samp[-nresort:] = [districts_samp[-nresort:][s] for s in sort]
# prices[-nresort:] = [prices[-nresort:][s] for s in sort]
# q25s = [np.quantile(a, 0.25) for a in prices]
# nresort = sum([q > 999.999 for q in q25s])
# q05s = [np.quantile(a, 0.05) for a in prices[-nresort:]]
# sort = np.argsort(q05s)
# districts_samp[-nresort:] = [districts_samp[-nresort:][s] for s in sort]

# prices = []
# gains = []
# for j,d in enumerate(districts_samp):
#     prices.append(results.loc[results[d+'_share'] > 0, d+'_avg_price'])
#     gains.append(results.loc[results[d+'_share'] > 0, d+'_exp_gain'])


# ### plot gains individual districts
# ax = axs[1,0]

# for i in range(3):
#     c = pal_cb[i]
#     idxs = list(range(breaks[i], breaks[i+1]))
#     ax.barh(y = range(len(gains) - breaks[i], len(gains) - breaks[i+1], -1), 
#             width = [np.quantile(gains[idx], 0.625) - np.quantile(gains[idx], 0.375) for idx in idxs],
#             left = [np.quantile(gains[idx], 0.375) for idx in idxs],
#             height = 0.75, align = 'edge', color=c, alpha=1, zorder=2)
#     ax.barh(y = np.arange(len(gains) - breaks[i] , len(gains) - breaks[i+1], -1), 
#             width = [np.quantile(gains[idx], 0.75) - np.quantile(gains[idx], 0.25) for idx in idxs],
#             left = [np.quantile(gains[idx], 0.25) for idx in idxs],
#             height = 0.75, align = 'edge', color=c, alpha=0.5, zorder=2)
#     ax.barh(y = np.arange(len(gains) - breaks[i], len(gains) - breaks[i+1], -1), 
#             width = [np.quantile(gains[idx], 0.95) - np.quantile(gains[idx], 0.05) for idx in idxs],
#             left = [np.quantile(gains[idx], 0.05) for idx in idxs],
#             height = 0.75, align = 'edge', color=c, alpha=0.3, zorder=2)
#     # print(districts_samp[breaks[i]: breaks[i+1]])
#     # print([np.median(prices[j]) for j in range(breaks[i], breaks[i+1])])
    
# for idx, d in enumerate(districts_samp):
#     ax.plot([np.median(gains[idx])]*2, [len(gains) - idx + 0.15, len(gains) - idx + 0.6], color='k', lw=1.5, zorder=3)
#     ax.plot([np.quantile(gains[idx], 0.0), np.quantile(gains[idx], 0.05)], [len(gains) - idx + 0.375]*2, color='k', lw=0.5, zorder=1)
#     ax.plot([np.quantile(gains[idx], 0.95), np.quantile(gains[idx], 1)], [len(gains) - idx + 0.375]*2, color='k', lw=0.5, zorder=1)
        
     
# ax.set_xlim(-30,70)
# ax.set_ylim(0.5, 42.5)

# ax.set_xlabel('Captured water gains (GL/year)')
# ax.set_ylabel('District')
# ax.annotate('c)', xy=(-28,40.6), ma='center', xycoords='data', weight='bold', annotation_clip=False)

# ax.set_yticks(np.arange(1.375, 42, 1))
# ax.set_ylabel('District')
# ax.set_yticklabels([str(41 - i) if i%4 == 0 else '' for i in range(0,41)])

# # ### plot prices
# ax = axs[1,1]

# for i in range(3):
#     c = pal_cb[i]
#     idxs = list(range(breaks[i], breaks[i+1]))
#     ax.barh(y = range(len(prices) - breaks[i], len(prices) - breaks[i+1], -1), 
#             width = [np.quantile(prices[idx], 0.625) - np.quantile(prices[idx], 0.375) for idx in idxs],
#             left = [np.quantile(prices[idx], 0.375) for idx in idxs],
#             height = 0.75, align = 'edge', color=c, alpha=1, zorder=2)
#     ax.barh(y = np.arange(len(prices) - breaks[i] , len(prices) - breaks[i+1], -1), 
#             width = [np.quantile(prices[idx], 0.75) - np.quantile(prices[idx], 0.25) for idx in idxs],
#             left = [np.quantile(prices[idx], 0.25) for idx in idxs],
#             height = 0.75, align = 'edge', color=c, alpha=0.5, zorder=2)
#     ax.barh(y = np.arange(len(prices) - breaks[i], len(prices) - breaks[i+1], -1), 
#             width = [np.quantile(prices[idx], 0.95) - np.quantile(prices[idx], 0.05) for idx in idxs],
#             left = [np.quantile(prices[idx], 0.05) for idx in idxs],
#             height = 0.75, align = 'edge', color=c, alpha=0.3, zorder=2)

# for idx, d in enumerate(districts_samp):
#     ax.plot([np.median(prices[idx])]*2, [len(prices) - idx + 0.15, len(prices) - idx + 0.6], color='k', lw=1.5, zorder=3)
#     ax.plot([np.quantile(prices[idx], 0.0), np.quantile(prices[idx], 0.05)], [len(prices) - idx + 0.375]*2, color='k', lw=0.5, zorder=1)
#     ax.plot([np.quantile(prices[idx], 0.95), np.quantile(prices[idx], 1)], [len(prices) - idx + 0.375]*2, color='k', lw=0.5, zorder=1)
    

# ax.set_xlim(-65,1030)
# ax.set_xticks([0,200,400,600,800,1000])
# ax.set_xticklabels(['0','200','400','600','800','1000+'])
# ax.set_ylim(0.5, 42.5)

# ax.set_xlabel('Cost of gains ($/ML)')
# ax.annotate('d)', xy=(-51,40.6), ma='center', xycoords='data', weight='bold', annotation_clip=False)

# ax.set_yticks(np.arange(1.375, 42, 1))
# ax.set_yticklabels([str(41 - i) if i%4 == 0 else '' for i in range(0,41)])
# ax.yaxis.set_tick_params(labelleft=True)            
# ### add legends
# leg_tier = [Patch(facecolor=pal_cb[0], label='1', alpha=0.7),
#              Patch(facecolor=pal_cb[1], label='2', alpha=0.7),
#              Patch(facecolor=pal_cb[2], label='3', alpha=0.7)]
# leg1 = axs[1,0].legend(handles=leg_tier, loc='center', bbox_to_anchor=(2.38,0.55), title='District tier', frameon=False)#, ncol=3)
# leg1.get_title().set_ma('center')

# leg_range = [Patch(facecolor='cornflowerblue', label='Histogram', alpha=0.7),
#              Line2D([0],[0], color='k', marker = '|', label='Median', ls = 'none', markeredgewidth=1.5),
#              Patch(facecolor='0.5', label='Inner 25%', alpha=1),
#              Patch(facecolor='0.5', label='Inner 50%', alpha=0.6),
#              Patch(facecolor='0.5', label='Inner 90%', alpha=0.25),
#              Line2D([0],[0], color='k', label='Full range', lw=0.5)]
# leg1 = axs[1,1].legend(handles=leg_range, loc='center', bbox_to_anchor=(1.25,1.02), title='Data ranges', frameon=False)#, ncol=3)
# leg1.get_title().set_ma('center')

# figname = 'boxplot_combined'
# plt.savefig(fig_dir + figname + '.png', bbox_inches='tight', dpi=300)
# print()



######################################################
### figure 4
######################################################
print('Making Figure 4')

# ### prices for each district in scenarios for which they are participants - 3x3, split by hydro & project
# fig,axs = plt.subplots(3,3,figsize=(6., 2.5), sharex=True, sharey=True, gridspec_kw={'hspace':0.15, 'wspace':0.1}) 

# barht = 0.1

# ### plot 3x3 grid
# labels = [['a)','b)','c)'], ['d)','e)','f)'], ['g)','h)','i)']]
# binsize = 40.0001
# bins = np.arange(-binsize/2, binmax+2.5*binsize+0.001, binsize)
# for row, p in enumerate(projects):
#     for col, h in enumerate(['wet','median','dry']):
#         ax = axs[row,col]
    
#         ### subset data
#         prices = []
#         for j,d in enumerate(districts_samp):
#             prices.append(results.loc[np.logical_and(np.logical_and(results['project'] == p, results['hydro'] == h), results[d+'_share'] > 0), d+'_avg_price'] / 100)
    
#         ### first do distribution of outcomes for whole partnership - cost
#         dat = results.loc[np.logical_and(results['project'] == p, results['hydro'] == h), 'avg_price_gain_dolAF']
#         hist_y, hist_x = np.histogram(dat, bins=bins)
#         kde_x = [hist_x[0]]
#         kde_y = [hist_y[0]]
#         for i in range(len(hist_y)-1):
#             kde_x.append(hist_x[i+1])
#             kde_y.append(hist_y[i])
#             kde_x.append(hist_x[i+1])
#             kde_y.append(hist_y[i+1])
#         ax.fill_between(kde_x, kde_y, color='cornflowerblue', edgecolor='none', alpha=0.7)


# barht = barht * (ax.get_ylim()[1] - ax.get_ylim()[0])
# for row, p in enumerate(projects):
#     for col, h in enumerate(['wet','median','dry']):
#         ax = axs[row,col]
        
#         ### subset data
#         prices = []
#         for j,d in enumerate(districts_samp):
#             prices.append(results.loc[np.logical_and(np.logical_and(results['project'] == p, results['hydro'] == h), results[d+'_share'] > 0), d+'_avg_price'] / 100)
    
#         ### first do distribution of outcomes for whole partnership - cost
#         dat = results.loc[np.logical_and(results['project'] == p, results['hydro'] == h), 'avg_price_gain_dolAF'] 
        
#         ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.625) - np.quantile(dat, 0.375)],
#                     left = [np.quantile(dat, 0.375)],
#                     height = barht, align = 'edge', color='0.5', alpha=1, zorder=2)
#         ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.75) - np.quantile(dat, 0.25)],
#                     left = [np.quantile(dat, 0.25)],
#                     height = barht, align = 'edge', color='0.5', alpha=0.5, zorder=2)
#         ax.barh(y = [-barht*1.4], width = [np.quantile(dat, 0.95) - np.quantile(dat, 0.05)],
#                     left = [np.quantile(dat, 0.05)],
#                     height = barht, align = 'edge', color='0.5', alpha=0.3, zorder=2)
#         ax.plot([np.median(dat)]*2, [-barht*0.4-barht*0.8,-barht*0.4-barht*0.2], color='k', lw=1.5, zorder=3)
#         ax.plot([np.min(dat), np.quantile(dat, 0.05)], [-barht*0.4-barht/2]*2, color='k', lw=0.5, zorder=1)
#         ax.plot([np.quantile(dat, 0.95), np.max(dat)], [-barht*0.4-barht/2]*2, color='k', lw=0.5, zorder=1)

#         # print(p,h)
#         # print('min: ', np.quantile(dat, 0.0), '5: ', np.quantile(dat, 0.05),'25: ', np.quantile(dat, 0.25), '50: ', np.quantile(dat, 0.5),
#         #      '75: ', np.quantile(dat, 0.75), '95: ', np.quantile(dat, 0.95), 'max: ', np.quantile(dat, 1))
        
#         ax.set_xlim(-25,1050)
#         if row == 0:
#             ax.set_xlabel(f'Hydrology = {ldict_hydro[h]}', labelpad=7)
#             ax.xaxis.set_label_position('top') 
#         if col==2:
#             ax.set_ylabel(f'Project =\n{ldict_project[p]}', rotation=270, labelpad=20)
#             ax.yaxis.set_label_position('right')             
#         ax.set_xticks(range(0,1001,200))
#         if row == 2:
#             ax.set_xticks([0,200,400,600,800,1000])
#             ax.set_xticklabels(['0','200','400','600','800','1000+'])
#             ax.set_xlabel('Cost of gains ($/ML)')
#         else:
#             ax.set_xticklabels([])

#         ax.set_yticks([])
#         ax.annotate(labels[row][col], xy=(960,ax.get_ylim()[1]*0.75), ma='center', xycoords='data', weight='bold', annotation_clip=False)

# # ### add legends
# leg_range = [Patch(facecolor='cornflowerblue', label='Histogram', alpha=0.7),
#              Line2D([0],[0], color='k', marker = '|', label='Median', ls = 'none', markeredgewidth=1.5),
#              Patch(facecolor='0.5', label='Inner 25%', alpha=1),
#              Patch(facecolor='0.5', label='Inner 50%', alpha=0.6),
#              Patch(facecolor='0.5', label='Inner 90%', alpha=0.25),
#              Line2D([0],[0], color='k', label='Full range', lw=0.5)]
# leg1 = axs[0,2].legend(handles=leg_range, loc='center', bbox_to_anchor=(1.6,-0.5), title='Data ranges', frameon=False)#, ncol=3)
# leg1.get_title().set_ma('center')

# figname = 'boxplot_kde_3x3'
# plt.savefig(fig_dir + figname + '.png', bbox_inches='tight', dpi=300)

# print()




######################################################
### figure 5
######################################################
print('Making Figure 5')

# ### prices for each district in scenarios for which they are participants - 3x3, split by hydro & project
# fig,axs = plt.subplots(3,3,figsize=(6., 8), sharex=True, gridspec_kw={'hspace':0.07, 'wspace':0.12}) 

# districts_samp = districts.copy()
# for d in districts:
#     try:
#         if results[d + '_share'].sum() == 0.0:
#             districts_samp.remove(d)
#     except:
#         districts_samp.remove(d)


# ### sort based on prices
# prices = []
# for j,d in enumerate(districts_samp):
#     prices.append(results.loc[results[d+'_share'] > 0, d+'_avg_price'])
    
# medians = [np.median(a) for a in prices]
# sort = np.argsort(medians)
# districts_samp = [districts_samp[s] for s in sort]


# ### plot 3x3 grid
# labels = [['a)','b)','c)'], ['d)','e)','f)'], ['g)','h)','i)']]
# for row, p in enumerate(projects):
#     for col, h in enumerate(['wet','median','dry']):
#         ax = axs[row,col]
    
#         ### subset data
#         prices = []
#         for j,d in enumerate(districts_samp):
#             prices.append(results.loc[np.logical_and(np.logical_and(results['project'] == p, results['hydro'] == h), results[d+'_share'] > 0), d+'_avg_price'])
    
#         ### plot prices
#         for i in range(3):
#             c = pal_cb[i]
#             idxs = list(range(breaks[i], breaks[i+1]))
#             ax.barh(y = range(len(prices) - breaks[i], len(prices) - breaks[i+1], -1), 
#                     width = [np.quantile(prices[idx], 0.625) - np.quantile(prices[idx], 0.375) for idx in idxs],
#                     left = [np.quantile(prices[idx], 0.375) for idx in idxs],
#                     height = 0.75, align = 'edge', color=c, alpha=1, zorder=2)
#             ax.barh(y = np.arange(len(prices) - breaks[i] , len(prices) - breaks[i+1], -1), 
#                     width = [np.quantile(prices[idx], 0.75) - np.quantile(prices[idx], 0.25) for idx in idxs],
#                     left = [np.quantile(prices[idx], 0.25) for idx in idxs],
#                     height = 0.75, align = 'edge', color=c, alpha=0.5, zorder=2)
#             ax.barh(y = np.arange(len(prices) - breaks[i], len(prices) - breaks[i+1], -1), 
#                     width = [np.quantile(prices[idx], 0.95) - np.quantile(prices[idx], 0.05) for idx in idxs],
#                     left = [np.quantile(prices[idx], 0.05) for idx in idxs],
#                     height = 0.75, align = 'edge', color=c, alpha=0.3, zorder=2)

#         for idx, d in enumerate(districts_samp):
#             ax.plot([np.median(prices[idx])]*2, [len(prices) - idx + 0.15, len(prices) - idx + 0.6], color='k', lw=1.5, zorder=3)
#             ax.plot([np.quantile(prices[idx], 0.0), np.quantile(prices[idx], 0.05)], [len(prices) - idx + 0.375]*2, color='k', lw=0.5, zorder=1)
#             ax.plot([np.quantile(prices[idx], 0.95), np.quantile(prices[idx], 1)], [len(prices) - idx + 0.375]*2, color='k', lw=0.5, zorder=1)

#         ax.set_xlim(-100,1050)
#         ax.set_ylim(0.5, 42.5)

#         if row == 0:
#             ax.set_xlabel(f'Hydrology = {ldict_hydro[h]}', labelpad=7)
#             ax.xaxis.set_label_position('top') 
#         if col==2:
#             ax.set_ylabel(f'Project type = {ldict_project[p]}', rotation=270, labelpad=12)
#             ax.yaxis.set_label_position('right')             
#         ax.set_xticks(range(0,1010,200))
#         if row == 2:
#             ax.set_xticks([0,200,400,600,800,1000])
#             ax.set_xticklabels(['0','200','400','600','800','1000+'])
#             ax.set_xlabel('Cost of gains ($/ML)')
#         else:
#             ax.set_xticklabels([])
#         ax.set_yticks(np.arange(1.375, 42, 1))
#         if col == 0:
#             ax.set_ylabel('District')
#             ax.set_yticklabels([str(41 - i) if i%4 == 0 else '' for i in range(0,41)])
#         else:
#             ax.set_yticklabels([])
#         ax.annotate(labels[row][col], xy=(-80,40.), ma='center', xycoords='data', weight='bold', annotation_clip=False)

# # ### add legends
# leg_tier = [Patch(facecolor=pal_cb[0], label='1', alpha=0.7),
#              Patch(facecolor=pal_cb[1], label='2', alpha=0.7),
#              Patch(facecolor=pal_cb[2], label='3', alpha=0.7)]
# leg1 = axs[2,2].legend(handles=leg_tier, loc='center', bbox_to_anchor=(1.52,1.33), title='District tier', frameon=False)#, ncol=3)
# leg1.get_title().set_ma('center')

# leg_range = [Line2D([0],[0], color='k', marker = '|', label='Median', ls = 'none', markeredgewidth=1.5),
#              Patch(facecolor='0.5', label='Inner 25%', alpha=1),
#              Patch(facecolor='0.5', label='Inner 50%', alpha=0.6),
#              Patch(facecolor='0.5', label='Inner 90%', alpha=0.25),
#              Line2D([0],[0], color='k', label='Full range', lw=0.5)]
# leg1 = axs[0,2].legend(handles=leg_range, loc='center', bbox_to_anchor=(1.53,-0.32), title='Data ranges', frameon=False)#, ncol=3)
# leg1.get_title().set_ma('center')

# figname = 'boxplot_3x3'
# plt.savefig(fig_dir + figname + '.png', bbox_inches='tight', dpi=300)
# print()


# ### save district order & colors for FIgs 1&8
# print('Saving district tier info for map')
# colors = []
# for i in range(3):
#     j = breaks[i]
#     while j < breaks[i+1]:
#         colors.append(pal_cb[i])
#         j += 1
# df = pd.DataFrame({'district': districts_samp, 'district_label': districts_samp, 'color': colors})
# df.to_csv(fig_dir + 'results_boxplot_combined.csv', index=False)
# print()




######################################################
### figure 8
######################################################
print('Making Figure 8')

# def get_district_hists(idx):
#     sol = results.iloc[idx-1:idx+2,]
#     soldis = [d for d in districts if sol.iloc[0,].loc[d + '_share'] > 0]
#     solshares = [-sol.iloc[0,].loc[d + '_share'] for d in soldis]
#     sort = np.argsort(solshares)
#     soldis = [soldis[s] for s in sort]
#     solshares = [-solshares[s] for s in sort]

#     df = pd.read_csv(fig_dir + 'results_boxplot_combined.csv')
#     sharecolors = [df['color'].loc[df['district'] == d].iloc[0] for d in soldis]
#     sharex = [x + 0.125 for x in range(len(soldis))]
    
#     gain_conversion = 1
#     cost_conversion = 1
    
#     solgaindry = [sol.iloc[0,].loc[d + '_exp_gain'] * gain_conversion for d in soldis]
#     solgainmed = [sol.iloc[1,].loc[d + '_exp_gain'] * gain_conversion for d in soldis]
#     solgainwet = [sol.iloc[2,].loc[d + '_exp_gain'] * gain_conversion for d in soldis]
#     solcostdry = [min(sol.iloc[0,].loc[d + '_avg_price'] * cost_conversion, 1000 * cost_conversion) for d in soldis]
#     solcostmed = [min(sol.iloc[1,].loc[d + '_avg_price'] * cost_conversion, 1000 * cost_conversion) for d in soldis]
#     solcostwet = [min(sol.iloc[2,].loc[d + '_avg_price'] * cost_conversion, 1000 * cost_conversion) for d in soldis]

#     solgaincomb = []
#     solcostcomb = []
#     costx = []
#     costcolors = []
#     for i in range(len(soldis)):
#         solgaincomb.append(solgaindry[i])
#         solgaincomb.append(solgainmed[i])    
#         solgaincomb.append(solgainwet[i])    
#         solcostcomb.append(solcostdry[i])
#         solcostcomb.append(solcostmed[i])    
#         solcostcomb.append(solcostwet[i])   
#         costx.append(i*4+0.5)
#         costx.append(i*4+1.5)
#         costx.append(i*4+2.5)
#         costcolors.append(cdict_hydro['dry'])
#         costcolors.append(cdict_hydro['median'])    
#         costcolors.append(cdict_hydro['wet'])    
        
#     soldict = {'solnum':len(soldis), 'soldis':soldis, 'solshares':solshares, 'sharex':sharex, 'sharecolors':sharecolors, 
#                'solgaindry':solgaindry, 'solgainmed':solgainmed, 'solgainwet':solgainwet, 'solgaincomb':solgaincomb,
#                'solcostdry':solcostdry, 'solcostmed':solcostmed, 'solcostwet':solcostwet, 'solcostcomb':solcostcomb,
#                'costx':costx, 'costcolors':costcolors, 
#                'soltotgaindry': sol.iloc[0,].loc['total_partner_avg_gain'],
#                'soltotgainmed': sol.iloc[1,].loc['total_partner_avg_gain'],
#                'soltotgainwet': sol.iloc[2,].loc['total_partner_avg_gain'],
#                'soltotcostdry': sol.iloc[0,].loc['avg_price_gain_dolAF'],
#                'soltotcostmed': sol.iloc[1,].loc['avg_price_gain_dolAF'],
#                'soltotcostwet': sol.iloc[2,].loc['avg_price_gain_dolAF']}
    
#     print(idx, ': ', soldis, ': ', solshares)
#     return(soldict)

# ### Select Friant-16, Alt-8, and Alt-3 partnerships
# idxs = [27004, 14983, 8071]

# solns = [get_district_hists(i) for i in idxs]

# fig, axs = plt.subplots(3,2, figsize=(6,4.5), sharex='col', sharey=True, gridspec_kw={'hspace':0.1, 'wspace':0.05})

# rowargs = [['solgainwet', 'solcostwet'], ['solgainmed', 'solcostmed'], ['solgaindry', 'solcostdry']]
# rowavgargs = [['soltotgainwet', 'soltotcostwet'], ['soltotgainmed', 'soltotcostmed'], ['soltotgaindry', 'soltotcostdry']]
# hydronames = ['Wet','Avg.','Dry']
# cols = ['Captured water gains\n(GL/yr)', 'Cost of gains\n($/ML)']
# solnames = ['Friant-16\npartnership','Alt-8\npartnership','Alt-3\npartnership']
# hydrocols = [cdict_hydro['wet'], cdict_hydro['median'], cdict_hydro['dry']]
# labels = [['a)','b)'], ['c)','d)'],['e)','f)']]

# for s in range(3):
#     for col in range(2):
#         for row, sol in enumerate(solns):
#             ax = axs[row, col]
#             avgmet = sol[rowavgargs[s][col]]
#             if col==0:
#                 avgmet /= sol['solnum']
#             print(s, row, col, avgmet, sol[rowargs[s][col]])
#             ax.plot([avgmet, avgmet], [2-s-0.47, 2-s+0.47], c=hydrocols[s], zorder=2, lw=2)
#             for i in range(sol['solnum']):
#                 y = 1.7 - s + (i)/(sol['solnum']-1)*0.6
#                 ax.scatter(sol[rowargs[s][col]][i], y, color='none', edgecolor=sol['sharecolors'][i],
#                            lw=2, alpha=0.7, s=20 + 210*sol['solshares'][i], zorder=3)
#             ax.set_ylim([-0.5,2.5])
#             ax.set_yticks([2,1,0])
#             ax.set_yticklabels(hydronames)
#             if col==0:
#                 ax.set_ylabel(solnames[row], labelpad=5)   
#             if row==2:
#                 ax.set_xlabel(cols[col])
#             ax.axhline(1.5, c='k', zorder=5, lw=ax.spines['top'].get_linewidth())
#             ax.axhline(0.5, c='k', zorder=5, lw=ax.spines['top'].get_linewidth())     
#             ax.axvline(0, c='k', zorder=1, lw=ax.spines['top'].get_linewidth(), ls='--', dashes=(1,2))
#             if col==1:
#                 ax.axvline(1000, c='0.5', zorder=1, lw=ax.spines['top'].get_linewidth(), ls='--', dashes=(6,6))
#                 if row==2:
#                     ax.set_xticks([0,200,400,600,800,1000])
#                     ax.set_xticklabels(['0','200','400','600','800', '1000+'])
#             if col==0:
#                 ax.annotate(labels[row][col], (-4,2.2), weight='bold')
#                 ax.set_xlim([-4.5,44])
#             else:
#                 ax.annotate(labels[row][col], (-66,2.2), weight='bold')
#                 ax.set_xlim([-80,1040])
            
# ### add legend
# ax = axs[0,1]
# leg_hands = [Line2D([0],[0], markeredgecolor=solns[0]['sharecolors'][0], color='none', label='1', marker='o', markersize=7, lw=0, markeredgewidth=2, alpha=0.7),
#              Line2D([0],[0], markeredgecolor=solns[0]['sharecolors'][4], color='none', label='2', marker='o', markersize=7, lw=0, markeredgewidth=2, alpha=0.7),
#              Line2D([0],[0], markeredgecolor=solns[0]['sharecolors'][-1], color='none', label='3', marker='o', markersize=7, lw=0, markeredgewidth=2, alpha=0.7)]
# leg1 = ax.legend(handles=leg_hands, loc='center left', title='District\ntier', bbox_to_anchor=(1.015,0.3), frameon=False)
# plt.setp(leg1.get_title(), multialignment='center')

# ax = axs[1,1]
# leg_hands = [Line2D([0],[0], markeredgecolor='k', color='none', label='1%', marker='o', markersize=math.sqrt(20 + 210*0.01), lw=0, markeredgewidth=2, alpha=0.7),
#              Line2D([0],[0], markeredgecolor='k', color='none', label='10%', marker='o', markersize=math.sqrt(20 + 210*0.1), lw=0, markeredgewidth=2, alpha=0.7),
#              Line2D([0],[0], markeredgecolor='k', color='none', label='33%', marker='o', markersize=math.sqrt(20 + 210*0.33), lw=0, markeredgewidth=2, alpha=0.7)]
# leg1 = ax.legend(handles=leg_hands, loc='center left', title='District\nownership\nshare', bbox_to_anchor=(1.015,0.5), frameon=False)
# plt.setp(leg1.get_title(), multialignment='center')

# ax = axs[2,1]
# leg_hands = [Line2D([0],[0], color=cdict_hydro['wet'], label='Wet', lw=2),
#              Line2D([0],[0], color=cdict_hydro['median'], label='Avg.', lw=2),
#              Line2D([0],[0], color=cdict_hydro['dry'], label='Dry', lw=2)]
# leg1 = ax.legend(handles=leg_hands, loc='center left', title='Partnership\naverage for\nhydrology', bbox_to_anchor=(1.015,0.6), frameon=False)
# plt.setp(leg1.get_title(), multialignment='center')

# figname = 'scatter_alternatives_' + str(idxs)
# plt.savefig(fig_dir + figname + '.png', bbox_inches='tight', dpi=300)
# print()





######################################################
### figure 7
######################################################
print('Making Figure 7')

# ### plot partnership averages in tile plot
# fig,axs = plt.subplots(1,3,figsize=(7.8,3), gridspec_kw={'wspace':0.1})

# ### params for CWG & Cost plots
# varindexes = [0,0,1]
# cmapnames = ['PiYG', 'PiYG', 'PiYG_r']
# cmapmaxs = [85,30,100]
# cmapmins = [20,0,40]
# cmaplabels = ['Captured water gains\nfor partnership\n(GL/year)',
#               'Average captured water\ngains per partner\n(GL/year)',
#               'Average cost of gains\nfor partnership\n($/ML)']
# labels = ['a)','b)','c)']
# for i in range(3):
#     ax = axs[i]

#     ### now plot patches with percentages
#     cmap = cm.get_cmap(cmapnames[i])
#     rownames = ['Friant\n-16', 'Alt-8', 'Alt-3']
#     colnames = ['Wet', 'Avg.', 'Dry',]

#     def get_color(cmap, value, maxval, minval):
#         valnorm = (value - minval) / (maxval - minval)
#         return cmap(valnorm)


#     for r,varlist in enumerate(rowavgargs):
#         for c,soln in enumerate(solns):
#             xy = np.zeros((5,2))
#             xy[0,] = (r, 2-c)
#             xy[1,] = (r, 2-c+1)
#             xy[2,] = (r+1, 2-c+1)
#             xy[3,] = (r+1, 2-c)
#             xy[4,] = (r, 2-c)

#             path = mpath.Path(xy)
#             value = soln[varlist[varindexes[i]]]
#             if i == 1:
#                 value /= soln['solnum']
#             color = get_color(cmap, value, cmapmaxs[i], cmapmins[i])
#             patch = mpatches.PathPatch(path, facecolor=color, edgecolor='k', alpha=0.7)
#             ax.add_patch(patch)
#             ax.annotate(str(round(value,1)), (xy[:-1,0].mean(), xy[:-1,1].mean()), va='center', ha='center')#, fontsize=10)

#             if r == 0:
#                 ax.annotate(colnames[c], (c+0.5, -0.3), va='center', ha='center', ma='center', zorder=2)

#         ax.annotate(rownames[r], (-0.5, 2-r+0.5), va='center', ha='center', ma='center', zorder=2)

#     ax.set_xticks([])
#     ax.set_yticks([])
#     for spine in ['top','right','left','bottom']:
#         ax.spines[spine].set_visible(False)


#     ax.set_xlim([-0.8, 3.3])
#     ax.set_ylim([-0.5, 3.2])

#     cb = plt.colorbar(mappable = cm.ScalarMappable(cmap = cmap, norm = Normalize(vmin=cmapmins[i], vmax=cmapmaxs[i])), 
#                          ax=ax, shrink=0.7, label=cmaplabels[i], orientation='horizontal', pad=0.05)

#     ax.annotate(labels[i], (-1.25, 3), weight='bold', annotation_clip=False)
# figname = 'tile_alternatives_' + str(idxs)
# plt.savefig(fig_dir + figname + '.png', bbox_inches='tight', dpi=300)
# print()





######################################################
### figure 2
######################################################
print('Making Figure 2')

reservoir = 'SSJB'

data_dir = '../../calfews_src/data/'
### get inflow data
df_list = []
filpaths = [data_dir + 'input/calfews_src-data-sim.csv', 
            data_dir + 'capow_synthetic/capow_synthetic_50yr_wet.csv',
            data_dir + 'capow_synthetic/capow_synthetic_50yr_median.csv', 
            data_dir + 'capow_synthetic/capow_synthetic_50yr_dry.csv']
for n in range(101):
    filpaths.append(data_dir + 'capow_synthetic/ORCA_forecast_flows' + str(n) + '.csv')
names = ['Historical', 'Wet', 'Avg.', 'Dry']
dates = [['19051001','20160930'], ['19051001','19560929'], ['19051001','19560929'], ['19051001','19560929']]
colors = ['k', cdict_hydro['wet'], cdict_hydro['median'], cdict_hydro['dry']]
alphas = [0.8,0.8,0.8,0.8]
zorders = [3,2,2,2]

for i, filpath in enumerate(filpaths):
    df = pd.read_csv(filpath)
    df.index = pd.date_range(dates[min(i,3)][0], dates[min(i,3)][1],freq='D')
    df['year'] = df.index.year
    df['month'] = df.index.month
    df['wy'] = df.index.year
    df['wy'].loc[df['month'] >= 10] += 1
    ### get aggregated flows
    df['local_fnf'] = df['PFT_fnf'] + df['KWH_fnf'] + df['SUC_fnf'] + df['ISB_fnf']
    df['delta_fnf'] = df['ORO_fnf'] + df['SHA_fnf'] + df['FOL_fnf'] + df['YRS_fnf']
    df['SSJB_fnf'] = df['MIL_fnf'] + df['local_fnf']
    
    df_list.append(df)
    colors.append('0.7')
    alphas.append(0.8)
    zorders.append(1)


### subplots with different exceedence curves for MIL_fnf
fig,axs = plt.subplots(4,2,figsize=(6.5,8.5), gridspec_kw={'hspace':0.06, 'wspace':0.06}, sharex='col', sharey='col')
labels = [['a)','b)','c)','d)'], ['e)','f)','g)','h)']]

km3_conversion = 1.23/1e6  ### convert from acre-feet to km3

### daily flows
for i, df in enumerate(df_list[:4]):
    ### plot flow
    ax = axs[i,0]
    ax.plot(df[reservoir + '_fnf'] * km3_conversion, color=colors[i])
    ax.set_xticks(pd.date_range(start = "1906", end = "2016", freq = "20Y"))
    ax.set_xticklabels(np.arange(0, 111, 20))
    ax.set_ylabel('Daily FNF\n(km$^3$/day)')
    ax.annotate(labels[0][i], xy=(0.03,0.93), xycoords='axes fraction', ha='center', va='center', weight='bold')

### multi-annual exceedances
for i, df in enumerate(df_list):
    
    ### plot annual-sum flow exceedance curves
    ax = axs[0,1]
    flow = df.groupby('wy').sum()[reservoir + '_fnf'].values * km3_conversion
    flow = np.sort(flow)
    p_exc = [(1+i) / (len(flow) + 1) for i in range(len(flow))]
    ax.plot(p_exc, flow, color=colors[i], alpha=alphas[i], zorder=zorders[i])
    ax.yaxis.set_label_position('right') 
    ax.yaxis.tick_right()
    ax.set_ylabel('Annual FNF\n(km$^3$/year)', rotation=270, labelpad=20)
    
    ### plot 2yr-sum flow exceedance curves
    ax = axs[1,1]
    flow = df.groupby('wy').sum().rolling(2).sum()[reservoir + '_fnf'].values / 2 * km3_conversion
    flow = np.sort(flow)
    p_exc = [(1+i) / (len(flow) + 1) for i in range(len(flow))]
    ax.plot(p_exc, flow, color=colors[i], alpha=alphas[i], zorder=zorders[i])  
    ax.yaxis.set_label_position('right') 
    ax.yaxis.tick_right()
    ax.set_ylabel('2-year-average\nannual FNF\n(km$^3$/year)', rotation=270, labelpad=27)
    
    ### plot 5yr-sum flow exceedance curves
    ax = axs[2,1]
    flow = df.groupby('wy').sum().rolling(4).sum()[reservoir + '_fnf'].values / 4 * km3_conversion
    flow = np.sort(flow)
    p_exc = [(1+i) / (len(flow) + 1) for i in range(len(flow))]
    ax.plot(p_exc, flow, color=colors[i], alpha=alphas[i], zorder=zorders[i])  
    ax.yaxis.set_label_position('right') 
    ax.yaxis.tick_right()
    ax.set_ylabel('4-year-average\nannual FNF\n(km$^3$/year)', rotation=270, labelpad=27)
    
    ### plot 10yr-sum flow exceedance curves
    ax = axs[3,1]
    flow = df.groupby('wy').sum().rolling(8).sum()[reservoir + '_fnf'].values / 8 * km3_conversion
    flow = np.sort(flow)
    p_exc = [(1+i) / (len(flow) + 1) for i in range(len(flow))]
    ax.plot(p_exc, flow, color=colors[i], alpha=alphas[i], zorder=zorders[i])      
    ax.yaxis.set_label_position('right') 
    ax.yaxis.tick_right()
    ax.set_ylabel('8-year-average\nannual FNF\n(km$^3$/year)', rotation=270, labelpad=27)
    
for row in range(4):
    axs[row,1].annotate(labels[1][row], xy=(0.03,0.93), xycoords='axes fraction', ha='center', va='center', weight='bold')
    
axs[3,0].set_xlabel('Year')
axs[3,1].set_xlabel('Exceedence probability')
    
leg_proj = [Line2D([0],[0], color=colors[0], alpha=alphas[0], label='Historical'),
            Line2D([0],[0], color=colors[1], alpha=alphas[1], label='Synthetic wet'),
            Line2D([0],[0], color=colors[2], alpha=alphas[2], label='Synthetic average'),
            Line2D([0],[0], color=colors[3], alpha=alphas[3], label='Synthetic dry'),
            Line2D([0],[0], color=colors[4], alpha=alphas[4], label='Synthetic other'),]
leg1 = axs[3,0].legend(handles=leg_proj, loc='center', bbox_to_anchor=(1,-0.5), title='Hydrologic scenario', ncol=3, frameon=False)
leg1.get_title().set_ma('center')
    
figname = 'inflow_exceedances_' + reservoir
plt.savefig(fig_dir + figname + '.png', bbox_inches='tight', dpi=300)    
print()