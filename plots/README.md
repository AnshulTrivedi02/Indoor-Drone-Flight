# Plots

Presentation figures generated from existing trial data (no new flights). All
figures are **n=1** and labelled as such.

| File | Shows | Source trial | Data |
|---|---|---|---|
| `nomag_trajectory.png` | Top-down GT vs EKF3 (XKF1) trajectory; EKF dead-reckoning curves east as yaw drifts. End-point separation 49.3 m. | `nomag_corridor_baseline` | `ardupilot.bin` (XKF1, SIM) |
| `nomag_yaw_error.png` | XKF1 yaw − GT yaw vs time; fitted drift +5.32 deg/min (no yaw source). | `nomag_corridor_baseline` | `ardupilot.bin` (XKF1, SIM) |
| `inlier_ratio_transition.png` | Optical-flow `inlier_ratio` vs along-corridor position; textured (mean 0.97) → blank (mean 0.33) across the y=80 m boundary. | `corridor_trans_verify` | ROS2 bag (`/optical_flow/measurement`, `/ground_truth/pose`) |

Regenerate: `plot_nomag.py` (venv-ardupilot) and `plot_inlier.py` (venv-evo).
Scale/yaw use EKF3's own `XKF1` vs SIM truth on one `TimeUS` clock; no
ground-truth yaw alignment is applied.
