# Master-worker Borg run with Python wrapper
# ensure libborgms.so or libborgms.so is compiled and in this directory
from borg import *
from problem_infra import *

nSeeds = 2
maxEvals = 6000
maxEvalsPrevious = 5000
runtimeFreq = 25
createCheckpt = 1

ndistricts = 37
nvars = ndistricts + 2
nobjs = 5
nconstrs = 2
results_dir = 'results/infra_borg/'


### need to start up MPI first
Configuration.startMPI()
for seed in range(nSeeds):
    ### create an instance of Borg with the calfews infrastructure problem
    borg = Borg(nvars, nobjs, nconstrs, problem_infra)
    Configuration.seed(seed)

    runtimeFile = results_dir + '/runtime/s' + str(seed) + '_fe' + str(maxEvals) + '.runtime'
    set1File = results_dir + '/sets/s' + str(seed) + '_fe' + str(maxEvals) + '.set'

    ### set bounds - dvs[0] is between [1.0, 4.0), and will be rounded down to get int in (1,2,3) representing project type.
    ###              dvs[1] is between [1.0, ndistricts+1), and will be rounded down to get int in (1,2,...,ndistricts) representing number of partners 
    ###              rest of dvs are between [0-1], representing ownership shares.
    borg.setBounds([1.0, 4.0 - 1e-13], [1.0, ndistricts - 1e-13], *[[0.0, 1.0]]*ndistricts)
    ### set epsilons - units for objs 0,1,2 are kAF/year, 3 is $/AF, and 4 is number of partners
    borg.setEpsilons(2., 2., 2., 5., 0.999)


    # perform the optimization
    if createCheckpt == 0:
        result = borg.solveMPI(maxEvaluations=maxEvals, runtime=runtimeFile, frequency=runtimeFreq)
    else:
        newCheckptFile = results_dir + '/checkpts/s' + str(seed) + '_fe' + str(maxEvals) + '.checkpoint'
        if maxEvalsPrevious <= 0:
            result = borg.solveMPI(maxEvaluations=maxEvals, runtime=runtimeFile, frequency=runtimeFreq, newCheckptFile=newCheckptFile)
        else:
            oldCheckptFile = results_dir + '/checkpts/s' + str(seed) + '_fe' + str(maxEvalsPrevious) + '.checkpoint'
            result = borg.solveMPI(maxEvaluations=maxEvals, runtime=runtimeFile, frequency=runtimeFreq, newCheckptFile=newCheckptFile, oldCheckptFile=oldCheckptFile)


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
            for c in solution.getConstraints():
                line += str(c) + ' '
            f.write(line[:-1] + '\n')
        f.write('#')
        f.close()

# shut down MPI
Configuration.stopMPI()

