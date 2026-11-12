# Thesis assets: index

Built 2026-11-13 by `eval/build_thesis_assets.py` from the committed outputs; no generator run, no number changed. `thesis_complete.pdf` holds all items in this order with their draft captions.

| number | title | file(s) in this bundle | source generator | source output |
|---|---|---|---|---|
| Figure 3.1 | System architecture: sensors, bridges, the three estimators and where each one runs. | `figures/fig_3-1.pdf` | `eval/figs_thesis_methods.py` | `figures_thesis/methods_architecture.pdf` |
| Table 3.1 | Estimator design: EKF3, the UKF and the FGO | `tables_tex/tab_3-1.tex` | `eval/figs_thesis_methods.py` | `tables/methods_estimator_design.md`, `tables/methods_estimator_design.tex` |
| Table 3.2 | Noise parity: measurement and process noise per sensor and estimator | `tables_tex/tab_3-2.tex` | `eval/figs_thesis_methods.py` | `tables/methods_noise_parity.md`, `tables/methods_noise_parity.tex` |
| Table 3.3 | Documented exceptions to noise and treatment parity, with their rulings | `tables_tex/tab_3-3.tex` | `eval/figs_thesis_methods.py` | `tables/methods_noise_exceptions.md`, `tables/methods_noise_exceptions.tex` |
| Table 3.4 | Experiment matrix | `tables_tex/tab_3-4.tex` | `eval/figs_thesis_methods.py` | `tables/methods_experiment_matrix.md`, `tables/methods_experiment_matrix.tex` |
| Figure 4.1 | The camera heading stops the sideways drift: without it every estimator flies into the west wall. | `figures/fig_4-1.pdf` | `eval/figs_thesis.py` | `figures_thesis/F2_heading_stops_sideways_drift.pdf` |
| Figure 4.1b | Without a heading source the heading error grows until the wall; with the camera heading it stays near zero. | `figures/fig_4-1b.pdf` | `eval/figs_thesis.py` | `figures_thesis/F9_heading_error_closed_loop.pdf` |
| Figure 4.1c | Without a heading source, all three estimates drift sideways: the unaligned paths and their errors along the corridor. | `figures/fig_4-1c.pdf` | `eval/figs_thesis_drift.py` | `figures_thesis/R5_drift_unaligned.pdf` |
| Figure 4.1d | Without a heading source, every one of the 9 flights drifts sideways off the true path. | `figures/fig_4-1d.pdf` | `eval/figs_thesis_drift9.py` | `figures_thesis/R6_drift_9flights.pdf` |
| Figure 4.2 | True and estimated paths, top-down: with the camera heading the UKF and FGO paths lie on the true path. | `figures/fig_4-2.pdf` | `eval/figs_thesis_results.py` | `figures_thesis/R3_trajectory_overlay.pdf` |
| Table 4.1 | Position error without and with the camera heading (textured floor) | `tables_tex/tab_4-1.tex` | `eval/figs_thesis.py` | `tables/T2_accuracy_heading.md`, `tables/T2_accuracy_heading.tex` |
| Table 4.1b | Experiment 1B accuracy with the camera heading: EKF3 (via Replay) and matched 5° UKF/FGO arms (DESCRIPTIVE) | `tables_tex/tab_4-1b.tex` | `eval/figs_thesis.py` | `tables/T2B_ekf3_heading_replay.md`, `tables/T2B_ekf3_heading_replay.tex` |
| Table 4.2 | Blank floor: position error after the loss of flow aiding | `tables_tex/tab_4-2.tex` | `eval/figs_thesis.py` | `tables/T3_blank_floor.md`, `tables/T3_blank_floor.tex` |
| Table 4.3 | Closed loop at half real-time (RTF 0.5): the final build of each estimator flying the vehicle | `tables_tex/tab_4-3.tex` | `eval/figs_thesis.py` | `tables/T4_closed_loop.md`, `tables/T4_closed_loop.tex` |
| Table 4.3b | Closed loop at full real-time (RTF 1.0): the no-heading n = 3 cells, companion to Table 4.3 | `tables_tex/tab_4-3b.tex` | `eval/figs_thesis.py` | `tables/T4F_closed_loop_full_speed.md`, `tables/T4F_closed_loop_full_speed.tex` |
| Table 4.4 | Experiment 1A, standard-sensor dataset, textured floor, flights 1-9: fitted cruise ATE and raw world-frame error, per estimator | `tables_tex/tab_4-4.tex` | `eval/figs_thesis.py` | `tables/T9_1A_fitted_vs_raw.md`, `tables/T9_1A_fitted_vs_raw.tex` |
| Figure 5.1 | Fewer tags, larger live errors; the FGO's hindsight batch stays at 0.01–0.03 m. | `figures/fig_5-1.pdf` | `eval/figs_thesis.py` | `figures_thesis/F5_T_tags_known_positions.pdf` |
| Figure 5.2 | Re-identifying tags at unknown positions keeps the FGO's error flat; without it the error grows 2.9 to 4.5 times over five laps. | `figures/fig_5-2.pdf` | `eval/figs_thesis.py` | `figures_thesis/F7_L_loop_closure.pdf` |
| Figure 5.3 | Indoors without GNSS the live tracks drift and EKF3 jumps 4.1 m on return; hindsight keeps the error near 1 m. | `figures/fig_5-3.pdf` | `eval/figs_thesis.py` | `figures_thesis/F6_O_outdoor_indoor.pdf` |
| Table 5.1 | Experiment 4 (outdoor–indoor): indoor horizontal RMSE per flight (123 s, GNSS off) | `tables_tex/tab_5-1.tex` | `eval/figs_thesis.py` | `tables/T6_O_indoor_rmse.md`, `tables/T6_O_indoor_rmse.tex` |
| Table 5.2 | Hindsight: the FGO whole-flight batch against the smoothed UKF | `tables_tex/tab_5-2.tex` | `eval/figs_thesis.py` | `tables/T8_hindsight_ratio.md`, `tables/T8_hindsight_ratio.tex` |
| Table 6.1 | Experiment 5 (tag hold): drift while the wall tag is hidden, flying estimators | `tables_tex/tab_6-1.tex` | `eval/figs_thesis.py` | `tables/T5_H_tag_loss_drift.md`, `tables/T5_H_tag_loss_drift.tex` |
| Table 7.1 | Scorecard of the restated verdicts by experiment and estimator | `tables_tex/tab_7-1.tex` | `eval/figs_thesis.py` | `tables/T1_scorecard.md`, `tables/T1_scorecard.tex` |
| Table 7.2 | Failure behaviour: blank-floor validity, the Experiment 4 return jump and the 5S safety tests | `tables_tex/tab_7-2.tex` | `eval/figs_thesis.py` | `tables/T7_failure_behaviour.md`, `tables/T7_failure_behaviour.tex` |
| Table 7.3 | Hypothesis scorecard: every pre-registered hypothesis, comparison and check, with its restated verdict | `tables_tex/tab_7-3.tex` | `eval/figs_thesis_results.py` | `tables/R1_hypothesis_scorecard.md`, `tables/R1_hypothesis_scorecard.tex` |
| Table 7.4 | Corrections grouped by how they were found, with the headline claims and hypotheses each one changed | `tables_tex/tab_7-4.tex` | `eval/figs_thesis_results.py` | `tables/R2_corrections_by_discovery.md`, `tables/R2_corrections_by_discovery.tex` |
| Table 7.5 | Spread between estimators against the effect of adding information, per condition | `tables_tex/tab_7-5.tex` | `eval/figs_thesis_results.py` | `tables/R4_information_vs_estimator.md`, `tables/R4_information_vs_estimator.tex` |
| Table 8.1 | Compute and deployability per estimator | `tables_tex/tab_8-1.tex` | `eval/figs_thesis_methods.py` | `tables/realflight_compute.md`, `tables/realflight_compute.tex` |
| Table 8.2 | Safety findings from the SITL safety bench, with mitigations and status | `tables_tex/tab_8-2.tex` | `eval/figs_thesis_methods.py` | `tables/realflight_safety_findings.md`, `tables/realflight_safety_findings.tex` |
| Table A.1 | Closed loop: every flown build against the five closed-loop criteria and the contact window. | `tables_tex/tab_A-1.tex`, `figures/tab_A-1_p1.pdf`, `figures/tab_A-1_p2.pdf` | `eval/figs_thesis.py` | `figures_thesis/A1_closed_loop_builds.pdf`, `figures_thesis/A1_closed_loop_builds_p1.pdf`, `figures_thesis/A1_closed_loop_builds_p2.pdf` |
| Table A.2 | Experiment 5 hold sets and the 5S safety tests (all runs). | `tables_tex/tab_A-2.tex`, `figures/tab_A-2_p1.pdf`, `figures/tab_A-2_p2.pdf`, `figures/tab_A-2_p3.pdf` | `eval/figs_thesis.py` | `figures_thesis/A2_H_and_safety_p1.pdf`, `figures_thesis/A2_H_and_safety_p2.pdf`, `figures_thesis/A2_H_and_safety_p3.pdf` |
| Table A.3 | The robust-weighting test (H1.4), the Experiment 3 compute cost and the build ablations. | `tables_tex/tab_A-3.tex`, `figures/tab_A-3_p1.pdf`, `figures/tab_A-3_p2.pdf` | `eval/figs_thesis.py` | `figures_thesis/A3_F1_cost_ablations_p1.pdf`, `figures_thesis/A3_F1_cost_ablations_p2.pdf` |
| Table A.4 | Verdict register: every registered hypothesis/check across Experiments 1–5/5S, the tier-1 extension experiments E2–E6 and the exploratory attribution ablation | `tables_tex/tab_A-4.tex` | `eval/ta_verdicts_check.py` | `figures_thesis/tables_extra/TA_verdicts.pdf` |

Notes:
- Tables A.1-A.3 are rendered by their generator as images only; their LaTeX places the rendered page(s) (`figures/tab_A-*_p*.pdf`) in a table environment.
- Table A.4 is converted from `tables/TA_verdicts.md` (longtable).
- Labels: `tab:<n>` and `fig:<n>`, with `.` replaced by `-` (e.g. `tab:4-3b`, `fig:4-1b`, `tab:A-4`).
- The `.tex` files need `booktabs` (and `longtable` for Table A.4, `graphicx` for figures and Tables A.1-A.3); they were checked for balanced braces only (no TeX on the build machine).
