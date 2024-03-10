import json
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statistics import quantiles
import sys

results_folder = sys.argv[1]
kaf_to_gl = 1.23


results = {}
results_metadata = {}
### get results from hdf5 file
with h5py.File(f'{results_folder}/results.hdf5', 'r') as open_hdf5:
    for label in ['s1', 's2', 's3', 's4', 'statusquo']:
        results_metadata[label] = {
            'colnames': open_hdf5[f'{label}/soln0'].attrs['colnames'],
            'rownames': open_hdf5[f'{label}/soln0'].attrs['rownames'],
            'dvnames': open_hdf5[f'{label}/soln0'].attrs['dv_names'],	
        }
        for soln in list(open_hdf5[label].keys()):
            solname = f'{label}/{soln}'
            ds = open_hdf5[solname]
            results[solname] = {}
            results[solname]['raw'] = ds[:,:] * kaf_to_gl
            results[solname]['dvs'] = ds.attrs['dvs']
            results[solname]['avg_captured_water'] = results[solname]['raw'][::3, :]
            
districts = [s.split('_')[0] for s in results_metadata['statusquo']['rownames'][::3]]

#### get annual payments for infrastructure
FKC_participant_payment = 50e6
CFWB_cost = 50e6
interest_annual = 0.03
time_horizon = 30
projects = {0: 'none', 1: 'FKC', 2: 'CFWB', 3: 'FKC_CFWB'}
principal = {'none': 0., 'FKC': FKC_participant_payment, 'CFWB': CFWB_cost, 'FKC_CFWB': FKC_participant_payment + CFWB_cost}
payments_per_yr = 1
interest_rt = interest_annual / payments_per_yr
num_payments = time_horizon * payments_per_yr
annual_debt_payment_dict = {k: principal[k] / (((1 + interest_rt) ** num_payments - 1) / (interest_rt * (1 + interest_rt) ** num_payments)) for k in principal}

### read in baseline results with no infrastructure investment
baseline_dir = f'{results_folder}/../MOO_results_bridges2/baseline/'
results['baseline'] = {'avg_captured_water': np.zeros(results['statusquo/soln0']['avg_captured_water'].shape)}
for mc in range(21,100):
    mc_idx = mc - 21
    baseline_dict = json.loads(open(f'{baseline_dir}/{mc}_baseline.json', 'r').read())
    for district in baseline_dict.keys():
        idx = [i for i,d in enumerate(districts) if d == district]
        results['baseline']['avg_captured_water'][idx, mc_idx] = baseline_dict[district]['avg_captured_water'] * kaf_to_gl

### calculate objectives by comparing to baseline case
for solname in list(results.keys()):
    if solname == 'baseline':
        results[solname]['cwg_p'] = 0
        results[solname]['cwg_np'] = 0
        results[solname]['n_p'] = 0
        results[solname]['cog_wp_p90'] = 1e6
    else:
        dataset = solname.split('/')[0]
        gains = results[solname]['avg_captured_water'] - results['baseline']['avg_captured_water']
        shares = []
        for d in districts:
            dvname = 'share_'+d
            if dvname in results_metadata[dataset]['dvnames']:
                shares.append(results[solname]['dvs'][np.where(results_metadata[dataset]['dvnames'] == dvname)[0]][0])
            else:
                shares.append(0.)
        shares = np.array(shares)
        #print('shares', shares)
        is_partner = [True if shares[i] > 0 else False for i in range(len(shares))]
        is_nonpartner = [False if shares[i] > 0 else True for i in range(len(shares))]
        partner_gains = gains[is_partner, :]
        nonpartner_gains = gains[is_nonpartner, :]
        results[solname]['cwg_p'] = partner_gains.mean(axis=1).sum()      # captured water gain for partners. avg over time, avg over MC, sum over partners
        results[solname]['cwg_np'] = nonpartner_gains.mean(axis=1).sum()  # captured water gain for nonpartners. avg over time, avg over MC, sum over nonpartners
        results[solname]['n_p'] = partner_gains.shape[0]
        
        project = projects[results[solname]['dvs'][0]]
        annual_debt_payment = annual_debt_payment_dict[project]
        partner_debt_payment = annual_debt_payment * shares[shares > 0]
        partner_cost_gains = np.divide(partner_debt_payment, partner_gains.transpose()).transpose() / 1000
        partner_cost_gains[partner_cost_gains < 0] = 1e6
        worst_partner_cost_gains = partner_cost_gains.max(axis=0)
        results[solname]['cog_wp_p90'] = quantiles(worst_partner_cost_gains, n=10)[-1]  # cost of gains for partners. avg over time, worst over nonpartners, p90 over MC


### write results to file to redo pareto dominance
objnames = ('cwg_p','cwg_np','cog_wp_p90','n_p')
with open(f'{results_folder}objs_wcu.csv', 'w') as f:
    def write_element(s, endline=False):
        if endline:
            f.write(f'{s}\n')
        else:
            f.write(f'{s}, ')
    ### first write header
    write_element('label')
    for dvname in results_metadata['statusquo']['dvnames']:
        write_element(dvname)
    for s in objnames:
        endline = True if s == objnames[-1] else False
        write_element(s, endline)
    
    ### now write each solution
    for solname in results.keys():
        if solname != 'baseline':
            r = results[solname]
            write_element(solname)
            for dv in r['dvs']:
                write_element(dv)
            # need to add one more 0. for OFK, which is partner in statusquo but not in optimization solns
            if solname != 'statusquo/soln0':
                write_element(0)
            for s in objnames:
                endline = True if s == objnames[-1] else False
                write_element(r[s], endline)
        
        
        
