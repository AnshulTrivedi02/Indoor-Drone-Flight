# Install gate for the D18-corrected C++ FGO (item 2d), written BEFORE any band was run

Source under test: `fwd-camera` `cca8e90` (the D18 change `df50ad9`: initial yaw σ 1°, roll/pitch σ 5°, both cores).
Bands, bags, thresholds and scripts are the 2026-10-09 ones (`fgo_cpp_equiv_binit0`, `fgo_cpp_equiv_yawgate`):
same keyframe count, same factor decisions, |Δp| ≤ 1 mm, |Δyaw| ≤ 0.01°; default Eigen build.

## Rule (from the 2026-10-09 rulings; fixed now, before seeing any number)
- **Must PASS** (any failure = a NEW failure: stop, report, do NOT install):
  - B1 fwdc_tex_r1 heading; B2/B3 T_A_r1/T_D_r1 live (anchored rows); B4/B5 T_A_r1/T_D_r1 batch;
  - C on all four bags (dsn_tex_r1 baseline, fwdc_tex_r1 heading, T_A_r1, T_D_r1);
  - L1 (dsn_tex_r1) and L2 (fwdc_tex_r1 heading).
- **Optional:** B6 (O_r1 GNSS live / batch). Reported; a failure is reported but does not by itself block.
- **Band A:**
  - dsn_blank_r1 and dsn_trans_r1: reported AS WORDED. They fail by the known mechanism (round-off amplified where
    the Python FGO itself diverges); not a blocker, as ruled 2026-10-09.
  - dsn_tex_r1: if it PASSES, fine. If it FAILS, the post-hoc forced-gate diagnostic is run. The failure is accepted
    as the RULED threshold-tie mode (ruling 2026-10-09 item 1) ONLY IF, with the gate decisions forced equal, the
    emulate-gemv build is bit-identical to Python AND the default build is within the 1 mm / 0.01° band. Otherwise:
    stop, report, do NOT install.
- **Probe:** the new Python probe vs the new C++ probe: bit-identical except the known gemv / inverse round-off lines.
  The new Python probe vs the yaw-gate probe: only lines depending on the X(0) prior may differ; every factor [A|b]
  unchanged.
