# Methodology source pack — index

This pack indexes the decisions, findings, rulings and open items that feed the
methodology chapter. Each entry gives a short factual summary, where the primary record
sits in the snapshot, the commit that introduced it (and the last material change where
that differs), and whether it is CURRENT or SUPERSEDED. The companion file
`numbers.md` lists the quotable values.

- **Snapshot:** `docs/thesis/export_2026-09-29_d89a902/{METHODOLOGY.md,PROGRESS.md,CLAUDE.md}`,
  identical to HEAD `d89a902` of `~/thesis_ws` (branch `fwd-camera`; checked with `diff`
  against `git show d89a902:<file>`).
- **Line ranges refer to the snapshot copy**, not to any later edit of the working files.
  "M" = METHODOLOGY.md, "C" = CLAUDE.md, "P" = PROGRESS.md.
- **Commit hashes** were found with `git log -S "<distinctive phrase>"` and
  `git log -L <range>` on `d89a902`. Several sections exist as cherry-pick twins on
  `fwd-camera` and `master`; the `fwd-camera` commit is cited first, with its twin in
  brackets. Sections authored on `master` reached `fwd-camera` through merges `54b9bce`
  (brings `9b0f5d9`) and `42d5ef2` (brings `cb4c845`, `a733654`). Commit `4d2cc6d` only
  restructured (moved) text and is never cited as an introduction or a material change.
- **Status:** CURRENT = the standing record. SUPERSEDED = replaced; the replacing entry is
  named. Several CLAUDE.md and PROGRESS.md sections are stale without carrying a
  SUPERSEDED marker of their own; they are marked SUPERSEDED (stale) here and the
  contradicting record is named.
- **Outside the snapshot:** `FGO_DESIGN.md` (§6, §9.4, §9.5) and
  `docs/partC_onboard_feasibility.md` are cited by the snapshot but are not part of it.
  They are referred to by commit only, with no line range.

---

## 1. Simulation setup

### 1.1 Corridor worlds (dsn): geometry, texture as the only variable
- **Summary:** Three 20 × 160 m corridor worlds (textured, blank, transition at y = 80 m)
  built from one template so floor texture is the only variable; walls, lighting and spawn
  identical. The later fix made all nine floor tiles visual-only with one
  `ground_collision` per world, and replaced the blank world's single plane with nine
  untextured tiles at the same poses, so the blank floor is rendered (not skybox).
- **Source:** C L91-L199 (original design text); C L1740-L1838 (Known Issue #11 fix and
  root cause); C L1839-L1880 (Known Issue #12 fix); P L397-L449 (session record).
- **Commit:** introduced `e2624ef` (C L91); collision/blank-floor fix `ba35071`; root
  cause `ef7673d`.
- **Status:** CURRENT for the fixed worlds (C L1740-L1880). **C L91-L199 is SUPERSEDED
  (stale, no marker):** it still says the worlds live in `~/ardupilot_gazebo/worlds/`, that
  `corridor_blank.sdf` is a single plane, and that neither world has flown end to end.
  Superseded by C L1740-L1880 and by vendoring (1.3).

### 1.2 Collision-plane finding (Known Issue #11)
- **Summary:** Eight coincident infinite `<plane>` collisions made `corridor_textured`
  run at RTF 0.0134. Making seven of eight tiles visual-only restored RTF to 0.3934
  standalone (29×), with all tiles still rendering. `gpu_lidar` raycasts the rendering
  scene, so collision stripping does not change the LiDAR. The earlier CPU-saturation
  attribution was wrong.
- **Source:** C L1740-L1838; P L480-L490.
- **Commit:** root cause `ef7673d`; fix verified `ba35071`; the superseded CPU attribution
  `5a32655`.
- **Status:** CURRENT. The "machine too slow" attribution (C L1827-L1838, the retained
  original investigation) is SUPERSEDED by the collision root cause (C L1779-L1826).

### 1.3 Vendored simulation assets and mesh provenance
- **Summary:** Worlds and custom floor/wall models are vendored in `sim/` and run from
  there, so a trial's `git_commit` pins the environment. Iris and runway meshes stay in
  `~/ardupilot_gazebo` (upstream base `082a0fe`); each trial records the live
  `ardupilot_gazebo_commit`. The nine `ds_*` trials predate vendoring; equivalence rests on a
  byte-identical diff plus one verify flight.
- **Source:** M L818-L846; C L45-L55.
- **Commit:** vendoring `7be3672`; METHODOLOGY/CLAUDE record `78da9a9`.
- **Status:** CURRENT.

### 1.4 Vehicle model `iris` and forward-camera variant `iris_fwd`
- **Summary:** `iris_fwd_standoffs` is a copy of `iris_with_standoffs` differing only by the
  inserted `forward_camera` block (downward camera, LiDAR and IMU byte-identical).
  Forward camera: 60° HFOV, 640 × 480, 30 Hz, mono, 0.15 m forward, level, far clip 200 m.
  Justified from corridor geometry and measured cruise attitude.
- **Source:** M L1310-L1341; C L227 (sensor status row).
- **Commit:** `c89d05a`; CLAUDE row last changed `294fcdc`.
- **Status:** CURRENT.

### 1.5 Forward-camera worlds: `_fwd` (line-textured walls), design decision
- **Summary:** `corridor_*_fwd` differ from the dsn worlds only by the world name,
  line-textured side walls (`corridor_wall_lined`, same collision box), a static end wall
  at y = 165 and the `iris_fwd` include. Walls are textured in all three worlds so the
  forward cue is identical across floor conditions. Texture v1 was too faint (render check)
  and replaced by v2.
- **Source:** M L1343-L1382.
- **Commit:** `c89d05a`.
- **Status:** SUPERSEDED (sky visible) by the ceiling worlds, M L2298-L2340. Kept on disk,
  not analysed further.

### 1.6 Textured walls reframed as the UPPER BOUND; plain-wall worlds `_fwdplain`
- **Summary:** The thesis is about featureless environments, so textured walls are the
  best case (upper bound) and no featureless claim is made from them. Plain-wall worlds
  (`corridor_wall` sides, plain end wall, no other change) were promoted from a deferred
  ablation to the main featureless case.
- **Source:** M L2128-L2140 (reframing); M L2142-L2171 (plain-wall design).
- **Commit:** `4855dcc`; worlds built `23d9423`.
- **Status:** The upper-bound framing is CURRENT. The `_fwdplain` worlds themselves are
  SUPERSEDED (sky visible) by `_fwdplainc`, M L2310-L2340.

### 1.7 Sky finding and the ceiling ruling (`_fwdc`, `_fwdplainc`)
- **Summary:** The render check showed a textured cloud skybox in ~46% of the forward
  frame height in every corridor world. Clouds at infinity are a near-ideal heading and
  yaw-rate cue that no real corridor has. Ruling (option a): a plain, non-shadow-casting,
  visual-only ceiling at z = 5 m added to both forward-camera datasets, so wall texture is
  the only difference between them.
- **Source:** M L2261-L2296 (finding); M L2298-L2308 (ruling); M L2310-L2328 (ceiling
  design); C L40 (key-path row).
- **Commit:** finding `2d50ab2`; ruling and design `f5f5db8`; worlds built `4a7ab90`.
- **Status:** CURRENT.

### 1.8 Supersession of `fwd_*`, `_fwd`, `_fwdplain` and check flights
- **Summary:** The `_fwd` and `_fwdplain` worlds, the `fwd_*` dataset and the check flights
  `p1_fwd_*` and `p1plain_*` are superseded because the forward view includes the sky. They
  are kept (`SUPERSEDED.txt`), not analysed further, and their Phase 1/2 results remain as
  the record of what was run. `fwd_tex_r1`'s Phase 5 flag is not carried across.
- **Source:** M L2330-L2340; M L1801-L1804; C L40.
- **Commit:** `f5f5db8`.
- **Status:** CURRENT (as the supersession record).

### 1.9 Trial harness: `run_trial.sh`, `fly_trial.py`, state-gated phases
- **Summary:** Headless single-trial harness (launch, fly, record, teardown) with every
  flight phase gated on measured state, never wall-clock sleep; `fly_trial.py` verifies
  `EXPECTED_PARAMS` live (eeprom gotcha). Forward-camera recording is opt-in and name-driven
  (empty-array mechanism leaves other worlds' command lines unchanged).
- **Source:** P L754-L779 (harness build); M L1384-L1396 (forward-camera opt-in);
  M L757-L762 (pinned and recorded parameters); C L1738 (RTF-aware discipline kept).
- **Commit:** `run_trial.sh` `f0fa64a`; `fly_trial.py` `0dae4f8`; `run_batch_trials.sh`
  `197c0ba`; forward-camera opt-in `c89d05a`.
- **Status:** CURRENT.

### 1.10 Resumable batch runner and crash handling
- **Summary:** `run_resumable_batch.sh` runs datasets in tmux with a per-trial log,
  DONE/FAILED markers and `ABORTED.txt` for partial trials, resuming on re-run. It was built
  after a kernel panic (rt2800usb Wi-Fi dongle → xhci NULL dereference). Datasets are flown
  interleaved; no commits during flights (after a provenance slip on `p1plain_*`). A trial
  that fails to record is re-flown once. Phase 4 uses the analogous
  `eval/run_jobs_resumable.sh`.
- **Source:** M L1857-L1863; M L2238-L2242; M L2233-L2234; M L2356; M L3000-L3002;
  C L74; P L98-L104.
- **Commit:** runner `7967a39`; CLAUDE row `8d31667`; job runner `938fdb6`.
- **Status:** CURRENT.

### 1.11 Flights on simulator truth (`AHRS_EKF_TYPE=10`) and its consequences
- **Summary:** `/ekf/pose` carried simulator truth, not EKF3, so Stage B/C ATEs compared
  truth with truth. Decision: keep `AHRS_EKF_TYPE=10` and evaluate EKF3 offline from
  `XKF1`, so no estimator shapes the trajectory; one fixed trajectory across conditions.
  Costs: no closed-loop stability claim; clock alignment between `TimeUS` and bag time. The
  2026-09-29 scope change keeps all current flights as offline observers and plans
  closed-loop flight.
- **Source:** C L805-L886 (§1, including the decision at C L852-L862 and costs at
  C L864-L886); M L1324-L1332; M L2844-L2849.
- **Commit:** `bdd7d5b`; last change `d89a902` (correction box).
- **Status:** CURRENT (decision). See 1.12 for the origin.

### 1.12 Origin of `AHRS_EKF_TYPE=10`: eeprom account vs SITL injection
- **Summary:** The 2026-07-22 audit attributed three unrecorded values, including
  `AHRS_EKF_TYPE=10`, to the gitignored `eeprom.bin`. The 2026-09-29 correction found in
  source that SITL itself injects it as a default: `SIM_JSON.cpp:410-413` calls
  `set_default_by_name("AHRS_EKF_TYPE", 10)` when the model sends `no_time_sync`, which our
  iris model does (`model.sdf:789`). Before any closed-loop run it must be set explicitly
  in a `.parm` file and confirmed from the PARM dump.
- **Source:** eeprom account C L791-L803; correction C L807-L815 and M L3084-L3091.
- **Commit:** eeprom account `bdd7d5b`; correction `d89a902`.
- **Status:** The **SITL-injection correction is CURRENT**. The eeprom account is
  qualified, not withdrawn: the correction says the value is "(also)" injected by SITL
  (M L3085-L3086), so eeprom as the *sole* source is SUPERSEDED.

### 1.13 Other hidden-configuration findings (GPS1_TYPE, compass, full param diff)
- **Summary:** `GPS1_TYPE=0` is needed to arm with no GPS fitted (arming check not
  disabled). `COMPASS_ENABLE=1` with `COMPASS_USE*=0` and `EK3_SRC1_YAW=0` is deliberate (an
  unconditional Copter compass-health arming gate). A full live-parameter diff (1379
  parameters, 16 differences, `SIM_FLOW_ENABLE` inert) shows the old configuration is
  fully enumerable. Standing rule: any live `PARAM_SET` goes into a `.parm` file the same
  session.
- **Source:** C L887-L937; C L797-L803.
- **Commit:** `bdd7d5b`.
- **Status:** CURRENT.

### 1.14 RTF: machine migration and live-lockstep RTF
- **Summary:** Migration to an i7-8700 + Quadro P620 desktop raised RTF from 0.05–0.17 to
  ≈0.86; after the collision fix the live-lockstep RTF on the corridors is 0.919 mean.
  Gazebo 8.11.0 → 8.14.0 was unavoidable. The state-gating discipline is kept.
- **Source:** C L984-L1005; C L1738; C L1752-L1765.
- **Commit:** `bdd7d5b` (environment table); `ba35071` (live-lockstep RTF).
- **Status:** CURRENT.

---

## 2. Estimators and shared inputs

### 2.1 EKF3 configuration: GNSS-denied sources (`gnss_denied.parm`)
- **Summary:** Flow as the only horizontal-velocity source (`EK3_SRC1_VELXY 5`,
  `FLOW_TYPE 5`, `EK3_FLOW_USE 1`), LiDAR height (`EK3_SRC1_POSZ 2`), no horizontal position
  source (`EK3_SRC1_POSXY 0`, dead reckoning), `EK3_SRC1_VELZ 0`, simulated GPS disabled.
  LiDAR injected as `RNGFND1` via `DISTANCE_SENSOR`; flow via `OPTICAL_FLOW` (message 100,
  not `OPTICAL_FLOW_RAD`, which this build drops). EKF3 derotates internally with its own
  gyro (`FLOW_OPTIONS=0`).
- **Source:** C L496-L590 (Stage C sources); C L284-L412 (Stage A flow fusion);
  C L229-L282 (LiDAR Stage 2); M L268-L280 (derotation code path).
- **Commit:** Stage C `3e48fe2`; Stage A `dfc2cda`; LiDAR `ea939ab`; derotation
  architecture `08bc2eb`.
- **Status:** CURRENT for the source configuration. The Stage B/C ATE/RPE figures in the
  same sections are VOID (C L416-L427, L557-L565).

### 2.2 EKF3 comparison configuration: nomag (`gnss_denied_nomag.parm`)
- **Summary:** `gnss_denied.parm` leaves EKF3 fusing the compass for yaw, a source the
  UKF/FGO cannot have. The three-way comparison therefore uses the `dsn_*` batch flown under
  `gnss_denied_nomag.parm` (`EK3_SRC1_YAW=0`, compass present but unused). Verified not
  fusing (`XKFS.MAG_FUSION=0`, `XKF2` mag states frozen). Datasets are labelled positively by
  a `yaw_source:` metadata block. `ds_*` is kept as the compass-active reference and noise
  floor.
- **Source:** M L848-L885; C L1280-L1328 (fix and verification); C L904-L918 (why
  `COMPASS_ENABLE=1`).
- **Commit:** params file `87ced37`; harness switched to nomag and dataset supersession
  `6f953b2`; results framing `4a023df`.
- **Status:** CURRENT per METHODOLOGY. **C L1280-L1300 and the C L66 key-path row (the
  "throwaway, not the baseline" label for `gnss_denied_nomag.parm`) are SUPERSEDED (stale)**
  by M L848-L873, which makes nomag the comparison configuration. The CLAUDE warning that
  nomag must not be folded into the standing baseline until EKF3's yaw drift is re-measured
  from `XKF1` (C L1329-L1344) is not marked closed in CLAUDE; M L875-L878 reports that
  measurement on `dsn_*` (`XKF1.Yaw` +6.6…+11.1 deg/min).

### 2.3 EKF3 prediction dt = 0.0125 s (80 Hz), not 400 Hz
- **Summary:** EKF3 accumulates five 400 Hz IMU frames and predicts on the total, so the
  prediction dt is 0.0125 s (derived, not logged). The UKF predicts at the same dt, so
  EKF3's `*_NSE` values transfer unchanged (scale factor 1).
- **Source:** C L592-L625.
- **Commit:** `ca120e6`.
- **Status:** CURRENT. Supersedes the 400 Hz / 50 Hz Q scaling (C L1214-L1245), see 6.5.

### 2.4 UKF implementation and configuration
- **Summary:** Euler 15-state UKF (position, velocity, roll/pitch/yaw, gyro and accel
  bias in EKF3's delta units), predicting at EKF3's 0.0125 s with EKF3's `*_NSE` values;
  measurement noise and gates matched to EKF3 (`FLOW_M_NSE` 0.25 rad/s, flow gate 300 → NIS
  9, `RNG_M_NSE` 0.5 m, range gate 500 → NIS 25, `FLOW_MAX` 2.5 rad/s); quality is a binary
  gate, not R-scaling. Lever arms: range `p_U − 0.12`, camera `p_U − 0.25`. Shared
  `h_flow`/`h_range` with the FGO.
- **Source:** C L1125-L1278 (design decisions); C L1922 (implemented: Euler 15-state,
  shared models, gated pseudo-yaw); P L273-L277.
- **Commit:** design `ce2a367`; last design change `ca120e6`; first UKF code `a19196a`.
- **Status:** Design decisions CURRENT. **The C L1125 header "confirmed, not yet
  implemented", the "no UKF code exists yet" text (C L1127-L1133) and the 9-state
  constant-velocity scaffold are SUPERSEDED (stale)** by C L1922 and M (UKF results
  throughout). The 400 Hz Q table inside it is superseded (6.5).

### 2.5 UKF pseudo-yaw cap: variance-gated to match EKF3
- **Summary:** The UKF fuses a zero-innovation yaw pseudo-measurement only when
  `P[6,6]+P[7,7]+P[8,8] > 0.04`, the exact Euler equivalent of EKF3's quaternion gate 0.01,
  checked three ways (Jacobian identity, EKF3 tilt variance, `XKV1` pinned under 0.01).
  Firing unconditionally was rejected because it improves ATE by doing something EKF3 does
  not do. The UKF fires ~1% because flow updates hold its yaw covariance below the gate.
- **Source:** M L887-L923.
- **Commit:** `9f0e2ff`; firing-rate section `ca4c474`.
- **Status:** CURRENT.

### 2.6 FGO implementation: GTSAM fixed-lag smoother, noise conversion
- **Summary:** GTSAM `BatchFixedLagSmoother` (iSAM2 unusable: `marginalizeLeaves` cascades on
  the Python flow `CustomFactor`). IMU preintegration noise converted from EKF3 as
  σ_c = NSE·√dt at dt = 0.0125 s (bias terms reach the same form once delta vs rate units
  are handled); `integrationCovariance` has no EKF3 counterpart (~1e-8·I); every 333 Hz
  sample is integrated, never decimated; `MakeSharedU(9.81)`.
- **Source:** C L723-L789 (noise conversion); M L704-L713 (solver); P L251-L259.
- **Commit:** noise conversion `ca120e6`; first FGO `8f44e6d`; solver/window `e79ab8e`,
  recorded `04426d2`. FGO_DESIGN §6 (outside the snapshot).
- **Status:** CURRENT.

### 2.7 FGO window 0.25 s: a declared configuration choice; LM iterations capped
- **Summary:** The pre-registered 1.0 s window took 96 ms/step, over the 33 ms
  deployability budget. The sweep {1.0, 0.5, 0.25} s selected 0.25 s as the largest window
  inside the budget; ATE is window-independent, so this is not selection for accuracy. LM
  is capped at 2 warm-started iterations, verified against full LM (RMS 0.029 m).
- **Source:** M L691-L713; P L251-L259.
- **Commit:** `04426d2`; restated on cruise `42193a5` (twin `17df652`).
- **Status:** CURRENT. **C L1923 ("batch used (~101 ms/step, 3–5× over the 33 ms
  budget)") is SUPERSEDED (stale)**; the 101 ms figure is the pre-window 1.0 s-era timing
  (M L1111-L1119), replaced by the 0.25 s configuration.

### 2.8 FGO yaw-anchor correction (fair zero-innovation anchor)
- **Summary:** The first FGO yaw prior anchored each keyframe to a fixed yaw, which
  accumulated into an absolute heading anchor and gave a void 0.49 m ATE. The corrected
  anchor ties each keyframe to its IMU-predicted yaw (zero innovation), matching EKF3's
  `fuseEulerYaw(PREDICTED)`. With it the FGO's yaw drifts at about −9 deg/min, on par with
  EKF3 on the same metric.
- **Source:** M L1019-L1047 (void artefact and retraction); M L1049-L1119 (fair-anchor
  result).
- **Commit:** code `c575baf`; METHODOLOGY `67ef203`; scale check `d0306d2`; cruise
  restatement `42193a5` (twin `17df652`). FGO_DESIGN §9.4 (outside the snapshot).
- **Status:** Fair anchor CURRENT. The fixed-anchor 0.49 m result is VOID (M L1024-L1037).

### 2.9 §9.5: UKF/FGO do not replicate EKF3's `const_pos`
- **Summary:** User ruling that the UKF and FGO dead-reckon on aiding loss rather than
  replicating EKF3's constant-position mode; a formulation difference, visible in the
  failure modes.
- **Source:** P L315-L316; M L566-L570. FGO_DESIGN §9.5 (outside the snapshot).
- **Commit:** `08d5c69`.
- **Status:** CURRENT, with the attribution qualified by OI-1 (9.1).

### 2.10 Shared inputs: IMU bridge at 333 Hz, MAVProxy bypass
- **Summary:** `/imu/data_raw` (`HIGHRES_IMU`, specific force, FRD → FLU) raised from 50 Hz
  to 333.27 Hz, the ceiling ArduPilot permits at `SCHED_LOOP_RATE=400` (not raised, as that
  would change EKF3). It runs on a dedicated SITL serial output (port 14556), bypassing
  MAVProxy, for headroom. Stream starts ~2.35 s after the others. Rectangular integration of
  instantaneous samples is a stated approximation for the UKF/FGO.
- **Source:** C L627-L721; C L783-L789 (standing caveat).
- **Commit:** `ca120e6` (bridge first added `8d2ff6e`).
- **Status:** CURRENT. **C L1055-L1123 ("Rate: 50 Hz", port 14555) and Terminal 11
  (C L1595-L1612) are SUPERSEDED (stale)** by C L627-L721.

### 2.11 Shared inputs: downward flow and LiDAR
- **Summary:** All three estimators receive identical raw, un-derotated flow
  (`flow_bridge.py` sends rates only) and the same LiDAR range; EKF3 derotates on the
  measurement side, the UKF/FGO inside `h_flow`. Flow processing (RANSAC, seed 42, focal
  length, derotation handling) is baked in at record time and cannot be varied from the
  bags. LiDAR at 30 Hz sim-time, verified sub-millimetre in hover.
- **Source:** M L268-L280; M L764-L781; C L1007-L1053; C L219-L227.
- **Commit:** architecture `5787b04`; baked-in record `257204d`; code-path record
  `08bc2eb`.
- **Status:** CURRENT.

### 2.12 Shared `h_flow` model and the interval-averaged gyro (FINDING 1–4)
- **Summary:** `h_flow` showed a roll-rate-coupled lateral residual. A sign flip was
  refuted by the re-run gate. The raw flow's rotational content is the gyro averaged over
  the frame interval (as EKF3 uses); feeding `h_flow` the interval-averaged gyro is the
  geometrically correct derotation. It degraded nomag UKF/FGO textured ATE because more
  lateral flow passes the EKF3-matched gate and leaks into yaw (~71% acceptance-driven); no
  admissible gate/R lever removes it. Applied by decision because it is correct and restores
  EKF3-consistent gating.
- **Source:** M L209-L456 (L237-L266 status and decision; L282-L307 FINDING 1;
  L309-L336 FINDING 2; L338-L347 FINDING 3; L349-L411 FINDING 4; L413-L425 metric arbiter;
  L448-L456 lateral/forward asymmetry).
- **Commit:** sign-flip revert `51aaeba`; correction applied `51e1bb9`; re-run gate and
  asymmetry `36cc78c`; cruise restatement `42193a5` (twin `17df652`).
- **Status:** Findings CURRENT. Their UKF/FGO tables were computed on receipt stamps and
  are pending the consolidated re-run (M L503-L509, L1159-L1161); see 6.7.

### 2.13 Empirical re-run gate (standing control)
- **Summary:** Every measurement-model, gate or noise change is gated on a from-scratch
  estimator re-run and reverted if the outcome degrades; offline residuals and innovation
  correlations are necessary but not sufficient. It caught two offline-evidenced changes.
- **Source:** M L427-L446.
- **Commit:** `36cc78c`; last change `42193a5` (twin `17df652`).
- **Status:** CURRENT.

### 2.14 Sensor noise and gyro drift: deterministic, single realisation
- **Summary:** All three estimators see one identical recorded sensor stream. SITL random
  noise is zeroed (`sim_noise.parm`); the only gyro error is SITL's deterministic
  triangle-wave drift (3.00 deg/min per minute, period 10 min). Robustness across drift
  realisations is out of scope (Term 3). Parameters are pinned, verified live and dumped to
  metadata.
- **Source:** M L715-L762.
- **Commit:** `257204d`; triangle-wave correction `51e1bb9`.
- **Status:** CURRENT. The earlier "constant drift" description is superseded by the
  triangle-wave correction (M L733-L742).

---

## 3. Fairness framework

### 3.1 Same bags, same inputs, each estimator correct on its own terms
- **Summary:** Fairness comes from each estimator consuming the same raw recorded inputs
  and being correctly implemented for its own architecture, not from identical
  preprocessing. EKF3 runs at literal ArduPilot defaults; the FGO window is declared as a
  config choice.
- **Source:** C L1007-L1053; M L715-L723; M L691-L697.
- **Commit:** `5787b04`; `257204d`; `04426d2`.
- **Status:** CURRENT.

### 3.2 IMU timestamp asymmetry (OI-2) and the dejitter ruling
- **Summary:** EKF3 integrates on true sensor time; the UKF/FGO replayed receipt stamps
  (0–9 ms scatter, mean exactly 3.0005 ms). Offline, sensor time helped the FGO (−6%) and
  had mixed effect on the UKF. Decomposition showed dejitter alone improves both robustly,
  while the 5–9 ms IMU-vs-flow shift is an estimator-dependent lever known only to ±5 ms.
  Adopted: dejitter only (linear fit to receipt stamps), through the re-run gate on all nine
  `dsn` bags. The sensor-time shift was not adopted.
- **Source:** M L1163-L1175 (opened); M L1206-L1247 (result); M L1249-L1284
  (decomposition); M L474-L501 (adopted baseline).
- **Commit:** opened `cc588df`; result `b9766d3`; decomposition `e7e22f9` (master record
  `9b0f5d9`, merged via `54b9bce`); correction code `cb4c845` and re-run `a733654` (merged
  via `42d5ef2`).
- **Status:** CURRENT (dejitter). Residual in 9.2.

### 3.3 Clock alignment: TimeUS vs sim time — bounded, not proven
- **Summary:** EKF3 TUMs come from dataflash `TimeUS`, UKF/FGO and the window from bag sim
  time. Instead of a formal alignment proof, the pinned window was shifted ±0.25 s and
  ±0.5 s on all nine bags: the largest change in evo -a (cruise) is 0.103 m (transition) and
  ≤ 0.015 m on textured, far below between-estimator gaps.
- **Source:** M L84-L102; C L874-L879.
- **Commit:** `42193a5` (twin `17df652`).
- **Status:** CURRENT (closed as "bounded, not proven").

### 3.4 SITL dataflash clock runs ~0.02% slow
- **Summary:** `TimeUS` differs from Gazebo sim time in rate as well as offset (SITL slow by
  0.016–0.022%; offset drifts from about −7 ms to about −60 ms over a flight). All
  TimeUS-to-bag comparisons use `eval/input_timing.py` `clock_map()` (offset and rate). The
  drift is inside the ±0.5 s bound. The earlier single-offset latency figures are superseded.
- **Source:** M L1177-L1204; C L880-L886.
- **Commit:** `b9766d3` (master record `9b0f5d9`); CLAUDE update `e7e22f9`.
- **Status:** CURRENT.

### 3.5 Latency standing rules
- **Summary:** The forward camera adds ~5–10 ms median flow → EKF3 latency (EKF3 only; the
  UKF/FGO replay on capture stamps). P2 latency is DIAGNOSTIC from Phase 2 on, because Phase
  5 compares arms on the same bags. Standing rule: EKF3 on forward-camera bags is never
  compared with EKF3 on `dsn_*` without stating the latency difference.
- **Source:** M L1737-L1758; M L1760-L1780; M L1782-L1799.
- **Commit:** re-check `b9766d3`; framing `e7e22f9`; ruling `b0f0fbf`.
- **Status:** CURRENT.

### 3.6 Ceiling-effect standing rule (transition forward flow)
- **Summary:** No comparison between the ceiling datasets and `dsn_*` on the transition
  world without stating the characterised effect (+0.43 px/s, +0.6%, p = 0.31, n = 8 + 8).
  It does not affect Phase 5 (same-bag arms).
- **Source:** M L2561-L2595.
- **Commit:** `60a1060`.
- **Status:** CURRENT.

---

## 4. Evaluation

### 4.1 Cruise window definition
- **Summary:** Defined once per trial from ground truth: horizontal speed smoothed by a
  centred 0.42 s moving average, criterion > 0.30 m/s, largest contiguous run; the same
  `[t0, t1]` is cropped from every estimator and reference.
- **Source:** M L30-L53; P L201-L206.
- **Commit:** `42193a5` (twin `17df652`).
- **Status:** CURRENT. Replaces the historical per-estimator windows (M L51-L53).

### 4.2 Threshold justification and sensitivity
- **Summary:** Hover ≤ 0.001 m/s and cruise floor 0.497 m/s, so any threshold between them
  selects the same segment; 0.30 m/s is 60% of commanded speed. The 0.42 s boxcar guards the
  largest-run rule against single-sample spikes. Thresholds 0.20 and 0.40 m/s move no
  conclusion.
- **Source:** M L55-L82.
- **Commit:** `26c46c1` (twin `df5c818`).
- **Status:** CURRENT.

### 4.3 SE(3) alignment: evo -a (Umeyama, no scale), fitted on cruise
- **Summary:** `evo_ape -a` (Umeyama SE3, no scale) is fitted over the cropped cruise span
  only. It removes the arbitrary yaw gauge that no-compass estimators carry, and keeps yaw
  drift.
- **Source:** M L47-L49; M L9-L15; M L636-L640.
- **Commit:** `42193a5` (twin `17df652`); rule `360a794`.
- **Status:** CURRENT.

### 4.4 STANDING RULE on metrics (label every ATE, never compare across metrics)
- **Summary:** Every ATE states its alignment and window: `evo -a`, unaligned, or apparatus.
  The primary cross-estimator metric is **evo -a (cruise)** from
  `eval/three_way_eval.py`; unlabelled figures are full-window, historical. Prompted by two
  near-misses (the "5× win" and the mixed-window table).
- **Source:** M L7-L28; C L1889-L1890 (Conventions).
- **Commit:** `360a794`; amended `42193a5` (twin `17df652`).
- **Status:** CURRENT.

### 4.5 Failure metrics on transition and blank
- **Summary:** Transition and blank are failure regimes where evo -a is not a quality
  metric; they are reported by displacement ratio (final displacement / true travel) and
  divergence onset (true y where the estimate departs ground truth by > 15 m), measured over
  the cruise window. Failure modes differ: EKF3 freezes, the UKF/FGO dead-reckon. Within
  EKF3 and the FGO the texture gradient survives on onset.
- **Source:** M L548-L570; M L626-L634.
- **Commit:** `e2b45bd`; last change `42193a5` (twin `17df652`).
- **Status:** Method CURRENT. EKF3 values CURRENT; UKF/FGO values are receipt-stamp and
  pending restatement (6.7).

### 4.6 Apparatus metric and why it is not the arbiter
- **Summary:** The apparatus metric (cruise, origin gauge-fixed, no yaw alignment) was used
  for the EKF3/UKF noise floor because `XKF1` is in the true NED frame. Under nomag it
  penalises the unobservable constant yaw offset; more flow improves apparatus ATE while
  worsening evo -a. evo -a arbitrates because it keeps yaw drift, the real failure, and
  because metrics must not be mixed.
- **Source:** M L413-L425; M L11-L15.
- **Commit:** `51e1bb9`; `360a794`.
- **Status:** CURRENT.

### 4.7 ATE window audit
- **Summary:** Every quoted ATE was checked for its window and, where needed, re-run from
  its original commit, reproduced on the full window, then restated on cruise. Every
  qualitative conclusion survives. Not restated: the full-LM trajectory (never stored), the
  void 0.49 m artefact, apparatus figures and Stage B/C.
- **Source:** M L104-L129; M L527-L546 (the mixed-window table found by the Phase 0 gate).
- **Commit:** `42193a5` (twin `17df652`); gate finding `4c25091` (twin `3a271cf`).
- **Status:** CURRENT.

### 4.8 n = 3 caveat: ranges are not a noise floor
- **Summary:** With three repeats, a fourth run falls outside the observed range with
  probability 2/(n+1) = 50%. The ranges describe the data and do not bound it. A `dsn` evo -a
  (cruise) noise floor is open.
- **Source:** M L131-L134.
- **Commit:** `42193a5` (twin `17df652`).
- **Status:** CURRENT.

### 4.9 Phase 0 reproducibility gate and smoke test
- **Summary:** One committed script regenerates every published figure before building on
  it; this caught the mixed-window table. The pre-registered smoke test `p0_smoke_tex`
  reproduced the `dsn_*` pipeline end to end.
- **Source:** M L136-L177; M L539-L546.
- **Commit:** `42193a5` (pre-registration, twin `17df652`); result `94fa543` (twin
  `759faf8`).
- **Status:** CURRENT.

### 4.10 Run-to-run noise floor on `ds_*` (compass-active, apparatus metric)
- **Summary:** n = 3 per condition on the compass-active `ds_*` batch, `XKF1`-vs-`SIM`,
  apparatus metric: within-condition ATE range 2.81–10.90 m against ~68 m between
  conditions; cross-track noisy, along-track reproducible. **This is not the `dsn` evo -a
  noise floor**, which is still open (9.4).
- **Source:** M L783-L816.
- **Commit:** `f29d614`.
- **Status:** CURRENT as a `ds_*` apparatus characterisation only.

### 4.11 Filter consistency (overconfidence) result
- **Summary:** Against their own ±3σ, EKF3 and (much more) the UKF are overconfident in the
  weakly observable directions (horizontal position, heading), the textbook FEJ/OC
  symptom. n = 1, `dsn_tex_r1`. NEES would quantify it; FGO covariance never logged.
- **Source:** M L179-L207.
- **Commit:** `6953e74`.
- **Status:** Finding CURRENT; the UKF percentages are receipt-stamp and pending the
  consolidated re-run (M L1159-L1161).

### 4.12 Current textured baseline (dejittered)
- **Summary:** On evo -a (cruise), EKF3 and the FGO are indistinguishable at n = 3; the UKF is
  ~3.4× worse and unstable across repeats. The fine EKF3–FGO ordering flips under the IMU
  timestamp variants, so no ordering between them is claimed.
- **Source:** M L474-L501.
- **Commit:** `a733654` (merged via `42d5ef2`).
- **Status:** CURRENT. Supersedes the receipt-stamp table (M L511-L525) and the
  mixed-window table (M L527-L546).

### 4.13 Yaw leak: capping frequency, not parameterisation
- **Summary:** A flow_x residual partitions 69% velocity / 31% yaw identically in the Euler
  UKF and SO(3) FGO; the yaw behaviour is set by how often each estimator caps yaw variance.
  After the `h_flow` correction the partition and capping attribution survive; the UKF's
  near-physical drift coincidence does not. The gyro-z bias is effectively unobservable
  under no yaw for all three.
- **Source:** M L925-L984; M L648-L666; M L668-L689.
- **Commit:** `8f44e6d`; re-checked `51e1bb9`.
- **Status:** CURRENT (findings). The earlier Euler-vs-quaternion attribution
  (`9a6527a`) is SUPERSEDED by M L958-L975. Ramp-tracking UKF/FGO numbers pending the
  consolidated re-run.

### 4.14 Lateral drift: EKF3 east-velocity bias is yaw rotation (CLOSED)
- **Summary:** EKF3's +0.194 m/s east-velocity bias on `dsn_tex_r3` is ~74% heading-driven
  (body-forward velocity rotated by drifted yaw); the flow measurement is unbiased and the
  gate reduces innovation bias. A ~26% residual is uncorrelated with yaw and not pursued.
  This is the basis of the forward-camera hypothesis.
- **Source:** M L986-L1017; M L1288-L1308.
- **Commit:** `0cfdd69`.
- **Status:** CURRENT (closed).

---

## 5. Pre-registration rules

### 5.1 PRE-REGISTRATION RULE: primary vs diagnostic, band margins
- **Summary:** Each criterion is labelled PRIMARY (tests the confound) or DIAGNOSTIC
  (reported, never a gate); no band uses the bare observed range, each states its margin and
  basis; only primary criteria can stop a phase. Prompted by two zero-margin band errors in
  forward-camera Phase 1.
- **Source:** M L1121-L1132.
- **Commit:** `cc588df` (master record `9b0f5d9`).
- **Status:** CURRENT.

### 5.2 STANDING RULE: scope control (two questions)
- **Summary:** Before any work outside the phase brief ask (a) does it change a thesis claim,
  (b) would a reviewer's objection stand without it; if both are no, log one line in the
  open-items list and move on. Diagnostics are reported, not investigated on the spot.
- **Source:** M L1134-L1143.
- **Commit:** `a733654` (merged via `42d5ef2`).
- **Status:** CURRENT.

### 5.3 Revised Phase 1 criterion (tests the confound directly)
- **Summary:** RTF was a proxy. After the RTF failure, diagnosis and a throttled direct test,
  the criterion became P1 input timing, P2 flow → EKF3 latency (one EKF3 step, 12.5 ms), P3
  downward-flow conditions and P4 outcome, with stated margins; RTF, receive rates and the
  IMU gap share became diagnostic. Stated openly as revised after failures.
- **Source:** M L1660-L1701; M L1468-L1643 (the failures and diagnosis); M L1645-L1658
  (gap-share ruling).
- **Commit:** `cc588df`; failures `2d3bcd1`, `e37fd46`, `0f3e8c1`.
- **Status:** CURRENT, with P2 made DIAGNOSTIC from Phase 2 (3.5). The single-offset P2
  limits (≤ 23.4 / ≤ 55.2 ms) are SUPERSEDED by the linear-map limits (M L1762-L1765).

### 5.4 Phase 2 criteria: FGO bands rebased on the dejittered baseline
- **Summary:** P1, P3 and P4 (EKF3 and FGO) are primary, judged per trial; the FGO's textured
  band uses a 0.40 m floor equal to its measured IMU-timing sensitivity. P2, RTF, rates, the
  UKF and degraded-world evo -a are diagnostic. Interleaved flight order.
- **Source:** M L1813-L1853.
- **Commit:** `3a960ed`.
- **Status:** CURRENT (reused for Phase 2b, the ceiling checks and ceiling datasets).

### 5.5 IMU gap rule (2026-09-24) and its extension (receipt bunch, ≥ 10 s)
- **Summary:** Original rule: a gap (> 10 ms step in `/imu/time_ref` sensor time) before
  arming → replay starts after it; after arming → bag unusable for UKF/FGO, EKF3 still scored.
  Extended rule: an irregularity is a gap or a receipt bunch (> 25 ms displacement from the
  receipt-vs-sensor linear map, the dejitter guard's own limit); a pre-arm trim is allowed
  only if ≥ 10 s of stationary data remains before arming.
- **Source:** original M L1955-L1989; applied M L2013-L2040; extension M L2457-L2488.
- **Commit:** original `061facc`; applied `9f2fa40`; extension `15b960c`; extension
  implemented and applied `2f3dbf1`.
- **Status:** The **extended rule is CURRENT**; the original rule is SUPERSEDED by it
  (M L2457-L2458), with earlier verdicts unchanged (M L2484-L2485).

### 5.6 Keep-and-record rule for primary misses (selection bias)
- **Summary:** A primary miss is reported, not re-scored or waived; bags are excluded only
  for an input defect; a poor estimator result alone never excludes a bag, because doing so
  would be selection bias; post-arm IMU gaps give n = 2 with no re-flight.
  Applications: `fwd_tex_r1` (FGO P4 miss, kept after a one-hour bounded check found no
  defect); `p1c_fwdplainc_trans` (P3 miss; decision rule ≥ 2/3 dataset fails → stop; 0/3
  failed → run-to-run variability); `fwdc_trans_r1` (P3 miss, run-to-run variability, effect
  size characterised).
- **Source:** M L1991-L2011 (Ruling 1); M L2042-L2090 (bounded check); M L2092-L2116 (kept);
  M L2223-L2234 (handling fixed for Phase 2b); M L2384-L2389; M L2441-L2456 (p1c Ruling 1);
  M L2534-L2539 (applied); M L2561-L2595 (`fwdc_trans_r1`).
- **Commit:** `061facc`; `9f2fa40`; `22eee2a`; `4855dcc`; `15b960c`; `9fd5610`; `60a1060`.
- **Status:** CURRENT. `fwd_tex_r1`'s Phase 5 flag is not carried to the ceiling datasets
  (M L2339-L2340).

### 5.7 Batched baseline corrections
- **Summary:** The OI-2 dejitter re-run is the current `dsn` baseline; further corrections
  are batched into one consolidated re-run before the results chapter, not restated one at a
  time. Dejitter applies to all new data from Phase 2.
- **Source:** M L1145-L1161.
- **Commit:** `a733654` (merged via `42d5ef2`).
- **Status:** CURRENT.

---

## 6. Baseline corrections

### 6.1 IMU rate 50 → 333 Hz
- **Summary:** 50 Hz aliased a real 35 Hz `acc_z` tone to 15 Hz; at 333 Hz aliased energy
  falls 8.7×. See 2.10.
- **Source:** C L629-L666; C L685-L702.
- **Commit:** `ca120e6`.
- **Status:** CURRENT. 50 Hz figures and the VIBE-based magnitude are SUPERSEDED
  (C L668-L683).

### 6.2 EKF3 prediction dt and Q transfer
- **Summary:** See 2.3. Predicting at 0.0125 s removes any NSE rescaling.
- **Source:** C L592-L625; C L1214-L1245.
- **Commit:** `ca120e6`.
- **Status:** CURRENT.

### 6.3 `h_flow` correction: interval-averaged gyro
- **Summary:** See 2.12. Applied to both UKF and FGO through the shared
  `FlowFrameGyroAverager`; the sign flip stays reverted. Bundled with the PHYS_DRIFT
  correction (triangle wave, not constant 9.8).
- **Source:** M L237-L266.
- **Commit:** `51e1bb9`.
- **Status:** CURRENT.

### 6.4 FGO yaw-anchor correction
- **Summary:** See 2.8.
- **Source:** M L1049-L1119.
- **Commit:** `c575baf`; `67ef203`.
- **Status:** CURRENT.

### 6.5 400 Hz / 50 Hz Q scaling table
- **Summary:** Assumed EKF3 predicted at 400 Hz and rescaled NSE for a 50 Hz UKF predict,
  making bias terms 11.18× too small.
- **Source:** C L1205-L1245.
- **Commit:** original `ce2a367`; superseded `ca120e6`.
- **Status:** SUPERSEDED by 2.3 (C L592-L625). "Use neither column" (C L1245).

### 6.6 IMU dejitter (OI-2)
- **Summary:** See 3.2. Implementation reproduces the offline `oi2dj` control exactly on all
  three textured bags.
- **Source:** M L474-L501; M L1249-L1284.
- **Commit:** `cb4c845`; `a733654`.
- **Status:** CURRENT.

### 6.7 Tables not yet restated on the dejittered baseline (batched)
- **Summary:** Deferred to the consolidated re-run: transition and blank evo -a and failure
  metrics; the FINDING 2 and 4 tables; the gyro-z ramp-tracking table; the consistency
  percentages. Dejittered transition/blank values exist in
  `eval/results/dsn_dejitter_baseline.json` but are not interpreted in METHODOLOGY.
- **Source:** M L1159-L1161; M L503-L509.
- **Commit:** `a733654`.
- **Status:** CURRENT (as the pending list).

---

## 7. Forward camera

### 7.1 Hypothesis
- **Summary:** A forward camera supplies an absolute heading cue relative to the corridor
  (vanishing point) and, through horizontal forward flow, gyro-z bias observability; the
  heading-driven share of lateral drift (74%) should fall and the 26% residual stay roughly
  unchanged. Tested in Phase 5 within each estimator, arms on the same bags.
- **Source:** M L1288-L1308.
- **Commit:** `c89d05a`.
- **Status:** CURRENT, except that the test bags are now the ceiling datasets, not `fwd_*`
  (M L1801-L1804).

### 7.2 Phase 1 (forward-camera confound checks) — record
- **Summary:** The forward camera costs ~20% RTF, all of it once the image is bridged (CPU in
  `gz sim`); a throttled direct test showed RTF itself leaves inputs, latency and outcome
  within tolerance. All three `_fwd` worlds pass the revised criterion.
- **Source:** M L1398-L1735.
- **Commit:** `c89d05a`; `2d3bcd1`; `e37fd46`; `0f3e8c1`; `cc588df`; `6bb1586`.
- **Status:** SUPERSEDED-but-recorded (sky visible; M L2330-L2337). The infrastructure note
  (one camera ≈ 40% of a core, ≈ 20% RTF; test input timing directly) remains CURRENT
  (M L1654-L1658).

### 7.3 Phase 2 `fwd_*` dataset — record
- **Summary:** 9/9 flown; P1 and P3 pass 9/9; P4 8/9 with the recorded `fwd_tex_r1` FGO miss
  (kept); IMU-gap rule applied to `fwd_trans_r1` and `fwd_trans_r3`.
- **Source:** M L1855-L2126.
- **Commit:** `8d31667`; `061facc`; `9f2fa40`; `22eee2a`.
- **Status:** SUPERSEDED-but-recorded (M L2330-L2337).

### 7.4 Plain-wall Phase 1 and Phase 2b pre-registration — record
- **Summary:** `p1plain_*` passed every primary criterion but the batch was held on the sky
  finding. Phase 2b handling rules (miss reporting, defect-only exclusion, n = 2 on post-arm
  gap, one re-flight for recording failures) carried into the ceiling datasets.
- **Source:** M L2173-L2259.
- **Commit:** `4855dcc`; `2d50ab2`.
- **Status:** Results SUPERSEDED-but-recorded; the Phase 2b plan is superseded by the ceiling
  pre-registration (M L2342); its handling rules are CURRENT through M L2384-L2389.

### 7.5 Ceiling check flights (Phase 1c) and ceiling datasets
- **Summary:** Six check flights: render check passes (no sky); one P3 miss
  (`p1c_fwdplainc_trans`); the `p1c_fwdc_trans` receipt bunch led to the extended IMU rule.
  Datasets: 18/18 flown in 140.9 min; `fwdplainc` 9/9 pass; `fwdc` 8/9 with the recorded
  `fwdc_trans_r1` P3 miss; 3 bags trimmed, none unusable. These are the Phase 3–5 datasets.
- **Source:** M L2342-L2389 (pre-registration); M L2391-L2437 (Phase 1c); M L2439-L2488
  (rulings); M L2490-L2559 (datasets); M L2597-L2604 (complete).
- **Commit:** `f5f5db8`; `b5f1080`; `15b960c`; `2f3dbf1`; `9fd5610`; `60a1060`.
- **Status:** CURRENT.

### 7.6 Phase 3 measurement method (frozen)
- **Summary:** Heading from an LSD + RANSAC vanishing point (ψ = atan((u_vp − cx)/fx)),
  per-frame confidence = balanced two-sided support, "no measurement" below S_MIN (also the
  end-wall dropout). Three priors (VP inside the image, VP within ±5° of the horizon row,
  balanced two-sided scoring) were added after failures on calibration frames, stated
  openly. Yaw rate from median horizontal LK flow in a box around the previous VP; residual
  parallax is a stated, unremoved bias. No ground truth inside the pipeline.
- **Source:** M L2606-L2658.
- **Commit:** `6f290e8`.
- **Status:** CURRENT.

### 7.7 Calibration / validation split and frozen parameters
- **Summary:** Calibration on the six `p1c_*` flights only, by a pre-registered selection
  rule; validation on the 18 dataset bags with no re-tuning. Frozen: inlier tolerance 0.5°,
  S_MIN 200 px, box half-size 80 px, N_MIN 5. Ground truth is used for evaluation only; the
  flights test bias/noise/availability at near-zero heading and yaw rate, not the response.
- **Source:** M L2660-L2718; M L2720-L2752.
- **Commit:** pre-registration `6f290e8`; calibration `f4462b6`.
- **Status:** CURRENT.

### 7.8 Phase 3 validation results and static sweep
- **Summary:** Heading validated on 15/18 bags (all textured-wall bags; plain walls on blank
  and transition floors); fails with plain walls over the checkerboard floor (floor aliasing
  outvotes the junctions). Yaw rate validated only with textured walls (9/9; plain 0/9). The
  static-response bar passes in 1/6 worlds and stands as failed: confident wrong VPs near the
  end wall.
- **Source:** M L2754-L2827.
- **Commit:** `e67b3ff`.
- **Status:** CURRENT.

### 7.9 Transition segment breakdown (checker vs blank halves)
- **Summary:** Per-segment (y < 80 checker, y > 80 blank) heading and yaw-rate statistics for
  the six ceiling transition bags. Committed with the Phase 4 code; not written up.
- **Source:** METHODOLOGY: NOT FOUND. Only `eval/results/fwd_transition_segments.json`
  (script `eval/fwd_transition_segments.py`).
- **Commit:** `938fdb6`.
- **Status:** CURRENT (diagnostic; not written up in the snapshot).

### 7.10 Phase 4 pre-registration: arms, noise, gate, FGO covariance recursion, timing
- **Summary:** UKF and FGO only (EKF3 fixed baseline). Arms: `fwdc` baseline / +heading /
  +heading+yaw rate; `fwdplainc` baseline / +heading; 90 replay runs. Baseline arm must
  reproduce existing trajectories byte for byte. Validity is measurement-intrinsic only (no
  ground truth, position or world knowledge in gating). Models: h_ψ = yaw (wrapped), h_ω =
  interval-averaged gyro-z − bias. Noise from static-sweep residuals (σ_ω derived by the
  sweep/flight inflation, flagged for the user). Identical χ² gate ν²/S ≤ 9; the FGO gets a
  gate-only filtering covariance recursion. Timing is diagnostic only.
- **Source:** M L2924-L3011.
- **Commit:** pre-registration `2e23099`; code `938fdb6` (implemented σ and gate at
  `src/estimators/measurement_models.py:146-152`, matching the pre-registration).
- **Status:** CURRENT (pre-registered). **Results: none in the snapshot; the replays were
  running at the time of writing.** The byte-identical baseline claim appears only in the
  `938fdb6` commit message; the snapshot records no regression result.

---

## 8. EKF3 heading ruling, ArduPilot findings, scope change, Part C

### 8.1 Supervisor scope change (2026-09-29)
- **Summary:** Real indoor mocap flights in scope; UKF/FGO ideally onboard as EKF3 drop-ins;
  forward camera flown only once verified in sim. Consequences: the Python estimators are the
  reference implementations; offline Phases 4–5 are the sim verification; all future flights
  log with `LOG_REPLAY=1` and `LOG_DISARMED=1`.
- **Source:** M L2829-L2852; P L8-L28; C L1951.
- **Commit:** `294fcdc`.
- **Status:** CURRENT.

### 8.2 EKF3 ruling: option 3 (fixed no-yaw-source baseline)
- **Summary:** EKF3 is the fixed no-yaw baseline; only UKF/FGO get forward arms. Live
  injection (option 2) rejected: separate-run latency confound and the `VISO_YAW_M_NSE`
  floor. Re-record with `LOG_REPLAY=1` + `REPH` (option 1) deferred until after Phase 5, and
  to be revisited under the onboard plan. Phase 5 tests the prediction within the UKF and
  within the FGO; no claim is made about EKF3 with heading.
- **Source:** M L2854-L2922; M L1801-L1811.
- **Commit:** `294fcdc`.
- **Status:** CURRENT. The earlier Phase 4 note assuming ArduPilot Replay (`b0f0fbf`) is
  SUPERSEDED by M L1806-L1811.

### 8.3 ArduPilot findings behind the ruling
- **Summary:** One downward optical-flow backend only (a forward camera is not a second flow
  sensor for EKF3). ExternalNav yaw exists but each message needs a position, and yaw error
  is clamped to at least `VISO_YAW_M_NSE` (default 0.2 rad, range 0.05–1.0 rad). No EKF3 input
  for external yaw rate. Recorded logs have `LOG_REPLAY=0`, `LOG_DISARMED=0` and no DAL
  records, so Replay is impossible on them.
- **Source:** M L2878-L2912.
- **Commit:** `294fcdc`.
- **Status:** CURRENT, extended by 8.4 (the 5° floor).

### 8.4 ExternalNav yaw floor of 5° inside `writeExtNavData`
- **Summary:** `NavEKF3_core::writeExtNavData` sets `yawAngErr = MAX(angErr, radians(5))`,
  on top of the `VISO_YAW_M_NSE` clamp. Replay `REPH` records enter through the same
  function, so injected heading cannot bypass it: EKF3 cannot be told heading is better than
  5°, against the UKF/FGO's 0.13–0.15°.
- **Source:** M L3093-L3099.
- **Commit:** `d89a902`.
- **Status:** CURRENT. Answers one open item of option 1 (M L2872-L2874).

### 8.5 Supervisor answers (2026-09-29)
- **Summary:** One firmware build preferred; real flights are the main result (SITL-only as a
  fallback only); offline comparison stays with less weight; target STM32H743 on an
  ArduPlane quadplane in multirotor mode; UKF onboard as EKF3 drop-in; FGO may run with GTSAM
  on a companion if shown working and beating EKF3 in a clear case. Part C adjusted, item 9
  interpretation (NEES/consistency) pending user confirmation.
- **Source:** M L3013-L3039; P L29-L37.
- **Commit:** `8dff5e1`.
- **Status:** CURRENT.

### 8.6 Part C onboard feasibility summary
- **Summary:** UKF onboard feasible on the H743 for Copter and QuadPlane (estimates); FGO
  off-board via ExtNav means EKF3 re-filtering the FGO (IMU double-counted, 5° floor); no
  companion External-AHRS backend; companion compute needs C++ ports; no existing trial is
  replayable; under SIM, failsafes never fire; candidate fair FGO advantages are distance
  scale and consistency/NEES. Effort ~18–30 person-weeks (estimate).
- **Source:** M L3041-L3082; full report `docs/partC_onboard_feasibility.md` (outside the
  snapshot).
- **Commit:** `d89a902`.
- **Status:** CURRENT (figures are estimates).

---

## 9. Open items

### 9.1 OI-1: FGO blank-floor failure mode changed with the `h_flow` correction
- **Summary:** Pre-correction, the FGO froze on blank (ratio 0.06/0.18/0.04); corrected, it
  dead-reckons at 1.58–1.64×. Hypotheses: H1 gating decides what reaches velocity; H2
  near-zero flow read as motion. Must be resolved (half-day box) before the failure-mode
  write-up; the attribution of dead-reckoning to §9.5 alone is qualified meanwhile.
- **Source:** M L572-L624; M L1154-L1155.
- **Commit:** `26c46c1` (twin `df5c818`); flagged `42193a5`.
- **Status:** CURRENT (open).

### 9.2 OI-2 residual: sensor-time IMU shift not adopted
- **Summary:** True sensor time (`/imu/time_ref`, recorded from Phase 2 on) could replace the
  dejitter in the consolidated re-run if ruled; not usable on `dsn_*` without
  reconstruction.
- **Source:** M L1156-L1158; M L1276-L1284; M L1925-L1927.
- **Commit:** `a733654`.
- **Status:** CURRENT (open).

### 9.3 Clock alignment: bounded, not proven
- **Summary:** See 3.3 and 3.4. No formal proof; bounded by the ±0.5 s sensitivity check and
  the rate-aware clock map.
- **Source:** M L84-L102; M L1190-L1194; C L874-L886.
- **Commit:** `42193a5`; `b9766d3`.
- **Status:** CURRENT (closed as "bounded, not proven"; a stated limitation, not a proof).

### 9.4 `dsn` evo -a (cruise) noise floor
- **Summary:** n = 3 ranges are not a noise floor; a `dsn` noise floor is open. Linked to the
  `fwd_tex_r1` ruling (run-to-run variability in an unobservable state).
- **Source:** M L131-L134; M L2105-L2108.
- **Commit:** `42193a5`; `22eee2a`.
- **Status:** CURRENT (open).

### 9.5 Unexplained EKF3 vs FGO velocity-scale difference
- **Summary:** On `dsn_tex_r1` the FGO inherits a +4.7% velocity scale against EKF3's +12.6%
  from the same flow; the smaller inheritance is unexplained and not leaned on (n = 1).
  Part C quotes distance scale EKF3 +6–10% against FGO ~+1% (n = 9) as a candidate
  advantage.
- **Source:** M L1097-L1104; M L3078-L3080; C L1923.
- **Commit:** `d0306d2`; `d89a902`.
- **Status:** CURRENT (open).

### 9.6 Lateral-drift 26% residual
- **Summary:** ~0.05 m/s of EKF3 east-velocity bias uncorrelated with yaw error, source not
  established; logged as "not worth further investigation" but the forward-camera
  hypothesis predicts it stays unchanged.
- **Source:** M L1005-L1011; M L1302-L1304.
- **Commit:** `0cfdd69`.
- **Status:** CURRENT (open, not being worked).

### 9.7 iSAM2 cascade root cause
- **Summary:** The incremental solver cascades after ~590 keyframes; isolated to the GTSAM
  incremental marginalisation with the Python `CustomFactor`, not root-caused.
- **Source:** M L1111-L1119; M L704-L707.
- **Commit:** `67ef203`; `e79ab8e`.
- **Status:** CURRENT (open; batch used instead).

### 9.8 `fwd_tex_r1` heading-drift cause
- **Summary:** The miss localises to larger UKF/FGO heading drift on identical IMU input; the
  cause was not found in the one-hour box and is not investigated further.
- **Source:** M L2085-L2090.
- **Commit:** `9f2fa40`.
- **Status:** CURRENT (open; by ruling not pursued; the dataset is superseded).

### 9.9 Ceiling-world transition forward flow
- **Summary:** 2 of 8 ceiling transition flights exceed the ±2% band against 0 of 8 without a
  ceiling; the characterised effect is not distinguishable from zero; the blank half is more
  variable under the ceiling. Recorded as a fact, mechanism not investigated.
- **Source:** M L2541-L2595.
- **Commit:** `9fd5610`; `60a1060`.
- **Status:** CURRENT (open; a standing caveat, 3.6).

### 9.10 Phase 4/5 items awaiting results or rulings
- **Summary:** Phase 4 results (running); the σ_ω derivation flagged for the user
  (M L2975); option 1 (`REPH`) deferred; Part C item 9 interpretation to be confirmed;
  `AHRS_EKF_TYPE` and time sync to be settled before any closed-loop run; forward heading near
  the end wall must be treated with suspicion or gated (M L2817-L2820), left to intrinsic
  confidence and the χ² gate in Phase 4 (M L2949-L2951).
- **Source:** M L2965-L2975; M L2865-L2877; M L3036-L3039; M L3090-L3091.
- **Commit:** `2e23099`; `294fcdc`; `8dff5e1`; `d89a902`.
- **Status:** CURRENT (open).

### 9.11 Known Issues still open in CLAUDE.md
- **Summary:** #2 drone shadow contaminates downward flow; #3 ArduPilot-to-ROS timestamp sync
  (sim time resolved; now handled offline by the clock map, 3.4); #5 LiDAR dropouts under
  aggressive attitude (harmless while `EK3_RNG_USE_HGT=-1`); #13 intermittent
  `PARAM_REQUEST_READ` loss (5× retry mitigation). #1 is deferred indefinitely; #6 motivates
  the corridors. Shadow rejection is listed as remaining in C L1913.
- **Source:** C L1728-L1881 (#2 L1731, #3 L1732, #5 L1734, #13 L1881).
- **Commit:** list `ce2a367`; #11/#12 closed `ba35071`.
- **Status:** CURRENT (open) for #2, #3, #5, #13. **P L1072-L1124 ("Known Issues (open)") and
  P L993-L1025 ("Next Priorities") are SUPERSEDED (stale):** they still list the corridor
  worlds as unflyable (#11), low RTF (#6) and the Stage C ATE gap (#9), all resolved or void in
  C L1738-L1880 and C L416-L427.

### 9.12 Velocity as a second experimental axis
- **Summary:** Commanded velocity (0.25–1.0 m/s) is a planned robustness axis; flow error grows
  with speed (~+7.8% to ~+12.5%), treated as an expected condition, not a defect. All datasets
  so far are at 0.5 m/s.
- **Source:** C L1925-L1938.
- **Commit:** `5787b04`.
- **Status:** CURRENT (open; planned, not yet run).
