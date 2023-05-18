import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statistics import quantiles
import sys

results_folder = sys.argv[1]
kaf_to_gl = 1.23
results = {}
#solndict = {'soln96': 'alt3', 'soln97': 'alt8', 'soln98': 'friant16', 'soln95': 'baseline', 'soln50': 'compromise'}

### get results from hdf5 file
with h5py.File(f'{results_folder}/results.hdf5', 'r') as open_hdf5:
    dvnames = open_hdf5['soln0'].attrs['dv_names']
    rownames = open_hdf5['soln0'].attrs['rownames']
    colnames = open_hdf5['soln0'].attrs['colnames']
    for soln in open_hdf5['infra_du_1'].keys():
        ds = open_hdf5[soln]
        results[soln] = {}
        results[soln]['raw_du_1'] = ds[:,:] * kaf_to_gl
        results[soln]['raw_du_2'] = 
        results[soln]['dvs'] = ds.attrs['dvs']
#        results[solname]['runtimes'] = ds.attrs['runtimes']
        assert sum([dvnames[i] == list(ds.attrs['dv_names'])[i] for i in range(len(ds.attrs['dv_names']))]), 'non-matching dvnames'
        assert sum([rownames[i] == list(ds.attrs['rownames'])[i] for i in range(len(ds.attrs['rownames']))]), 'non-matching rownames'
        assert sum([colnames[i] == list(ds.attrs['colnames'])[i] for i in range(len(ds.attrs['colnames']))]), 'non-matching colnames'
            
districts = [s.split('_')[0] for s in rownames[::6]]
for soln in results.keys():
    results[soln]['avg_captured_water'] = results[soln]['raw'][::6, :]
    results[soln]['avg_pumping'] = results[soln]['raw'][3::6, :]

#### get annual paymetns for infrastructure
FKC_participant_payment = 50e6
CFWB_cost = 50e6
interest_annual = 0.03
time_horizon = 30
#      cap = 1000
projects = {0: 'none', 1: 'FKC', 2: 'CFWB', 3: 'FKC_CFWB'}
principle = {'none': 0., 'FKC': FKC_participant_payment, 'CFWB': CFWB_cost, 'FKC_CFWB': FKC_participant_payment + CFWB_cost}
payments_per_yr = 1
interest_rt = interest_annual / payments_per_yr
num_payments = time_horizon * payments_per_yr
annual_debt_payment_dict = {k: principle[k] / (((1 + interest_rt) ** num_payments - 1) / (interest_rt * (1 + interest_rt) ** num_payments)) for k in principle}

### calculate objectives by comparing to baseline case
baseline = results['baseline']
for soln in list(results.keys()):
    gains = results[soln]['avg_captured_water'] - baseline['avg_captured_water']
    pumpaverted = baseline['avg_pumping'] - results[soln]['avg_pumping']
    shares = []
    for d in districts:
        if d in dvnames:
            shares.append(results[soln]['dvs'][np.where(dvnames == d)[0]][0])
        else:
            shares.append(0.)
    shares = np.array(shares)
    is_partner = [True if shares[i] > 0 else False for i in range(len(shares))]
    is_nonpartner = [False if shares[i] > 0 else True for i in range(len(shares))]
    partner_gains = gains[is_partner, :]
    partner_pumpaverted = pumpaverted[is_partner, :]
    nonpartner_gains = gains[is_nonpartner, :]
    results[soln]['cwg_p'] = partner_gains.mean(axis=1).sum()      # captured water gain for partners. avg over time, avg over MC, sum over partners
    results[soln]['ap_p'] = partner_pumpaverted.mean(axis=1).sum() # averted pumping for partners. avg over time, avg over MC, sum over partners
    results[soln]['cwg_np'] = nonpartner_gains.mean(axis=1).sum()  # captured water gain for nonpartners. avg over time, avg over MC, sum over nonpartners
    results[soln]['n_p'] = partner_gains.shape[0]
    
    if soln != 'baseline':
        project = projects[results[soln]['dvs'][0]]
        annual_debt_payment = annual_debt_payment_dict[project]
        partner_debt_payment = annual_debt_payment * shares[shares > 0]
        partner_cost_gains = np.divide(partner_debt_payment, partner_gains.transpose()).transpose() / 1000
        partner_cost_gains[partner_cost_gains < 0] = 1e6
        worst_partner_cost_gains = partner_cost_gains.max(axis=0)
        results[soln]['cog_wp_p90'] = quantiles(worst_partner_cost_gains, n=10)[-1]  # cost of gains for partners. avg over time, worst over nonpartners, p90 over MC
    else:
        results[soln]['cog_wp_p90'] = 1e6


### write results to file to redo pareto dominance
objnames = ('cwg_p','ap_p','cwg_np','cog_wp_p90','n_p')
with open(f'{results_folder}objs_du.csv', 'w') as f:
    def write_element(s, endline=False):
        if endline:
            f.write(f'{s}\n')
        else:
            f.write(f'{s}, ')
    ### first write header
    write_element('label')
    for dvname in dvnames:
        write_element('dvname')
    for s in objnames:
        endline = True if s == objnames[-1] else False
        write_element(s, endline)
    
    ### now write each solution
    for soln in results.keys():
        r = results[soln]
        write_element(soln)
        for dv in r['dvs']:
            write_element(dv)
        for s in objnames:
            endline = True if s == objnames[-1] else False
            write_element(r[s], endline)
        
        
        
