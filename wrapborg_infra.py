# Master-worker Borg run with Python wrapper
# ensure libborgms.so or libborgms.so is compiled and in this directory
from borg import *
from problem_infra import *

maxEvals = 240
runtimeFreq = 1
ndistricts = 41
nvars = ndistricts + 1
nobjs = 5
nconstrs = 1
results_dir = 'results/infra_borg/'

### need to start up MPI first
Configuration.startMPI()
for seed in range(1):
    ### create an instance of Borg with the calfews infrastructure problem
    borg = Borg(nvars, nobjs, nconstrs, problem_infra)
    Configuration.seed(seed)

    runtimeFile = results_dir + 's' + str(seed) + '.runtime'
    set1File = results_dir + 's' + str(seed) + '.set'

    ### set bounds - dvs[0] is between [1.0, 4.0), and will be rounded down to get int in (1,2,3) representing project type. 
    ###              rest of dvs are between [0-1], representing ownership shares.
    borg.setBounds([1.0, 4.0 - 1e-13], *[[0.0, 1.0]]*ndistricts)
    ### set epsilons - units for objs 0,1,2 are kAF/year, 3 is $/AF, and 4 is number of partners
    borg.setEpsilons(0.1, 0.1, 0.1, 1.0, 0.999)

    # perform the optimization
    result = borg.solveMPI(maxEvaluations=maxEvals, runtime=runtimeFile, frequency=runtimeFreq) #maxTime=maxtime)
    # print the objectives to output
    if result:
        result.display()
        f = open(set1File, 'w')
        for solution in result:
            line = ''
            for v in solution.getVariables():
                line += str(v) + ' '
            for o in solution.getObjectives():
                line += str(o) + ' '
            f.write(line[:-1] + '\n')
        f.write('#')
        f.close()

# shut down MPI
Configuration.stopMPI()

