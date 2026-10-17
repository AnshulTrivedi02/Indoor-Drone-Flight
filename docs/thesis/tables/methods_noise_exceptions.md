# Table 3.3. Documented exceptions to noise and treatment parity, with their rulings

Every documented place where the noise or the treatment differs between estimators, with the ruling that covers it. Two code differences (5, 6) have no ruling in the record and are reported, not resolved.

| # | item | difference | ruling / status | source |
|---|---|---|---|---|
| 1 | flow/range fusion rate | EKF3 fuses flow at 15.1 Hz and range at 16 Hz; the UKF and FGO at 30 Hz with the same σ | EKF3 design under D18; results state that the UKF and FGO fuse ~2× the information per second | M:12338; ruling M:12359 |
| 2 | forward heading offline (1B) | only the UKF and FGO receive the camera heading; EKF3 none | EKF3 is the fixed no-yaw-source baseline (VISO_YAW_M_NSE floor; LOG_REPLAY=0) | ruling M:2884-2888 |
| 3 | closed-loop heading σ (1C) | all three at 5°; the camera's own σ (0.148°) is not usable by EKF3 | 5° is ArduPilot's floor (VISO_YAW_M_NSE 0.05); the UKF port applies the same 5° (D17) | M:4896; ruling M:7553 |
| 4 | GTSAM integrationCovariance | FGO only, 1e-8 (no EKF3 counterpart) | documented asymmetry (a conditioning floor); no separate ruling found | M:9528; FC:31 |
| 5 | FGO flow/range gating | no flow or range NIS gate in the FGO code (only a 4.2 rad/s flow clamp); EKF3 and the UKF gate at 3σ / 5σ and 2.5 rad/s | NO RULING FOUND; recorded where it mattered (short LiDAR returns taken by the FGO) | FC:184; M:8659; M:8884; design FGO_DESIGN.md:446 |
| 6 | FLOW_MAX sidedness | the UKF rejects \|flow\| ≥ 2.5 rad/s (two-sided); the design document describes EKF3's test as signed and one-sided | NO RULING FOUND | UC:293; AP_NavUKF.cpp:874; FGO_DESIGN.md:420 |
| 7 | ground-proximity flow rule (D15) | EKF3's rule (flow zeroed and still fused below 0.5 m before take-off) applied to the UKF and FGO | a sensor-validity rule, shared (not tuning) | ruling M:7038; M:7060 |
| 8 | EKF3's pre-arm yaw-bias learning | EKF3 learns gyro-z bias on the ground; not given to the UKF or FGO | D18 principle: design features are not copied; a caveat on the no-heading closed loop only | M:7785-7792; PROGRESS.md:47 |
| 9 | EKF3 range median-of-3, tilt cut, floor | EKF3 only | EKF3 design, not copied (D18) | M:8871 |
| 10 | UKF offline predict period and process noise (D27) | offline UKF steps 15.00 ms; its process noise is scaled to EKF3's per-second densities | ruled: same per-second densities as the FGO and the UKF port | M:9567; N:186 |
| 11 | FGO initial uncertainty | corrected to yaw 1°, roll/pitch 5° (the UKF's); flown FGO results used 1e-3 rad / 2°; EKF3 keeps 0.1 rad | a MODEL CORRECTION under D18 (initial-uncertainty correction); EKF3's 0.1 rad is its design | ruling M:12857-12862; N:36 |
| 12 | FGO biasAccOmegaInt | was diag(0.2², 0.043633²): extra IMU white noise (gyro ~26×, accel ~5× looser); set to 0 | a MODEL CORRECTION under D18 (sensor-noise error) | ruling M:12046; M:12052; FC:35 |
| 13 | UKF Cholesky jitter | both builds added 1e-12·I to P before every Cholesky; now jitter is added only if the factorisation fails (ladder 0, 1e-12, 1e-9, 1e-6) | a MODEL CORRECTION under D18 | M:12329; ruling M:12343; UC:57 |
| 14 | UKF flow derotation | the UKF derotates flow with the bias-corrected rate | a MODEL CORRECTION, not a copied design feature | ruling M:11366 |
| 15 | lateral optical-flow sign | the lateral flow sign was wrong in EKF3's input and in the UKF/FGO model; fixed for all | a finding, fixed in every estimator before the consolidated re-run | M:4069; M:4155; N:213 |
| 16 | flow validity | every estimator accepts flow on the same binary validity flag (feature count), no R-scaling | D22: flow validity uses the feature count only | M:8936; FGO_DESIGN.md:424 |
| 17 | IMU gap rule | replays of the UKF and FGO start after / exclude IMU gaps; EKF3 (live) is still scored | ruling (2026-09-24), extended | M:1985; M:2487 |
| 18 | tag-fix gating (Exp. 2–5) | EKF3 gates tag fixes (position 5σ, yaw 3σ, bypassed after a 10 s timeout); the UKF and FGO do not gate them | pre-registered; validity is the shared tag rule (sensor validity under D18) | M:10066; M:10134; M:11613 |
| 19 | GNSS on return (Exp. 4) | the UKF and FGO fuse the GNSS samples EKF3 received, ungated, and on return simply resume (no reset or variance inflation); EKF3 behaves by its own design | EKF3 design, not copied (D18); no gate as in Exp. 2 | M:10336; M:10337 |
| 20 | FGO: no yaw reset at the first heading | the FGO fuses the first heading with no reset | design feature, not copied (D18) | M:8043 |
| 21 | robust heading weighting | Cauchy kernel, k = 2.385, in the robust FGO only (H1.4, H1.7) | calibrated on the calibration bags, as pre-registered | M:8281 |
| 22 | drift band per estimator (H5.5) | the UKF's band is 2× the others' | pre-registered | M:10691 |

*Source abbreviations: M = METHODOLOGY.md; N = docs/thesis/numbers.md (content-frozen); V = docs/thesis/thesis_vocabulary.md; UC = src/estimators/ukf_core.py; MM = src/estimators/measurement_models.py; FC = src/estimators/fgo/fgo_core.py; FN = src/estimators/fgo/fgo_node.py; CN / CC = src/estimators/fgo_cpp/src/fgo_cpp_node.cpp / fgo_core.cpp; AP_NavUKF.cpp, AP_NavFGO.h, AP_AHRS.* and GCS_Common.cpp are in the thesis ArduPilot fork ~/ardupilot_ukf (ukf-jitter-fix @ f30f6ffa2f); AP_NavEKF3*.cpp/.h are in the pinned ArduPilot ~/ardupilot (7bac20cbcc). Parameter files are at the repository root. Every file:line is verified by the generator against a verbatim needle (index_methods.md).*

*D-numbers are the decision-queue rulings (docs/decisions_queue.md); the thesis text describes each ruling instead of citing its number (vocabulary §8.2).*

<!-- generated by eval/figs_thesis_methods.py (commit 337c931); no number recomputed. Sources verified and cross-checks: docs/thesis/figures_thesis/index_methods.md, Table 3.3. -->
