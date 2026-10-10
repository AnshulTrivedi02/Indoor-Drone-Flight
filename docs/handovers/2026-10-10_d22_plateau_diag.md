# Handover, 2026-10-10: D22 climb-plateau mechanism (image expansion + off-centre median)

## 0. D22 decay-test criterion, written down BEFORE the D22 prediction was computed (12:01 +11:00)

- **Model (one free parameter).** While the tracker keeps its feature set, the median feature's image x-offset u
  (px, from the principal point) evolves as
  du/dt = −(ż/h)·u + F·(c_rot·ω_x + c_lat·v_left/h), and the published flow is
  flow_x = [−(ż/h)·u]/F + c_rot·ω_x + c_lat·v_left/h.
  - h = GT z − 0.25 (camera height; confirmed by the analogue's fitted scale rate, §2), ż from GT,
    ω_x = `/attitude/angular_rates` x (FRD roll rate), v_left = −v_East from GT (vehicle heading north).
  - **Coefficients from an independent source, not fitted on D22:** c_lat = +1.004 and c_rot = +1.0
    (METHODOLOGY "FINDING — lateral optical-flow sign": flow_x = +1.004·v_left/h, and ArduPilot's convention
    raw_x = v_left/h + p). c_rot = 1.5 (the 17 Hz-tone value from the same finding) is reported as a sensitivity.
  - u0 is set from the FIRST plateau frame only (where ω_x ≈ 0 and v_East ≈ 0): u0 = −flow_x·F/(ż/h).
- **Window:** the climb plateau frames listed in real_flights_plan §7.1a (valid, GT z 1.07–1.6 m), starting at the
  re-detection frame, ending before the next feature-set jump (count drop of ≥ 5).
- **Pass:** residual RMS (observed − predicted) over the window, excluding the u0 frame, ≤ 0.10 rad/s on BOTH
  flights, AND at least 3× smaller than the null model (u ≡ 0: rotation + lateral terms only).
- A pass makes D22 *consistent with* the mechanism; it cannot *confirm* it (no downward images were recorded).

(Results follow below.)

## 1. Verdict

- **D22 flights themselves: NOT DETERMINABLE from the recorded data.**
  - Neither bag has downward images. `cl_ukf_b_tex_r3_half` and `cl_fgo_b_tex_r3_half_v3` record
    `/forward_camera/image` only, and their `metadata.yaml` has no `with_images` key.
  - No recorded bag anywhere has downward images over the checkerboard. The only bags with
    `/downward_camera/image` are the `room_tags` flights `tagchar_h15/20/25/30`, `room_check` and `tag_check2img`.
- **Mechanism: CONFIRMED on two image-bearing analogues** (`tagchar_h20`, `tag_check2img`; `room_tags` world, the
  same harness climb profile, ż ≈ 1.3 m/s through z ≈ 1 m). Report these as analogues, not as D22.
- **D22: CONSISTENT with the mechanism.** The pre-registered one-parameter decay test (§0) passes on both flights.

## 2. Analogue result (images; offline replay of flow_tracker)

- **The replay is exact.** `plots/d22_plateau/replay_tracker.py` re-implements `flow_tracker.image_callback` with the
  same parameters and seed. It runs on system python3 (cv2 4.6.0, the build the node uses) and reads the bag's sqlite
  directly. It is a copy of the logic, not an import, because the node module needs rclpy.
  - **tagchar_h20:** 1423/1424 frames are identical to the published values (flow_x, flow_y bit-exact; count,
    inlier ratio and valid identical).
  - **tag_check2img:** 2333/2334 frames are identical, on the same measures.
  - **The one mismatch** in each bag is the bag's first frame. The node had already seen an earlier image, so it
    published a real measurement there (on the ground: flow 0, count 194, valid); the replay has no previous frame. Every later frame matches, so the
    tracker state re-converges at once.
- **Per-frame diagnostics.** Over the 40 valid climb frames (z 0.5–2.0 m) of each analogue:

  | | tagchar_h20 | tag_check2img |
  |---|---|---|
  | inlier ratio | 1.00 throughout | 1.00 throughout |
  | peak flow_x (truth ≈ 0: ωx = 0, v_lat = 0) | **+0.230 rad/s** | **+0.218 rad/s** |
  | median feature offset at plateau start (x, y) | (−49.0, −3.0) px | (−46.5, −3.0) px |
  | RMS flow at the principal point (fitted similarity's translation) | **0.0027 rad/s** | **0.0019 rad/s** |
  | RMS(flow_x − flow@PP − (s−1)·u_med/dt/F) | **0.0025 rad/s** | **0.0022 rad/s** |
  | fitted −(s−1)/dt ÷ GT ż/h_cam, median (range) | **1.004** (0.98–1.07) | **0.997** (0.92–1.12) |

- **What this shows.**
  - The excess flow_x is entirely the expansion term (s−1) times the median feature's offset from the principal
    point. The residual is ≤ 0.003 rad/s.
  - The similarity transform's translation at the principal point is ≈ 0, which is the truth.
  - RANSAC's similarity model fits the expanding field exactly, so the inlier ratio stays at 1.00.
  - The fitted scale rate equals GT ż/(z − 0.25), which also confirms h_cam = z − 0.25.
  - The offset decays as 1/h, because the tracked ground points converge on the principal point as the camera
    climbs, so the excess decays as ż/h².
- **Limit of the analogue.** Its offset is −49 px, which gives 0.23 rad/s. D22 needs about −217 px. The analogue
  proves that the mechanism exists and that RANSAC accepts these frames. It does not prove D22's magnitude.

## 3. D22 result (published flow + GT only)

- **Implied offset at the plateau start.** At the first plateau frame, GT z = 1.07 m (h_cam 0.82 m), ż/h = 1.65–1.68 /s,
  and ωx = vE = 0.
  - To give the observed +0.654 / +0.646 rad/s, the median feature would need an x-offset of **−218 px (UKF) and
    −217 px (FGO)**: one third of the way in from the left edge. The image half-width is 320 px.
  - **flow_y ≈ 0.01** at the same ż/h, so the median y-offset must be within about 3 px of centre.
  - Both flights give the same offset at the same height. Both took off from the same spot on the same floor, and
    the tracker is deterministic.
  - This −217 px is 0.32 m on the floor at h 0.82, which is about one checker square (0.3125 m; `checker.png` is
    64 squares over a 20 m tile). That is suggestive only: without images, which corners the tracker kept is unknown.
- **Pre-registered decay test (§0).** Coefficients come from METHODOLOGY's lateral-sign finding and are not fitted
  here. u0 is fixed on the first frame, and the next frames are predicted.

  | flight | window | n | RMS(obs − pred), c_rot 1.0 / 1.5 | RMS(obs − null) | pass? |
  |---|---|---|---|---|---|
  | UKF | primary (to the 50→43 count drop) | 3 | **0.038 / 0.025** | 0.576 | yes |
  | FGO | primary (to the 46→39 count drop) | 1 | **0.004 / 0.004** | 0.584 | yes, but n = 1 |
  | UKF | §7.1a full, z 1.07–1.6 (secondary) | 11 | 0.061 / 0.019 | 0.452 | yes (≤ 0.10, ≥ 3×) |
  | FGO | §7.1a full, z 1.07–1.6 (secondary) | 11 | 0.080 / 0.077 | 0.395 | yes |

  - **The primary windows are short.** The pre-registered "count drop ≥ 5" cut-off ended them after 3 frames (UKF)
    and 1 frame (FGO), so the full-window rows carry the evidence. The full-window rows are a stated departure from
    the pre-registered window, not the primary test.
  - **The null model fails** (RMS 0.37–0.58 rad/s): roll rate plus lateral velocity alone cannot produce the plateau.
  - **The one-parameter expansion model reproduces the shape**: the plateau holds near +0.6 while the roll term grows,
    then decays as ż/h falls.
  - **The largest residuals sit on feature-set changes**, as the mechanism predicts, since the median offset jumps
    when the inlier set changes:
    - FGO, z 1.31–1.35: obs 0.24/0.26 against pred 0.42/0.41, where the inlier count goes 37 → 36;
    - UKF, at the next frame after the window (z 1.84): flow_x flips +0.09 → −0.10 where the count drops 42 → 32.
- **Caveats.**
  - The gyro lag (−16 ms in the METHODOLOGY fit) is not applied.
  - c_rot is uncertain between 1.0 and 1.5; both are shown.
  - Shadow features (Known Issue #2) cannot be excluded without images.
  - This is a consistency test with one fitted parameter. It cannot replace an image replay.

## 4. Implication for the candidate fixes (future work, not implemented)

- **(b) the scale check and (c) the climb-rate check measure the same quantity.** The fitted −(s−1)/dt equals GT
  ż/h_cam to within about 1% (median; per-frame 0.92–1.12).
  - The worst-case bias is (ż/h)·(W/2)/F ≈ 0.58·ż/h rad/s, with the median at the image edge.
  - At the D22 plateau start, |s−1| ≈ 5.5% per frame (ż/h ≈ 1.65 /s at 30 Hz). Either gate would flag it easily.
  - For comparison, cruise frames have ż ≈ 0.
- **(b) is the cleaner input.** It uses the same frame and the same fit the tracker already computes (the matrix
  `estimateAffinePartial2D` returns and the node discards), so there is no extra sensor and no timing alignment.
- **(c) is noisier.** It needs a differentiated rangefinder signal, and the rangefinder has near-zero dropouts during
  climbs (Known Issue #5), so (c) would need filtering.
- **Both are blunt.** They reject every climb frame, whether or not the features are centred.
  - **A threshold could be derived instead of tuned:** reject when 0.58·|s−1|/dt exceeds an allowed bias, for example
    the 0.1 rad/s test level used here.
- **(a) is noted because it was measured here, not ruled on.** Taking the flow as the fitted translation at the
  principal point removes the bias without discarding frames: the residual is ≤ 0.003 rad/s RMS on both analogues.

## 5. Files and housekeeping

- **Files in `plots/d22_plateau/`:**
  - `replay_tracker.py`: the exact offline replay plus diagnostics (system python3);
  - `compare.py`: the replay-vs-published check;
  - `extract.py`: flow/GT/range/attitude extraction (venv-evo, rosbags);
  - `climb.py`: the per-frame climb table and implied offset;
  - `diag.py`: the analogue per-frame decomposition;
  - `decay_test.py`: the pre-registered D22 test. Lift-off times 27.93 / 28.16 s are taken from `climb.py`
    (first GT z > 0.30 m);
  - `make_figure.py`: produces `d22_plateau_expansion.png` and `summary.txt`.
- **Scratch.** The decompressed `cl_ukf` bag and both analogue bags were decompressed to the session scratchpad with
  `zstd -d -o` and deleted after extraction. No original was touched.
- **Not edited:** METHODOLOGY, numbers.md, real_flights_plan.md, src/. No flights, no simulator, no heavy jobs.
- **Next (for a ruling):** whether a short `--with-images` checkerboard climb is worth recording to close the D22
  question directly. It would be a new flight, so it needs a ruling. The decision on (a)/(b)/(c)/(d) is the user's.
