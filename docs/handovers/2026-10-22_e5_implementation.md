# Handover: E5 landmark UKF, implementation (2026-10-22)

**One stage: implementation and light synthetic unit tests only.**
- No recorded flight was replayed and no bag was opened.
- Nothing involving `arducopter` or `gz sim` was run.
- Nothing was written under `~/thesis_data`. The harness test monkeypatches the output guard to a temporary directory.
- **The V-E5 gates and the E5 result runs have NOT been run.** They are the next stage (commands below).
- **Design followed:** `docs/thesis/tier1/e5_design.md`, signed off 2026-10-22 with amendment 5, together with
  `preregistration.md` §4, §6 and §7.
- **Branch:** `worktree-agent-a907b5bbdf5a90782`, reset to `fwd-camera` at `a09230a`, then committed on top. Not
  merged.

## Files (all new; no existing file was edited)

| file | role |
|---|---|
| `src/estimators/ukf_lm.py` | the variable-size UKF core (design §1) |
| `src/estimators/lc_ukf_replay.py` | the harness: result runs (`--mode lc\|nolc`) and the gates V-E5a/b/c (`--validate world\|known-map\|augmented`) |
| `src/estimators/test_ukf_lm.py` | synthetic unit tests (plain asserts; pytest is not installed) |
| `eval/e5_val_compare.py` | **the V-E5 gate judge**: implements §8.4 against the stored `room_ukf/` files. Not named in design §1, but the gates need a judge. It should be in the supplementary E5 code snapshot (see below). |

**Untouched:** `ukf_core.py`, `measurement_models.py`, `room_ukf_replay.py`, `imu_timing.py`, `lc_fgo_replay.py`,
`fgo_core.py` and `tier1_paths.py`. The new code only imports from them.
- `ukf_lm` calls `ukf_core._process`, `make_params`, `init_state` and `_wrap`, plus `measurement_models.h_flow` and
  `h_range`.
- The harness calls `ukf_core` (V-E5a), `imu_timing`, `measurement_models` (`reanchor_jacobian`, `GroundProximityFlow`,
  `FlowFrameGyroAverager` and the tag sigmas), `tier1_paths.resolve_out` and `tag_measure`.

**venv:** `~/venv-evo`. It is the venv that produced the stored `room_ukf` tracks (numpy 2.5.1, rosbags, no gtsam).
The harness does not import gtsam.

## Design section → code

| design | what | code |
|---|---|---|
| §1 | variable-n sigma points, mean and residual. They mirror `ukf_core.py:61-106` operation by operation, which gives bit-identity at n = 15 (test 1). | `ukf_lm.py:37-86` |
| §1 | vehicle block via `ukf_core._process` | `ukf_lm.py:89-112` (`_f`, `predict`) |
| §2 | inputs: `/tags/raw` central third (lc_fgo_replay.py:80, :110-123) | `lc_ukf_replay.py:71-131` (`quat_to_R`, `central_tagrel`, `read_events`) |
| §2 | gap rule, dejitter, DT_STEP, ground-proximity flow, bias-corrected derotation | `lc_ukf_replay.py:345-370`, `:405-412`, `:446-451` |
| §2 | cut at anchor + 245 s (lc_fgo_replay.py:268) | `lc_ukf_replay.py:397-398` |
| §2 | live = the state after each predict, from the anchor on | `lc_ukf_replay.py:433`, `:533-546` |
| §3 | landmark block [x, y, ψ] and ψ as an angle state | `ukf_lm.py:31-34` (`ang_indices`); `lc_ukf_replay.py:206-216` (`LandmarkLayout`) |
| §3a | inverse model (= `lm_from`, lc_fgo_replay.py:153-155) | `ukf_lm.py:248-251` |
| §3b | unscented augmentation over [x; w] with P_xL | `ukf_lm.py:254-274` |
| §3c | first sighting not fused again | `lc_ukf_replay.py:517-521` |
| §4 | h = vehicle (x, y, yaw) in the landmark frame (= the FGO factor, lc_fgo_replay.py:132-135) | `ukf_lm.py:180-193` |
| §4, §10.4 | sequential-scalar update (x, y, then yaw in `update_heading`'s relative form), no gate; the joint 3-D alternative is behind `--tag-update joint` and is never used by a pre-registered run | `ukf_lm.py:196-245` |
| §4 | several detections in one frame applied in bag order | the event loop, `lc_ukf_replay.py:490-526` |
| §5.2 | anchor = the first central tag-0 detection in `/tags/raw` at or after t_init; re-anchor as `room_ukf_replay.py:181-182`; tag 0 held EXACT (never augmented) | `lc_ukf_replay.py:491-505`, `:312-316`, `:511-514` |
| §5.2 | pseudo-yaw before the anchor only | `lc_ukf_replay.py:421-422`, `:431-432` |
| §5.3 | keyframe clock t_init + k/30, the pass rule on keyframe labels, and exclusion of detections whose keyframe never runs before the cut | `lc_ukf_replay.py:134-175` (`KeyframeClock`, `keyframe_prepass`), `:178-203` (`PassBook`) |
| §5.3 | invariants: `t_anchor` and the landmark (pass) count equal the stored FGO run's. Exit code 3 on a mismatch; `tag_measurements_used` against `landmark_factors` is reported | `lc_ukf_replay.py:575-587`, `:564`, `:569-572` |
| §6 | lc: one key per id; nolc: one per pass; finished passes dropped (marginalised) | `PassBook`; `lc_ukf_replay.py:387-394` (`drop_finished`, called before each predict and before each detection); `ukf_lm.py:286-292` (`remove_block`) |
| §7 | RTS over a chain of predict, augmentation and removal nodes; the gain is solved on the diagonally scaled matrix as `ukf_core.rts_smooth` (`ukf_core.py:177-184`) | `ukf_lm.py:295-316` (`rts_backward`) |
| §7 | output rows at predict nodes only: row i = the smoothed state just before predict i+1 (`room_ukf_replay.py:193-198`'s convention) | `lc_ukf_replay.py:552-555` |
| §7 | memory: nodes in RAM, spilling to `np.memmap` (`rts_nodes.bin` in the run directory) above 4 GB; recorded in stats | `lc_ukf_replay.py:219-268` (`NodeStore`) |
| §8.2, §8.3 | V-E5a: `ukf_core` calls only (`predict`/`predict_rts`, `update_flow`, `update_range`, `update_yaw_pseudo`, `update_tag`, `rts_smooth`), `/tags/sent`, uncut | `lc_ukf_replay.py:414-422`, `:437-441`, `:452-458`, `:474-475`, `:547-551` |
| §8.3 | V-E5b: world fix → tag-relative with the TRUE map pose of the reported id (`frame_id` "tag_<id>"), `ukf_lm`'s tag-frame update against a FIXED landmark | `lc_ukf_replay.py:319-322`, `:476-488` |
| §8.3 | V-E5c: each id augmented AT the map pose with variance 1e-10 at its first fix (the anchoring fix's id at the anchor), then fused | `lc_ukf_replay.py:469-472`, `:481-486` |
| §8.4 | the gate judge (conditions 1–5, the 1e-9 round-off band; byte identity reported; optional `--delta-rmse`) | `eval/e5_val_compare.py` |
| §8.4 cond. 5 | accept/reject log of every gated flow-axis and range decision with its test ratio (`gate_log.npz`). In V-E5a it comes from a recording wrapper around `ukf_core._update_scalar`, installed for the run and restored after; the wrapper returns the original result unchanged. | `lc_ukf_replay.py:272-309` |
| §9 | α = 1e-3, β = 2, κ = 0; Q from `make_params(dt=DT_STEP)`, landmark Q = 0; the jitter ladder and eigen fallback (counted, in stats `chol`); symmetrisation; angles wrapped after every update | `ukf_lm.py` throughout |

**Outputs:**
- Result runs: `~/thesis_data/tier1/<trial>/lc_ukf_{lc,nolc}_t245/`, containing `live.tum`, `hindsight.tum`,
  `stats.json` and `gate_log.npz`. `l_score.py --prefix lc_ukf --suffix _t245` reads `live.tum` and `hindsight.tum`
  there.
- Validation runs: `~/thesis_data/tier1/<trial>/lc_ukf_val_{world,knownmap,augmented}/`, containing `ukf_live.tum`,
  `ukf_rts.tum`, `stats.json` and `gate_log.npz`.
- Every directory goes through `tier1_paths.resolve_out`: never under `trials/`, and never into an existing non-empty
  directory.

## Tests (`~/venv-evo/bin/python src/estimators/test_ukf_lm.py`, about 17 s, ALL OK)

The six required cases are marked (1)–(6).

| test | result |
|---|---|
| **1**, n = 15 against `ukf_core` | **Bit-identical** (`np.array_equal`) over 160 predicts with D, and over range (64 accepted / 16 rejected), flow (including X-axis rejections), pseudo-yaw (23 fires), tag updates (fixed landmark at the origin with yaw 0) and the RTS over 160 nodes. |
| 1b, known-map tag-frame update against the world `update_tag` | Agree to 8.1e-10 m. This is round-off only: the UT weight Wm[0] ≈ −1e6 amplifies 1e-16 cancellation in `Wm @ Z`. The joint 3-D mode agrees to < 1e-6. |
| **2**, augmentation | Shapes 15 → 18 → 21. D = [P, P_xL]. The vehicle block is kept exactly. Mean, P_LL and P_xL agree with a 2e5-sample Monte Carlo of g(x, w) to < 2%. The UT mean sits 3.1 mm from the inverse model evaluated at the mean: this is the second-order term, as designed (§3b). |
| 2b, V-E5c premise | A landmark at the map pose with variance 1e-10 agrees with a fixed landmark to 7.3e-9 m. |
| **3**, landmark yaw wrapping | Circular mean across ±π. Residual wrapped. An update with ψ_v − ψ_L across ±π moves by +0.0173 rad, the same as the rotated problem, which does not wrap. |
| **4**, tag-0 anchor | The anchor is the first central gauge detection at or after t_init; earlier detections and non-gauge detections are ignored. Keyframe labels are correct. Key 0 = the gauge pass (lc: every tag-0 sighting; nolc: a new key after a gap of more than 1 s). The re-anchor sets x, y, yaw and the rotated velocity, with a diagonal P carrying the tag noise. Quaternion → R is correct. |
| **5**, no-LC drop | A pass ends at strictly more than 1.0 s. A detection pending at the cut is excluded. Removal keeps the vehicle block exactly. Kept and dropped landmarks give vehicle estimates within 1.8e-9 over 80 steps, the UT n-dependence of §6.1. |
| **6**, RTS over a growing and shrinking state | On a linear-Gaussian chain (an augmentation, then a removal), `rts_backward` equals the batch joint-Gaussian posterior to 8e-15, both with the landmark dropped and with it kept. 6b runs the UKF chain through `NodeStore` with a forced memmap spill (22 of 32 nodes) and reads it back bit-exactly. |
| H, harness end to end on synthetic events (read_events monkeypatched) | All five tasks run. V-E5b/c reproduce V-E5a with matching rows: known-map differs by 0, augmented by ≤ 1.4e-6 m (one 6-dp LSB), with identical gate decisions. lc gives 3 landmarks; nolc gives 5 and drops 3 finished passes. Live and hindsight rows equal the predict count. The invariant failure exits with code 3. |
| C, comparator | Row match; the 1 mm and 2 mm bounds; a round-off flip against a real flip; `judge()` on the gate directory layout, with \|ΔRMSE\| against a synthetic ground truth. |

Also checked:
- **Quaternion conversion:** the numpy Eigen formula equals `gtsam.Rot3.Quaternion(...).matrix()` exactly
  (difference 0) on 2000 random quaternions, including non-unit ones (gtsam does not normalise). This was a one-off
  run in `~/venv-fgo`, not part of the test file.
- `py_compile` passes on all four files.

## Commands for the next stage (NOT run)

Run them one job at a time, after the idle check (`pgrep -fa '[a]rducopter'`, `pgrep -fa '[g]z sim'`, no
`~/thesis_data/FLIGHT_LOCK`), and after G0-UKF has PASSED (§7).

```bash
# 0. supplementary E5 code snapshot (preregistration §6), immediately before the first V-E5 run (main checkout)
cd /home/makerspace/thesis_ws && python3 tools/tier1_checksum_guard.py snapshot --repo /home/makerspace/thesis_ws \
  --paths $PWD/src/estimators/ukf_lm.py $PWD/src/estimators/lc_ukf_replay.py $PWD/src/estimators/test_ukf_lm.py \
          $PWD/eval/e5_val_compare.py \
  --out docs/thesis/tier1/e5_code_manifest_<ts>.json
#    (preregistration §6 prescribes `snapshot --paths <E5 files>`; the tool's help labels --paths "TEST ONLY" because it
#     replaces the default coverage, which is the intent here: this is the separate, supplementary E5 code manifest)

# 1. V-E5a, then V-E5b, then V-E5c, per flight (12 flights: T_{A,B,C,D}_r{1,2,3}); V-E5a first on each flight
#    (it is the count reference for b and c)
cd /home/makerspace/thesis_ws && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 nice -n 10 \
  /home/makerspace/venv-evo/bin/python src/estimators/lc_ukf_replay.py T_A_r1 --validate world
#   ... --validate known-map
#   ... --validate augmented

# 2. judge each (exit 0 = PASS); the --json under docs/thesis/tier1/scores/ must be a new file
/home/makerspace/venv-evo/bin/python eval/e5_val_compare.py T_A_r1 --task world     --delta-rmse --json docs/thesis/tier1/scores/ve5a_T_A_r1.json
/home/makerspace/venv-evo/bin/python eval/e5_val_compare.py T_A_r1 --task knownmap  --delta-rmse --json docs/thesis/tier1/scores/ve5b_T_A_r1.json
/home/makerspace/venv-evo/bin/python eval/e5_val_compare.py T_A_r1 --task augmented --delta-rmse --json docs/thesis/tier1/scores/ve5c_T_A_r1.json

# 3. only if G0-UKF and V-E5a/b/c PASS on 12/12: the 6 result runs (T_A_r1..r3, lc and nolc)
cd /home/makerspace/thesis_ws && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 nice -n 10 \
  /home/makerspace/venv-evo/bin/python src/estimators/lc_ukf_replay.py T_A_r1 --mode lc
#   ... --mode nolc     (exit 3 = a §5.3 invariant failed: stop E5 before scoring)

# 4. score (Experiment 3 metrics), per flight
/home/makerspace/venv-evo/bin/python eval/l_score.py T_A_r1 --in-root ~/thesis_data/tier1 --prefix lc_ukf --suffix _t245 \
  --json docs/thesis/tier1/scores/e5_T_A_r1.json

# 5. after the last E5 result run: verify the supplementary snapshot
python3 tools/tier1_checksum_guard.py verify docs/thesis/tier1/e5_code_manifest_<ts>.json
```

- **Cost (an estimate from the synthetic runs, not measured on a bag):** about 5–6 ms per predict step with
  updates at n = 27.
  - Uncut validation runs have about 17k steps, so V-E5a/b take about 1–2 min and V-E5c (n ≤ 39 on condition A)
    about 3–4 min.
  - LC result runs (n ≤ 36) take about 3 min; no-LC runs are less.
- **Memory:** the RTS store peaks at about 0.6 GB (V-E5c on A).
- These fit preregistration §8.

## Implementation choices within the design (none changes a signed-off rule; the first is flagged for a ruling)

1. **V-E5c fuses the first fix of every landmark.**
   - **Flagged for confirmation.**
   - Design §8.3 says each landmark is "augmented into the state at its first fix, initialised AT the true map with
     variance 1e-10". The augmentation is not computed from the measurement, so §3c's "not fused again" rule (which
     avoids double counting) does not apply, and the fix is fused.
   - Without this, `n_tag_fused` (§8.4 condition 2) and the track could not match the stored run, which fuses every
     fix.
   - The anchoring fix stays a world re-anchor, as in all three gates. Its id is augmented at the anchor and not
     fused again.
2. **The augmentation keeps the existing (x, P) block exactly.**
   - In exact arithmetic, the unscented mean and covariance of that block equal x and P, because g is the identity
     there. Only P_LL, P_xL and the landmark mean come from the sigma points.
   - Keeping the block exact avoids an O(1e-16·1/α²) perturbation of the vehicle at every augmentation.
3. **The landmark mean is the unscented mean (§3b), not the inverse model at the mean** (the FGO's initial value,
   lc_fgo_replay.py:255). They differ by the second-order term, about 3 mm in test 2.
   - This is as designed, because the FGO relinearises its initial value away and the UKF cannot. It is noted here so
     that it is not mistaken for a bug.
4. **When a finished pass is dropped.**
   - A pass is dropped at the first predict step, or the first detection, at which the keyframe clock is more than
     1.0 s past its last label. From then on, any later sighting would open a new pass, so the drop is equivalent to
     the FGO's rule.
   - The design fixes the rule, not the instant.
5. **The FGO's `pim.deltaTij() <= 0` early return** (lc_fgo_replay.py:230-231) cannot drop a pending detection.
   - Pending detections attach to the first keyframe of the next firing loop.
   - That keyframe always follows at least one IMU integration, because the dejittered stamps are strictly
     increasing.
   - So `keyframe_prepass` does not model the early return. The landmark-count invariant would catch any mismatch.
6. **`/tags/raw` quaternions** are converted with the numpy Eigen formula, which equals gtsam's exactly (above), so the
   harness runs in venv-evo without gtsam.
7. **Not read by the harness:** the environment switches that `room_ukf_replay.py` honours (`ROOM_TAG_SIGMA_POS`,
   `ROOM_TAG_MAX`, `ROOM_TAG_SKIP`, `UKF_APIN`, `UKF_OUT_ROOT`). The stored references were produced with them unset.
8. **The §8 failure report** (per-flight |ΔRMSE| "from `tag_score`").
   - `tag_score.py` cannot read a UKF track from another directory, and it is not edited here.
   - Instead, `e5_val_compare.py --delta-rmse` computes the same quantity with `tag_score`'s `err()` method: horizontal
     error at the track's own samples, ground truth interpolated, over `window_s`.
   - It is reported, and it never gates.

## Not done (next stage)

- The supplementary code snapshot, the V-E5a/b/c gates (36 runs) and the 6 E5 result runs, with their scoring.
- Rows in `numbers_tier1.md`.
- Ruling on item 1 above. It should come before V-E5c is judged.
