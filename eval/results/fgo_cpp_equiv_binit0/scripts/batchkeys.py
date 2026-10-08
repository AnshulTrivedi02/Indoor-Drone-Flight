import sys
import numpy as np
D = "/tmp/claude-1000/-home-makerspace-thesis-ws/3eb7b0fe-468e-4e2e-8ced-a1893d7c2d5c/scratchpad/binit0/dump/"
for p in sys.argv[1:]:
    a = np.fromfile(D + "cpp_" + p + ".batch.f64").reshape(-1, 14)
    b = np.fromfile(D + "fe_" + p + ".batch.f64").reshape(-1, 14)
    print(p, "k identical:", np.array_equal(a[:, 0], b[:, 0]), " max |dt|:", np.abs(a[:, 1] - b[:, 1]).max())
