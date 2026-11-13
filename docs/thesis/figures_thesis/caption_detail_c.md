# Caption detail removed by the restyle (stage C)

Material removed from reader-facing captions during the 2026-11-13 figure restyle (common brief: "Restyle the
thesis figures only", item 7 - captions become plain 2-4 sentences, with everything removed from the previous
caption kept here verbatim). One block per figure, headed `## <figure id>: caption detail`.

## Figure 3.1: caption detail

Scope: `eval/figs_thesis_methods.py`, `fig_architecture()`. The previous (2026-11-02 restyle) caption read, verbatim:

> Sensors (left) reach ArduPilot's flight controller through MAVLink bridges (flow, range, and the
> external-navigation (ExtNav) path for the camera heading or a tag) and reach the UKF and FGO through recorded
> ROS 2 topics. Which estimator flies is set by AHRS_EKF_TYPE: simulator truth in Experiments 1A, 1B, 2, 3 and 4
> (open loop; EKF3 runs live but passively, the UKF and FGO are replayed offline), and EKF3, the UKF port or the
> FGO in Experiments 1C, 5 and 5S (closed loop; the others run in shadow). The FGO runs outside ArduPilot as a
> node whose state an in-firmware output predictor (AP_NavFGO) propagates. In simulation every process ran on
> one desktop; the companion computer (Pi) is planned and its timing is estimated. Two safety watchers: the
> simulation watcher used in Experiments 1C, 5 and 5S, and the real-hardware watcher, tested only on the SITL
> bench.

The 2026-11-13 pass replaced this with 4 plain sentences (no experiment-id enumeration, no `AHRS_EKF_TYPE` or
`AP_NavFGO` named, no file/script names). Nothing beyond the quote above was removed from the caption body.
