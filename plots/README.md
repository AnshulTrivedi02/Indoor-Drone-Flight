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
