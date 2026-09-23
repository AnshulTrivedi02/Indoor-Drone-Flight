# Plots

Figures generated from existing trial data (no new flights).

## Dataset noise-floor figures (n=3 per condition)

From the 9-trial GNSS-denied dataset (`ds_{tex,blank,trans}_r{1,2,3}`, 0.5 m/s,
2.0 m, 300 s, RANSAC seed 42). Metrics are XKF1-vs-SIM from each `.BIN`.

| File | Shows |
|---|---|
| `ate_by_condition.png` | ATE and cross-track error by condition, each as its 3 repeats + mean/range. ATE separates conditions (~68 m, tight clusters); cross-track overlaps (noisy channel). |
| `pn_vs_truey.png` | EKF along-track estimate (XKF1 PN) vs true y, all 9 trials: textured tracks the ideal (slightly above, +6% scale), transition flattens at y≈80 m, blank frozen at ~0. Repeats overlap per condition. |
| `alongtrack_vs_travel.png` | Final EKF along-track estimate (XKF1 PN) vs true travel, all 9 trials grouped by condition: textured ~154 m (near ideal), transition ~80 m (stops at the y=80 m boundary), blank ~0 (frozen). |
| `textured_crosstrack.png` | Cross-track error vs time, 3 corridor_textured repeats (identical config). Spread widens 3.5 m (60 s) → 6.1 m (150 s) → 15.0 m (300 s). |
| `textured_yaw.png` | Yaw error (XKF1−SIM) vs time, 3 corridor_textured repeats. Spread ≤0.26° at 300 s. |

Regenerate (venv-ardupilot): `result_plots.py`, `alongtrack.py`, `textured_repeats.py`, `noise_floor.py`.
See `METHODOLOGY.md`, "Run-to-run noise floor" for the characterisation.

## Characterisation figures (n=1)

| File | Shows | Source trial |
|---|---|---|
| `nomag_trajectory.png` | Top-down GT vs EKF3 (XKF1) trajectory; EKF dead-reckoning curves east as yaw drifts. End-point separation 49.3 m. | `nomag_corridor_baseline` |
| `nomag_yaw_error.png` | XKF1 yaw − GT yaw vs time; fitted drift +5.32 deg/min (no yaw source). | `nomag_corridor_baseline` |
| `inlier_ratio_transition.png` | Optical-flow `inlier_ratio` vs along-corridor position; textured (mean 0.97) → blank (mean 0.33) across the y=80 m boundary. | `corridor_trans_verify` |

Regenerate: `plot_nomag.py` (venv-ardupilot), `plot_inlier.py` (venv-evo).

All metrics use EKF3's own `XKF1` vs SIM truth on one `TimeUS` clock; no
ground-truth yaw alignment is applied.

## Lateral-drift diagnostic — one state per figure (`lateral_drift_diag.py`)

`lateral_drift_diag.py <trial>` (venv-ardupilot) writes each state to its **own**
PNG under `lateral_diag/<trial>/`, for reading individual channels closely — the
same underlying data as `ekf3_diag_1/2/3`, unpacked from the 5x3 grids. All series
are EKF3 `XKF1` vs `SIM` truth on one `TimeUS` clock; position is gauge-fixed at
the sample where flow aiding engages (EKF position leaves 0).

| File | Shows |
|---|---|
| `00_physical_vs_estimated_crosstrack.png` | True east position vs EKF3 `PE` — separates *aircraft* drift from *estimate* drift |
| `01_trajectory_topdown.png` | GT vs EKF3 in the corridor plane |
| `02/03_*_error.png` | Cross-track (PE) and along-track (PN) position error, with the filter's own ±3σ |
| `04-05_pos_*.png` | East / north position, estimate vs truth |
| `06-09_vel_*.png` | East / north velocity and their errors, with ±3σ |
| `10-15_{yaw,roll,pitch}*.png` | Attitude estimate vs truth and error; yaw error carries a linear drift fit |
| `16-18_gyro_bias_*.png` | EKF3 gyro-bias states X/Y/Z |
| `19-21_flow_*.png` | Flow X (lateral) / Y (forward) innovations and the NI test ratio |
| `22_crosstrack_attribution.png` | East-velocity error split into (true speed × yaw error) and the remainder, each integrated into metres of cross-track |
| `23-25_*resid*.png` | Lateral/forward `h_flow` residual vs GT and vs roll rate (needs `_diag_<trial>_flowresid.npz` from `diag_flow_residual.py`, venv-evo) |

Generated for `dsn_{tex_r1,tex_r2,tex_r3,blank_r1,trans_r1}`. The script prints a
summary table (true vs estimated excursion, attribution split, ±3σ breach %,
flow rejection %) alongside the figures.
