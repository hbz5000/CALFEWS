import pandas as pd
import fig_functions
import time

import warnings
warnings.filterwarnings('ignore')

fontsize = 14
fig_dir = 'figs/'

### function for printing fig completion with time
t0 = time.time()
def print_completion(fig_label):
    print(f'Finished {fig_label}, {round((time.time() - t0)/60, 2)} minutes')
    print()

### get results from reevaluation, after recauculating Pareto set with original 5 objs from multi-objective optimization step, plus baseline results from friant16, & 2 other solns from Earth's Future paper
results = pd.read_csv('../../results_arx/infra_wcu/objs_wcu_pareto_5objs.csv', sep=', ')
baseline_results = pd.read_csv('../../results_arx/infra_wcu/objs_wcu_pareto_5objs_coarse_withBaselines.csv', sep=', ').iloc[-3:, :]
results = results.append(baseline_results, ignore_index=True)

### map all costs >1000 to 1000 for visual clarity
for c in ['cog_wp_p90','cog_wp_p50','cog_p_p90','cog_p_p50']:
    results.loc[results[c] > 1000, c] = 1000



# ### parallel coordinates plots
columns = ['n_p', 'cwg_p', 'ap_p', 'cwg_np', 'cog_wp_p90']
column_labels = ['Number of\npartners', 'Captured water\ngain (GL/yr)', 'Pumping reduction\n(GL/yr)',
              'Captured water\ngain for non-\npartners (GL/yr)', 'Cost of gains for\nworst-off partner\n($/ML)']
color_by = 'n_p'  # 'n_p' or 'proj'

### parallel coordinates plot has various options based on brushing criteria & highlighted solutions (see function).
### here loop over fig_stage options used in paper. Do 13 last, which returns soln labels for status quo & compromise partnerships.
fig_stages_paper = [6, 8, 9, 10, 11, 13]
for fig_stage in fig_stages_paper:
    soln_statusquo, soln_compromise = fig_functions.plot_parallel_coords(results, columns, column_labels,
                                                                         fig_stage, color_by)
    print_completion(f'parallel coord option {fig_stage} figure')


### get geospatial data for map figures
water_providers, states, canals_fkc, canals_other, tlb, sjr, kings, res_gdf = fig_functions.get_geodata()

### plot basic regional map
fig_functions.plot_regional_map(water_providers, states, canals_fkc, canals_other, tlb, sjr, kings, res_gdf)
print_completion(f'base regional map')

## plot 3-part figure of performance for each partnership
fig_functions.plot_3part_partnership_compromise(results, [soln_compromise], columns, water_providers, states,
                                                canals_fkc, canals_other, tlb, sjr, kings, res_gdf)
print_completion(f'3-part partnership performance figure for compromise')

fig_functions.plot_3part_partnership_compromise(results, [soln_compromise, soln_statusquo], columns, water_providers, states,
                                                canals_fkc, canals_other, tlb, sjr, kings, res_gdf)
print_completion(f'3-part partnership performance figure for status quo')



### plot 4-pt partner-level disaggregated performance across hydrologic scenarios for 2 partnerships
fig_functions.plot_partner_disagg_performance(results, soln_compromise)
print_completion(f'4-part partner-level disagg  performance figure for compromise')

fig_functions.plot_partner_disagg_performance(results, soln_statusquo)
print_completion(f'4-part partner-level disagg  performance figure for status quo')


### Note: The rest of figures only use the results from optimization - exclude 3 non-optimization solutions
results = results.loc[['soln' in s for s in results['label']],:]

### plot 5-part figure of share distributions in optimal tradeoff partnership with bivariate choropleth map.
fig_functions.plot_share_distributions_bivariateChoropleth(results, water_providers, states, canals_fkc, canals_other,
                                                           tlb, sjr, kings, res_gdf)
print_completion(f'5-part figure for ownership share distributions')

### plot ownership share concentration across optimal tradeoff partnerships
fig_functions.plot_ownership_share_concentrations(results, water_providers)
print_completion(f'ownership share concentration figure')




