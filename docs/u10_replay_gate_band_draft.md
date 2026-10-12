# U10: the Replay gate on rung-1 logs. DRAFT pre-registration for the user's sign-off

**Status: DRAFT, written 2026-10-12 (stage `2026-10-12_port_merge_u4_drafts`). NOT in force.**
- **It must be SIGNED OFF before rung-1 day 3** (ruling 2026-10-12 item 1; plan U-d0). Day 3 is the first day a real
  log with the UKF port replayed on it can exist (the hand-carried pass).
- If it is signed later, any UKF Replay of a real log made before the sign-off makes the gate **post hoc**. That is the
  E5 failure class, and it would be reported as such.
- No real log exists yet. Every number below comes from SITL evidence or from existing pre-registered bands, cited per
  line.
- **Updated 2026-10-12 (stage `2026-10-12_xuko_u10_h10`, ruling 5), still a DRAFT for sign-off this week.** Changed:
  1. §2: the binary is now `ukf-jitter-fix` = `xuko-fmt` `0a214d29d3`, installed Replay `e82c050b…`.
  2. §3: the scored record is the **FMT-declared `XUKO` in the Replay output log** (open item R-d CLOSED). The
     `ukf_shadow.csv` fallback (`UKF_horizon`) is removed. In Replay, XUKO's TimeUS is now the DAL frame time.
  3. §3: a fork-flown input interleaves the onboard and the replayed XUKO under one FMT. The scorer refuses that, so
     G6 takes its Replay side from `ukf_shadow.csv` (new paragraph).
  4. §3 and **G3**: `_n_chol_fail` / `_n_chol_retry` come from the Replay's new `ukf_stats.csv` (and its end-of-run
     stdout line). The precondition is MET. A missing `ukf_stats.csv` (a run that did not end normally) fails G3.
  5. §7 item 1: the R-d choice and the counter output are settled; only the signature, D_max and the volume remain.
  No band, criterion, set rule or threshold changed.

Implements:
- `docs/ukf_only_closed_loop_costing.md` §7 (U10);
- `docs/realflight_plan_copter.md` §4.3 U-d0 and §5 item 17a;
- METHODOLOGY "RULINGS (user, 2026-10-12)", items 1–3.

Labels: **[V]** verified (source, a build or a stored result); **[E]** an estimate; **[TBD-S]** supervisor or
hardware input, fixed before day 3; **[TBD-V]** fixed once on VERIFICATION logs before any RESULT log is gated.

---

## 1. What the gate decides

**The question:** may the onboard UKF steer the real vehicle (the stage-3 closed loop)?
- It is the strongest evidence available without flying the UKF: the identical C++ code, on the real sensor data and
  the real IMU of the rung-1 flights.
- **Gate PASS** is a precondition of the stage-3 free flights (`docs/stage3_ukf_closed_loop_preregistration_draft.md`
  §5). It does not by itself authorise them; the bench, SITL and tether gates there still apply.
- **Gate FAIL** stops the stage-3 programme at that point. It is reported with the failing criterion and the
  per-flight values. The gate is never re-run with a changed band. A code fix produces a NEW binary, which needs a new
  dated gate run (§7).
- **It is not a rung-1 result.** The rung-1 UKF row is scored by the signed-off rung-1 pre-registration. This gate
  re-uses the same Replay outputs with its own pass/fail criteria.

## 2. What is replayed

- **The binary:** the fork's `Tools/Replay`, built from the branch that will fly in stage 3, recorded by commit and
  md5.
  - Today that is `ukf-jitter-fix` = `xuko-fmt` `0a214d29d3` (= `rung1-geometry` `16535f9a29` + the XUKO FMT and
    stamp fix + the Cholesky counters; Replay-only changes). It was installed on 2026-10-12 as Replay `e82c050b…`,
    replacing `be7c4d18…` [V]. Its four CSVs are byte-identical to `be7c4d18`'s on the five SITL logs, and UKF_Equiv
    is 10/10 identical (`eval/results/xuko_fmt/`).
  - It also carries U4 (`u4-gndclr` `53bac01636`) and `board-h743`, if those are merged before the gate runs.
  - The Replay used must come from the same source commit as the board image. The two differ only in the
    `#if` paths, which are compiled out (`AP_NAVUKF_REPLAY_IO_ENABLED`).
- **The input logs (run in this order, recorded before scoring):**
  1. the hand-carried log (H, rung-1 day 3): **plumbing only**, no pass/fail beyond G1 and G3. The vehicle is
     disarmed and EKF3 does not flow-aid;
  2. the first-hover log(s) (V, day 4): the **[TBD-V]** calibration of the G6 band (§4), and G1–G3;
  3. every **usable rung-1 result flight** (R1…Rn, after the rung-1 §3.3 exclusions): **the gate proper**.
- **The environment:** the defaults only. That is the D18 own-bias derotation and the geometry from the log's PARM,
  with no `UKF_GEOM_SITL`, no `UKF_DEROT_ROFH` and no test hook.
  - **Sensitivity row, reported and not gated:** the same Replay with `UKF_DEROT_ROFH=1`. It derotates with the
    flow's paired gyro as delivered. See the multi-IMU caveat, §6.

## 3. The scored record

- **Primary:** the replayed **`XUKO`** (current-time output, the like-for-like counterpart of `XKF1`). This is the
  signed-off rung-1 UKF record.
- **Source (R-d CLOSED, 2026-10-12, ruling 4): the FMT-declared `XUKO` record in the Replay output log**, read by
  `eval/df_reader.py` (`real_score.py --est-bin UKF=XUKO`).
  - **The fix (installed Replay `e82c050b`):** Replay now writes the FMT and FMTU of every UKF record it emits
    (XUKF, XUKO, XUKS, XUKH, XUKT; `AP_Logger::WriteV` under `APM_BUILD_Replay`).
  - **Verified on `cl_a_tex_half` [V]:**
    - XUKO is decodable by df_reader and by both pymavlink readers;
    - 0 undeclared types and 0 skipped bytes;
    - pymavlink reads all 2 684 XKF1 per core again;
    - `replay_gate.py` and the scorer run on it.
  - **XUKO's TimeUS in Replay is the DAL frame time** (the replayed frame's logged time, the clock `XKF1` uses).
    - Before the fix it was the Replay PROCESS clock: 0.025–3.14 s over a 270 s flight, different on every run.
    - Onboard, the flying port stamps `AP_HAL::micros64()` at the write. That differs from the frame time by at most
      one loop.
    - Check [V]: XUKF interpolated at the XUKO stamps agrees with XUKO to a p99 of 5 mm horizontal.
  - **The `ukf_shadow.csv` fallback (`UKF_horizon`) is withdrawn.** `UKF_horizon` (`XUKF`) stays a reported
    secondary row, as in the rung-1 pre-registration.
- **Fork-flown input logs** (any log the fork flew, with the UKF in shadow or active: stage-3 logs, or rung 1 if the
  fork-in-shadow option is taken):
  - the output then carries the onboard XUKO/XUKF, copied through, AND the replayed ones, interleaved under one FMT;
  - verified on `cl_ukf_b_tex_r1_half_v2`: 17 077 XUKO, not increasing;
  - the scorer refuses such a series (`real_score.bin_trajs`).
  - **So for G6, the Replay side is `ukf_shadow.csv` (= the replayed `XUKF`), and the onboard side is `XUKF` read
    from the INPUT log.** The G1–G5 rows of a fork-flown log use `ukf_shadow.csv` for the horizon state. For the
    current-time output they need the port to separate the replayed records (port spec §S2a: a different name or an
    instance field). That is not built; a gated fork-flown log would then be scored on `UKF_horizon`, labelled.
- **Flags and health:** from `ukf_shadow.csv`:
  - `SS` (the nav_filter_status bits);
  - `Healthy`;
  - `FlowAgeMs` (ms since the last accepted flow);
  - `FXa`, `FYa`, `Ra` (accepted counts).
- **Numerical health:** `_n_chol_fail` (Cholesky failures after all jitter retries) and `_n_chol_retry`.
  - **Precondition MET (2026-10-12, installed Replay `e82c050b`)** [V]. At the end of every run, Replay writes both
    counters:
    - a NEW file `ukf_stats.csv` (`name,value` rows `n_chol_retry`, `n_chol_fail`);
    - the stdout line `thesis shadow UKF: end of run: n_chol_retry=N n_chol_fail=M` (in `replay.log`).
  - The four existing CSVs are unchanged: byte-identical to `be7c4d18` on the five SITL logs. All five SITL logs give
    0 / 0.
  - The first retry still sends its GCS text ("UKF: Cholesky needed jitter (first fallback)").
  - **G3 reads `n_chol_fail` from `ukf_stats.csv`.** The file is written only when Replay reaches the end of the log.
    A missing file means the run did not end normally, and G3 FAILS for that flight.
  - (Before the fix, no Replay output carried either counter; only `examples/UKF_Equiv` printed them.)
- **Truth:** mocap via `eval/mocap_align.py` with its default (disarmed-wiggle) windows, exactly as in rung 1.
- **The window W:** rung 1's §4.2 rule (`[t_to + 25 s, t_ld − 5 s]`, from mocap only).

## 4. Pass criteria (per gated flight)

| # | criterion | band | basis |
|---|---|---|---|
| **G1** | **Initialises before arming.** `ukf_geometry.csv` resolved with every geometry source `log_parm`. 0 late-PARM warnings, or each one listed and shown not to change a value | must hold | the arming gate in type 12 needs an initialised UKF (`AP_AHRS_UKF::pre_arm_check`). If the rangefinder reads below its minimum on the ground, this needs U4 (`u4_init_from_gndclr` line) |
| **G2** | **Stays valid through the hover and the legs:** `SS` bit 3 (`horiz_pos_rel`) set and `Healthy` = 1 on **every** row in W; `FlowAgeMs` < 5000 throughout W | 100 % of W | in closed loop a 5 s aiding gap (`AID_TIMEOUT_MS`) makes `thesis_nav_check` command LAND. A gap in Replay means a LAND in stage 3 |
| **G3** | **No numerical failure:** `n_chol_fail` = 0 over the whole log, read from the Replay's `ukf_stats.csv` (missing file = FAIL). `n_chol_retry` is reported | = 0 | the jitter fix (2026-10-09): 0 fallbacks on all SITL data [V]; the counters in the Replay output since `e82c050b`: 0 / 0 on the five SITL logs [V] |
| **G4** | **Accuracy against mocap:** UKF evo -a (SE(3), `t_max_diff` 0.05) over W ≤ **max(2.0 × EKF3_R, EKF3_R + 0.10 m)**, with EKF3_R = the replayed EKF3 (`XKF1@100`) on the same flight and window | per flight | see below |
| **G5** | **Bounded unaligned drift:** the start-aligned horizontal drift (rung-1 §4.3 rule) at t_ld − 5 s ≤ **D_max = [TBD-S] m** (proposed 1.0 m: half the smallest watcher-box half-width expected in a mocap volume) | per flight | a closed loop steers on the unaligned estimate; this is the physical excursion it would cause |
| **G6** | **Replay fidelity:** ONLY if rung 1 flew the fork in shadow (an onboard `XUKF` exists; costing §13 option). Replay `XUKF`/CSV against onboard `XUKF`: E1 horizontal max ≤ 0.05 m, rms ≤ 0.01 m; E3 yaw ≤ 0.05°; E5 accepted-count increments within 0.1 % | per flight, **[TBD-V]** | see below |

**Set rule:** **the gate PASSES only if G1–G5 (and G6 where it applies) hold on EVERY usable result flight**, with at
least 4 usable flights.
- This is a safety gate, so one failing flight fails it. A failure is never averaged away.
- With fewer than 4 usable flights the gate is **NOT EVALUABLE**. More rung-1 flights are needed, flown under the
  rung-1 rules; none is re-flown because of a UKF result.

**Basis of G4:**
- **SITL, textured, open-loop UKF against EKF3 on the same flight.** These are per-flight ratios of evo -a (cruise),
  recomputed 2026-10-12 from `eval/results/rerun_dsn_evo.json`, `dsn_extra_evo.json`, `rerun_fwdc_evo.json` and
  `rerun_fwdplainc_evo.json`:
  - `dsn_tex` r1–r9: 0.99, 0.42, 1.26, 1.27, 1.24, 0.38, 1.27, **1.43** (r8), 1.23. **Every one is ≤ 1.43;**
  - `fwdc_tex` r1–r3: 1.21, 0.49, 1.22;
  - `fwdplainc_tex` r1–r3: 1.23, **2.76, 2.65**. r2 and r3 are the D15 residual take-off-kick flights.
- **The factor 2.0** therefore passes every SITL textured flight except the two take-off-kick flights. Those are
  exactly the behaviour a closed-loop gate should catch.
- **The + 0.10 m floor** keeps the band meaningful when EKF3 itself is near the mocap and alignment floor on a short
  flight. That is likely on 90 s of cruise, where the SITL numbers (150 m corridors) do not transfer. The 0.10 m is
  [E]: several times the expected alignment residual (mm) and below a leg width.
- **EKF3 is the reference because it already flies this vehicle stably** (rung 1 is flown on it). A UKF within the
  band of an estimator known to fly is the claim the gate needs. It is not an accuracy-ordering claim.

**Basis of G6 (only with the fork-in-shadow option):**
- **The bands are the existing port-equivalence bands** (METHODOLOGY step 1, 2026-09-30), unchanged.
- On SITL, Replay against the flying port gave:
  - E1 max 0.0184 m / rms 0.0032 m, E3 0.0049° on `cl_ukf_b_tex_r1_half_v2` (max at 9.5 s, just after initialisation);
  - 0.00055 m / 0.00006 m, 0.0006° on `H_s2v2_r1` [V, `eval/results/r1_ukf_port/b_*.json`].
- **Adapted to real logs, declared here before any data:**
  - Pairing starts at the LATER of the two initialisations + 10 s. In SITL the Replay UKF initialised 1.0 s after the
    flying one (a pre-existing offset; this is what made E5 fail as worded on 2026-10-11).
  - **E5 uses the increment form** over the paired window, pre-registered here. On 2026-10-11 it was adopted post hoc.
  - **Board ≠ x86 numerics** (Cortex-M7 double, FMA contraction, compiler): bit-identity is not expected. As in
    rung 1 §5, the E1/E3 bounds are confirmed or widened **ONCE**, on the H and V logs, with the reason recorded,
    before any result log is gated. Never after.
- **Without the fork-in-shadow option, G6 does not apply.** Stock rung-1 firmware runs no UKF. The gate then tests
  the replayed UKF against mocap only, and **Replay-to-board fidelity is first tested in stage 3** (the stage-3
  hand-carried and tethered steps log `XUKF` onboard and replay them; stage-3 §5 S9).

## 5. Reported with the gate (no pass/fail)

- **The heading drift rate**, deg/min, UNALIGNED: the UKF yaw against mocap yaw over W, with a linear fit. Also the
  cross-track drift per minute.
  - These are the signed-off rung-1 secondaries (ruling 2026-10-12 item 2).
  - **They feed the stage-3 predictions** (stage-3 §6): the predicted physical excursion is computed from the
    largest |heading drift| over the gated flights.
- The flow and range acceptance fractions (`FXa`/`FYa`/`Ra` against delivered), and the D15 replaced-flow count.
- The `UKF_DEROT_ROFH=1` sensitivity row: G4 and G5 values and the per-flight difference.
- The take-off kick: the UKF yaw step in the 5 s after the take-off detector latches. The SITL kicks were −1.4 …
  −4.4°.
- Whether the U4 path was used (`u4_*` lines), and the resting range against `RNGFND1_MIN`.

## 6. Stated caveats

1. **Multi-IMU boards (the open item of `2026-10-11_r1_ukf_port.md` §2).**
   - On a type-3 (EKF3-flown) rung-1 log the D18 rule swaps the flow's paired-gyro bias. `b_active` is Replay EKF3's
     PRIMARY-core bias (`getGyroBias(-1)`), and `ROFH.G` comes from the AHRS gyro of that core's IMU.
   - The UKF's own `b_own` is for `get_first_usable_gyro()`. **If the board has two or more IMUs and EKF3's primary
     core is not on the UKF's IMU, the swap mixes IMUs.** The derotation then carries the inter-IMU bias difference
     Δb. That is a velocity error ≈ h·Δb (about 1.2 mm/s for h = 1.2 m and Δb = 1 mrad/s) and a drift of about 0.1 m
     over 90 s [E].
   - **Recorded for every gated log:** the IMU count, `EK3_IMU_MASK`, `EK3_PRIMARY`, the primary core in use (`XKF4`
     core index / `XKFS`), and `INS_USE*`.
   - The `UKF_DEROT_ROFH=1` row bounds the effect: it uses the delivered gyro, whose bias is EKF3's on the same IMU as
     `ROFH.G`.
   - **If the primary core is not on the UKF's IMU, the gate result is labelled "IMU-mixed derotation" and the
     sensitivity row is reported next to it.** The plan's U-i fix (compare per IMU, or pin the IMUs) is the remedy. If
     it is applied before day 3, this caveat lapses and that is recorded.
2. **Replay derotation ≠ closed-loop derotation.**
   - In Replay of an EKF3-flown log the swap is active.
   - In stage 3 (type 12) the rule is the identity: the UKF's own `gyro + drift`.
   - The gate therefore tests the swap path, not the exact flying path. **Flying with the swap active (UKF shadow
     under EKF3) has never been logged**; SITL V1 is the first such log (plan §4.2).
3. **Own-gyro flow sensors** (FLOW_TYPE 1, 3, 6, 10) are used as delivered, with a warning, pending a ruling (plan
   U-h). If the rung-1 sensor is one of these, the gate is labelled accordingly.
4. **Open loop.** The gate replays an EKF3-flown trajectory. A UKF error that would change the flown path in closed
   loop (the kick, the drift) is measured here only as an estimate error. Stage 3 measures the physical consequence.
5. **Flow timing.** The port fuses flow at EKF3's time (`EK3_FLOW_DELAY` from the log) unless the capture-delay option
   (R-c) is built and selected. Whichever is used in the rung-1 UKF row is used here, and it is stated.
6. **Short flights.** About 90 s of cruise in a mocap volume. The long-duration drift is not tested.

## 7. Procedure and records

1. **Before day 3:**
   - this document signed (§9);
   - ~~the R-d choice of record and the `_n_chol_fail` output settled (§3)~~ DONE 2026-10-12 (Replay `e82c050b`):
     the FMT-declared XUKO, and `ukf_stats.csv`;
   - the Replay binary built and its md5 recorded;
   - D_max and the volume entered (**[TBD-S]**).
2. **Days 3–4 (verification logs):** G1–G3 plumbing; the G6 bounds confirmed or widened once (only with the
   fork-in-shadow option); the reason recorded.
3. **Day 6 (after the rung-1 result flights, rung-1 §8 step 4):**
   - the gate run on every usable result flight, with the same Replay outputs the rung-1 UKF row uses;
   - results to `eval/results/u10_gate/<flight>.json`;
   - a METHODOLOGY entry with PASS / FAIL / NOT EVALUABLE.
4. **A binary change after the gate** (any fix) means a NEW gate run on the same logs with the same bands, dated. Both
   results are reported. A pass on the new binary is labelled "after fix <commit>".

## 8. What the gate does NOT claim

- No accuracy ordering of the UKF against EKF3 or the FGO. That is the rung-1 pre-registration's job.
- No closed-loop stability claim.
- No claim about other floors (rung 1 is textured; the exploratory plain-sheet set, if flown, is not gated).

## 9. Sign-off

| | name | date | changes requested |
|---|---|---|---|
| user | | | |
| supervisor (informed) | | | |

Once signed, this file is copied to `docs/u10_replay_gate_band.md` (status PRE-REGISTERED). A METHODOLOGY entry records
the commit. Any later change is a dated amendment, made before the affected logs are gated.
