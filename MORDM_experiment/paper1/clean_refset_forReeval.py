import numpy as np
import pandas as pd
import sys

### match refsets to original DVs, separate by formulation
reffile = 'results/MOO_results_s2/overall_ref/overall.reference'
checkptfiles = ['results/MOO_results_s2/dv2_seed0_round3/checkpts/s0_nfe96902.checkpt',
                'results/MOO_results_s2/dv2_seed1_round3/checkpts/s1_nfe98802.checkpt',
                'results/MOO_results_s2/dv2_seed2_round3/checkpts/s2_nfe114202.checkpt',
                'results/MOO_results_s2/dv1_seed0_round3/checkpts/s0_nfe106202.checkpt',
                'results/MOO_results_s2/dv1_seed1_round3/checkpts/s1_nfe108502.checkpt',
                'results/MOO_results_s2/dv1_seed2_round3/checkpts/s2_nfe104702.checkpt']
dvs = [2,2,2,1,1,1]
seeds = [0,1,2,0,1,2]
solns = []
with open(reffile) as rf:
    for numr, liner in enumerate(rf, 0):
        liner = [round(float(s), 6) for s in liner.split()]
        if abs(sum(liner)) > 0.1:
            found_line = False
            for checkptfile, dv, seed in zip(checkptfiles, dvs, seeds):
                if not found_line:
                    isarx = False
                    with open(checkptfile) as cf:
                        for numc, linec in enumerate(cf, 0):
                            if 'Number of Improvements' in linec:
                                isarx = False
                            if isarx:
                                linec = [round(float(s), 6) for s in linec.split()]
                                if sum([x in linec for x in liner]) == 5:
                                    solns.append([dv, seed] + linec)
                                    found_line = True
                            if 'Archive:' in linec:
                                isarx = True

### get district shares based on formulation and combine into single dataframe
districts = ["FRS","COF","TUL","KWD","EXE","LDS", "LND","PRT","LWT","TPD", \
             "SAU","TBA","PIX","DLE","KRT","SSJ","SFW","NKN","ARV", "DLR", \
             "ID4","SMI","TJC","BLR","LHL","BDM","WRM","COB","BVA","CWO","HML",\
             "KND","RRB","CNS","ALT","CWC","MAD","SOC","SOB","CCA"]

cols = ['dv', 'seed', 'project'] + ['share_' + str(d) for d in districts] + ['obj' + str(i) for i in range(5)]
min_share = 0.01

df = pd.DataFrame(columns = cols)

for soln in solns:
    ### "project" should be <4, but rounding seems to have made some == 4. subtract small amount. then take floor to get discrete.
    if soln[2] >= 4.0:
        soln[2] = 3.0 - 1e-13
    soln[2] = int(soln[2])
    ### dv_formulation == 1: set number of partners P, and district shares. Set all except largest P to 0
    if soln[0] == 1:
        ### get number of partners & shares
        npartners = int(soln[3])
        shares = np.array(soln[4:-8])
        # get indices of npartners largest shares
        partners = np.argpartition(shares, -npartners)[-npartners:]
        nonpartners = np.argpartition(shares, -npartners)[:-npartners]
        shares[nonpartners] = 0.
    ### dv_formulation == 2: for each district, have binary switch turning on/off, as well as share. 
    else:
        ndistricts = 40
        ### get switch. This will be in [0.0, 2.0).
        switches = np.array(soln[3:ndistricts+3])
        ### get shares
        shares = np.array(soln[ndistricts+3:-8])
        ### Only districts with switch >=1 should have non-zero shares.
        shares[switches < 1.] = 0.
    ### for all dv_formulations, normalize shares to sum to 1, then set all districts below min_share to 0, then renormalize.
    shares = shares / shares.sum()
    loop = 0
    while (loop < 5) and (np.any(np.logical_and(shares < min_share, shares > 0))):
        shares[shares < min_share] = 0.
        shares /= shares.sum()
        loop += 1
    
    ### append solution
    soln_updated = soln[:3] + list(shares) + soln[-8:-3]
    dfsingle = pd.DataFrame({cols[i]:[soln_updated[i]] for i in range(len(soln_updated))})
    df = df.append(dfsingle)


### now add solutions from previous Earth's Future paper (Hamilton et al, 2022) for reevaluation. Plus baseline with no new infrastructure.
alt3 = pd.DataFrame({'share_ID4':0.3632764114896976, 'share_LWT':0.3381612256546455, 'share_PIX':0.2985623628556568}, index=[0])
alt3['project'] = 3
alt8 = pd.DataFrame({'share_'+k:v for k,v in zip(['LHL', 'KRT', 'OTL', 'KND', 'SOC', 'NKN', 'ARV', 'TUL'], [0.2042886185766813, 0.1794291485898997, 0.1492737685922382, 0.1427780807519122, 0.1230885688261011, 0.0897598541362769, 0.0890444390183038, 0.0223375215085865])}, index=[0])
alt8['project'] = 3
friant16 = pd.DataFrame({'share_'+k:v for k,v in zip(['ARV', 'LWT', 'DLE', 'SSJ', 'OFK', 'TUL', 'SFW', 'COF', 'LND', 'SAU', 'TBA', 'LDS', 'PRT', 'FRS', 'EXE', 'TPD'],  [0.136207165, 0.135494501, 0.134481079, 0.11488389800000001, 0.075812672, 0.073845762, 0.063438028, 0.06162258599999999, 0.040607704, 0.031784396, 0.029784795, 0.028243958, 0.025589446000000002, 0.022890257, 0.017610656000000002, 0.0077030959999999996])}, index=[0])
friant16['project'] = 1
baseline = pd.DataFrame({'project':0}, index=[0])
for d in (alt3, alt8, friant16, baseline):
    df = df.append(d)


### save file with all solutions for WCU reevaluation
df.reset_index(inplace=True, drop=True)
df.to_csv(f'results/MOO_results_s2/overall_ref/overall_clean.csv', index=False)

