import numpy as np
import problem_infra

dvs = np.zeros(42)
dvs[0] = 3
dvs[2] = 1.

objs = problem_infra.problem_infra(dvs, 3, 2)

print()
print()
print(objs)