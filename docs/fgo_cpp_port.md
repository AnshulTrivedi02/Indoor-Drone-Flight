# FGO C++ port — option A (equivalence to the thesis FGO)

Supervisor ruling 2026-10-08: start the FGO C++ port as coding work and prove equivalence to the
thesis FGO on recorded bags before any further step. Option A of `docs/real_flights_plan.md` §9.3:
a C++ port with the SAME numerical central-difference Jacobians as `src/estimators/fgo/factors.py`.
SymForce exact Jacobians are a later, separate step and are not started here. No simulator was used.

## Pre-registered equivalence band (written 2026-10-08, before the first comparison run)

On the same recorded bag, the C++ FGO and the Python FGO (`fgo_replay.py <trial> 0.25 2 baseline`)
must give:

- an **identical keyframe count**;
- per keyframe, **position difference ≤ 1 mm** (Euclidean, base_link, world ENU);
- per keyframe, **yaw difference ≤ 0.01°**.

Bags, in order: `dsn_tex_r1` (300 s corridor, textured), then `dsn_blank_r1`, `dsn_trans_r1`.
If the band is not met, the cause is found (LM, linearisation order, floating point) rather than the
band being loosened; any unavoidable residual is reported with its size and cause.

(Results, build steps and timing are added below after the runs.)
