import sys, numpy as np
rep = np.load(sys.argv[1]); pub = np.load(sys.argv[2])
R = rep['rows']; C = list(rep['cols']); fl = pub['fl']; gt = pub['gt']
col = lambda n: R[:, C.index(n)]
# match by stamp
idx = np.searchsorted(fl[:, 0], R[:, 0]); idx = np.clip(idx, 0, len(fl) - 1)
ok = np.abs(fl[idx, 0] - R[:, 0]) < 1e-6
print('matched', ok.sum(), 'of', len(R), 'published', len(fl))
P = fl[idx[ok]]; Q = R[ok]
dfx = np.abs(P[:, 1] - Q[:, 2]); dfy = np.abs(P[:, 2] - Q[:, 3])
dc = np.abs(P[:, 3] - Q[:, 4]); di = np.abs(P[:, 4] - Q[:, 5]); dv = np.abs(P[:, 5] - Q[:, 6])
print('max |dflow_x| %.2e |dflow_y| %.2e  count mismatches %d  inlier mismatches %d  valid mismatches %d' %
      (dfx.max(), dfy.max(), (dc > 0).sum(), (di > 1e-9).sum(), (dv > 0).sum()))
bad = np.where((dfx > 1e-6) | (dc > 0))[0]
print('first mismatches at t =', Q[bad[:5], 0])
