# E5: UKF with tag landmark states, design (no code yet)

**Extension experiment, pre-registered.** This is the design that `preregistration.md` §4 points to.
- **Status: SIGNED OFF 2026-10-22, with amendments** (METHODOLOGY.md on `fwd-camera`, heading "SIGN-OFF (user,
  2026-10-22): extension experiments Stage 1 accepted with amendments; Stage 2 authorised"). Written 2026-10-21 against
  `c1dd6ee`; amended 2026-10-22. No code has been written and nothing has been run.
- **Amendments applied here:**
  - **Amendment 5:** how the FGO anchors its frame, and why tag 0's treatment matches it (§5); why dropping
    finished-pass landmarks in no-LC is equivalent to the FGO's no-LC arm (§6.1).
  - **Amendment 2:** the known-map validation is a numerical tolerance against the stored Experiment 2 UKF tracks, not
    byte identity (§8).
  - **Decision:** the design choices of §10 are accepted, subject to amendment 5. They are marked DECIDED.
- **Correction (2026-10-22, found while writing amendment 2).** The draft §7 said the smoother gain is solved by a plain
  Cholesky of P⁻. `ukf_core.rts_smooth` (`ukf_core.py:172-186`) solves it on the **diagonally scaled (correlation)**
  matrix, because P⁻ spans about 1e-14 (the delta-form bias states) to about 1 (yaw). The unscaled solve is
  ill-conditioned (the T_D_r1 note in that function). E5 uses the same scaling (§7), which is needed to reproduce the
  stored RTS track (§8).
- **Labelled:** "UKF with tag landmarks (loop closure)", a separate estimator from the thesis UKF. It mirrors the
  Experiment 3 keyframe FGO (`lc_fgo_replay.py`), cited at `c1dd6ee` lines.

## 1. Code layout and rules

- **New modules only:**
  - `src/estimators/ukf_lm.py`: the variable-size UKF core;
  - `src/estimators/lc_ukf_replay.py`: the harness;
  - `src/estimators/test_ukf_lm.py`: synthetic unit tests.
- **No file covered by the checksum guard may be edited** (`preregistration.md` §6). That includes `ukf_core.py`,
  `measurement_models.py`, `room_ukf_replay.py` and `imu_timing.py`.
  - `ukf_core` cannot simply be reused for the augmented state, because its sigma points, mean and residual use the
    module-global `N` = 15 (`ukf_core.py:61-108`).
  - `ukf_lm.py` therefore re-implements those three functions for a variable n. For the vehicle block it **calls**
    the unchanged `ukf_core._process`, `measurement_models.h_flow_pose` / `h_range`, `ukf_core.make_params` and
    `init_state`, so the vehicle model is the thesis UKF's, not a copy.
- **Output:** `~/thesis_data/tier1/<trial>/lc_ukf_{lc,nolc}_t245/{live.tum, hindsight.tum, stats.json}`, through
  `tier1_paths.resolve_out` (the same refusal rules as the FGO tools). It is scored by `l_score.py --prefix lc_ukf`.
- **Validation output (§8):** `~/thesis_data/tier1/<trial>/lc_ukf_val_{world,knownmap,augmented}/{ukf_live.tum,
  ukf_rts.tum, stats.json}`. The file names are those of the stored `room_ukf/`, so each pair is compared row for row.

## 2. Inputs and timing (as Experiment 3, and as the Experiment 2 UKF)

- **Bag topics:** `/imu/data_raw`, `/optical_flow/measurement`, `/downward_lidar/range`, `/attitude/angular_rates`,
  and `/tags/raw`.
  - `/tags/raw` uses every central-third detection, with the same rule and constants as lc_fgo_replay.py:45, :69-79.
  - The tag measurement is the vehicle (x, y, yaw) in the tag frame, from `tag_measure.vehicle_pose` with the tag at
    the origin (:78-79).
- **The same IMU gap rule, dejitter, predict period and ground-proximity flow rule as `room_ukf_replay.py`:**
  - `apply_gap_rule` and `dejitter_imu` (:105);
  - `DT_STEP` = ceil(0.0125 / period) · period (:106-107);
  - the flow derotation with the bias-corrected gyro average (:149-159).
- **Cut at anchor + 245 s**, as Experiment 3 (lc_fgo_replay.py:216).
- **Live** = the state after each predict step, from the anchor on (room_ukf_replay.py:145, :182-185).

## 3. State vector and augmentation on first sighting

- **Vehicle block:** the thesis UKF's 15 states (`measurement_models.N`):
  - p (3), v (3) and Euler angles (3; indices 6–8, angle states);
  - gyro bias and accel bias, both in delta units.
- **Landmark j:** 3 states [x_j, y_j, ψ_j], the tag pose on the floor plane in the gauge (tag 0) frame. The
  flat-floor assumption is the same as Experiment 3's (lc_fgo_replay.py:12-13): tag z, roll and pitch are known.
  - ψ_j is an **angle state**. It is added to the angle-index set used by the sigma-point mean (circular mean) and the
    residual (wrapped), exactly as indices 6–8 are in `ukf_core._state_mean` / `_state_residual`.
- **Order:** landmarks are appended in order of first sighting.
- **Index book-keeping:** a dict `tag_or_pass → slice`. Removal is described in §6.
- **Augmentation at the first sighting of a non-gauge landmark, at time t with measurement z = (m_x, m_y, m_ψ):**
  - (a) Inverse model, identical to the FGO's `lm_from` (lc_fgo_replay.py:108-110):
    - ψ_L = wrap(ψ_v − m_ψ);
    - p_L = p_v − R(ψ_L) [m_x, m_y].
  - (b) Unscented augmentation with **cross-covariance**:
    - form the joint vector [x; w] with w ~ N(0, R_tag);
    - draw sigma points of dimension n + 3;
    - push each through g(x, w) = [x; inverse(x, z + w)];
    - take the weighted mean (circular for ψ_L) and the covariance.
    - This gives P_LL and the cross block P_xL = cov(x, L) consistently, with no Jacobian.
  - (c) The new landmark's own measurement is NOT fused again at this instant. Its information is already in the
    initial covariance, exactly as the FGO's first factor and initial value carry it once. This rule avoids double
    counting the first measurement and is stated as a design rule.
- **Later sightings** of that landmark (or of the pass, in no-LC) are standard updates (§4).

## 4. Measurement model, noise and updates (matched to the FGO's tag factor)

- **Model:** h(x) = vehicle (x, y, yaw) in landmark j's frame. It is the same as the FGO landmark factor's
  `err + meas` (lc_fgo_replay.py:83-90):
  - h_x = c·dx + s·dy;
  - h_y = −s·dx + c·dy;
  - h_ψ = wrap(ψ_v − ψ_j);
  - with dx = p_vx − x_j, dy = p_vy − y_j, c = cos ψ_j and s = sin ψ_j.
- **Noise:** R = diag(0.05², 0.05², (5°)²). These are the same constants as the FGO tag factor:
  `measurement_models.TAG_SIGMA_POS`, `TAG_SIGMA_YAW` (`measurement_models.py:356-357`), used at
  lc_fgo_replay.py:123.
- **No gate,** as both the FGO landmark factor and the Experiment 2 UKF `update_tag` (`ukf_core.py:188-195`) have none.
- **No robust weighting.**
- **Update form:** one joint 3-D unscented update per detection.
  - The innovation's yaw component is wrapped: wrap(z_ψ − ẑ_ψ), with ẑ_ψ the circular mean over the sigma points.
  - The Experiment 2 UKF uses sequential scalar updates (x, y, then yaw through `update_heading`). For the
    known-landmark validation (§8), the E5 code also has a **sequential-scalar mode** that applies the same three
    scalar updates in the tag frame.
  - The validation gate is run in that mode, and the result runs use the same mode. This is a design choice (§10.4).
  - With a fixed landmark, x and y in the tag frame are linear in the state, so the unscented transform is exact, and
    the rotated sequential updates equal the world-frame ones up to round-off.
- **Several detections in one camera frame** (different tags) are applied sequentially in bag order, as the FGO adds
  them as separate factors on one keyframe.

## 5. Anchor and gauge: how the FGO anchors its frame, and the matching UKF treatment (amendment 5)

### 5.1 How the Experiment 3 FGO anchors its frame (`lc_fgo_replay.py` at `c1dd6ee`)

1. **Before the anchor** the FGO is the thesis FGO, unchanged: `FGO(window=0.25, kf_dt=1/30, lm_maxiter=2)`,
   initialised by `fgo.init` (:114-119). Its yaw cap applies only here.
2. **Anchor time.** The first central detection of the gauge tag (`--gauge-tag`, default 0; :40) at bag time `tt`
   calls `start_isam(tt, d)` (:230-233). `t_anchor = tt` (:151). Stored values: 28.546 / 28.975 / 28.744 s on
   T_A_r1 / r2 / r3 (`T_A_r*/lc_fgo_{lc,nolc}_t245/stats.json:t_anchor`; identical in both modes).
3. **Anchor pose: a re-anchor to the measured pose, held by a loose prior** (`start_isam`, :133-151).
   - The state is that of the newest fixed-lag keyframe (`fgo.prev_pose`, `prev_vel`, `prev_bias`, covariance
     `C = fgo.cov_prev`; tangent order [roll, pitch, yaw, x, y, z], then velocity, then the biases;
     `fgo_core.py:116-138`).
   - **Pose** := roll and pitch kept, yaw := the measured yaw, (x, y) := the measured (m_x, m_y), z kept (:137-138).
   - **Velocity** rotated by the yaw change d = wrap(m_ψ − ψ) (:137, :139). Bias kept (:139).
   - **Priors on X(0), V(0), B(0), all DIAGONAL** (:141-148):
     - pose σ = [√C_roll, √C_pitch, **0.5 rad (yaw)**, **1.0 m (x)**, **1.0 m (y)**, √C_z] (:141; the code comment
       says "loose x, y, yaw on the state prior (the gauge comes from the gauge-tag prior + this first measurement)");
     - velocity σ = √diag(R₃ C_vv R₃ᵀ) (:142);
     - bias σ = √diag(C_bb) (:142).
   - Every cross-correlation of the fixed-lag covariance is dropped (diagonal priors).
4. **The frame (gauge) comes from two factors, not from the loose prior:**
   - **the gauge prior** on L(0): mean (0, 0, 0), isotropic σ = **1e-4** (:199-201). It is inserted when the first
     tag-0 detection is processed;
   - **the anchoring detection itself, used ONCE**, as an ordinary landmark factor X(1)–L(0) with σ = 0.05 m, 0.05 m,
     5° (`tags_pend = [d]`, :233; factor at :204). It is attached to the next keyframe, up to 1/30 s after X(0).
5. **Effective anchor uncertainty** (the loose prior combined with one use of the measurement against an origin held
   to 1e-4):
   - σ_xy = (1/1.0² + 1/0.05²)^−½ = **0.04994 m** (against 0.05 m);
   - σ_ψ = (1/0.5² + 1/(5°)²)^−½ = **4.93°** (against 5°);
   - the loose prior's mean is the measurement, so it adds **0.25%** of the measurement's information in x and y, and
     **3.0%** in yaw. The FGO therefore uses the anchoring detection about 1.0025 times in x, y and 1.03 times in yaw.
6. **The gauge prior is effectively exact (stored evidence).** `landmarks_final["0"]` in all six stored
   `T_A_r*/lc_fgo_{lc,nolc}_t245/stats.json` lies within **4e-10 m and 4e-10 rad** of the origin (largest component
   −3.5e-10, T_A_r3 LC yaw). That is with 577–653 tag-0 factors at σ 0.05 m pulling on it. In information terms, the
   prior is 1/(1e-4)² = 1e8 against at most 653/0.05² ≈ 2.6e5 from the factors, a ratio of about 380:1.
7. **After the anchor:** the retained-history iSAM2 (QR), no yaw cap (M:10468), no pseudo-yaw.

### 5.2 The landmark UKF's anchor and tag 0 (matches §5.1)

| | Experiment 3 FGO (§5.1) | E5 landmark UKF | match |
|---|---|---|---|
| before the anchor | thesis FGO, fixed-lag, yaw cap | thesis UKF (`room_ukf_replay.py` loop, :122-181), predict, flow, range and the zero-innovation pseudo-yaw | each estimator's own thesis configuration, as in Experiment 2 |
| anchor event | first central tag-0 detection in `/tags/raw`, `t_anchor = tt` | the same detection, `t_anchor = tt` | identical; checked: `t_anchor` must equal the stored FGO value per flight (invariant, §5.3) |
| x, y, yaw at the anchor | set to the measurement (loose prior mean) | set to the measurement by `measurement_models.reanchor_jacobian` (`measurement_models.py:364-375`), as `room_ukf_replay.py:176` | identical mean |
| velocity | rotated by the yaw change | rotated by the yaw change (`J[3:5,3:5] = Rz`) | identical |
| roll, pitch, z, biases | kept, with their own variances | kept, with their own variances | identical form |
| cross-correlations | dropped (diagonal priors) | dropped: P ← diag(J P Jᵀ) (`room_ukf_replay.py:177`) | identical form |
| x, y, yaw uncertainty after the anchor | 0.04994 m, 4.93° (item 5) | **exactly 0.05 m, 5°** (P set to the tag noise, :177) | equivalent: 0.12% in σ_xy and 1.5% in σ_ψ |
| use of the anchoring detection | once as a factor (plus 0.25% / 3% from the loose prior's mean) | once, as the re-anchor; **not fused again** (as `room_ukf_replay.py:175-178`, and §3c for other landmarks) | equivalent; no double counting in either |
| gauge (tag 0's pose) | L(0) prior σ 1e-4; stored final L(0) within 4e-10 of the origin | tag 0 held **exactly** at (0, 0, 0) and **not augmented** | equivalent: the prior is about 380× stronger than all tag-0 factors together, and the stored L(0) did not move measurably |
| later tag-0 sightings, LC | factor X(k)–L(0) | sequential-scalar update against the fixed origin (§4) | equivalent (a 1e-4 m landmark σ adds (1e-4/0.05)² = 4e-6 to the innovation variance) |
| later tag-0 passes, no-LC | new free landmark per pass; only the first pass gets the gauge prior (:172, :199) | new augmented landmark per pass; only the first (anchor) pass uses the fixed origin | identical rule |
| timing of the anchoring measurement | applied at the next keyframe, up to 33 ms after the detection | applied to the state of the last predict, up to 15 ms before it | **stated difference**, the same as between the Experiment 2 FGO and UKF; not new to E5 |
| after the anchor | no yaw cap | pseudo-yaw stops (`room_ukf_replay.py:142`) | identical |

**Why tag 0 is held exact rather than put in the state with a 1e-4 prior: equivalence.** The FGO's prior on L(0) is
about 380× stronger than all its tag-0 factors together (item 6), and the stored final L(0) stayed within 4e-10 of the
origin in all six runs. So the FGO's gauge tag behaved as exactly known. Holding it exact in the UKF is the matching
treatment, and it is not an approximation that changes the numbers measurably. (Numerical conditioning is NOT the
reason: P⁻ already carries bias variances of about 1e-14 (§7), and V-E5c augments landmarks at 1e-10.)

### 5.3 Invariants (a failure stops E5 before scoring) and checks on every E5 result run

- `t_anchor` equals the stored FGO value of the same flight (28.546 / 28.975 / 28.744 s), to the bag stamp.
- **Landmark (pass) count** equals the stored FGO count: **8** in LC and **41** in no-LC (the gauge pass included),
  on each of T_A_r1–r3 (`stats.json:landmarks`).
  - The FGO applies the pass rule at **keyframe times**: `landmark_key(tid, t)` is called inside `isam_keyframe` with
    t = the keyframe time (:196-197), not the detection time.
  - E5 therefore runs a **book-keeping keyframe clock**: t_init + k/30, advanced by IMU events exactly as
    lc_fgo_replay.py:242-258. Each detection is labelled with the keyframe time it would be attached to, and the pass
    rule (> `PASS_GAP_S` = 1.0 s since the last sighting) uses those labels. The measurement itself is applied at its
    own time (§4). Without this, a pass boundary near 1.0 s could split or merge differently, and 41 could drift.
- **Reported (not a stop):** the count of tag measurements used from the anchor on, against the stored
  `landmark_factors` (2145 / 2057 / 2038). The anchoring detection counts once (the re-anchor). Detections still pending
  when the FGO's loop breaks at the cut (:216-217) were never factors, and E5 excludes them the same way. Any mismatch is
  explained in `numbers_tier1.md` before the run is scored.

## 6. Re-identification: LC and no-LC

- **LC:** one landmark per tag id. A later sighting of id j updates the existing landmark j: re-identification is a
  loop closure through the cross-covariance. This mirrors lc_fgo_replay.py:170-176 with `--mode lc`.
- **no-LC:** a NEW landmark per **pass**. A pass ends after more than `PASS_GAP_S` = 1.0 s without a sighting of that
  id (lc_fgo_replay.py:44, :172; M:10478-10479), on the keyframe time base of §5.3. This includes tag 0's later
  passes:
  - in no-LC, its later passes are new free landmarks, as in the FGO, where only the first gets the gauge prior (:199);
  - the first tag-0 pass after the anchor uses the fixed origin.
- **Finished-pass landmarks are removed from the state (no-LC only).** A landmark whose pass has ended is marginalised
  out (its rows and columns deleted). §6.1 gives the equivalence argument and its one approximation.
  - It bounds n at 15 + 3 × (passes open at once), instead of 15 + 3 × 40.
  - In LC every landmark is kept: n ≤ 15 + 3 × 7 = 36.

### 6.1 Why dropping finished-pass landmarks is equivalent to the FGO's no-LC arm (amendment 5)

**What the FGO's no-LC arm does.** `landmark_key` (lc_fgo_replay.py:170-176) creates a new key L(j) when a tag id has
not been seen for more than 1.0 s. A finished pass's L(j) **stays in the iSAM2 graph** (no marginalisation; retained
history). But by construction it **never receives another factor**: any later sighting of the same id makes a new
key. After its pass, L(j) is connected only to the keyframe poses X(k) of that pass, through that pass's 3-D factors.

**What information L(j) carries after its pass.** Its factors say: during the pass, the vehicle poses were rigidly
consistent with one fixed but unknown tag pose. Eliminating L(j) turns them into **relative-pose constraints among the
poses of that pass only**. There is nothing about any other time, and nothing absolute, because L(j) is free. (The one
exception is the gauge pass, whose landmark is the fixed origin, and which is not dropped in either estimator.)

**Live estimate (filter).**
1. The UKF's live estimate at time t is the vehicle block of the filtered state.
2. While the pass is open, the landmark's sightings act on the vehicle through the cross-covariance P_xL. That is
   exactly how the within-pass relative constraint reaches the vehicle.
3. When the pass closes, everything L(j) has told the vehicle is already in the vehicle marginal (x_v, P_vv) and in
   its correlations with the other open landmarks. Marginalising L(j) out of a Gaussian leaves every other marginal and
   cross-covariance unchanged.
4. L(j) is never observed again. In a linear-Gaussian filter, keeping it would therefore never change the vehicle's
   estimate: the update gain on the vehicle block depends only on the vehicle rows of P, because H has zeros in L(j)'s
   columns. L(j) would only be dragged along through its correlation.
5. **So the live vehicle estimate with L(j) dropped equals the one with L(j) kept**, exactly in the linear-Gaussian
   case.

**How the FGO's live estimate compares.** In the FGO, the retained L(j) still constrains only past poses (those of
its pass). Whatever the FGO's live estimate gains from keeping it can come only through **relinearisation**: iSAM2
revisits those past poses when later factors move their linearisation points. That is not a consequence of dropping
landmarks. The same filter-versus-graph difference is present in every comparison of the UKF and FGO in this thesis,
LC and Experiment 2 included, and it is the quantity E5 measures. The drop removes no information the filter could use
live.

**The one approximation: the unscented transform depends on n.**
- `ukf_core._sigma_points` scales the spread by √(n + λ) = α√n (κ = 0) and sets the weights from n (:61-89). Removing
  3 dimensions changes n, so the sigma points and weights of the vehicle block change.
- **Why this is small:** the scaled unscented transform matches the mean and covariance of a nonlinear map to second
  order whatever n is. Only third- and higher-order terms change with n.
- With α = 1e-3 the vehicle sigma points sit about α√n × σ ≈ 0.005σ from the mean. The higher-order terms therefore
  scale with (α√n)² ≈ 2e-5 relative to the second-order ones.
- **How it is handled:** stated as an approximation. It is NOT a difference between E5's arms, because the LC arm's n
  also changes (augmentation). The V-E5c gate (§8) tests the analogous effect of a changing n on the vehicle estimate,
  with landmarks augmented into the state.

**Hindsight (RTS) track.**
- Removal is an explicit **selection transition** x⁺ = S x, with D = P Sᵀ and P⁻ = S P Sᵀ (§7). The RTS backward pass
  through such a node recovers the dropped landmark's smoothed estimate from its filtered cross-covariance with the
  rest of the state.
- In the linear-Gaussian case, this is the exact RTS smoother of the same model with L(j) kept to the end with an
  identity transition, zero process noise and no further measurements. The smoothed vehicle track is therefore the
  same either way.
- **Approximation:** the RTS uses the forward pass's statistical linearisations (D, P⁻), with the n-dependent sigma
  sets above. It is a single pass at the filter's linearisation points.
- **What differs from the FGO's no-LC hindsight:** the FGO uses iSAM2's full-graph estimate after 5 extra updates
  (DEVIATION, M:10557). It relinearises every variable that is over the threshold, the retained L(j) included. That is
  the same difference as between RTS-UKF and the batch FGO in Experiment 2. It is the filter-versus-graph difference,
  not an effect of the drop.
- **Reporting:** the E5 no-LC hindsight is labelled "RTS over the filter's linearisation" wherever it is set beside the
  FGO's no-LC hindsight. The amendment 1 secondary comparison ("RTS vs batch") maps to the FGO's Experiment 3
  hindsight, iSAM2 plus 5 updates. That mapping is stated wherever the comparison is reported.

## 7. RTS hindsight over a state that changes size

- **Node chain:** from the anchor on, one node per predict step, as in the Experiment 2 UKF (room_ukf_replay.py:136-139,
  :188-195). Each node stores:
  - the filtered (x, P) before the predict;
  - the predicted (x⁻, P⁻);
  - the cross-covariance D = cov(x_k, x⁻_{k+1}) from the unscented predict.
- **Dimension changes are explicit transition nodes:**
  - **Augmentation (§3):** a node with transition g. Its D = cov(x, [x; L]) = [P, P_xL] comes from the same unscented
    augmentation, and its "predicted" (x⁻, P⁻) is the augmented mean and covariance.
  - **Removal (no-LC):** a selection transition x⁺ = S x, with D = P Sᵀ and P⁻ = S P Sᵀ.
- **The backward pass** uses the general (rectangular) gain G_k = D_k (P⁻_{k+1})⁻¹. It is solved exactly as
  `ukf_core.rts_smooth` does (`ukf_core.py:172-186`): on the **diagonally scaled (correlation) matrix** P⁻/(s sᵀ), with
  s = √diag(P⁻) clipped at 1e-300, by a linear solve, never an explicit inverse. P⁻ spans about 1e-14 (the delta-form
  bias states) to about 1 (yaw), so the unscaled solve is ill-conditioned (the T_D_r1 note in that function).
  Corrected 2026-10-22: the draft said a plain Cholesky solve.
  - Each step uses: x_k^s = x_k + G_k (x_{k+1}^s ⊟ x⁻_{k+1});
  - and: P_k^s = P_k + G_k (P_{k+1}^s − P⁻_{k+1}) G_kᵀ.
  - ⊟ wraps the angle states (vehicle Euler angles and landmark ψ).
  - This is the same recursion as `ukf_core.rts_smooth` (`ukf_core.py:172-186`), generalised to rectangular blocks.
- **Memory:** with LC (n ≤ 36), the per-node storage of P, P⁻ and D is ≤ 31 kB. Over about 19,500 nodes
  (245 s / 12.5 ms) that is about 0.6 GB, held in RAM; the machine has 15 GB.
  - With no-LC (n ≤ about 21), it is smaller.
  - If measured memory exceeds 4 GB, nodes are written to `np.memmap` files under the run's tier-1 directory, and this
    is stated in `stats.json`.
- **Hindsight track:** the smoothed vehicle pose at every node, written as `hindsight.tum`.

## 8. VALIDATION: a HARD gate before any E5 result counts (amendment 2)

The ruling requires that, with a known map, the new code reproduces the existing Experiment 2 UKF result. Amendment 2
sets how that is judged:
- **Byte identity** applies only to unchanged code paths. For the UKF that is the frozen Experiment 2 replay
  (`room_ukf_replay.py`, gate G0-UKF).
- **The new landmark-UKF code** is judged against the stored Experiment 2 UKF tracks with the pre-registered numerical
  tolerance below. The tolerance applies to every V-E5 gate.

### 8.1 The stored reference (compared directly; V-E5 gates are never chained through one another)

- **Live:** `~/thesis_data/trials/T_{A,B,C,D}_r{1,2,3}/room_ukf/ukf_live.tum` (12 files).
- **Hindsight:** `~/thesis_data/trials/T_{A,B,C,D}_r{1,2,3}/room_ukf/ukf_rts.tum` (12 files).
- **Also used:** `room_ukf/stats.json` keys `t_anchor` and `n_tag_fused`.
- **Format:** TUM, written at 6 dp, so 1 µm position precision (`room_ukf_replay.py:78-82`). For example, T_A_r1 has
  17,272 rows from 28.553746 to 287.674086 s, one per 15.003 ms predict step, in both files.
- **Provenance:** produced at commit `1b978de` (`~/thesis_data/batches/final_room_T/jobs.log`, line 1); scored in
  `json:expT/T_*.json` and N:526-529. The checksum guard covers these files (preregistration §6), so the reference
  cannot change between the snapshot and the gates.

### 8.2 Validation runs differ from result runs in three stated ways

These differences let the validation runs match the stored files, which cover the whole flight:
1. They run **uncut**: no anchor + 245 s cut.
2. They **anchor on the first `/tags/sent` fix,** exactly as `room_ukf_replay.py:175-178` does.
3. They take the tag input from `/tags/sent`.

The 245 s cut, the anchor on the first central tag-0 detection in `/tags/raw`, and the `/tags/raw` input apply in
result mode only.

### 8.3 Gates

| gate | what runs | output | reference | PASS iff |
|---|---|---|---|---|
| **G0-UKF** (unchanged code path) | the frozen `room_ukf_replay.py` at HEAD, `UKF_OUT_ROOT=~/thesis_data/tier1/g0_ukf` (it refuses any root under `trials/`) | `g0_ukf/<trial>/room_ukf/` | §8.1 | `ukf_live.tum` and `ukf_rts.tum` **byte-identical**, 12/12. The only UKF-path delta since `1b978de` is the `geom=None` plumbing, which is designed to leave the default arithmetic unchanged. |
| **V-E5a** (new harness, `ukf_core` filter) | `lc_ukf_replay.py --validate world`: the E5 harness reads `/tags/sent` and fuses with `ukf_core.update_tag` in the world frame, with the identical re-anchor. The filter calls are ONLY `ukf_core` functions (`predict`/`predict_rts`, `update_flow`, `update_range`, `update_yaw_pseudo`, `update_tag`, `rts_smooth`) | `lc_ukf_val_world/` | §8.1 | the tolerance of §8.4, 12/12. **Byte identity is reported but is not the gate:** the harness is new code. It is expected, since the arithmetic is `ukf_core`'s, and a non-identical result localises a harness difference before `ukf_lm.py` enters. |
| **V-E5b** (known map, the ruling's gate) | `--validate known-map`: `/tags/sent` fixes converted to tag-relative measurements with the TRUE map pose of the reported id, fused by `ukf_lm.py`'s tag-frame update (§4, sequential-scalar mode) against landmarks FIXED at the map (not in the state) | `lc_ukf_val_knownmap/` | §8.1 | the tolerance of §8.4, 12/12 |
| **V-E5c** (augmentation path) | `--validate augmented`: as V-E5b, but each landmark is augmented into the state at its first fix, initialised AT the true map with variance 1e-10 (m², rad²) | `lc_ukf_val_augmented/` | §8.1 | the tolerance of §8.4, 12/12 |

### 8.4 The pre-registered tolerance (every V-E5 gate, per flight, live and RTS separately)

1. **Rows match 1:1.** The same number of rows, and identical timestamps at the stored 6 dp. There is **no
   interpolation**. A timing error in the harness cannot hide inside a position tolerance.
2. **Anchor and tag count.** `t_anchor` and `n_tag_fused` are equal to the stored `room_ukf/stats.json` values.
3. **RMS horizontal position difference ≤ 1.0 mm.**
   - Over the rows inside the scored lap window (`json:expT/T_*.json:window_s`, the `tag_score` window).
   - Δ_i = ‖(x, y)_E5,i − (x, y)_stored,i‖ for each row i; RMS = √(mean Δ_i²).
   - The same figure over all rows is reported beside it.
4. **Max per-sample horizontal position difference ≤ 2.0 mm,** over the same window.
5. **Flow and range accept/reject counts** are equal to V-E5a's. The stored files carry no counts, so V-E5a, which uses
   `ukf_core`'s own gated updates, is the count reference.
   - **A count difference is not automatically a failure.** Without byte identity, one round-off flip at the flow gate
     (NIS gate 9, test ratio = 1.0) or the range gate can change a count, and no permitted fix to the E5 modules can
     remove it.
   - Each flip is logged with its time, its axis and both runs' test ratios. A flip whose two test ratios both lie
     within 1e-9 (relative) of 1.0 is a **round-off flip**: it is reported, and conditions 3 and 4 decide.
   - Any other count difference is a FAIL. It means a real difference in the innovation, not round-off.

**Why these figures.** Each one sits between a derived floor and a derived ceiling, and the choice of the value
within that range is labelled.

- **Floor (what round-off can produce).**
  - The stored TUM's 6-dp rounding alone gives an RMS of 1 µm/√12 ≈ 0.29 µm per axis.
  - `ukf_lm.py` re-implements the sigma points, mean and residual for a variable n (§1). That changes the float64
    operation order, for example the summation order in `Wm @ sig` and the Cholesky column order. Each such
    difference is about 1e-16 relative per operation.
  - The filter is stable, and the gate decisions are identical (condition 5), so such differences stay far below 1 µm
    in position. The tolerance must sit far above this floor, or a correct implementation would fail.
- **Ceiling (what the reproduced track takes part in).**
  - **The formal link to the scored numbers:** over the same samples, |RMSE_E5 − RMSE_stored| ≤ RMS(Δ) (Minkowski).
    The max per-sample difference bounds the change in any per-lap or per-gap RMSE the same way.
  - **The smallest stored per-flight gap between a UKF track and another estimator's track** in `json:expT` (EKF3
    live, FGO live, FGO batch; 12 flights) is **2.16 mm**: RTS-UKF 0.01280 m against FGO batch 0.01064 m on T_A_r1
    (`json:expT/T_A_r1.json`).
    - The next are 2.45 mm (UKF live 0.03623 against EKF3 live 0.03868 m, T_A_r2), 2.78 mm (UKF live against EKF3
      live, T_A_r3), 3.17 mm (the same, T_A_r1) and 3.37 mm (RTS-UKF against FGO batch, T_A_r2).
    - UKF live against FGO live is ≥ 14.2 mm on every flight.
    - The comparisons E5 itself makes are UKF against FGO (S-E5.5, S-E5.6). Their stored Experiment 2 analogues are
      ≥ 2.16 mm (hindsight) and ≥ 14.2 mm (live).
  - A tolerance at or above 2.16 mm could therefore let the validated code move a reproduced track across an
    Experiment 2 ordering.
  - **The scale of the scored E5 quantities:** the smallest stored Experiment 3 per-lap value, over every
    `per_lap_rmse_m` entry of `json:expL/T_A_r*_t245.json` (LC and no-LC, live and hindsight), is **0.0149 m** (LC
    hindsight, lap 5, T_A_r3). The smallest LC live lap value is 0.0258 m (lap 5, T_A_r3). The overall LC live values
    are 0.049–0.076 m.
  - **The reporting precision** is 1 mm (3 dp, N:526-529).
- **The chosen figures (judgement, not derived from data, within the derived range).**
  - **RMS ≤ 1.0 mm:** the user's suggested figure. It equals the reporting precision and is less than half the
    smallest UKF gap (2.16 mm), so no stored Experiment 2 ordering between a UKF track and another estimator can
    change through it. It is about 3,400× the quantisation floor, and 1/15 of the smallest stored Experiment 3 lap
    value (0.0149 m).
  - **Max ≤ 2.0 mm:** just below the 2.16 mm ceiling, so that no per-lap or per-gap RMSE can move by the smallest gap
    either. It allows a short local excursion of up to twice the RMS bound.
  - **1e-9 round-off band** on the test ratio: far above float64 round-off (about 1e-15 relative) and far below any
    innovation change that could matter.
  - **No yaw or z bound:** the E5 metrics are horizontal only (`l_score.py`), and a yaw or z error that mattered would
    show in the horizontal position through the flow model.
- **What V-E5c adds:** with landmarks in the state at variance 1e-10 (σ = 1e-5 m), the landmark adds
  (1e-5/0.05)² = 4e-8 to the innovation variance, so its own effect on the vehicle is far below 1 µm. A V-E5c
  difference above tolerance would therefore show that the augmented sigma set (n > 15) changes the vehicle estimate.
  That is a numerical-conditioning finding, reported and fixed **before** any result run (§9).

**Failure handling.**
- Any gate failure stops E5. The failure is reported with the per-flight differences: all quantities of §8.4, plus the
  per-flight |ΔRMSE| from `tag_score`.
- Fixes are allowed only to the E5 modules. Each fix is followed by a fresh supplementary code snapshot and a full
  re-run of the V-E5 gates.
- No E5 result run starts before G0-UKF and V-E5a/b/c all PASS.
- If G0-UKF fails, E5 stops for a ruling. The stored reference itself then cannot be reproduced, which no E5 fix can
  address.

## 9. Numerical conditioning

- **Sigma points:** the thesis UKF's Van der Merwe parameters, unchanged: α = 1e-3, β = 2, κ = 0
  (`ukf_core.make_params`, `ukf_core.py:55`). They are dimension-agnostic, with λ = α²(n + κ) − n, as in
  `_sigma_points` (:61-89), evaluated with the current n.
  - Process noise Q for the vehicle block is `make_params(dt=DT_STEP)['Q']` unchanged. The landmark block's Q is 0.
- **Cholesky:** the same jitter ladder (0, 1e-12, 1e-9, 1e-6) and eigen fallback as `ukf_core` (`CHOL_JITTER_LADDER`,
  `ukf_core.py:57-58`). Retries are counted and reported.
- **Symmetrisation:** P ← (P + Pᵀ)/2 after every update and removal.
- **Angle states:** wrapped after every update. The circular mean uses atan2 of the weighted sines and cosines.
- **Smoother gains:** solved on the diagonally scaled matrix, as `ukf_core.rts_smooth` (§7).

## 10. Design choices that change the numbers: DECIDED (sign-off 2026-10-22, subject to amendment 5)

The user accepted these choices on 2026-10-22, subject to amendment 5, which §5 and §6.1 now answer.
1. **DECIDED. Predict:** a joint sigma set over the full augmented state. The landmark rows are identity with zero
   process noise; tags are fixed on the floor. The alternative, vehicle-only sigma points plus a linearised
   cross-covariance update, is cheaper but a different estimator. The joint set keeps "UKF" meaning the same thing
   throughout.
2. **DECIDED. Gauge tag 0** is held exact, rather than given a 1e-4 prior. §5 shows this matches the FGO's anchor and
   gauge: the stored FGO L(0) stayed within 4e-10 of the origin.
3. **DECIDED. no-LC** drops finished-pass landmarks. It is equivalent to the FGO's no-LC arm in information; the one
   stated approximation (the unscented transform's dependence on n, and the RTS over the filter's linearisation) is in
   §6.1. It bounds memory.
4. **DECIDED. Tag update in sequential-scalar form** (x, y, yaw in the tag frame), to match the Experiment 2 UKF and
   make the known-map validation tight (§8). The alternative, one joint 3-D update, differs only through sigma-point
   redraws.
5. **DECIDED. The first sighting is used for initialisation only, not fused again** (§3c). For tag 0, the anchoring
   detection is used once, as the re-anchor (§5.2).
6. **DECIDED (amendment 2). Validation tolerance:** §8.4, against the stored Experiment 2 UKF tracks.
7. **Added 2026-10-22 (amendment 5): the pass rule runs on the FGO's keyframe time base** (§5.3), so the pass
   boundaries, and hence the landmark counts, match the FGO's.

## 11. Effort

About 3 working days:
- `ukf_lm.py` and the harness: 1.5 d;
- synthetic unit tests (augmentation, removal, RTS with dimension changes, angle wrap) and the gates V-E5a/b/c:
  1 d, including debugging;
- buffer: 0.5 d.

Compute is in `preregistration.md` §8: about 1.3 h for validation and about 0.3 h for results.
