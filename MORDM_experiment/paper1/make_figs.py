import pandas as pd
import time
import fig_functions

import warnings
warnings.filterwarnings('ignore')

fontsize = 14
fig_dir = 'figs/'

### function for printing fig completion with time
t0 = time.time()
def print_completion(fig_label):
    print(f'Finished {fig_label}, {round((time.time() - t0)/60, 2)} minutes')
    print()

### get results from optimized partnerships after reevaluation, after recalculating Pareto set with original 4 objs from multi-objective optimization step. Plus statusquo nonoptimized solution.
results = pd.read_csv('../../results_arx/infra_wcu/objs_wcu_pareto_withStatusQuo.csv', sep=', ')


### map all costs >1000 to 1000 for visual clarity
for c in ['cog_wp_p90']:
    results.loc[results[c] > 1000, c] = 1000



# ### parallel coordinates plots
columns = ['n_p', 'cwg_p', 'cwg_np', 'cog_wp_p90']
column_labels = ['Number of\npartners', 'Captured water\ngain (GL/yr)', 
              'Captured water\ngain for non-\npartners (GL/yr)', 'Cost of gains for\nworst-off partner\n($/ML)']
color_by = 'n_p'  # 'n_p' or 'proj'

### parallel coordinates plot has various options based on brushing criteria & highlighted solutions (see function).
### here loop over fig_stage options used in paper. Do 13 last, which returns soln labels for status quo & compromise partnerships.
fig_stages_paper = [13]#6, 8, 9, 10, 11, 13]
for fig_stage in fig_stages_paper:
    soln_statusquo, soln_compromise = fig_functions.plot_parallel_coords(results, columns, column_labels,
                                                                         fig_stage, color_by)
    print_completion(f'parallel coord option {fig_stage} figure')
print(f'statusquo: {soln_statusquo}, compromise: {soln_compromise}')

### get geospatial data for map figures
water_providers, states, canals_fkc, canals_other, tlb, sjr, kings, res_gdf = fig_functions.get_geodata()

### plot basic regional map
fig_functions.plot_regional_map(water_providers, states, canals_fkc, canals_other, tlb, sjr, kings, res_gdf)
print_completion(f'base regional map')

# ## plot 3-part figure of performance for each partnership
# fig_functions.plot_3part_partnership_performance(results, [soln_compromise], columns, water_providers, states,
#                                                 canals_fkc, canals_other, tlb, sjr, kings, res_gdf)
# print_completion(f'3-part partnership performance figure for compromise')

# fig_functions.plot_3part_partnership_performance(results, [soln_compromise, soln_statusquo], columns, water_providers, states,
#                                                 canals_fkc, canals_other, tlb, sjr, kings, res_gdf)
# print_completion(f'3-part partnership performance figure for status quo')

# # ## comparison of disaggregated performance under climate projections vs mhmm
# fig_functions.compare_partnership_performance_climate(results, soln_compromise, columns)
# fig_functions.compare_partnership_performance_climate(results, soln_statusquo, columns)
# print_completion(f'figure comparing partnership performance under climate projections vs MHMM')


# ### plot 4-pt partner-level disaggregated performance across hydrologic scenarios for 2 partnerships
# fig_functions.plot_partner_disagg_performance(results, soln_compromise)
# print_completion(f'3-part partner-level disagg  performance figure for compromise')

# fig_functions.plot_partner_disagg_performance(results, soln_statusquo)
# print_completion(f'3-part partner-level disagg  performance figure for status quo')


# # ## Note: The rest of figures only use the results from optimization - exclude statusquo solutions
# results = results.loc[['statusquo' not in s for s in results['label']],:]

# # ## plot 5-part figure of share distributions in optimal tradeoff partnership with bivariate choropleth map.
# fig_functions.plot_share_distributions_bivariateChoropleth(results, water_providers, states, canals_fkc, canals_other,
#                                                            tlb, sjr, kings, res_gdf)
# print_completion(f'5-part figure for ownership share distributions')


# ### plot MOO convergence metrics
# fig_functions.plot_moo_metrics()
# print_completion(f'optimization metrics figures')


