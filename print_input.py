import sys

resultsfile = 'results/MOO_results_s2/overall_ref/overall_coarse_clean.csv'
linenum = int(sys.argv[1])

with open(resultsfile, 'r') as f:
    for i, line in enumerate(f):
        if i == 0:
            cols = line
        if i == linenum:
            vals = line
            break

cols = cols.strip().split(',')
vals = vals.strip().split(',')
project = int(vals[2])
print(project)
share_dict = {col.split('_')[1]: val for col, val in zip(cols[3:-5], vals[3:-5])}
print(share_dict)
