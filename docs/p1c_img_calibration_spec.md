# Calibration flights `p1c_img_*`: specification and pre-registered acceptance bands (SIGNED OFF by the user 2026-10-10, with the climb-cycle change below made BEFORE any flight)

**Purpose:** validate the real-flight camera-path flow (option 2, ruling 2026-10-10). Option (a) takes the flow as the
fitted similarity transform's translation at the image centre. It is compared against the current median-feature
flow, both measured against ground truth. The flights also set the thresholds of the (b) backstop.

**These are CALIBRATION flights only, NEVER datasets.** No thesis comparison result is computed from them, and the
simulation datasets keep the original flow computation.

## 1. Flights

| name | world | floor |
|---|---|---|
| `p1c_img_tex` | `corridor_textured.sdf` | textured |
| `p1c_img_trans` | `corridor_transition.sdf` | textured y < 80 m, blank y > 80 m |
| `p1c_img_blank` | `corridor_blank.sdf` | blank |

- **Configuration:** the `run_trial.sh` defaults, as for every recent corridor trial: nomag, `sim_noise.parm`,
  `consolidated_rerun.parm`, so `AHRS_EKF_TYPE 10` (it flies on simulator truth, the same trajectory in every world).
  `EXTRA_RECORD_TOPICS="/downward_camera/image /downward_camera/camera_info"` records the downward images (run_trial.sh has no `--with-images` flag; corrected 2026-10-10).
- **Profile** (identical in all three; a `HPROFILE` JSON, `batches/p1c_img/profile.json`):
  1. take-off to 2.0 m: **the CLIMB segment** (the natural GUIDED take-off, as in the D22 flights);
  2. **the first hover, with two climb cycles inserted** (change made 2026-10-10, BEFORE any flight). The reason: a
     single take-off climb may not produce a climb bias of 0.10 rad/s, and A3 would then go untested. The sequence:
     hold 10 s (**HOVER**); then 2.0 → 3.5 → 2.0 → 3.5 → 2.0 m at 1.1 m/s (**CLIMB**, both directions), with a 3 s
     hold at each turn (not scored); then hold 10 s (**HOVER**). The climb rate is the take-off climb rate measured on
     `cl_fgo_b_tex_r3_half_v3` (mean 1.11 m/s over z 0.3–1.9 m; peak 1.41 m/s). 3.5 m stays well below the 5 m walls,
     and these corridor worlds have no ceiling. A new profile segment type, `alt`, was added to `fly_trial.py` for
     this (it is additive: existing segments send byte-identical setpoints; mock-tested);
  3. move to N = 90 m, E = 0 at 0.5 m/s (~180 s; it crosses the transition boundary at y = 80 m): **CRUISE**;
  4. hold 20 s: a second **HOVER**;
  5. land.
- **Cost:** ~6 min of sim time per flight, ~10 min wall time with set-up, so **~35 min for the three**.
  - Images: ~8 GB per flight (~24 GB; 249 GB free).
  - Recording 30 Hz images loads the machine. The RTF is logged and reported, but no band depends on it.
- **Schedule:** after the SITL safety re-tests, before the overnight FGO-only re-run. If they would delay the
  re-run's completion before 16 Oct, they fly after the re-run instead, and the user is told.

## 2. Measurement

1. **Reproduction gate (first, mandatory):** an offline replay of `flow_tracker.py`'s exact algorithm on the
   recorded images (same parameters, same RANSAC seed) must reproduce the PUBLISHED median-feature flow bit for bit,
   apart from each bag's first frame. If it does not, STOP and report. No comparison is made.
2. **Both methods from the same replay, on the same frames:**
   - **M** = the current median-feature flow;
   - **A** = the fitted transform's translation at the principal point (option a).
   - Frames are those valid under the CURRENT count rule (feature count ≥ 20), so both methods see the identical
     frame set.
3. **Ground-truth flow:** the analytic model from `/ground_truth/pose`. It is body-frame velocity over the camera
   height (h_cam = GT z − 0.25 m, tilt-corrected) plus the body-rate terms, in the sign convention verified in
   METHODOLOGY ("FINDING — lateral optical-flow sign"; Stage A for the forward axis).
   - **Truth-model sanity gate:** on the textured CRUISE segment, the slope of M against truth on the forward axis
     must lie within 0.85–1.15 (the known flow scale error is about +8–13%). Outside that range, STOP: the truth
     model is wrong, not the method.
4. **Segments** (from GT and the profile log):
   - **CLIMB:** the take-off (from GT z ≥ 0.3 m to the first time z ≥ 1.9 m) PLUS the four `alt` ramps (from each
     `HSEG … alt START` to its `ALT reached` log line, excluding the first and last 0.3 s of each ramp). Ascents and
     descents are pooled for A3; the bias is also reported per direction;
   - **HOVER:** both holds, excluding the first 3 s of each;
   - **CRUISE:** the move segment, excluding the first and last 3 s.
   - **The floor class is per frame:** textured, or blank in the transition world for y > 80 m.
5. **Metrics,** per method, axis (x, y), segment and floor class:
   - bias = the mean of (flow − truth);
   - RMS of (flow − truth);
   - and n.

## 3. Pre-registered acceptance bands (textured-floor frames, pooled over `p1c_img_tex` and the textured half of `p1c_img_trans`)

| ID | segment | criterion (both axes) |
|---|---|---|
| A1 | HOVER | RMS(A) ≤ 1.10 × RMS(M) + 0.005 rad/s |
| A2 | CRUISE | RMS(A) ≤ 1.10 × RMS(M) + 0.005 rad/s, and \|bias(A)\| ≤ \|bias(M)\| + 0.01 rad/s |
| A3 | CLIMB | \|bias(A)\| ≤ 0.05 rad/s, and \|bias(A)\| ≤ 0.25 × \|bias(M)\|. **Applies only if \|bias(M)\| ≥ 0.10 rad/s** on that axis. Otherwise A3 for that axis is reported as **"not tested: no climb bias present"**, which is not a pass |
| A4 | all | n(A) = n(M) (option a drops no frames by construction; checked) |

- **ADOPT** iff A1, A2 and A4 pass on both axes, and A3 passes on every axis where it is tested.
- **If A3 is untested on both axes:** do NOT adopt on these flights. Report it; the climb bias would not have been
  shown removed.
- **Blank floor:** reported only (few valid frames), with no band.

## 4. Backstop (b) thresholds (set here, on these flights only)

- **Inputs:** the fitted transform's scale s and rotation θ per frame, against GT.
  - expected scale: 1 − (ż/h_cam)·Δt;
  - expected rotation: the body yaw-rate integral.
- **Implausibility thresholds = the 99.5th percentile** of |s − s_expected| and |θ − θ_expected| over the textured
  HOVER plus CRUISE plus CLIMB frames.
- **Reported:** the fraction of textured frames the backstop rejects (it must be ≤ 1%; otherwise the thresholds are
  reported without adoption), and what it rejects on blank.

## 5. Outputs

- `eval/results/p1c_img_validation.json`, the figures in `plots/p1c_img/`, and a handover.
- METHODOLOGY records the verdict as worded.
- **Adoption is a separate user ruling after the report.**

## 6. Launcher pass-through (confirmed 2026-10-10, before any flight)
- `tools/run_p1c_img.sh {tex,trans,blank}` sets `HPROFILE` and `EXTRA_RECORD_TOPICS` in `run_trial.sh`'s environment.
  `run_trial.sh` does not touch `HPROFILE`, so `fly_trial.py` inherits it. After the take-off `wait_altitude`,
  `main()` takes the `HPROFILE` branch (`fly_trial.py:875`), then `stop()` and land.
- `HWORLD` is used only by the occluder segment (unused here). `WATCH_HEARTBEAT` is not set, so the room-world
  watcher and the pre-arm tag gate do not apply.
- **The driver checks the flight log for "HPROFILE: 11 segments" and STOPS if it is missing,** so a failed
  pass-through cannot go unnoticed.
- **The `alt` segment was mock-tested offline:** the setpoints ramp 2.0 → 3.5 → 2.0 m with vz feed-forward
  ∓1.1 m/s, and the hold/move setpoints are unchanged. It is first exercised in flight on `p1c_img_tex`.
