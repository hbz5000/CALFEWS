# Master-worker Borg run with Python wrapper
# ensure libborgms.so or libborgms.so is compiled and in this directory

def main():
    from borg import Configuration, Borg
    from problem_infra import problem_infra
    import sys

    results_dir = sys.argv[1]
    maxEvals = int(sys.argv[2])
    maxEvalsPrevious = int(sys.argv[3])
    seed = int(sys.argv[4])
    runtimeFreq = int(sys.argv[5])
    dv_formulation = int(sys.argv[6])

    createCheckpt = 1
    ndistricts = 40
    nobjs = 5
    nconstrs = 2

    ### see get_effective_dvs() in problem_infra.py for explanation of different decision variable formulatons
    if dv_formulation == 0:
        nvars = ndistricts + 1 
    elif dv_formulation == 1:
        nvars = ndistricts + 2
    elif dv_formulation == 2:
        nvars = ndistricts * 2 + 1


    ### need to start up MPI first
    Configuration.startMPI()
      
    ### create an instance of Borg with the calfews infrastructure problem
    borg = Borg(nvars, nobjs, nconstrs, problem_infra)
    Configuration.seed(seed)

    runtimeFile = results_dir + '/runtime/s' + str(seed) + '_nfe' + str(maxEvalsPrevious) + '.runtime'
    setFile = results_dir + '/sets/s' + str(seed) + '_nfe' + str(maxEvalsPrevious) + '.set'
    evaluationFile = results_dir + '/evaluations/s' + str(seed) + '.evaluations'

    if dv_formulation == 0:
        ### set bounds - dvs[0] is between [1.0, 4.0), and will be rounded down to get int in (1,2,3) representing project type.
        ### rest of dvs are between [0-1], representing ownership shares.
        borg.setBounds([1.0, 4.0 - 1e-13], *[[0.0, 1.0]]*ndistricts)
    elif dv_formulation == 1:
        ### set bounds - dvs[0] is between [1.0, 4.0), and will be rounded down to get int in (1,2,3) representing project type.
        ### dvs[1] is between [1.0, ndistricts+1), and will be rounded down to get int representing number of partners
        ### rest of dvs are between [0-1], representing ownership shares.
        borg.setBounds([1.0, 4.0 - 1e-13], [1.0, ndistricts + 1 - 1e-13], *[[0.0, 1.0]]*ndistricts)
    elif dv_formulation == 2:
        ### set bounds - dvs[0] is between [1.0, 4.0), and will be rounded down to get int in (1,2,3) representing project type.
        ### dvs[1 to ndistricts] are between [0.0, 2.0), and will be rounded down to get binary switch for each district's inclusion in partnership
        ### rest of dvs are between [0-1], representing ownership shares.
        borg.setBounds([1.0, 4.0 - 1e-13], *[[0.0, 2.0 - 1e-13]]*ndistricts, *[[0.0, 1.0]]*ndistricts)

    ### set epsilons - units for objs 0,1,2 are kAF/year, 3 is $/AF, and 4 is number of partners
    borg.setEpsilons(2., 2., 2., 5., 0.999)


    # perform the optimization
    if createCheckpt == 0:
        result = borg.solveMPI(maxEvaluations=maxEvals, runtime=runtimeFile, frequency=runtimeFreq, evaluationFile=evaluationFile)
    else:
        newCheckptFile = results_dir + '/checkpts/s' + str(seed)  # This is just base - will have "_NFE#.checkpt" appended, where # is number of function evals. Will print checkpt each time we write to runtime file, as well as end
        if maxEvalsPrevious <= 0:
            result = borg.solveMPI(maxEvaluations=maxEvals, runtime=runtimeFile, frequency=runtimeFreq, newCheckptFile=newCheckptFile, evaluationFile=evaluationFile)
        else:
            oldCheckptFile = results_dir + '/checkpts/s' + str(seed) + '_nfe' + str(maxEvalsPrevious) + '.checkpnt'
            result = borg.solveMPI(maxEvaluations=maxEvals, runtime=runtimeFile, frequency=runtimeFreq, newCheckptFile=newCheckptFile, oldCheckptFile=oldCheckptFile, evaluationFile=evaluationFile)


    # print the objectives to output
    if result:
        result.display()
        f = open(setFile, 'w')
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


if __name__ == '__main__':
    from multiprocessing import set_start_method
    set_start_method("spawn")

    main()
