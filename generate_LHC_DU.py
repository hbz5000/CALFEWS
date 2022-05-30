import pandas as pd
from scipy.stats.qmc import LatinHypercube, discrepancy, scale

num_samples = 1152

du_bounds = [('dry_state_mean_multiplier', 0.96, 1.04),
             ('wet_state_mean_multiplier', 0.96, 1.04),
             ('covariance_matrix_dry_multiplier', 0.75, 1.25),
             ('covariance_matrix_wet_multiplier', 0.75, 1.25),
             ('transition_drydry_addition', -0.3, 0.3),
             ('transition_wetwet_addition', -0.3, 0.3),
             ('envflow_base_multiplier_MIL', 0.5, 1.5),
             ('envflow_base_multiplier_north', 0.5, 1.5),
             ('envflow_base_multiplier_south', 0.5, 1.5),
             ('envflow_peak_multiplier_MIL', 0.5, 1.5),
             ('envflow_peak_multiplier_north', 0.5, 1.5),
             ('envflow_peak_multiplier_south', 0.5, 1.5),
             ('demand_MDD_multiplier', 0.7, 1.15),
             ('demand_acreage_multiplier', 0.7, 1.15),
             ('demand_partner_multiplier', 0.85, 1.15),
             ('bank_initial_recharge_multiplier', 0.25, 2),
             ('bank_tot_storage_multiplier', 0.25, 2),
             ('bank_recovery_multiplier', 0.25, 2)]
du_names = [t[0] for t in du_bounds]
du_lb = [t[1] for t in du_bounds]
du_ub = [t[2] for t in du_bounds]

lhc = LatinHypercube(d=len(du_names), optimization='random-cd', seed=18)
sample = lhc.random(n=num_samples)
sample = scale(sample, du_lb, du_ub)

df = pd.DataFrame(data=sample, columns=du_names)
df.to_csv('calfews_src/data/LHC_DU/LHC_DU.csv', index=False)
