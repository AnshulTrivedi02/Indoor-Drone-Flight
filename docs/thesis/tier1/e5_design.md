# E5: UKF with tag landmark states, design (no code yet)

**Extension experiment, pre-registered.** This is the design that `preregistration.md` §4 points to.
- **Status:** DRAFT, awaiting sign-off. Written 2026-10-21 against `c1dd6ee`. No code has been written and nothing has
  been run.
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

## 5. Anchor and gauge (mirrors the FGO)

- **Before the anchor:** the thesis UKF, unchanged. That means the predict, flow and range updates, and the
  zero-innovation pseudo-yaw. This is the same as `room_ukf_replay.py` before its first fix (:142-144).
- **Anchor:** the first central sighting of tag 0. It re-anchors the vehicle with
  `measurement_models.reanchor_jacobian(x, (m_x, m_y), m_ψ)` and the Experiment 2 UKF covariance treatment:
  - P ← diag(J P Jᵀ);
  - the x, y and yaw variances are set to the tag noise.

  Both are from `room_ukf_replay.py:175-178`, and correspond to the FGO's re-anchor at lc_fgo_replay.py:133-151.
- **The pseudo-yaw stops at the anchor,** as in the Experiment 2 UKF (:142) and as the FGO's "no yaw cap after the
  anchor" (M:10468).
- **Gauge:** landmark 0 (tag 0) is the origin, (0, 0, 0), and is **not augmented**. It is treated as exactly known.
  - The FGO puts a prior with σ = 1e-4 on L(0) (lc_fgo_replay.py:199-201). Against σ_pos = 0.05 m that prior is
    effectively exact.
  - Keeping tag 0 out of the state avoids a near-singular 1e-8 variance block in the Cholesky.
  - Every later sighting of tag 0 in LC is an update against the fixed origin, which is the loop closure.
  - The difference from the FGO's 1e-4 prior is stated.

## 6. Re-identification: LC and no-LC

- **LC:** one landmark per tag id. A later sighting of id j updates the existing landmark j: re-identification is a
  loop closure through the cross-covariance. This mirrors lc_fgo_replay.py:170-176 with `--mode lc`.
- **no-LC:** a NEW landmark per **pass**. A pass ends after more than `PASS_GAP_S` = 1.0 s without a sighting of that
  id (lc_fgo_replay.py:44, :172; M:10478-10479). This includes tag 0's later passes:
  - in no-LC, its later passes are new free landmarks, as in the FGO, where only the first gets the gauge prior (:199);
  - the first tag-0 pass after the anchor uses the fixed origin.
- **Finished-pass landmarks are removed from the state (no-LC only).**
  - By the pass rule, a landmark whose pass has ended is never observed again. Marginalising it out (deleting its
    rows and columns) is therefore **exact** for the filter.
  - With the smoother book-keeping of §7, it is also exact for the RTS smoother.
  - It bounds n at 15 + 3 × (passes open at once), instead of 15 + 3 × 40.
  - In LC every landmark is kept: n ≤ 15 + 3 × 7 = 36.

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
- **The backward pass** uses the general (rectangular) gain G_k = D_k (P⁻_{k+1})⁻¹. It is solved with a Cholesky of
  P⁻ (`scipy.linalg.cho_solve`), never an explicit inverse.
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

## 8. VALIDATION: a HARD gate before any E5 result counts

The ruling requires that, with a known map, the new code reproduces the existing Experiment 2 UKF result. The stored
Experiment 2 UKF outputs are:
- `~/thesis_data/trials/T_*/room_ukf/{ukf_live.tum, ukf_rts.tum}`;
- TUM written at 6 dp, a 1 µm position precision (`room_ukf_replay.py:78-82`);
- produced at commit `1b978de` (`~/thesis_data/batches/final_room_T/jobs.log`, line 1);
- scored in `json:expT/T_*.json` and N:526-529.

**Validation runs differ from result runs in three stated ways,** so that they can match the stored Experiment 2
UKF files, which cover the whole flight:
1. They run **uncut**: no anchor + 245 s cut.
2. They **anchor on the first `/tags/sent` fix,** exactly as `room_ukf_replay.py:173-178` does.
3. They take the tag input from `/tags/sent`.

The 245 s cut, the anchor on the first central tag-0 detection in `/tags/raw`, and the `/tags/raw` input apply in
result mode only.

**Code path per gate.**
- **V-E5a** uses ONLY `ukf_core` functions for the filter: `predict` / `predict_rts`, `update_flow`, `update_range`,
  `update_yaw_pseudo`, `update_tag` and `rts_smooth`. It therefore tests the new harness (event reading, timing,
  re-anchor, node book-keeping) without the variable-n re-implementation, whose floating-point operation order would
  otherwise break byte identity for no real reason.
- `ukf_lm.py`, the variable-n code, first enters at **V-E5b**, which has a numerical tolerance.

| gate | what runs | reference | PASS iff |
|---|---|---|---|
| **G0-UKF** | the frozen `room_ukf_replay.py` at HEAD, `UKF_OUT_ROOT=~/thesis_data/tier1/g0_ukf` (it now refuses any root that resolves under `trials/`) | stored `room_ukf/` | `ukf_live.tum` and `ukf_rts.tum` byte-identical, 12/12. The only UKF-path delta since `1b978de` is the `geom=None` plumbing. |
| **V-E5a** (harness) | `lc_ukf_replay.py --validate world`: the E5 harness reads `/tags/sent` and fuses with `ukf_core.update_tag` in the world frame, with an identical re-anchor | stored `room_ukf/` | byte-identical, 12/12. This proves the event reading, timing, re-anchor and RTS book-keeping. |
| **V-E5b** (known map, the ruling's gate) | `--validate known-map`: `/tags/sent` fixes converted to tag-relative measurements with the TRUE map pose of the reported id. Fused through the E5 tag-frame update (§4, sequential-scalar mode) against landmarks FIXED at the map (not in the state) | V-E5a | 12/12, live and RTS: (i) identical flow and range accept/reject counts (E5 logs them); (ii) max per-sample horizontal position difference ≤ 1 mm; (iii) per-flight horizontal RMSE (`tag_score`) equal to |Δ| ≤ 1e-4 m |
| **V-E5c** (augmentation path) | `--validate augmented`: as V-E5b, but each landmark is augmented into the state at its first fix, initialised AT the true map with variance 1e-10 (m², rad²) | V-E5b | the same three conditions, 12/12 |

**Derivation of the tolerance.**
- With a fixed landmark, the tag-frame measurement is a rotation of the world-frame one. Both h and the noise are
  isotropic in x and y, so the update differs only by floating-point round-off (about 1e-15 relative).
- The 1 mm per-sample bound is 1000× the storage precision, 1/50 of σ_pos, and equal to the 3-dp (mm) reporting
  precision (N:526). The 1e-4 m RMSE bound is 1/10 of that reporting precision.
- The accept-count condition exists to catch a near-threshold flow-gate flip. Such a flip would otherwise hide inside
  an RMSE tolerance.
- A V-E5c gap above tolerance would show that the augmented sigma set (n > 15) changes the vehicle estimate even with
  a near-certain landmark. That would be a numerical-conditioning finding, reported and fixed **before** any result run.
  The jitter is stated in §9.

**Failure handling.**
- Any gate failure stops E5. The failure is reported with the per-flight differences.
- Fixes are allowed only to the E5 modules, followed by a fresh supplementary code snapshot and a full re-run of the
  gates.
- No E5 result run starts before all four gates PASS.

## 9. Numerical conditioning

- **Sigma points:** the thesis UKF's Van der Merwe parameters, unchanged: α = 1e-3, β = 2, κ = 0
  (`ukf_core.make_params`, `ukf_core.py:55`). They are dimension-agnostic, with λ = α²(n + κ) − n, as in
  `_sigma_points` (:61-89), evaluated with the current n.
  - Process noise Q for the vehicle block is `make_params(dt=DT_STEP)['Q']` unchanged. The landmark block's Q is 0.
- **Cholesky:** the same jitter ladder (0, 1e-12, 1e-9, 1e-6) and eigen fallback as `ukf_core` (`CHOL_JITTER_LADDER`,
  `ukf_core.py:57-58`). Retries are counted and reported.
- **Symmetrisation:** P ← (P + Pᵀ)/2 after every update and removal.
- **Angle states:** wrapped after every update. The circular mean uses atan2 of the weighted sines and cosines.
- **Smoother gains:** solved by Cholesky (§7).

## 10. Design choices that change the numbers (flagged for sign-off)

1. **Predict:** a joint sigma set over the full augmented state. The landmark rows are identity with zero process
   noise; tags are fixed on the floor. The alternative is vehicle-only sigma points plus a linearised cross-covariance
   update. That is cheaper, but it is a different estimator. The joint set is chosen so that "UKF" means the same thing
   throughout.
2. **Gauge tag 0** is held exact, rather than given a 1e-4 prior (§5).
3. **no-LC** drops finished-pass landmarks: exact, and it bounds memory (§6).
4. **Tag update in sequential-scalar form** (x, y, yaw in the tag frame), to match the Experiment 2 UKF and make the
   validation exact. The alternative is one joint 3-D update, which differs only through sigma-point redraws.
5. **The first sighting is used for initialisation only, not fused again** (§3c).

## 11. Effort

About 3 working days:
- `ukf_lm.py` and the harness: 1.5 d;
- synthetic unit tests (augmentation, removal, RTS with dimension changes, angle wrap) and the gates V-E5a/b/c:
  1 d, including debugging;
- buffer: 0.5 d.

Compute is in `preregistration.md` §8: about 1.3 h for validation and about 0.3 h for results.
