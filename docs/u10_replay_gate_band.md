# U10: the Replay gate on rung-1 logs. FOR FINAL SIGN-OFF

**Status: SIGNED OFF by the user on 2026-10-12, including N1–N6, with D_max = 1.0 m (basis: half the 2 m clearance required at every hold point). IN FORCE from 2026-10-12, before rung-1 day 1.** (Written as "for final sign-off" by stage `2026-10-12_u10_final`.)
- It must be SIGNED OFF before rung-1 day 3 (ruling 2026-10-12 item 1; plan U-d0). Day 3 is the first day a real log
  with the UKF port replayed on it can exist. A UKF Replay of a real log made before the signature makes the gate
  **post hoc** (the E5 failure class), and that would be reported.
- It supersedes `docs/u10_replay_gate_band_draft.md`, which is kept unchanged for the record. Every change from the
  draft is listed in §0.2.
- No real log exists yet. Every number comes from SITL evidence or an existing pre-registered band, cited per line.

Labels: **[V]** verified (source, a build or a stored result); **[E]** an estimate; **[TBD-S]** supervisor or
hardware input, fixed before day 3; **[TBD-V]** fixed ONCE on the verification logs (H, V) before any result log is
gated.

---

## 0. One-page summary

**The question.** May the onboard UKF steer the real vehicle (stage 3)? The gate replays the identical port code on
every usable rung-1 result flight and checks, per flight:

| # | criterion | band | data source |
|---|---|---|---|
| G1 | initialises before arming, geometry from the log | must hold | `ukf_geometry.csv`; `ukf_shadow.csv` row 1; the log's `ARM` |
| G2 | valid throughout W: `horiz_pos_rel`, healthy, flow age | 100 % of W | `ukf_shadow.csv` `SS` bit 3, `Healthy`, `FlowAgeMs` |
| G3 | no Cholesky failure | `n_chol_fail` = 0; **a missing `ukf_stats.csv` FAILS** | `ukf_stats.csv` |
| G4 | accuracy against mocap | UKF evo -a ≤ max(2.0 × EKF3_R, EKF3_R + 0.10 m) | `real_score.py`: UKF = `XUKO` (message `RUKO`), EKF3_R = `XKF1@100` |
| G5 | bounded start-aligned drift at t_ld − 5 s | ≤ D_max = **1.0 m** (signed 2026-10-12) | `real_score.py` `drift_start_aligned.final_h_m` |
| G6 | Replay fidelity (fork-in-shadow only) | E1 3-D max ≤ 0.05 m, rms ≤ 0.01 m; E3 ≤ 0.05°; E5 ≤ 0.1 % **[TBD-V]** | the Replay output log: `RUKF`/`RUKS` vs `XUKF`/`XUKS` |

**Set rule.** PASS only if every gated flight passes G1–G5 (and G6 where it applies), with at least 4 usable result
flights; fewer than 4 → NOT EVALUABLE; one failing flight fails the gate. All flights replayed by ONE Replay binary.

**Scoring command** (§7): `eval/real_score.py` with the signed rung-1 pre-registration, then
`eval/u10_gate.py flight ... --d-max <D_max>` per flight, then `eval/u10_gate.py set ...`.

**The binary.** Port `ukf-jitter-fix` = `replay-rukx` `f30f6ffa2f`, installed 2026-10-12 as Replay
`3c3b62bbe51d515b6ff0789a19fe1136` [V].

### 0.1 The two U10 rules (ruling 2026-10-12 items 2 and 3)

1. **Rule 1 (APPROVED):** a missing `ukf_stats.csv` FAILS G3. It is written only when Replay reaches the end of the
   log; a missing file means the run did not end normally. Implemented in `eval/u10_gate.py` and tested (§8).
2. **Rule 2: the PREFERRED option was done.** Replay now writes the UKF's records under DISTINCT names:
   `RUKF`, `RUKO`, `RUKS`, `RUKH` and `RUKT`. The flying port keeps `XUKF`, `XUKO`, `XUKS`, `XUKH` and `XUKT`.
   - So the onboard and the replayed records of a fork-flown log can no longer interleave.
   - The fallback (score fork-flown logs on `UKF_horizon`) is **not needed and is withdrawn**.
   - **Why a name and not an instance field (EKF3's `C` = 100):** the UKF records have no core field.
     - Adding one only in Replay would put two FMTs named `XUKO` with different formats in one log, and both df_reader
       and pymavlink merge records by name.
     - Adding it to the flying port as well changes the flying log format. That needs a copter and board rebuild, and
       the existing fork-flown logs would lack it.
     - The rename is one file and a few lines (port commit `f30f6ffa2f`), compiled only into Replay.
   - **Verified (§8):** CSVs byte-identical to `e82c050b` on 5 SITL logs; logs decodable by df_reader and pymavlink;
     on fork-flown logs the two streams are separate and the scorer picks the replayed one; UKF_Equiv unchanged.

### 0.2 What changed from the draft (all need the signature; items N1–N6 in point 4 are NEW decisions)

1. **§3 record source:** the registered `XUKO` / `XUKF` (the replayed UKF, as the signed rung-1 pre-registration names
   them) are READ from the messages `RUKO` / `RUKF` in a Replay output from `f30f6ffa2f` on.
   - `docs/rung1_preregistration.json` is NOT changed.
   - `real_score.py` maps the names and writes both the registered record and the physical message into its output.
   - The onboard records are named explicitly, `XUKO@onboard` / `XUKF@onboard`.
2. **§3 fork-flown inputs:** scored on the replayed `XUKO` (`RUKO`) like any other log. The draft's conditional
   `UKF_horizon` fallback is withdrawn. G6 reads both of its sides from the ONE Replay output log (`RUKF`/`RUKS`
   replayed, `XUKF`/`XUKS` onboard, copied through), not from `ukf_shadow.csv` and the input log.
3. **G3:** rule 1 written into the criterion.
4. **NEW DECISIONS, not wording. The user approved rules 1 and 2 only; each item below needs its own signature.**
   They were implicit or absent in the draft. They are written out in §4.1 and implemented as written.
   - **(N1) G5 "not computable = FAIL".** When the rung-1 drift rule refuses its initial segment (it moves < 1.0 m
     horizontally), G5 FAILS the flight. **This one can change a verdict:** the SITL `H_s2v2_r1` demo fails on it.
     The alternative would be to count such a flight as not usable. That is not chosen here, because a safety gate
     should not pass on a missing number.
   - **(N2) G2 coverage of W.** "Throughout W" is read as: the `ukf_shadow.csv` rows cover W, with no gap (including
     the gaps to W's two ends) longer than the rung-1 `max_gap_s` (0.5 s).
   - **(N3) G1 late-PARM rule.** A late geometry PARM passes only if:
     - it repeats the value in use for one of the five resolved parameters; or
     - it is a lever arm (`FLOW_POS_*`, `INS_POS*`, `RNGFNDn_POS_*`), which the port takes per sample from the sensor
       records.
     - Any other late parameter (e.g. `RNGFND2_MIN`) fails G1. In a gated (armed) flight, a missing `ARM` record also
       fails G1. The draft said "each one listed and shown not to change a value"; this makes that rule mechanical.
   - **(N4) Single binary.** Every flight in the set must carry the same Replay md5 (`binary.md5`). Mixed → INVALID; a
     missing md5 is refused.
   - **(N5) Score↔log precondition.** The score JSON must have been computed on the same Replay output .BIN (sha256),
     with UKF = `XUKO`/`RUKO` and EKF3 = `XKF1@100`. The log must have 0 undeclared types, 0 bad FMT and 0 re-declared
     ids. Otherwise the flight fails.
   - **(N6) G6 E1 is 3-D, not "horizontal".**
     - The draft's table said "E1 horizontal max ≤ 0.05 m". But its basis says "the existing port-equivalence bands,
       unchanged".
     - That band is the 3-D position difference (METHODOLOGY "UKF port validation, step 1": "E1 | 3-D position
       difference"), and the cited SITL numbers (0.0184 m, 0.00055 m) are 3-D.
     - 3-D is the stricter reading.
5. **Definitions written out with no new decision (§4.1):** "initialises before arming" (the first UKF row and the
   geometry resolution both before the first ARM), the G1 source labels required, G6 pairing (exact TimeUS from the
   later first record + 10 s) and the E5 increment arithmetic. These are as the draft stated, made exact.
6. **The tool:** `eval/replay_gate.py` was checked against this document.
   - It does NOT implement U10. It is the rung-1 §5 EKF3 Replay-fidelity check (`XKF1@0` against `XKF1@100`), and it
     implements rung-1 §5 exactly [V].
   - G1–G6 and the set rule are implemented in a NEW `eval/u10_gate.py` (§7). `replay_gate.py` is unchanged; its
     result is reported per flight (§5), and it is not a U10 criterion.
7. **§2:** the binary is now Replay `3c3b62bb` (`replay-rukx` `f30f6ffa2f`).
- **Unchanged:** every band, threshold and factor (G2 5000 ms, G4 2.0 × / + 0.10 m, G5 proposed 1.0 m, G6 bands),
  the set rule (≥ 4 flights, every flight must pass), the window W, the truth, the caveats and the procedure.

---

## 1. What the gate decides

**The question:** may the onboard UKF steer the real vehicle (the stage-3 closed loop)?
- It is the strongest evidence available without flying the UKF: the identical C++ code, on the real sensor data and
  the real IMU of the rung-1 flights.
- **Gate PASS** is a precondition of the stage-3 free flights (`docs/stage3_ukf_closed_loop_preregistration_draft.md`
  §5). It does not by itself authorise them; the bench, SITL and tether gates there still apply.
- **Gate FAIL** stops the stage-3 programme at that point. It is reported with the failing criterion and the
  per-flight values. The gate is never re-run with a changed band. A code fix produces a NEW binary, which needs a new
  dated gate run (§9).
- **It is not a rung-1 result.** The rung-1 UKF row is scored by the signed-off rung-1 pre-registration. This gate
  re-uses the same Replay outputs with its own pass/fail criteria.

## 2. What is replayed

- **The binary:** the fork's `Tools/Replay`, built from the branch that will fly in stage 3, recorded by commit and
  md5.
  - Today: `ukf-jitter-fix` = `replay-rukx` `f30f6ffa2f` (= `xuko-fmt` `0a214d29d3` + the U10 rule-2 rename). It was
    installed on 2026-10-12 as Replay `3c3b62bbe51d515b6ff0789a19fe1136`, replacing `e82c050b…` [V]. UKF_Equiv is
    unchanged (`fe548d36…`, byte-identical after recompiling the file). The SITL copter (`5f94ea1a…`) was not
    rebuilt: the change compiles only into Replay.
  - Backup of the replaced binaries: `~/opt/ukf_port_backup_e82c050b_2026-10-12/`.
  - It also carries U4 (`u4-gndclr` `53bac01636`) and `board-h743`, if those are merged before the gate runs. **Both
    branches now need a rebase onto `f30f6ffa2f`** (no overlapping hunks expected; `board-h743` also needs
    `write_end_stats()` inside `AP_NAVUKF_REPLAY_IO_ENABLED`, handover `2026-10-12_xuko_u10_h10.md` §1.6).
  - The Replay used must come from the same source commit as the board image. The two differ only in the `#if` paths,
    which are compiled out (`APM_BUILD_Replay`, `AP_NAVUKF_REPLAY_IO_ENABLED`).
- **The input logs (run in this order, recorded before scoring):**
  1. the hand-carried log (H, rung-1 day 3): **plumbing only**: G1 and G3, no other pass/fail. The vehicle is disarmed
     and EKF3 does not flow-aid. `u10_gate.py flight` without `--score` (verdict "PLUMBING PASS/FAIL");
  2. the first-hover log(s) (V, day 4): the **[TBD-V]** confirmation of the G6 bands (§4), and G1–G3;
  3. every **usable rung-1 result flight** (R1…Rn, after the rung-1 §3.3 exclusions): **the gate proper**.
- **The environment:** the defaults only. That is the D18 own-bias derotation and the geometry from the log's PARM,
  with no `UKF_GEOM_SITL`, no `UKF_DEROT_ROFH` and no test hook.
  - **Sensitivity row, reported and not gated:** the same Replay with `UKF_DEROT_ROFH=1`. It derotates with the
    flow's paired gyro as delivered. See the multi-IMU caveat, §6.

## 3. The scored record

- **Primary:** the replayed **`XUKO`** (the current-time output, the like-for-like counterpart of `XKF1`). This is the
  signed-off rung-1 UKF record.
- **Where it is read from (R-d CLOSED; U10 rule 2 DONE):** the Replay output log, message **`RUKO`**, read by
  `eval/df_reader.py` through `eval/real_score.py --est-bin UKF=XUKO`.
  - **Names.** From Replay `3c3b62bb` (`f30f6ffa2f`), Replay writes every UKF record under an R name: `RUKF`, `RUKO`,
    `RUKS`, `RUKH`, `RUKT`. Fields, units and values are unchanged.
    - In a Replay output, an `XUK*` record is therefore ALWAYS the onboard one, copied through from a fork-flown input.
    - `real_score.py` reads the registered `XUKO` / `XUKF` from `RUKO` / `RUKF`, and the onboard ones only when named
      `XUKO@onboard` / `XUKF@onboard`. Its output JSON gives both `record` and `physical_record`.
  - **Refusals** (`real_score.bin_trajs`):
    - a log with no `RUKO` but an `XUKO` (an older Replay's output, or a flight log), with the reason;
    - `XUKO@onboard` declared with a type id in Replay's own window [220, 230] (written by an older Replay);
    - any type id re-declared under a different FMT (new `df_reader` diagnostic `redeclared_ids`);
    - a non-increasing series, as before.
  - **FMT records:** Replay writes the FMT and FMTU of every UKF record it emits (since `e82c050b`); 0 undeclared types
    and 0 skipped bytes on all five SITL outputs [V].
  - **XUKO's TimeUS in Replay is the DAL frame time** (the replayed frame's logged time, the clock `XKF1` uses; since
    `e82c050b`). Onboard, the flying port stamps `AP_HAL::micros64()` at the write, which differs by at most one loop.
    Check [V]: `XUKF` interpolated at the `XUKO` stamps agrees with `XUKO` to p99 5 mm horizontal.
  - **`UKF_horizon` (`XUKF`, read from `RUKF`)** stays a reported secondary row, as in the rung-1 pre-registration.
  - **The signed rung-1 pre-registration is not edited.** Its §4.1 implementation note on where `XUKO` is read from
    describes the pre-rename source; the mapping (`XUKO` → message `RUKO`) is to be recorded there as a dated
    implementation note by the user (the record itself is unchanged).
  - **Scoring a FLIGHT log's own UKF** (a fork-flown flight log, not a Replay output) now needs `XUKO@onboard`; a plain
    `XUKO` is refused there with that reason.
- **Fork-flown input logs** (any log the fork flew, UKF in shadow or active):
  - the Replay output carries the onboard `XUKF`/`XUKO`/`XUKS`/`XUKH`/`XUKT` (copied through) AND the replayed
    `RUK*`, under different names and type ids;
  - they are scored like any other log: the gate's `XUKO` is the replayed `RUKO`;
  - verified on `cl_ukf_b_tex_r1_half_v2` and `H_s2v2_r1` [V]: the output's `XUK*` equal the input log's record for
    record; `RUKO` and `XUKO` are each strictly increasing; the scorer scores both separately.
- **Flags and health:** from `ukf_shadow.csv` (`SS`, the nav_filter_status bits; `Healthy`; `FlowAgeMs`, ms since the
  last accepted flow; `FXa`, `FYa`, `Ra`, the accepted counts). The same values are in `RUKS`.
- **Numerical health:** `n_chol_fail` (Cholesky failures after all jitter retries) and `n_chol_retry`, from the Replay
  run's `ukf_stats.csv` (`name,value` rows) and its end-of-run stdout line (`thesis shadow UKF: end of run:
  n_chol_retry=N n_chol_fail=M`, in `replay.log`). Both written at the end of the log only. 0 / 0 on all five SITL
  logs [V].
- **Truth:** mocap via `eval/mocap_align.py` with its default (disarmed-wiggle) windows, exactly as in rung 1.
- **The window W:** rung 1's §4.2 rule (`[t_to + 25 s, t_ld − 5 s]`, from mocap only), as `real_score.py` computes it
  (`window_s` in its output).

## 4. Pass criteria (per gated flight)

| # | criterion | band | basis |
|---|---|---|---|
| **G1** | **Initialises before arming, with the log's geometry** (definition §4.1) | must hold | the arming gate in type 12 needs an initialised UKF (`AP_AHRS_UKF::pre_arm_check`). If the rangefinder reads below its minimum on the ground, this needs U4 (`u4_init_from_gndclr` line) |
| **G2** | **Stays valid through the hover and the legs:** `SS` bit 3 (`horiz_pos_rel`) set and `Healthy` = 1 on **every** `ukf_shadow.csv` row in W; `FlowAgeMs` < 5000 on every row in W; the rows cover W (§4.1) | 100 % of W | in closed loop a 5 s aiding gap (`AID_TIMEOUT_MS`) makes `thesis_nav_check` command LAND. A gap in Replay means a LAND in stage 3 |
| **G3** | **No numerical failure:** `n_chol_fail` = 0 over the whole log, read from the Replay's `ukf_stats.csv`. **A missing `ukf_stats.csv`, or one without an `n_chol_fail` row, FAILS G3** (U10 rule 1). `n_chol_retry` is reported | = 0 | the jitter fix (2026-10-09): 0 fallbacks on all SITL data [V]; the counters in the Replay output since `e82c050b`: 0 / 0 on the five SITL logs [V] |
| **G4** | **Accuracy against mocap:** UKF (`XUKO`, message `RUKO`) evo -a (SE(3), `t_max_diff` 0.05) over W ≤ **max(2.0 × EKF3_R, EKF3_R + 0.10 m)**, with EKF3_R = the replayed EKF3 (`XKF1@100`) on the same flight, window and Replay output | per flight | see below |
| **G5** | **Bounded unaligned drift:** the start-aligned horizontal drift (rung-1 §4.3 rule; `drift_start_aligned.final_h_m`, the error at the last estimator sample in W, i.e. at t_ld − 5 s) ≤ **D_max = 1.0 m** (SIGNED 2026-10-12; basis: half the 2 m clearance required at every hold point; the draft had proposed it as half the smallest watcher-box half-width). **Not computable** (the rung-1 rule refuses the segment) **= FAIL** | per flight | a closed loop steers on the unaligned estimate; this is the physical excursion it would cause |
| **G6** | **Replay fidelity:** ONLY if rung 1 flew the fork in shadow (the Replay output holds onboard `XUKF`). Replayed `RUKF`/`RUKS` against onboard `XUKF`/`XUKS` in the same Replay output: **E1 3-D position max ≤ 0.05 m, rms ≤ 0.01 m; E3 yaw max ≤ 0.05°; E5 accepted-count increments within 0.1 %** (definition §4.1) | per flight, **[TBD-V]** | see below |

**Set rule:** **the gate PASSES only if G1–G5 (and G6 where it applies) hold on EVERY usable result flight**, with at
least 4 usable flights, all replayed by the same Replay binary (md5).
- This is a safety gate, so one failing flight fails it. A failure is never averaged away.
- With fewer than 4 usable flights the gate is **NOT EVALUABLE**. More rung-1 flights are needed, flown under the
  rung-1 rules; none is re-flown because of a UKF result.
- "Usable" = not excluded under rung-1 §3.3. A Replay output whose `XKF1@100` TimeUS sequence differs from
  `XKF1@0`'s counts as incomplete for replay (rung-1 §3.3 item 2; `replay_gate.py` and `real_score.py` both refuse
  it).

### 4.1 Exact definitions (as implemented in `eval/u10_gate.py`)

- **Preconditions (per flight; failing one fails the flight):**
  - the score JSON was computed on THIS Replay output (`estimators.*.sha256` = the sha256 of the Replay output .BIN);
  - its UKF row is record `XUKO` / message `RUKO`, and its EKF3 row is record `XKF1@100` / message `XKF1`;
  - the Replay output has 0 undeclared types, 0 bad FMT and 0 re-declared type ids.
- **G1:**
  - `ukf_geometry.csv` has `mode,log` and a `resolved_at_ms` row;
  - the source label of `flow_delay_ms` (`EK3_FLOW_DELAY`), of `hgt_delay` and `bcn_delay` (`EK3_HGT_DELAY`,
    `EK3_BCN_DELAY`) and of `rng1_min_max` (`RNGFND1_MIN`/`_MAX`) is `log_parm` each. `default` or
    `replay_registered_default` fails;
  - every `warning_late_parm` row is listed in the output. It "does not change a value" if:
    - it is one of the five resolved parameters above with the value in use (tolerance 1e-6 × max(1, |value|)); or
    - it is a lever-arm parameter (`FLOW_POS_*`, `INS_POS*`, `RNGFNDn_POS_*`): the port takes the lever arms per
      sample from the sensor records, not from PARM (`AP_NavUKF.cpp` `note_log_param` comment).
    - Any other late parameter, or a changed value, fails G1;
  - "before arming": the first `ukf_shadow.csv` row (the first initialised state) and `resolved_at_ms` are both
    earlier than the first `ARM` record with `ArmState` = 1 in the Replay output. On the H log (no score, disarmed)
    a missing `ARM` makes this part not applicable. On a gated flight a missing `ARM` FAILS G1 (N3).
- **G2:**
  - every `ukf_shadow.csv` row with TimeUS in W, inclusive;
  - "the rows cover W": the longest gap between consecutive rows, counting the gaps from W's start to the first row
    and from the last row to W's end, is ≤ the rung-1 pre-registration's `metrics.max_gap_s` (0.5 s), read from the
    score JSON. No row in W fails G2.
- **G6:**
  - "initialisation" = the first record of each series (`RUKF` replayed, `XUKF` onboard);
  - pairs = exact TimeUS matches from the later initialisation + 10 s to the last match. E1 = the 3-D norm of
    (PN, PE, PD) differences: max and rms. E3 = the wrapped yaw difference, max;
  - E5, for each of `FXa`, `FYa`, `Ra`: the increment over the paired span [first pair, last pair], taken from the
    last `XUKS` / `RUKS` record at or before each end; |Δonboard − Δreplay| / max(Δonboard, 1) ≤ 0.001;
  - G6 does not apply when the Replay output holds no `XUKF` (stock firmware flew). It fails if `XUKF` exists but no
    `RUKF` does.
- **Verdict:** a flight PASSES if the preconditions and G1–G6 all pass (G6 passes when it does not apply). The set
  verdict is §4's set rule.

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
- **The bands are the existing port-equivalence bands** (METHODOLOGY step 1, 2026-09-30), unchanged: E1 is the 3-D
  position difference.
- On SITL, Replay against the flying port gave [V, `eval/results/r1_ukf_port/b_*.json`, whole overlap]:
  - E1 max 0.0184 m / rms 0.0032 m, E3 0.0049° on `cl_ukf_b_tex_r1_half_v2` (max at 9.5 s, just after initialisation);
  - 0.00055 m / 0.00006 m, 0.0006° on `H_s2v2_r1`.
  - Recomputed 2026-10-12 from the renamed records (`RUKF` vs `XUKF` in one Replay output, whole overlap):
    0.01839 m / 0.00322 m, 0.0045° and 0.00054 m / 0.00003 m, 0.0001°. That reproduces the stored values to the
    CSV's 4-decimal printing, so the right streams were picked [V].
  - With the gate's pairing start (later initialisation + 10 s), `u10_gate.py` gives 0.0124 m / 0.0025 m, 0.0040°
    and 1.1e-6 m / 1.2e-7 m, 7.7e-6°; E5 relative differences ≤ 1.1e-4 [V, plumbing].
- **Adapted to real logs, declared here before any data:**
  - Pairing starts at the LATER of the two initialisations + 10 s. In SITL the Replay UKF initialised 1.0 s after the
    flying one (a pre-existing offset; this is what made E5 fail as worded on 2026-10-11).
  - **E5 uses the increment form** over the paired window, pre-registered here. On 2026-10-11 it was adopted post hoc.
  - **Board ≠ x86 numerics** (Cortex-M7 double, FMA contraction, compiler): bit-identity is not expected. As in
    rung 1 §5, the E1/E3 bounds are confirmed or widened **ONCE**, on the H and V logs, with the reason recorded,
    before any result log is gated. Never after. (`u10_gate.py flight --g6-bands` takes the confirmed values.)
- **Without the fork-in-shadow option, G6 does not apply.** Stock rung-1 firmware runs no UKF. The gate then tests
  the replayed UKF against mocap only, and **Replay-to-board fidelity is first tested in stage 3** (the stage-3
  hand-carried and tethered steps log `XUKF` onboard and replay them; stage-3 §5 S9).

## 5. Reported with the gate (no pass/fail)

- **The rung-1 §5 EKF3 Replay-fidelity result** (`eval/replay_gate.py`), per flight. It labels EKF3_R ("EKF3 (onboard,
  reproduced in Replay)" or "Replay EKF3"); it does not change G4, which uses the replayed `XKF1@100` either way.
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
- `n_chol_retry`.

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
7. **Replay's id window.** Replay allocates its own dynamic message ids from 230 down to 220. An input log that
   declares a DIFFERENT message in that window would be re-declared by Replay. No SITL log comes near it (the
   flying port's ids start at 254). The scorer and the gate refuse any re-declared id rather than misread it.

## 7. Procedure, records and the scoring command

1. **Before day 3:**
   - this document signed (§10);
   - ~~the record and the counter output settled (§3)~~ DONE (Replay `e82c050b`, then `3c3b62bb` for rule 2);
   - the Replay binary built from the flying source commit and its md5 recorded;
   - D_max and the volume entered (**[TBD-S]**).
2. **Days 3–4 (verification logs):** G1 and G3 plumbing on H; G1–G3 on V; the G6 bounds confirmed or widened once
   (only with the fork-in-shadow option); the reason recorded.
3. **Day 6 (after the rung-1 result flights, rung-1 §8 step 4):** the gate run on every usable result flight, with the
   same Replay outputs the rung-1 UKF row uses. Per flight `F` (Replay run directory `RD/F`, holding `ukf_shadow.csv`,
   `ukf_geometry.csv`, `ukf_stats.csv`, `replay.log`, `binary.md5` and `logs/<one>.BIN`):

   ```
   # the Replay (one heavy step; default environment)
   cd RD/F && md5sum ~/ardupilot_ukf/build/sitl/tool/Replay > binary.md5 && \
     ~/ardupilot_ukf/build/sitl/tool/Replay <F flight log>.BIN > replay.log 2>&1
   # the rung-1 EKF3 Replay-fidelity check (reported, §5)
   python3 eval/replay_gate.py RD/F/logs/<one>.BIN --json eval/results/u10_gate/F_replay_gate.json
   # the rung-1 score of this Replay output (G4, G5 and the window W)
   python3 eval/real_score.py --prereg docs/rung1_preregistration.json --mocap <F mocap_fc_clock_est_frame.tum> \
       --mocap-align-json <F mocap_align.json> --bin RD/F/logs/<one>.BIN \
       --est-bin EKF3=XKF1@100 --est-bin UKF=XUKO --est-bin UKF_horizon=XUKF [--est FGO=<F fgo>.tum] \
       --work-dir <work> --out eval/results/u10_gate/F_score.json
   # the gate, per flight
   python3 eval/u10_gate.py flight --replay-dir RD/F --score eval/results/u10_gate/F_score.json \
       --d-max <D_max> [--g6-bands <E1max> <E1rms> <E3> <E5>] --name F --json eval/results/u10_gate/F.json
   # the set
   python3 eval/u10_gate.py set eval/results/u10_gate/R*.json --json eval/results/u10_gate/SET.json
   ```
   - The H log: `u10_gate.py flight --replay-dir RD/H --d-max <D_max> --name H` with no `--score` (plumbing: G1, G3).
   - A METHODOLOGY entry with PASS / FAIL / NOT EVALUABLE, the binary md5 and the per-flight values.
4. **A binary change after the gate** (any fix) means a NEW gate run on the same logs with the same bands, dated. Both
   results are reported. A pass on the new binary is labelled "after fix <commit>".

## 8. Verification of the tools and of rule 2 (SITL; plumbing, not results)

All under `eval/results/u10_final/` (scripts `eval/diag/u10_final/`), on the 5 SITL `LOG_REPLAY` logs (stock-flown:
`cl_a_tex_half`, `dsn_tex_r1`, `fwdplainc_tex_r1`; fork-flown: `cl_ukf_b_tex_r1_half_v2`, `H_s2v2_r1`), each with its
stored environment, scratch build and then the installed binary:
- **(a) stock-flown:**
  - the output holds no `XUK*`, and `RUKF`/`RUKO`/`RUKS` equal `e82c050b`'s `XUKF`/`XUKO`/`XUKS` value for value;
  - byte level, record by record, the only differences from `e82c050b`'s log are the 3 FMT name fields
    (`XUK` → `RUK`) and the 3 FMTU process-clock stamps;
  - df_reader: 0 undeclared, 0 skipped, 0 bad FMT, 0 re-declared ids;
  - pymavlink (both readers) counts equal df_reader's;
  - `replay_gate.py` PASS (0 / 0 / 0); the scorer scores `UKF` from `RUKO` (cl_a: 1.0148 m, as before).
- **(b) fork-flown:**
  - the output's `XUK*` equal the input log's records one for one (8 551 and 9 606 `XUKO`);
  - `RUKO` (8 526 / 9 606) and `XUKO` are each strictly increasing; pymavlink reads them separately;
  - E1 recomputed from `RUKF` vs `XUKF` reproduces the stored CSV-based values (§4, G6 basis);
  - the scorer scores the replayed `XUKO` (`RUKO`) and, as test labels, `XUKO@onboard` (`XUKO`) side by side:
    0.1943 vs 0.1943 m, 0.0083 vs 0.0083 m (SIM truth).
- **(c)** the five CSVs (`ukf_shadow`, `ukf_inputs`, `ukf_derot`, `ukf_geometry`, `ukf_stats`) on all five logs:
  **25 / 25 byte-identical** to the installed `e82c050b`.
- **(d)** UKF_Equiv: 10 / 10 outputs identical; the installed binary is byte-identical (`fe548d36`).
- **The gate tool (`u10_gate_demo_*.json`; SIM truth stands in for mocap; D_max = 1.0 m as a test input):**
  - `cl_ukf_b_tex_r1_half_v2`: PASS, with G6 applying;
  - `cl_a_tex_half`: G5 FAIL (5.15 m start-aligned drift over a 150 m corridor);
  - `H_s2v2_r1`: G5 FAIL (drift not computable: the hover segment moves 0.6 m < 1.0 m);
  - the same `cl_a_tex_half` run with `ukf_stats.csv` removed: G3 FAIL (rule 1);
  - the set of 3: NOT EVALUABLE (< 4);
  - the H mode (no score): "PLUMBING PASS".
  - These are plumbing checks of the tool, not results.
- **Every pass/fail branch of `u10_gate.py` executed once** (`gate_branch_tests.json`, ALL OK; edited copies of the
  CSVs and score in a scratch directory, base = `cl_ukf_b_tex_r1_half_v2`):
  - G1: a non-`log_parm` source, a late PARM that changes a value, and a late `RNGFND2_MIN` each FAIL. A late PARM
    equal to the value in use, and a late lever arm, each PASS. A gated flight with no `ARM` FAILS; on H the check is
    not applicable;
  - G2: a 2 s row gap, one row with `Healthy` = 0, one with `FlowAgeMs` = 5000, and one with `SS` bit 3 clear each
    FAIL;
  - G3: `n_chol_fail` = 1 FAILS; a missing file FAILS;
  - G4: UKF 1 mm above the band FAILS;
  - G6: bands below the observed differences FAIL;
  - preconditions: a score of a different log FAILS, and so does a UKF row read from the onboard `XUKO`;
  - set rule: 4 passing → PASS; 3 passing + 1 failing → FAIL; 3 → NOT EVALUABLE; mixed binaries → INVALID. A missing
    md5, a duplicate flight and an H record are each refused.
- `eval/real_score_test.py`: 16 / 16 pass, including a new test of the replayed vs onboard selection and the refusals.

## 9. What the gate does NOT claim

- No accuracy ordering of the UKF against EKF3 or the FGO. That is the rung-1 pre-registration's job.
- No closed-loop stability claim.
- No claim about other floors (rung 1 is textured; the exploratory plain-sheet set, if flown, is not gated).

## 10. Sign-off

| | name | date | changes requested |
|---|---|---|---|
| user | | | |
| supervisor (informed) | | | |

Once signed, the status line becomes PRE-REGISTERED with the date and commit, and a METHODOLOGY entry records it. Any
later change is a dated amendment, made before the affected logs are gated.
