import numpy as np
import problem_infra

dvs = np.zeros(42)
dvs[0] = 3
dvs[11] = 0.33
dvs[17] = 0.34
dvs[26] = 0.33

objs = problem_infra.problem_infra(dvs, 2, 2)

print()
print()
print(objs)
