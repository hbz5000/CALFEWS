import pstats
import sys

name = sys.argv[1]
mode = sys.argv[2]
p = pstats.Stats("profile_" + name + ".stats")
p.sort_stats("cumulative")
if mode == 'cumulative':
    p.print_stats()
elif mode == 'caller':
    p.print_callers()
elif mode == 'callee':
    p.print_callees()
